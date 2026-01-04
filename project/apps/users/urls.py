from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_users import FastAPIUsers

# Django-like relative imports (same app)
from .auth import auth_backend, get_user_manager
from .models import User
from .schemas import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend],
)

# Auth routes (FastAPI Users)
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/register",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/reset-password",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/verify",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
)

# Convenience dependencies (Django-like feel)
get_current_user = fastapi_users.current_user()
get_current_active_user = fastapi_users.current_user(active=True)
get_current_verified_user = fastapi_users.current_user(verified=True)
get_current_superuser = fastapi_users.current_user(superuser=True)


def get_current_staff_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Django-like: require staff user."""
    if not current_user.is_staff:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return current_user


def get_current_superuser_or_staff(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Django-like: require superuser or staff."""
    if not (current_user.is_superuser or current_user.is_staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser or staff access required",
        )
    return current_user
