from app.domain.models.exceptions import TokenLimitExceededError as DomainTokenLimitExceededError


class AppException(RuntimeError):
    def __init__(
        self,
        code: int,
        msg: str,
        status_code: int = 400,
    ):
        super().__init__(msg)
        self.code = code
        self.msg = msg
        self.status_code = status_code


class NotFoundError(AppException):
    def __init__(self, msg: str = "Resource not found"):
        super().__init__(code=404, msg=msg, status_code=404)


class BadRequestError(AppException):
    def __init__(self, msg: str = "Bad request parameters"):
        super().__init__(code=400, msg=msg, status_code=400)


class ServerError(AppException):
    def __init__(self, msg: str = "Internal server error"):
        super().__init__(code=500, msg=msg, status_code=500)


class UnauthorizedError(AppException):
    def __init__(self, msg: str = "Unauthorized"):
        super().__init__(code=401, msg=msg, status_code=401)


class TokenLimitExceededError(AppException, DomainTokenLimitExceededError):
    """应用层Token限制异常，继承领域异常并添加HTTP状态码"""
    def __init__(self, msg: str, current_tokens: int, max_tokens: int):
        AppException.__init__(self, code=429, msg=msg, status_code=429)
        DomainTokenLimitExceededError.__init__(self, message=msg, current_tokens=current_tokens, max_tokens=max_tokens) 