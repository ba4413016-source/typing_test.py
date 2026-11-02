from datetime import timedelta
import unittest

from fastapi.testclient import TestClient
from sqlalchemy import select

from typing_app.api import create_app
from typing_app.config import Settings
from typing_app.models import Challenge, PracticeRound, utcnow


class ChallengeRegressionTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(
            create_app(
                Settings(database_url="sqlite://", testing=True, cookie_secure=False)
            )
        )
        self.client.__enter__()

    def tearDown(self):
        self.client.__exit__(None, None, None)

    def register(self, username):
        self.client.cookies.clear()
        response = self.client.post(
            "/api/auth/register",
            json={"username": username, "password": "only-for-test-123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"X-CSRF-Token": response.json()["csrf"]}

    def login(self, username):
        self.client.cookies.clear()
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": "only-for-test-123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return {"X-CSRF-Token": response.json()["csrf"]}

    def create(self, headers, visibility="private"):
        response = self.client.post(
            "/api/challenges",
            headers=headers,
            json={
                "game": "repeat",
                "difficulty": "easy",
                "language": "ar",
                "count": 1,
                "visibility": visibility,
                "max_players": 2,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["challenge"]

    def test_invitee_can_preview_private_lobby_without_receiving_target(self):
        challenge = self.create(self.register("host"))
        self.register("invitee")
        response = self.client.get(f'/api/challenges/{challenge["token"]}')
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIsNone(response.json()["challenge"]["round"])
        self.assertEqual(self.client.get("/api/challenges").json()["challenges"], [])

    def test_public_challenge_exposes_join_token_to_nonmember(self):
        challenge = self.create(self.register("host"), "public")
        self.register("viewer")
        listed = self.client.get("/api/challenges").json()["challenges"]
        self.assertEqual(listed[0]["token"], challenge["token"])
        self.assertIsNone(listed[0]["round"])

    def test_expired_lobby_cannot_start_and_expiry_is_persisted(self):
        host = self.register("host")
        challenge = self.create(host)
        guest = self.register("guest")
        self.client.post(f'/api/challenges/{challenge["token"]}/join', headers=guest)
        with self.client.app.state.session_factory() as db:
            row = db.get(Challenge, challenge["id"])
            row.expires_at = utcnow() - timedelta(seconds=1)
            db.commit()
        host = self.login("host")
        response = self.client.post(
            f'/api/challenges/{challenge["token"]}/start', headers=host
        )
        self.assertEqual(response.status_code, 409, response.text)
        with self.client.app.state.session_factory() as db:
            self.assertEqual(db.get(Challenge, challenge["id"]).status, "expired")

    def test_completed_results_are_linked_and_winner_is_available(self):
        host = self.register("host")
        challenge = self.create(host)
        guest = self.register("guest")
        self.client.post(f'/api/challenges/{challenge["token"]}/join', headers=guest)
        host = self.login("host")
        started = self.client.post(
            f'/api/challenges/{challenge["token"]}/start', headers=host
        )
        self.assertEqual(started.status_code, 200, started.text)
        with self.client.app.state.session_factory() as db:
            c = db.get(Challenge, challenge["id"])
            c.starts_at = utcnow() - timedelta(seconds=60)
            c.deadline_at = utcnow() + timedelta(seconds=120)
            for row in db.scalars(
                select(PracticeRound).where(PracticeRound.challenge_id == c.id)
            ):
                row.started_at = c.starts_at
            db.commit()
        for username in ("host", "guest"):
            headers = self.login(username)
            payload = self.client.get(f'/api/challenges/{challenge["token"]}').json()[
                "challenge"
            ]
            row = payload["round"]
            response = self.client.post(
                f'/api/rounds/{row["id"]}/submit',
                headers=headers,
                json={"text": row["target"]},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(
                response.json()["stats"], response.json()["result"]["stats"]
            )
        final = self.client.get(f'/api/challenges/{challenge["token"]}').json()[
            "challenge"
        ]
        self.assertEqual(final["status"], "complete")
        self.assertIsNotNone(final["winner"])
        self.assertTrue(all(p.get("result") for p in final["participants"]))
        with self.client.app.state.session_factory() as db:
            self.assertEqual(db.get(Challenge, challenge["id"]).status, "complete")


if __name__ == "__main__":
    unittest.main()
