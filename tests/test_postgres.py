"""Optional real-PostgreSQL tests. Never accepts a remote/production database."""

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import os
import threading
import unittest
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.engine import make_url

from typing_app.api import create_app
from typing_app.config import Settings
from typing_app.models import (
    Attempt,
    Challenge,
    ChallengeParticipant,
    Follow,
    Message,
    PracticeRound,
    utcnow,
)


@unittest.skipUnless(
    os.getenv("TEST_POSTGRES_URL"),
    "Set TEST_POSTGRES_URL to a dedicated local mt_test_* database",
)
class PostgreSQLIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ["TEST_POSTGRES_URL"]
        parsed = make_url(url)
        if parsed.host not in {"127.0.0.1", "localhost"} or not (
            parsed.database or ""
        ).startswith("mt_test_"):
            raise RuntimeError(
                "PostgreSQL tests refuse nonlocal or non-mt_test_ databases"
            )
        cls.settings = Settings(database_url=url, cookie_secure=False, testing=True)
        cls.app = create_app(cls.settings)
        cls.client = TestClient(cls.app)
        cls.client.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls.client.__exit__(None, None, None)

    def register(self):
        username = "u_" + uuid4().hex[:12]
        self.client.cookies.clear()
        response = self.client.post(
            "/api/auth/register",
            json={"username": username, "password": "postgres-test-only-123"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        headers = {
            "X-CSRF-Token": response.json()["csrf"],
            "Cookie": "mt_session=" + self.client.cookies.get("mt_session"),
        }
        self.client.cookies.clear()
        return username, headers

    def request(self, path, headers, body=None):
        client = TestClient(self.app)
        try:
            return (
                client.post(path, headers=headers, json=body)
                if body is not None
                else client.post(path, headers=headers)
            )
        finally:
            client.close()

    def create_challenge(self, headers, maximum=2):
        response = self.request(
            "/api/challenges",
            headers,
            {
                "game": "repeat",
                "difficulty": "easy",
                "language": "en",
                "count": 1,
                "visibility": "private",
                "max_players": maximum,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["challenge"]

    def test_concurrent_case_insensitive_registration(self):
        username = "race_" + uuid4().hex[:10]

        def register(value):
            return self.request(
                "/api/auth/register",
                {},
                {"username": value, "password": "postgres-test-only-123"},
            ).status_code

        with ThreadPoolExecutor(2) as pool:
            statuses = list(pool.map(register, (username, username.upper())))
        self.assertEqual(sorted(statuses), [200, 409])

    def test_duplicate_submission_is_atomic(self):
        _, headers = self.register()
        response = self.request(
            "/api/rounds",
            headers,
            {"game": "repeat", "difficulty": "easy", "language": "en", "count": 1},
        )
        row = response.json()["round"]
        with self.app.state.session_factory() as db:
            db.get(PracticeRound, row["id"]).started_at = utcnow() - timedelta(
                seconds=60
            )
            db.commit()
        with ThreadPoolExecutor(2) as pool:
            responses = list(
                pool.map(
                    lambda _: self.request(
                        f'/api/rounds/{row["id"]}/submit',
                        headers,
                        {"text": row["target"]},
                    ),
                    range(2),
                )
            )
        self.assertEqual(sorted(r.status_code for r in responses), [200, 409])
        with self.app.state.session_factory() as db:
            self.assertEqual(
                db.scalar(
                    select(func.count())
                    .select_from(Attempt)
                    .where(Attempt.round_id == row["id"])
                ),
                1,
            )

    def test_concurrent_join_cannot_overfill(self):
        _, host = self.register()
        challenge = self.create_challenge(host)
        players = [self.register()[1] for _ in range(2)]
        with ThreadPoolExecutor(2) as pool:
            statuses = list(
                pool.map(
                    lambda headers: self.request(
                        f'/api/challenges/{challenge["token"]}/join', headers
                    ).status_code,
                    players,
                )
            )
        self.assertEqual(sorted(statuses), [200, 409])
        with self.app.state.session_factory() as db:
            self.assertEqual(
                db.scalar(
                    select(func.count())
                    .select_from(ChallengeParticipant)
                    .where(ChallengeParticipant.challenge_id == challenge["id"])
                ),
                2,
            )

    def test_concurrent_start_creates_one_round_per_member(self):
        _, host = self.register()
        challenge = self.create_challenge(host)
        _, guest = self.register()
        self.request(f'/api/challenges/{challenge["token"]}/join', guest)
        with ThreadPoolExecutor(2) as pool:
            statuses = list(
                pool.map(
                    lambda _: self.request(
                        f'/api/challenges/{challenge["token"]}/start', host
                    ).status_code,
                    range(2),
                )
            )
        self.assertEqual(sorted(statuses), [200, 409])
        with self.app.state.session_factory() as db:
            self.assertEqual(
                db.scalar(
                    select(func.count())
                    .select_from(PracticeRound)
                    .where(PracticeRound.challenge_id == challenge["id"])
                ),
                2,
            )

    def test_join_start_race_never_leaves_member_without_round(self):
        _, host = self.register()
        challenge = self.create_challenge(host, 3)
        _, guest = self.register()
        self.request(f'/api/challenges/{challenge["token"]}/join', guest)
        _, late = self.register()
        actions = [("start", host), ("join", late)]
        with ThreadPoolExecutor(2) as pool:
            responses = list(
                pool.map(
                    lambda action: self.request(
                        f'/api/challenges/{challenge["token"]}/{action[0]}', action[1]
                    ),
                    actions,
                )
            )
        self.assertEqual(responses[0].status_code, 200)
        self.assertIn(responses[1].status_code, (200, 409))
        with self.app.state.session_factory() as db:
            participants = db.scalars(
                select(ChallengeParticipant).where(
                    ChallengeParticipant.challenge_id == challenge["id"]
                )
            ).all()
            self.assertTrue(all(p.round_id for p in participants))
            self.assertEqual(
                len(participants),
                db.scalar(
                    select(func.count())
                    .select_from(PracticeRound)
                    .where(PracticeRound.challenge_id == challenge["id"])
                ),
            )

    def test_account_persists_across_app_restart(self):
        username, _ = self.register()
        other = create_app(self.settings)
        with TestClient(other) as client:
            response = client.post(
                "/api/auth/login",
                json={"username": username, "password": "postgres-test-only-123"},
            )
            self.assertEqual(response.status_code, 200, response.text)
            self.assertEqual(client.get("/api/me").json()["user"]["username"], username)

    def test_block_commits_before_send_and_follow_cannot_be_resurrected(self):
        sender_name, sender = self.register()
        recipient_name, recipient = self.register()
        followed = self.request(f"/api/users/{recipient_name}/follow", sender)
        self.assertEqual(followed.status_code, 200, followed.text)

        blocked = self.request(f"/api/users/{sender_name}/block", recipient)
        self.assertEqual(blocked.status_code, 200, blocked.text)
        rejected = self.request(
            f"/api/messages/{recipient_name}", sender, {"body": "blocked"}
        )
        self.assertEqual(rejected.status_code, 403, rejected.text)
        resurrected = self.request(f"/api/users/{recipient_name}/follow", sender)
        self.assertEqual(resurrected.status_code, 403, resurrected.text)
        with self.app.state.session_factory() as db:
            self.assertIsNone(
                db.get(
                    Follow,
                    (self._user_id(db, sender_name), self._user_id(db, recipient_name)),
                )
            )

    def test_sender_blocking_recipient_hides_existing_unread_message(self):
        sender_name, sender = self.register()
        recipient_name, recipient = self.register()
        sent = self.request(
            f"/api/messages/{recipient_name}", sender, {"body": "unread before block"}
        )
        self.assertEqual(sent.status_code, 200, sent.text)
        blocked = self.request(f"/api/users/{recipient_name}/block", sender)
        self.assertEqual(blocked.status_code, 200, blocked.text)

        client = TestClient(self.app)
        try:
            session = client.get("/api/session", headers=recipient).json()
            threads = client.get("/api/messages/threads", headers=recipient).json()
        finally:
            client.close()
        self.assertEqual(session["unread_messages"], 0)
        self.assertEqual(threads["threads"], [])

    def test_send_holds_pair_lock_before_concurrent_block(self):
        sender_name, sender = self.register()
        recipient_name, recipient = self.register()
        send_insert_entered = threading.Event()
        allow_send_insert = threading.Event()
        block_lock_attempted = threading.Event()

        def pause_send_and_observe_block(
            conn, cursor, statement, params, context, executemany
        ):
            if "insert into mt_messages" in statement.lower():
                send_insert_entered.set()
                if not allow_send_insert.wait(15):
                    raise TimeoutError("Timed out waiting to release message insert")
            if send_insert_entered.is_set() and "FOR UPDATE" in statement.upper():
                block_lock_attempted.set()

        event.listen(
            self.app.state.engine, "before_cursor_execute", pause_send_and_observe_block
        )
        try:
            with ThreadPoolExecutor(max_workers=2) as pool:

                def send_first():
                    return self.request(
                        f"/api/messages/{recipient_name}",
                        sender,
                        {"body": "committed before block"},
                    )

                def block_after_lock_contends():
                    return self.request(f"/api/users/{sender_name}/block", recipient)

                send_future = pool.submit(send_first)
                self.assertTrue(
                    send_insert_entered.wait(10), "send did not reach message insert"
                )
                block_future = pool.submit(block_after_lock_contends)
                self.assertTrue(
                    block_lock_attempted.wait(10), "block did not contend on pair lock"
                )
                allow_send_insert.set()
                sent = send_future.result(timeout=15)
                blocked = block_future.result(timeout=15)
        finally:
            allow_send_insert.set()
            event.remove(
                self.app.state.engine,
                "before_cursor_execute",
                pause_send_and_observe_block,
            )

        self.assertEqual(sent.status_code, 200, sent.text)
        self.assertEqual(blocked.status_code, 200, blocked.text)
        rejected = self.request(
            f"/api/messages/{recipient_name}", sender, {"body": "after block"}
        )
        self.assertEqual(rejected.status_code, 403, rejected.text)
        with self.app.state.session_factory() as db:
            message = db.scalar(
                select(Message).where(
                    Message.sender_id == self._user_id(db, sender_name),
                    Message.recipient_id == self._user_id(db, recipient_name),
                )
            )
            self.assertIsNotNone(message)
            self.assertIsNone(message.read_at)
        session_client = TestClient(self.app)
        try:
            session = session_client.get("/api/session", headers=recipient).json()
        finally:
            session_client.close()
        self.assertEqual(session["unread_messages"], 0)

    @staticmethod
    def _user_id(db, username):
        from typing_app.models import User

        return db.scalar(select(User.id).where(User.username == username))


if __name__ == "__main__":
    unittest.main()
