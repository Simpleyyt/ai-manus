import json
import logging
from typing import Dict, Optional


logger = logging.getLogger(__name__)

_HEADER_ENABLED_PROVIDERS = {"openai"}


def parse_extra_headers(raw_headers: Optional[str]) -> Dict[str, str]:
    if not raw_headers:
        return {}

    try:
        headers = json.loads(raw_headers)
        if isinstance(headers, dict):
            return {
                str(key).strip(): str(value).strip()
                for key, value in headers.items()
                if str(key).strip()
            }
    except json.JSONDecodeError:
        pass

    parsed: Dict[str, str] = {}
    for item in raw_headers.split(","):
        segment = item.strip()
        if not segment:
            continue
        separator = ":" if ":" in segment else "=" if "=" in segment else None
        if not separator:
            logger.warning("Ignore invalid EXTRA_HEADERS item: %s", segment)
            continue

        key, value = segment.split(separator, 1)
        key = key.strip()
        value = value.strip()
        if not key:
            logger.warning("Ignore empty EXTRA_HEADERS key: %s", segment)
            continue
        parsed[key] = value
    return parsed


def build_default_headers(
    model_provider: str,
    extra_headers: Optional[str],
) -> Dict[str, str]:
    if model_provider not in _HEADER_ENABLED_PROVIDERS:
        return {}

    return parse_extra_headers(extra_headers)
