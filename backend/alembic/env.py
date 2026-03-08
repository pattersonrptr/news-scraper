"""Alembic env.py — configured for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

# Import all models so Alembic can detect schema changes (autogenerate)
from backend.src.infrastructure.database.models.alert import Base as AlertBase      # noqa: F401
from backend.src.infrastructure.database.models.article import Base as ArticleBase  # noqa: F401
from backend.src.infrastructure.database.models.source import Base as SourceBase    # noqa: F401

# Use a unified metadata that includes all bases' tables
import sqlalchemy as sa
target_metadata = sa.MetaData()
for base in (AlertBase, ArticleBase, SourceBase):
    for table in base.metadata.tables.values():
        table.tometadata(target_metadata)

# Alembic Config object
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# target_metadata is already defined above from imported models


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (no live DB connection needed)."""
    from backend.src.core.config import get_settings
    url = get_settings().database_url
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # required for SQLite ALTER support
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:  # type: ignore[no-untyped-def]
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode using async engine."""
    from backend.src.infrastructure.database.engine import engine

    async with engine.begin() as conn:
        await conn.run_sync(do_run_migrations)


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
