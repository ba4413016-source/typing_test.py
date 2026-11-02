from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tempfile
import unittest

from sqlalchemy import inspect, text

from typing_app.database import initialize_database, make_engine
from typing_app.migrations import apply_migrations


class MigrationTests(unittest.TestCase):
    def test_legacy_sqlite_schema_gets_all_additive_columns_idempotently(self):
        engine = make_engine("sqlite://")
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql("CREATE TABLE mt_challenges (id VARCHAR(36) PRIMARY KEY)")
                connection.exec_driver_sql("CREATE TABLE mt_rounds (id VARCHAR(36) PRIMARY KEY)")
                connection.exec_driver_sql("CREATE TABLE mt_messages (id INTEGER PRIMARY KEY)")
                apply_migrations(connection)
                apply_migrations(connection)
                columns = {
                    table: {item["name"] for item in inspect(connection).get_columns(table)}
                    for table in ("mt_challenges", "mt_rounds", "mt_messages")
                }
            self.assertTrue(
                {
                    "round_count", "current_round", "judge_mode", "event_kind",
                    "scheduled_at", "topic",
                }.issubset(columns["mt_challenges"])
            )
            self.assertTrue({"challenge_round", "topic"}.issubset(columns["mt_rounds"]))
            self.assertTrue({"media_id", "challenge_token"}.issubset(columns["mt_messages"]))
        finally:
            engine.dispose()

    def test_parallel_sqlite_initialization_serializes_schema_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            url = f"sqlite:///{Path(directory) / 'parallel.db'}"

            def initialize():
                engine = make_engine(url)
                try:
                    initialize_database(engine)
                finally:
                    engine.dispose()

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(lambda _: initialize(), range(2)))
            self.assertEqual(results, [None, None])

            engine = make_engine(url)
            try:
                with engine.connect() as connection:
                    applied = connection.scalar(
                        text("SELECT COUNT(*) FROM mt_schema_migrations")
                    )
                self.assertEqual(applied, 1)
            finally:
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
