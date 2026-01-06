from __future__ import annotations

import asyncio
from logging.config import fileConfig
from typing import Any

from alembic import context
from alembic.operations import ops
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


def process_revision_directives(context: Any, revision: tuple, directives: list) -> None:
    """
    Process revision directives to add necessary imports for custom types.
    This ensures that types like fastapi_users_db_sqlalchemy.generics.GUID()
    are properly imported in migration files.
    """
    if directives:
        script = directives[0]
        # Check if any operation uses fastapi_users_db_sqlalchemy types
        for op in script.upgrade_ops.ops:
            if isinstance(op, ops.CreateTableOp):
                for col in op.columns:
                    if hasattr(col, "type"):
                        col_type = col.type
                        if hasattr(col_type, "__module__") and "fastapi_users_db_sqlalchemy" in col_type.__module__:
                            script.imports.add("import fastapi_users_db_sqlalchemy")
                            break


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
        process_revision_directives=process_revision_directives,
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
        process_revision_directives=process_revision_directives,
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


