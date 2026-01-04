from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import typer
import uvicorn
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from typer import Option
import json

# Django-like: Add project directory to Python path for shorter imports
# This allows: from apps.users.models import User (instead of project.apps.users.models)
# Note: This only affects imports when running manage.py commands
_project_dir = Path(__file__).parent / "project"
if str(_project_dir.resolve()) not in sys.path:
    sys.path.insert(0, str(_project_dir.resolve()))

# Core imports
from project.core.db import (
    Base,
    Manager,
    QuerySet,
    get_async_session,
    get_default_engine,
    get_default_sessionmaker,
)
from project.core.db.serialization import dump_data, load_data
from project.core.registry import load_installed_apps
from project.settings import get_settings

# User app imports
from project.apps.users.auth import get_user_manager
from project.apps.users.models import User
from project.apps.users.schemas import UserCreate
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

# Optional/Shell imports
try:
    import nest_asyncio
except ImportError:
    nest_asyncio = None

try:
    import IPython
    from IPython.terminal.embed import InteractiveShellEmbed
except ImportError:
    IPython = None
    InteractiveShellEmbed = None

import code
from sqlalchemy import text

app = typer.Typer(no_args_is_help=True, add_completion=False)
console = Console()


def _load_env() -> None:
    # Prefer `env` (committed template exists), but allow `.env` too.
    load_dotenv("env")
    load_dotenv(".env")


@app.command()
def runserver(
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload/--no-reload", help="Enable auto-reload"),
) -> None:
    """Start the dev server (Django-like runserver)."""
    _load_env()
    uvicorn.run(
        "project.main:create_app",
        factory=True,
        host=host,
        port=port,
        reload=reload,
    )


@app.command()
def makemigrations(message: str = Option("auto", "--message", "-m", help="Migration message")) -> None:
    """Create an Alembic revision (Django-like makemigrations)."""
    _load_env()
    cmd = [
        "alembic",
        "-c",
        str(Path(__file__).with_name("alembic.ini")),
        "revision",
        "--autogenerate",
        "-m",
        message,
    ]
    raise SystemExit(subprocess.call(cmd))


@app.command()
def migrate(revision: str = typer.Option("head", "--revision", "-r", help="Migration revision")) -> None:
    """Apply migrations (Django-like migrate)."""
    _load_env()
    cmd = [
        "alembic",
        "-c",
        str(Path(__file__).with_name("alembic.ini")),
        "upgrade",
        revision,
    ]
    raise SystemExit(subprocess.call(cmd))


@app.command()
def createsuperuser(
    email: str = Option(..., "--email", "-e", prompt="Email", help="Email address"),
    password: str = Option(..., "--password", "-p", prompt="Password", hide_input=True, help="Password"),
) -> None:
    """Create a superuser (Django-like createsuperuser)."""
    _load_env()

    async def _create() -> None:
        sessionmaker = get_default_sessionmaker()
        async with sessionmaker() as session:
            user_db = SQLAlchemyUserDatabase(session, User)
            user_manager = await anext(get_user_manager(user_db))

            try:
                # Create user with UserCreate schema
                user_create = UserCreate(
                    email=email,
                    password=password,
                    is_superuser=True,
                    is_staff=True,
                    is_verified=True,
                )
                user = await user_manager.create(user_create)
                console.print(f"[green]✓[/green] Superuser created: {user.email}")
            except Exception as e:
                console.print(f"[red]✗[/red] Error creating superuser: {e}")
                raise SystemExit(1)

    asyncio.run(_create())


