"""
领域层异常定义
遵循DDD架构规范，领域层异常不依赖其他层
"""

class DomainException(Exception):
    """领域异常基类"""
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class TokenLimitExceededError(DomainException):
    """Token限制超出异常（领域异常）"""
    def __init__(self, message: str, current_tokens: int, max_tokens: int):
        super().__init__(message)
        self.current_tokens = current_tokens
        self.max_tokens = max_tokens 