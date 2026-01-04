from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status

# Django-like relative imports (same app)
from .auth import auth_backend, get_user_manager, fastapi_users
from .models import User

router = APIRouter(prefix="/auth", tags=["auth"])

# We import views here to register our MANUAL routes
from . import views  # noqa: F401

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