@app.command()
def shell() -> None:
    """Start an async-aware Python shell (Django-like shell)."""
    _load_env()

    # Allow nested event loops for IPython compatibility
    if nest_asyncio:
        nest_asyncio.apply()

    async def _setup_shell() -> None:
        """Set up Django-like shell environment."""

        settings = get_settings()
        sessionmaker = get_default_sessionmaker()  # Uses "default" database

        # Load all installed apps (Django-like: models are pre-imported)
        registry = load_installed_apps(settings)

        # Collect all models from installed apps (Django-like)
        models = {}
        for app_path in registry.imported:
            try:
                models_mod = __import__(f"{app_path}.models", fromlist=[""])
                for attr_name in dir(models_mod):
                    attr = getattr(models_mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Base)
                        and attr is not Base
                        and attr.__module__.startswith(app_path)
                    ):
                        models[attr_name] = attr
            except ImportError:
                pass

        # Create async session helper (Django-like)
        # sessionmaker() when called returns an async context manager
        # We create a simple wrapper function that returns it
        def get_session():
            """Get async database session context manager (Django-like).
            
            Usage:
                async with get_session() as session:
                    users = await User.objects.all(session)
            """
            return sessionmaker()

        # Build namespace (Django-like shell environment)
        ns = {
            # Settings and config
            "settings": settings,
            "get_settings": get_settings,
            # Database
            "sessionmaker": sessionmaker,
            "get_session": get_session,
            "get_async_session": get_async_session,
            # Core utilities
            "Base": Base,
            "Manager": Manager,
            "QuerySet": QuerySet,
            # Registry
            "registry": registry,
            # All models from installed apps (Django-like)
            **models,
        }

        # Try IPython first (better experience)
        if IPython and InteractiveShellEmbed:

            banner = f"""
Python {sys.version.split()[0]} shell
FastAPI Backend (Django-like)
Settings: {settings.PROJECT_NAME}
Installed Apps: {', '.join(registry.imported)}
Available Models: {', '.join(sorted(models.keys()))}

Quick start:
  async with get_session() as session:
      users = await User.objects.all(session)
      user = await User.objects.get(session, email="test@example.com")
"""
            shell = InteractiveShellEmbed(banner1=banner, user_ns=ns)
            shell()
        except Exception:
            # Fallback to standard Python shell
            console.print("[yellow]IPython not installed. Install with: pip install ipython[/yellow]")
            console.print("Falling back to standard Python shell...")

            banner = f"""
Python {sys.version.split()[0]} shell
FastAPI Backend (Django-like)
Settings: {settings.PROJECT_NAME}
Installed Apps: {', '.join(registry.imported)}
Available Models: {', '.join(sorted(models.keys()))}

Quick start:
  async with get_session() as session:
      users = await User.objects.all(session)
"""
            code.interact(banner=banner, local=ns)

    asyncio.run(_setup_shell())


