"""CLI seed script: inserts the 5 default news sources defined in SPEC.md §7.

Usage:
    poetry run python -m backend.src.interfaces.cli.seed_sources
    # or from project root:
    PYTHONPATH=. python -m backend.src.interfaces.cli.seed_sources

The script is idempotent: if a source with the same feed_url already exists it
is skipped, so running it multiple times is safe.
"""

from __future__ import annotations

import asyncio
import sys

from backend.src.core.config import get_settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.domain.entities.source import Source, SourceType
from backend.src.infrastructure.database.engine import AsyncSessionFactory
from backend.src.infrastructure.database.repositories.source_repo import (
    SQLSourceRepository,
)

setup_logging()
log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Default sources — SPEC.md §7
# ---------------------------------------------------------------------------
DEFAULT_SOURCES: list[dict[str, str]] = [
    {
        "name": "Hacker News (top)",
        "url": "https://news.ycombinator.com",
        "feed_url": "https://hnrss.org/frontpage",
        "language": "en",
        "category": "Tech",
    },
    {
        "name": "TechCrunch",
        "url": "https://techcrunch.com",
        "feed_url": "https://techcrunch.com/feed/",
        "language": "en",
        "category": "Tech",
    },
    {
        "name": "BBC News World",
        "url": "https://www.bbc.com/news/world",
        "feed_url": "http://feeds.bbci.co.uk/news/world/rss.xml",
        "language": "en",
        "category": "World",
    },
    {
        "name": "G1 Tecnologia",
        "url": "https://g1.globo.com/tecnologia/",
        "feed_url": "https://g1.globo.com/rss/g1/tecnologia/",
        "language": "pt-BR",
        "category": "Tech",
    },
    {
        "name": "InfoMoney",
        "url": "https://www.infomoney.com.br",
        "feed_url": "https://www.infomoney.com.br/feed/",
        "language": "pt-BR",
        "category": "Economy",
    },
]


async def _seed() -> None:
    """Insert default sources into the database, skipping existing ones."""
    settings = get_settings()
    log.info("seed_sources.start", database_url=settings.database_url)

    inserted = 0
    skipped = 0

    async with AsyncSessionFactory() as session:
        repo = SQLSourceRepository(session)

        # Fetch all existing feed_urls to detect duplicates without extra queries
        existing_sources = await repo.list_all()
        existing_feed_urls: set[str] = {s.feed_url for s in existing_sources}

        for data in DEFAULT_SOURCES:
            feed_url: str = data["feed_url"]

            if feed_url in existing_feed_urls:
                log.info(
                    "seed_sources.skip",
                    name=data["name"],
                    reason="already_exists",
                )
                skipped += 1
                continue

            source = Source(
                name=data["name"],
                url=data["url"],
                feed_url=feed_url,
                source_type=SourceType.RSS,
                language=data["language"],
                fetch_interval=60,
                is_active=True,
            )
            await repo.save(source)
            log.info("seed_sources.inserted", name=source.name, feed_url=feed_url)
            inserted += 1

        await session.commit()

    log.info(
        "seed_sources.done",
        inserted=inserted,
        skipped=skipped,
        total=inserted + skipped,
    )


def main() -> None:
    """Entry point for `poetry run seed-sources`."""
    asyncio.run(_seed())
    sys.exit(0)


if __name__ == "__main__":
    main()
