"""
Base response schemas for consistent API responses (Django-like).

All APIs return a consistent format:
{
    "success": true,
    "status_code": 200,
    "message": "Operation successful",
    "data": {...}
}

Usage:
    # Define your response schema inheriting from BaseResponse
    class ItemResponse(BaseResponse[ItemData]):
        pass
    
    # In your view
    @router.get("/items", response_model=ItemResponse, status_code=200)
    async def get_items() -> ItemResponse:
        return ItemResponse(
            success=True,
            status_code=200,
            message="Items retrieved",
            data={"items": [...]}
        )
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from fastapi import status
from pydantic import BaseModel, Field

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """
    Base response schema for all API responses.
    
    All response schemas should inherit from this class.
    
    Example:
        class UserListResponse(BaseResponse[list[UserSchema]]):
            pass
        
        class UserDetailResponse(BaseResponse[UserSchema]):
            pass
    """

    success: bool = Field(description="Whether the request was successful")
    status_code: int = Field(description="HTTP status code")
    message: str = Field(description="Human-readable message")
    data: T | None = Field(default=None, description="Response data (if any)")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "status_code": 200,
                "message": "Operation successful",
                "data": {"key": "value"},
            }
        }


class ErrorResponse(BaseResponse[None]):
    """
    Error response schema (inherits from BaseResponse).
    
    Use this for error responses or create your own error response schemas.
    """

    success: bool = Field(default=False, description="Always false for errors")
    error: dict[str, Any] | None = Field(default=None, description="Additional error details")

    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "status_code": 400,
                "message": "Validation error",
                "data": None,
                "error": {"field": "email", "reason": "Invalid format"},
            }
        }


# Helper functions to create BaseResponse instances (for convenience)
# These return Pydantic models that FastAPI will automatically serialize


def create_success_response(
    data: T | None = None,
    message: str = "Operation successful",
    status_code: int = status.HTTP_200_OK,
) -> BaseResponse[T]:
    """
    Create a successful BaseResponse instance (helper function).
    
    Args:
        data: Response data (optional)
        message: Success message
        status_code: HTTP status code (default: 200)
    
    Returns:
        BaseResponse instance
    
    Example:
        return create_success_response(data={"user_id": 123}, message="User created")
    """
    return BaseResponse(
        success=True,
        status_code=status_code,
        message=message,
        data=data,
    )


def create_error_response(
    message: str,
    status_code: int = status.HTTP_400_BAD_REQUEST,
    error: dict[str, Any] | None = None,
) -> ErrorResponse:
    """
    Create an error ErrorResponse instance (helper function).
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        error: Additional error details (optional)
    
    Returns:
        ErrorResponse instance
    
    Example:
        return create_error_response(message="User not found", status_code=404)
    """
    return ErrorResponse(
        success=False,
        status_code=status_code,
        message=message,
        data=None,
        error=error,
    )


def create_created_response(
    data: T | None = None,
    message: str = "Resource created successfully",
) -> BaseResponse[T]:
    """Create a 201 Created BaseResponse instance."""
    return create_success_response(data=data, message=message, status_code=status.HTTP_201_CREATED)


def create_not_found_response(message: str = "Resource not found") -> ErrorResponse:
    """Create a 404 Not Found ErrorResponse instance."""
    return create_error_response(message=message, status_code=status.HTTP_404_NOT_FOUND)


def create_forbidden_response(message: str = "Access forbidden") -> ErrorResponse:
    """Create a 403 Forbidden ErrorResponse instance."""
    return create_error_response(message=message, status_code=status.HTTP_403_FORBIDDEN)


def create_unauthorized_response(message: str = "Authentication required") -> ErrorResponse:
    """Create a 401 Unauthorized ErrorResponse instance."""
    return create_error_response(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


def create_validation_error_response(
    message: str = "Validation error",
    errors: dict[str, Any] | None = None,
) -> ErrorResponse:
    """Create a 422 Validation Error ErrorResponse instance."""
    return create_error_response(
        message=message,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error={"validation_errors": errors} if errors else None,
    )


__all__ = [
    "BaseResponse",
    "ErrorResponse",
    "create_success_response",
    "create_error_response",
    "create_created_response",
    "create_not_found_response",
    "create_forbidden_response",
    "create_unauthorized_response",
    "create_validation_error_response",
]

