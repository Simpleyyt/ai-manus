from datetime import date, timedelta

import httpx

from app.infrastructure.external.search.specstream_search import SpecStreamSearchEngine


def _transport(captured: dict, status: int = 200, body: dict | None = None):
    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = request.url
        captured["method"] = request.method
        captured["headers"] = dict(request.headers)
        return httpx.Response(status, json=body if body is not None else {"data": {"sources": []}})

    return httpx.MockTransport(handler)


async def test_search_sends_bearer_key_and_maps_sources():
    captured: dict = {}
    body = {
        "data": {
            "sources": [
                {"url": "https://a.example", "title": "A", "site": "a.example", "snippet": "sa", "cited": False, "published": "2026-05-06"},
                {"url": "https://b.example", "title": "", "site": "b.example", "snippet": "sb", "cited": False},
                {"url": "", "title": "no url", "site": "", "snippet": "x", "cited": False},
            ]
        }
    }
    engine = SpecStreamSearchEngine(api_key="secret", transport=_transport(captured, body=body))

    result = await engine.search("python", date_range="all")

    assert captured["method"] == "GET"
    assert f"{captured['url'].scheme}://{captured['url'].host}{captured['url'].path}" == "https://api.specstream.ai/v1/web-search"
    assert dict(captured["url"].params) == {"q": "python", "num": "10", "speed": "fast"}
    assert captured["headers"]["authorization"] == "Bearer secret"
    assert result.success
    assert result.data.total_results == 2
    assert [(r.title, r.link, r.snippet) for r in result.data.results] == [
        ("A", "https://a.example", "sa"),
        ("https://b.example", "https://b.example", "sb"),
    ]


async def test_date_range_adds_after_operator():
    captured: dict = {}
    engine = SpecStreamSearchEngine(api_key="secret", transport=_transport(captured))

    result = await engine.search("python", date_range="past_week")

    after = (date.today() - timedelta(days=7)).isoformat()
    assert captured["url"].params["q"] == f"python after:{after}"
    assert result.success
    assert result.data.query == "python"
    assert result.data.results == []


async def test_http_error_returns_failed_tool_result():
    body = {"error": {"code": "invalid_token", "message": "bad key"}}
    engine = SpecStreamSearchEngine(api_key="bad", transport=_transport({}, status=401, body=body))

    result = await engine.search("python")

    assert not result.success
    assert "SpecStream Search failed" in result.message
    assert result.data.total_results == 0


async def test_malformed_response_returns_failed_tool_result():
    engine = SpecStreamSearchEngine(api_key="secret", transport=_transport({}, body={"data": {}}))

    result = await engine.search("python")

    assert not result.success
    assert "data.sources" in result.message


def test_factory_builds_specstream_only_with_key(monkeypatch):
    from app.core.config import get_settings
    from app.infrastructure.external.search import get_search_engine

    monkeypatch.setenv("API_KEY", "test-llm-key")
    monkeypatch.setenv("SEARCH_PROVIDER", "specstream")
    monkeypatch.delenv("SPECSTREAM_API_KEY", raising=False)
    get_settings.cache_clear()
    get_search_engine.cache_clear()
    try:
        assert get_search_engine() is None

        monkeypatch.setenv("SPECSTREAM_API_KEY", "ss-key")
        get_settings.cache_clear()
        get_search_engine.cache_clear()
        engine = get_search_engine()
        assert isinstance(engine, SpecStreamSearchEngine)
        assert engine.api_key == "ss-key"
    finally:
        get_settings.cache_clear()
        get_search_engine.cache_clear()
