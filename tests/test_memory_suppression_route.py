"""M15 explicit suppression routing with synthetic PostgreSQL ownership."""

import hashlib
import http.client
import json
import os
import threading
import unittest
from http.server import ThreadingHTTPServer
from unittest.mock import patch
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg

from noah.__main__ import Handler
from noah.capability_route import (
    MODEL_SCHEMA, NO_ACTION, ROUTES, SAVE_MODEL_SCHEMA, SAVE_ROUTES,
    SUPPRESS_MODEL_SCHEMA, SUPPRESS_ROUTE, _suppress_messages, route_read_request,
)
from noah.db import connect
from noah.memory_suppression import suppress_memory
from noah.ollama import OllamaClient, OllamaTimeout, OllamaUnavailable
from noah.routing_audit import AuditWriteError, RoutingAudit
from noah.service import (create_project, list_memories, provision_user,
                          read_memory, search_memories)


QUESTION = "내가 지정한 테스트 기억을 일반 조회에서 제외해 줘."
CONTENT = "M15 public synthetic otter memory body"
FAKE_SETTINGS = lambda: {"POSTGRES_PASSWORD": "synthetic-password-not-real"}


class RouteModel:
    def __init__(self, proposal):
        self.proposal, self.calls = proposal, []

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        if isinstance(self.proposal, Exception):
            raise self.proposal
        return self.proposal


class FaultAudit(RoutingAudit):
    def __init__(self, factory, phase, uncertain=False, after_commit=False):
        super().__init__(factory)
        self.phase, self.uncertain, self.after_commit = phase, uncertain, after_commit

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


class NoMemoryConnection:
    """Fail if the router reads any target before a no-action decision."""

    def __init__(self):
        self.db = connect()

    def __enter__(self):
        self.db.__enter__()
        return self

    def __exit__(self, *args):
        return self.db.__exit__(*args)

    def execute(self, query, params=None):
        if "noah.memories" in query:
            raise AssertionError("Router read target before selection")
        return self.db.execute(query, params)

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()


class RevokeAfterM14Preflight:
    """The delegate's first commit is followed by a synthetic token revocation."""

    def __init__(self, token_hash):
        self.db, self.token_hash, self.commits = connect(), token_hash, 0

    def execute(self, query, params=None):
        return self.db.execute(query, params)

    def commit(self):
        self.db.commit()
        self.commits += 1
        if self.commits == 1:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE token_hash=%s",
                           (self.token_hash,))

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()


class MemorySuppressionRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users, cls.project = [], None
        cls.addClassCleanup(cls._cleanup)
        try:
            with connect() as db:
                db.execute("SELECT suppressed_at FROM noah.memories LIMIT 0")
                db.execute("SELECT 1 FROM noah.routing_audit LIMIT 0")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"M15 PostgreSQL unavailable: {type(error).__name__}") from error
        cls.owner, cls.token = provision_user("M15 synthetic owner")
        cls.users.append(cls.owner)
        cls.other, cls.other_token = provision_user("M15 synthetic outsider")
        cls.users.append(cls.other)
        cls.project = create_project("M15 synthetic project", str(cls.owner))

    @classmethod
    def _cleanup(cls):
        if not cls.users:
            return
        with connect() as db:
            db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id = ANY(%s)",
                       (cls.users,))
            db.execute("DELETE FROM noah.memory_write_requests WHERE actor_user_id = ANY(%s)",
                       (cls.users,))
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id = ANY(%s)",
                       (cls.users,))
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id = ANY(%s)", (cls.users,))
            db.execute("DELETE FROM noah.memories WHERE created_by = ANY(%s)", (cls.users,))
            if cls.project:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s",
                           (cls.project,))
                db.execute("DELETE FROM noah.projects WHERE id=%s", (cls.project,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id = ANY(%s)", (cls.users,))
            db.execute("DELETE FROM noah.users WHERE id = ANY(%s)", (cls.users,))

    def memory(self, owner=None, project=False, content=CONTENT):
        memory_id = uuid4()
        with connect() as db:
            if project:
                db.execute("""INSERT INTO noah.memories
                    (id,project_id,scope,content,created_by)
                    VALUES(%s,%s,'project',%s,%s)""",
                    (memory_id, self.project, content, self.owner))
            else:
                owner = owner or self.owner
                db.execute("""INSERT INTO noah.memories
                    (id,owner_user_id,scope,content,created_by)
                    VALUES(%s,%s,'user',%s,%s)""",
                    (memory_id, owner, content, owner))
        return memory_id

    def payload(self, target, question=QUESTION):
        return {"question": question, "memory_suppress": {"memory_id": str(target)}}

    def counts(self):
        with connect() as db:
            return {table: db.execute(f"SELECT count(*) AS n FROM noah.{table} WHERE {field}=%s",
                (self.owner,)).fetchone()["n"] for table, field in (
                ("routing_audit", "actor_user_id"), ("memories", "owner_user_id"),
                ("tasks", "actor_user_id"), ("execution_records", "actor_user_id"),
                ("memory_write_requests", "actor_user_id"))}

    def route(self, target, proposal=None, **kwargs):
        payload = kwargs.pop("payload", self.payload(target))
        model = kwargs.pop("model", None)
        return route_read_request(payload, self.token,
            model=model if model is not None else RouteModel(
                {"route": SUPPRESS_ROUTE} if proposal is None else proposal),
            settings_provider=FAKE_SETTINGS, **kwargs)

    def audit_row(self, router_id):
        with connect() as db:
            return db.execute("SELECT * FROM noah.routing_audit WHERE router_id=%s",
                              (router_id,)).fetchone()

    def test_first_and_repeat_reuse_m14_without_duplicate_execution(self):
        target = self.memory()
        before = self.counts()
        calls = []
        def counted_suppress(*args):
            calls.append(args)
            return suppress_memory(*args)
        status, first = self.route(target, suppress_runner=counted_suppress)
        self.assertEqual((status, first["status"], first["routing"]["capability"],
                          first["routing"]["audit_status"]),
                         (200, "succeeded", SUPPRESS_ROUTE, "recorded"))
        self.assertEqual(calls, [(str(target), {}, self.token)])
        result = first["result"]
        self.assertEqual((result["outcome"], result["memory_id"]),
                         ("suppressed", str(target)))
        self.assertEqual(self.counts(), {**before, "routing_audit": before["routing_audit"] + 1,
            "tasks": before["tasks"] + 1, "execution_records": before["execution_records"] + 1})
        row = self.audit_row(first["router_id"])
        self.assertEqual((row["stage"], row["validated_route"], row["delegate_capability"],
                          row["observation_class"], row["outcome_code"],
                          row["delegate_request_id"], row["delegate_task_id"],
                          row["delegate_execution_id"]),
                         ("observed", SUPPRESS_ROUTE, SUPPRESS_ROUTE, "delegate_returned",
                          "suppressed", UUID(result["request_id"]), UUID(result["task_id"]),
                          UUID(result["execution_id"])))
        with connect() as db:
            execution = db.execute("""SELECT request_id,task_id,memory_id,capability,status
                FROM noah.execution_records WHERE id=%s""",
                (UUID(result["execution_id"]),)).fetchone()
            memory = db.execute("SELECT content,suppressed_at FROM noah.memories WHERE id=%s",
                                (target,)).fetchone()
        self.assertEqual((execution["request_id"], execution["task_id"],
                          execution["memory_id"], execution["capability"], execution["status"]),
                         (UUID(result["request_id"]), UUID(result["task_id"]), target,
                          SUPPRESS_ROUTE, "succeeded"))
        self.assertEqual((memory["content"], memory["suppressed_at"].isoformat()),
                         (CONTENT, result["suppressed_at"]))
        audit_text = json.dumps({name: str(value) for name, value in row.items()})
        for secret in (QUESTION, CONTENT, str(target), self.token,
                       FAKE_SETTINGS()["POSTGRES_PASSWORD"]):
            self.assertNotIn(secret, audit_text)

        repeat_before = self.counts()
        status, repeat = self.route(target, idempotency_key="ignored-m15-header")
        self.assertEqual((status, repeat["result"]["outcome"],
                          repeat["result"]["suppressed_at"]),
                         (200, "already_suppressed", result["suppressed_at"]))
        self.assertNotEqual(repeat["result"]["request_id"], result["request_id"])
        self.assertEqual((repeat["result"]["task_id"], repeat["result"]["execution_id"]),
                         (None, None))
        self.assertEqual(self.counts(), {**repeat_before,
            "routing_audit": repeat_before["routing_audit"] + 1})
        repeat_row = self.audit_row(repeat["router_id"])
        self.assertEqual((repeat_row["observation_class"], repeat_row["outcome_code"],
                          repeat_row["delegate_request_id"], repeat_row["delegate_task_id"],
                          repeat_row["delegate_execution_id"]),
                         ("delegate_returned", "already_suppressed",
                          UUID(repeat["result"]["request_id"]), None, None))
        self.assertNotIn(str(target), json.dumps({k: str(v) for k,v in repeat_row.items()}))
        self.assertTrue(read_memory(str(target), self.token)[1]["memory"]["suppressed"])

    def test_routed_suppression_excludes_new_normal_list_and_search(self):
        term = "m15-visibility-" + uuid4().hex
        content = "Public synthetic memory " + term
        target = self.memory(content=content)
        def observations():
            list_status, listed = list_memories(self.token, "scope=user&limit=100")
            search_status, searched = search_memories(
                self.token, "user", [term], uuid4())
            self.assertEqual((list_status, search_status), (200, 200))
            return ({item["id"] for item in listed["memories"]},
                    {item["id"] for item in searched["memories"]})
        before_list, before_search = observations()
        self.assertIn(str(target), before_list)
        self.assertIn(str(target), before_search)

        before = self.counts()
        status, body = self.route(target)
        self.assertEqual((status, body["result"]["outcome"]), (200, "suppressed"))
        self.assertEqual(self.counts(), {**before,
            "routing_audit": before["routing_audit"] + 1,
            "tasks": before["tasks"] + 1,
            "execution_records": before["execution_records"] + 1})
        row = self.audit_row(body["router_id"])
        self.assertEqual((row["delegate_request_id"], row["delegate_task_id"],
                          row["delegate_execution_id"]),
                         tuple(UUID(body["result"][key]) for key in
                               ("request_id", "task_id", "execution_id")))
        with connect() as db:
            persisted = db.execute("SELECT suppressed_at FROM noah.memories WHERE id=%s",
                                   (target,)).fetchone()
        self.assertIsNotNone(persisted["suppressed_at"])
        after_list, after_search = observations()
        self.assertNotIn(str(target), after_list)
        self.assertNotIn(str(target), after_search)
        direct_status, direct = read_memory(str(target), self.token)
        self.assertEqual((direct_status, direct["memory"]["content"],
                          direct["memory"]["suppressed"]), (200, content, True))

    def test_ownership_change_after_route_decision_is_denied_by_m14(self):
        target = self.memory()
        model = RouteModel({"route": SUPPRESS_ROUTE})
        calls = []
        before = self.counts()
        def transfer_then_suppress(memory_id, payload, token):
            calls.append((memory_id, payload, token))
            self.assertEqual(len(model.calls), 1)
            with connect() as db:
                db.execute("UPDATE noah.memories SET owner_user_id=%s WHERE id=%s",
                           (self.other, target))
            return suppress_memory(memory_id, payload, token)

        status, body = self.route(target, model=model,
            connection_factory=NoMemoryConnection,
            suppress_runner=transfer_then_suppress)
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (404, "MEMORY_NOT_FOUND"))
        self.assertEqual(calls, [(str(target), {}, self.token)])
        self.assertEqual(body["routing"]["capability"], SUPPRESS_ROUTE)
        self.assertNotIn(CONTENT, json.dumps(body, ensure_ascii=False))
        self.assertNotIn(str(target), json.dumps(body))
        after = self.counts()
        self.assertEqual(after["routing_audit"], before["routing_audit"] + 1)
        for name in ("tasks", "execution_records", "memory_write_requests"):
            self.assertEqual(after[name], before[name])
        with connect() as db:
            memory = db.execute("SELECT owner_user_id,suppressed_at,content FROM noah.memories "
                                "WHERE id=%s", (target,)).fetchone()
        self.assertEqual((memory["owner_user_id"], memory["suppressed_at"],
                          memory["content"]), (self.other, None, CONTENT))
        row = self.audit_row(body["router_id"])
        self.assertEqual((row["stage"], row["validated_route"],
                          row["observation_class"], row["outcome_code"],
                          row["delegate_request_id"], row["delegate_task_id"],
                          row["delegate_execution_id"]),
                         ("observed", SUPPRESS_ROUTE, "correlation_unverified",
                          "MEMORY_NOT_FOUND", None, None, None))

    def test_preflight_auth_shape_conflict_and_uuid_before_model(self):
        target = self.memory()
        before = self.counts()
        cases = (
            (self.payload(target), "invalid-token", "UNAUTHENTICATED"),
            ({"question": QUESTION, "memory_suppress": {"memory_id": "not-a-uuid"}},
             self.token, "INVALID_TARGET"),
            ({"question": QUESTION, "memory_suppress": {"memory_id": 7}},
             self.token, "INVALID_TARGET"),
            ({"question": QUESTION, "memory_suppress": []}, self.token, "INVALID_REQUEST"),
            ({"question": QUESTION, "memory_suppress": {"memory_id": str(target), "force": True}},
             self.token, "INVALID_REQUEST"),
            ({**self.payload(target), "project_id": str(self.project)},
             self.token, "INVALID_REQUEST"),
            ({**self.payload(target), "memory_save": {"content": CONTENT}},
             self.token, "INVALID_REQUEST"),
            ({**self.payload(target), "scope": "project"}, self.token, "INVALID_REQUEST"),
            ({"question": "\ud800", "memory_suppress": {"memory_id": str(target)}},
             self.token, "INVALID_REQUEST"),
            ({"question": self.token, "memory_suppress": {"memory_id": str(target)}},
             self.token, "SENSITIVE_CONTEXT_REJECTED"),
        )
        for payload, token, code in cases:
            with self.subTest(code=code, payload_type=type(payload.get("memory_suppress"))):
                model = RouteModel({"route": SUPPRESS_ROUTE})
                status, body = route_read_request(payload, token, model=model,
                    settings_provider=FAKE_SETTINGS)
                expected_status = (401 if code == "UNAUTHENTICATED" else
                                   422 if code == "SENSITIVE_CONTEXT_REJECTED" else 400)
                self.assertEqual((status, body["failure"]["code"]),
                                 (expected_status, code))
                self.assertEqual(model.calls, [])
                self.assertNotIn("router_id", body)
                self.assertEqual(self.counts(), before)

    def test_no_action_does_not_read_target_or_call_delegate(self):
        target = uuid4()  # No row exists; even this fact must not be queried.
        before = self.counts()
        model = RouteModel({"route": NO_ACTION})
        calls = []
        status, body = self.route(target, model=model,
            connection_factory=NoMemoryConnection,
            suppress_runner=lambda *args: calls.append(args))
        self.assertEqual((status, body["routing"]["outcome"], body["result"]),
                         (200, NO_ACTION, None))
        self.assertEqual(calls, [])
        self.assertEqual(self.counts(), {**before,
            "routing_audit": before["routing_audit"] + 1})
        messages, schema, tokens = model.calls[0]
        self.assertEqual((schema, tokens), (SUPPRESS_MODEL_SCHEMA, 64))
        serialized = json.dumps(messages, ensure_ascii=False)
        self.assertIn("memory_suppress_present", serialized)
        self.assertIn(QUESTION, serialized)
        self.assertNotIn(str(target), serialized)
        self.assertNotIn(CONTENT, serialized)
        self.assertNotIn(self.token, serialized)
        self.assertEqual(self.audit_row(body["router_id"])["observation_class"], "no_action")

    def test_model_failures_and_strict_branch_allowlist(self):
        target = self.memory()
        before = self.counts()
        for proposal, expected in (
            ({"route": "memory.query"}, "ROUTING_MODEL_OUTPUT_INVALID"),
            ({"route": "memory.save"}, "ROUTING_MODEL_OUTPUT_INVALID"),
            ({"route": SUPPRESS_ROUTE, "memory_id": str(target)}, "ROUTING_MODEL_OUTPUT_INVALID"),
            ({"route": SUPPRESS_ROUTE, "arguments": {}}, "ROUTING_MODEL_OUTPUT_INVALID"),
            ("memory.suppress", "ROUTING_MODEL_OUTPUT_INVALID"),
            (OllamaTimeout(), "ROUTING_OLLAMA_TIMEOUT"),
            (OllamaUnavailable(), "ROUTING_OLLAMA_UNAVAILABLE"),
        ):
            with self.subTest(expected=expected):
                calls = []
                status, body = self.route(target, proposal=proposal,
                    suppress_runner=lambda *args: calls.append(args))
                self.assertEqual(body["failure"]["code"], expected)
                self.assertEqual(calls, [])
                self.assertEqual(self.audit_row(body["router_id"])["observation_class"],
                                 "routing_failed")
        after = self.counts()
        self.assertEqual(after["routing_audit"] - before["routing_audit"], 7)
        for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
            self.assertEqual(after[name], before[name])
        self.assertEqual(ROUTES, {"memory.query", "project.documents.answer.auto", NO_ACTION})
        self.assertEqual(SAVE_ROUTES, {"memory.save", NO_ACTION})
        self.assertEqual(MODEL_SCHEMA["properties"]["route"]["enum"],
                         ["memory.query", NO_ACTION, "project.documents.answer.auto"])
        self.assertEqual(SAVE_MODEL_SCHEMA["properties"]["route"]["enum"],
                         ["memory.save", NO_ACTION])
        self.assertEqual(SUPPRESS_MODEL_SCHEMA["properties"]["route"]["enum"],
                         ["memory.suppress", NO_ACTION])
        status, body = route_read_request({"question": "anything"}, self.token,
            model=RouteModel({"route": SUPPRESS_ROUTE}), settings_provider=FAKE_SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (502, "ROUTING_MODEL_OUTPUT_INVALID"))

    def test_m14_non_enumerating_target_failures_stay_authoritative(self):
        foreign = self.memory(owner=self.other)
        project = self.memory(project=True)
        missing = uuid4()
        before = self.counts()
        for target, status_expected, code in (
            (foreign, 404, "MEMORY_NOT_FOUND"),
            (missing, 404, "MEMORY_NOT_FOUND"),
            (project, 422, "UNSUPPORTED_SCOPE"),
        ):
            with self.subTest(code=code):
                status, body = self.route(target)
                self.assertEqual((status, body["result"]["failure"]["code"]),
                                 (status_expected, code))
                self.assertEqual(body["routing"]["capability"], SUPPRESS_ROUTE)
                row = self.audit_row(body["router_id"])
                self.assertEqual((row["stage"], row["delegate_task_id"],
                                  row["delegate_execution_id"]), ("observed", None, None))
                self.assertNotIn(str(target), json.dumps({k: str(v) for k,v in row.items()}))
        after = self.counts()
        self.assertEqual(after["routing_audit"] - before["routing_audit"], 3)
        for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
            self.assertEqual(after[name], before[name])

    def test_predelegate_audit_failures_never_invoke_m14(self):
        target = self.memory()
        for phase in ("reserve", "route_validated", "dispatch_prepared"):
            for after_commit in (False, True):
                with self.subTest(phase=phase, after_commit=after_commit):
                    calls = []
                    before = self.counts()
                    status, body = self.route(target,
                        audit=FaultAudit(connect, phase, uncertain=after_commit,
                                         after_commit=after_commit),
                        suppress_runner=lambda *args: calls.append(args))
                    self.assertEqual(status, 503)
                    self.assertEqual(calls, [])
                    if phase == "reserve" and not after_commit:
                        self.assertNotIn("router_id", body)
                        self.assertEqual(self.counts()["routing_audit"],
                                         before["routing_audit"])
                    else:
                        self.assertEqual(body["routing"]["audit_status"], "unconfirmed")
                        row = self.audit_row(body["router_id"])
                        expected_stage = (
                            "reserved" if phase == "reserve" or
                            (phase == "route_validated" and not after_commit) else
                            "route_validated" if phase == "dispatch_prepared" and
                            not after_commit else phase)
                        self.assertEqual(row["stage"], expected_stage)
                        self.assertIsNone(row["delegate_request_id"])
                        self.assertIsNone(row["delegate_task_id"])
                        self.assertIsNone(row["delegate_execution_id"])
                    after = self.counts()
                    for name in ("memories", "tasks", "execution_records", "memory_write_requests"):
                        self.assertEqual(after[name], before[name])
                    self.assertFalse(read_memory(str(target), self.token)[1]["memory"]["suppressed"])

    def test_final_audit_failure_preserves_delegate_and_no_action_boundary(self):
        for after_commit in (False, True):
            target = self.memory()
            calls = []
            def counted(*args):
                calls.append(args)
                return suppress_memory(*args)
            status, body = self.route(target, suppress_runner=counted,
                audit=FaultAudit(connect, "observed", uncertain=after_commit,
                                 after_commit=after_commit))
            self.assertEqual((status, body["result"]["outcome"],
                              body["routing"]["audit_status"], len(calls)),
                             (200, "suppressed", "unconfirmed", 1))
            self.assertTrue(read_memory(str(target), self.token)[1]["memory"]["suppressed"])
        target = uuid4()
        calls = []
        status, body = self.route(target, proposal={"route": NO_ACTION},
            audit=FaultAudit(connect, "observed"),
            suppress_runner=lambda *args: calls.append(args))
        self.assertEqual((status, body["failure"]["code"], calls),
                         (503, "ROUTING_AUDIT_UNAVAILABLE", []))

    def test_unknown_delegate_result_and_unverified_correlation_are_not_retried(self):
        target = self.memory()
        request_id = str(uuid4())
        unknown = {"status": "failed", "request_id": request_id,
            "task_id": None, "execution_id": None, "outcome": "unknown",
            "failure": {"code": "SUPPRESSION_OUTCOME_UNKNOWN", "category": "Environment Failure"}}
        calls = []
        def uncertain(*args):
            calls.append(args)
            return 503, unknown
        status, body = self.route(target, suppress_runner=uncertain)
        self.assertEqual((status, body["result"], len(calls)), (503, unknown, 1))
        row = self.audit_row(body["router_id"])
        self.assertEqual((row["observation_class"], row["outcome_code"],
                          row["delegate_task_id"], row["delegate_execution_id"]),
                         ("delegate_uncertain", "SUPPRESSION_OUTCOME_UNKNOWN", None, None))
        self.assertFalse(read_memory(str(target), self.token)[1]["memory"]["suppressed"])
        forged = {"status": "succeeded", "request_id": str(uuid4()),
            "task_id": str(uuid4()), "execution_id": str(uuid4()),
            "memory_id": str(target), "suppressed_at": "2026-01-01T00:00:00+00:00",
            "outcome": "suppressed"}
        status, body = self.route(target,
            suppress_runner=lambda *args: (200, forged))
        self.assertEqual((status, body["result"]), (200, forged))
        row = self.audit_row(body["router_id"])
        self.assertEqual((row["observation_class"], row["delegate_request_id"],
                          row["delegate_task_id"], row["delegate_execution_id"]),
                         ("correlation_unverified", None, None, None))

    def test_token_revocation_inside_m14_transaction_blocks_transition(self):
        target = self.memory()
        digest = hashlib.sha256(self.token.encode()).hexdigest()
        def revoking_runner(memory_id, payload, token):
            return suppress_memory(memory_id, payload, token,
                connection_factory=lambda: RevokeAfterM14Preflight(digest))
        try:
            status, body = self.route(target, suppress_runner=revoking_runner)
            self.assertEqual((status, body["result"]["failure"]["code"]),
                             (401, "UNAUTHENTICATED"))
            self.assertIsNone(self.audit_row(body["router_id"])["delegate_execution_id"])
        finally:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=NULL WHERE token_hash=%s",
                           (digest,))
        self.assertFalse(read_memory(str(target), self.token)[1]["memory"]["suppressed"])

    def test_http_parser_rejects_duplicate_json_keys_and_uses_internal_delegate(self):
        target = self.memory()
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        url = f"http://127.0.0.1:{server.server_port}/requests/route"
        model = RouteModel({"route": SUPPRESS_ROUTE})
        before = self.counts()
        duplicate = (f'{{"question":"{QUESTION}","memory_suppress":'
                     f'{{"memory_id":"{target}","memory_id":"{target}"}}}}').encode()
        connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
        connection.request("POST", "/requests/route", body=duplicate,
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json; charset=utf-8"})
        response = connection.getresponse()
        invalid = json.loads(response.read())
        connection.close()
        self.assertEqual((response.status, invalid["failure"]["code"]),
                         (400, "INVALID_REQUEST"))
        self.assertEqual(self.counts(), before)
        request = Request(url, data=json.dumps(self.payload(target), ensure_ascii=False).encode(),
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json; charset=utf-8"}, method="POST")
        with patch("noah.capability_route.OllamaClient", return_value=model):
            with urlopen(request, timeout=5) as response:
                body = json.loads(response.read())
                self.assertEqual(response.status, 200)
        self.assertEqual((body["routing"]["capability"], body["result"]["outcome"],
                          len(model.calls)), (SUPPRESS_ROUTE, "suppressed", 1))

    @unittest.skipUnless(os.environ.get("NOAH_TEST_OLLAMA_M15") == "1",
                         "opt-in synthetic M15 routing-model selection test")
    def test_actual_ollama_suppression_and_no_action_choices(self):
        model = OllamaClient()
        for question, expected in (
            ("내가 지정한 기억을 일반 조회에서 제외해 줘.", SUPPRESS_ROUTE),
            ("Please suppress the separately selected memory.", SUPPRESS_ROUTE),
            ("내일 날씨를 알려줘.", NO_ACTION),
            ("What is the weather tomorrow?", NO_ACTION),
        ):
            with self.subTest(expected=expected):
                self.assertEqual(model.complete(_suppress_messages(question),
                    SUPPRESS_MODEL_SCHEMA, 64), {"route": expected})


if __name__ == "__main__":
    unittest.main()
