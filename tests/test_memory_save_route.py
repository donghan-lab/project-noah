"""M13 explicit user-memory routing against synthetic PostgreSQL records."""

import json
import http.client
import hashlib
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg

from noah.__main__ import Handler
from noah.capability_route import (NO_ACTION, SAVE_ROUTE, SAVE_MODEL_SCHEMA,
                                   _save_messages, route_read_request)
from noah.db import connect
from noah.ollama import (OllamaClient, OllamaTimeout, OllamaUnavailable,
                        OllamaUnsafeBinding)
from noah.routing_audit import AuditWriteError, RoutingAudit
from noah.service import provision_user, save_memory


FAKE_SETTINGS = lambda: {"POSTGRES_PASSWORD": "synthetic-password-not-real"}
CONTENT = "M13 public synthetic memory: the test animal is an otter."
QUESTION = "내가 명시한 테스트 메모를 저장해줘."


class RouterModel:
    def __init__(self, proposal):
        self.proposal, self.calls = proposal, []

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        if isinstance(self.proposal, Exception):
            raise self.proposal
        return self.proposal


class FaultAudit(RoutingAudit):
    def __init__(self, factory, phase, after_commit=False, uncertain=False):
        super().__init__(factory)
        self.phase, self.after_commit, self.uncertain = phase, after_commit, uncertain

    def _fault(self, phase, action):
        if self.phase == phase and not self.after_commit:
            raise AuditWriteError(self.uncertain)
        action()
        if self.phase == phase and self.after_commit:
            raise AuditWriteError(self.uncertain)

    def reserve(self, *args):
        self._fault("reserve", lambda: super(FaultAudit, self).reserve(*args))

    def route_validated(self, *args):
        self._fault("route_validated", lambda: super(FaultAudit, self).route_validated(*args))

    def dispatch_prepared(self, *args):
        self._fault("dispatch_prepared", lambda: super(FaultAudit, self).dispatch_prepared(*args))

    def observed(self, *args, **kwargs):
        self._fault("observed", lambda: super(FaultAudit, self).observed(*args, **kwargs))


class MemorySaveRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.routing_audit")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"M13 PostgreSQL unavailable: {type(error).__name__}") from error
        cls.user, cls.token = provision_user("NOAH M13 synthetic actor")
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _cleanup(cls):
        with connect() as db:
            db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.memory_write_requests WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.memories WHERE owner_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.users WHERE id=%s", (cls.user,))

    def payload(self, content=CONTENT):
        return {"question": QUESTION, "memory_save": {"content": content}}

    def counts(self):
        with connect() as db:
            return {table: db.execute(f"SELECT count(*) AS n FROM noah.{table} WHERE {field}=%s",
                (self.user,)).fetchone()["n"] for table, field in (
                ("routing_audit", "actor_user_id"), ("memories", "owner_user_id"),
                ("tasks", "actor_user_id"), ("execution_records", "actor_user_id"),
                ("memory_write_requests", "actor_user_id"))}

    def route(self, payload=None, key=None, proposal=None, **kwargs):
        model = kwargs.pop("model", None)
        return route_read_request(self.payload() if payload is None else payload, self.token,
            idempotency_key=key if key is not None else f"m13-{uuid4().hex}",
            model=model if model is not None else
                  RouterModel({"route": SAVE_ROUTE} if proposal is None else proposal),
            settings_provider=FAKE_SETTINGS, **kwargs)

    def audit_row(self, router_id):
        with connect() as db:
            return db.execute("SELECT * FROM noah.routing_audit WHERE router_id=%s",
                              (router_id,)).fetchone()

    def test_first_write_replay_conflict_and_correlation(self):
        before = self.counts()
        key = f"m13-{uuid4().hex}"
        calls = []
        def counted_save(*args, **kwargs):
            calls.append(1)
            return save_memory(*args, **kwargs)
        status, body = self.route(key=key, write_runner=counted_save)
        self.assertEqual(calls, [1])
        self.assertEqual((status, body["status"], body["routing"]["audit_status"]),
                         (201, "succeeded", "recorded"))
        result = body["result"]
        with connect() as db:
            memory = db.execute("SELECT content,scope,owner_user_id FROM noah.memories WHERE id=%s",
                                (UUID(result["evidence"]["memory_id"]),)).fetchone()
        self.assertEqual((memory["content"], memory["scope"], memory["owner_user_id"]),
                         (CONTENT, "user", self.user))
        row = self.audit_row(body["router_id"])
        self.assertEqual((row["stage"], row["validated_route"], row["delegate_capability"],
                          row["observation_class"], row["delegate_request_id"],
                          row["delegate_task_id"], row["delegate_execution_id"]),
                         ("observed", SAVE_ROUTE, SAVE_ROUTE, "delegate_returned",
                          UUID(result["request_id"]), UUID(result["task_id"]),
                          UUID(result["execution_id"])))
        audit_text = json.dumps({name: str(value) for name, value in row.items()})
        for private_value in (CONTENT, QUESTION, key, hashlib.sha256(key.encode()).hexdigest(),
                              self.token, FAKE_SETTINGS()["POSTGRES_PASSWORD"]):
            self.assertNotIn(private_value, audit_text)
        after = self.counts()
        self.assertEqual({name: after[name] - before[name] for name in before},
                         {"routing_audit": 1, "memories": 1, "tasks": 1,
                          "execution_records": 1, "memory_write_requests": 1})

        status, replay = self.route(key=key)
        self.assertEqual((status, replay["result"]["replayed"]), (200, True))
        for name in ("request_id", "task_id", "execution_id"):
            self.assertEqual(replay["result"][name], result[name])
        self.assertEqual(replay["result"]["evidence"], result["evidence"])
        replay_row = self.audit_row(replay["router_id"])
        self.assertEqual(replay_row["delegate_execution_id"], UUID(result["execution_id"]))
        self.assertNotEqual(replay["router_id"], body["router_id"])
        self.assertEqual(self.counts()["memories"], after["memories"])

        status, conflict = self.route(key=key, payload=self.payload("different synthetic note"))
        self.assertEqual((status, conflict["result"]["failure"]["code"]),
                         (409, "IDEMPOTENCY_CONFLICT"))
        conflict_row = self.audit_row(conflict["router_id"])
        self.assertEqual(conflict_row["delegate_request_id"], UUID(conflict["result"]["request_id"]))
        self.assertIsNone(conflict_row["delegate_task_id"])
        self.assertIsNone(conflict_row["delegate_execution_id"])
        self.assertEqual(self.counts()["memories"], after["memories"])
        self.assertEqual(self.counts()["memory_write_requests"], after["memory_write_requests"])

        status, fresh = self.route(key=f"m13-{uuid4().hex}")
        self.assertEqual(status, 201)
        self.assertNotEqual(fresh["result"]["evidence"]["memory_id"],
                            result["evidence"]["memory_id"])
        self.assertEqual(self.counts()["memories"], after["memories"] + 1)

    def test_preflight_never_reserves_audit_or_calls_model(self):
        before = self.counts()
        cases = [
            (self.payload(), "bad-token", "UNAUTHENTICATED", "valid"),
            ({**self.payload(), "project_id": str(uuid4())}, self.token, "INVALID_REQUEST", "valid"),
            ({"question": QUESTION, "memory_save": {"content": " "}}, self.token, "INVALID_CONTENT", "valid"),
            ({"question": QUESTION, "memory_save": {"content": CONTENT, "scope": "project"}},
             self.token, "INVALID_REQUEST", "valid"),
            ({"question": "\ud800", "memory_save": {"content": CONTENT}},
             self.token, "INVALID_REQUEST", "valid"),
            (self.payload(), self.token, "IDEMPOTENCY_KEY_REQUIRED", None),
            (self.payload(), self.token, "INVALID_IDEMPOTENCY_KEY", "invalid key"),
            ({"question": self.token, "memory_save": {"content": CONTENT}},
             self.token, "SENSITIVE_CONTEXT_REJECTED", "valid"),
        ]
        for payload, token, code, key in cases:
            with self.subTest(code=code):
                model = RouterModel({"route": SAVE_ROUTE})
                status, body = route_read_request(payload, token, idempotency_key=key,
                    model=model, settings_provider=FAKE_SETTINGS)
                self.assertEqual(body["failure"]["code"], code)
                self.assertEqual(model.calls, [])
                self.assertNotIn("router_id", body)
                self.assertEqual(self.counts(), before)

    def test_model_sees_only_question_marker_and_two_routes(self):
        model = RouterModel({"route": NO_ACTION})
        before = self.counts()
        key = f"m13-{uuid4().hex}"
        status, body = self.route(model=model, key=key,
                                  payload=self.payload("private synthetic marker 53c9"))
        self.assertEqual((status, body["routing"]["outcome"]), (200, NO_ACTION))
        messages, schema, _ = model.calls[0]
        serialized = json.dumps(messages, ensure_ascii=False)
        self.assertIn(QUESTION, serialized)
        self.assertIn("memory_save_present", serialized)
        self.assertNotIn("private synthetic marker 53c9", serialized)
        self.assertNotIn(key, serialized)
        self.assertNotIn(hashlib.sha256(key.encode()).hexdigest(), serialized)
        self.assertEqual(schema, SAVE_MODEL_SCHEMA)
        self.assertEqual(schema["properties"]["route"]["enum"], ["memory.save", "no_action"])
        after = self.counts()
        self.assertEqual(after["routing_audit"], before["routing_audit"] + 1)
        for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
            self.assertEqual(after[name], before[name])

    def test_model_stage_failure_is_audited_without_write(self):
        for proposal, code in ((OllamaUnsafeBinding(), "ROUTING_OLLAMA_NOT_LOCAL"),
                               (OllamaUnavailable(), "ROUTING_OLLAMA_UNAVAILABLE"),
                               (OllamaTimeout(), "ROUTING_OLLAMA_TIMEOUT"),
                               ({"route": "memory.query"}, "ROUTING_MODEL_OUTPUT_INVALID"),
                               ({"route": SAVE_ROUTE, "content": CONTENT}, "ROUTING_MODEL_OUTPUT_INVALID")):
            with self.subTest(code=code):
                before = self.counts()
                called = []
                status, body = self.route(proposal=proposal,
                    write_runner=lambda *args, **kwargs: called.append((args, kwargs)))
                self.assertEqual(body["failure"]["code"], code)
                self.assertEqual(called, [])
                row = self.audit_row(body["router_id"])
                self.assertEqual((row["stage"], row["observation_class"]),
                                 ("observed", "routing_failed"))
                after = self.counts()
                self.assertEqual(after["routing_audit"], before["routing_audit"] + 1)
                for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
                    self.assertEqual(after[name], before[name])

    def test_predelegate_audit_failure_never_calls_write(self):
        for phase in ("reserve", "route_validated", "dispatch_prepared"):
            for after_commit in (False, True):
                with self.subTest(phase=phase, after_commit=after_commit):
                    called = []
                    before = self.counts()
                    status, body = self.route(audit=FaultAudit(connect, phase,
                        after_commit=after_commit, uncertain=after_commit),
                        write_runner=lambda *args, **kwargs: called.append((args, kwargs)))
                    self.assertEqual(status, 503)
                    self.assertEqual(called, [])
                    after = self.counts()
                    for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
                        self.assertEqual(after[name], before[name])

    def test_final_audit_failure_preserves_write_result(self):
        before = self.counts()
        status, body = self.route(audit=FaultAudit(connect, "observed"))
        self.assertEqual((status, body["result"]["status"],
                          body["routing"]["audit_status"]), (201, "succeeded", "unconfirmed"))
        after = self.counts()
        self.assertEqual((after["memories"] - before["memories"],
                          after["tasks"] - before["tasks"],
                          after["execution_records"] - before["execution_records"]),
                         (1, 1, 1))
        self.assertEqual(self.audit_row(body["router_id"])["stage"], "dispatch_prepared")

    def test_revoked_token_after_model_prevents_write(self):
        class RevokingModel(RouterModel):
            def complete(inner_self, messages, schema, max_tokens):
                with connect() as db:
                    db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s",
                               (self.user,))
                return super().complete(messages, schema, max_tokens)

        before = self.counts()
        called = []
        try:
            status, body = self.route(model=RevokingModel({"route": SAVE_ROUTE}),
                write_runner=lambda *args, **kwargs: called.append((args, kwargs)))
            self.assertEqual((status, body["failure"]["code"]), (401, "UNAUTHENTICATED"))
            self.assertEqual(called, [])
            self.assertEqual(self.audit_row(body["router_id"])["observation_class"],
                             "routing_failed")
            after = self.counts()
            self.assertEqual(after["routing_audit"], before["routing_audit"] + 1)
            for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
                self.assertEqual(after[name], before[name])
        finally:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=NULL WHERE user_id=%s",
                           (self.user,))

    def test_unknown_write_result_is_not_retried_or_reclassified(self):
        called = []
        request_id = str(uuid4())
        result = {"status": "failed", "request_id": request_id, "task_id": str(uuid4()),
                  "execution_id": str(uuid4()),
                  "failure": {"code": "WRITE_OUTCOME_UNKNOWN", "category": "Environment Failure"}}
        def uncertain_runner(*args, **kwargs):
            called.append((args, kwargs))
            return 503, result
        before = self.counts()
        status, body = self.route(write_runner=uncertain_runner)
        self.assertEqual((status, body["result"], len(called)), (503, result, 1))
        self.assertEqual(self.audit_row(body["router_id"])["observation_class"],
                         "delegate_uncertain")
        after = self.counts()
        for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
            self.assertEqual(after[name], before[name])

    def test_http_header_and_duplicate_key_preflight(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_port}/requests/route"
        before = self.counts()
        request = Request(url, data=json.dumps(self.payload(), ensure_ascii=False).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json; charset=utf-8",
                     "Idempotency-Key": f"m13-{uuid4().hex}"}, method="POST")
        with patch("noah.capability_route.OllamaClient",
                   return_value=RouterModel({"route": SAVE_ROUTE})):
            with urlopen(request, timeout=5) as response:
                self.assertEqual(response.status, 201)
                body = json.loads(response.read())
        self.assertEqual(body["routing"]["capability"], SAVE_ROUTE)
        self.assertEqual(self.counts()["memories"], before["memories"] + 1)
        after = self.counts()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        data = json.dumps(self.payload(), ensure_ascii=False).encode("utf-8")
        connection.putrequest("POST", "/requests/route")
        connection.putheader("Authorization", f"Bearer {self.token}")
        connection.putheader("Content-Type", "application/json; charset=utf-8")
        connection.putheader("Content-Length", str(len(data)))
        connection.putheader("Idempotency-Key", "first-synthetic-key")
        connection.putheader("Idempotency-Key", "second-synthetic-key")
        connection.endheaders(data)
        response = connection.getresponse()
        duplicate_body = json.loads(response.read())
        connection.close()
        self.assertEqual((response.status, duplicate_body["failure"]["code"]),
                         (400, "INVALID_IDEMPOTENCY_KEY"))
        self.assertEqual(self.counts(), after)

    @unittest.skipUnless(os.environ.get("NOAH_TEST_OLLAMA_M13") == "1",
                         "opt-in synthetic M13 routing-model test")
    def test_actual_ollama_save_and_no_action_choices(self):
        model = OllamaClient()
        for question, expected in (("내가 별도로 제공한 내용을 내 메모로 저장해줘.", SAVE_ROUTE),
                                   ("Please save the separately supplied note as my memory.", SAVE_ROUTE),
                                   ("Delete all project files.", NO_ACTION)):
            with self.subTest(expected=expected):
                self.assertEqual(model.complete(_save_messages(question), SAVE_MODEL_SCHEMA, 64),
                                 {"route": expected})


if __name__ == "__main__":
    unittest.main()
