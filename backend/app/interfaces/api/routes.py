from fastapi import APIRouter
from . import session_routes, file_routes, auth_routes, tool_routes, health_routes


def create_api_router() -> APIRouter:
    """Create and configure the main API router"""
    api_router = APIRouter()

    # Include all sub-routers
    api_router.include_router(health_routes.router)
    api_router.include_router(session_routes.router)
    api_router.include_router(file_routes.router)
    api_router.include_router(auth_routes.router)
    api_router.include_router(tool_routes.router)

    return api_router


# Create the main router instance
router = create_api_router() 