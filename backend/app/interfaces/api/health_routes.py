"""Health check endpoints for monitoring and orchestration"""
from fastapi import APIRouter, Depends
from datetime import datetime, UTC
from typing import Any
import logging

from app.core.config import get_settings
from app.infrastructure.storage.mongodb import get_mongodb
from app.infrastructure.storage.redis import get_redis
from app.interfaces.schemas.base import APIResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=APIResponse)
async def health_check() -> APIResponse:
    """Basic health check - returns OK if the service is running"""
    return APIResponse(
        code=0,
        msg="OK",
        data={
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat()
        }
    )


@router.get("/ready", response_model=APIResponse)
async def readiness_check() -> APIResponse:
    """Readiness check - verifies all dependencies are available"""
    settings = get_settings()
    checks = {
        "mongodb": False,
        "redis": False,
        "timestamp": datetime.now(UTC).isoformat()
    }
    all_healthy = True

    # Check MongoDB connection
    try:
        mongodb = get_mongodb()
        if mongodb.client:
            await mongodb.client.admin.command('ping')
            checks["mongodb"] = True
    except Exception as e:
        logger.warning(f"MongoDB health check failed: {e}")
        all_healthy = False

    # Check Redis connection
    try:
        redis = get_redis()
        if redis.client:
            await redis.client.ping()
            checks["redis"] = True
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        all_healthy = False

    status = "ready" if all_healthy else "degraded"
    status_code = 0 if all_healthy else 503

    return APIResponse(
        code=status_code,
        msg=status.upper(),
        data={
            "status": status,
            "checks": checks
        }
    )


@router.get("/live", response_model=APIResponse)
async def liveness_check() -> APIResponse:
    """Liveness check - basic check that the service is alive"""
    return APIResponse(
        code=0,
        msg="OK",
        data={
            "status": "alive",
            "timestamp": datetime.now(UTC).isoformat()
        }
    )


@router.get("/info", response_model=APIResponse)
async def service_info() -> APIResponse:
    """Service information endpoint"""
    settings = get_settings()
    return APIResponse(
        code=0,
        msg="OK",
        data={
            "service": "Manus AI Agent",
            "version": "1.0.0",
            "environment": settings.environment,
            "timestamp": datetime.now(UTC).isoformat()
        }
    )
