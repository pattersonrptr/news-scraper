"""Celery task: update implicit interest weights from read article history."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    name="backend.src.infrastructure.messaging.tasks.update_implicit_weights.update_implicit_weights_task",
    bind=True,
    max_retries=3,
)
def update_implicit_weights_task(self) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Celery task: learn implicit interest weights from the user's read history.

    Runs once daily. Increments category weights for recently read articles
    and applies a small decay to all existing weights.
    """
    log.info("update_implicit_weights_task_started")
    try:
        result = asyncio.run(_run_update())
        log.info(
            "update_implicit_weights_task_done",
            articles_read=result.get("articles_read"),
            categories_updated=result.get("categories_updated"),
        )
        return result
    except Exception as exc:
        log.error("update_implicit_weights_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=300) from exc


async def _run_update() -> dict[str, Any]:
    """Wire dependencies and execute UpdateImplicitWeightsUseCase."""
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.article_repo import SQLArticleRepository
    from backend.src.infrastructure.database.repositories.user_repo import SQLUserRepository
    from backend.src.use_cases.update_implicit_weights import UpdateImplicitWeightsUseCase

    async with get_session() as session:
        use_case = UpdateImplicitWeightsUseCase(
            article_repo=SQLArticleRepository(session),
            profile_repo=SQLUserRepository(session),
        )
        return await use_case.execute()
