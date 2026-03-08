"""Integration tests for RSSCollector.

Uses respx to mock httpx requests — no real network calls.
"""

from __future__ import annotations

import textwrap
import uuid

import pytest
import respx
from httpx import Response

from backend.src.core.exceptions import SourceFetchError
from backend.src.infrastructure.collectors.rss.collector import RSSCollector

# ---------------------------------------------------------------------------
# RSS XML fixtures
# ---------------------------------------------------------------------------

_VALID_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"
         xmlns:media="http://search.yahoo.com/mrss/"
         xmlns:dc="http://purl.org/dc/elements/1.1/">
      <channel>
        <title>Test Feed</title>
        <link>https://example.com</link>
        <description>A test feed</description>
        <item>
          <title>Article One</title>
          <link>https://example.com/article-1</link>
          <description>Body of article one.</description>
          <author>Alice</author>
          <pubDate>Mon, 01 Jan 2024 12:00:00 +0000</pubDate>
          <category>Tech</category>
          <media:thumbnail url="https://example.com/img1.jpg"/>
        </item>
        <item>
          <title>Article Two</title>
          <link>https://example.com/article-2</link>
          <description>Body of article two.</description>
          <pubDate>Tue, 02 Jan 2024 08:00:00 +0000</pubDate>
        </item>
      </channel>
    </rss>
""").encode()

_EMPTY_RSS = textwrap.dedent("""\
    <?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Empty Feed</title>
        <link>https://example.com</link>
        <description>No items here</description>
      </channel>
    </rss>
""").encode()

_FEED_URL = "https://example.com/feed.rss"
_SOURCE_ID = str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@respx.mock
async def test_collect_happy_path_returns_two_articles() -> None:
    """Collector returns one RawArticle per feed item."""
    respx.get(_FEED_URL).mock(return_value=Response(200, content=_VALID_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL, language="en")

    assert len(articles) == 2


@pytest.mark.asyncio
@respx.mock
async def test_collect_article_fields_are_parsed_correctly() -> None:
    """First article has correctly parsed title, url, author, tags, and image."""
    respx.get(_FEED_URL).mock(return_value=Response(200, content=_VALID_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL, language="en")

    first = articles[0]
    assert first.title == "Article One"
    assert first.url == "https://example.com/article-1"
    assert first.body == "Body of article one."
    assert first.author == "Alice"
    assert first.source_id == _SOURCE_ID
    assert first.language == "en"
    assert "Tech" in first.tags
    assert first.image_url == "https://example.com/img1.jpg"


@pytest.mark.asyncio
@respx.mock
async def test_collect_published_at_is_utc_aware() -> None:
    """published_at is parsed into a UTC-aware datetime."""
    from datetime import timezone

    respx.get(_FEED_URL).mock(return_value=Response(200, content=_VALID_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL, language="en")

    assert articles[0].published_at is not None
    assert articles[0].published_at.tzinfo == timezone.utc


@pytest.mark.asyncio
@respx.mock
async def test_collect_empty_feed_returns_empty_list() -> None:
    """A feed with no <item> elements yields an empty list."""
    respx.get(_FEED_URL).mock(return_value=Response(200, content=_EMPTY_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL)

    assert articles == []


@pytest.mark.asyncio
@respx.mock
async def test_collect_http_404_raises_source_fetch_error() -> None:
    """A 404 response raises SourceFetchError."""
    respx.get(_FEED_URL).mock(return_value=Response(404))

    collector = RSSCollector()
    with pytest.raises(SourceFetchError):
        await collector.collect(_SOURCE_ID, _FEED_URL)


@pytest.mark.asyncio
@respx.mock
async def test_collect_http_500_raises_source_fetch_error() -> None:
    """A 500 response raises SourceFetchError."""
    respx.get(_FEED_URL).mock(return_value=Response(500))

    collector = RSSCollector()
    with pytest.raises(SourceFetchError):
        await collector.collect(_SOURCE_ID, _FEED_URL)


@pytest.mark.asyncio
@respx.mock
async def test_collect_article_without_author_has_none() -> None:
    """Article without <author> element has author=None."""
    respx.get(_FEED_URL).mock(return_value=Response(200, content=_VALID_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL)

    second = articles[1]
    assert second.author is None


@pytest.mark.asyncio
@respx.mock
async def test_collect_passes_language_to_articles() -> None:
    """language parameter is forwarded to every RawArticle."""
    respx.get(_FEED_URL).mock(return_value=Response(200, content=_VALID_RSS))

    collector = RSSCollector()
    articles = await collector.collect(_SOURCE_ID, _FEED_URL, language="pt-BR")

    assert all(a.language == "pt-BR" for a in articles)
