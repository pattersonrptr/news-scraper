"""Unit tests for RelevanceScoringService."""

from __future__ import annotations

import uuid

import pytest

from backend.src.domain.entities import Article, UserProfile
from backend.src.domain.services.relevance_scoring import RelevanceScoringService


@pytest.fixture()
def service() -> RelevanceScoringService:
    return RelevanceScoringService()


@pytest.fixture()
def profile_tech() -> UserProfile:
    return UserProfile(
        id=uuid.uuid4(),
        email="test@example.com",
        explicit_interests=["tech", "economy"],
        implicit_weights={"tech": 0.8, "economy": 0.4, "sports": 0.1},
        alert_keywords=["Python", "AI", "Bitcoin"],
    )


@pytest.fixture()
def article_tech() -> Article:
    return Article(
        id=uuid.uuid4(),
        title="Python 3.13 AI features announced",
        body="The Python community announced major AI integrations in version 3.13...",
        category="tech",
    )


class TestRelevanceScoringService:

    def test_full_match_scores_high(
        self, service: RelevanceScoringService, article_tech: Article, profile_tech: UserProfile
    ) -> None:
        score = service.compute(article_tech, profile_tech)
        # category in explicit (0.5) + implicit 0.8 (0.3*0.8=0.24) + keywords match
        assert score > 0.7

    def test_no_match_scores_zero(
        self, service: RelevanceScoringService, profile_tech: UserProfile
    ) -> None:
        article = Article(
            title="Local weather report",
            body="Temperatures will drop this weekend.",
            category="weather",
        )
        score = service.compute(article, profile_tech)
        assert score == 0.0

    def test_score_is_clamped_to_one(
        self, service: RelevanceScoringService, profile_tech: UserProfile
    ) -> None:
        article = Article(
            title="Python AI Bitcoin news",
            body="Python AI Bitcoin",
            category="tech",
        )
        score = service.compute(article, profile_tech)
        assert 0.0 <= score <= 1.0

    def test_empty_profile_scores_zero(self, service: RelevanceScoringService) -> None:
        article = Article(title="Any news", body="Any body", category="tech")
        profile = UserProfile(email="empty@example.com")
        score = service.compute(article, profile)
        assert score == 0.0

    def test_keyword_contributes_to_score(
        self, service: RelevanceScoringService
    ) -> None:
        # Article has no category match but keywords hit
        article = Article(
            title="Bitcoin price surges",
            body="Bitcoin reached new highs today.",
            category="finance",
        )
        profile = UserProfile(
            email="t@t.com",
            explicit_interests=["sports"],
            implicit_weights={},
            alert_keywords=["Bitcoin"],
        )
        score = service.compute(article, profile)
        # Only keyword score contributes: 1 match / 1 keyword * 0.2 = 0.2
        assert score == pytest.approx(0.2)
