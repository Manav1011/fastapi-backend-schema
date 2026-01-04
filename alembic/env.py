from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from project.core.db.base import Base
from project.core.registry import load_installed_apps
from project.settings import get_settings


config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_url(using: str = "default") -> str:
    """
    Get database URL for migrations (supports multiple databases).
    
    Args:
        using: Database alias (defaults to "default")
    
    Returns:
        Database URL for the specified database
    """
    settings = get_settings()
    databases = settings.databases_dict
    if using not in databases:
        raise ValueError(
            f"Database '{using}' not found in DATABASES. "
            f"Available: {list(databases.keys())}"
        )
    return databases[using]


def run_migrations_offline() -> None:
    # Ensure all installed app models are imported before autogenerate runs.
    load_installed_apps(get_settings())

    url = get_url()
    context.configure(
        url=url,
        target_metadata=Base.metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    # Ensure all installed app models are imported before autogenerate runs.
    load_installed_apps(get_settings())

    context.configure(
        connection=connection,
        target_metadata=Base.metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = get_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())


