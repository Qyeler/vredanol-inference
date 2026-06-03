"""Celery application factory for inference tasks."""

from celery import Celery

from src.app.core import logger as _logger  # noqa: F401
from src.app.core.config import settings


def create_celery_app() -> Celery:
    app = Celery(
        "vredanol-inference",
        broker=settings.CELERY_BROKER_URL,
        backend=settings.CELERY_RESULT_BACKEND,
    )
    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone=settings.CELERY_TIMEZONE,
        enable_utc=True,
        broker_connection_retry_on_startup=True,
        task_track_started=True,
        task_default_queue=settings.CELERY_INFERENCE_QUEUE,
        task_routes={
            "inference.classify": {"queue": settings.CELERY_INFERENCE_QUEUE},
        },
    )
    return app


celery_app = create_celery_app()

# Register task modules on this app instance.
import src.app.modules.inference.tasks  # noqa: E402, F401
