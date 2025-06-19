import logging
from typing import List, Dict, Any
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
    """记忆管理服务"""
    
    def __init__(self, llm: LLM, json_parser: JsonParser):
        self.llm = llm
        self.json_parser = json_parser
        self.cleanup_threshold = 20  # 20条消息时触发清理
        self.compress_count = 10  # 压缩前10条消息
        self.target_count = 12  # 压缩后保持12条消息（system + 摘要 + 最新10条）
    
    def should_compress_memory(self, memory: Memory) -> bool:
        """判断是否需要压缩记忆
        
        Args:
            memory: 记忆对象
            
        Returns:
            是否需要压缩
        """
        if not memory or memory.empty:
            return False
        
        # 统计非system消息的数量
        non_system_messages = memory.get_non_system_messages()
        return len(non_system_messages) >= self.cleanup_threshold
    
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
    
    async def compress_by_message_count(
        self, 
        memory: Memory,
        agent_type: AgentType
    ) -> CompressionResult:
        """基于消息数量压缩记忆 - 20条消息压缩到12条
        
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
        
        # 保留结构：system(1) + 摘要(1) + 最新10条
        system_msg = messages[0]
        latest_10 = messages[-10:]  # 最新10条
        
        # 计算要压缩的消息范围
        if system_msg:
            # 如果有system消息，压缩中间的10条（跳过system和最新10条）
            start_idx = 1  # 跳过system消息
            end_idx = len(messages) - 10  # 排除最新10条
            old_messages = messages[start_idx:end_idx]
        else:
            # 如果没有system消息，压缩除最新10条外的所有消息
            old_messages = messages[:-10]
        
        if not old_messages:
            return CompressionResult(
                original_content="",
                compressed_content="",
                compression_type=CompressionType.MEMORY_CLEANUP,
                original_token_count=0,
                compressed_token_count=0
            )
        
        # 生成摘要
        if agent_type == AgentType.EXECUTION:
            summary_content = await self._generate_execution_history_summary(old_messages)
        else:
            summary_content = await self._generate_general_summary(old_messages)
        
        # 创建摘要消息
        summary_message = {
            "role": "assistant",
            "content": f"[历史对话摘要]: {summary_content}"
        }
        
        # 构造新的消息列表
        new_messages = []
        if system_msg:
            new_messages.append(system_msg)
        new_messages.append(summary_message)
        new_messages.extend(latest_10)
        
        # 更新记忆
        original_content = self._messages_to_text(old_messages)
        memory.clear_messages()
        memory.add_messages(new_messages)
        
        # 计算token数量
        original_tokens = self._estimate_tokens(original_content)
        compressed_tokens = self._estimate_tokens(summary_content)
        
        logger.info(f"Memory compressed from {len(messages)} to {len(new_messages)} messages")
        
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
    
    async def compress_old_messages(self, memory: Memory) -> CompressionResult:
        """压缩旧的消息为摘要（兼容旧接口）
        
        Args:
            memory: 记忆对象
            
        Returns:
            压缩结果
        """
        # 默认当作execution处理
        return await self.compress_by_message_count(memory, AgentType.EXECUTION)
    
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
    
    async def _generate_execution_history_summary(self, messages: List[Dict[str, Any]]) -> str:
        """为执行历史生成摘要
        
        Args:
            messages: 要摘要的消息列表
            
        Returns:
            生成的摘要
        """
        # 将消息转换为文本
        content = self._messages_to_text(messages)
        
        prompt = EXECUTION_HISTORY_SUMMARY_PROMPT.format(content=content)

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
    
    async def _generate_general_summary(self, messages: List[Dict[str, Any]]) -> str:
        """生成通用摘要
        
        Args:
            messages: 要摘要的消息列表
            
        Returns:
            生成的摘要
        """
        content = self._messages_to_text(messages)
        
        prompt = GENERAL_SUMMARY_PROMPT.format(content=content)

        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", content[:300] + "...")
        except Exception as e:
            logger.warning(f"Failed to generate general summary: {str(e)}")
            return content[:300] + "..."
    
    async def maintain_memory_size(self, memory: Memory) -> bool:
        """维护记忆大小，确保不会无限增长（兼容旧接口）
        
        Args:
            memory: 记忆对象
            
        Returns:
            是否进行了压缩操作
        """
        # 默认当作execution处理
        return await self.auto_manage_memory(memory, AgentType.EXECUTION) 