from functools import lru_cache
from typing import Optional
import logging

from app.domain.external.search import SearchEngine
from app.core.config import get_settings

logger = logging.getLogger(__name__)

@lru_cache()
def get_search_engine() -> Optional[SearchEngine]:
    """Get search engine instance based on configuration"""
    from app.infrastructure.external.search.google_search import GoogleSearchEngine
    from app.infrastructure.external.search.baidu_search import BaiduSearchEngine
    from app.infrastructure.external.search.baidu_web_search import BaiduWebSearchEngine
    from app.infrastructure.external.search.bing_search import BingSearchEngine
    from app.infrastructure.external.search.bing_web_search import BingWebSearchEngine
    from app.infrastructure.external.search.tavily_search import TavilySearchEngine
    from app.infrastructure.external.search.serper_search import SerperSearchEngine
    from app.infrastructure.external.search.custom_search import CustomSearchEngine

    settings = get_settings()
    if settings.search_provider == "google":
        if settings.google_search_api_key and settings.google_search_engine_id:
            logger.info("Initializing Google Search Engine")
            return GoogleSearchEngine(
                api_key=settings.google_search_api_key,
                cx=settings.google_search_engine_id
            )
        else:
            logger.warning("Google Search Engine not initialized: missing API key or engine ID")
    elif settings.search_provider == "baidu":
        if settings.baidu_search_api_key:
            logger.info("Initializing Baidu Search Engine (API)")
            return BaiduSearchEngine(api_key=settings.baidu_search_api_key)
        else:
            logger.warning("Baidu Search Engine not initialized: missing API key (BAIDU_SEARCH_API_KEY)")
    elif settings.search_provider == "baidu_web":
        logger.info("Initializing Baidu Web Search Engine (scraping)")
        return BaiduWebSearchEngine()
    elif settings.search_provider == "bing":
        if settings.bing_search_api_key:
            logger.info("Initializing Bing Search Engine (API)")
            return BingSearchEngine(api_key=settings.bing_search_api_key)
        else:
            logger.warning("Bing Search Engine not initialized: missing API key (BING_SEARCH_API_KEY)")
    elif settings.search_provider == "bing_web":
        logger.info("Initializing Bing Web Search Engine (scraping)")
        return BingWebSearchEngine()
    elif settings.search_provider == "tavily":
        if settings.tavily_api_key:
            logger.info("Initializing Tavily Search Engine")
            return TavilySearchEngine(api_key=settings.tavily_api_key)
        else:
            logger.warning("Tavily Search Engine not initialized: missing API key (TAVILY_API_KEY)")
    elif settings.search_provider == "serper":
        if settings.serper_api_key:
            logger.info("Initializing Serper Search Engine")
            return SerperSearchEngine(api_key=settings.serper_api_key)
        else:
            logger.warning("Serper Search Engine not initialized: missing API key (SERPER_API_KEY)")
    elif settings.search_provider == "custom":
        if settings.search_api_url:
            logger.info(f"Initializing Custom Search Engine (url={settings.search_api_url})")
            return CustomSearchEngine(
                api_url=settings.search_api_url,
                api_key=settings.search_api_key or "",
                api_key_header=settings.search_api_key_header,
                api_key_header_prefix=settings.search_api_key_header_prefix,
                api_key_param=settings.search_api_key_param,
                method=settings.search_api_method,
                query_field=settings.search_query_field,
                result_field=settings.search_result_field,
                title_field=settings.search_title_field,
                link_field=settings.search_link_field,
                snippet_field=settings.search_snippet_field,
            )
        else:
            logger.warning("Custom Search Engine not initialized: missing SEARCH_API_URL")
    else:
        logger.warning(f"Unknown search provider: {settings.search_provider}")

    return None