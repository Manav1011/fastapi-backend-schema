from __future__ import annotations

from dataclasses import dataclass

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

import logging

from project.core.responses import create_error_response, ErrorResponse


@dataclass
class ApiError(Exception):
    """Custom API error exception."""

    status_code: int
    code: str
    message: str


def install_exception_handlers(app: FastAPI) -> None:
    """Install exception handlers for consistent error responses."""

    @app.exception_handler(ApiError)
    async def _api_error_handler(_: Request, exc: ApiError) -> ErrorResponse:
        """Handle custom ApiError exceptions."""
        error_response = create_error_response(
            message=exc.message,
            status_code=exc.status_code,
            error={"code": exc.code},
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_response.model_dump(exclude_none=True),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_: Request, exc: RequestValidationError) -> ErrorResponse:
        """Handle Pydantic validation errors."""
        errors = {}
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors[field] = error["msg"]
        error_response = create_error_response(
            message="Validation error",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error={"validation_errors": errors},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump(exclude_none=True),
        )

    @app.exception_handler(Exception)
    async def _general_exception_handler(_: Request, exc: Exception) -> ErrorResponse:
        """Handle unexpected exceptions."""
        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception", exc_info=exc)
        error_response = create_error_response(
            message="An unexpected error occurred",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump(exclude_none=True),
        )


