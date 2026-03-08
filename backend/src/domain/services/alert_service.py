"""Domain service: keyword-based alert matching.

Pure function — no I/O, no dependencies, fully testable.
"""

from __future__ import annotations

from backend.src.domain.entities.article import Article


def match_articles(
    keywords: list[str],
    articles: list[Article],
) -> list[tuple[str, Article]]:
    """Return (keyword, article) pairs where the keyword appears in the article.

    Matching is case-insensitive and checks both title and summary fields.
    Each article may appear multiple times if it matches multiple keywords.

    Args:
        keywords: List of keyword strings to watch for.
        articles: List of articles to check.

    Returns:
        Ordered list of (keyword, article) tuples for every match found.
    """
    results: list[tuple[str, Article]] = []

    for keyword in keywords:
        kw_lower = keyword.lower().strip()
        if not kw_lower:
            continue
        for article in articles:
            haystack = " ".join(
                filter(
                    None,
                    [
                        article.title.lower(),
                        (article.summary or "").lower(),
                    ],
                )
            )
            if kw_lower in haystack:
                results.append((keyword, article))

    return results
