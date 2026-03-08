"""Use case: compute trending topics from recently collected articles.

Aggregates the top categories, keywords extracted from titles, and sentiment
distribution over the last N hours. Results are returned as a plain dict so
they can be cached in Redis or persisted as needed.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any

from backend.src.core.logging import get_logger
from backend.src.domain.entities.article import Article

log = get_logger(__name__)

# Stopwords to ignore when extracting title keywords
_STOPWORDS: frozenset[str] = frozenset({
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "is", "it", "its", "this", "that", "with", "as", "by", "from",
    "was", "are", "be", "been", "has", "have", "had", "will", "not", "no",
    "new", "how", "why", "what", "who", "says", "after", "over", "about",
})


class ComputeTrendsUseCase:
    """Computes trend metrics from a batch of articles.

    Designed to be dependency-injected with a list of recent articles so it
    stays framework-agnostic and easy to unit-test.
    """

    def __init__(self, articles: list[Article]) -> None:
        self._articles = articles

    def execute(self) -> dict[str, Any]:
        """Return a trends summary dict.

        Keys:
        - ``total_articles``: total in the batch
        - ``top_categories``: list of (category, count) sorted by count desc
        - ``top_keywords``: list of (keyword, count) from article titles
        - ``sentiment_distribution``: dict {-1: n, 0: n, 1: n}
        - ``computed_at``: ISO-8601 UTC timestamp
        """
        total = len(self._articles)
        log.info("compute_trends.start", total_articles=total)

        category_counter: Counter[str] = Counter()
        keyword_counter: Counter[str] = Counter()
        sentiment_counter: Counter[int] = Counter({-1: 0, 0: 0, 1: 0})

        for article in self._articles:
            # Categories
            if article.category:
                category_counter[article.category.lower()] += 1

            # Keywords from title (simple word tokenisation)
            for word in article.title.lower().split():
                cleaned = word.strip(".,!?\"'();:-")
                if cleaned and len(cleaned) > 2 and cleaned not in _STOPWORDS:
                    keyword_counter[cleaned] += 1

            # Sentiment
            sentiment_counter[article.sentiment] += 1

        result: dict[str, Any] = {
            "total_articles": total,
            "top_categories": category_counter.most_common(10),
            "top_keywords": keyword_counter.most_common(20),
            "sentiment_distribution": dict(sentiment_counter),
            "computed_at": datetime.now(timezone.utc).isoformat(),
        }

        log.info(
            "compute_trends.done",
            top_category=result["top_categories"][0] if result["top_categories"] else None,
            top_keyword=result["top_keywords"][0] if result["top_keywords"] else None,
        )
        return result
