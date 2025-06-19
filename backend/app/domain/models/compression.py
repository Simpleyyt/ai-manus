from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class AgentType(str, Enum):
    """Agent类型枚举"""
    PLANNER = "planner"
    EXECUTION = "execution"


class CompressionType(str, Enum):
    """压缩类型枚举"""
    USER_INPUT = "user_input"
    TOOL_OUTPUT = "tool_output"
    MEMORY_CLEANUP = "memory_cleanup"


class TokenInfo(BaseModel):
    """Token信息模型"""
    current_tokens: int
    max_tokens: int
    
    @property
    def available_tokens(self) -> int:
        """可用token数量"""
        return max(0, self.max_tokens - self.current_tokens)
    
    @property
    def usage_ratio(self) -> float:
        """使用率"""
        return self.current_tokens / self.max_tokens if self.max_tokens > 0 else 0.0


class ContentSegment(BaseModel):
    """内容分段模型"""
    index: int
    content: str
    estimated_tokens: int
    preserved_boundary: bool = True  # 是否保留了完整边界
    
    
class CompressionResult(BaseModel):
    """压缩结果模型"""
    original_content: str
    compressed_content: str
    compression_type: CompressionType
    segments_processed: List[ContentSegment] = []
    original_token_count: int
    compressed_token_count: int
    preserved_intent: Optional[str] = None  # 保留的用户意图
    summary: Optional[str] = None  # 生成的摘要
    
    @property
    def compression_ratio(self) -> float:
        """压缩比例"""
        if self.original_token_count == 0:
            return 0.0
        return (self.original_token_count - self.compressed_token_count) / self.original_token_count
    
    @property
    def token_saved(self) -> int:
        """节省的token数量"""
        return self.original_token_count - self.compressed_token_count 