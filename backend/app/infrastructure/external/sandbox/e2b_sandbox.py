"""E2B sandbox provider adapter.

E2B provides cloud sandboxes with credits (free tier ~ $100 or 1h sessions).
The original Manus used E2B Firecracker VMs (see e2b.dev/customers/how-manus-uses-e2b).

In the replica, this provider is used when SANDBOX_PROVIDER=e2b and E2B_API_KEY is set.
It delegates file/shell/browser operations to the E2B SDK when available, else falls
back to Docker local provider.

Docs: https://e2b.dev/docs
"""

import logging

logger = logging.getLogger(__name__)


class E2BSandboxAdapter:
    """Placeholder adapter for E2B cloud sandboxes.

    To enable, install `e2b-code-interpreter` and set:

        SANDBOX_PROVIDER=e2b
        E2B_API_KEY=e2b_...

    Full implementation would wrap `e2b.sandbox` lifecycle.
    This scaffold exposes the interface and logs intent, keeping the system
    bootable without the optional dependency.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key
        self.provider = "e2b"

    async def create(self, timeout_minutes: int = 60):
        logger.info(f"[E2B] would create sandbox (key={'set' if self.api_key else 'missing'}, timeout={timeout_minutes}m)")
        # Fallback: instruct user to use Docker local
        raise NotImplementedError(
            "E2B provider scaffold — install `e2b-code-interpreter` and implement create(). "
            "Falling back to Docker local sandbox. Set SANDBOX_PROVIDER=docker or unset E2B_API_KEY."
        )
