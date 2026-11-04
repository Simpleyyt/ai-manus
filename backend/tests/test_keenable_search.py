import json

import httpx

from app.infrastructure.external.search.keenable_search import KeenableSearchEngine


def _transport(captured: dict, status: int = 200, body: dict | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["headers"] = dict(request.headers)
        captured["json"] = json.loads(request.content)
        return httpx.Response(status, json=body if body is not None else {"results": []})

    return httpx.MockTransport(handler)


async def test_keyless_uses_public_endpoint_and_maps_results():
    captured: dict = {}
    body = {
        "results": [
            {"title": "A", "url": "https://a.example", "snippet": "sa", "description": ""},
            {"title": "", "url": "https://b.example", "snippet": "", "description": "db"},
            {"title": "no url", "url": "", "snippet": "x"},
        ]
    }
    engine = KeenableSearchEngine(transport=_transport(captured, body=body))

    result = await engine.search("python", date_range="past_week")

    assert captured["url"] == "https://api.keenable.ai/v1/search/public"
    assert captured["headers"]["x-keenable-title"] == "ai-manus"
    assert "x-api-key" not in captured["headers"]
    assert captured["json"] == {"query": "python", "max_results": 10, "published_after": "7d"}
    assert result.success
    assert result.data.total_results == 2
    assert [(r.title, r.link, r.snippet) for r in result.data.results] == [
        ("A", "https://a.example", "sa"),
        ("https://b.example", "https://b.example", "db"),
    ]


async def test_api_key_uses_authenticated_endpoint_without_date_filter():
    captured: dict = {}
    engine = KeenableSearchEngine(api_key="secret", transport=_transport(captured))

    result = await engine.search("python", date_range="all")

    assert captured["url"] == "https://api.keenable.ai/v1/search"
    assert captured["headers"]["x-api-key"] == "secret"
    assert "x-keenable-title" not in captured["headers"]
    assert "published_after" not in captured["json"]
    assert result.success
    assert result.data.results == []


async def test_http_error_returns_failed_tool_result():
    engine = KeenableSearchEngine(transport=_transport({}, status=429, body={"detail": "rate limited"}))

    result = await engine.search("python")

    assert not result.success
    assert "Keenable Search failed" in result.message
    assert result.data.total_results == 0


async def test_malformed_response_returns_failed_tool_result():
    engine = KeenableSearchEngine(transport=_transport({}, body={"error": "bad"}))

    result = await engine.search("python")

    assert not result.success
    assert "results" in result.message


def test_factory_builds_keenable_without_key(monkeypatch):
    from app.core.config import get_settings
    from app.infrastructure.external.search import get_search_engine

    monkeypatch.setenv("API_KEY", "test-llm-key")
    monkeypatch.setenv("SEARCH_PROVIDER", "keenable")
    monkeypatch.delenv("KEENABLE_API_KEY", raising=False)
    get_settings.cache_clear()
    get_search_engine.cache_clear()
    try:
        engine = get_search_engine()
        assert isinstance(engine, KeenableSearchEngine)
        assert engine.api_key == ""
    finally:
        get_settings.cache_clear()
        get_search_engine.cache_clear()
