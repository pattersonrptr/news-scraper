"""Use case: compile a daily news digest from recent articles."""

from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timezone

from backend.src.domain.entities.article import Article
from backend.src.domain.repositories import ArticleRepository

logger = logging.getLogger(__name__)


class CompileDigestUseCase:
    """Aggregate the most relevant articles from the last N hours into a digest.

    Groups articles by category and selects the top articles per group,
    ordered by relevance_score descending.
    """

    def __init__(
        self,
        article_repo: ArticleRepository,
        max_per_category: int = 5,
        hours: int = 24,
    ) -> None:
        self._repo = article_repo
        self._max_per_category = max_per_category
        self._hours = hours

    async def execute(self) -> dict:
        """Return a digest dict ready to be passed to the email template.

        Returns
        -------
        {
          "total_articles": int,
          "date_label": str,          # e.g. "March 8, 2026"
          "generated_at": str,        # ISO datetime string
          "top_categories": list[str],
          "sentiment_distribution": {-1: int, 0: int, 1: int},
          "sections": {category: [Article, ...]},
        }
        """
        articles = await self._repo.list_recent(hours=self._hours, limit=500)
        logger.info("Compiling digest from %d articles (last %dh)", len(articles), self._hours)

        now = datetime.now(timezone.utc)

        sentiment_dist: dict[int, int] = {-1: 0, 0: 0, 1: 0}
        by_category: dict[str, list[Article]] = defaultdict(list)

        for article in articles:
            sentiment_dist[article.sentiment] = sentiment_dist.get(article.sentiment, 0) + 1
            category = (article.category or "other").lower()
            by_category[category].append(article)

        # Sort each category bucket by relevance_score desc, take top N
        sections: dict[str, list[Article]] = {}
        for cat, arts in sorted(
            by_category.items(),
            key=lambda kv: len(kv[1]),
            reverse=True,
        ):
            sorted_arts = sorted(arts, key=lambda a: a.relevance_score, reverse=True)
            sections[cat] = sorted_arts[: self._max_per_category]

        top_categories = list(sections.keys())

        return {
            "total_articles": len(articles),
            "date_label": now.strftime("%B %-d, %Y"),
            "generated_at": now.strftime("%Y-%m-%d %H:%M"),
            "top_categories": top_categories,
            "sentiment_distribution": sentiment_dist,
            "sections": sections,
        }
