from collections import deque
from io import BytesIO
import os
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from PIL import Image
from sqlalchemy.exc import IntegrityError

from typing_app.config import Settings
from typing_app.database import initialize_database, make_engine, make_session_factory
from typing_app.models import User
from typing_app.security import (
    RateLimiter,
    clean_text,
    normalize_username,
    normalized_avatar,
    password_hash,
    password_matches,
    social_handle,
)


class SecurityUnitTests(unittest.TestCase):
    def test_username_policy_and_normalization(self):
        self.assertEqual(normalize_username("  Bader.12_x  "), "bader.12_x")
        for value in ("ab", "1234", "عربي", "bad name", "a-b", "a@b", "a" * 25):
            with self.subTest(value=value), self.assertRaises(ValueError):
                normalize_username(value)

    def test_password_is_hashed_and_verified(self):
        encoded = password_hash("example-not-a-real-secret")
        self.assertTrue(encoded.startswith("$argon2id$"))
        self.assertTrue(password_matches(encoded, "example-not-a-real-secret"))
        self.assertFalse(password_matches(encoded, "incorrect-password"))
        with self.assertRaises(ValueError):
            password_hash("short")

    def test_handles_cannot_be_arbitrary_urls(self):
        self.assertEqual(social_handle("@bader_12", "twitter"), "bader_12")
        for value in ("https://example.com", "javascript:alert(1)", "a/b"):
            with self.assertRaises(ValueError):
                social_handle(value, "instagram")

    def test_display_text_preserves_arabic_but_rejects_overrides(self):
        self.assertEqual(clean_text("  سيارة جميلة  ", 1, 40), "سيارة جميلة")
        with self.assertRaises(ValueError):
            clean_text("name\u202eevil", 1, 40)

    def test_avatar_is_decoded_resized_and_reencoded(self):
        source = BytesIO()
        Image.new("RGBA", (700, 400), (100, 120, 240, 255)).save(source, "PNG")
        result = normalized_avatar(source.getvalue())
        with Image.open(BytesIO(result)) as image:
            self.assertEqual(image.format, "WEBP")
            self.assertEqual(image.size, (256, 256))
            self.assertFalse(image.getexif())
        for raw in (b"<svg><script>bad</script></svg>", b"x" * (2 * 1024 * 1024 + 1)):
            with self.assertRaises(ValueError):
                normalized_avatar(raw)

    def test_limiter_limits_requests_and_total_memory_keys(self):
        limiter = RateLimiter()
        limiter.check("one", 1, 60)
        with self.assertRaises(HTTPException):
            limiter.check("one", 1, 60)
        limiter.events = {str(i): deque([time.monotonic()]) for i in range(10000)}
        with self.assertRaises(HTTPException):
            limiter.check("new", 1, 60)
        self.assertEqual(len(limiter.events), 10000)

    def test_database_enforces_unique_normalized_usernames(self):
        engine = make_engine("sqlite://")
        initialize_database(engine)
        factory = make_session_factory(engine)
        with factory() as db:
            db.add(
                User(username="bader", display_name="Bader", password_hash="test-only")
            )
            db.commit()
            for username in ("bader", "BADER"):
                db.add(
                    User(
                        username=username,
                        display_name="Other",
                        password_hash="test-only",
                    )
                )
                with self.assertRaises(IntegrityError):
                    db.commit()
                db.rollback()
        engine.dispose()

    def test_render_refuses_ephemeral_database_and_uses_external_url(self):
        with patch.dict(os.environ, {"RENDER": "true", "DATABASE_URL": ""}):
            with self.assertRaises(RuntimeError):
                Settings.from_env()
        with patch.dict(
            os.environ,
            {
                "RENDER": "true",
                "DATABASE_URL": "postgresql://user:placeholder@db/db",
                "PUBLIC_URL": "",
                "RENDER_EXTERNAL_URL": "https://example.onrender.com",
            },
        ):
            settings = Settings.from_env()
            self.assertTrue(settings.cookie_secure)
            self.assertEqual(settings.public_url, "https://example.onrender.com")
            self.assertTrue(settings.database_url.startswith("postgresql+psycopg://"))

    def test_secure_cookie_defaults_to_true_outside_render(self):
        self.assertTrue(Settings().cookie_secure)
        with patch.dict(os.environ, {"DATABASE_URL": "sqlite://"}, clear=True):
            self.assertTrue(Settings.from_env().cookie_secure)
        with patch.dict(
            os.environ,
            {"DATABASE_URL": "sqlite://", "SESSION_COOKIE_SECURE": "false"},
            clear=True,
        ):
            self.assertFalse(Settings.from_env().cookie_secure)

    def test_secure_cookie_cannot_be_disabled_on_render_or_https(self):
        cases = (
            {
                "DATABASE_URL": "postgresql://user:placeholder@db/db",
                "RENDER": "true",
                "SESSION_COOKIE_SECURE": "false",
            },
            {
                "DATABASE_URL": "sqlite://",
                "PUBLIC_URL": "https://example.test",
                "SESSION_COOKIE_SECURE": "0",
            },
            {"DATABASE_URL": "sqlite://", "SESSION_COOKIE_SECURE": "truue"},
        )
        for env in cases:
            with self.subTest(env=env), patch.dict(
                os.environ, env, clear=True
            ), self.assertRaises(RuntimeError):
                Settings.from_env()

    def test_render_rejects_sqlite_even_if_database_url_is_present(self):
        with patch.dict(
            os.environ, {"RENDER": "true", "DATABASE_URL": "sqlite://"}, clear=True
        ), self.assertRaises(RuntimeError):
            Settings.from_env()


if __name__ == "__main__":
    unittest.main()
