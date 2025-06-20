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
from app.domain.models.compression import AgentType, TokenInfo
from app.domain.models.exceptions import TokenLimitExceededError

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
        
        # 跟踪是否正在处理分段内容
        self._processing_segments = False
        self._segment_context = None
    
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
        """执行Agent任务"""
        # 执行前检查记忆是否需要整理（主动压缩）
        if self._agent_type == AgentType.EXECUTION:
            compressed = await self._memory_manager.auto_manage_memory(self.memory, self._agent_type)
            # 如果发生了压缩，立即保存
            if compressed:
                await self._repository.save_memory(self._agent_id, self.name, self.memory)
                logger.info(f"Memory compressed and saved before execution for {self.name} agent")
        
        # 如果请求超长，可能需要分段处理
        request_tokens = self._compression_service._estimate_tokens(request)
        max_model_tokens = self.llm.max_tokens
        
        # 如果请求本身就很长，先检查是否需要分段
        if request_tokens > max_model_tokens * 0.5:  # 超过模型容量的50%
            logger.info(f"Request is long ({request_tokens} tokens), may need segmentation")
            # 标记可能需要分段处理
            self._segment_context = {
                "original_request": request,
                "type": "user_input"
            }
        
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
                        
                        # 使用改进的压缩方法
                        compression_result = await self._compression_service.compress_for_immediate_use(
                            content=tool_content,
                            content_type="tool",
                            context=request,  # 使用当前步骤作为上下文
                            token_info=token_info,
                            agent_type=self._agent_type
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
        compressed = await self._memory_manager.auto_manage_memory(self.memory, self._agent_type)
        
        # 如果发生了压缩，立即保存到数据库
        if compressed:
            await self._repository.save_memory(self._agent_id, self.name, self.memory)
            logger.info(f"Memory compressed and saved for {self.name} agent")

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
            logger.debug(f"=== BaseAgent ask_with_messages caught exception ===: {type(e).__name__}: {str(e)}")
            
            # 检查是否是Token限制错误
            if isinstance(e, TokenLimitExceededError):
                # 3. token错误时的专门处理
                return await self._handle_token_limit_error(e, response_format)
            
            # 如果不是token错误或压缩失败，重新抛出异常
            raise

    async def _handle_token_limit_error(
        self, 
        error: TokenLimitExceededError, 
        response_format: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理token限制错误 - 改进版
        
        处理流程：
        1. 首先尝试清理消息列表（记忆管理）
        2. 如果还超限，找最长消息进行压缩或分段处理
        3. 如果是分段处理，启动分段提交流程
        
        Args:
            error: Token限制错误
            response_format: 响应格式
            
        Returns:
            LLM响应消息
        """
        logger.warning(f"Token limit exceeded: Current: {error.current_tokens}, Max: {error.max_tokens}")
        
        # 构造token信息
        from app.domain.models.compression import TokenInfo
        token_info = TokenInfo(
            current_tokens=error.current_tokens,
            max_tokens=error.max_tokens
        )
        
        # 步骤1: 先尝试强制记忆清理
        logger.info("Step 1: Attempting forced memory cleanup")
        memory_compressed = await self._memory_manager.auto_manage_memory(
            self.memory, self._agent_type, force=True
        )
        
        if memory_compressed:
            await self._repository.save_memory(self._agent_id, self.name, self.memory)
            logger.info("Memory cleanup successful, retrying LLM call")
            
            try:
                # 重试调用
                message = await self.llm.ask(
                    self.memory.get_messages(), 
                    tools=self.get_available_tools(), 
                    response_format=response_format
                )
                if message.get("tool_calls"):
                    message["tool_calls"] = message["tool_calls"][:1]
                await self._add_to_memory([message])
                return message
            except TokenLimitExceededError as retry_error:
                logger.warning("Still exceeds token limit after memory cleanup")
                # 更新token信息
                token_info = TokenInfo(
                    current_tokens=retry_error.current_tokens,
                    max_tokens=retry_error.max_tokens
                )
        
        # 步骤2: 找到最长的消息进行处理
        logger.info("Step 2: Finding longest message for compression")
        longest_msg_info = await self._memory_manager.find_and_compress_longest_message(
            self.memory, token_info.max_tokens
        )
        
        if not longest_msg_info:
            logger.error("No suitable message found for compression")
            raise error
        
        msg_index, msg_type = longest_msg_info
        messages = self.memory.get_messages()
        longest_msg = messages[msg_index]
        
        logger.info(f"Found longest message: type={msg_type}, index={msg_index}, " 
                   f"content_length={len(longest_msg.get('content', ''))}")
        
        # 步骤3: 根据消息类型决定处理策略
        content = longest_msg.get("content", "")
        content_tokens = self._compression_service._estimate_tokens(content)
        
        # 判断是否需要分段处理
        if content_tokens > token_info.max_tokens * 0.7:  # 超过最大容量的70%
            logger.info("Content is too long, initiating segmented processing")
            # 启动分段处理流程
            return await self._handle_segmented_processing(
                msg_index, msg_type, content, token_info, response_format
            )
        else:
            # 直接压缩
            logger.info("Content can be compressed directly")
            return await self._compress_and_retry(
                msg_index, msg_type, content, token_info, response_format
            )
    
    async def _compress_and_retry(
        self,
        msg_index: int,
        msg_type: str,
        content: str,
        token_info: TokenInfo,
        response_format: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """压缩消息并重试
        
        Args:
            msg_index: 消息索引
            msg_type: 消息类型
            content: 消息内容
            token_info: Token信息
            response_format: 响应格式
            
        Returns:
            LLM响应
        """
        # 获取任务上下文
        context = "未知任务"
        if msg_type == "user":
            context = "用户输入"
        elif msg_type == "tool":
            # 尝试从前一条消息获取上下文
            messages = self.memory.get_messages()
            if msg_index > 0:
                prev_msg = messages[msg_index - 1]
                if prev_msg.get("role") == "assistant":
                    context = prev_msg.get("content", "工具执行")[:100]
        
        # 压缩内容
        compression_result = await self._compression_service.compress_for_immediate_use(
            content=content,
            content_type=msg_type,
            context=context,
            token_info=token_info,
            agent_type=self._agent_type
        )
        
        if not compression_result.compressed_content:
            logger.error("Compression failed")
            raise RuntimeError("Failed to compress content")
        
        # 替换原消息
        messages = self.memory.get_messages()
        messages[msg_index]["content"] = compression_result.compressed_content
        
        # 更新记忆
        self.memory.clear_messages()
        self.memory.add_messages(messages)
        await self._repository.save_memory(self._agent_id, self.name, self.memory)
        
        logger.info(f"Message compressed: {compression_result.original_token_count} -> "
                   f"{compression_result.compressed_token_count} tokens")
        
        # 重试调用
        try:
            message = await self.llm.ask(
                self.memory.get_messages(), 
                tools=self.get_available_tools(), 
                response_format=response_format
            )
            if message.get("tool_calls"):
                message["tool_calls"] = message["tool_calls"][:1]
            await self._add_to_memory([message])
            return message
        except Exception as e:
            logger.error(f"Retry failed after compression: {str(e)}")
            raise
    
    async def _handle_segmented_processing(
        self,
        msg_index: int,
        msg_type: str,
        content: str,
        token_info: TokenInfo,
        response_format: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """处理需要分段的超长内容
        
        这是实现用户需求的核心功能：
        - 将超长内容分段
        - 每段包含历史摘要
        - 分次提交给LLM
        
        Args:
            msg_index: 消息索引
            msg_type: 消息类型
            content: 消息内容
            token_info: Token信息
            response_format: 响应格式
            
        Returns:
            最终的LLM响应
        """
        logger.info("Starting segmented processing for long content")
        
        # 获取任务上下文
        context = self._get_task_context(msg_index, msg_type)
        
        # 标记正在处理分段
        self._processing_segments = True
        
        # 保存原始消息
        messages = self.memory.get_messages()
        original_msg = messages[msg_index].copy()
        
        # 初始化分段处理
        segment_generator = self._compression_service.process_long_content_in_segments(
            content=content,
            content_type=msg_type,
            context=context,
            max_tokens=token_info.max_tokens
        )
        
        final_response = None
        accumulated_responses = []
        
        # 处理每个分段
        async for segment_result in segment_generator:
            if segment_result["type"] == "segment":
                # 构造当前段的消息
                segment_content = segment_result["content"]
                
                # 如果有历史摘要，添加到内容前面
                if segment_content["has_history"]:
                    formatted_content = (
                        f"[历史摘要]:\n{segment_content['history_summary']}\n\n"
                        f"[当前内容 - 第{segment_content['segment_index']}/{segment_content['total_segments']}段]:\n"
                        f"{segment_content['content']}"
                    )
                else:
                    formatted_content = (
                        f"[内容 - 第{segment_content['segment_index']}/{segment_content['total_segments']}段]:\n"
                        f"{segment_content['content']}"
                    )
                
                # 替换消息内容
                messages[msg_index]["content"] = formatted_content
                
                # 更新记忆并调用LLM
                self.memory.clear_messages()
                self.memory.add_messages(messages)
                
                try:
                    logger.info(f"Processing segment {segment_result['index'] + 1}/{segment_result['total']}")
                    
                    response = await self.llm.ask(
                        self.memory.get_messages(), 
                        tools=self.get_available_tools(), 
                        response_format=response_format
                    )
                    
                    # 收集响应
                    accumulated_responses.append(response)
                    final_response = response
                    
                    # 对于非最后一段，添加助手响应到记忆中
                    if segment_result['index'] < segment_result['total'] - 1:
                        self.memory.add_message({
                            "role": "assistant",
                            "content": f"已处理第{segment_result['index'] + 1}段内容。"
                        })
                    
                except Exception as e:
                    logger.error(f"Failed to process segment {segment_result['index'] + 1}: {str(e)}")
                    # 恢复原始消息
                    messages[msg_index] = original_msg
                    self.memory.clear_messages()
                    self.memory.add_messages(messages)
                    self._processing_segments = False
                    raise
            
            elif segment_result["type"] == "final_summary":
                # 处理完成，使用最终摘要替换原始消息
                final_summary = segment_result["summary"]
                messages[msg_index]["content"] = f"[内容摘要]:\n{final_summary}"
                self.memory.clear_messages()
                self.memory.add_messages(messages)
                await self._repository.save_memory(self._agent_id, self.name, self.memory)
                logger.info("Segmented processing completed")
        
        self._processing_segments = False
        
        if not final_response:
            raise RuntimeError("No response generated from segmented processing")
        
        # 如果需要，可以合并所有响应
        if len(accumulated_responses) > 1 and response_format and response_format.get("type") == "json_object":
            # 对于JSON响应，可能需要合并多个响应
            final_response = self._merge_json_responses(accumulated_responses)
        
        # 处理工具调用
        if final_response.get("tool_calls"):
            final_response["tool_calls"] = final_response["tool_calls"][:1]
        
        await self._add_to_memory([final_response])
        return final_response
    
    def _get_task_context(self, msg_index: int, msg_type: str) -> str:
        """获取任务上下文
        
        Args:
            msg_index: 消息索引
            msg_type: 消息类型
            
        Returns:
            任务上下文描述
        """
        messages = self.memory.get_messages()
        
        # 对于用户消息，查找任务需求
        if msg_type == "user":
            # 尝试从第一条用户消息获取任务
            for msg in messages:
                if msg.get("role") == "user":
                    content = msg.get("content", "")
                    if len(content) > 50:  # 假设任务描述至少50字符
                        return content[:200]  # 返回前200字符作为上下文
            return "用户输入"
        
        # 对于工具输出，从前面的助手消息获取上下文
        elif msg_type == "tool" and msg_index > 0:
            prev_msg = messages[msg_index - 1]
            if prev_msg.get("role") == "assistant":
                return prev_msg.get("content", "工具执行")[:200]
        
        return "执行任务"
    
    def _merge_json_responses(self, responses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """合并多个JSON响应
        
        对于分段处理的JSON响应，可能需要合并结果
        
        Args:
            responses: 响应列表
            
        Returns:
            合并后的响应
        """
        # 简单实现：返回最后一个响应
        # 根据具体需求，可以实现更复杂的合并逻辑
        return responses[-1]
    
    async def ask(self, request: str, format: Optional[str] = None) -> Dict[str, Any]:
        return await self.ask_with_messages([
            {
                "role": "user", "content": request
            }
        ], format)
    
    def roll_back(self):
        self.memory.roll_back()
