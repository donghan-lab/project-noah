import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg

from noah.__main__ import Handler
from noah.db import ROOT, connect, initialize
from noah.service import create_project, provision_user, save_memory


class StorageFailureTests(unittest.TestCase):
    def test_unavailable_database_returns_failure_without_leaking_request(self):
        secret_content = "private test memory content"
        token = "private test token"

        def unavailable():
            raise psycopg.OperationalError("connection failed")

        status, result = save_memory({"action": "save_memory", "scope": "user", "content": secret_content},
            token, connection_factory=unavailable)
        self.assertEqual(status, 503)
        self.assertEqual(result["failure"]["code"], "DATABASE_UNAVAILABLE")
        self.assertFalse(result["failure"]["retryable"])
        audit = (ROOT / ".noah" / "failures.jsonl").read_text(encoding="utf-8")
        self.assertIn(result["request_id"], audit)
        self.assertNotIn(secret_content, audit)
        self.assertNotIn(token, audit)


class FirstSliceIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            initialize()
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}")
        cls.user_id, cls.token = provision_user("NOAH slice test owner")
        cls.other_id, cls.other_token = provision_user("NOAH slice test outsider")
        cls.project_id = create_project("NOAH slice test project", str(cls.user_id))
        cls.anonymous_execution_ids = []

    @classmethod
    def tearDownClass(cls):
        if not hasattr(cls, "user_id"):
            return
        with connect() as connection:
            users = (cls.user_id, cls.other_id)
            for execution_id in cls.anonymous_execution_ids:
                connection.execute("DELETE FROM noah.execution_records WHERE id = %s", (execution_id,))
            connection.execute("DELETE FROM noah.execution_records WHERE actor_user_id IN (%s, %s)", users)
            connection.execute("DELETE FROM noah.memories WHERE created_by IN (%s, %s)", users)
            connection.execute("DELETE FROM noah.tasks WHERE actor_user_id IN (%s, %s)", users)
            connection.execute("DELETE FROM noah.project_memberships WHERE project_id = %s", (cls.project_id,))
            connection.execute("DELETE FROM noah.projects WHERE id = %s", (cls.project_id,))
            connection.execute("DELETE FROM noah.api_tokens WHERE user_id IN (%s, %s)", users)
            connection.execute("DELETE FROM noah.users WHERE id IN (%s, %s)", users)

    def personal_request(self, content="Remember this explicit test note"):
        return {"action": "save_memory", "scope": "user", "owner_user_id": str(self.user_id), "content": content}

    def test_save_readback_and_durable_records(self):
        status, result = save_memory(self.personal_request(), self.token)
        self.assertEqual(status, 201)
        self.assertEqual(result["status"], "succeeded")
        memory_id = result["evidence"]["memory_id"]
        with connect() as connection:
            memory = connection.execute("SELECT content, provenance FROM noah.memories WHERE id = %s", (memory_id,)).fetchone()
            task = connection.execute("SELECT status, verification_status FROM noah.tasks WHERE id = %s", (result["task_id"],)).fetchone()
            execution = connection.execute("SELECT status, memory_id, verified_at FROM noah.execution_records WHERE id = %s", (result["execution_id"],)).fetchone()
        self.assertEqual(memory["content"], self.personal_request()["content"])
        self.assertEqual(memory["provenance"], "explicit_user_request")
        self.assertEqual((task["status"], task["verification_status"]), ("completed", "passed"))
        self.assertEqual(execution["status"], "succeeded")
        self.assertEqual(str(execution["memory_id"]), memory_id)
        self.assertIsNotNone(execution["verified_at"])

    def test_unauthorized_and_invalid_input_record_failures(self):
        for token, payload, expected_status, expected_code in (
            ("invalid token", self.personal_request(), 401, "UNAUTHENTICATED"),
            (self.other_token, self.personal_request(), 403, "SCOPE_DENIED"),
            (self.token, self.personal_request("   "), 400, "INVALID_CONTENT"),
            (self.other_token, {"action": "save_memory", "scope": "project", "project_id": str(self.project_id), "content": "no access"}, 403, "SCOPE_DENIED"),
        ):
            with self.subTest(expected_code=expected_code):
                status, result = save_memory(payload, token)
                self.assertEqual(status, expected_status)
                self.assertEqual(result["failure"]["code"], expected_code)
                self.assertIsNone(result["task_id"])
                if expected_code == "UNAUTHENTICATED":
                    self.anonymous_execution_ids.append(result["execution_id"])
                with connect() as connection:
                    record = connection.execute("SELECT status, failure_category, failure_code FROM noah.execution_records WHERE id = %s", (result["execution_id"],)).fetchone()
                self.assertEqual(record["status"], "failed")
                self.assertEqual(record["failure_code"], expected_code)

    def test_database_write_failure_rolls_back_memory_and_marks_task_failed(self):
        def fail_insert(connection, memory_id, owner, project, scope, content, _actor):
            # A real foreign-key violation aborts the PostgreSQL write transaction.
            connection.execute(
                """INSERT INTO noah.memories
                (id, owner_user_id, project_id, scope, content, created_by)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (memory_id, owner, project, scope, content, uuid4()),
            )

        status, result = save_memory(self.personal_request("must roll back"), self.token, insert_memory=fail_insert)
        self.assertEqual(status, 500)
        self.assertEqual(result["failure"]["code"], "DATABASE_WRITE_FAILED")
        with connect() as connection:
            task = connection.execute("SELECT status, verification_status FROM noah.tasks WHERE id = %s", (result["task_id"],)).fetchone()
            execution = connection.execute("SELECT status, failure_code, memory_id FROM noah.execution_records WHERE id = %s", (result["execution_id"],)).fetchone()
            memory_count = connection.execute("SELECT count(*) AS n FROM noah.memories WHERE content = %s AND created_by = %s", ("must roll back", self.user_id)).fetchone()["n"]
        self.assertEqual((task["status"], task["verification_status"]), ("failed", "failed"))
        self.assertEqual((execution["status"], execution["failure_code"], execution["memory_id"]), ("failed", "DATABASE_WRITE_FAILED", None))
        self.assertEqual(memory_count, 0)

    def test_project_permission_and_server_restart_persistence(self):
        payload = {"action": "save_memory", "scope": "project", "project_id": str(self.project_id), "content": "Project note persists"}
        first = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=first.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f"http://127.0.0.1:{first.server_port}/memories", data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, method="POST")
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 201)
                memory_id = json.load(response)["evidence"]["memory_id"]
        finally:
            first.shutdown()
            first.server_close()
            thread.join(timeout=5)

        second = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=second.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{second.server_port}/memories/{memory_id}"
            with urlopen(Request(url, headers={"Authorization": f"Bearer {self.token}"}), timeout=5) as response:
                self.assertEqual(json.load(response)["memory"]["content"], payload["content"])
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(url, headers={"Authorization": f"Bearer {self.other_token}"}), timeout=5)
            self.assertEqual(error.exception.code, 404)
        finally:
            second.shutdown()
            second.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
