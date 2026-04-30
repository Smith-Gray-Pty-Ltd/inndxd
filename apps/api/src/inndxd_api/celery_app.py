"""Celery app configuration for distributed task execution."""

from celery import Celery
from celery.schedules import crontab
from inndxd_core.config import settings

celery_app = Celery(
    "inndxd_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
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
    beat_schedule={
        "cleanup-stuck-tasks": {
            "task": "inndxd_api.tasks.cleanup_stuck_briefs",
            "schedule": crontab(minute="*/30"),
        },
    },
)
