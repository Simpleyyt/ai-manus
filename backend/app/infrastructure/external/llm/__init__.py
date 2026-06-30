from functools import lru_cache

from app.domain.external.llm import LLM


@lru_cache()
def get_llm() -> LLM:
    """Get the configured LLM gateway instance."""
    from app.infrastructure.external.llm.langchain_llm import LangChainLLM
    return LangChainLLM()
