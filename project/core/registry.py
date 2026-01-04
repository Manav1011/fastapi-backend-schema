from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from types import ModuleType
from typing import Optional

from fastapi import APIRouter

from project.settings import Settings


def _import_optional(module_path: str) -> Optional[ModuleType]:
    try:
        return importlib.import_module(module_path)
    except ModuleNotFoundError as e:
        # Only treat it as "optional missing module" if the missing name is the target module.
        # If imports *inside* the module fail, we want to surface that error.
        if e.name == module_path:
            return None
        raise


@dataclass
class AppRegistry:
    installed_apps: list[str]
    imported: list[str] = field(default_factory=list)
    routers: list[APIRouter] = field(default_factory=list)

    def load(self) -> "AppRegistry":
        for app_path in self.installed_apps:
            importlib.import_module(app_path)
            self.imported.append(app_path)

            # Django-like autodiscovery
            _import_optional(f"{app_path}.models")

            urls_mod = _import_optional(f"{app_path}.urls")
            if urls_mod is not None and hasattr(urls_mod, "router"):
                r = getattr(urls_mod, "router")
                if isinstance(r, APIRouter):
                    self.routers.append(r)
            
            # Import views to ensure routes are registered on the router
            # (views.py imports router from urls.py and registers routes with decorators)
            _import_optional(f"{app_path}.views")

            _import_optional(f"{app_path}.admin")

        return self


_loaded_registry: Optional[AppRegistry] = None


def load_installed_apps(settings: Settings) -> AppRegistry:
    global _loaded_registry
    _loaded_registry = AppRegistry(installed_apps=settings.installed_apps_list).load()
    return _loaded_registry


def get_loaded_registry() -> Optional[AppRegistry]:
    return _loaded_registry


def get_loaded_routers() -> list[APIRouter]:
    if _loaded_registry is None:
        return []
    return list(_loaded_registry.routers)


