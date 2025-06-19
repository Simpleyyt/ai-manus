import json
import logging
import asyncio
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncGenerator
from app.domain.external.llm import LLM
from app.domain.models.agent import Agent
from app.domain.models.memory import Memory
from app.domain.services.tools.base import BaseTool
from app.domain.models.tool_result import ToolResult
from app.domain.events.agent_events import (
    BaseEvent,
    ToolEvent,
    ToolStatus,
    ErrorEvent,
    MessageEvent,
    DoneEvent,
)
from app.domain.repositories.agent_repository import AgentRepository
from app.domain.utils.json_parser import JsonParser
from app.domain.models.compression import AgentType

logger = logging.getLogger(__name__)
class BaseAgent(ABC):
    """
    Base agent class, defining the basic behavior of the agent
    """

    name: str = ""
    system_prompt: str = ""
    format: Optional[str] = None
    max_iterations: int = 30
    max_retries: int = 3
    retry_interval: float = 1.0

    def __init__(
        self,
        agent_id: str,
        agent_repository: AgentRepository,
        llm: LLM,
        json_parser: JsonParser,
        tools: List[BaseTool] = []
    ):
        self._agent_id = agent_id
        self._repository = agent_repository
        self.llm = llm
        self.json_parser = json_parser
        self.tools = tools
        self.memory = None
        # 初始化压缩相关服务
        from app.domain.services.memory_compression_service import MemoryCompressionService
        from app.domain.services.memory_manager_service import MemoryManagerService
        self._compression_service = MemoryCompressionService(llm, json_parser)
        self._memory_manager = MemoryManagerService(llm, json_parser)
        
        # 确定agent类型
        self._agent_type = AgentType.PLANNER if self.name == "planner" else AgentType.EXECUTION
    
    def get_available_tools(self) -> Optional[List[Dict[str, Any]]]:
        """Get all available tools list"""
        available_tools = []
        for tool in self.tools:
            available_tools.extend(tool.get_tools())
        return available_tools
    
    def get_tool(self, function_name: str) -> BaseTool:
        """Get specified tool"""
        for tool in self.tools:
            if tool.has_function(function_name):
                return tool
        raise ValueError(f"Unknown tool: {function_name}")

    async def invoke_tool(self, tool: BaseTool, function_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Invoke specified tool, with retry mechanism"""

        retries = 0
        while retries <= self.max_retries:
            try:
                return await tool.invoke_function(function_name, **arguments)
            except Exception as e:
                last_error = str(e)
                retries += 1
                if retries <= self.max_retries:
                    await asyncio.sleep(self.retry_interval)
                else:
                    logger.exception(f"Tool execution failed, {function_name}, {arguments}")
                    break
        
        raise ValueError(f"Tool execution failed, retried {self.max_retries} times: {last_error}")
    
    async def execute(self, request: str) -> AsyncGenerator[BaseEvent, None]:
        # 执行前检查记忆是否需要整理（主动压缩）
        if self._agent_type == AgentType.EXECUTION:
            await self._memory_manager.auto_manage_memory(self.memory, self._agent_type)
        
        message = await self.ask(request, self.format)
        for _ in range(self.max_iterations):
            if not message.get("tool_calls"):
                break
            tool_responses = []
            for tool_call in message["tool_calls"]:
                if not tool_call.get("function"):
                    continue
                
                function_name = tool_call["function"]["name"]
                tool_call_id = tool_call["id"]
                function_args = await self.json_parser.parse(tool_call["function"]["arguments"])
                
                tool = self.get_tool(function_name)

                # Generate event before tool call
                yield ToolEvent(
                    status=ToolStatus.CALLING,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args
                )

                result = await self.invoke_tool(tool, function_name, function_args)
                
                # 检查工具输出是否过长，如果是则进行压缩
                tool_content = result.model_dump_json()
                estimated_tokens = self._compression_service._estimate_tokens(tool_content)
                
                # 如果工具输出token数超过阈值，进行压缩
                if estimated_tokens > 3000:  # 设置阈值为3000token
                    logger.info(f"Tool output is large ({estimated_tokens} tokens), attempting compression")
                    try:
                        # 构造token信息
                        from app.domain.models.compression import TokenInfo
                        token_info = TokenInfo(
                            current_tokens=estimated_tokens,
                            max_tokens=4000  # 假设最大4000token
                        )
                        
                        # 对于execution agent，使用专门的工具输出压缩
                        if self._agent_type == AgentType.EXECUTION:
                            compression_result = await self._compression_service.compress_tool_output_for_execution(
                                tool_content, request, token_info  # request作为当前步骤描述
                            )
                        else:
                            # 其他agent使用通用压缩
                            compression_result = await self._compression_service.compress_tool_output(
                                tool_content, function_name, token_info
                            )
                        
                        if compression_result.compressed_content:
                            tool_content = compression_result.compressed_content
                            logger.info(f"Tool output compressed, saved {compression_result.token_saved} tokens")
                    except Exception as e:
                        logger.warning(f"Failed to compress tool output: {str(e)}")
                
                # Generate event after tool call
                yield ToolEvent(
                    status=ToolStatus.CALLED,
                    tool_name=tool.name,
                    function_name=function_name,
                    function_args=function_args,
                    function_result=result
                )

                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "content": tool_content
                }
                tool_responses.append(tool_response)

            message = await self.ask_with_messages(tool_responses)
        else:
            yield ErrorEvent(error="Maximum iteration count reached, failed to complete the task")
        
        yield MessageEvent(message=message["content"])
    
    async def _add_to_memory(self, messages: List[Dict[str, Any]]) -> None:
        """Update memory and save to repository"""
        if not self.memory:
            self.memory = await self._repository.get_memory(self._agent_id, self.name)
            if self.memory.empty:
                logger.info(f"=== Initializing empty memory for {self.name} agent ===")
                logger.info(f"=== System prompt preview: {self.system_prompt[:100]}... ===")
                self.memory.add_message({
                    "role": "system", "content": self.system_prompt,
                })
                logger.info(f"=== Added system message to memory ===")
        
        # 记录当前memory状态
        current_messages = self.memory.get_messages()
        system_msg = self.memory.get_latest_system_message()
        if system_msg:
            logger.debug(f"=== Current system message preview: {system_msg.get('content', '')[:100]}... ===")
        
        self.memory.add_messages(messages)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)

    async def ask_with_messages(self, messages: List[Dict[str, Any]], format: Optional[str] = None) -> Dict[str, Any]:
        await self._add_to_memory(messages)

        # 1. 首先检查消息数量，自动压缩
        await self._memory_manager.auto_manage_memory(self.memory, self._agent_type)

        response_format = None
        if format:
            response_format = {"type": format}

        # 2. 正常调用LLM
        try:
            message = await self.llm.ask(self.memory.get_messages(), 
                                         tools=self.get_available_tools(), 
                                         response_format=response_format)
            if message.get("tool_calls"):
                message["tool_calls"] = message["tool_calls"][:1]
            await self._add_to_memory([message])
            return message
        except Exception as e:
            logger.error(f"=== BaseAgent ask_with_messages caught exception ===: {type(e).__name__}: {str(e)}")
            logger.error(f"=== Exception MRO ===: {[cls.__name__ for cls in type(e).__mro__]}")
            
            # 检查是否是Token限制错误
            from app.domain.models.exceptions import TokenLimitExceededError
            logger.error(f"=== Checking isinstance(e, TokenLimitExceededError) ===: {isinstance(e, TokenLimitExceededError)}")
            logger.error(f"=== TokenLimitExceededError type ===: {TokenLimitExceededError}")
            logger.error(f"=== Exception type ===: {type(e)}")
            
            if isinstance(e, TokenLimitExceededError):
                # 3. token错误时的专门处理
                return await self._handle_token_limit_error(e, response_format)
            
            # 如果不是token错误或压缩失败，重新抛出异常
            raise

    async def _handle_token_limit_error(
        self, 
        error: "TokenLimitExceededError", 
        response_format: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理token限制错误
        
        Args:
            error: Token限制错误
            response_format: 响应格式
            
        Returns:
            LLM响应消息
        """
        logger.warning(f"=== BaseAgent detected TokenLimitExceededError ===: Current: {error.current_tokens}, Max: {error.max_tokens}")
        logger.warning("=== Starting compression process ===")
        
        # 记录压缩前的消息状态
        original_messages = self.memory.get_messages()
        logger.warning(f"=== Original message count: {len(original_messages)} ===")
        
        # 检查system消息
        system_msg = self.memory.get_latest_system_message()
        if system_msg:
            logger.warning(f"=== Current system message preview: {system_msg.get('content', '')[:100]}... ===")
            logger.warning(f"=== Expected system prompt preview: {self.system_prompt[:100]}... ===")
            logger.warning(f"=== System message matches: {system_msg.get('content', '') == self.system_prompt} ===")
        else:
            logger.warning("=== No system message found in memory! ===")
        
        # 估算原始消息总token数
        original_total_tokens = sum(self._compression_service._estimate_tokens(str(msg)) for msg in original_messages)
        logger.warning(f"=== Estimated original total tokens: {original_total_tokens} ===")
        
        # 使用压缩服务处理token超限
        from app.domain.models.compression import TokenInfo
        token_info = TokenInfo(
            current_tokens=error.current_tokens,
            max_tokens=error.max_tokens
        )
        
        # 根据agent类型选择压缩策略
        compression_result = await self._compression_service.compress_by_token_limit(
            self.memory.get_messages(), 
            token_info, 
            self._agent_type, 
            self.system_prompt
        )
        
        logger.warning(f"=== Compression result: original_tokens={compression_result.original_token_count}, compressed_tokens={compression_result.compressed_token_count}, saved={compression_result.token_saved} ===")
        
        if compression_result.compressed_content:
            logger.warning("=== Compression successful, updating memory ===")
            
            # 找到并替换用户输入
            memory_messages = self.memory.get_messages().copy()
            user_message_replaced = False
            
            # 检查copy后的system消息
            for i, msg in enumerate(memory_messages):
                if msg.get("role") == "system":
                    logger.warning(f"=== Found system message at index {i}, content preview: {msg.get('content', '')[:100]}... ===")
                    break
            
            for i in reversed(range(len(memory_messages))):
                if memory_messages[i].get("role") == "user":
                    logger.warning(f"=== Replacing user message at index {i} ===")
                    logger.warning(f"=== Original content length: {len(memory_messages[i]['content'])} chars ===")
                    logger.warning(f"=== Compressed content length: {len(compression_result.compressed_content)} chars ===")
                    
                    memory_messages[i]["content"] = compression_result.compressed_content
                    user_message_replaced = True
                    break
            
            if user_message_replaced:
                # 再次检查system消息
                for i, msg in enumerate(memory_messages):
                    if msg.get("role") == "system":
                        logger.warning(f"=== After replacement, system message at index {i}, content preview: {msg.get('content', '')[:100]}... ===")
                        break
                
                # 计算压缩后的总token数
                compressed_total_tokens = sum(self._compression_service._estimate_tokens(str(msg)) for msg in memory_messages)
                logger.warning(f"=== Estimated compressed total tokens: {compressed_total_tokens} ===")
                
                # 如果压缩后仍然太大，尝试记忆清理
                if compressed_total_tokens > token_info.max_tokens * 0.8:  # 如果还超过80%，进行记忆清理
                    logger.warning("=== Compressed content still too large, attempting memory cleanup ===")
                    
                    # 临时更新memory以便进行记忆管理
                    self.memory.clear_messages()
                    self.memory.add_messages(memory_messages)
                    
                    # 检查memory更新后的system消息
                    updated_system_msg = self.memory.get_latest_system_message()
                    if updated_system_msg:
                        logger.warning(f"=== After memory update, system message preview: {updated_system_msg.get('content', '')[:100]}... ===")
                    
                    # 强制进行记忆管理
                    memory_compressed = await self._memory_manager.auto_manage_memory(self.memory, self._agent_type, force=True)
                    if memory_compressed:
                        memory_messages = self.memory.get_messages()
                        final_total_tokens = sum(self._compression_service._estimate_tokens(str(msg)) for msg in memory_messages)
                        logger.warning(f"=== After memory cleanup, estimated total tokens: {final_total_tokens} ===")
                        
                        # 检查记忆管理后的system消息
                        final_system_msg = self.memory.get_latest_system_message()
                        if final_system_msg:
                            logger.warning(f"=== After memory management, system message preview: {final_system_msg.get('content', '')[:100]}... ===")
                
                # 重新尝试调用
                try:
                    logger.warning("=== Retrying LLM call with compressed content ===")
                    message = await self.llm.ask(memory_messages, 
                                                 tools=self.get_available_tools(), 
                                                 response_format=response_format)
                    if message.get("tool_calls"):
                        message["tool_calls"] = message["tool_calls"][:1]
                    
                    logger.warning("=== LLM call successful after compression ===")
                    
                    # 更新实际的memory
                    self.memory.clear_messages()
                    self.memory.add_messages(memory_messages)
                    await self._add_to_memory([message])
                    
                    return message
                except Exception as retry_error:
                    logger.error(f"=== LLM call failed even after compression: {str(retry_error)} ===")
                    
                    # 如果还是失败，尝试更激进的压缩
                    if isinstance(retry_error, TokenLimitExceededError):
                        logger.warning("=== Attempting more aggressive compression ===")
                        
                        # 只保留system消息和最后一条压缩后的用户消息
                        system_msg = self.memory.get_latest_system_message()
                        last_user_msg = None
                        
                        for msg in reversed(memory_messages):
                            if msg.get("role") == "user":
                                last_user_msg = msg
                                break
                        
                        if system_msg and last_user_msg:
                            minimal_messages = [system_msg, last_user_msg]
                            logger.warning(f"=== Trying with minimal messages: {len(minimal_messages)} ===")
                            logger.warning(f"=== Minimal system message preview: {system_msg.get('content', '')[:100]}... ===")
                            
                            try:
                                message = await self.llm.ask(minimal_messages, 
                                                             tools=self.get_available_tools(), 
                                                             response_format=response_format)
                                if message.get("tool_calls"):
                                    message["tool_calls"] = message["tool_calls"][:1]
                                
                                # 更新memory为最小版本
                                self.memory.clear_messages()
                                self.memory.add_messages(minimal_messages)
                                await self._add_to_memory([message])
                                
                                logger.warning("=== Success with minimal messages ===")
                                return message
                            except Exception as final_error:
                                logger.error(f"=== Even minimal messages failed: {str(final_error)} ===")
                    
                    # 重新抛出重试错误
                    raise retry_error
            else:
                logger.warning("=== No user message found to replace ===")
        else:
            logger.warning("=== Compression returned empty content ===")
        
        # 如果压缩失败，尝试记忆管理
        logger.warning("=== Attempting memory management as fallback ===")
        compressed = await self._memory_manager.auto_manage_memory(self.memory, self._agent_type)
        if compressed:
            logger.warning("=== Memory management successful, retrying LLM call ===")
            try:
                # 重新尝试调用
                message = await self.llm.ask(self.memory.get_messages(), 
                                             tools=self.get_available_tools(), 
                                             response_format=response_format)
                if message.get("tool_calls"):
                    message["tool_calls"] = message["tool_calls"][:1]
                await self._add_to_memory([message])
                logger.warning("=== LLM call successful after memory management ===")
                return message
            except Exception as memory_retry_error:
                logger.error(f"=== LLM call failed even after memory management: {str(memory_retry_error)} ===")
        
        # 如果所有压缩策略都失败，重新抛出异常
        logger.error("=== All compression strategies failed ===")
        raise error

    async def ask(self, request: str, format: Optional[str] = None) -> Dict[str, Any]:
        return await self.ask_with_messages([
            {
                "role": "user", "content": request
            }
        ], format)
    
    def roll_back(self):
        self.memory.roll_back()
