"""
Django-like database routing support.

Allows models to specify which database they use.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from project.core.db.base import Base


class DatabaseRouter:
    """
    Django-like database router.
    
    Override db_for_read() and db_for_write() to route models to specific databases.
    """
    
    def db_for_read(self, model: type["Base"], **hints: dict) -> Optional[str]:
        """
        Suggest which database should be used for read operations.
        
        Returns:
            Database alias (e.g., "default", "analytics") or None to use default
        """
        return None
    
    def db_for_write(self, model: type["Base"], **hints: dict) -> Optional[str]:
        """
        Suggest which database should be used for write operations.
        
        Returns:
            Database alias (e.g., "default", "analytics") or None to use default
        """
        return None


# Default router (all models use "default" database)
_default_router = DatabaseRouter()


def get_db_for_model(model: type["Base"], operation: str = "read") -> str:
    """
    Get database alias for a model (Django-like routing).
    
    Args:
        model: The model class
        operation: "read" or "write"
    
    Returns:
        Database alias (defaults to "default")
    """
    # Check if model has a _database attribute (explicit routing)
    if hasattr(model, "_database"):
        return model._database
    
    # Use router
    if operation == "read":
        db = _default_router.db_for_read(model)
    else:
        db = _default_router.db_for_write(model)
    
    return db or "default"

