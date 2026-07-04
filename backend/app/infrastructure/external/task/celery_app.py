"""Celery application shared by the API process (producer) and workers (consumer).

The broker defaults to the same Redis instance used for streams/caching, and
can be overridden with the CELERY_BROKER_URL setting. Results are not stored
in a Celery result backend: task state is tracked in Redis metadata keys
(see celery_task.py), and all agent events flow through Redis Streams.
"""
import logging

from celery import Celery

from app.core.config import get_settings

logger = logging.getLogger(__name__)

AGENT_TASK_NAME = "manus.agent.run"


def _build_redis_url() -> str:
    settings = get_settings()
    auth = f":{settings.redis_password}@" if settings.redis_password else ""
    return f"redis://{auth}{settings.redis_host}:{settings.redis_port}/{settings.redis_db}"


def _create_celery_app() -> Celery:
    settings = get_settings()
    broker_url = settings.celery_broker_url or _build_redis_url()
    app = Celery("manus", broker=broker_url)
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        # Task state is tracked via Redis metadata keys, not a result backend
        task_ignore_result=True,
        # Agent tasks are long-running; don't prefetch more than one per worker process
        worker_prefetch_multiplier=1,
        broker_connection_retry_on_startup=True,
    )
    return app


celery_app = _create_celery_app()
