"""Celery worker entry point.

Start with:
    uv run celery -A app.worker.celery_app worker --loglevel=INFO --concurrency=4

Each agent task occupies one worker process for its whole run, so
``--concurrency`` bounds how many agent sessions execute in parallel.
"""
from app.infrastructure.logging import setup_logging

setup_logging()

from app.infrastructure.external.task.celery_app import celery_app
# Import registers the agent task with the Celery app
import app.infrastructure.external.task.celery_worker  # noqa: E402,F401

__all__ = ["celery_app"]
