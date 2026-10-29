"""Cloud Computer — persistent sandbox for automations and hosting.

In Manus 2.0, Cloud Computer is a dedicated VM that stays alive beyond a single
task, hosting servers, bots, and automations. See:
https://manus.im/features/cloud-computer
https://manus.im/blog/introducing-manus-2-0

In the replica, Cloud Computer maps to a long-lived Docker container or an
E2B/Daytona sandbox that persists until TTL or manual stop.

Status: scaffold — API + model present, actual provisioning delegates to
existing Sandbox infrastructure (Docker/E2B).
"""

from datetime import datetime, UTC
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
import uuid


class CloudComputerStatus(str, Enum):
    PROVISIONING = "provisioning"
    RUNNING = "running"
    STOPPED = "stopped"
    EXPIRED = "expired"
    ERROR = "error"


class CloudComputer(BaseModel):
    """Persistent compute environment."""

    id: str = Field(default_factory=lambda: uuid.uuid4().hex[:12])
    user_id: str
    name: str = Field(default="Landis Cloud")
    status: CloudComputerStatus = CloudComputerStatus.PROVISIONING
    sandbox_id: Optional[str] = None  # underlying sandbox/container id
    sandbox_provider: str = "docker"  # docker | e2b | daytona
    region: str = "auto"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    expires_at: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None
    metadata: dict = Field(default_factory=dict)

    model_config = {"use_enum_values": False}
