from fastapi import APIRouter
from . import session_routes, file_routes, auth_routes, config_routes, claw_routes

def create_api_router() -> APIRouter:
    """Create and configure the main API router"""
    api_router = APIRouter()
    
    # Include all sub-routers
    api_router.include_router(session_routes.router)
    api_router.include_router(file_routes.router)
    api_router.include_router(auth_routes.router)
    api_router.include_router(config_routes.router)
    api_router.include_router(claw_routes.router)
    
    return api_router

# Create the main router instance
router = create_api_router() 