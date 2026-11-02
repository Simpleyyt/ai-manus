import logging
from types import SimpleNamespace

import pytest

from app.application.services.auth_service import AuthService
from app.core.config import get_settings
from app.infrastructure.storage import redis as redis_module


def test_password_verification_does_not_log_hashes(caplog):
    service = object.__new__(AuthService)
    service.settings = SimpleNamespace(password_salt="test-salt", password_hash_rounds=1_000)
    password_hash = service._hash_password("test-password")

    with caplog.at_level(logging.INFO):
        assert service._verify_password("test-password", password_hash)
        assert not service._verify_password("wrong-password", password_hash)

    assert password_hash not in caplog.text
    assert "Generated hash" not in caplog.text
    assert "expected hash" not in caplog.text


@pytest.mark.asyncio
async def test_redis_client_uses_provider_rediss_url(monkeypatch):
    redis_url = "rediss://default:secret@example.upstash.io:6379"
    monkeypatch.setenv("API_KEY", "unit-test-key")
    monkeypatch.setenv("REDIS_URL", redis_url)
    get_settings.cache_clear()

    calls = {}

    class FakeRedis:
        async def ping(self):
            return True

        async def close(self):
            return None

    fake_client = FakeRedis()

    def fake_from_url(cls, url, **kwargs):
        calls["url"] = url
        calls["kwargs"] = kwargs
        return fake_client

    monkeypatch.setattr(redis_module.Redis, "from_url", classmethod(fake_from_url))
    client = redis_module.RedisClient()
    await client.initialize()

    assert calls["url"] == redis_url
    assert calls["kwargs"] == {"decode_responses": True}
    assert client.client is fake_client

    await client.shutdown()
    get_settings.cache_clear()
