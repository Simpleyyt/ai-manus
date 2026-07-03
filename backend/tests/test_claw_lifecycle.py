"""Unit tests for Claw container lifecycle cleanup.

Verifies that ``ClawDomainService`` destroys the underlying runtime instance
(the Docker container) when a claw expires, is deleted, or fails to provision,
so containers never linger after their record is gone.
"""
from datetime import datetime, timedelta, UTC
from typing import Optional, List

import pytest

from app.domain.models.claw import Claw, ClawStatus, ClawMessage, ClawAttachment
from app.domain.external.claw import ClawInstanceInfo
from app.domain.services.claw_domain_service import ClawDomainService


class FakeClawRepository:
    def __init__(self, claw: Optional[Claw] = None):
        self.claw = claw
        self.deleted_user_ids: list[str] = []
        self.messages: list[tuple] = []

    async def get_by_user_id(self, user_id: str) -> Optional[Claw]:
        return self.claw

    async def get_by_id(self, claw_id: str) -> Optional[Claw]:
        return self.claw

    async def get_by_api_key(self, api_key: str) -> Optional[Claw]:
        return self.claw

    async def create(self, claw: Claw) -> Claw:
        self.claw = claw
        return claw

    async def update(self, claw: Claw) -> Claw:
        self.claw = claw
        return claw

    async def delete_by_user_id(self, user_id: str) -> bool:
        self.deleted_user_ids.append(user_id)
        self.claw = None
        return True

    async def get_messages(self, user_id: str) -> List[ClawMessage]:
        return []

    async def append_message(
        self, user_id: str, role: str, content: str = "",
        attachments: Optional[List[ClawAttachment]] = None,
    ) -> None:
        self.messages.append((user_id, role, content))

    async def clear_messages(self, user_id: str) -> None:
        pass


class FakeClawRuntime:
    creates_immediately = False

    def __init__(self, fail_create: bool = False, ready: bool = True):
        self.fail_create = fail_create
        self.ready = ready
        self.destroyed: list[Optional[str]] = []

    async def create(self, claw_id: str, api_key: str) -> ClawInstanceInfo:
        if self.fail_create:
            raise RuntimeError("boom")
        return ClawInstanceInfo(address="10.0.0.5", instance_name=f"manus-claw-{claw_id[:8]}")

    async def destroy(self, instance_name: Optional[str]) -> None:
        self.destroyed.append(instance_name)

    async def wait_for_ready(self, base_url: str) -> bool:
        return self.ready


class FakeClawClient:
    async def get_history(self, base_url, session_id, limit=200):
        return []

    async def get_file(self, base_url, filename):
        return b"", "application/octet-stream"

    def chat_stream(self, base_url, message, session_id):
        raise NotImplementedError


def _make_claw(**overrides) -> Claw:
    defaults = dict(
        id="claw-1234-abcd",
        user_id="user-1",
        api_key="manus-testkey",
        status=ClawStatus.RUNNING,
        container_name="manus-claw-claw1234",
        container_ip="10.0.0.5",
    )
    defaults.update(overrides)
    return Claw(**defaults)


async def test_expired_claw_destroys_container():
    claw = _make_claw(expires_at=datetime.now(UTC) - timedelta(seconds=1))
    repo = FakeClawRepository(claw)
    runtime = FakeClawRuntime()
    service = ClawDomainService(repo, runtime, FakeClawClient())

    result = await service.get_claw("user-1")

    assert result is None
    assert runtime.destroyed == ["manus-claw-claw1234"]
    assert repo.deleted_user_ids == ["user-1"]


async def test_delete_claw_destroys_container():
    claw = _make_claw()
    repo = FakeClawRepository(claw)
    runtime = FakeClawRuntime()
    service = ClawDomainService(repo, runtime, FakeClawClient())

    deleted = await service.delete_claw("user-1")

    assert deleted is True
    assert runtime.destroyed == ["manus-claw-claw1234"]
    assert repo.deleted_user_ids == ["user-1"]


async def test_delete_claw_without_record_is_noop():
    repo = FakeClawRepository(None)
    runtime = FakeClawRuntime()
    service = ClawDomainService(repo, runtime, FakeClawClient())

    deleted = await service.delete_claw("user-1")

    assert deleted is False
    assert runtime.destroyed == []


async def test_provision_failure_destroys_container():
    claw = _make_claw(status=ClawStatus.CREATING, container_name=None, container_ip=None)
    repo = FakeClawRepository(claw)
    runtime = FakeClawRuntime(ready=False)  # created but never becomes healthy
    service = ClawDomainService(repo, runtime, FakeClawClient())

    await service.provision_claw_instance(claw, ttl_seconds=3600)

    assert claw.status == ClawStatus.ERROR
    assert runtime.destroyed == ["manus-claw-claw-123"]
    assert claw.container_name is None
    assert claw.container_ip is None


async def test_provision_success_sets_expiry_from_start_time():
    claw = _make_claw(status=ClawStatus.CREATING, container_name=None, container_ip=None)
    repo = FakeClawRepository(claw)
    runtime = FakeClawRuntime(ready=True)
    service = ClawDomainService(repo, runtime, FakeClawClient())

    before = datetime.now(UTC)
    await service.provision_claw_instance(claw, ttl_seconds=3600)
    after = datetime.now(UTC)

    assert claw.status == ClawStatus.RUNNING
    assert runtime.destroyed == []
    # expires_at must be anchored at provisioning start, not at readiness,
    # so the DB record never outlives the container's own TTL clock.
    assert before + timedelta(seconds=3600) <= claw.expires_at <= after + timedelta(seconds=3600)
