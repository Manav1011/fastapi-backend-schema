from __future__ import annotations

from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from project.settings import get_settings


# Multiple database support (Django-like)
_engines: dict[str, AsyncEngine] = {}
_sessionmakers: dict[str, async_sessionmaker[AsyncSession]] = {}


def get_engine(using: str = "default") -> AsyncEngine:
    """
    Get database engine for a specific database (Django-like).
    
    Args:
        using: Database alias (defaults to "default")
    
    Returns:
        AsyncEngine for the specified database
    """
    global _engines
    
    if using not in _engines:
        settings = get_settings()
        databases = settings.databases_dict
        
        if using not in databases:
            raise ValueError(
                f"Database '{using}' not found in DATABASES. "
                f"Available databases: {list(databases.keys())}"
            )
        
        url = databases[using]
        _engines[using] = create_async_engine(url, future=True)
    
    return _engines[using]


def get_sessionmaker(using: str = "default") -> async_sessionmaker[AsyncSession]:
    """
    Get sessionmaker for a specific database (Django-like).
    
    Args:
        using: Database alias (defaults to "default")
    
    Returns:
        async_sessionmaker for the specified database
    """
    global _sessionmakers
    
    if using not in _sessionmakers:
        engine = get_engine(using)
        _sessionmakers[using] = async_sessionmaker(engine, expire_on_commit=False)
    
    return _sessionmakers[using]


async def get_async_session(using: str = "default") -> AsyncIterator[AsyncSession]:
    """
    Get async session for a specific database (Django-like).
    
    Args:
        using: Database alias (defaults to "default")
    
    Yields:
        AsyncSession for the specified database
    """
    async with get_sessionmaker(using)() as session:
        yield session


# Backward compatibility: default database functions
def get_default_engine() -> AsyncEngine:
    """Get default database engine (backward compatibility)."""
    return get_engine("default")


def get_default_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Get default database sessionmaker (backward compatibility)."""
    return get_sessionmaker("default")


