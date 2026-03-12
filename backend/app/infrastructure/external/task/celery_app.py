import logging
from functools import lru_cache
from celery import Celery

logger = logging.getLogger(__name__)


@lru_cache()
def get_celery_app() -> Celery:
    """Create and configure the Celery application.

    Uses the configured celery_broker_url or falls back to constructing
    a Redis URL from the standard Redis configuration on db=1.
    """
    from app.core.config import get_settings
    settings = get_settings()

    if settings.celery_broker_url:
        broker_url = settings.celery_broker_url
    else:
        password_part = f":{settings.redis_password}@" if settings.redis_password else ""
        broker_url = f"redis://{password_part}{settings.redis_host}:{settings.redis_port}/1"

    result_backend = settings.celery_result_backend or broker_url

    app = Celery("manus", broker=broker_url, backend=result_backend)
    app.conf.update(
        task_serializer="json",
        result_serializer="json",
        accept_content=["json"],
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        worker_hijack_root_logger=False,
    )

    logger.info("Celery app configured with broker: %s", broker_url)
    return app
