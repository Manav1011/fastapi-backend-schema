from __future__ import annotations

import uuid
from fastapi import Depends, HTTPException, status, Request, Body
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users import exceptions, schemas
from fastapi_users.router import ErrorCode

from project.core.responses import create_success_response
from .auth import auth_backend, get_user_manager, UserManager, fastapi_users
from .schemas import UserCreate, UserRead, LoginResponse, UserResponse, TokenData
from .urls import router
from .models import User

@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(),
    user_manager: UserManager = Depends(get_user_manager),
) -> LoginResponse:
    """Standardized login endpoint."""
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
        )

    # Manual token generation for standardized response
    strategy = auth_backend.get_strategy()
    token = await strategy.write_token(user)
    
    return create_success_response(
        data=TokenData(access_token=token, token_type="bearer"),
        message="Login successful",
    )

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager),
) -> UserResponse:
    """Standardized registration endpoint."""
    try:
        user = await user_manager.create(user_create, safe=True, request=request)
    except exceptions.UserAlreadyExists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
        )
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.REGISTER_INVALID_PASSWORD,
                "reason": e.reason,
            },
        )

    return create_success_response(
        data=UserRead.model_validate(user),
        message="Registration successful",
        status_code=status.HTTP_201_CREATED,
    )

@router.get("/me", response_model=UserResponse)
async def get_me(
    user: User = Depends(fastapi_users.current_user(active=True)),
) -> UserResponse:
    """Standardized 'get me' endpoint."""
    return create_success_response(
        data=UserRead.model_validate(user),
        message="Profile retrieved successfully",
    )

@router.post("/forgot-password", status_code=status.HTTP_202_ACCEPTED)
async def forgot_password(
    request: Request,
    email: str = Body(..., embed=True),
    user_manager: UserManager = Depends(get_user_manager),
):
    """Standardized forgot password endpoint."""
    try:
        user = await user_manager.get_by_email(email)
        await user_manager.forgot_password(user, request)
    except exceptions.UserNotExists:
        # Fall through to send accepted even if user doesn't exist (security)
        pass
    
    return create_success_response(
        message="If a user with this email exists, a password reset link has been sent.",
        status_code=status.HTTP_202_ACCEPTED,
    )

@router.post("/reset-password")
async def reset_password(
    request: Request,
    token: str = Body(...),
    password: str = Body(...),
    user_manager: UserManager = Depends(get_user_manager),
):
    """Standardized reset password endpoint."""
    try:
        await user_manager.reset_password(token, password, request)
    except (exceptions.InvalidResetPasswordTokenException, exceptions.UserNotExists):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.RESET_PASSWORD_BAD_TOKEN,
        )
    except exceptions.InvalidPasswordException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": ErrorCode.RESET_PASSWORD_INVALID_PASSWORD,
                "reason": e.reason,
            },
        )
    
    return create_success_response(message="Password has been reset successfully.")
