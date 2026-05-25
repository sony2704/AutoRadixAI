"""
Celery Application — background task queue for GPU inference and heavy jobs.
"""
from __future__ import annotations

from celery import Celery

from app.config import settings

celery_app = Celery(
    "autoradixai",
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
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_routes={
        "app.workers.tasks.run_inference_task": {"queue": "inference"},
        "app.workers.tasks.run_anonymization_task": {"queue": "processing"},
        "app.workers.tasks.run_feature_extraction_task": {"queue": "processing"},
        "app.workers.tasks.generate_report_task": {"queue": "reporting"},
    },
    task_soft_time_limit=settings.INFERENCE_TIMEOUT_SECONDS,
    task_time_limit=settings.INFERENCE_TIMEOUT_SECONDS + 30,
)
