"""Response schemas for API v1."""

from __future__ import annotations

from project.core.responses import BaseResponse


class HealthzResponse(BaseResponse[dict[str, str]]):
    """Response schema for health check endpoint."""

    pass

