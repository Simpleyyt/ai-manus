import logging
from typing import List, Dict, Any, Optional, Tuple
from app.domain.external.llm import LLM
from app.domain.models.memory import Memory
from app.domain.models.compression import CompressionResult, CompressionType, AgentType
from app.domain.utils.json_parser import JsonParser
from app.domain.services.prompts.memory_manager import (
    EXECUTION_HISTORY_SUMMARY_PROMPT,
    GENERAL_SUMMARY_PROMPT
)

logger = logging.getLogger(__name__)


class MemoryManagerService:
    """记忆管理服务 - 负责智能管理和压缩对话历史"""
    
    def __init__(self, llm: LLM, json_parser: JsonParser):
        self.llm = llm
        self.json_parser = json_parser
        self.cleanup_threshold = 20  # 20条消息时触发清理
        self.keep_recent_count = 8  # 保留最近8条消息
        # 实际保留结构：system(1) + 任务需求(1) + 摘要(1) + 最近8条 = 11条
        self.target_count = 11  
    
    def should_compress_by_count(self, memory: Memory) -> bool:
        """判断是否需要基于消息数量压缩
        
        Args:
            memory: 记忆对象
            
        Returns:
            是否需要压缩
        """
        if not memory or memory.empty:
            return False
        
        # 检查总消息数量是否达到阈值
        return len(memory.get_messages()) >= self.cleanup_threshold
    
    def _find_initial_task_message(self, messages: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """找到最初的任务需求消息
        
        通常是第一条用户消息，或者包含明确任务描述的消息
        
        Args:
            messages: 消息列表
            
        Returns:
            任务需求消息，如果没找到返回None
        """
        # 先找第一条用户消息
        for msg in messages:
            if msg.get("role") == "user":
                # 检查是否包含任务关键词
                content = msg.get("content", "").lower()
                task_keywords = ["帮我", "请", "需要", "任务", "目标", "help", "please", "need", "task", "goal"]
                if any(keyword in content for keyword in task_keywords) or len(content) > 50:
                    return msg
        
        # 如果没找到明确的任务消息，返回第一条用户消息
        for msg in messages:
            if msg.get("role") == "user":
                return msg
        
        return None
    
    def _identify_important_messages(self, messages: List[Dict[str, Any]]) -> Tuple[
        Optional[Dict[str, Any]], Optional[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]
    ]:
        """识别重要消息：系统提示词、任务需求、需要压缩的中间消息、最近消息
        
        Args:
            messages: 所有消息列表
            
        Returns:
            (系统消息, 任务消息, 中间消息列表, 最近消息列表)
        """
        system_msg = None
        task_msg = None
        
        # 找系统消息（通常是第一条）
        if messages and messages[0].get("role") == "system":
            system_msg = messages[0]
        
        # 找任务需求消息
        task_msg = self._find_initial_task_message(messages)
        
        # 计算需要保留的消息索引
        preserved_indices = set()
        if system_msg:
            preserved_indices.add(0)
        if task_msg:
            task_index = messages.index(task_msg)
            preserved_indices.add(task_index)
        
        # 最近的N条消息
        recent_start_index = max(0, len(messages) - self.keep_recent_count)
        recent_messages = messages[recent_start_index:]
        for i in range(recent_start_index, len(messages)):
            preserved_indices.add(i)
        
        # 中间需要压缩的消息
        middle_messages = []
        for i, msg in enumerate(messages):
            if i not in preserved_indices:
                middle_messages.append(msg)
        
        return system_msg, task_msg, middle_messages, recent_messages
    
    async def compress_by_message_count(
        self, 
        memory: Memory,
        agent_type: AgentType
    ) -> CompressionResult:
        """基于消息数量压缩记忆 - 保留系统提示词、任务需求和最近8条
        
        Args:
            memory: 记忆对象
            agent_type: Agent类型
            
        Returns:
            压缩结果
        """
        messages = memory.get_messages()
        if len(messages) < self.cleanup_threshold:
            return CompressionResult(
                original_content="",
                compressed_content="",
                compression_type=CompressionType.MEMORY_CLEANUP,
                original_token_count=0,
                compressed_token_count=0
            )
        
        # 识别重要消息
        system_msg, task_msg, middle_messages, recent_messages = self._identify_important_messages(messages)
        
        if not middle_messages:
            # 没有需要压缩的中间消息
            return CompressionResult(
                original_content="",
                compressed_content="",
                compression_type=CompressionType.MEMORY_CLEANUP,
                original_token_count=0,
                compressed_token_count=0
            )
        
        # 生成中间消息的摘要
        if agent_type == AgentType.EXECUTION:
            summary_content = await self._generate_execution_history_summary(middle_messages, task_msg)
        else:
            summary_content = await self._generate_general_summary(middle_messages, task_msg)
        
        # 创建摘要消息
        summary_message = {
            "role": "assistant",
            "content": f"[历史对话摘要]: {summary_content}"
        }
        
        # 构造新的消息列表
        new_messages = []
        
        # 1. 系统提示词
        if system_msg:
            new_messages.append(system_msg)
        
        # 2. 任务需求（如果不在最近消息中）
        if task_msg and task_msg not in recent_messages:
            new_messages.append(task_msg)
        
        # 3. 历史摘要
        new_messages.append(summary_message)
        
        # 4. 最近的消息
        new_messages.extend(recent_messages)
        
        # 更新记忆
        original_content = self._messages_to_text(middle_messages)
        memory.clear_messages()
        memory.add_messages(new_messages)
        
        # 计算token数量
        original_tokens = self._estimate_tokens(original_content)
        compressed_tokens = self._estimate_tokens(summary_content)
        
        logger.info(f"Memory compressed from {len(messages)} to {len(new_messages)} messages")
        logger.info(f"Preserved: system_msg={bool(system_msg)}, task_msg={bool(task_msg)}, recent={len(recent_messages)}")
        
        return CompressionResult(
            original_content=original_content,
            compressed_content=summary_content,
            compression_type=CompressionType.MEMORY_CLEANUP,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            summary=summary_content
        )
    
    async def auto_manage_memory(
        self, 
        memory: Memory, 
        agent_type: AgentType,
        force: bool = False
    ) -> bool:
        """自动记忆管理
        
        Args:
            memory: 记忆对象
            agent_type: Agent类型
            force: 是否强制压缩（即使未达到阈值）
            
        Returns:
            是否进行了压缩操作
        """
        if force or self.should_compress_by_count(memory):
            if force:
                logger.info("Force compression requested, performing memory compression")
            else:
                logger.info(f"Memory size exceeded threshold ({self.cleanup_threshold}), performing automatic compression")
            
            compression_result = await self.compress_by_message_count(memory, agent_type)
            
            if compression_result.token_saved > 0:
                logger.info(f"Memory compression completed, saved {compression_result.token_saved} tokens")
                return True
            
        return False
    
    async def find_and_compress_longest_message(
        self, 
        memory: Memory,
        max_tokens: int
    ) -> Optional[Tuple[int, str]]:
        """找到最长的消息并返回其索引和类型
        
        Args:
            memory: 记忆对象
            max_tokens: 最大token限制
            
        Returns:
            (消息索引, 消息类型) 或 None
        """
        messages = memory.get_messages()
        longest_index = -1
        longest_tokens = 0
        longest_type = None
        
        for i, msg in enumerate(messages):
            # 跳过系统消息
            if msg.get("role") == "system":
                continue
                
            content = msg.get("content", "")
            tokens = self._estimate_tokens(content)
            
            if tokens > longest_tokens:
                longest_tokens = tokens
                longest_index = i
                longest_type = msg.get("role")
        
        # 只有当最长消息超过一定阈值时才考虑压缩
        if longest_tokens > max_tokens * 0.3:  # 超过最大token的30%
            return longest_index, longest_type
        
        return None
    
    def _messages_to_text(self, messages: List[Dict[str, Any]]) -> str:
        """将消息列表转换为文本
        
        Args:
            messages: 消息列表
            
        Returns:
            文本内容
        """
        text_parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            text_parts.append(f"[{role}]: {content}")
        
        return "\n".join(text_parts)
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量（简化版本）"""
        import re
        
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        # 其他字符
        other_chars = len(text) - chinese_chars - english_words
        
        return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 0.5)
    
    async def _generate_execution_history_summary(
        self, 
        messages: List[Dict[str, Any]],
        task_msg: Optional[Dict[str, Any]] = None
    ) -> str:
        """为执行历史生成摘要
        
        Args:
            messages: 要摘要的消息列表
            task_msg: 任务消息（用于提供上下文）
            
        Returns:
            生成的摘要
        """
        # 将消息转换为文本
        content = self._messages_to_text(messages)
        task_context = ""
        if task_msg:
            task_context = f"\n原始任务需求：{task_msg.get('content', '')[:200]}"
        
        prompt = EXECUTION_HISTORY_SUMMARY_PROMPT.format(
            content=content,
            task_context=task_context
        )

        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", content[:300] + "...")
        except Exception as e:
            logger.warning(f"Failed to generate execution summary: {str(e)}")
            # 如果摘要生成失败，返回截断的原文
            return content[:300] + "..."
    
    async def _generate_general_summary(
        self, 
        messages: List[Dict[str, Any]],
        task_msg: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成通用摘要
        
        Args:
            messages: 要摘要的消息列表
            task_msg: 任务消息（用于提供上下文）
            
        Returns:
            生成的摘要
        """
        content = self._messages_to_text(messages)
        task_context = ""
        if task_msg:
            task_context = f"\n原始任务需求：{task_msg.get('content', '')[:200]}"
        
        prompt = GENERAL_SUMMARY_PROMPT.format(
            content=content,
            task_context=task_context
        )

        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", content[:300] + "...")
        except Exception as e:
            logger.warning(f"Failed to generate general summary: {str(e)}")
            return content[:300] + "..."
    
    # 保留向后兼容的方法
    async def compress_old_messages(self, memory: Memory) -> CompressionResult:
        """压缩旧的消息为摘要（兼容旧接口）"""
        return await self.compress_by_message_count(memory, AgentType.EXECUTION)
    
    def should_compress_memory(self, memory: Memory) -> bool:
        """判断是否需要压缩记忆（兼容旧接口）"""
        return self.should_compress_by_count(memory)
    
    async def maintain_memory_size(self, memory: Memory) -> bool:
        """维护记忆大小（兼容旧接口）"""
        return await self.auto_manage_memory(memory, AgentType.EXECUTION) 