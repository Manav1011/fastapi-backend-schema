from __future__ import annotations

from fastapi import APIRouter, status

from project.api.schemas import HealthzResponse

api_v1_router = APIRouter()


@api_v1_router.get("/healthz", tags=["system"], response_model=HealthzResponse, status_code=status.HTTP_200_OK)
async def healthz() -> HealthzResponse:
    """Health check endpoint."""
    return HealthzResponse(
        success=True,
        status_code=status.HTTP_200_OK,
        message="Service is healthy",
        data={"status": "ok"},
    )


# App routers will be included after installed-app autodiscovery imports their `urls.py`.
# We attach them via a function so `main.create_app()` stays import-safe.
def include_installed_app_routers(router: APIRouter) -> None:
    from project.core.registry import get_loaded_routers

    for r in get_loaded_routers():
        router.include_router(r)

__all__ = ["api_v1_router", "include_installed_app_routers"]


