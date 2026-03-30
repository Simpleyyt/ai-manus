from pydantic import BaseModel


class ClientConfigResponse(BaseModel):
    """Client runtime configuration response schema"""
    auth_provider: str
    show_github_button: bool
    github_repository_url: str
    google_analytics_id: str | None = None
    claw_enabled: bool
