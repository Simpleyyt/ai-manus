"""LLM gateway implementations and provider selection.

The concrete :class:`app.domain.external.llm.LLM` gateway is chosen at runtime
from the ``LLM_PROVIDER`` setting:

* ``langchain`` (default) — :class:`LangchainLLM`, supports many providers via
  ``init_chat_model``.
* ``openai`` — :class:`OpenAILLM`, talks to OpenAI / OpenAI-compatible endpoints
  directly through the official ``openai`` Python SDK.
"""
import logging

from app.core.config import get_settings
from app.domain.external.llm import LLM
from app.infrastructure.external.llm.langchain_llm import (
    LangchainLLM,
    get_langchain_llm,
)
from app.infrastructure.external.llm.openai_llm import OpenAILLM, get_openai_llm

logger = logging.getLogger(__name__)


def get_llm() -> LLM:
    """Return the configured LLM gateway singleton (chosen by ``LLM_PROVIDER``)."""
    provider = (get_settings().llm_provider or "langchain").lower()
    if provider == "openai":
        return get_openai_llm()
    if provider != "langchain":
        logger.warning(
            "Unknown LLM_PROVIDER '%s', falling back to 'langchain'", provider
        )
    return get_langchain_llm()


__all__ = [
    "LLM",
    "LangchainLLM",
    "OpenAILLM",
    "get_llm",
    "get_langchain_llm",
    "get_openai_llm",
]
