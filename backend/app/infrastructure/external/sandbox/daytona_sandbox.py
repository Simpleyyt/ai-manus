"""Daytona sandbox provider adapter.

Daytona offers cloud dev environments with API. Mentioned in Landis API essentials:

    Daytona: dtn_971a876f924679498453ee48d1f2af9e23a8f812926cc481b75909c1fe633d8f

Daytona open-source was archived June 2026 (per guia prático), but managed
service remains. This scaffold keeps the integration point for users with credits.

Set:
    SANDBOX_PROVIDER=daytona
    DAYTONA_API_KEY=dtn_...
"""

import logging

logger = logging.getLogger(__name__)


class DaytonaSandboxAdapter:
    """Placeholder adapter for Daytona sandboxes."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key
        self.base_url = base_url or "https://app.daytona.io/api"
        self.provider = "daytona"

    async def create(self, timeout_minutes: int = 60):
        logger.info(f"[Daytona] would create sandbox (key={'set' if self.api_key else 'missing'})")
        raise NotImplementedError(
            "Daytona provider scaffold — implement via Daytona SDK. "
            "Falling back to Docker. Set SANDBOX_PROVIDER=docker or unset DAYTONA_API_KEY."
        )