@app.command()
def createapp(
    name: str = Option(..., "--name", "-n", prompt="App name", help="App name"),
    add_to_installed: bool = Option(True, "--add-to-installed/--no-add-to-installed", help="Add to INSTALLED_APPS"),
) -> None:
    """Create a new app (Django-like createapp)."""
    _load_env()

    base_path = Path(__file__).parent
    apps_dir = base_path / "project" / "apps"
    app_dir = apps_dir / name

    if app_dir.exists():
        console.print(f"[red]✗[/red] App '{name}' already exists at {app_dir}")
        raise SystemExit(1)

    # Create directory structure
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "__init__.py").write_text('"""App: {name}"""\n')
    (app_dir / "models.py").write_text(
        """from __future__ import annotations

from project.core.db import Base

# Define your models here
# Example:
# from sqlalchemy.orm import Mapped, mapped_column
# from sqlalchemy import String
#
# class MyModel(Base):
#     __tablename__ = "mymodel"
#     id: Mapped[int] = mapped_column(primary_key=True)
#     name: Mapped[str] = mapped_column(String(255))
#     
#     def __str__(self) -> str:
#         \"\"\"Django-like string representation.\"\"\"
#         return self.name or f"MyModel({self.id})"
"""
    )
    (app_dir / "schemas.py").write_text(
        """from __future__ import annotations

from pydantic import BaseModel

from project.core.responses import BaseResponse

# Define your request/response schemas here
# Example:
# class MyModelCreate(BaseModel):
#     name: str
#
# class MyModelRead(BaseModel):
#     id: int
#     name: str
#
# # Response schemas inheriting from BaseResponse
# class MyModelListResponse(BaseResponse[list[MyModelRead]]):
#     \"\"\"Response schema for listing models.\"\"\"
#     pass
#
# class MyModelDetailResponse(BaseResponse[MyModelRead]):
#     \"\"\"Response schema for single model.\"\"\"
#     pass
#
# class MyModelCreateResponse(BaseResponse[MyModelRead]):
#     \"\"\"Response schema for creating a model.\"\"\"
#     pass
"""
    )
    (app_dir / "urls.py").write_text(
        """from __future__ import annotations

from fastapi import APIRouter

# Create router for this app
router = APIRouter(prefix="/{name}", tags=["{name}"])

# Import views to register routes on this router
# Routes are defined in views.py with @router decorators
# Django-like relative import (same app)
from . import views  # noqa: F401, E402
""".format(
            name=name
        )
    )
    (app_dir / "views.py").write_text(
        """from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from project.core.db import get_async_session

# Django-like relative imports (same app)
from .urls import router  # Import router from urls.py
from . import service  # Import service layer

# Define routes directly here with @router decorators
# Example:
# from .schemas import MyModelListResponse, MyModelDetailResponse  # Import your response schemas
#
# @router.get("/", response_model=MyModelListResponse, status_code=status.HTTP_200_OK)
# async def list_items(session: AsyncSession = Depends(get_async_session)) -> MyModelListResponse:
#     \"\"\"List all items.\"\"\"
#     items = await service.get_all_items(session)
#     return MyModelListResponse(
#         success=True,
#         status_code=status.HTTP_200_OK,
#         message="Items retrieved successfully",
#         data=[MyModelRead(id=i.id, name=i.name) for i in items],
#     )
#
# @router.get("/{{item_id}}", response_model=MyModelDetailResponse, status_code=status.HTTP_200_OK)
# async def get_item(item_id: int, session: AsyncSession = Depends(get_async_session)) -> MyModelDetailResponse:
#     \"\"\"Get a single item.\"\"\"
#     item = await service.get_item_by_id(session, item_id)
#     if not item:
#         raise HTTPException(status_code=404, detail="Item not found")
#     return MyModelDetailResponse(
#         success=True,
#         status_code=status.HTTP_200_OK,
#         message="Item retrieved successfully",
#         data=MyModelRead(id=item.id, name=item.name),
#     )
#
# @router.post("/", response_model=MyModelCreateResponse, status_code=status.HTTP_201_CREATED)
# async def create_item(data: MyModelCreate, session: AsyncSession = Depends(get_async_session)) -> MyModelCreateResponse:
#     \"\"\"Create a new item.\"\"\"
#     item = await service.create_item(session, data)
#     return MyModelCreateResponse(
#         success=True,
#         status_code=status.HTTP_201_CREATED,
#         message="Item created successfully",
#         data=MyModelRead(id=item.id, name=item.name),
#     )
""".format(
            name=name
        )
    )
    (app_dir / "admin.py").write_text(
        """from __future__ import annotations

from project.core.admin.site import admin_site

# Register your models with admin here
# Example:
# from sqladmin import ModelView
# from .models import MyModel  # Django-like relative import (same app)
#
# class MyModelAdmin(ModelView, model=MyModel):
#     column_list = [MyModel.id, MyModel.name]
#
# admin_site.register(MyModelAdmin)
""".format(
            name=name
        )
    )
    (app_dir / "service.py").write_text(
        """from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

# Business logic and data access layer
# Example:
# async def create_item(session: AsyncSession, data):
#     # Logic and DB access here
#     pass
"""
    )
    (app_dir / "dependencies.py").write_text(
        """from __future__ import annotations

# FastAPI dependencies for this app
# Example:
# from fastapi import Depends
# from project.core.db import get_async_session
# from sqlalchemy.ext.asyncio import AsyncSession
#
# async def get_current_item(session: AsyncSession = Depends(get_async_session)):
#     # Dependency logic
#     pass
"""
    )

    console.print(f"[green]✓[/green] Created app '{name}' at {app_dir}")

    # Optionally add to INSTALLED_APPS
    if add_to_installed:
        settings_file = base_path / "project" / "settings.py"
        if settings_file.exists():
            content = settings_file.read_text()
            app_path = f'"project.apps.{name}"'
            if app_path not in content:
                # Find INSTALLED_APPS line and add the new app
                lines = content.split("\n")
                for i, line in enumerate(lines):
                    if "INSTALLED_APPS" in line and "Field" in line:
                        # Handle string format (default="app1,app2")
                        if 'default="' in line:
                            # Insert before the closing quote of the default value
                            # Assuming format: default="app1" or default="app1,app2"
                            parts = line.split('default="')
                            if len(parts) > 1:
                                value_part = parts[1].split('"')
                                if len(value_part) > 1:
                                    current_value = value_part[0]
                                    new_value = f"{current_value},project.apps.{name}" if current_value else f"project.apps.{name}"
                                    lines[i] = line.replace(f'default="{current_value}"', f'default="{new_value}"')
                        # Handle list format (default=["app1"])
                        elif 'default=[' in line:
                            lines[i] = line.replace(']', f', "project.apps.{name}"]')
                        break
                settings_file.write_text("\n".join(lines))
                console.print(f"[green]✓[/green] Added '{app_path}' to INSTALLED_APPS")
            else:
                console.print(f"[yellow]⚠[/yellow] App already in INSTALLED_APPS")
        else:
            console.print(f"[yellow]⚠[/yellow] Could not find settings.py to update INSTALLED_APPS")



