"""Celery task: run the AI analysis pipeline over unprocessed articles."""

from __future__ import annotations

import asyncio
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.infrastructure.messaging.celery_app import celery_app

log = get_logger(__name__)


@celery_app.task(  # type: ignore[misc]
    name="backend.src.infrastructure.messaging.tasks.run_ai_pipeline.run_ai_pipeline_task",
    bind=True,
    max_retries=3,
)
def run_ai_pipeline_task(self, batch_size: int = 20) -> dict[str, Any]:  # type: ignore[no-untyped-def]
    """Celery task: analyse up to *batch_size* unprocessed articles with AI.

    Args:
        batch_size: Maximum number of articles to process per run (default 20).

    Returns:
        Dict with keys ``processed`` and ``skipped``.
    """
    log.info("run_ai_pipeline_task_started", batch_size=batch_size)
    try:
        result = asyncio.run(_run_pipeline(batch_size=batch_size))
        log.info(
            "run_ai_pipeline_task_done",
            processed=result.get("processed"),
            skipped=result.get("skipped"),
        )
        return result
    except Exception as exc:
        log.error("run_ai_pipeline_task_failed", error=str(exc))
        raise self.retry(exc=exc, countdown=120) from exc


async def _run_pipeline(batch_size: int) -> dict[str, Any]:
    """Wire dependencies and execute RunAIPipelineUseCase."""
    from backend.src.core.config.settings import AIProvider, get_settings
    from backend.src.infrastructure.database.engine import get_session
    from backend.src.infrastructure.database.repositories.article_repo import (
        SQLArticleRepository,
    )
    from backend.src.use_cases.run_ai_pipeline import RunAIPipelineUseCase

    settings = get_settings()

    if settings.ai_provider == AIProvider.GEMINI:
        from backend.src.infrastructure.ai.gemini.adapter import GeminiAdapter
        provider = GeminiAdapter()
    else:
        from backend.src.infrastructure.ai.ollama.adapter import OllamaAdapter
        provider = OllamaAdapter()

    async with get_session() as session:
        repo = SQLArticleRepository(session)
        use_case = RunAIPipelineUseCase(
            article_repo=repo,
            primary_provider=provider,
        )
        return await use_case.execute(batch_size=batch_size)
