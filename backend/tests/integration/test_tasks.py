"""Integration tests for Celery tasks.

Tasks run synchronously via Celery's ALWAYS_EAGER setting so no broker is
needed. External dependencies (DB, collector) are mocked with unittest.mock.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.src.domain.entities.article import Article
from backend.src.domain.entities.source import Source, SourceType
from backend.src.use_cases.compute_trends import ComputeTrendsUseCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_source(**kwargs: Any) -> Source:
    return Source(
        id=uuid.uuid4(),
        name=kwargs.get("name", "Test Source"),
        url=kwargs.get("url", "https://example.com"),
        feed_url=kwargs.get("feed_url", "https://example.com/rss"),
        source_type=SourceType.RSS,
        language=kwargs.get("language", "en"),
        is_active=True,
    )


def _make_article(**kwargs: Any) -> Article:
    return Article(
        id=uuid.uuid4(),
        url=kwargs.get("url", "https://example.com/a"),
        url_hash=str(uuid.uuid4()),
        content_hash=str(uuid.uuid4()),
        title=kwargs.get("title", "Test Article"),
        body="body",
        language=kwargs.get("language", "en"),
        sentiment=kwargs.get("sentiment", 0),
        category=kwargs.get("category", None),
        collected_at=datetime.now(timezone.utc),
    )


# ---------------------------------------------------------------------------
# ComputeTrendsUseCase — pure unit tests (no Celery, no DB)
# ---------------------------------------------------------------------------

class TestComputeTrendsUseCase:
    def test_empty_articles_returns_zero_total(self) -> None:
        result = ComputeTrendsUseCase(articles=[]).execute()
        assert result["total_articles"] == 0
        assert result["top_categories"] == []
        assert result["top_keywords"] == []
        assert result["sentiment_distribution"] == {-1: 0, 0: 0, 1: 0}

    def test_counts_categories(self) -> None:
        articles = [
            _make_article(category="Tech"),
            _make_article(category="Tech"),
            _make_article(category="World"),
        ]
        result = ComputeTrendsUseCase(articles=articles).execute()
        categories = dict(result["top_categories"])
        assert categories["tech"] == 2
        assert categories["world"] == 1

    def test_top_categories_sorted_by_count(self) -> None:
        articles = [_make_article(category="World")] * 3 + [_make_article(category="Tech")] * 1
        result = ComputeTrendsUseCase(articles=articles).execute()
        assert result["top_categories"][0][0] == "world"

    def test_extracts_title_keywords(self) -> None:
        articles = [
            _make_article(title="Python releases new version"),
            _make_article(title="Python dominates AI landscape"),
        ]
        result = ComputeTrendsUseCase(articles=articles).execute()
        keywords = dict(result["top_keywords"])
        assert keywords.get("python", 0) == 2

    def test_stopwords_are_excluded(self) -> None:
        articles = [_make_article(title="The quick brown fox")]
        result = ComputeTrendsUseCase(articles=articles).execute()
        keywords = dict(result["top_keywords"])
        assert "the" not in keywords
        assert "a" not in keywords

    def test_sentiment_distribution_keys(self) -> None:
        articles = [
            _make_article(sentiment=1),
            _make_article(sentiment=1),
            _make_article(sentiment=-1),
            _make_article(sentiment=0),
        ]
        result = ComputeTrendsUseCase(articles=articles).execute()
        dist = result["sentiment_distribution"]
        assert dist[1] == 2
        assert dist[-1] == 1
        assert dist[0] == 1

    def test_computed_at_is_present(self) -> None:
        result = ComputeTrendsUseCase(articles=[]).execute()
        assert "computed_at" in result
        assert result["computed_at"].endswith("+00:00") or "Z" in result["computed_at"] or "T" in result["computed_at"]

    def test_total_articles_matches_input(self) -> None:
        articles = [_make_article() for _ in range(7)]
        result = ComputeTrendsUseCase(articles=articles).execute()
        assert result["total_articles"] == 7


# ---------------------------------------------------------------------------
# Celery tasks — run eagerly with mocked DB
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Celery tasks — run eagerly with mocked async internals
# NOTE: these tests are plain sync functions. The tasks call asyncio.run()
# internally which cannot be used inside a running event loop, so we must
# NOT mark them as @pytest.mark.asyncio.
# ---------------------------------------------------------------------------

def test_collect_feeds_task_calls_use_case() -> None:
    """collect_feeds_task runs successfully when the use case returns a result."""
    mock_result = {"Test Source": 3}

    with (
        patch(
            "backend.src.infrastructure.messaging.tasks.collect_feeds._run_collection",
            new=AsyncMock(return_value=mock_result),
        ),
    ):
        from backend.src.infrastructure.messaging.tasks.collect_feeds import (
            collect_feeds_task,
        )

        result = collect_feeds_task.apply().get()
        assert result == mock_result


def test_compute_trends_task_calls_use_case() -> None:
    """compute_trends_task runs successfully when the use case returns a result."""
    mock_result: dict[str, Any] = {
        "total_articles": 10,
        "top_categories": [("tech", 5)],
        "top_keywords": [("python", 3)],
        "sentiment_distribution": {-1: 1, 0: 5, 1: 4},
        "computed_at": "2026-03-08T00:00:00+00:00",
    }

    with (
        patch(
            "backend.src.infrastructure.messaging.tasks.compute_trends._run_trends",
            new=AsyncMock(return_value=mock_result),
        ),
    ):
        from backend.src.infrastructure.messaging.tasks.compute_trends import (
            compute_trends_task,
        )

        result = compute_trends_task.apply(kwargs={"hours": 24}).get()
        assert result["total_articles"] == 10
        assert result["top_keywords"][0][0] == "python"


def test_collect_feeds_task_retries_on_error() -> None:
    """collect_feeds_task raises after exhausting retries on persistent error."""
    from celery.exceptions import Retry

    with (
        patch(
            "backend.src.infrastructure.messaging.tasks.collect_feeds._run_collection",
            new=AsyncMock(side_effect=RuntimeError("DB down")),
        ),
    ):
        from backend.src.infrastructure.messaging.tasks.collect_feeds import (
            collect_feeds_task,
        )

        with pytest.raises(Retry):
            collect_feeds_task.apply().get()


def test_compute_trends_task_retries_on_error() -> None:
    """compute_trends_task raises after exhausting retries on persistent error."""
    from celery.exceptions import Retry

    with (
        patch(
            "backend.src.infrastructure.messaging.tasks.compute_trends._run_trends",
            new=AsyncMock(side_effect=RuntimeError("DB down")),
        ),
    ):
        from backend.src.infrastructure.messaging.tasks.compute_trends import (
            compute_trends_task,
        )

        with pytest.raises(Retry):
            compute_trends_task.apply(kwargs={"hours": 24}).get()


# ---------------------------------------------------------------------------
# run_ai_pipeline_task — Celery AI pipeline (eager + mocked)
# ---------------------------------------------------------------------------


def test_run_ai_pipeline_task_returns_counts() -> None:
    """run_ai_pipeline_task returns processed/skipped counts."""
    mock_result = {"processed": 5, "skipped": 1}

    with patch(
        "backend.src.infrastructure.messaging.tasks.run_ai_pipeline._run_pipeline",
        new=AsyncMock(return_value=mock_result),
    ):
        from backend.src.infrastructure.messaging.tasks.run_ai_pipeline import (
            run_ai_pipeline_task,
        )

        result = run_ai_pipeline_task.apply(kwargs={"batch_size": 20}).get()
        assert result["processed"] == 5
        assert result["skipped"] == 1


def test_run_ai_pipeline_task_retries_on_error() -> None:
    """run_ai_pipeline_task raises Retry on persistent error."""
    from celery.exceptions import Retry

    with patch(
        "backend.src.infrastructure.messaging.tasks.run_ai_pipeline._run_pipeline",
        new=AsyncMock(side_effect=RuntimeError("AI down")),
    ):
        from backend.src.infrastructure.messaging.tasks.run_ai_pipeline import (
            run_ai_pipeline_task,
        )

        with pytest.raises(Retry):
            run_ai_pipeline_task.apply(kwargs={"batch_size": 20}).get()
