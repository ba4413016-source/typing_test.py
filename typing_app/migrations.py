"""Small additive, versioned schema migrations for the initial application schema.

The initial schema is still created from SQLAlchemy metadata. These migrations
upgrade existing installations without dropping or rewriting user data.
"""

from sqlalchemy import inspect, text


_VERSION = "2026-11-challenge-events-v1"
_COLUMNS = {
    "mt_challenges": {
        "round_count": 'INTEGER NOT NULL DEFAULT 1',
        "current_round": 'INTEGER NOT NULL DEFAULT 0',
        "judge_mode": "VARCHAR(16) NOT NULL DEFAULT 'points'",
        "event_kind": "VARCHAR(16) NOT NULL DEFAULT 'challenge'",
        "scheduled_at": "TIMESTAMP WITH TIME ZONE",
        "topic": "VARCHAR(24) NOT NULL DEFAULT 'mixed'",
    },
    "mt_rounds": {
        "challenge_round": "INTEGER NOT NULL DEFAULT 1",
        "topic": "VARCHAR(24) NOT NULL DEFAULT 'mixed'",
    },
    "mt_messages": {
        "media_id": "VARCHAR(36)",
        "challenge_token": "VARCHAR(64)",
    },
}


def apply_migrations(connection) -> None:
    """Apply known additive migrations once, under the caller's DB transaction."""
    connection.execute(
        text(
            "CREATE TABLE IF NOT EXISTS mt_schema_migrations ("
            "version VARCHAR(80) PRIMARY KEY, "
            "applied_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP)"
        )
    )
    applied = connection.execute(
        text("SELECT version FROM mt_schema_migrations WHERE version = :version"),
        {"version": _VERSION},
    ).first()
    if applied:
        return

    existing_tables = set(inspect(connection).get_table_names())
    for table, columns in _COLUMNS.items():
        if table not in existing_tables:
            continue
        existing_columns = {
            column["name"] for column in inspect(connection).get_columns(table)
        }
        for name, definition in columns.items():
            if name not in existing_columns:
                connection.execute(
                    text(f'ALTER TABLE "{table}" ADD COLUMN "{name}" {definition}')
                )

    connection.execute(
        text("INSERT INTO mt_schema_migrations (version) VALUES (:version)"),
        {"version": _VERSION},
    )
