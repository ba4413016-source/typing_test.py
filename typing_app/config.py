from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    database_url: str = "sqlite:///./data/local.db"
    cookie_secure: bool = True
    admin_username: str = ""
    admin_password: str = ""
    public_url: str = ""
    testing: bool = False
    session_days: int = 14

    @classmethod
    def from_env(cls) -> "Settings":
        on_render = os.getenv("RENDER", "").lower() in {"true", "1"}
        database_url = os.getenv("DATABASE_URL", "").strip()
        if on_render and not database_url:
            raise RuntimeError(
                "DATABASE_URL is required on Render. Attach persistent PostgreSQL before deploying accounts."
            )
        if not database_url:
            Path("data").mkdir(exist_ok=True)
            database_url = "sqlite:///./data/local.db"
        if database_url.startswith("postgres://"):
            database_url = database_url.replace(
                "postgres://", "postgresql+psycopg://", 1
            )
        elif database_url.startswith("postgresql://"):
            database_url = database_url.replace(
                "postgresql://", "postgresql+psycopg://", 1
            )
        if not database_url.startswith(("sqlite:", "postgresql+psycopg:")):
            raise RuntimeError(
                "Only SQLite for local development and PostgreSQL are supported."
            )
        if on_render and not database_url.startswith("postgresql+psycopg:"):
            raise RuntimeError(
                "Render requires persistent PostgreSQL; SQLite is local-development only."
            )
        public_url = (
            os.getenv("PUBLIC_URL") or os.getenv("RENDER_EXTERNAL_URL", "")
        ).rstrip("/")
        raw_secure = os.getenv("SESSION_COOKIE_SECURE", "true").strip().lower()
        if raw_secure not in {"true", "false", "1", "0"}:
            raise RuntimeError("SESSION_COOKIE_SECURE must be true, false, 1, or 0.")
        cookie_secure = raw_secure in {"true", "1"}
        if not cookie_secure and (
            on_render or public_url.lower().startswith("https://")
        ):
            raise RuntimeError(
                "Secure session cookies cannot be disabled on Render or an HTTPS public URL."
            )
        return cls(
            database_url=database_url,
            cookie_secure=cookie_secure,
            admin_username=os.getenv("ADMIN_USERNAME", "").strip(),
            admin_password=os.getenv("ADMIN_BOOTSTRAP_PASSWORD", ""),
            public_url=public_url,
        )
