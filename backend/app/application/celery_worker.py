"""Celery worker entry-point.

Start with::

    celery -A app.application.celery_worker worker --loglevel=info

The worker retrieves pre-created ``TaskRunner`` instances from the
module-level registry in ``celery_task`` (shared when the worker is
embedded in the same process as the API).  No runner reconstruction
or upper-layer imports are needed here.
"""

import asyncio
import logging

from app.infrastructure.external.task.celery_app import get_celery_app
from app.infrastructure.external.task.celery_task import (
    CeleryTaskProxy,
    get_runner,
    remove_runner,
)

logger = logging.getLogger(__name__)

app = get_celery_app()


@app.task(name="manus.execute_agent_task", bind=True)
def execute_agent_task(self, task_id: str):
    runner = get_runner(task_id)
    if not runner:
        logger.error("Runner not found for task %s (worker may be remote)", task_id)
        return

    proxy = CeleryTaskProxy(task_id)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(runner.run(proxy))
    except Exception:
        logger.exception("Task %s failed", task_id)
    finally:
        loop.run_until_complete(runner.on_done(proxy))
        remove_runner(task_id)
        loop.close()
