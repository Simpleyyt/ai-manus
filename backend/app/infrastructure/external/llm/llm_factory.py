"""LLM Factory module"""
import logging
from typing import Type
from app.domain.external.llm import LLM
from app.infrastructure.config import get_settings
from app.infrastructure.external.llm.openai_llm import OpenAILLM
from app.infrastructure.external.llm.gemini_llm import GeminiLLM

logger = logging.getLogger(__name__)

def create_llm() -> LLM:
    """Create LLM instance based on configuration"""
    settings = get_settings()
    
    if settings.model_provider == "gemini":
        logger.info("Using Gemini LLM")
        return GeminiLLM()
    elif settings.model_provider == "openai":
        logger.info("Using OpenAI LLM")
        return OpenAILLM()
    elif settings.model_provider == "deepseek":
        logger.info("Using Deepseek LLM (via OpenAI compatible API)")
        return OpenAILLM()
    else:
        logger.warning(f"Unknown model provider: {settings.model_provider}. Falling back to Deepseek.")
        return OpenAILLM()
