from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Type

from fastapi import FastAPI
from sqladmin import Admin, ModelView

from project.settings import Settings


@dataclass
class AdminSite:
    model_views: list[Type[ModelView]] = field(default_factory=list)

    def register(self, view: Type[ModelView]) -> None:
        self.model_views.append(view)

    def iter_views(self) -> Iterable[Type[ModelView]]:
        return list(self.model_views)


admin_site = AdminSite()


def mount_admin(app: FastAPI, settings: Settings) -> None:
    # Lazy import to avoid importing DB session at import time.
    from project.core.db import get_default_engine

    admin = Admin(app, engine=get_default_engine(), base_url=settings.ADMIN_PATH)
    for view in admin_site.iter_views():
        admin.add_view(view)


