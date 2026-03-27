from typing import Optional, List, AsyncIterator, Protocol
from dataclasses import dataclass

from app.domain.models.claw import ClawMessage


@dataclass
class ClawInstanceInfo:
    """Connection info returned after creating a claw instance."""
    address: str
    instance_name: Optional[str] = None


class ClawRuntime(Protocol):
    """Manages the lifecycle of claw instances.

    Implementations may use Docker (local), a remote HTTP API,
    Kubernetes, SSH, or any other provisioning mechanism.
    """

    creates_immediately: bool

    async def create(self, claw_id: str, api_key: str) -> ClawInstanceInfo:
        """Create a new claw instance. Returns connection info."""
        ...

    async def destroy(self, instance_name: Optional[str]) -> None:
        """Destroy a claw instance (best-effort, should not raise)."""
        ...

    async def wait_for_ready(self, base_url: str) -> bool:
        """Wait until the claw instance is healthy. Returns True if ready."""
        ...


class ClawClient(Protocol):
    """Communicates with a running claw instance.

    Implementations may use HTTP, gRPC, or any other protocol.
    """

    def chat_stream(
        self, base_url: str, message: str, session_id: str,
    ) -> AsyncIterator[dict]:
        """Stream chat response chunks from a claw instance.
        Yields dicts with at minimum a 'type' key ('text', 'file', 'done', 'error')."""
        ...

    async def get_history(
        self, base_url: str, session_id: str, limit: int = 200,
    ) -> List[ClawMessage]:
        """Fetch native session history from a claw instance."""
        ...

    async def get_file(self, base_url: str, filename: str) -> tuple[bytes, str]:
        """Download a file. Returns (content_bytes, content_type)."""
        ...