@app.command()
def flush(
    interactive: bool = Option(True, "--interactive/--no-interactive", help="Prompt for confirmation"),
) -> None:
    """Delete all data from all tables (Django-like flush)."""
    _load_env()
    
    if interactive:
        confirm = Prompt.ask("This will wipe [red]ALL[/red] data from your database. Are you sure?", default="no")
        if confirm.lower() not in ("y", "yes"):
            console.print("Cancelled.")
            return

    async def _flush() -> None:
        settings = get_settings()
        load_installed_apps(settings)
        
        engine = get_default_engine()
        async with engine.begin() as conn:
            # Disable foreign key checks for SQLite/PostgreSQL
            if engine.url.drivername == "aiosqlite":
                await conn.execute(text("PRAGMA foreign_keys = OFF;"))
            elif "postgresql" in engine.url.drivername:
                await conn.execute(text("SET session_replication_role = 'replica';"))

            for table in reversed(Base.metadata.sorted_tables):
                console.print(f"Flushing table: [cyan]{table.name}[/cyan]")
                await conn.execute(table.delete())
            
            if engine.url.drivername == "aiosqlite":
                await conn.execute(text("PRAGMA foreign_keys = ON;"))
            elif "postgresql" in engine.url.drivername:
                await conn.execute(text("SET session_replication_role = 'origin';"))
                
        console.print("[green]✓[/green] Database flushed successfully.")

    asyncio.run(_flush())


@app.command()
def dumpdata(
    labels: Optional[list[str]] = typer.Argument(None, help="Optional app labels or app_label.ModelName"),
    output: Optional[str] = Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Dump database data to JSON (Django-like dumpdata)."""
    _load_env()

    async def _dump() -> None:
        settings = get_settings()
        registry = load_installed_apps(settings)
        
        # Parse labels: ["users", "users.User"]
        target_apps = []
        target_models = {} # app_label -> [ModelName]
        
        if labels:
            for label in labels:
                if "." in label:
                    app_name, model_name = label.split(".", 1)
                    target_models.setdefault(app_name, []).append(model_name)
                else:
                    target_apps.append(label)

        models = []
        for app_path in registry.imported:
            app_label = app_path.split(".")[-1]
            
            # If labels provided, check if this app or its models are requested
            is_app_requested = not labels or app_label in target_apps or app_label in target_models
            
            if not is_app_requested:
                continue
                
            try:
                models_mod = __import__(f"{app_path}.models", fromlist=[""])
                for attr_name in dir(models_mod):
                    attr = getattr(models_mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Base)
                        and attr is not Base
                        and attr.__module__.startswith(app_path)
                    ):
                        # Filter by model name if specific models were requested for this app
                        if app_label in target_models and labels:
                            if attr_name in target_models[app_label]:
                                models.append(attr)
                        else:
                            models.append(attr)
            except ImportError:
                pass

        if not models:
            console.print(f"[yellow]⚠[/yellow] No models found for app label: {app_label}" if app_label else "No models found.")
            return

        sessionmaker = get_default_sessionmaker()
        async with sessionmaker() as session:
            json_data = await dump_data(session, models)
            
            if output:
                Path(output).write_text(json_data)
                console.print(f"[green]✓[/green] Data dumped to {output}")
            else:
                print(json_data)

    asyncio.run(_dump())


@app.command()
def loaddata(
    fixture: str = typer.Argument(..., help="Path to JSON fixture file"),
) -> None:
    """Load data from JSON fixture (Django-like loaddata)."""
    _load_env()
    
    fixture_path = Path(fixture)
    if not fixture_path.exists():
        console.print(f"[red]✗[/red] Fixture file not found: {fixture}")
        raise SystemExit(1)

    async def _load() -> None:
        settings = get_settings()
        registry = load_installed_apps(settings)
        
        # Collect registry models
        registry_models = {}
        for app_path in registry.imported:
            try:
                models_mod = __import__(f"{app_path}.models", fromlist=[""])
                for attr_name in dir(models_mod):
                    attr = getattr(models_mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Base)
                        and attr is not Base
                    ):
                        registry_models[attr_name] = attr
            except ImportError:
                pass

        data = json.loads(fixture_path.read_text())
        sessionmaker = get_default_sessionmaker()
        async with sessionmaker() as session:
            count = await load_data(session, data, registry_models)
            console.print(f"[green]✓[/green] Installed {count} object(s) from {fixture}")

    asyncio.run(_load())


if __name__ == "__main__":
    app()


