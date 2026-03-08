"""Value objects for the domain layer."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


# UTM and tracking params to strip during URL normalization
_TRACKING_PARAMS = frozenset(
    {
        "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
        "fbclid", "gclid", "ref", "source", "_ga",
    }
)


@dataclass(frozen=True)
class ArticleHash:
    """Immutable pair of hashes used for deduplication."""

    url_hash: str       # SHA-256 of normalized URL
    content_hash: str   # SHA-256 of title + first 500 chars of body

    @classmethod
    def from_article_data(cls, url: str, title: str, body: str) -> "ArticleHash":
        """Create hashes from raw article data."""
        normalized = _normalize_url(url)
        url_hash = hashlib.sha256(normalized.encode()).hexdigest()
        content_hash = hashlib.sha256(
            (title.strip().lower() + body[:500].strip().lower()).encode()
        ).hexdigest()
        return cls(url_hash=url_hash, content_hash=content_hash)


@dataclass(frozen=True)
class Sentiment:
    """Sentiment value object."""

    label: int      # -1 negative | 0 neutral | 1 positive
    score: float    # confidence in range [0.0, 1.0]

    def __post_init__(self) -> None:
        if self.label not in (-1, 0, 1):
            raise ValueError(f"Sentiment label must be -1, 0, or 1. Got: {self.label}")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError(f"Sentiment score must be in [0, 1]. Got: {self.score}")

    @property
    def label_name(self) -> str:
        """Human-readable label."""
        return {-1: "negative", 0: "neutral", 1: "positive"}[self.label]


@dataclass(frozen=True)
class RelevanceScore:
    """Personalized relevance score for an article."""

    value: float    # range [0.0, 1.0]

    def __post_init__(self) -> None:
        if not (0.0 <= self.value <= 1.0):
            raise ValueError(f"RelevanceScore must be in [0, 1]. Got: {self.value}")


def _normalize_url(url: str) -> str:
    """Normalize a URL for deduplication: strip tracking params, www, trailing slash."""
    parsed = urlparse(url.strip())
    # Remove www prefix
    netloc = re.sub(r"^www\.", "", parsed.netloc)
    # Strip tracking query params
    qs = parse_qs(parsed.query, keep_blank_values=False)
    clean_qs = {k: v for k, v in qs.items() if k not in _TRACKING_PARAMS}
    clean_query = urlencode(sorted(clean_qs.items()), doseq=True)
    # Rebuild without fragment, lowercase scheme+host, strip trailing slash
    normalized = urlunparse((
        parsed.scheme.lower(),
        netloc.lower(),
        parsed.path.rstrip("/") or "/",
        "",
        clean_query,
        "",
    ))
    return normalized
