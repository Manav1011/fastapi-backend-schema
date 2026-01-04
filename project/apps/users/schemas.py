from __future__ import annotations

from uuid import UUID

from fastapi_users import schemas


class UserRead(schemas.BaseUser[UUID]):
    """User read schema."""

    is_staff: bool
    date_joined: str
    last_login: str | None


class UserCreate(schemas.BaseUserCreate):
    """User creation schema."""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""

    pass
