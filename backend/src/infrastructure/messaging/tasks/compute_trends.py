"""Celery task: compute trending topics from recent articles."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    name="backend.src.infrastructure.messaging.tasks.compute_trends.compute_trends_task",
    bind=True,
    max_retries=3,
)
def compute_trends_task(self, hours: int = 24) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Celery task: aggregate trends from articles collected in the last N hours.

    Args:
        hours: Look-back window in hours (default 24).

    Returns:
        Trends summary dict with top categories, keywords, and sentiment
        distribution.
    """
    log.info("compute_trends_task_started", hours=hours)
    try:
        result = asyncio.run(_run_trends(hours=hours))
        log.info("compute_trends_task_done", total_articles=result.get("total_articles"))
        return result
    except Exception as exc:
        log.error("compute_trends_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120) from exc


async def _run_trends(hours: int) -> dict[str, Any]:
    """Wire dependencies and execute ComputeTrendsUseCase."""
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.article_repo import (
        SQLArticleRepository,
    )
    from backend.src.use_cases.compute_trends import ComputeTrendsUseCase

    async with get_session() as session:
        repo = SQLArticleRepository(session)
        articles = await repo.list_recent(hours=hours)
        use_case = ComputeTrendsUseCase(articles=articles)
        return use_case.execute()
