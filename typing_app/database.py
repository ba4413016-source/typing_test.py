from __future__ import annotations

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from .models import Base


def make_engine(url: str) -> Engine:
    options: dict = {"pool_pre_ping": True}
    if url.startswith("sqlite:"):
        options["connect_args"] = {"check_same_thread": False}
        if url in {"sqlite://", "sqlite:///:memory:"}:
            options["poolclass"] = StaticPool
    else:
        options.update(pool_size=5, max_overflow=5, pool_timeout=15)
    engine = create_engine(url, **options)
    if url.startswith("sqlite:"):

        @event.listens_for(engine, "connect")
        def sqlite_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def initialize_database(engine: Engine) -> None:
    # Initial schema only: create_all never drops or rewrites existing data.
    # A transaction-scoped advisory lock serializes concurrent initial deploys.
    with engine.begin() as connection:
        if engine.dialect.name == "postgresql":
            connection.execute(text("SELECT pg_advisory_xact_lock(748219341)"))
        Base.metadata.create_all(connection)


def make_session_factory(engine: Engine):
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
