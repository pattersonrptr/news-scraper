"""Celery task: scan recent articles for keyword alerts and send emails."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    name="backend.src.infrastructure.messaging.tasks.send_alerts.send_alerts_task",
    bind=True,
    max_retries=3,
)
def send_alerts_task(self) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Celery task: check keyword alerts and fire emails for new matches.

    Runs every 15 minutes. Rate-limited to 1 email per keyword per hour.
    """
    log.info("send_alerts_task_started")
    try:
        result = asyncio.run(_run_alerts())
        log.info(
            "send_alerts_task_done",
            matched=result.get("matched"),
            sent=result.get("sent"),
            skipped=result.get("skipped"),
        )
        return result
    except Exception as exc:
        log.error("send_alerts_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


async def _run_alerts() -> dict[str, Any]:
    """Wire dependencies and execute SendAlertsUseCase."""
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.alert_repo import SQLAlertRepository
    from backend.src.infrastructure.database.repositories.article_repo import SQLArticleRepository
    from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository
    from backend.src.infrastructure.notifications.email.smtp_adapter import SMTPEmailAdapter
    from backend.src.use_cases.send_alerts import SendAlertsUseCase

    async with get_session() as session:
        use_case = SendAlertsUseCase(
            article_repo=SQLArticleRepository(session),
            alert_repo=SQLAlertRepository(session),
            profile_repo=SQLUserRepository(session),
            email_adapter=SMTPEmailAdapter(),
        )
        return await use_case.execute()
