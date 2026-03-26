from fastapi import APIRouter

from app.core.config import get_settings
from app.interfaces.schemas.base import APIResponse
from app.interfaces.schemas.config import ClientConfigResponse

router = APIRouter(prefix="/config", tags=["config"])


@router.get("/frontend", response_model=APIResponse[ClientConfigResponse])
async def get_frontend_config() -> APIResponse[ClientConfigResponse]:
    """Get frontend runtime config."""
    settings = get_settings()

    return APIResponse.success(
        ClientConfigResponse(
            auth_provider=settings.auth_provider,
            show_github_button=settings.show_github_button,
            github_repository_url=settings.github_repository_url,
            google_analytics_id=settings.google_analytics_id,
        )
    )
