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

# Stopwords to ignore when extracting keywords.
# Covers both English and Portuguese (pt-BR) functional words so that common
# grammatical tokens don't pollute the Top Keywords chart.
_STOPWORDS: frozenset[str] = frozenset({
    # ── English ──────────────────────────────────────────────────────────────
    "a", "an", "the", "in", "on", "at", "to", "for", "of", "and", "or",
    "but", "is", "it", "its", "this", "that", "with", "as", "by", "from",
    "was", "are", "be", "been", "has", "have", "had", "will", "not", "no",
    "new", "how", "why", "what", "who", "says", "after", "over", "about",
    "up", "out", "into", "than", "more", "also", "just", "can", "all",
    "one", "two", "his", "her", "him", "she", "he", "they", "their",
    "we", "our", "you", "your", "me", "my", "do", "did", "does", "so",
    "if", "when", "which", "where", "would", "could", "should", "may",
    "get", "now", "say", "said", "then", "only", "off", "got", "still",
    "amid", "amid", "per", "via", "ago", "yet",
    # ── Portuguese (pt-BR) ───────────────────────────────────────────────────
    # articles / prepositions / contractions
    "o", "a", "os", "as", "um", "uma", "uns", "umas",
    "de", "do", "da", "dos", "das", "no", "na", "nos", "nas",
    "ao", "aos", "à", "às", "pelo", "pela", "pelos", "pelas",
    "em", "com", "por", "para", "entre", "sobre", "após",
    "até", "desde", "sem", "sob", "num", "numa", "nuns", "numas",
    "dum", "duma", "duns", "dumas",
    # pronouns
    "eu", "tu", "ele", "ela", "nós", "vós", "eles", "elas",
    "me", "te", "se", "lhe", "nos", "vos", "lhes",
    "isso", "este", "esta", "estes", "estas", "esse", "essa",
    "esses", "essas", "aquele", "aquela", "aqueles", "aquelas",
    "que", "quem", "qual", "quais",
    # conjunctions / adverbs
    "e", "ou", "mas", "porém", "contudo", "entretanto", "todavia",
    "porque", "pois", "como", "quando", "onde", "embora",
    "já", "não", "nem", "só", "sim", "muito", "mais", "menos",
    "bem", "mal", "assim", "ainda", "também", "sempre", "nunca",
    "aqui", "ali", "lá", "cá", "então", "antes", "depois",
    "logo", "apenas", "mesmo", "tanto", "tão", "seu", "sua",
    "seus", "suas", "meu", "minha", "meus", "minhas",
    # auxiliary verbs / copula forms
    "é", "são", "era", "eram", "ser", "estar", "está", "estão",
    "foi", "foram", "ser", "ter", "tem", "têm", "tinha", "tinham",
    "ter", "haver", "há", "houve", "diz", "disse", "afirma",
    "vai", "vão", "vir", "ser", "fazer", "faz",
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

            # Keywords from title + summary (simple word tokenisation).
            # Use len > 3 to skip most 2-3 letter functional words that slipped
            # through the stopword list (e.g. "diz", "por", "com").
            text_sources = [article.title]
            if article.summary:
                text_sources.append(article.summary)
            for text in text_sources:
                for word in text.lower().split():
                    cleaned = word.strip(".,!?\"'();:-«»""''")
                    if cleaned and len(cleaned) > 3 and cleaned not in _STOPWORDS:
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
