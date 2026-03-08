"""Celery task: compile and send the daily news digest email."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    name="backend.src.infrastructure.messaging.tasks.send_daily_digest.send_daily_digest_task",
    bind=True,
    max_retries=3,
)
def send_daily_digest_task(self) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Celery task: compile the daily digest and send it by email.

    Scheduled once per day at the time configured in digest_time (settings).
    """
    log.info("send_daily_digest_task_started")
    try:
        result = asyncio.run(_run_digest())
        log.info(
            "send_daily_digest_task_done",
            total_articles=result.get("total_articles"),
            sent=result.get("sent"),
        )
        return result
    except Exception as exc:
        log.error("send_daily_digest_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300) from exc


async def _run_digest() -> dict[str, Any]:
    """Wire dependencies and send the digest."""
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.article_repo import SQLArticleRepository
    from backend.src.infrastructure.database.repositories.user_profile_repo import InMemoryUserProfileRepository
    from backend.src.infrastructure.notifications.email.smtp_adapter import SMTPEmailAdapter
    from backend.src.use_cases.compile_digest import CompileDigestUseCase

    email_adapter = SMTPEmailAdapter()
    profile_repo = InMemoryUserProfileRepository()

    profile = await profile_repo.get_default()
    if not profile:
        log.warning("send_daily_digest: no profile found, skipping")
        return {"total_articles": 0, "sent": False}

    recipient = profile.notification_email or profile.email
    if not recipient:
        log.warning("send_daily_digest: no recipient email, skipping")
        return {"total_articles": 0, "sent": False}

    async with get_session() as session:
        use_case = CompileDigestUseCase(
            article_repo=SQLArticleRepository(session),
            hours=24,
        )
        context = await use_case.execute()

    await email_adapter.send_digest_email(to=recipient, context=context)
    return {"total_articles": context["total_articles"], "sent": True}
