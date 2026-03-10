"""CLI seed script: inserts the 5 default news sources defined in SPEC.md §7
and creates a default admin user if none exists.

Usage:
    poetry run python -m backend.src.interfaces.cli.seed_sources
    # or from project root:
    PYTHONPATH=. python -m backend.src.interfaces.cli.seed_sources

The script is idempotent: existing sources and users are skipped.
"""

from __future__ import annotations

import asyncio
import sys

from backend.src.core.config import get_settings
from backend.src.core.logging import get_logger, setup_logging
from backend.src.domain.entities.source import Source, SourceType
from backend.src.infrastructure.database.engine import AsyncSessionFactory
from backend.src.infrastructure.auth.password import hash_password
from backend.src.infrastructure.database.repositories.source_repo import (
    SQLSourceRepository,
)
from backend.src.infrastructure.database.repositories.user_repo import (
    SQLUserRepository,
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
        "name": "InfoMoney",
        "url": "https://www.infomoney.com.br",
        "feed_url": "https://www.infomoney.com.br/feed/",
        "language": "pt-BR",
        "category": "Economy",
    },
    {
        "name": "Bloomberg Markets",
        "url": "https://www.bloomberg.com",
        "feed_url": "https://feeds.bloomberg.com/markets/news.rss",
        "language": "en",
        "category": "Economy",
    },
    {
        "name": "Reuters Business",
        "url": "https://www.reuters.com",
        "feed_url": "https://www.reutersagency.com/feed/?best-topics=business-finance",
        "language": "en",
        "category": "Economy",
    },
    {
        "name": "Financial Times",
        "url": "https://www.ft.com",
        "feed_url": "https://www.ft.com/rss/home",
        "language": "en",
        "category": "Economy",
    },
    {
        "name": "Wall Street Journal Markets",
        "url": "https://www.wsj.com",
        "feed_url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "language": "en",
        "category": "Economy",
    },
    {
        "name": "CoinDesk",
        "url": "https://www.coindesk.com",
        "feed_url": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "language": "en",
        "category": "Crypto",
    },
    {
        "name": "Cointelegraph",
        "url": "https://cointelegraph.com",
        "feed_url": "https://cointelegraph.com/rss",
        "language": "en",
        "category": "Crypto",
    },
    {
        "name": "The Block",
        "url": "https://www.theblock.co",
        "feed_url": "https://www.theblock.co/rss.xml",
        "language": "en",
        "category": "Crypto",
    },
    {
        "name": "Bitcoin Magazine",
        "url": "https://bitcoinmagazine.com",
        "feed_url": "https://bitcoinmagazine.com/.rss/full/",
        "language": "en",
        "category": "Crypto",
    },
    {
        "name": "Ars Technica",
        "url": "https://arstechnica.com",
        "feed_url": "https://feeds.arstechnica.com/arstechnica/index",
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
        "name": "The Verge",
        "url": "https://www.theverge.com",
        "feed_url": "https://www.theverge.com/rss/index.xml",
        "language": "en",
        "category": "Tech",
    },
    {
        "name": "VentureBeat",
        "url": "https://venturebeat.com",
        "feed_url": "https://venturebeat.com/feed/",
        "language": "en",
        "category": "Tech",
    },
    {
        "name": "MIT Technology Review",
        "url": "https://www.technologyreview.com",
        "feed_url": "https://www.technologyreview.com/feed/",
        "language": "en",
        "category": "AI",
    },
    {
        "name": "OpenAI Blog",
        "url": "https://openai.com",
        "feed_url": "https://openai.com/blog/rss/",
        "language": "en",
        "category": "AI",
    },
    {
        "name": "Hugging Face Blog",
        "url": "https://huggingface.co",
        "feed_url": "https://huggingface.co/blog/feed.xml",
        "language": "en",
        "category": "AI",
    },
    {
        "name": "Foreign Policy",
        "url": "https://foreignpolicy.com",
        "feed_url": "https://foreignpolicy.com/feed/",
        "language": "en",
        "category": "Geopolitics",
    },
    {
        "name": "Council on Foreign Relations",
        "url": "https://www.cfr.org",
        "feed_url": "https://www.cfr.org/rss.xml",
        "language": "en",
        "category": "Geopolitics",
    },
    {
        "name": "The Economist",
        "url": "https://www.economist.com",
        "feed_url": "https://www.economist.com/rss.xml",
        "language": "en",
        "category": "Geopolitics",
    },
    {
        "name": "Krebs on Security",
        "url": "https://krebsonsecurity.com",
        "feed_url": "https://krebsonsecurity.com/feed/",
        "language": "en",
        "category": "Cybersecurity",
    },
    {
        "name": "The Hacker News",
        "url": "https://thehackernews.com",
        "feed_url": "https://feeds.feedburner.com/TheHackersNews",
        "language": "en",
        "category": "Cybersecurity",
    },
    {
        "name": "BleepingComputer",
        "url": "https://www.bleepingcomputer.com",
        "feed_url": "https://www.bleepingcomputer.com/feed/",
        "language": "en",
        "category": "Cybersecurity",
    },
    {
        "name": "Valor Econômico",
        "url": "https://valor.globo.com",
        "feed_url": "https://valor.globo.com/rss/",
        "language": "pt-BR",
        "category": "Economy",
    },
]


# ---------------------------------------------------------------------------
# Default admin user
# ---------------------------------------------------------------------------
DEFAULT_ADMIN = {
    "email": "admin@news.com",
    "password": "admin123",
    "display_name": "Admin",
}


async def _seed() -> None:
    """Insert default sources and admin user into the database (idempotent)."""
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

    # -----------------------------------------------------------------------
    # Seed default admin user
    # -----------------------------------------------------------------------
    async with AsyncSessionFactory() as session:
        user_repo = SQLUserRepository(session)
        existing_user = await user_repo.get_by_email(DEFAULT_ADMIN["email"])

        if existing_user is None:
            await user_repo.create(
                email=DEFAULT_ADMIN["email"],
                hashed_password=hash_password(DEFAULT_ADMIN["password"]),
                display_name=DEFAULT_ADMIN["display_name"],
            )
            await session.commit()
            log.info("seed_admin.inserted", email=DEFAULT_ADMIN["email"])
        else:
            log.info(
                "seed_admin.skip",
                email=DEFAULT_ADMIN["email"],
                reason="already_exists",
            )


def main() -> None:
    """Entry point for `poetry run seed-sources`."""
    asyncio.run(_seed())
    sys.exit(0)


if __name__ == "__main__":
    main()
