import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg

from noah.__main__ import Handler
from noah.db import connect
from noah.memory_query import query_memory
from noah.ollama import (
    OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable, OllamaUnsafeBinding,
    require_loopback_listener,
)
from noah.service import create_project, provision_user, read_memory, save_memory


class FakeModel:
    def __init__(self, *outputs):
        self.outputs = list(outputs)
        self.calls = []

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        output = self.outputs.pop(0)
        if isinstance(output, Exception):
            raise output
        return output


class ListenerGuardTests(unittest.TestCase):
    def test_network_facing_listener_is_rejected(self):
        result = type("Result", (), {"stdout": "TCP    0.0.0.0:11435  0.0.0.0:0  LISTENING  42"})()
        with patch("noah.ollama.subprocess.run", return_value=result):
            with self.assertRaises(OllamaUnsafeBinding):
                require_loopback_listener()

    def test_loopback_listener_is_accepted(self):
        result = type("Result", (), {"stdout": "TCP    127.0.0.1:11435  0.0.0.0:0  LISTENING  42"})()
        with patch("noah.ollama.subprocess.run", return_value=result):
            require_loopback_listener()


class MemoryQueryIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users = []
        cls.project_id = None
        cls.addClassCleanup(cls._cleanup)
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.users")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}") from error

        cls.owner_id, cls.owner_token = provision_user("NOAH slice 3 synthetic owner")
        cls.users.append(cls.owner_id)
        cls.reader_id, cls.reader_token = provision_user("NOAH slice 3 synthetic reader")
        cls.users.append(cls.reader_id)
        cls.outsider_id, cls.outsider_token = provision_user("NOAH slice 3 synthetic outsider")
        cls.users.append(cls.outsider_id)
        cls.project_id = create_project("NOAH slice 3 synthetic project", str(cls.owner_id))
        with connect() as db:
            db.execute("INSERT INTO noah.project_memberships (project_id, user_id, can_write) VALUES (%s, %s, false)",
                (cls.project_id, cls.reader_id))
        cls.personal_id = cls._save(cls.owner_token, "user", cls.owner_id,
            "Orion garden sprinkler schedule: every Tuesday at 07:00.")
        cls.korean_id = cls._save(cls.owner_token, "user", cls.owner_id,
            "오리온 정원 급수 계획: 매주 화요일 오전 7시.")
        cls.project_memory_id = cls._save(cls.owner_token, "project", cls.project_id,
            "Vega release checklist: sign off QA on Friday.")
        cls.outsider_private_id = cls._save(cls.outsider_token, "user", cls.outsider_id,
            "Orion garden sprinkler schedule: private outsider detail.")

    @classmethod
    def _save(cls, token, scope, target, content):
        payload = {"action": "save_memory", "scope": scope, "content": content}
        payload["owner_user_id" if scope == "user" else "project_id"] = str(target)
        status, result = save_memory(payload, token)
        if status != 201:
            raise AssertionError(f"Synthetic fixture save failed: {result['failure']['code']}")
        return result["evidence"]["memory_id"]

    @classmethod
    def _cleanup(cls):
        if not cls.users:
            return
        with connect() as db:
            for user_id in cls.users:
                db.execute("DELETE FROM noah.execution_records WHERE actor_user_id = %s", (user_id,))
                db.execute("DELETE FROM noah.memories WHERE created_by = %s", (user_id,))
                db.execute("DELETE FROM noah.tasks WHERE actor_user_id = %s", (user_id,))
            if cls.project_id:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id = %s", (cls.project_id,))
                db.execute("DELETE FROM noah.projects WHERE id = %s", (cls.project_id,))
            for user_id in cls.users:
                db.execute("DELETE FROM noah.api_tokens WHERE user_id = %s", (user_id,))
                db.execute("DELETE FROM noah.users WHERE id = %s", (user_id,))

    def test_authentication_precedes_model_and_invalid_input(self):
        model = FakeModel()
        status, result = query_memory({"question": "Find Orion"}, "invalid token", model=model)
        self.assertEqual((status, result["failure"]["code"]), (401, "UNAUTHENTICATED"))
        self.assertEqual(model.calls, [])
        status, result = query_memory({"question": ""}, self.owner_token, model=model)
        self.assertEqual((status, result["failure"]["code"]), (400, "INVALID_QUERY"))
        self.assertEqual(model.calls, [])

    def test_authorized_private_result_and_verified_quote(self):
        model = FakeModel(
            {"intent": "memory_read", "scope": "user", "query": "Orion sprinkler"},
            {"evidence": [{"memory_id": self.personal_id,
                "quote": "every Tuesday at 07:00"}]},
        )
        status, result = query_memory({"question": "Find my Orion sprinkler note"},
            self.owner_token, model=model)
        self.assertEqual(status, 200)
        self.assertEqual(result["outcome"], "grounded")
        self.assertEqual(result["evidence"][0]["memory_id"], self.personal_id)
        self.assertNotIn(self.outsider_private_id, json.dumps(result))
        self.assertNotIn(self.owner_token, json.dumps(model.calls))
        self.assertEqual(read_memory(self.personal_id, self.owner_token)[0], 200)

    def test_other_users_private_content_never_reaches_model(self):
        model = FakeModel({"intent": "memory_read", "scope": "user", "query": "Orion sprinkler"})
        status, result = query_memory({"question": "Find my Orion sprinkler note"},
            self.reader_token, model=model)
        self.assertEqual((status, result["outcome"]), (200, "no_match"))
        self.assertEqual(len(model.calls), 1)
        self.assertNotIn("private outsider detail", json.dumps(model.calls))

    def test_project_read_membership_and_outsider_denial(self):
        intent = {"intent": "memory_read", "scope": "project", "query": "Vega release"}
        evidence = {"evidence": [{"memory_id": self.project_memory_id,
            "quote": "sign off QA on Friday"}]}
        status, result = query_memory({"question": "Find the Vega release project note"},
            self.reader_token, model=FakeModel(intent, evidence))
        self.assertEqual((status, result["outcome"]), (200, "grounded"))
        self.assertEqual(result["evidence"][0]["memory_id"], self.project_memory_id)
        self.assertEqual(read_memory(self.project_memory_id, self.reader_token)[0], 200)
        status, result = query_memory({"question": "Find the Vega release project note"},
            self.outsider_token, model=FakeModel(intent))
        self.assertEqual((status, result["outcome"]), (200, "no_match"))
        self.assertEqual(read_memory(self.project_memory_id, self.outsider_token)[0], 404)

    def test_limit_is_reported_without_claiming_all_memories_examined(self):
        for number in range(6):
            self._save(self.owner_token, "user", self.owner_id,
                f"Synthetic Atlas limit note {number}")
        model = FakeModel(
            {"intent": "memory_read", "scope": "user", "query": "Atlas limit"},
            {"evidence": []},
        )
        status, result = query_memory({"question": "Find Atlas limit notes"},
            self.owner_token, model=model)
        self.assertEqual(status, 200)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["examined"], 5)
        self.assertEqual(result["outcome"], "insufficient_evidence")
        self.assertIn("추가 일치 메모", result["answer"])

    def test_unsupported_and_invalid_model_output(self):
        status, result = query_memory({"question": "Delete my notes"}, self.owner_token,
            model=FakeModel({"intent": "unsupported", "scope": "all", "query": ""}))
        self.assertEqual((status, result["failure"]["code"]), (422, "UNSUPPORTED_INTENT"))
        status, result = query_memory({"question": "Find Orion"}, self.owner_token,
            model=FakeModel({"intent": "memory_read", "scope": "user", "query": "invented"}))
        self.assertEqual((status, result["failure"]["code"]), (502, "MODEL_OUTPUT_INVALID"))

    def test_forged_or_modified_evidence_is_rejected(self):
        intent = {"intent": "memory_read", "scope": "user", "query": "Orion sprinkler"}
        for evidence in (
            {"evidence": [{"memory_id": str(uuid4()), "quote": "every Tuesday"}]},
            {"evidence": [{"memory_id": self.personal_id, "quote": "every Monday"}]},
        ):
            with self.subTest(evidence=evidence):
                status, result = query_memory({"question": "Find my Orion sprinkler note"},
                    self.owner_token, model=FakeModel(intent, evidence))
                self.assertEqual((status, result["failure"]["code"]), (502, "EVIDENCE_INVALID"))

    def test_distinct_model_and_database_failures(self):
        for error, code, http_status in (
            (OllamaUnavailable(), "OLLAMA_UNAVAILABLE", 503),
            (OllamaTimeout(), "OLLAMA_TIMEOUT", 504),
            (OllamaUnsafeBinding(), "OLLAMA_NOT_LOCAL", 503),
            (OllamaInvalidResponse(), "MODEL_OUTPUT_INVALID", 502),
        ):
            with self.subTest(code=code):
                status, result = query_memory({"question": "Find Orion"}, self.owner_token,
                    model=FakeModel(error))
                self.assertEqual((status, result["failure"]["code"]), (http_status, code))
                self.assertEqual(result["failure"]["recoverable"],
                    code in {"OLLAMA_UNAVAILABLE", "OLLAMA_TIMEOUT"})

        calls = 0
        def fail_after_authentication():
            nonlocal calls
            calls += 1
            if calls == 2:
                raise psycopg.OperationalError("synthetic database outage")
            return connect()
        status, result = query_memory({"question": "Find my Orion sprinkler note"},
            self.owner_token, connection_factory=fail_after_authentication,
            model=FakeModel({"intent": "memory_read", "scope": "user", "query": "Orion sprinkler"}))
        self.assertEqual((status, result["failure"]["code"]), (503, "DATABASE_UNAVAILABLE"))

    def test_http_route_and_existing_write_read_regression(self):
        model = FakeModel(
            {"intent": "memory_read", "scope": "user", "query": "Orion sprinkler"},
            {"evidence": [{"memory_id": self.personal_id, "quote": "every Tuesday at 07:00"}]},
        )
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with patch("noah.__main__.query_memory", side_effect=lambda payload, token:
                query_memory(payload, token, model=model)):
                request = Request(f"http://127.0.0.1:{server.server_port}/memories/query",
                    data=json.dumps({"question": "Find my Orion sprinkler note"}).encode(),
                    headers={"Authorization": f"Bearer {self.owner_token}",
                        "Content-Type": "application/json"}, method="POST")
                with urlopen(request, timeout=5) as response:
                    result = json.load(response)
                self.assertEqual(result["outcome"], "grounded")
                with self.assertRaises(HTTPError) as error:
                    urlopen(Request(request.full_url, data=request.data,
                        headers={"Content-Type": "application/json"}, method="POST"), timeout=5)
                self.assertEqual(error.exception.code, 401)
            self.assertEqual(read_memory(self.personal_id, self.owner_token)[0], 200)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    @unittest.skipUnless(os.environ.get("NOAH_RUN_OLLAMA_TESTS") == "1", "explicit local Ollama integration only")
    def test_real_local_model_with_synthetic_memory(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            for question, expected_id in (
                ("Find my personal note about the Orion garden sprinkler schedule", self.personal_id),
                ("내 개인 메모에서 오리온 정원 급수 계획을 찾아줘", self.korean_id),
            ):
                with self.subTest(question=question):
                    request = Request(f"http://127.0.0.1:{server.server_port}/memories/query",
                        data=json.dumps({"question": question}).encode(),
                        headers={"Authorization": f"Bearer {self.owner_token}",
                            "Content-Type": "application/json"}, method="POST")
                    with urlopen(request, timeout=120) as response:
                        self.assertEqual(response.status, 200)
                        result = json.load(response)
                    self.assertEqual(result["outcome"], "grounded")
                    self.assertEqual(result["evidence"][0]["memory_id"], expected_id)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
