from fastapi import APIRouter

from app.schemas.response import Response
from app.schemas.supervisor import TimeoutRequest
from app.services.supervisor import supervisor_service

router = APIRouter()

@router.get("/status", response_model=Response)
async def get_status():
    """
    Get status of all services
    """
    processes = await supervisor_service.get_all_processes()
    return Response(
        success=True,
        message="Services status retrieved successfully",
        data=[process.model_dump() for process in processes]
    )

@router.post("/stop", response_model=Response)
async def stop_services():
    """
    Stop all services
    """
    result = await supervisor_service.stop_all_services()
    return Response(
        success=True,
        message="All services stopped",
        data=result.model_dump()
    )

@router.post("/shutdown", response_model=Response)
async def shutdown_supervisor():
    """
    Shutdown only the supervisord service itself
    """
    result = await supervisor_service.shutdown()
    return Response(
        success=True,
        message="Supervisord service shutdown",
        data=result.model_dump()
    )

@router.post("/restart", response_model=Response)
async def restart_services():
    """
    Restart all services
    """
    result = await supervisor_service.restart_all_services()
    return Response(
        success=True,
        message="All services restarted",
        data=result.model_dump()
    )

@router.post("/timeout/activate", response_model=Response)
async def activate_timeout(request: TimeoutRequest):
    """
    Reset timeout feature, automatically shut down all services after the specified time
    
    minutes: Optional, timeout duration (minutes), if not provided, system default configuration will be used
    """
    result = await supervisor_service.activate_timeout(request.minutes)
    # Disable auto-extend since user explicitly controls timeout
    supervisor_service.disable_auto_extend()
    return Response(
        success=True,
        message=f"Timeout reset, all services will be shut down after {result.timeout_minutes} minutes",
        data=result.model_dump()
    )

@router.post("/timeout/extend", response_model=Response)
async def extend_timeout(request: TimeoutRequest):
    """
    Extend timeout duration
    
    minutes: Optional, number of minutes to extend, if not provided, system default configuration will be used
    """
    result = await supervisor_service.extend_timeout(request.minutes)
    # Disable auto-extend since user explicitly controls timeout
    supervisor_service.disable_auto_extend()
    return Response(
        success=True,
        message=f"Timeout extended, all services will be shut down after {result.timeout_minutes} minutes",
        data=result.model_dump()
    )

@router.post("/timeout/cancel", response_model=Response)
async def cancel_timeout():
    """
    Cancel timeout feature
    """
    result = await supervisor_service.cancel_timeout()
    return Response(
        success=True,
        message="Timeout cancelled" if result.status == "timeout_cancelled" else "No active timeout",
        data=result.model_dump()
    )

@router.get("/timeout/status", response_model=Response)
async def get_timeout_status():
    """
    Get timeout status
    """
    result = await supervisor_service.get_timeout_status()
    message = "No active timeout" if not result.active else f"Remaining time: {result.remaining_seconds // 60} minutes"
    return Response(
        success=True,
        message=message,
        data=result.model_dump()
    ) 