import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from app.domain.external.llm import LLM
from app.domain.models.compression import (
    CompressionResult, 
    CompressionType, 
    TokenInfo, 
    ContentSegment,
    AgentType
)
from app.domain.models.exceptions import TokenLimitExceededError
from app.domain.utils.json_parser import JsonParser
from app.domain.services.prompts.compression import (
    PLANNER_COMPRESSION_PROMPT_TEMPLATE,
    TOOL_OUTPUT_EXECUTION_SUMMARY_PROMPT,
    CONTENT_SUMMARY_PROMPT,
    USER_INTENT_EXTRACTION_PROMPT
)

logger = logging.getLogger(__name__)


class MemoryCompressionService:
    """记忆压缩服务"""
    
    def __init__(self, llm: LLM, json_parser: JsonParser):
        self.llm = llm
        self.json_parser = json_parser
        self.word_boundary_size = 100  # 保留边界的词数量
    
    def parse_token_error(self, error_message: str) -> Optional[TokenInfo]:
        """解析token错误信息，提取当前token数和最大支持token数
        
        Args:
            error_message: 错误信息字符串
            
        Returns:
            TokenInfo对象，如果解析失败返回None
        """
        try:
            # 使用正则表达式提取大于2000的前两个数字
            numbers = re.findall(r'\b(\d{4,})\b', error_message)
            
            if len(numbers) >= 2:
                # 转换为整数并排序
                token_numbers = [int(num) for num in numbers[:2] if int(num) > 2000]
                
                if len(token_numbers) >= 2:
                    token_numbers.sort()
                    max_tokens = token_numbers[0]  # 较小的是最大支持token数
                    current_tokens = token_numbers[1]  # 较大的是当前请求token数
                    
                    return TokenInfo(
                        current_tokens=current_tokens,
                        max_tokens=max_tokens
                    )
        except Exception as e:
            logger.warning(f"Failed to parse token error: {error_message}, {str(e)}")
        
        return None
    
    def _estimate_tokens(self, text: str) -> int:
        """估算文本的token数量
        
        简单估算：中文字符*1.5 + 英文单词*1.3
        """
        # 统计中文字符
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        # 统计英文单词
        english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
        # 其他字符
        other_chars = len(text) - chinese_chars - english_words
        
        return int(chinese_chars * 1.5 + english_words * 1.3 + other_chars * 0.5)
    
    def segment_content(self, content: str, target_token_limit: int) -> List[ContentSegment]:
        """将内容分段，保留100词边界
        
        Args:
            content: 要分段的内容
            target_token_limit: 每段的目标token限制
            
        Returns:
            分段结果列表
        """
        segments = []
        words = content.split()
        current_segment = []
        current_tokens = 0
        segment_index = 0
        
        for i, word in enumerate(words):
            word_tokens = self._estimate_tokens(word)
            
            # 如果添加这个词会超过限制
            if current_tokens + word_tokens > target_token_limit and current_segment:
                # 检查是否可以保留边界
                preserved_boundary = True
                if len(current_segment) > self.word_boundary_size:
                    # 保留前100个词作为边界
                    segment_content = ' '.join(current_segment[:-self.word_boundary_size])
                else:
                    segment_content = ' '.join(current_segment)
                    preserved_boundary = False
                
                segments.append(ContentSegment(
                    index=segment_index,
                    content=segment_content,
                    estimated_tokens=self._estimate_tokens(segment_content),
                    preserved_boundary=preserved_boundary
                ))
                
                # 开始新段，如果保留了边界，新段从边界开始
                if preserved_boundary and len(current_segment) > self.word_boundary_size:
                    current_segment = current_segment[-self.word_boundary_size:]
                    current_tokens = sum(self._estimate_tokens(w) for w in current_segment)
                else:
                    current_segment = []
                    current_tokens = 0
                
                segment_index += 1
            
            current_segment.append(word)
            current_tokens += word_tokens
        
        # 添加最后一段
        if current_segment:
            segments.append(ContentSegment(
                index=segment_index,
                content=' '.join(current_segment),
                estimated_tokens=current_tokens,
                preserved_boundary=True
            ))
        
        return segments
    
    async def compress_by_token_limit(
        self, 
        messages: List[Dict[str, Any]], 
        token_info: TokenInfo,
        agent_type: AgentType,
        system_prompt: str
    ) -> CompressionResult:
        """基于token限制的压缩
        
        Args:
            messages: 消息列表
            token_info: Token信息
            agent_type: Agent类型
            system_prompt: 系统提示
            
        Returns:
            压缩结果
        """
        if agent_type == AgentType.PLANNER:
            return await self.compress_user_input_for_planner(messages, token_info, system_prompt)
        elif agent_type == AgentType.EXECUTION:
            # 对于execution，主要处理工具输出或记忆压缩
            return await self.compress_user_input(messages, token_info)
        else:
            # 默认处理
            return await self.compress_user_input(messages, token_info)
    
    async def compress_user_input_for_planner(
        self, 
        messages: List[Dict[str, Any]], 
        token_info: TokenInfo,
        system_prompt: str
    ) -> CompressionResult:
        """专门为planner压缩用户输入
        
        Args:
            messages: 消息列表
            token_info: Token信息
            system_prompt: planner的系统提示
            
        Returns:
            压缩结果
        """
        # 找到最新的用户消息
        user_message = None
        user_message_index = -1
        
        for i in reversed(range(len(messages))):
            if messages[i].get("role") == "user":
                user_message = messages[i]
                user_message_index = i
                break
        
        if not user_message:
            return CompressionResult(
                original_content="",
                compressed_content="",
                compression_type=CompressionType.USER_INPUT,
                original_token_count=0,
                compressed_token_count=0
            )
        
        original_content = user_message.get("content", "")
        original_tokens = self._estimate_tokens(original_content)
        
        logger.info(f"=== Compressing user input for planner: original={original_tokens} tokens ===")
        
        # 计算其他消息的token数（除了当前要压缩的用户消息）
        other_messages_tokens = 0
        for i, msg in enumerate(messages):
            if i != user_message_index:
                other_messages_tokens += self._estimate_tokens(str(msg))
        
        logger.info(f"=== Other messages tokens: {other_messages_tokens} ===")
        
        # 更保守的目标token计算：为system prompt、tools、response留出充足空间
        # 假设system prompt + tools + expected response需要约4000 tokens
        reserved_tokens = 4000
        available_tokens = token_info.max_tokens - other_messages_tokens - reserved_tokens
        
        # 用户消息最多占用可用空间的60%
        target_tokens = max(int(available_tokens * 0.6), 500)  # 最少500 tokens
        
        logger.info(f"=== Available tokens: {available_tokens}, Target tokens for user input: {target_tokens} ===")
        
        if target_tokens <= 0:
            # 如果计算出的目标token为负数，说明其他内容太多，需要极端压缩
            target_tokens = 300  # 最小压缩到300 tokens
            logger.warning(f"=== Target tokens negative, using minimal: {target_tokens} ===")
        
        # 如果原始内容已经很短，不需要压缩
        if original_tokens <= target_tokens:
            logger.info("=== Original content already short enough, no compression needed ===")
            return CompressionResult(
                original_content=original_content,
                compressed_content=original_content,
                compression_type=CompressionType.USER_INPUT,
                original_token_count=original_tokens,
                compressed_token_count=original_tokens,
                preserved_intent=original_content
            )
        
        # 使用专门的planner压缩策略
        compressed_content = await self._compress_for_planner_context(
            original_content, target_tokens, system_prompt
        )
        
        compressed_tokens = self._estimate_tokens(compressed_content)
        logger.info(f"=== Compression result: {original_tokens} -> {compressed_tokens} tokens ===")
        
        return CompressionResult(
            original_content=original_content,
            compressed_content=compressed_content,
            compression_type=CompressionType.USER_INPUT,
            original_token_count=original_tokens,
            compressed_token_count=compressed_tokens,
            preserved_intent=compressed_content
        )
    
    async def _compress_for_planner_context(
        self, 
        user_content: str, 
        target_tokens: int,
        system_prompt: str
    ) -> str:
        """基于planner上下文的压缩
        
        Args:
            user_content: 用户输入内容
            target_tokens: 目标token数
            system_prompt: planner的系统提示
            
        Returns:
            压缩后的内容
        """
        logger.info(f"=== Compressing for planner context: target={target_tokens} tokens ===")
        
        # 如果内容已经很短，直接截断
        if self._estimate_tokens(user_content) <= target_tokens:
            return user_content
        
        # 分段处理
        segments = self.segment_content(user_content, target_tokens // 2)
        
        # 使用专门为planner设计的压缩提示词
        compress_prompt = PLANNER_COMPRESSION_PROMPT_TEMPLATE.format(
            user_content=user_content[:target_tokens * 3],
            target_tokens=target_tokens
        )

        try:
            logger.info("=== Calling LLM for compression ===")
            response = await self.llm.ask([{
                "role": "user",
                "content": compress_prompt
            }])
            compressed = response.get("content", "")
            
            compressed_tokens = self._estimate_tokens(compressed)
            logger.info(f"=== LLM compression result: {compressed_tokens} tokens ===")
            
            # 如果LLM压缩后还是太长，进行截断
            if compressed_tokens > target_tokens:
                logger.warning(f"=== LLM result still too long, truncating ===")
                words = compressed.split()
                target_words = int(target_tokens * 0.7)  # 保守估计
                compressed = ' '.join(words[:target_words])
                logger.info(f"=== After truncation: {self._estimate_tokens(compressed)} tokens ===")
            
            # 确保压缩后的内容不会太短
            if self._estimate_tokens(compressed) < target_tokens // 10:
                logger.warning("=== Compression too aggressive, using fallback ===")
                # 如果压缩得太厉害，使用简单截断
                words = user_content.split()
                target_words = int(target_tokens * 0.7)
                compressed = ' '.join(words[:target_words])
            
            return compressed
            
        except Exception as e:
            logger.warning(f"Failed to compress for planner context: {str(e)}")
            # 如果压缩失败，返回截断的原文
            words = user_content.split()
            target_words = int(target_tokens * 0.7)  # 保守截断
            result = ' '.join(words[:target_words])
            logger.info(f"=== Fallback truncation: {self._estimate_tokens(result)} tokens ===")
            return result
    
    async def compress_tool_output_for_execution(
        self, 
        tool_output: str, 
        current_step_description: str, 
        token_info: TokenInfo
    ) -> CompressionResult:
        """专门为execution压缩工具输出
        
        Args:
            tool_output: 工具输出内容
            current_step_description: 当前执行的步骤描述
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(tool_output)
        target_tokens = token_info.max_tokens // 4
        
        # 分段处理
        segments = self.segment_content(tool_output, target_tokens // 2)
        
        # 为每个分段生成执行相关的摘要
        summarized_segments = []
        for segment in segments:
            summary = await self._summarize_tool_output_for_execution(
                segment.content, current_step_description
            )
            summarized_segments.append(summary)
        
        # 组合压缩后的内容
        compressed_content = f"[工具执行结果摘要 - 步骤: {current_step_description}]:\n" + "\n".join(summarized_segments)
        
        return CompressionResult(
            original_content=tool_output,
            compressed_content=compressed_content,
            compression_type=CompressionType.TOOL_OUTPUT,
            segments_processed=segments,
            original_token_count=original_tokens,
            compressed_token_count=self._estimate_tokens(compressed_content),
            summary="\n".join(summarized_segments)
        )
    
    async def _summarize_tool_output_for_execution(
        self, 
        tool_output: str, 
        step_description: str
    ) -> str:
        """为execution生成工具输出摘要"""
        prompt = TOOL_OUTPUT_EXECUTION_SUMMARY_PROMPT.format(
            step_description=step_description,
            tool_output=tool_output
        )

        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", tool_output[:300] + "...")
        except Exception as e:
            logger.warning(f"Failed to summarize tool output for execution: {str(e)}")
            return tool_output[:300] + "..."

    async def summarize_content(self, content: str, context: str = "") -> str:
        """生成内容摘要
        
        Args:
            content: 要摘要的内容
            context: 上下文信息（如当前执行的任务）
            
        Returns:
            生成的摘要
        """
        prompt = CONTENT_SUMMARY_PROMPT.format(
            context=context if context else "无特定上下文",
            content=content
        )

        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", content[:200] + "...")
        except Exception as e:
            logger.warning(f"Failed to generate summary: {str(e)}")
            # 如果摘要生成失败，返回截断的原文
            return content[:200] + "..."
    
    async def extract_user_intent(self, user_input: str) -> str:
        """提取并保留用户意图
        
        Args:
            user_input: 用户输入的原始文本
            
        Returns:
            提取的用户意图
        """
        prompt = USER_INTENT_EXTRACTION_PROMPT.format(
            user_input=user_input
        )

        try:
            response = await self.llm.ask([{
                "role": "user", 
                "content": prompt
            }])
            return response.get("content", user_input[-500:])
        except Exception as e:
            logger.warning(f"Failed to extract user intent: {str(e)}")
            # 如果意图提取失败，返回输入的最后500字符
            return user_input[-500:]
    
    async def compress_user_input(self, messages: List[Dict[str, Any]], token_info: TokenInfo) -> CompressionResult:
        """压缩用户输入内容（通用版本）
        
        Args:
            messages: 消息列表
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        # 找到最新的用户消息
        user_message = None
        user_message_index = -1
        
        for i in reversed(range(len(messages))):
            if messages[i].get("role") == "user":
                user_message = messages[i]
                user_message_index = i
                break
        
        if not user_message:
            # 没有找到用户消息，返回空压缩结果
            return CompressionResult(
                original_content="",
                compressed_content="",
                compression_type=CompressionType.USER_INPUT,
                original_token_count=0,
                compressed_token_count=0
            )
        
        original_content = user_message.get("content", "")
        original_tokens = self._estimate_tokens(original_content)
        
        # 计算需要压缩到的目标大小
        target_tokens = token_info.max_tokens - (token_info.current_tokens - original_tokens) - 500  # 留500token缓冲
        
        if target_tokens <= 0:
            target_tokens = token_info.max_tokens // 4  # 压缩到最大token的1/4
        
        # 分段处理
        segments = self.segment_content(original_content, target_tokens // 2)
        
        # 提取用户意图
        user_intent = await self.extract_user_intent(original_content)
        
        # 为每个分段生成摘要
        summarized_segments = []
        for segment in segments:
            summary = await self.summarize_content(segment.content, "用户输入内容")
            summarized_segments.append(summary)
        
        # 组合压缩后的内容
        compressed_content = f"[用户意图]: {user_intent}\n\n[内容摘要]: " + "\n".join(summarized_segments)
        
        return CompressionResult(
            original_content=original_content,
            compressed_content=compressed_content,
            compression_type=CompressionType.USER_INPUT,
            segments_processed=segments,
            original_token_count=original_tokens,
            compressed_token_count=self._estimate_tokens(compressed_content),
            preserved_intent=user_intent,
            summary="\n".join(summarized_segments)
        )
    
    async def compress_tool_output(self, tool_output: str, current_task: str, token_info: TokenInfo) -> CompressionResult:
        """压缩工具输出内容
        
        Args:
            tool_output: 工具输出内容
            current_task: 当前执行的任务描述
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(tool_output)
        
        # 计算目标压缩大小
        target_tokens = token_info.max_tokens // 4  # 压缩到最大token的1/4
        
        # 分段处理
        segments = self.segment_content(tool_output, target_tokens // 2)
        
        # 为每个分段生成任务相关的摘要
        summarized_segments = []
        for segment in segments:
            context = f"当前执行任务: {current_task}"
            summary = await self.summarize_content(segment.content, context)
            summarized_segments.append(summary)
        
        # 组合压缩后的内容
        compressed_content = f"[工具输出摘要 - 任务: {current_task}]:\n" + "\n".join(summarized_segments)
        
        return CompressionResult(
            original_content=tool_output,
            compressed_content=compressed_content,
            compression_type=CompressionType.TOOL_OUTPUT,
            segments_processed=segments,
            original_token_count=original_tokens,
            compressed_token_count=self._estimate_tokens(compressed_content),
            summary="\n".join(summarized_segments)
        ) 