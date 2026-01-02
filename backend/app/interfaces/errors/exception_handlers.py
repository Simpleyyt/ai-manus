from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import logging
import uuid
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.application.errors.exceptions import AppException
from app.interfaces.schemas.base import APIResponse
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _generate_request_id() -> str:
    """Generate a unique request ID for error tracking"""
    return str(uuid.uuid4())[:8]


def _get_user_friendly_message(status_code: int, detail: str = None) -> str:
    """Convert technical errors to user-friendly messages"""
    messages = {
        400: "The request could not be processed. Please check your input.",
        401: "Please sign in to continue.",
        403: "You don't have permission to access this resource.",
        404: "The requested resource was not found.",
        422: "Please check your input and try again.",
        429: "Too many requests. Please wait a moment and try again.",
        500: "Something went wrong. Please try again later.",
        502: "The service is temporarily unavailable. Please try again later.",
        503: "The service is under maintenance. Please try again later.",
    }
    return messages.get(status_code, detail or "An error occurred.")


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers"""
    settings = get_settings()

    @app.exception_handler(AppException)
    async def api_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle custom API exceptions"""
        request_id = _generate_request_id()
        logger.warning(
            f"APIException [{request_id}]: {exc.msg} | "
            f"Path: {request.url.path} | Method: {request.method}"
        )

        # In production, return user-friendly messages
        message = exc.msg
        if settings.is_production and exc.status_code >= 500:
            message = _get_user_friendly_message(exc.status_code)

        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                code=exc.code,
                msg=message,
                data={"request_id": request_id} if exc.status_code >= 500 else None
            ).model_dump(),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle request validation errors with user-friendly messages"""
        request_id = _generate_request_id()

        # Extract meaningful error details
        errors = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error.get("loc", []))
            msg = error.get("msg", "Invalid value")
            errors.append(f"{field}: {msg}")

        error_summary = "; ".join(errors[:3])  # Limit to first 3 errors
        if len(errors) > 3:
            error_summary += f" (and {len(errors) - 3} more)"

        logger.warning(
            f"ValidationError [{request_id}]: {error_summary} | "
            f"Path: {request.url.path} | Method: {request.method}"
        )

        return JSONResponse(
            status_code=422,
            content=APIResponse(
                code=422,
                msg=f"Validation error: {error_summary}",
                data={"errors": errors} if not settings.is_production else None
            ).model_dump(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions"""
        request_id = _generate_request_id()
        logger.warning(
            f"HTTPException [{request_id}]: {exc.detail} | "
            f"Path: {request.url.path} | Method: {request.method} | Status: {exc.status_code}"
        )

        message = exc.detail
        if settings.is_production:
            message = _get_user_friendly_message(exc.status_code, exc.detail)

        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse(
                code=exc.status_code,
                msg=message,
                data=None
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle all uncaught exceptions"""
        request_id = _generate_request_id()
        logger.exception(
            f"UnhandledException [{request_id}]: {type(exc).__name__}: {str(exc)} | "
            f"Path: {request.url.path} | Method: {request.method}"
        )

        # Never expose internal error details in production
        message = _get_user_friendly_message(500)

        return JSONResponse(
            status_code=500,
            content=APIResponse(
                code=500,
                msg=message,
                data={"request_id": request_id}
            ).model_dump(),
        ) 