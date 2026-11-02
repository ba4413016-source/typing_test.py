from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from io import BytesIO

from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import select

from typing_app.api import create_app
from typing_app.config import Settings
from typing_app.models import Attempt, LoginSession, Message, PracticeRound, User


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(
            create_app(
                Settings(database_url="sqlite://", cookie_secure=False, testing=True)
            )
        )
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def register(self, username, password="correct-horse-123", display_name=None):
        payload = {"username": username, "password": password}
        if display_name:
            payload["display_name"] = display_name
        response = self.client.post("/api/auth/register", json=payload)
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    @staticmethod
    def csrf(data):
        return {"X-CSRF-Token": data["csrf"]}

    def login(self, username):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "correct-horse-123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()

    def logout(self, data):
        response = self.client.post("/api/auth/logout", headers=self.csrf(data))
        self.assertEqual(response.status_code, 200, response.text)
        self.client.cookies.clear()

    def test_register_session_cookie_csrf_and_password_hash(self):
        data = self.register("Alice_1")
        self.assertEqual(data["user"]["username"], "alice_1")
        self.assertTrue(data["csrf"])
        self.assertTrue(self.client.cookies.get("mt_session"))
        self.assertNotIn("password_hash", data["user"])
        self.assertNotIn("token", data["user"])
        self.assertEqual(self.client.get("/api/me").status_code, 200)
        self.assertEqual(
            self.client.patch("/api/me/bot", json={"name": "New bot"}).status_code, 403
        )
        self.assertEqual(
            self.client.patch(
                "/api/me/bot", json={"name": "New bot"}, headers=self.csrf(data)
            ).status_code,
            200,
        )
        with self.client.app.state.session_factory() as db:
            user = db.scalar(select(User).where(User.username == "alice_1"))
            self.assertNotEqual(user.password_hash, "correct-horse-123")
            self.assertTrue(user.password_hash.startswith("$argon2"))

    def test_case_insensitive_unique_and_username_password_policies(self):
        self.register("CaseUser")
        response = self.client.post(
            "/api/auth/register",
            json={"username": "caseuser", "password": "correct-horse-456"},
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(
            self.client.post(
                "/api/auth/register",
                json={"username": "12_", "password": "correct-horse-456"},
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/auth/register", json={"username": "okuser", "password": "short"}
            ).status_code,
            422,
        )
        self.assertEqual(
            self.client.post(
                "/api/auth/register",
                json={
                    "username": "okuser",
                    "password": "correct-horse-456",
                    "unexpected": 1,
                },
            ).status_code,
            422,
        )

    def test_authentication_csrf_origin_and_logout_revocation(self):
        self.assertEqual(self.client.get("/api/me").status_code, 401)
        data = self.register("security")
        bad = self.client.patch(
            "/api/me/bot", json={"name": "Bot"}, headers={"X-CSRF-Token": "wrong"}
        )
        self.assertEqual(bad.status_code, 403)
        cross = self.client.patch(
            "/api/me/bot",
            json={"name": "Bot"},
            headers={**self.csrf(data), "Origin": "https://evil.example"},
        )
        self.assertEqual(cross.status_code, 403)
        self.assertEqual(
            self.client.post("/api/auth/logout", headers=self.csrf(data)).json(),
            {"ok": True},
        )
        self.assertEqual(self.client.get("/api/me").status_code, 401)

    def test_follow_followback_and_block_removes_both_directions(self):
        self.register("follow_a")
        self.client.cookies.clear()
        self.register("follow_b")
        self.client.cookies.clear()
        login_a = self.login("follow_a")
        self.assertEqual(
            self.client.post(
                "/api/users/follow_b/follow", headers=self.csrf(login_a)
            ).status_code,
            200,
        )
        self.logout(login_a)
        login_b = self.login("follow_b")
        self.assertEqual(
            self.client.post(
                "/api/users/follow_a/follow", headers=self.csrf(login_b)
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                "/api/users/follow_a/block", headers=self.csrf(login_b)
            ).status_code,
            200,
        )
        profile_a = self.client.get("/api/users/follow_a").json()["user"]
        self.assertEqual(profile_a["followers"], 0)
        self.assertEqual(profile_a["following"], 0)
        self.assertEqual(
            self.client.post(
                "/api/users/follow_a/follow", headers=self.csrf(login_b)
            ).status_code,
            403,
        )

    def test_dm_is_private_and_read_state_requires_explicit_read(self):
        self.register("sender")
        self.client.cookies.clear()
        self.register("recipient")
        self.client.cookies.clear()
        sender = self.login("sender")
        response = self.client.post(
            "/api/messages/recipient",
            json={"body": "private words"},
            headers=self.csrf(sender),
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.logout(sender)
        recipient = self.login("recipient")
        self.assertEqual(recipient["unread_notifications"], 1)
        self.assertEqual(recipient["unread_messages"], 1)
        self.assertEqual(
            self.client.get("/api/messages/sender").json()["messages"][0]["body"],
            "private words",
        )
        self.assertEqual(self.client.get("/api/session").json()["unread_messages"], 1)
        self.assertEqual(
            self.client.post(
                "/api/messages/sender/read", headers=self.csrf(recipient)
            ).json(),
            {"ok": True},
        )
        self.assertEqual(self.client.get("/api/session").json()["unread_messages"], 0)
        self.logout(recipient)
        self.register("outsider")
        private_view = self.client.get("/api/messages/sender")
        self.assertEqual(private_view.status_code, 200)
        self.assertEqual(private_view.json()["messages"], [])

    def test_account_deletion_removes_messages_in_both_directions(self):
        self.register("erase_user")
        self.client.cookies.clear()
        peer = self.register("erase_peer")
        received = self.client.post(
            "/api/messages/erase_user",
            json={"body": "sent to the account being deleted"},
            headers=self.csrf(peer),
        )
        self.assertEqual(received.status_code, 200, received.text)
        self.logout(peer)

        account = self.login("erase_user")
        sent = self.client.post(
            "/api/messages/erase_peer",
            json={"body": "sent by the account being deleted"},
            headers=self.csrf(account),
        )
        self.assertEqual(sent.status_code, 200, sent.text)
        with self.client.app.state.session_factory() as db:
            user = db.scalar(select(User).where(User.username == "erase_user"))
            user_id = user.id
            self.assertEqual(len(db.scalars(select(Message)).all()), 2)

        rejected = self.client.request(
            "DELETE",
            "/api/me",
            json={"password": "incorrect-password", "confirm_username": "erase_user"},
            headers=self.csrf(account),
        )
        self.assertEqual(rejected.status_code, 403)
        with self.client.app.state.session_factory() as db:
            self.assertIsNotNone(db.get(User, user_id))
            self.assertEqual(len(db.scalars(select(Message)).all()), 2)

        deleted = self.client.request(
            "DELETE",
            "/api/me",
            json={"password": "correct-horse-123", "confirm_username": "erase_user"},
            headers=self.csrf(account),
        )
        self.assertEqual(deleted.status_code, 200, deleted.text)
        self.assertEqual(deleted.json(), {"ok": True})
        self.assertIsNone(self.client.cookies.get("mt_session"))
        self.assertIsNone(self.client.get("/api/session").json()["user"])
        with self.client.app.state.session_factory() as db:
            self.assertIsNone(db.get(User, user_id))
            self.assertEqual(db.scalars(select(Message)).all(), [])
            self.assertEqual(
                db.scalars(
                    select(LoginSession).where(LoginSession.user_id == user_id)
                ).all(),
                [],
            )
            self.assertIsNotNone(
                db.scalar(select(User).where(User.username == "erase_peer"))
            )

    def test_block_hides_unread_without_marking_read_and_prevents_later_messages(self):
        self.register("block_sender")
        self.client.cookies.clear()
        self.register("block_recipient")
        self.client.cookies.clear()
        sender = self.login("block_sender")
        sent = self.client.post(
            "/api/messages/block_recipient",
            json={"body": "unread until blocked"},
            headers=self.csrf(sender),
        )
        self.assertEqual(sent.status_code, 200, sent.text)
        self.logout(sender)

        recipient = self.login("block_recipient")
        self.assertEqual(recipient["unread_messages"], 1)
        blocked = self.client.post(
            "/api/users/block_sender/block", headers=self.csrf(recipient)
        )
        self.assertEqual(blocked.status_code, 200, blocked.text)
        session = self.client.get("/api/session").json()
        self.assertEqual(session["unread_messages"], 0)
        self.assertEqual(self.client.get("/api/messages/threads").json()["threads"], [])
        self.assertEqual(
            self.client.post(
                "/api/messages/block_sender/read", headers=self.csrf(recipient)
            ).status_code,
            403,
        )
        with self.client.app.state.session_factory() as db:
            message = db.scalar(select(Message))
            self.assertIsNone(message.read_at)

        self.logout(recipient)
        sender = self.login("block_sender")
        rejected = self.client.post(
            "/api/messages/block_recipient",
            json={"body": "must be rejected"},
            headers=self.csrf(sender),
        )
        self.assertEqual(rejected.status_code, 403)

    def test_avatar_reencoding_and_invalid_upload(self):
        data = self.register("avataruser")
        csrf = self.csrf(data)
        bad = self.client.post(
            "/api/me/avatar",
            files={"image": ("bad.png", b"not image", "image/png")},
            headers=csrf,
        )
        self.assertEqual(bad.status_code, 422)
        image = Image.new("RGB", (12, 8), "red")
        raw = BytesIO()
        image.save(raw, format="PNG")
        response = self.client.post(
            "/api/me/avatar",
            files={"image": ("source.png", raw.getvalue(), "image/png")},
            headers=csrf,
        )
        self.assertEqual(response.status_code, 200, response.text)
        fetched = self.client.get(response.json()["user"]["avatar_url"])
        self.assertEqual(fetched.status_code, 200)
        self.assertEqual(fetched.headers["content-type"], "image/webp")
        self.assertEqual(fetched.content[:4], b"RIFF")
        self.assertEqual(fetched.content[8:12], b"WEBP")
        self.assertEqual(fetched.headers["x-content-type-options"], "nosniff")

    def test_round_server_scoring_ownership_and_duplicate_submit(self):
        data = self.register("round_user")
        csrf = self.csrf(data)
        response = self.client.post(
            "/api/rounds",
            json={"game": "repeat", "difficulty": "easy", "language": "en", "count": 1},
            headers=csrf,
        )
        self.assertEqual(response.status_code, 200, response.text)
        rid = response.json()["round"]["id"]
        with self.client.app.state.session_factory() as db:
            round_obj = db.get(PracticeRound, rid)
            round_obj.started_at = datetime.now(timezone.utc) - timedelta(seconds=120)
            db.commit()
            expected = round_obj.expected
        score = self.client.post(
            f"/api/rounds/{rid}/submit", json={"text": expected}, headers=csrf
        )
        self.assertEqual(score.status_code, 200, score.text)
        result = score.json()["result"]
        self.assertTrue(result["eligible"])
        self.assertGreater(result["wpm"], 0)
        self.assertIn("stats", result)
        self.assertGreater(result["points"], 0)
        self.assertEqual(
            self.client.post(
                f"/api/rounds/{rid}/submit", json={"text": expected}, headers=csrf
            ).status_code,
            409,
        )
        with self.client.app.state.session_factory() as db:
            self.assertIsNotNone(
                db.scalar(select(Attempt).where(Attempt.round_id == rid))
            )
        # A different account cannot access or submit the round.
        self.logout(data)
        other = self.register("round_other")
        self.assertEqual(
            self.client.post(
                f"/api/rounds/{rid}/cancel", headers=self.csrf(other)
            ).status_code,
            404,
        )

    def test_challenge_host_only_shared_target_and_no_lobby_target(self):
        owner = self.register("hostuser")
        response = self.client.post(
            "/api/challenges",
            json={
                "game": "repeat",
                "difficulty": "easy",
                "language": "en",
                "count": 1,
                "visibility": "private",
                "max_players": 3,
            },
            headers=self.csrf(owner),
        )
        self.assertEqual(response.status_code, 200, response.text)
        challenge = response.json()["challenge"]
        self.assertIsNone(challenge.get("round"))
        token = challenge["token"]
        self.client.cookies.clear()
        self.register("guestuser")
        guest = self.login("guestuser")
        self.assertEqual(
            self.client.post(
                f"/api/challenges/{token}/start", headers=self.csrf(guest)
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.post(
                f"/api/challenges/{token}/join", headers=self.csrf(guest)
            ).status_code,
            200,
        )
        self.logout(guest)
        owner = self.login("hostuser")
        started = self.client.post(
            f"/api/challenges/{token}/start", headers=self.csrf(owner)
        )
        self.assertEqual(started.status_code, 200, started.text)
        payload = started.json()["challenge"]
        self.assertEqual(payload["status"], "active")
        self.assertIsNotNone(payload["round"])
        shared_target = payload["round"]["target"]
        self.logout(owner)
        guest = self.login("guestuser")
        guest_payload = self.client.get(f"/api/challenges/{token}").json()["challenge"]
        self.assertEqual(guest_payload["round"]["target"], shared_target)

    def test_admin_queue_permissions_and_review_notification(self):
        self.register("normaluser")
        csrf = self.client.get("/api/session").json()["csrf"]
        suggestion = self.client.post(
            "/api/suggestions",
            json={"title": "An idea", "body": "A thoughtful proposal"},
            headers={"X-CSRF-Token": csrf},
        )
        self.assertEqual(suggestion.status_code, 200)
        self.assertEqual(self.client.get("/api/admin/suggestions").status_code, 403)
        self.logout({"csrf": csrf})
        self.register("reviewadmin")
        self.logout({"csrf": self.client.get("/api/session").json()["csrf"]})
        with self.client.app.state.session_factory() as db:
            admin = db.scalar(select(User).where(User.username == "reviewadmin"))
            admin.role = "admin"
            db.commit()
        admin_data = self.login("reviewadmin")
        queue = self.client.get("/api/admin/suggestions")
        self.assertEqual(queue.status_code, 200)
        self.assertEqual(
            queue.json()["suggestions"][0]["user"]["username"], "normaluser"
        )
        item_id = suggestion.json()["suggestion"]["id"]
        reviewed = self.client.patch(
            f"/api/admin/suggestions/{item_id}",
            json={"status": "approved", "admin_note": "Looks good"},
            headers=self.csrf(admin_data),
        )
        self.assertEqual(reviewed.status_code, 200)
        self.assertEqual(reviewed.json()["suggestion"]["status"], "approved")
        self.logout(admin_data)
        self.login("normaluser")
        self.assertEqual(
            self.client.get("/api/notifications").json()["notifications"][0]["kind"],
            "suggestion_review",
        )

    def test_pwa_assets_are_served_from_origin_root(self):
        expected_types = {
            "/manifest.json": "application/manifest+json",
            "/sw.js": "application/javascript",
            "/static/pwa.js": "text/javascript",
            "/apple-touch-icon.png": "image/png",
            "/icon-192.png": "image/png",
            "/icon-512.png": "image/png",
        }
        for path, media_type in expected_types.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200, response.text[:200])
                self.assertTrue(response.headers["content-type"].startswith(media_type))
                self.assertGreater(len(response.content), 0)
        self.assertEqual(
            self.client.get("/sw.js").headers.get("service-worker-allowed"), "/"
        )


if __name__ == "__main__":
    unittest.main()
