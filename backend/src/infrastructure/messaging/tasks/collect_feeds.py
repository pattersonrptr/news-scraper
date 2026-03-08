"""Celery task: collect articles from all active RSS sources."""

from __future__ import annotations

import asyncio

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(name="backend.src.infrastructure.messaging.tasks.collect_feeds.collect_feeds_task", bind=True, max_retries=3)  # type: ignore[misc]
def collect_feeds_task(self) -> dict[str, int]:  # type: ignore[no-untyped-def]
    """Celery task: fetch all active RSS feeds and persist new articles.

    Runs synchronously (Celery tasks are sync by default) but internally
    uses asyncio.run() to execute the async use case.
    """
    log.info("collect_feeds_task_started")
    try:
        result = asyncio.run(_run_collection())
        log.info("collect_feeds_task_done", result=result)
        return result
    except Exception as exc:
        log.error("collect_feeds_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=60) from exc


async def _run_collection() -> dict[str, int]:
    """Wire up dependencies and execute the CollectFeedsUseCase."""
    # Import here to avoid circular imports at module load time
    from backend.src.domain.services.deduplication import DeduplicationService
    from backend.src.infrastructure.collectors.rss.collector import RSSCollector
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.article_repo import SQLArticleRepository
    from backend.src.infrastructure.database.repositories.source_repo import SQLSourceRepository
    from backend.src.use_cases.collect_feeds import CollectFeedsUseCase

    async with get_session() as session:
        article_repo = SQLArticleRepository(session)
        source_repo = SQLSourceRepository(session)
        dedup = DeduplicationService(article_repo)
        collector = RSSCollector()
        use_case = CollectFeedsUseCase(
            source_repo=source_repo,
            article_repo=article_repo,
            dedup_service=dedup,
            collector=collector,
        )
        return await use_case.execute()
