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
