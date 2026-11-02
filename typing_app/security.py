from __future__ import annotations

import hashlib
import re
import secrets
import threading
import time
import unicodedata
import warnings
from collections import defaultdict, deque
from datetime import datetime, timezone
from io import BytesIO
from urllib.parse import urlsplit

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from fastapi import HTTPException, Request
from PIL import Image, ImageOps, UnidentifiedImageError

PASSWORDS = PasswordHasher()
USERNAME_RE = re.compile(r"^[a-z0-9._]{3,24}$")


def normalize_username(value: str) -> str:
    username = value.strip().lower()
    if not USERNAME_RE.fullmatch(username) or not re.search(r"[a-z]", username):
        raise ValueError(
            "Username must be 3–24 English letters, digits, dots or underscores, with at least one letter."
        )
    return username


def validate_password(value: str) -> str:
    if len(value) < 10 or len(value) > 128:
        raise ValueError("Password must contain 10–128 characters.")
    return value


def clean_text(value: str, minimum: int, maximum: int) -> str:
    value = unicodedata.normalize("NFC", value.strip())
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"Text must contain {minimum}–{maximum} characters.")
    if any(unicodedata.category(char) == "Cc" and char not in "\n\t" for char in value):
        raise ValueError("Control characters are not allowed.")
    if any(
        0x202A <= ord(char) <= 0x202E or 0x2066 <= ord(char) <= 0x2069 for char in value
    ):
        raise ValueError("Directional override characters are not allowed.")
    return value


def social_handle(value: str, network: str) -> str:
    value = value.strip().lstrip("@")
    if not value:
        return ""
    patterns = {
        "instagram": r"[A-Za-z0-9._]{1,30}",
        "snapchat": r"[A-Za-z0-9._-]{1,30}",
        "twitter": r"[A-Za-z0-9_]{1,15}",
    }
    if not re.fullmatch(patterns[network], value):
        raise ValueError(f"Invalid {network} username; enter a handle, not a URL.")
    return value


def password_hash(value: str) -> str:
    return PASSWORDS.hash(validate_password(value))


def password_matches(encoded: str, value: str) -> bool:
    try:
        return PASSWORDS.verify(encoded, value)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def opaque_token() -> str:
    return secrets.token_urlsafe(32)


def digest_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def aware(value: datetime) -> datetime:
    return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value


def same_origin(request: Request) -> None:
    origin = request.headers.get("origin")
    if not origin:
        return
    expected = request.app.state.settings.public_url or str(request.base_url).rstrip(
        "/"
    )
    a, b = urlsplit(origin), urlsplit(expected)
    if (a.scheme, a.netloc) != (b.scheme, b.netloc):
        raise HTTPException(403, "Cross-origin requests are not allowed.")


class RateLimiter:
    """Bounded single-instance abuse protection; no claim of distributed rate limiting."""

    def __init__(self):
        self.events: dict[str, deque[float]] = defaultdict(deque)
        self.lock = threading.Lock()

    def check(self, key: str, limit: int, seconds: int) -> None:
        now = time.monotonic()
        with self.lock:
            if key not in self.events and len(self.events) >= 10000:
                for old_key, old_queue in list(self.events.items()):
                    if not old_queue or old_queue[-1] < now - 3600:
                        self.events.pop(old_key, None)
                if len(self.events) >= 10000:
                    raise HTTPException(
                        429, "Request capacity reached. Try again shortly."
                    )
            queue = self.events[key]
            while queue and queue[0] <= now - seconds:
                queue.popleft()
            if len(queue) >= limit:
                raise HTTPException(
                    429,
                    "Too many requests. Try again shortly.",
                    headers={"Retry-After": str(seconds)},
                )
            queue.append(now)


def normalized_avatar(raw: bytes) -> bytes:
    if not raw or len(raw) > 2 * 1024 * 1024:
        raise ValueError("Upload a JPEG, PNG or WebP image no larger than 2 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Only JPEG, PNG and WebP images are supported.")
                if image.width > 4096 or image.height > 4096:
                    raise ValueError("Image dimensions must not exceed 4096×4096.")
                image.load()
                image = ImageOps.exif_transpose(image).convert("RGB")
                image = ImageOps.fit(image, (256, 256), method=Image.Resampling.LANCZOS)
                output = BytesIO()
                # A fresh encoding removes EXIF and prevents serving the uploaded original.
                image.save(output, format="WEBP", quality=82, method=4)
                return output.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("The uploaded file is not a valid supported image.") from exc



def normalized_message_image(raw: bytes) -> bytes:
    """Validate and resize a message image without cropping its aspect ratio."""
    if not raw or len(raw) > 5 * 1024 * 1024:
        raise ValueError("Upload an image no larger than 5 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValueError("Only JPEG, PNG and WebP images are supported.")
                if image.width > 4096 or image.height > 4096:
                    raise ValueError("Image dimensions must not exceed 4096×4096.")
                image.load()
                image = ImageOps.exif_transpose(image).convert("RGB")
                image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
                output = BytesIO()
                image.save(output, format="WEBP", quality=84, method=4)
                return output.getvalue()
    except (
        UnidentifiedImageError,
        OSError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise ValueError("The uploaded file is not a valid supported image.") from exc


class _MessageImageBodyTooLarge(Exception):
    pass


class MessageImageBodyLimitMiddleware:
    """Bound private-image upload bodies before multipart parsing or buffering."""

    def __init__(self, app, max_bytes: int = 6 * 1024 * 1024):
        self.app = app
        self.max_bytes = max_bytes

    @staticmethod
    def _is_message_image_upload(scope) -> bool:
        if scope.get("type") != "http" or scope.get("method") != "POST":
            return False
        parts = scope.get("path", "").strip("/").split("/")
        return (
            len(parts) == 4
            and parts[0] == "api"
            and parts[1] == "messages"
            and bool(parts[2])
            and parts[3] == "image"
        )

    async def _reject(self, send, status: int = 413) -> None:
        body = (
            b'{"detail":"Upload request exceeds the allowed size."}'
            if status == 413
            else b'{"detail":"Invalid Content-Length."}'
        )
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("ascii")),
                    (b"cache-control", b"no-store"),
                    (b"x-content-type-options", b"nosniff"),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body})

    async def __call__(self, scope, receive, send):
        if not self._is_message_image_upload(scope):
            await self.app(scope, receive, send)
            return

        for name, value in scope.get("headers", []):
            if name.lower() == b"content-length":
                try:
                    length = int(value)
                except (TypeError, ValueError):
                    await self._reject(send, 400)
                    return
                if length < 0:
                    await self._reject(send, 400)
                    return
                if length > self.max_bytes:
                    await self._reject(send)
                    return

        received = 0
        response_started = False

        async def limited_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _MessageImageBodyTooLarge
            return message

        async def tracked_send(message):
            nonlocal response_started
            if message.get("type") == "http.response.start":
                response_started = True
            await send(message)

        try:
            await self.app(scope, limited_receive, tracked_send)
        except _MessageImageBodyTooLarge:
            if not response_started:
                await self._reject(send)
