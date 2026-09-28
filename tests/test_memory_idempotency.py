"""Fourth-slice checks against test-owned rows in the existing PostgreSQL."""

import json
import hashlib
import socket
import subprocess
import sys
import threading
import time
import unittest
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg

from noah.db import ROOT, connect, initialize
from noah.service import provision_user, save_memory


class MemoryIdempotencyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            initialize()
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}") from error
        cls.user_id, cls.token = provision_user("NOAH slice 4 synthetic owner")
        cls.other_id, cls.other_token = provision_user("NOAH slice 4 synthetic outsider")
        cls.anonymous_execution_ids = []
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _cleanup(cls):
        with connect() as db:
            users = (cls.user_id, cls.other_id)
            for execution_id in cls.anonymous_execution_ids:
                db.execute("DELETE FROM noah.execution_records WHERE id = %s", (execution_id,))
            db.execute("DELETE FROM noah.memory_write_requests WHERE actor_user_id IN (%s, %s)", users)
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id IN (%s, %s)", users)
            db.execute("DELETE FROM noah.memories WHERE created_by IN (%s, %s)", users)
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id IN (%s, %s)", users)
            db.execute("DELETE FROM noah.api_tokens WHERE user_id IN (%s, %s)", users)
            db.execute("DELETE FROM noah.users WHERE id IN (%s, %s)", users)

    def payload(self, content="synthetic idempotency note", owner=None):
        return {"action": "save_memory", "scope": "user", "owner_user_id": str(owner or self.user_id),
            "content": content}

    def _counts(self, content, key):
        with connect() as db:
            return (
                db.execute("SELECT count(*) n FROM noah.memories WHERE created_by = %s AND content = %s",
                    (self.user_id, content)).fetchone()["n"],
                db.execute("SELECT count(*) n FROM noah.memory_write_requests WHERE actor_user_id = %s AND key_digest = %s",
                    (self.user_id, hashlib.sha256(key.encode("ascii")).hexdigest())).fetchone()["n"],
            )

    def test_replay_conflict_and_distinct_keys(self):
        content = "synthetic replay " + str(uuid4())
        payload = self.payload(content)
        key = str(uuid4())
        first_status, first = save_memory(payload, self.token, idempotency_key=key)
        self.assertEqual(first_status, 201)
        second_status, second = save_memory(payload, self.token, idempotency_key=key)
        self.assertEqual(second_status, 200)
        self.assertTrue(second["replayed"])
        for name in ("request_id", "task_id", "execution_id"):
            self.assertEqual(first[name], second[name])
        self.assertEqual(first["evidence"], second["evidence"])
        self.assertEqual(self._counts(content, key), (1, 1))

        conflict_status, conflict = save_memory(self.payload(content + " changed"), self.token,
            idempotency_key=key)
        self.assertEqual((conflict_status, conflict["failure"]["code"]), (409, "IDEMPOTENCY_CONFLICT"))
        self.assertEqual(self._counts(content, key), (1, 1))
        self.assertEqual(self._counts(content + " changed", key)[0], 0)

        different_status, different = save_memory(payload, self.token, idempotency_key=str(uuid4()))
        self.assertEqual(different_status, 201)
        self.assertNotEqual(first["evidence"]["memory_id"], different["evidence"]["memory_id"])
        self.assertEqual(self._counts(content, key), (2, 1))

    def test_key_is_scoped_to_authenticated_user_and_bad_keys_rejected(self):
        key = str(uuid4())
        self.assertEqual(save_memory(self.payload(), self.token, idempotency_key=key)[0], 201)
        other = self.payload("other synthetic note", owner=self.other_id)
        self.assertEqual(save_memory(other, self.other_token, idempotency_key=key)[0], 201)
        denied_status, denied = save_memory(self.payload(), self.other_token, idempotency_key=key)
        self.assertEqual((denied_status, denied["failure"]["code"]), (403, "SCOPE_DENIED"))
        anonymous_status, anonymous = save_memory(self.payload(), "invalid", idempotency_key=key)
        self.assertEqual((anonymous_status, anonymous["failure"]["code"]), (401, "UNAUTHENTICATED"))
        self.anonymous_execution_ids.append(anonymous["execution_id"])
        invalid_status, invalid = save_memory(self.payload(), self.token, idempotency_key="bad key")
        self.assertEqual((invalid_status, invalid["failure"]["code"]), (400, "INVALID_IDEMPOTENCY_KEY"))

    def test_concurrent_same_key_does_not_start_second_write(self):
        content = "synthetic concurrent " + str(uuid4())
        payload = self.payload(content)
        key = str(uuid4())
        entered, release = threading.Event(), threading.Event()
        output = {}

        def slow_insert(db, memory_id, owner, project, scope, value, actor):
            entered.set()
            if not release.wait(10):
                raise AssertionError("Timed out waiting for the second request")
            db.execute("""INSERT INTO noah.memories
                (id, owner_user_id, project_id, scope, content, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (memory_id, owner, project, scope, value, actor))

        worker = threading.Thread(target=lambda: output.setdefault("first",
            save_memory(payload, self.token, idempotency_key=key, insert_memory=slow_insert)))
        worker.start()
        self.assertTrue(entered.wait(5))
        try:
            pending_status, pending = save_memory(payload, self.token, idempotency_key=key)
            self.assertEqual((pending_status, pending["status"]), (202, "pending"))
            self.assertEqual(self._counts(content, key), (0, 1))
        finally:
            release.set()
            worker.join(10)
        self.assertFalse(worker.is_alive())
        self.assertEqual(output["first"][0], 201)
        self.assertEqual(pending["task_id"], output["first"][1]["task_id"])
        self.assertEqual(save_memory(payload, self.token, idempotency_key=key)[0], 200)
        self.assertEqual(self._counts(content, key), (1, 1))

    def test_failed_write_rolls_back_and_failure_replays(self):
        content = "synthetic rollback " + str(uuid4())
        payload, key = self.payload(content), str(uuid4())

        def fail_insert(db, memory_id, owner, project, scope, value, actor):
            db.execute("""INSERT INTO noah.memories
                (id, owner_user_id, project_id, scope, content, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (memory_id, owner, uuid4(), "project", value, actor))

        status, result = save_memory(payload, self.token, idempotency_key=key, insert_memory=fail_insert)
        self.assertEqual((status, result["failure"]["code"]), (500, "DATABASE_WRITE_FAILED"))
        self.assertEqual(self._counts(content, key), (0, 1))
        with connect() as db:
            task = db.execute("SELECT status, verification_status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            execution = db.execute("SELECT status, memory_id FROM noah.execution_records WHERE id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual((task["status"], task["verification_status"]), ("failed", "failed"))
        self.assertEqual((execution["status"], execution["memory_id"]), ("failed", None))
        replay_status, replay = save_memory(payload, self.token, idempotency_key=key)
        self.assertEqual((replay_status, replay["failure"]["code"]), (500, "DATABASE_WRITE_FAILED"))
        self.assertEqual(replay["task_id"], result["task_id"])
        self.assertEqual(self._counts(content, key), (0, 1))

    def test_lost_commit_acknowledgement_never_overwrites_success(self):
        content, key = "synthetic uncertain commit " + str(uuid4()), str(uuid4())

        class LostAcknowledgement:
            def __init__(self):
                self.real = connect()
                self.commits = 0

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return self.real.__exit__(*args)

            def execute(self, *args):
                return self.real.execute(*args)

            def rollback(self):
                return self.real.rollback()

            def commit(self):
                self.commits += 1
                self.real.commit()
                if self.commits == 2:
                    raise psycopg.OperationalError("simulated lost commit acknowledgement")

        status, result = save_memory(self.payload(content), self.token,
            connection_factory=LostAcknowledgement, idempotency_key=key)
        self.assertEqual((status, result["failure"]["code"]), (503, "WRITE_OUTCOME_UNKNOWN"))
        self.assertTrue(result["failure"]["retryable"])
        audit = (ROOT / ".noah" / "failures.jsonl").read_text(encoding="utf-8").splitlines()
        uncertain = [json.loads(line) for line in audit if result["request_id"] in line]
        self.assertEqual([(entry["status"], entry["code"]) for entry in uncertain],
            [("unknown", "WRITE_OUTCOME_UNKNOWN")])
        replay_status, replay = save_memory(self.payload(content), self.token, idempotency_key=key)
        self.assertEqual((replay_status, replay["status"]), (200, "succeeded"))
        self.assertEqual(result["task_id"], replay["task_id"])
        self.assertEqual(self._counts(content, key), (1, 1))
        with connect() as db:
            task = db.execute("SELECT status, verification_status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            execution = db.execute("SELECT status, memory_id FROM noah.execution_records WHERE id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual((task["status"], task["verification_status"]), ("completed", "passed"))
        self.assertEqual((execution["status"], str(execution["memory_id"])),
            ("succeeded", replay["evidence"]["memory_id"]))

    def test_http_replay_after_real_server_process_restart(self):
        content, key = "synthetic process restart " + str(uuid4()), str(uuid4())
        payload = self.payload(content)
        with socket.socket() as listener:
            listener.bind(("127.0.0.1", 0))
            port = listener.getsockname()[1]

        def serve_once():
            server = subprocess.Popen([sys.executable, "-m", "noah", "serve", "--port", str(port)],
                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for _ in range(50):
                if server.poll() is not None:
                    self.fail("NOAH server process exited before accepting requests")
                try:
                    with socket.create_connection(("127.0.0.1", port), timeout=0.1):
                        return server
                except OSError:
                    time.sleep(0.1)
            server.terminate()
            self.fail("NOAH server process did not start")

        def send():
            request = Request(f"http://127.0.0.1:{port}/memories", data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json",
                    "Idempotency-Key": key}, method="POST")
            with urlopen(request, timeout=5) as response:
                return response.status, json.load(response)

        server = serve_once()
        try:
            first_status, first = send()
        finally:
            server.terminate()
            server.wait(timeout=5)
        server = serve_once()
        try:
            second_status, second = send()
        finally:
            server.terminate()
            server.wait(timeout=5)
        self.assertEqual((first_status, second_status), (201, 200))
        self.assertEqual(first["evidence"], second["evidence"])
        self.assertEqual(self._counts(content, key), (1, 1))


if __name__ == "__main__":
    unittest.main()
