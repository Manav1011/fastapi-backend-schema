from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.gzip import GZipMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from project.api.v1 import api_v1_router
from project.core.logging import configure_logging
from project.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    app.state.settings = settings

    configure_logging(debug=settings.DEBUG)

    # Registry autodiscovery (models/urls/admin) happens at startup so:
    # - Alembic autogenerate sees all models (when env.py calls the same loader)
    # - Routers are included automatically
    # - Admin registrations are imported
    from project.core.registry import load_installed_apps

    registry = load_installed_apps(settings)
    app.state.registry = registry

    # Now that `urls.py` modules have been imported, mount their routers under /api/v1.
    from project.api.v1 import include_installed_app_routers

    include_installed_app_routers(api_v1_router)

    # Admin needs the app instance, so initialize after registry imports admin modules.
    from project.core.admin.site import mount_admin

    mount_admin(app, settings)

    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        lifespan=lifespan,
        openapi_url=f"{settings.API_PREFIX}/openapi.json",
        docs_url=f"{settings.API_PREFIX}/docs",
        redoc_url=f"{settings.API_PREFIX}/redoc",
    )

    # Add JWT security scheme to OpenAPI for Swagger "Authorize" button
    from fastapi.openapi.utils import get_openapi

    def custom_openapi() -> dict:
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=settings.PROJECT_NAME,
            version="1.0.0",
            description="Django-like FastAPI backend",
            routes=app.routes,
        )
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
            }
        }
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Middleware: keep explicit + settings-driven (Django-like clarity)
    from project.core.middleware.access_log import AccessLogMiddleware
    from project.core.middleware.request_id import RequestIdMiddleware
    from starlette.middleware.cors import CORSMiddleware

    if settings.trusted_hosts_list:
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts_list)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(AccessLogMiddleware)

    if settings.cors_origins_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.add_middleware(GZipMiddleware, minimum_size=1024)

    # Root redirects for convenience (redirect /docs to /api/v1/docs)
    @app.get("/docs", include_in_schema=False)
    async def redirect_docs():
        return RedirectResponse(url=f"{settings.API_PREFIX}/docs")

    @app.get("/redoc", include_in_schema=False)
    async def redirect_redoc():
        return RedirectResponse(url=f"{settings.API_PREFIX}/redoc")

    @app.get("/openapi.json", include_in_schema=False)
    async def redirect_openapi():
        return RedirectResponse(url=f"{settings.API_PREFIX}/openapi.json")

    # Core API router (collects installed apps routers)
    app.include_router(api_v1_router, prefix=settings.API_PREFIX)

    # Exception handlers (consistent error format)
    from project.core.errors import install_exception_handlers

    install_exception_handlers(app)

    return app


app = create_app()


