from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from project.core.db import Base
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID


class User(SQLAlchemyBaseUserTableUUID, Base):
    """Django-like User model with UUID primary key."""

    __tablename__ = "users"

    # FastAPI Users provides: id (UUID), email, hashed_password, is_active, is_superuser, is_verified
    # We add Django-like fields:
    is_staff: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    date_joined: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Reverse relationships (for cross-app relationships)
    # These are defined here but the actual models are in other apps
    # Example:
    # posts: Mapped[list["Post"]] = relationship("Post", back_populates="author")
    
    def __str__(self) -> str:
        """Django-like string representation for User."""
        return self.email or f"User({self.id})"
