"""Unit tests for RunAIPipelineUseCase."""

from __future__ import annotations

import uuid
from dataclasses import replace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.core.exceptions import AIProviderError, AIRateLimitError
from backend.src.domain.entities.article import Article
from backend.src.domain.ports.ai_provider import AIResult
from backend.src.use_cases.run_ai_pipeline import RunAIPipelineUseCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_article(**kwargs) -> Article:  # type: ignore[no-untyped-def]
    defaults = dict(
        id=uuid.uuid4(),
        title="Breaking News",
        body="Some article body text.",
        is_processed=False,
        collected_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Article(**defaults)  # type: ignore[arg-type]


_GOOD_RESULT = AIResult(
    summary="Short summary.",
    sentiment=1,
    sentiment_score=0.9,
    category="technology",
    entities={"people": [], "orgs": [], "places": []},
)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunAIPipelineUseCase:
    @pytest.mark.asyncio
    async def test_processes_articles_successfully(self):
        articles = [_make_article(), _make_article()]
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=articles)
        mock_repo.update = AsyncMock(side_effect=lambda a: a)

        mock_provider = AsyncMock()
        mock_provider.analyze = AsyncMock(return_value=_GOOD_RESULT)

        use_case = RunAIPipelineUseCase(
            article_repo=mock_repo,
            primary_provider=mock_provider,
        )
        result = await use_case.execute(batch_size=10)

        assert result["processed"] == 2
        assert result["skipped"] == 0
        assert mock_repo.update.call_count == 2

    @pytest.mark.asyncio
    async def test_article_marked_as_processed_after_analysis(self):
        article = _make_article()
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[article])

        updated_articles: list[Article] = []

        async def capture_update(a: Article) -> Article:
            updated_articles.append(a)
            return a

        mock_repo.update = AsyncMock(side_effect=capture_update)

        mock_provider = AsyncMock()
        mock_provider.analyze = AsyncMock(return_value=_GOOD_RESULT)

        use_case = RunAIPipelineUseCase(
            article_repo=mock_repo,
            primary_provider=mock_provider,
        )
        await use_case.execute()

        assert len(updated_articles) == 1
        saved = updated_articles[0]
        assert saved.is_processed is True
        assert saved.summary == "Short summary."
        assert saved.sentiment == 1
        assert saved.category == "technology"

    @pytest.mark.asyncio
    async def test_skips_article_on_provider_error(self):
        articles = [_make_article(), _make_article()]
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=articles)
        mock_repo.update = AsyncMock(side_effect=lambda a: a)

        mock_provider = AsyncMock()
        mock_provider.analyze = AsyncMock(
            side_effect=AIProviderError("gemini")
        )

        use_case = RunAIPipelineUseCase(
            article_repo=mock_repo,
            primary_provider=mock_provider,
        )
        result = await use_case.execute()

        assert result["processed"] == 0
        assert result["skipped"] == 2
        mock_repo.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_falls_back_to_ollama_on_rate_limit(self):
        article = _make_article()
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[article])
        mock_repo.update = AsyncMock(side_effect=lambda a: a)

        mock_primary = AsyncMock()
        mock_primary.analyze = AsyncMock(side_effect=AIRateLimitError("gemini"))

        mock_fallback = AsyncMock()
        mock_fallback.analyze = AsyncMock(return_value=_GOOD_RESULT)

        with patch(
            "backend.src.use_cases.run_ai_pipeline.get_settings"
        ) as mock_settings:
            mock_settings.return_value.ollama_fallback = True
            from backend.src.core.config.settings import AIProvider
            mock_settings.return_value.ai_provider = AIProvider.GEMINI

            with patch(
                "backend.src.use_cases.run_ai_pipeline.RunAIPipelineUseCase._get_fallback",
                return_value=mock_fallback,
            ):
                use_case = RunAIPipelineUseCase(
                    article_repo=mock_repo,
                    primary_provider=mock_primary,
                )
                result = await use_case.execute()

        assert result["processed"] == 1
        assert result["skipped"] == 0

    @pytest.mark.asyncio
    async def test_skips_when_fallback_also_fails(self):
        article = _make_article()
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[article])
        mock_repo.update = AsyncMock()

        mock_primary = AsyncMock()
        mock_primary.analyze = AsyncMock(side_effect=AIRateLimitError("gemini"))

        mock_fallback = AsyncMock()
        mock_fallback.analyze = AsyncMock(
            side_effect=AIProviderError("ollama")
        )

        with patch(
            "backend.src.use_cases.run_ai_pipeline.get_settings"
        ) as mock_settings:
            mock_settings.return_value.ollama_fallback = True
            from backend.src.core.config.settings import AIProvider
            mock_settings.return_value.ai_provider = AIProvider.GEMINI

            with patch(
                "backend.src.use_cases.run_ai_pipeline.RunAIPipelineUseCase._get_fallback",
                return_value=mock_fallback,
            ):
                use_case = RunAIPipelineUseCase(
                    article_repo=mock_repo,
                    primary_provider=mock_primary,
                )
                result = await use_case.execute()

        assert result["processed"] == 0
        assert result["skipped"] == 1

    @pytest.mark.asyncio
    async def test_no_articles_returns_zeros(self):
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[])
        mock_provider = AsyncMock()

        use_case = RunAIPipelineUseCase(
            article_repo=mock_repo,
            primary_provider=mock_provider,
        )
        result = await use_case.execute()

        assert result == {"processed": 0, "skipped": 0}
        mock_provider.analyze.assert_not_called()

    @pytest.mark.asyncio
    async def test_batch_size_passed_to_list_unprocessed(self):
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[])
        mock_provider = AsyncMock()

        use_case = RunAIPipelineUseCase(
            article_repo=mock_repo,
            primary_provider=mock_provider,
        )
        await use_case.execute(batch_size=5)

        mock_repo.list_unprocessed.assert_called_once_with(limit=5)

    @pytest.mark.asyncio
    async def test_rate_limit_no_fallback_configured_skips(self):
        article = _make_article()
        mock_repo = AsyncMock()
        mock_repo.list_unprocessed = AsyncMock(return_value=[article])
        mock_repo.update = AsyncMock()

        mock_primary = AsyncMock()
        mock_primary.analyze = AsyncMock(side_effect=AIRateLimitError("gemini"))

        with patch(
            "backend.src.use_cases.run_ai_pipeline.get_settings"
        ) as mock_settings:
            mock_settings.return_value.ollama_fallback = False
            from backend.src.core.config.settings import AIProvider
            mock_settings.return_value.ai_provider = AIProvider.GEMINI

            use_case = RunAIPipelineUseCase(
                article_repo=mock_repo,
                primary_provider=mock_primary,
            )
            result = await use_case.execute()

        assert result["processed"] == 0
        assert result["skipped"] == 1
