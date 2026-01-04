from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Type, Union

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import DeclarativeBase


# Django-like on_delete constants
CASCADE = "CASCADE"
PROTECT = "PROTECT"
SET_NULL = "SET NULL"
SET_DEFAULT = "SET DEFAULT"
DO_NOTHING = "NO ACTION"


def _get_fk_target(to: Union[str, Type["DeclarativeBase"]]) -> str:
    """Get foreign key target string."""
    if isinstance(to, str):
        # If it's a string, assume it's a table name
        # Check if it already contains a dot (table.column format)
        if "." in to:
            return to
        # Otherwise, assume it's just a table name and add .id
        return f"{to}.id"
    # Get the table name from the model
    if hasattr(to, "__tablename__"):
        return f"{to.__tablename__}.id"
    # Fallback to module.class format (for forward references)
    return f"{to.__module__}.{to.__name__}"


def _get_fk_type(to: Union[str, Type["DeclarativeBase"]]) -> Any:
    """Infer foreign key column type from target model."""
    from sqlalchemy import Integer

    # Default to UUID (our standard)
    default_type = PG_UUID(as_uuid=True)

    if isinstance(to, type):
        # Try to get the type from the model's id column
        if hasattr(to, "__table__"):
            id_col = to.__table__.columns.get("id")
            if id_col is not None:
                return id_col.type

    return default_type


def _get_ondelete_value(on_delete: str, nullable: bool) -> tuple[Optional[str], bool]:
    """Convert Django-like on_delete to SQLAlchemy ondelete value."""
    if on_delete == CASCADE:
        return ("CASCADE", nullable)
    elif on_delete == PROTECT:
        # PROTECT is handled at application level in SQLAlchemy
        return (None, nullable)
    elif on_delete == SET_NULL:
        return ("SET NULL", True)  # Force nullable for SET_NULL
    elif on_delete == SET_DEFAULT:
        return ("SET DEFAULT", nullable)
    elif on_delete == DO_NOTHING:
        return ("NO ACTION", nullable)
    else:
        return (None, nullable)


# Simplified approach: provide helper functions that return the right constructs
# Users will define FK column and relationship separately, but with less boilerplate

def create_foreign_key(
    to: Union[str, Type["DeclarativeBase"]],
    *,
    on_delete: str = CASCADE,
    nullable: bool = False,
    column_name: Optional[str] = None,
    **kwargs: Any,
) -> Mapped[Any]:
    """
    Create a foreign key column (Django-like).

    Usage:
        class Post(Base):
            author_id: Mapped[UUID] = create_foreign_key(User, on_delete=CASCADE)
            author: Mapped[User] = relationship("User", back_populates="posts")
    """
    fk_target = _get_fk_target(to)
    fk_type = _get_fk_type(to)
    ondelete_value, is_nullable = _get_ondelete_value(on_delete, nullable)

    if column_name is None:
        if isinstance(to, type):
            column_name = f"{to.__name__.lower()}_id"
        else:
            column_name = "foreign_key_id"

    return mapped_column(
        fk_type,
        ForeignKey(fk_target, ondelete=ondelete_value),
        nullable=is_nullable,
        **kwargs,
    )


def create_relationship(
    to: Union[str, Type["DeclarativeBase"]],
    *,
    back_populates: Optional[str] = None,
    foreign_keys: Optional[list[str]] = None,
    **kwargs: Any,
) -> Mapped[Any]:
    """
    Create a relationship (simplified).

    Usage:
        class Post(Base):
            author: Mapped[User] = create_relationship(User, back_populates="posts")
    """
    rel_kwargs: dict[str, Any] = {}
    if back_populates:
        rel_kwargs["back_populates"] = back_populates
    if foreign_keys:
        rel_kwargs["foreign_keys"] = foreign_keys

    rel_kwargs.update(kwargs)

    return relationship(to, **rel_kwargs)


def create_many_to_many(
    to: Union[str, Type["DeclarativeBase"]],
    *,
    secondary: Optional[Union[str, Type["DeclarativeBase"]]] = None,
    back_populates: Optional[str] = None,
    **kwargs: Any,
) -> Mapped[Any]:
    """
    Create a many-to-many relationship (Django-like).

    Usage:
        class Post(Base):
            tags: Mapped[list[Tag]] = create_many_to_many(Tag, back_populates="posts")

    With explicit through table:
        class Post(Base):
            tags: Mapped[list[Tag]] = create_many_to_many(Tag, secondary=PostTag, back_populates="posts")
    """
    rel_kwargs: dict[str, Any] = {}
    if secondary:
        rel_kwargs["secondary"] = secondary
    if back_populates:
        rel_kwargs["back_populates"] = back_populates
    rel_kwargs.update(kwargs)

    return relationship(to, **rel_kwargs)


def create_one_to_one(
    to: Union[str, Type["DeclarativeBase"]],
    *,
    on_delete: str = CASCADE,
    back_populates: Optional[str] = None,
    nullable: bool = True,
    **kwargs: Any,
) -> tuple[Mapped[Any], Mapped[Any]]:
    """
    Create a one-to-one relationship (Django-like).

    Returns tuple of (fk_column, relationship).

    Usage:
        class Profile(Base):
            user_id, user = create_one_to_one(User, on_delete=CASCADE, back_populates="profile")
    """
    fk_column = create_foreign_key(to, on_delete=on_delete, nullable=nullable, unique=True, **kwargs)
    rel = create_relationship(to, back_populates=back_populates, foreign_keys=[fk_column], uselist=False, **kwargs)
    return (fk_column, rel)
