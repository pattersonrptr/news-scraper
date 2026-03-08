"""RSS/Atom feed collector adapter.

Uses feedparser for parsing and httpx for async HTTP.
Respects per-source fetch interval via Redis caching.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import email.utils

import feedparser
import httpx

from backend.src.core.config import get_settings
from backend.src.core.exceptions import SourceFetchError
from backend.src.core.logging import get_logger

log = get_logger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; NewsScraper/0.1; +https://github.com/pattersonrptr/news-scraper)"
    ),
    "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
}

# Timeout settings for HTTP requests
_TIMEOUT = httpx.Timeout(connect=10.0, read=30.0, write=10.0, pool=5.0)


@dataclass
class RawArticle:
    """Raw article data as returned directly from a feed entry."""

    source_id: str
    url: str
    title: str
    body: str
    author: Optional[str]
    published_at: Optional[datetime]
    language: Optional[str]
    tags: list[str]
    image_url: Optional[str]


class RSSCollector:
    """Collects and normalizes articles from RSS/Atom feeds."""

    def __init__(self) -> None:
        self._settings = get_settings()

    async def collect(self, source_id: str, feed_url: str, language: Optional[str] = None) -> list[RawArticle]:
        """Fetch and parse a feed URL. Returns a list of RawArticle.

        Raises SourceFetchError on HTTP or parse errors.
        """
        log.info("rss_collect_start", source_id=source_id, feed_url=feed_url)

        try:
            raw_content = await self._fetch_feed(feed_url)
        except Exception as exc:
            raise SourceFetchError(feed_url, cause=exc) from exc

        feed = feedparser.parse(raw_content)

        if feed.bozo and feed.bozo_exception:
            log.warning(
                "feed_parse_warning",
                feed_url=feed_url,
                reason=str(feed.bozo_exception),
            )

        articles: list[RawArticle] = []
        for entry in feed.entries:
            try:
                article = self._parse_entry(entry, source_id=source_id, language=language)
                articles.append(article)
            except Exception as exc:  # noqa: BLE001
                log.warning("entry_parse_error", feed_url=feed_url, error=str(exc))
                continue

        log.info("rss_collect_done", source_id=source_id, count=len(articles))
        return articles

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _fetch_feed(self, url: str) -> bytes:
        """Async HTTP fetch of the feed URL."""
        async with httpx.AsyncClient(headers=_HEADERS, timeout=_TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    def _parse_entry(
        self, entry: feedparser.FeedParserDict, *, source_id: str, language: Optional[str]
    ) -> RawArticle:
        """Extract and normalize fields from a single feed entry."""
        url = self._get_url(entry)
        raw_title = entry.get("title") or ""
        title = self._get_text(str(raw_title)).strip() or "(no title)"
        body = self._get_body(entry)
        raw_author = entry.get("author")
        author: Optional[str] = str(raw_author) if raw_author else None
        published_at = self._parse_date(entry)
        raw_tags = entry.get("tags") or []
        tags: list[str] = [str(t.get("term", "")) for t in raw_tags if t.get("term")]  # type: ignore[union-attr]
        image_url = self._get_image(entry)

        return RawArticle(
            source_id=source_id,
            url=url,
            title=title,
            body=body,
            author=author,
            published_at=published_at,
            language=language,
            tags=tags,
            image_url=image_url,
        )

    @staticmethod
    def _get_url(entry: feedparser.FeedParserDict) -> str:
        """Get canonical URL from entry, preferring `link`."""
        url = entry.get("link") or entry.get("id") or ""
        if not url:
            raise ValueError("Feed entry has no URL")
        return str(url).strip()

    @staticmethod
    def _get_text(html_or_text: str) -> str:
        """Strip basic HTML tags for plain text (lightweight, no dep)."""
        import re
        return re.sub(r"<[^>]+>", " ", html_or_text).strip()

    def _get_body(self, entry: feedparser.FeedParserDict) -> str:
        """Extract best available body text from a feed entry."""
        # Try content first (full body), then summary
        content_list = entry.get("content") or []
        if content_list:
            return self._get_text(str(content_list[0].get("value") or ""))  # type: ignore[index]
        summary = entry.get("summary") or entry.get("description") or ""
        return self._get_text(str(summary))

    @staticmethod
    def _parse_date(entry: feedparser.FeedParserDict) -> Optional[datetime]:
        """Parse published date from feed entry, always return UTC-aware datetime."""
        # feedparser gives us a 9-tuple struct_time for *_parsed fields.
        # The FeedParserDict stubs are very loose, so we cast to Any once.
        from typing import Any as _Any
        for key in ("published_parsed", "updated_parsed", "created_parsed"):
            t: _Any = entry.get(key)
            if t is not None:
                try:
                    return datetime(
                        int(t[0]), int(t[1]), int(t[2]),
                        int(t[3]), int(t[4]), int(t[5]),
                        tzinfo=timezone.utc,
                    )
                except (TypeError, ValueError, IndexError):
                    pass

        # Fallback: try raw string with email.utils
        for key in ("published", "updated"):
            raw: _Any = entry.get(key)
            if raw and isinstance(raw, str):
                try:
                    parsed = email.utils.parsedate_to_datetime(raw)
                    return parsed.astimezone(timezone.utc)
                except Exception:  # noqa: BLE001
                    pass
        return None

    @staticmethod
    def _get_image(entry: feedparser.FeedParserDict) -> Optional[str]:
        """Try to find a thumbnail or media image URL."""
        media_content = entry.get("media_content") or []
        if media_content:
            val = media_content[0].get("url")  # type: ignore[index]
            return str(val) if val else None
        media_thumbnail = entry.get("media_thumbnail") or []
        if media_thumbnail:
            val = media_thumbnail[0].get("url")  # type: ignore[index]
            return str(val) if val else None
        return None
