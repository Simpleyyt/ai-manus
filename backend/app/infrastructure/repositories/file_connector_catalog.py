import json
import logging
import os
from pathlib import Path
from typing import List, Optional

from pydantic import ValidationError

from app.core.config import get_settings
from app.domain.mcp_json import McpJsonError, parse_mcp_url
from app.domain.models.connector_catalog import CatalogConnector, CatalogHeaderField
from app.domain.models.mcp_config import MCPTransport

logger = logging.getLogger(__name__)

_ALLOWED_TRANSPORTS = {MCPTransport.STREAMABLE_HTTP.value, MCPTransport.SSE.value}


def default_connector_catalog_path() -> str:
    """Resolve the Apps catalog file.

    ``CONNECTOR_CATALOG_PATH`` wins. Otherwise use ``/etc/connectors.json``
    when it is mounted, then the repo-root ``connectors.json``.
    """
    configured = (get_settings().connector_catalog_path or "").strip()
    if configured:
        return configured
    if os.path.isfile("/etc/connectors.json"):
        return "/etc/connectors.json"
    repo_root = Path(__file__).resolve().parents[4]
    return str(repo_root / "connectors.json")


def _sort_entries(entries: List[CatalogConnector]) -> List[CatalogConnector]:
    """order 0 last, otherwise ascending; equal keys keep file order."""

    def sort_key(entry: CatalogConnector):
        if entry.order == 0:
            return (1, 0)
        return (0, entry.order)

    return sorted(entries, key=sort_key)


class FileConnectorCatalog:
    """Apps marketplace list from a JSON file the operator can edit."""

    def __init__(self, path: Optional[str] = None):
        self._path = path

    def list_entries(self) -> List[CatalogConnector]:
        return _sort_entries(self._load())

    def get(self, uid: str) -> Optional[CatalogConnector]:
        key = (uid or "").strip()
        if not key:
            return None
        for entry in self._load():
            if entry.uid == key:
                return entry
        return None

    def _resolve_path(self) -> str:
        if self._path is not None:
            return self._path
        return default_connector_catalog_path()

    def _load(self) -> List[CatalogConnector]:
        path = self._resolve_path()
        if not os.path.isfile(path):
            logger.info("Connector catalog file not found: %s", path)
            return []
        try:
            with open(path, "r", encoding="utf-8") as file:
                raw = json.load(file)
        except Exception:
            logger.exception("Error reading connector catalog %s", path)
            return []

        if isinstance(raw, dict):
            rows = raw.get("connectors")
        elif isinstance(raw, list):
            rows = raw
        else:
            rows = None
        if not isinstance(rows, list):
            logger.error(
                "Connector catalog %s must be an object with a connectors array",
                path,
            )
            return []

        entries: List[CatalogConnector] = []
        seen = set()
        for index, row in enumerate(rows):
            entry = _parse_entry(row, index, path)
            if entry is None:
                continue
            if entry.uid in seen:
                logger.warning(
                    "Skipping duplicate connector uid %s in %s", entry.uid, path
                )
                continue
            seen.add(entry.uid)
            entries.append(entry)
        return entries


def _parse_entry(row, index: int, path: str) -> Optional[CatalogConnector]:
    if not isinstance(row, dict):
        logger.warning("Skipping connector catalog item %s in %s: not an object", index, path)
        return None
    try:
        entry = CatalogConnector.model_validate(row)
    except ValidationError as exc:
        logger.warning("Skipping connector catalog item %s in %s: %s", index, path, exc)
        return None
    uid = entry.uid.strip()
    name = entry.name.strip()
    transport = (entry.transport or "").strip()
    if not uid or not name:
        logger.warning("Skipping connector catalog item %s in %s: uid and name are required", index, path)
        return None
    if transport not in _ALLOWED_TRANSPORTS:
        logger.warning(
            "Skipping connector %s in %s: transport must be streamable-http or sse",
            name,
            path,
        )
        return None
    try:
        url = parse_mcp_url(entry.url)
    except McpJsonError as exc:
        logger.warning("Skipping connector %s in %s: %s", name, path, exc)
        return None
    headers: List[CatalogHeaderField] = []
    for field in entry.headers:
        key = field.key.strip()
        if not key:
            continue
        headers.append(
            CatalogHeaderField(
                key=key,
                label=(field.label or key).strip() or key,
                placeholder=(field.placeholder or "").strip() or None,
            )
        )
    return entry.model_copy(
        update={
            "uid": uid,
            "name": name,
            "description": (entry.description or "").strip(),
            "icon": (entry.icon or "").strip() or None,
            "icon_dark": (entry.icon_dark or "").strip() or None,
            "transport": transport,
            "url": url,
            "headers": headers,
        }
    )
