import json
from pathlib import Path

from app.infrastructure.repositories.file_connector_catalog import FileConnectorCatalog


def test_shipped_catalog_is_the_repo_root_file():
    path = Path(__file__).resolve().parents[2] / "connectors.json"
    catalog = FileConnectorCatalog(str(path))
    entries = catalog.list_entries()
    assert [item.name for item in entries[:6]] == [
        "Crypto.com",
        "CoinGecko",
        "PopHIVE",
        "Neimo",
        "TomTom Maps",
        "ilert",
    ]
    assert len(entries) == 67
    learn = catalog.get("f4c2516f-40c3-4be2-b1c6-fb18da6a04bf")
    assert learn is not None
    assert learn.url == "https://learn.microsoft.com/api/mcp"
    assert learn.headers == []
    tomtom = catalog.get("15027330-caa8-49d2-8c90-75397e2c6410")
    assert tomtom is not None
    assert tomtom.headers[0].key == "tomtom-api-key"
    assert catalog.get("9444d960-ab7e-450f-9cb9-b9467fb0adda") is None


def test_catalog_file_skips_invalid_rows_and_sorts_order_zero_last(tmp_path):
    path = tmp_path / "connectors.json"
    path.write_text(json.dumps({
        "connectors": [
            {
                "uid": "zero",
                "name": "Last",
                "url": "https://example.com/zero",
                "transport": "streamable-http",
            },
            {
                "uid": "local",
                "name": "Stdio",
                "url": "https://example.com/stdio",
                "transport": "stdio",
            },
            {
                "uid": "second",
                "name": "Second",
                "url": "https://example.com/b",
                "transport": "sse",
                "order": 2,
                "iconDark": "https://cdn.example.com/dark.png",
            },
            {
                "uid": "first",
                "name": "First",
                "url": "https://example.com/a",
                "transport": "streamable-http",
                "order": 1,
            },
            {
                "uid": "first",
                "name": "Duplicate",
                "url": "https://example.com/dup",
                "transport": "streamable-http",
                "order": 1,
            },
            {"name": "Missing uid", "url": "https://example.com/x", "transport": "sse"},
        ]
    }), encoding="utf-8")
    catalog = FileConnectorCatalog(str(path))
    entries = catalog.list_entries()
    assert [item.name for item in entries] == ["First", "Second", "Last"]
    assert entries[1].icon_dark == "https://cdn.example.com/dark.png"
    assert catalog.get("local") is None


def test_missing_catalog_file_is_empty(tmp_path):
    catalog = FileConnectorCatalog(str(tmp_path / "missing.json"))
    assert catalog.list_entries() == []
    assert catalog.get("any") is None
