"""Celery worker entrypoint.

Run: ``celery -A src.app.core.celery.settings worker -l INFO``
"""

from src.app.core.celery.app import celery_app as app

__all__ = ["app"]
