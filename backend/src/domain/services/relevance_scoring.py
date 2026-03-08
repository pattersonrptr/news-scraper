"""Relevance scoring domain service.

Computes a personalized relevance score for an article given a user profile.

Score formula (weights defined in SPEC.md §6):
  - Category match vs explicit_interests  : weight 0.5
  - Implicit learned weight for category  : weight 0.3
  - Keyword overlap (title + body)        : weight 0.2
"""

from __future__ import annotations

from backend.src.domain.entities import Article, UserProfile


class RelevanceScoringService:
    """Pure domain service — no I/O, fully unit-testable."""

    EXPLICIT_WEIGHT: float = 0.5
    IMPLICIT_WEIGHT: float = 0.3
    KEYWORD_WEIGHT: float = 0.2

    def compute(self, article: Article, profile: UserProfile) -> float:
        """Return a relevance score in [0.0, 1.0]."""
        explicit = self._explicit_score(article, profile)
        implicit = self._implicit_score(article, profile)
        keyword = self._keyword_score(article, profile)

        score = (
            explicit * self.EXPLICIT_WEIGHT
            + implicit * self.IMPLICIT_WEIGHT
            + keyword * self.KEYWORD_WEIGHT
        )
        return round(min(max(score, 0.0), 1.0), 4)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _explicit_score(self, article: Article, profile: UserProfile) -> float:
        """1.0 if article category is in user's explicit interests, else 0.0."""
        if not profile.explicit_interests or not article.category:
            return 0.0
        category_lower = article.category.lower()
        interests_lower = [i.lower() for i in profile.explicit_interests]
        return 1.0 if category_lower in interests_lower else 0.0

    def _implicit_score(self, article: Article, profile: UserProfile) -> float:
        """Learned weight for the article's category, or 0.0 if unknown."""
        if not profile.implicit_weights or not article.category:
            return 0.0
        return profile.implicit_weights.get(article.category.lower(), 0.0)

    def _keyword_score(self, article: Article, profile: UserProfile) -> float:
        """Fraction of alert keywords that appear in the article title+body."""
        if not profile.alert_keywords:
            return 0.0
        searchable = (article.title + " " + article.body).lower()
        matches = sum(1 for kw in profile.alert_keywords if kw.lower() in searchable)
        return matches / len(profile.alert_keywords)
