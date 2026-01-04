from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

from fastapi import Depends
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.authentication import AuthenticationBackend, BearerTransport, JWTStrategy
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

from project.core.db import get_async_session
from project.settings import get_settings

if TYPE_CHECKING:
    from uuid import UUID

    from fastapi import Request
    from sqlalchemy.ext.asyncio import AsyncSession

    from .models import User
else:
    from .models import User
    from uuid import UUID


class UserManager(UUIDIDMixin, BaseUserManager[User, UUID]):
    """User manager for FastAPI Users."""

    reset_password_token_secret = get_settings().SECRET_KEY
    verification_token_secret = get_settings().SECRET_KEY

    async def on_after_register(self, user: User, request: Request | None = None) -> None:
        """Called after user registration."""
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(self, user: User, token: str, request: Request | None = None) -> None:
        """Called after forgot password request."""
        print(f"User {user.id} has requested password reset. Token: {token}")

    async def on_after_verify(self, user: User, request: Request | None = None) -> None:
        """Called after email verification."""
        print(f"User {user.id} has been verified.")


async def get_user_db(session: AsyncSession = Depends(get_async_session)) -> SQLAlchemyUserDatabase[User, UUID]:
    """Get user database adapter."""
    from .models import User

    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase[User, UUID] = Depends(get_user_db)) -> UserManager:
    """Get user manager."""
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy[User, UUID]:
    """Get JWT authentication strategy."""
    settings = get_settings()
    return JWTStrategy(secret=settings.JWT_SECRET, lifetime_seconds=settings.JWT_LIFETIME_SECONDS)


bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
