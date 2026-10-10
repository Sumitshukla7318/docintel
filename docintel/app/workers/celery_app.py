"""
Celery application instance. Run the worker with:
    celery -A app.workers.celery_app worker --loglevel=info
"""
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "docintel",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=60 * 10,       # hard kill after 10 minutes
    task_soft_time_limit=60 * 8,   # raise SoftTimeLimitExceeded at 8 minutes
    worker_prefetch_multiplier=1,  # don't hoard tasks — fairer across workers
    result_expires=60 * 60 * 24,   # keep task results for 24h
)