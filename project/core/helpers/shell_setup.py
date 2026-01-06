from __future__ import annotations

import sys
from pathlib import Path
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Optional nicer shells / notebook helpers
try:
    import nest_asyncio
except Exception:  # pragma: no cover - optional
    nest_asyncio = None

try:
    from IPython import get_ipython
except Exception:  # pragma: no cover - optional
    get_ipython = None

import code

from project.settings import get_settings
from project.core.registry import load_installed_apps
from project.core.db import Base, Manager, QuerySet, get_async_session, get_default_sessionmaker

# ensure project/ is importable when this helper is used standalone
_project_dir = Path(__file__).resolve().parents[2]
if str(_project_dir) not in sys.path:
    sys.path.insert(0, str(_project_dir))


def _load_env() -> None:
    """Load env files used across the project."""
    load_dotenv("env")
    load_dotenv(".env")


_bootstrapped = False
_registry = None
_sessionmaker = None
_settings = None
_models: Dict[str, type] = {}


def bootstrap() -> None:
    """Idempotent bootstrap: load env, settings, installed apps and collect models.

    This mirrors what `manage.py shell` does so notebooks and scripts can reuse the
    same environment.
    """
    global _bootstrapped, _registry, _sessionmaker, _settings, _models
    if _bootstrapped:
        return

    _load_env()
    _settings = get_settings()
    _registry = load_installed_apps(_settings)
    _sessionmaker = get_default_sessionmaker()

    # collect models from installed apps (import <app>.models)
    collected: Dict[str, type] = {}
    for app_path in getattr(_registry, "imported", []):
        try:
            models_mod = __import__(f"{app_path}.models", fromlist=[""])
        except ImportError:
            continue
        for attr_name in dir(models_mod):
            attr = getattr(models_mod, attr_name)
            try:
                if isinstance(attr, type) and issubclass(attr, Base) and attr is not Base and getattr(
                    attr, "__module__", ""
                ).startswith(app_path):
                    collected[attr_name] = attr
            except Exception:
                continue

    _models = collected
    _bootstrapped = True


def get_namespace() -> Dict[str, Any]:
    """Return the same namespace `manage.py shell` exposes to users.

    Contains: `settings`, `sessionmaker`, `get_session`, `get_async_session`, `Base`,
    `Manager`, `QuerySet`, `registry`, and collected model classes.
    """
    bootstrap()
    assert _settings is not None
    assert _sessionmaker is not None
    assert _registry is not None

    def get_session():
        """Return an async session context manager: `async with get_session() as s:`"""
        return _sessionmaker()

    ns: Dict[str, Any] = {
        "settings": _settings,
        "get_settings": get_settings,
        "sessionmaker": _sessionmaker,
        "get_session": get_session,
        "get_async_session": get_async_session,
        "Base": Base,
        "Manager": Manager,
        "QuerySet": QuerySet,
        "registry": _registry,
        **_models,
    }
    return ns


def run_shell() -> None:
    """Start an interactive shell like `manage.py shell` (with IPython if available)."""
    _load_env()
    if nest_asyncio:
        nest_asyncio.apply()

    bootstrap()
    ns = get_namespace()

    banner = f"""
Python {sys.version.split()[0]} shell
FastAPI Backend (Django-like)
Settings: {_settings.PROJECT_NAME if _settings else 'unknown'}
Installed Apps: {', '.join(getattr(_registry, 'imported', []))}
Available Models: {', '.join(sorted(_models.keys()))}

Quick start:
  async with get_session() as session:
      users = await User.objects.all(session)
"""

    # Use IPython if available
    if get_ipython is not None and get_ipython() is None:
        try:
            # launch embedded IPython shell
            from IPython.terminal.embed import InteractiveShellEmbed

            shell = InteractiveShellEmbed(banner1=banner, user_ns=ns)
            shell()
            return
        except Exception:
            pass

    # Fallback to stdlib shell
    print("IPython not available; falling back to standard Python shell.")
    code.interact(banner=banner, local=ns)


def run(coro):
    """Helper to run async coroutines from the shell/scripts."""
    return asyncio.run(coro)


def setup_shell(inject: bool = True) -> Dict[str, Any]:
    """Prepare a notebook-friendly shell namespace and optionally inject it into
    the running IPython user namespace.

    Returns the namespace dict so callers can inspect or merge it themselves.

    Usage in a notebook:
        from project.core.helpers.shell_setup import setup_shell
        ns = setup_shell()            # returns namespace
        # or to inject into the notebook globals automatically:
        setup_shell()                 # now `User`, `get_session`, etc. are available
    """
    _load_env()
    # apply nest_asyncio in notebooks to allow asyncio.run/awaits
    if nest_asyncio:
        nest_asyncio.apply()

    bootstrap()
    ns = get_namespace()
    # helpful helper to run coroutines in simple scripts/cells
    ns["run"] = run

    # If running inside IPython (notebook), optionally push into user namespace
    try:
        if get_ipython is not None:
            ip = get_ipython()
            if ip is not None and inject:
                ip.push(ns)
    except Exception:
        # silently ignore injection failures
        pass

    return ns


__all__ = [
    "bootstrap",
    "get_namespace",
    "run_shell",
    "run",
    "setup_shell",
]
