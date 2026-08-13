import logging
from fastapi import Request

from app.core.config import settings

logger = logging.getLogger(__name__)


async def auto_extend_timeout_middleware(request: Request, call_next):
    """
    Middleware to automatically extend timeout on every API request.
    Only auto-extends when enabled (disabled when user explicitly manages timeout).
    """
    # Imported lazily to avoid connecting to supervisord at module import time
    from app.services.supervisor import supervisor_service

    # Only extend timeout if timeout is currently active, it's an API request,
    # and not a timeout management API call, and auto-extend is enabled
    if (settings.SERVICE_TIMEOUT_MINUTES is not None and
        supervisor_service.timeout_active and
        request.url.path.startswith("/api/") and
        not request.url.path.startswith("/api/v1/supervisor/timeout/") and
        supervisor_service.auto_extend_enabled):
        try:
            await supervisor_service.extend_timeout()
            logger.debug("Timeout automatically extended due to API request: %s", request.url.path)
        except Exception as e:
            logger.warning("Failed to auto-extend timeout: %s", str(e))

    return await call_next(request) 