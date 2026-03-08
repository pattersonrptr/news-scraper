"""Celery application factory."""

from __future__ import annotations

from celery import Celery

from backend.src.core.config import get_settings

_settings = get_settings()

celery_app = Celery(
    "news_scraper",
    broker=_settings.celery_broker_url,
    backend=_settings.celery_result_backend,
    include=[
        "backend.src.infrastructure.messaging.tasks.collect_feeds",
        "backend.src.infrastructure.messaging.tasks.compute_trends",
        "backend.src.infrastructure.messaging.tasks.run_ai_pipeline",
        "backend.src.infrastructure.messaging.tasks.send_alerts",
        "backend.src.infrastructure.messaging.tasks.send_daily_digest",
        "backend.src.infrastructure.messaging.tasks.update_implicit_weights",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # Beat schedule — tasks run on a fixed interval
    beat_schedule={
        "collect-all-feeds": {
            "task": "backend.src.infrastructure.messaging.tasks.collect_feeds.collect_feeds_task",
            "schedule": 60 * _settings.default_fetch_interval,  # seconds
        },
        "compute-trends-hourly": {
            "task": "backend.src.infrastructure.messaging.tasks.compute_trends.compute_trends_task",
            "schedule": 3600,  # every hour
            "kwargs": {"hours": 24},
        },
        "run-ai-pipeline-hourly": {
            "task": "backend.src.infrastructure.messaging.tasks.run_ai_pipeline.run_ai_pipeline_task",
            "schedule": 3600,  # every hour
            "kwargs": {"batch_size": 20},
        },
        "send-alerts-every-15min": {
            "task": "backend.src.infrastructure.messaging.tasks.send_alerts.send_alerts_task",
            "schedule": 900,  # every 15 minutes
        },
        "send-daily-digest": {
            "task": "backend.src.infrastructure.messaging.tasks.send_daily_digest.send_daily_digest_task",
            "schedule": 86400,  # every 24 hours (Beat crontab not needed — daily is fine)
        },
        "update-implicit-weights-daily": {
            "task": "backend.src.infrastructure.messaging.tasks.update_implicit_weights.update_implicit_weights_task",
            "schedule": 86400,  # every 24 hours
        },
    },
)
