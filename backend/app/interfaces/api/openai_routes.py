"""
OpenAI-compatible API proxy for manus-claw.
All LLM requests from OpenClaw containers go through this endpoint,
authenticated using per-user API keys.
"""
import logging
import json
from typing import Optional, AsyncIterator
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

from app.application.services.claw_service import ClawService
from app.core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["openai-proxy"])


def _extract_bearer_token(request: Request) -> Optional[str]:
    """Extract Bearer token from Authorization header"""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[7:]
    return None


async def _get_claw_service() -> ClawService:
    from app.interfaces.dependencies import get_claw_service
    return get_claw_service()


async def _stream_llm_response(
    request_body: dict,
    settings,
) -> AsyncIterator[bytes]:
    """Stream LLM response from the configured backend"""
    api_base = settings.api_base or "https://api.openai.com"
    api_key = settings.api_key
    extra_headers = settings.extra_headers or {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        **extra_headers,
    }

    target_url = f"{api_base.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            target_url,
            json=request_body,
            headers=headers,
        ) as resp:
            if not resp.is_success:
                error_body = await resp.aread()
                error_msg = error_body.decode("utf-8", errors="replace")
                sse_error = (
                    f'data: {json.dumps({"error": {"message": f"LLM backend error: {error_msg}", "type": "api_error"}})}\n\n'
                    f"data: [DONE]\n\n"
                )
                yield sse_error.encode("utf-8")
                return

            async for chunk in resp.aiter_bytes():
                if chunk:
                    yield chunk


async def _get_llm_response(
    request_body: dict,
    settings,
) -> dict:
    """Get non-streaming LLM response"""
    api_base = settings.api_base or "https://api.openai.com"
    api_key = settings.api_key
    extra_headers = settings.extra_headers or {}

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        **extra_headers,
    }

    target_url = f"{api_base.rstrip('/')}/chat/completions"

    async with httpx.AsyncClient(timeout=120.0) as client:
        resp = await client.post(target_url, json=request_body, headers=headers)
        resp.raise_for_status()
        return resp.json()


def _openai_error_response(status_code: int, message: str, error_type: str) -> JSONResponse:
    """Return an OpenAI-compatible error JSON response directly, bypassing the global handler."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"message": message, "type": error_type}},
    )


@router.post("/v1/chat/completions")
async def chat_completions(request: Request):
    """
    OpenAI-compatible chat completions proxy.
    Authenticates using per-user manus API keys and forwards to the configured LLM backend.
    """
    api_key = _extract_bearer_token(request)
    if not api_key:
        return _openai_error_response(status.HTTP_401_UNAUTHORIZED, "Missing API key", "auth_error")

    # Verify API key and get user
    claw_service = await _get_claw_service()
    user_id = await claw_service.verify_api_key(api_key)
    if not user_id:
        return _openai_error_response(status.HTTP_401_UNAUTHORIZED, "Invalid API key", "auth_error")

    try:
        body = await request.json()
    except Exception:
        return _openai_error_response(status.HTTP_400_BAD_REQUEST, "Invalid request body", "invalid_request_error")

    settings = get_settings()

    # Override model with configured model name
    if settings.model_name and body.get("model") in ("default", "manus-proxy/default", None):
        body = {**body, "model": settings.model_name}

    is_stream = body.get("stream", False)

    logger.info(f"[openai-proxy] user={user_id} model={body.get('model')} stream={is_stream}")

    try:
        if is_stream:
            return StreamingResponse(
                _stream_llm_response(body, settings),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            result = await _get_llm_response(body, settings)
            return JSONResponse(content=result)

    except httpx.HTTPStatusError as e:
        logger.error(f"[openai-proxy] LLM backend error: {e.response.status_code} {e.response.text}")
        return _openai_error_response(e.response.status_code, f"LLM backend error: {e.response.text}", "api_error")
    except Exception as e:
        logger.error(f"[openai-proxy] Unexpected error: {str(e)}")
        return _openai_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, str(e), "api_error")
