"""Use case: run the AI analysis pipeline over unprocessed articles."""

from __future__ import annotations

import logging
from dataclasses import replace

from backend.src.core.config.settings import AIProvider, get_settings
from backend.src.core.exceptions import AIProviderError, AIRateLimitError
from backend.src.domain.ports.ai_provider import AIProviderPort, AIResult
from backend.src.domain.repositories import ArticleRepository

logger = logging.getLogger(__name__)


class RunAIPipelineUseCase:
    """Fetch unprocessed articles, run AI analysis, and persist results.

    Fallback strategy:
    - If the primary provider is Gemini and raises AIRateLimitError,
      and ``ollama_fallback`` is True, the use case will instantiate an
      OllamaAdapter and retry the failed article — then continue using
      Ollama for the remainder of the batch.
    """

    def __init__(
        self,
        article_repo: ArticleRepository,
        primary_provider: AIProviderPort,
    ) -> None:
        self._repo = article_repo
        self._primary = primary_provider
        self._fallback: AIProviderPort | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def execute(
        self,
        batch_size: int = 20,
        commit_fn: object = None,
    ) -> dict[str, int]:
        """Analyse up to *batch_size* unprocessed articles.

        Parameters
        ----------
        batch_size:
            Maximum number of articles to process per run.
        commit_fn:
            Optional async callable invoked after each article is persisted.
            Use this to commit per-article instead of once at the end.

        Returns
        -------
        dict with keys:
          - processed: number of articles successfully analysed
          - skipped: number of articles that failed analysis
        """
        settings = get_settings()
        articles = await self._repo.list_unprocessed(limit=batch_size)
        logger.info("AI pipeline: %d articles to process", len(articles))

        processed = 0
        skipped = 0
        use_fallback = False  # once we switch to fallback we stay there

        for article in articles:
            provider = self._get_fallback() if use_fallback else self._primary

            try:
                result: AIResult = await provider.analyze(
                    title=article.title,
                    body=article.body,
                )
            except AIRateLimitError:
                if (
                    not use_fallback
                    and settings.ollama_fallback
                    and settings.ai_provider == AIProvider.GEMINI
                ):
                    logger.warning(
                        "Gemini rate limit hit — switching to Ollama fallback"
                    )
                    use_fallback = True
                    fallback = self._get_fallback()
                    try:
                        result = await fallback.analyze(
                            title=article.title,
                            body=article.body,
                        )
                    except AIProviderError as exc:
                        logger.error(
                            "Ollama fallback also failed for article %s: %s",
                            article.id,
                            exc,
                        )
                        skipped += 1
                        continue
                else:
                    logger.error(
                        "Rate limit on %s and no fallback available",
                        "ollama" if use_fallback else "gemini",
                    )
                    skipped += 1
                    continue
            except AIProviderError as exc:
                logger.error(
                    "AI analysis failed for article %s: %s", article.id, exc
                )
                skipped += 1
                continue

            updated = replace(
                article,
                summary=result.summary,
                sentiment=result.sentiment,
                sentiment_score=result.sentiment_score,
                category=result.category,
                entities=result.entities,
                is_processed=True,
            )
            await self._repo.update(updated)
            if commit_fn is not None:
                await commit_fn()  # type: ignore[misc]
            processed += 1

        logger.info(
            "AI pipeline complete: processed=%d skipped=%d", processed, skipped
        )
        return {"processed": processed, "skipped": skipped}

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_fallback(self) -> AIProviderPort:
        """Lazily instantiate the Ollama fallback adapter."""
        if self._fallback is None:
            from backend.src.infrastructure.ai.ollama.adapter import OllamaAdapter
            self._fallback = OllamaAdapter()
        return self._fallback
