from __future__ import annotations

from functools import lru_cache
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("env", ".env"),
        env_ignore_empty=True,
        extra="ignore",
    )

    PROJECT_NAME: str = "fastapi-backend"
    ENV: str = "local"
    DEBUG: bool = True

    SECRET_KEY: str = "change-me"

    # Django-like: Multiple database support
    # Format: DATABASES=default:sqlite+aiosqlite:///./db.sqlite3,analytics:postgresql+asyncpg://user:pass@localhost/analytics
    # Or use DATABASE_URL for single database (backward compatibility)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./db.sqlite3")
    DATABASES: str = Field(default="")

    # Django-feel: installed apps drives autodiscovery (models/urls/admin)
    # Use str type to prevent JSON parsing, then convert in validator
    INSTALLED_APPS: str = Field(default="project.apps.users")

    # API routing
    API_PREFIX: str = "/api/v1"

    # Middleware config - use str to prevent JSON parsing
    CORS_ORIGINS: str = Field(default="http://localhost:3000")
    TRUSTED_HOSTS: str = Field(default="localhost,127.0.0.1")

    # Admin
    ADMIN_PATH: str = "/admin"

    # Auth
    JWT_SECRET: str = "change-me-too"
    JWT_LIFETIME_SECONDS: int = 3600

    @field_validator("CORS_ORIGINS", "TRUSTED_HOSTS", "INSTALLED_APPS", mode="after")
    @classmethod
    def _split_csv(cls, v: Any) -> list[str]:
        # If it's already a list, return as-is
        if isinstance(v, list):
            return v
        if v is None:
            return []
        if isinstance(v, str):
            # Handle empty strings
            if not v.strip():
                return []
            parts = [p.strip() for p in v.split(",")]
            return [p for p in parts if p]
        return []

    @property
    def installed_apps_list(self) -> list[str]:
        """Get INSTALLED_APPS as a list."""
        return self._split_csv(self.INSTALLED_APPS)

    @property
    def cors_origins_list(self) -> list[str]:
        """Get CORS_ORIGINS as a list."""
        return self._split_csv(self.CORS_ORIGINS)

    @property
    def trusted_hosts_list(self) -> list[str]:
        """Get TRUSTED_HOSTS as a list."""
        return self._split_csv(self.TRUSTED_HOSTS)

    @property
    def databases_dict(self) -> dict[str, str]:
        """
        Get DATABASES as a dictionary (Django-like).
        
        Format: DATABASES=default:sqlite+aiosqlite:///./db.sqlite3,analytics:postgresql+asyncpg://...
        Or use DATABASE_URL for single database (backward compatibility).
        
        Returns:
            Dictionary mapping database alias to connection URL
        """
        if self.DATABASES:
            # Parse DATABASES string: "default:url1,analytics:url2"
            databases = {}
            for db_config in self.DATABASES.split(","):
                db_config = db_config.strip()
                if ":" in db_config:
                    alias, url = db_config.split(":", 1)
                    databases[alias.strip()] = url.strip()
            return databases
        else:
            # Backward compatibility: use DATABASE_URL as "default"
            return {"default": self.DATABASE_URL}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


