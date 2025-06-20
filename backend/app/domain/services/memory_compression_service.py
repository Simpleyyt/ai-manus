import re
import logging
from typing import List, Dict, Any, Optional, Tuple, AsyncGenerator
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
    USER_INTENT_EXTRACTION_PROMPT,
    SEGMENT_SUMMARY_PROMPT,
    COMBINE_SUMMARIES_PROMPT
)

logger = logging.getLogger(__name__)


class MemoryCompressionService:
    """记忆压缩服务 - 负责处理超长文本的智能压缩和分段"""
    
    def __init__(self, llm: LLM, json_parser: JsonParser):
        self.llm = llm
        self.json_parser = json_parser
        self.word_boundary_size = 100  # 保留边界的词数量
        self.segment_target_tokens = 2000  # 每个分段的目标token数
        self.summary_context_size = 500  # 摘要上下文的目标大小
    
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
        """将内容分段，保留边界以保持上下文连贯性
        
        Args:
            content: 要分段的内容
            target_token_limit: 每段的目标token限制
            
        Returns:
            分段结果列表
        """
        segments = []
        words = content.split()
        
        if not words:
            return segments
        
        current_segment = []
        current_tokens = 0
        segment_index = 0
        overlap_words = []  # 用于存储重叠部分
        
        for i, word in enumerate(words):
            word_tokens = self._estimate_tokens(word)
            
            # 如果添加这个词会超过限制
            if current_tokens + word_tokens > target_token_limit and current_segment:
                # 保存当前段的最后部分作为下一段的开始（重叠）
                if len(current_segment) >= self.word_boundary_size:
                    overlap_words = current_segment[-self.word_boundary_size:]
                    segment_content = ' '.join(current_segment)
                else:
                    overlap_words = current_segment[:]
                    segment_content = ' '.join(current_segment)
                
                segments.append(ContentSegment(
                    index=segment_index,
                    content=segment_content,
                    estimated_tokens=self._estimate_tokens(segment_content),
                    preserved_boundary=True
                ))
                
                # 开始新段，包含重叠部分
                current_segment = overlap_words + [word]
                current_tokens = sum(self._estimate_tokens(w) for w in current_segment)
                segment_index += 1
            else:
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
    
    async def process_long_content_in_segments(
        self,
        content: str,
        content_type: str,  # "user_input" 或 "tool_output"
        context: str,  # 任务上下文
        max_tokens: int
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """分段处理超长内容，每段都包含历史摘要
        
        Args:
            content: 超长内容
            content_type: 内容类型
            context: 任务上下文
            max_tokens: 最大token限制
            
        Yields:
            每个分段的处理结果
        """
        # 计算合理的分段大小
        # 需要为历史摘要、系统提示等预留空间
        reserved_tokens = int(max_tokens * 0.5)  # 预留50%空间
        segment_size = max_tokens - reserved_tokens
        
        # 将内容分段
        segments = self.segment_content(content, segment_size)
        total_segments = len(segments)
        
        if total_segments == 0:
            return
        
        # 累积的历史摘要
        accumulated_summary = ""
        
        for i, segment in enumerate(segments):
            # 构造当前段的输入
            if i == 0:
                # 第一段，没有历史摘要
                current_input = {
                    "segment_index": i + 1,
                    "total_segments": total_segments,
                    "content": segment.content,
                    "context": context,
                    "has_history": False,
                    "history_summary": ""
                }
            else:
                # 后续段，包含历史摘要
                current_input = {
                    "segment_index": i + 1,
                    "total_segments": total_segments,
                    "content": segment.content,
                    "context": context,
                    "has_history": True,
                    "history_summary": accumulated_summary
                }
            
            # 生成当前段的摘要
            segment_summary = await self._generate_segment_summary(
                segment.content,
                context,
                accumulated_summary,
                i + 1,
                total_segments
            )
            
            # 更新累积摘要
            if accumulated_summary:
                # 合并摘要，保持在合理长度内
                accumulated_summary = await self._combine_summaries(
                    accumulated_summary,
                    segment_summary,
                    self.summary_context_size
                )
            else:
                accumulated_summary = segment_summary
            
            # 返回当前段的处理结果
            yield {
                "type": "segment",
                "index": i,
                "total": total_segments,
                "content": current_input,
                "summary": segment_summary
            }
        
        # 最后返回完整的摘要
        yield {
            "type": "final_summary",
            "summary": accumulated_summary,
            "total_segments": total_segments
        }
    
    async def _generate_segment_summary(
        self,
        segment_content: str,
        context: str,
        previous_summary: str,
        segment_index: int,
        total_segments: int
    ) -> str:
        """为单个分段生成摘要
        
        Args:
            segment_content: 分段内容
            context: 任务上下文
            previous_summary: 之前的摘要
            segment_index: 当前段索引
            total_segments: 总段数
            
        Returns:
            生成的摘要
        """
        prompt = SEGMENT_SUMMARY_PROMPT.format(
            context=context,
            previous_summary=previous_summary if previous_summary else "无",
            segment_index=segment_index,
            total_segments=total_segments,
            segment_content=segment_content
        )
        
        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", segment_content[:200] + "...")
        except Exception as e:
            logger.warning(f"Failed to generate segment summary: {str(e)}")
            return segment_content[:200] + "..."
    
    async def _combine_summaries(
        self,
        previous_summary: str,
        new_summary: str,
        target_length: int
    ) -> str:
        """合并两个摘要，保持在目标长度内
        
        Args:
            previous_summary: 之前的摘要
            new_summary: 新的摘要
            target_length: 目标长度（token数）
            
        Returns:
            合并后的摘要
        """
        # 如果两个摘要都很短，直接合并
        combined = f"{previous_summary}\n\n{new_summary}"
        if self._estimate_tokens(combined) <= target_length:
            return combined
        
        # 否则需要压缩合并
        prompt = COMBINE_SUMMARIES_PROMPT.format(
            previous_summary=previous_summary,
            new_summary=new_summary,
            target_tokens=target_length
        )
        
        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            return response.get("content", combined[:target_length])
        except Exception as e:
            logger.warning(f"Failed to combine summaries: {str(e)}")
            # 简单截断
            return combined[:target_length]
    
    async def compress_for_immediate_use(
        self,
        content: str,
        content_type: str,
        context: str,
        token_info: TokenInfo,
        agent_type: AgentType
    ) -> CompressionResult:
        """压缩内容以便立即使用（不分段，直接压缩到合适大小）
        
        这是现有压缩逻辑的改进版本，当不需要分段处理时使用
        
        Args:
            content: 要压缩的内容
            content_type: 内容类型 ("user" 或 "tool")
            context: 任务上下文
            token_info: Token信息
            agent_type: Agent类型
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(content)
        
        # 根据agent类型和内容类型选择压缩策略
        if agent_type == AgentType.PLANNER and content_type == "user":
            return await self.compress_user_input_for_planner(
                content, context, token_info
            )
        elif agent_type == AgentType.EXECUTION and content_type == "tool":
            return await self.compress_tool_output_for_execution(
                content, context, token_info
            )
        else:
            # 通用压缩
            return await self.compress_content_general(
                content, content_type, context, token_info
            )
    
    async def compress_user_input_for_planner(
        self, 
        content: str,
        context: str,
        token_info: TokenInfo
    ) -> CompressionResult:
        """专门为planner压缩用户输入（改进版）
        
        Args:
            content: 用户输入内容
            context: 任务上下文
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(content)
        
        # 计算目标大小
        # 为系统提示词、工具定义、响应等预留空间
        reserved_tokens = 4000
        available_tokens = token_info.max_tokens - reserved_tokens
        target_tokens = max(int(available_tokens * 0.6), 500)
        
        # 如果已经足够短，不压缩
        if original_tokens <= target_tokens:
            return CompressionResult(
                original_content=content,
                compressed_content=content,
                compression_type=CompressionType.USER_INPUT,
                original_token_count=original_tokens,
                compressed_token_count=original_tokens,
                preserved_intent=content
            )
        
        # 使用planner专用压缩提示词
        compress_prompt = PLANNER_COMPRESSION_PROMPT_TEMPLATE.format(
            user_content=content[:target_tokens * 3],  # 限制输入长度
            target_tokens=target_tokens
        )
        
        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": compress_prompt
            }])
            compressed = response.get("content", "")
            
            # 确保压缩结果在目标范围内
            compressed_tokens = self._estimate_tokens(compressed)
            if compressed_tokens > target_tokens:
                # 截断到目标大小
                words = compressed.split()
                target_words = int(target_tokens * 0.7)
                compressed = ' '.join(words[:target_words])
            
            return CompressionResult(
                original_content=content,
                compressed_content=compressed,
                compression_type=CompressionType.USER_INPUT,
                original_token_count=original_tokens,
                compressed_token_count=self._estimate_tokens(compressed),
                preserved_intent=compressed
            )
            
        except Exception as e:
            logger.warning(f"Failed to compress for planner: {str(e)}")
            # 回退到简单截断
            words = content.split()
            target_words = int(target_tokens * 0.7)
            truncated = ' '.join(words[:target_words])
            
            return CompressionResult(
                original_content=content,
                compressed_content=truncated,
                compression_type=CompressionType.USER_INPUT,
                original_token_count=original_tokens,
                compressed_token_count=self._estimate_tokens(truncated)
            )
    
    async def compress_tool_output_for_execution(
        self, 
        content: str,
        context: str,
        token_info: TokenInfo
    ) -> CompressionResult:
        """专门为execution压缩工具输出（改进版）
        
        Args:
            content: 工具输出内容
            context: 当前执行的步骤描述
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(content)
        target_tokens = token_info.max_tokens // 4
        
        # 使用专门的工具输出压缩提示词
        prompt = TOOL_OUTPUT_EXECUTION_SUMMARY_PROMPT.format(
            step_description=context,
            tool_output=content[:target_tokens * 3]  # 限制输入长度
        )
        
        try:
            response = await self.llm.ask([{
                "role": "user",
                "content": prompt
            }])
            summary = response.get("content", content[:300] + "...")
            
            # 构造压缩后的内容
            compressed_content = f"[工具执行结果摘要 - 步骤: {context}]:\n{summary}"
            
            return CompressionResult(
                original_content=content,
                compressed_content=compressed_content,
                compression_type=CompressionType.TOOL_OUTPUT,
                original_token_count=original_tokens,
                compressed_token_count=self._estimate_tokens(compressed_content),
                summary=summary
            )
            
        except Exception as e:
            logger.warning(f"Failed to compress tool output: {str(e)}")
            # 回退到简单截断
            truncated = content[:target_tokens * 2] + "..."
            compressed_content = f"[工具输出截断 - 步骤: {context}]:\n{truncated}"
            
            return CompressionResult(
                original_content=content,
                compressed_content=compressed_content,
                compression_type=CompressionType.TOOL_OUTPUT,
                original_token_count=original_tokens,
                compressed_token_count=self._estimate_tokens(compressed_content)
            )
    
    async def compress_content_general(
        self,
        content: str,
        content_type: str,
        context: str,
        token_info: TokenInfo
    ) -> CompressionResult:
        """通用内容压缩
        
        Args:
            content: 要压缩的内容
            content_type: 内容类型
            context: 上下文
            token_info: Token信息
            
        Returns:
            压缩结果
        """
        original_tokens = self._estimate_tokens(content)
        
        # 计算目标大小
        available_tokens = token_info.max_tokens - token_info.current_tokens + original_tokens
        target_tokens = max(available_tokens - 500, token_info.max_tokens // 4)  # 留500的缓冲
        
        # 提取关键信息
        if content_type == "user":
            intent = await self.extract_user_intent(content)
            prefix = f"[用户意图]: {intent}\n\n[内容摘要]: "
        else:
            prefix = f"[{content_type}内容摘要 - {context}]: "
        
        # 生成摘要
        summary = await self.summarize_content(content[:target_tokens * 3], context)
        compressed_content = prefix + summary
        
        return CompressionResult(
            original_content=content,
            compressed_content=compressed_content,
            compression_type=CompressionType.USER_INPUT if content_type == "user" else CompressionType.TOOL_OUTPUT,
            original_token_count=original_tokens,
            compressed_token_count=self._estimate_tokens(compressed_content),
            preserved_intent=intent if content_type == "user" else None,
            summary=summary
        )
    
    async def extract_user_intent(self, user_input: str) -> str:
        """提取用户意图（保持原有实现）"""
        prompt = USER_INTENT_EXTRACTION_PROMPT.format(
            user_input=user_input[:1000]  # 限制长度
        )
        
        try:
            response = await self.llm.ask([{
                "role": "user", 
                "content": prompt
            }])
            return response.get("content", user_input[:500])
        except Exception as e:
            logger.warning(f"Failed to extract user intent: {str(e)}")
            return user_input[:500]
    
    async def summarize_content(self, content: str, context: str = "") -> str:
        """生成内容摘要（保持原有实现）"""
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
            return content[:200] + "..."
    
    # 保持向后兼容的方法
    async def compress_by_token_limit(
        self, 
        messages: List[Dict[str, Any]], 
        token_info: TokenInfo,
        agent_type: AgentType,
        system_prompt: str
    ) -> CompressionResult:
        """基于token限制的压缩（兼容旧接口）
        
        找到最新的用户消息并压缩
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
        
        content = user_message.get("content", "")
        
        # 使用新的压缩方法
        return await self.compress_for_immediate_use(
            content=content,
            content_type="user",
            context="用户输入",
            token_info=token_info,
            agent_type=agent_type
        )
    
    async def compress_user_input(self, messages: List[Dict[str, Any]], token_info: TokenInfo) -> CompressionResult:
        """压缩用户输入（兼容旧接口）"""
        return await self.compress_by_token_limit(messages, token_info, AgentType.EXECUTION, "")
    
    async def compress_tool_output(self, tool_output: str, current_task: str, token_info: TokenInfo) -> CompressionResult:
        """压缩工具输出（兼容旧接口）"""
        return await self.compress_tool_output_for_execution(tool_output, current_task, token_info) 