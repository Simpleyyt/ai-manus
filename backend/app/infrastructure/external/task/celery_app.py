import os
from celery import Celery


def _build_redis_url() -> str:
    host = os.getenv("REDIS_HOST", "redis")
    port = os.getenv("REDIS_PORT", "6379")
    db = os.getenv("REDIS_DB", "0")
    password = os.getenv("REDIS_PASSWORD", "")
    if password:
        return f"redis://:{password}@{host}:{port}/{db}"
    return f"redis://{host}:{port}/{db}"


celery_app = Celery(
    "manus",
    broker=os.getenv("CELERY_BROKER_URL") or _build_redis_url(),
    backend=os.getenv("CELERY_BACKEND_URL") or _build_redis_url(),
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    imports=["app.infrastructure.external.task.celery_task"],
)
