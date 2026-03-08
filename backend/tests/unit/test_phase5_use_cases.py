"""Unit tests for Phase 5 use cases and domain service:
- alert_service.match_articles
- SendAlertsUseCase
- CompileDigestUseCase
- UpdateImplicitWeightsUseCase
"""

from __future__ import annotations

import uuid
from datetime import datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.src.domain.entities.alert import Alert, NotificationChannel
from backend.src.domain.entities.article import Article
from backend.src.domain.entities.user_profile import UserProfile
from backend.src.domain.services.alert_service import match_articles
from backend.src.use_cases.compile_digest import CompileDigestUseCase
from backend.src.use_cases.send_alerts import SendAlertsUseCase
from backend.src.use_cases.update_implicit_weights import UpdateImplicitWeightsUseCase


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _article(**kwargs) -> Article:  # type: ignore[no-untyped-def]
    defaults = dict(
        id=uuid.uuid4(),
        title=kwargs.pop("title", "Headline"),
        body="body",
        summary=kwargs.pop("summary", None),
        category=kwargs.pop("category", None),
        sentiment=kwargs.pop("sentiment", 0),
        is_read=kwargs.pop("is_read", False),
        relevance_score=kwargs.pop("relevance_score", 0.5),
        collected_at=datetime.now(timezone.utc),
    )
    defaults.update(kwargs)
    return Article(**defaults)  # type: ignore[arg-type]


def _profile(**kwargs) -> UserProfile:  # type: ignore[no-untyped-def]
    defaults = dict(
        id=_USER_ID,
        email="user@example.com",
        notification_email="user@example.com",
        alert_keywords=kwargs.pop("keywords", []),
        implicit_weights=kwargs.pop("implicit_weights", {}),
        digest_time=time(8, 0),
    )
    defaults.update(kwargs)
    return UserProfile(**defaults)  # type: ignore[arg-type]


# ===========================================================================
# AlertService — match_articles
# ===========================================================================


class TestAlertServiceMatchArticles:
    def test_no_keywords_returns_empty(self):
        articles = [_article(title="Python 3.13 released")]
        assert match_articles([], articles) == []

    def test_no_articles_returns_empty(self):
        assert match_articles(["python"], []) == []

    def test_keyword_in_title_matches(self):
        articles = [_article(title="Python 3.13 released")]
        results = match_articles(["python"], articles)
        assert len(results) == 1
        assert results[0][0] == "python"

    def test_keyword_in_summary_matches(self):
        articles = [_article(title="New release", summary="Python 3.13 is out")]
        results = match_articles(["python"], articles)
        assert len(results) == 1

    def test_match_is_case_insensitive(self):
        articles = [_article(title="PYTHON announces new release")]
        results = match_articles(["python"], articles)
        assert len(results) == 1

    def test_keyword_not_found_returns_empty(self):
        articles = [_article(title="Rust is fast")]
        results = match_articles(["python"], articles)
        assert results == []

    def test_multiple_keywords_multiple_matches(self):
        article_py = _article(title="Python release")
        article_rust = _article(title="Rust is fast")
        results = match_articles(["python", "rust"], [article_py, article_rust])
        assert len(results) == 2

    def test_article_matches_multiple_keywords(self):
        article = _article(title="Python and Rust are both great")
        results = match_articles(["python", "rust"], [article])
        assert len(results) == 2

    def test_blank_keyword_is_skipped(self):
        articles = [_article(title="Python released")]
        results = match_articles(["", "  ", "python"], articles)
        assert len(results) == 1


# ===========================================================================
# SendAlertsUseCase
# ===========================================================================


