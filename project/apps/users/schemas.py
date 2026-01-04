from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from fastapi_users import schemas

from project.core.responses import BaseResponse


class UserRead(schemas.BaseUser[UUID]):
    """User read schema."""

    is_staff: bool
    date_joined: datetime
    last_login: datetime | None


class UserCreate(schemas.BaseUserCreate):
    """User creation schema."""

    pass


class UserUpdate(schemas.BaseUserUpdate):
    """User update schema."""

    pass


# Standardized Response Schemas
class UserResponse(BaseResponse[UserRead]):
    """Standardized user response."""

    pass


class TokenData(BaseModel):
    """Token data schema."""

    access_token: str
    token_type: str


class LoginResponse(BaseResponse[TokenData]):
    """Standardized login response."""

    pass
