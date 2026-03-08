from types import SimpleNamespace

from app.domain.utils.model_headers import build_default_headers, parse_extra_headers


def _make_settings(**overrides):
    defaults = {
        "model_name": "gpt-4o",
        "model_provider": "openai",
        "temperature": 0.7,
        "max_tokens": 2000,
        "api_base": "https://api.openai.com/v1",
        "extra_header": None,
        "extra_headers": None,
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_parse_extra_headers_json():
    result = parse_extra_headers('{"X-Trace-Id":"abc","X-Env":"prod"}')
    assert result == {"X-Trace-Id": "abc", "X-Env": "prod"}


def test_parse_extra_headers_kv_pairs():
    result = parse_extra_headers("X-Trace-Id:abc,X-Env=prod")
    assert result == {"X-Trace-Id": "abc", "X-Env": "prod"}


def test_build_model_kwargs_include_legacy_and_extra_headers():
    settings = _make_settings(
        extra_header="legacy-app-code",
        extra_headers='{"X-Trace-Id":"trace-123"}',
    )

    kwargs = {
        "default_headers": build_default_headers(
            model_provider=settings.model_provider,
            extra_header=settings.extra_header,
            extra_headers=settings.extra_headers,
        )
    }

    assert kwargs["default_headers"] == {
        "APP-Code": "legacy-app-code",
        "X-Trace-Id": "trace-123",
    }


def test_build_model_kwargs_non_openai_skip_default_headers():
    settings = _make_settings(
        model_provider="ollama",
        extra_header="legacy-app-code",
        extra_headers="X-Trace-Id:trace-123",
    )

    kwargs = {
        "default_headers": build_default_headers(
            model_provider=settings.model_provider,
            extra_header=settings.extra_header,
            extra_headers=settings.extra_headers,
        )
    }

    assert kwargs["default_headers"] == {}