class TestSendAlertsUseCase:
    def _make_use_case(
        self,
        *,
        profile: UserProfile | None = None,
        articles: list[Article] | None = None,
        recent_alerts: list[Alert] | None = None,
        email_raises: bool = False,
    ) -> tuple[SendAlertsUseCase, AsyncMock, AsyncMock, AsyncMock]:
        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(return_value=profile)

        article_repo = AsyncMock()
        article_repo.list_recent = AsyncMock(return_value=articles or [])

        alert_repo = AsyncMock()
        alert_repo.list_recent_by_keyword = AsyncMock(return_value=recent_alerts or [])
        alert_repo.save = AsyncMock(side_effect=lambda a: a)

        email = AsyncMock()
        if email_raises:
            email.send_alert_email = AsyncMock(side_effect=RuntimeError("SMTP error"))
        else:
            email.send_alert_email = AsyncMock()

        use_case = SendAlertsUseCase(
            article_repo=article_repo,
            alert_repo=alert_repo,
            profile_repo=profile_repo,
            email_adapter=email,
        )
        return use_case, article_repo, alert_repo, email

    @pytest.mark.asyncio
    async def test_no_keywords_returns_zero(self):
        profile = _profile(keywords=[])
        use_case, *_ = self._make_use_case(profile=profile)
        result = await use_case.execute()
        assert result == {"matched": 0, "sent": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_no_profile_returns_zero(self):
        use_case, *_ = self._make_use_case(profile=None)
        result = await use_case.execute()
        assert result == {"matched": 0, "sent": 0, "skipped": 0}

    @pytest.mark.asyncio
    async def test_sends_email_on_match(self):
        profile = _profile(keywords=["python"])
        articles = [_article(title="Python 3.13 released")]
        use_case, _, alert_repo, email = self._make_use_case(
            profile=profile, articles=articles
        )
        result = await use_case.execute()
        assert result["sent"] == 1
        assert result["matched"] == 1
        email.send_alert_email.assert_awaited_once()
        alert_repo.save.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rate_limit_skips_if_already_sent(self):
        profile = _profile(keywords=["python"])
        articles = [_article(title="Python 3.13 released")]
        recent = [Alert(trigger_keyword="python", channel=NotificationChannel.EMAIL)]
        use_case, _, _, email = self._make_use_case(
            profile=profile, articles=articles, recent_alerts=recent
        )
        result = await use_case.execute()
        assert result["skipped"] == 1
        assert result["sent"] == 0
        email.send_alert_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_smtp_failure_counts_as_skipped(self):
        profile = _profile(keywords=["python"])
        articles = [_article(title="Python 3.13 released")]
        use_case, _, _, email = self._make_use_case(
            profile=profile, articles=articles, email_raises=True
        )
        result = await use_case.execute()
        assert result["skipped"] == 1
        assert result["sent"] == 0


# ===========================================================================
# CompileDigestUseCase
# ===========================================================================


class TestCompileDigestUseCase:
    @pytest.mark.asyncio
    async def test_empty_articles_returns_zero_total(self):
        repo = AsyncMock()
        repo.list_recent = AsyncMock(return_value=[])
        use_case = CompileDigestUseCase(article_repo=repo)
        result = await use_case.execute()
        assert result["total_articles"] == 0
        assert result["sections"] == {}

    @pytest.mark.asyncio
    async def test_groups_articles_by_category(self):
        articles = [
            _article(title="Tech news", category="technology"),
            _article(title="Sports update", category="sports"),
            _article(title="More tech", category="technology"),
        ]
        repo = AsyncMock()
        repo.list_recent = AsyncMock(return_value=articles)
        use_case = CompileDigestUseCase(article_repo=repo)
        result = await use_case.execute()
        assert "technology" in result["sections"]
        assert "sports" in result["sections"]
        assert len(result["sections"]["technology"]) == 2

    @pytest.mark.asyncio
    async def test_respects_max_per_category(self):
        articles = [_article(category="technology") for _ in range(10)]
        repo = AsyncMock()
        repo.list_recent = AsyncMock(return_value=articles)
        use_case = CompileDigestUseCase(article_repo=repo, max_per_category=3)
        result = await use_case.execute()
        assert len(result["sections"]["technology"]) == 3

    @pytest.mark.asyncio
    async def test_returns_sentiment_distribution(self):
        articles = [
            _article(sentiment=1),
            _article(sentiment=-1),
            _article(sentiment=0),
        ]
        repo = AsyncMock()
        repo.list_recent = AsyncMock(return_value=articles)
        use_case = CompileDigestUseCase(article_repo=repo)
        result = await use_case.execute()
        dist = result["sentiment_distribution"]
        assert dist[1] == 1
        assert dist[-1] == 1
        assert dist[0] == 1

    @pytest.mark.asyncio
    async def test_none_category_goes_to_other(self):
        articles = [_article(category=None)]
        repo = AsyncMock()
        repo.list_recent = AsyncMock(return_value=articles)
        use_case = CompileDigestUseCase(article_repo=repo)
        result = await use_case.execute()
        assert "other" in result["sections"]


# ===========================================================================
# UpdateImplicitWeightsUseCase
# ===========================================================================


class TestUpdateImplicitWeightsUseCase:
    @pytest.mark.asyncio
    async def test_no_read_articles_returns_zeros(self):
        article_repo = AsyncMock()
        article_repo.list_recent = AsyncMock(return_value=[])
        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(return_value=_profile())
        use_case = UpdateImplicitWeightsUseCase(
            article_repo=article_repo, profile_repo=profile_repo
        )
        result = await use_case.execute()
        assert result == {"articles_read": 0, "categories_updated": 0}
        profile_repo.update_implicit_weights.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_increments_weight_for_read_category(self):
        articles = [_article(category="technology", is_read=True)]
        article_repo = AsyncMock()
        article_repo.list_recent = AsyncMock(return_value=articles)

        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(return_value=_profile())
        profile_repo.update_implicit_weights = AsyncMock()

        use_case = UpdateImplicitWeightsUseCase(
            article_repo=article_repo, profile_repo=profile_repo
        )
        result = await use_case.execute()

        assert result["articles_read"] == 1
        assert result["categories_updated"] == 1
        call_kwargs = profile_repo.update_implicit_weights.call_args[1]
        weights = call_kwargs["weights"]
        assert "technology" in weights
        assert weights["technology"] > 0.0

    @pytest.mark.asyncio
    async def test_unread_articles_are_ignored(self):
        articles = [_article(category="sports", is_read=False)]
        article_repo = AsyncMock()
        article_repo.list_recent = AsyncMock(return_value=articles)

        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(return_value=_profile())

        use_case = UpdateImplicitWeightsUseCase(
            article_repo=article_repo, profile_repo=profile_repo
        )
        result = await use_case.execute()
        assert result["articles_read"] == 0

    @pytest.mark.asyncio
    async def test_weight_capped_at_1(self):
        articles = [_article(category="tech", is_read=True)] * 100
        article_repo = AsyncMock()
        article_repo.list_recent = AsyncMock(return_value=articles)

        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(
            return_value=_profile(implicit_weights={"tech": 0.99})
        )
        profile_repo.update_implicit_weights = AsyncMock()

        use_case = UpdateImplicitWeightsUseCase(
            article_repo=article_repo, profile_repo=profile_repo
        )
        await use_case.execute()
        call_kwargs = profile_repo.update_implicit_weights.call_args[1]
        assert call_kwargs["weights"]["tech"] <= 1.0

    @pytest.mark.asyncio
    async def test_no_profile_returns_zeros(self):
        article_repo = AsyncMock()
        profile_repo = AsyncMock()
        profile_repo.get_default = AsyncMock(return_value=None)
        use_case = UpdateImplicitWeightsUseCase(
            article_repo=article_repo, profile_repo=profile_repo
        )
        result = await use_case.execute()
        assert result == {"articles_read": 0, "categories_updated": 0}
