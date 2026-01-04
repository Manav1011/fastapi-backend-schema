from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Mixin that adds created_at and updated_at timestamp fields (Django-like)."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class SoftDeleteMixin:
    """Mixin that adds soft delete functionality (Django-like)."""

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )

    @property
    def is_deleted(self) -> bool:
        """Check if the object is soft deleted."""
        return self.deleted_at is not None


class UUIDPrimaryKeyMixin:
    """Mixin that adds UUID primary key (Django-like for UUID models)."""

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class IntegerPrimaryKeyMixin:
    """Mixin that adds integer primary key (Django-like default)."""

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class NameMixin:
    """Mixin that adds a name field."""

    name: Mapped[str] = mapped_column(String(255), nullable=False)


class SlugMixin:
    """Mixin that adds a slug field (Django-like)."""

    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)


class DescriptionMixin:
    """Mixin that adds a description field."""

    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

