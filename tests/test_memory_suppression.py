"""M14 contracts over isolated synthetic PostgreSQL users and memories."""

import json
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from http.server import ThreadingHTTPServer
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.request import Request, urlopen
from uuid import UUID, uuid4

import psycopg

from noah.__main__ import Handler
from noah.capability_route import MEMORY_ROUTE, route_read_request
from noah.db import connect
from noah.memory_query import query_memory
from noah.memory_suppression import suppress_memory
from noah.recovery import triage_memory_writes
from noah.service import (_audit_db_failure, create_project, list_memories,
                          provision_user, read_memory, save_memory)


class QueryModel:
    def __init__(self, term, evidence_id, quote, before_evidence=None):
        self.term, self.evidence_id, self.quote = term, evidence_id, quote
        self.before_evidence, self.calls = before_evidence, 0

    def complete(self, _messages, _schema, _max_tokens):
        self.calls += 1
        if self.calls == 1:
            return {"intent": "memory_read", "scope": "user", "query": self.term}
        if self.before_evidence:
            self.before_evidence()
        return {"evidence": [{"memory_id": str(self.evidence_id), "quote": self.quote}]}


class RouteModel:
    def complete(self, _messages, _schema, _max_tokens):
        return {"route": MEMORY_ROUTE}


class CursorRow:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class FaultConnection:
    """Inject only synthetic DB failure points; delegate all other operations."""
    def __init__(self, mode, revoke_hash=None):
        self.db, self.mode = connect(), mode
        self.commits, self.updated, self.revoke_hash = 0, False, revoke_hash

    def execute(self, query, params=None):
        sql = query.strip()
        if sql.startswith("UPDATE noah.memories"):
            if self.mode == "update":
                raise psycopg.OperationalError("synthetic update failure")
            self.updated = True
        cursor = self.db.execute(query, params)
        if (self.mode == "readback" and self.updated
                and sql == "SELECT * FROM noah.memories WHERE id=%s"):
            row = dict(cursor.fetchone())
            row["content"] = "synthetic mismatched readback"
            return CursorRow(row)
        if (self.mode == "readback_error" and self.updated
                and sql == "SELECT * FROM noah.memories WHERE id=%s"):
            raise psycopg.OperationalError("synthetic readback failure")
        return cursor

    def commit(self):
        self.commits += 1
        self.db.commit()
        if self.mode == "revoke" and self.commits == 1:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE token_hash=%s",
                           (self.revoke_hash,))
        if self.mode == "unknown" and self.commits == 2:
            raise psycopg.OperationalError("synthetic lost commit acknowledgement")

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.close()


class DiagnosticStatusTests(unittest.TestCase):
    def test_unknown_outcomes_and_definite_failure_are_distinct(self):
        codes = ("WRITE_OUTCOME_UNKNOWN", "SUPPRESSION_OUTCOME_UNKNOWN",
                 "DATABASE_UNAVAILABLE")
        with TemporaryDirectory() as directory, patch("noah.service.ROOT", Path(directory)):
            for code in codes:
                _audit_db_failure(uuid4(), code=code)
            records = [json.loads(line) for line in
                (Path(directory) / ".noah" / "failures.jsonl").read_text(
                    encoding="utf-8").splitlines()]
        self.assertEqual([(record["code"], record["status"]) for record in records],
            [("WRITE_OUTCOME_UNKNOWN", "unknown"),
             ("SUPPRESSION_OUTCOME_UNKNOWN", "unknown"),
             ("DATABASE_UNAVAILABLE", "failed")])


class MemorySuppressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users, cls.project = [], None
        cls.addClassCleanup(cls._cleanup)
        try:
            with connect() as db:
                db.execute("SELECT suppressed_at FROM noah.memories LIMIT 0")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"M14 PostgreSQL migration unavailable: {type(error).__name__}") from error
        cls.owner, cls.token = provision_user("M14 synthetic owner")
        cls.users.append(cls.owner)
        cls.other, cls.other_token = provision_user("M14 synthetic outsider")
        cls.users.append(cls.other)
        cls.project = create_project("M14 synthetic project", str(cls.owner))

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

    def memory(self, content="M14 synthetic note", owner=None, project=False):
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

    def records(self, memory_id):
        with connect() as db:
            return db.execute("""SELECT e.id,e.request_id,e.task_id,e.capability,e.status,
                e.verified_at,t.status AS task_status,t.verification_status
                FROM noah.execution_records e JOIN noah.tasks t ON t.id=e.task_id
                WHERE e.memory_id=%s AND e.capability='memory.suppress'""",
                (memory_id,)).fetchall()

    def test_first_repeat_readback_and_active_response_contract(self):
        memory_id = self.memory("M14 synthetic otter")
        before = read_memory(str(memory_id), self.token)[1]["memory"]
        self.assertEqual((before["suppressed"], before["suppressed_at"]), (False, None))
        listed = list_memories(self.token, "scope=user&limit=100")[1]["memories"]
        self.assertEqual(next(x for x in listed if x["id"] == str(memory_id)), before)
        status, first = suppress_memory(str(memory_id), {}, self.token)
        self.assertEqual((status, first["status"], first["outcome"]),
                         (200, "succeeded", "suppressed"))
        self.assertEqual(first["memory_id"], str(memory_id))
        rows = self.records(memory_id)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual((str(row["id"]), str(row["task_id"]), row["capability"],
                          row["status"], row["task_status"], row["verification_status"]),
                         (first["execution_id"], first["task_id"], "memory.suppress",
                          "succeeded", "completed", "passed"))
        self.assertIsNotNone(row["verified_at"])
        direct = read_memory(str(memory_id), self.token)[1]["memory"]
        self.assertEqual((direct["content"], direct["suppressed"], direct["suppressed_at"]),
                         (before["content"], True, first["suppressed_at"]))
        self.assertEqual({key: direct[key] for key in before if key not in
                          {"suppressed", "suppressed_at"}},
                         {key: before[key] for key in before if key not in
                          {"suppressed", "suppressed_at"}})
        status, repeat = suppress_memory(str(memory_id), {}, self.token)
        self.assertEqual((status, repeat["outcome"], repeat["suppressed_at"],
                          repeat["task_id"], repeat["execution_id"]),
                         (200, "already_suppressed", first["suppressed_at"], None, None))
        self.assertNotEqual(first["request_id"], repeat["request_id"])
        self.assertEqual(len(self.records(memory_id)), 1)
        self.assertNotIn(str(memory_id), [x["id"] for x in
            list_memories(self.token, "scope=user&limit=100")[1]["memories"]])

    def test_denials_and_transactional_token_revalidation(self):
        own, foreign, project = self.memory(), self.memory(owner=self.other), self.memory(project=True)
        for target, token, payload, expected in (
            (str(own), self.other_token, {}, (404, "MEMORY_NOT_FOUND")),
            (str(foreign), self.token, {}, (404, "MEMORY_NOT_FOUND")),
            (str(project), self.token, {}, (422, "UNSUPPORTED_SCOPE")),
            (str(own), "invalid", {}, (401, "UNAUTHENTICATED")),
            ("not-a-uuid", self.token, {}, (400, "INVALID_TARGET")),
            (str(own), self.token, {"content": "not accepted"}, (400, "INVALID_REQUEST")),
        ):
            status, body = suppress_memory(target, payload, token)
            self.assertEqual((status, body["failure"]["code"]), expected)
            self.assertEqual((body["task_id"], body["execution_id"]), (None, None))
        self.assertEqual(self.records(own), [])
        import hashlib
        digest = hashlib.sha256(self.token.encode()).hexdigest()
        try:
            status, body = suppress_memory(str(own), {}, self.token,
                connection_factory=lambda: FaultConnection("revoke", digest))
            self.assertEqual((status, body["failure"]["code"]), (401, "UNAUTHENTICATED"))
            self.assertEqual(self.records(own), [])
        finally:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=NULL WHERE token_hash=%s",
                           (digest,))
        self.assertFalse(read_memory(str(own), self.token)[1]["memory"]["suppressed"])

    def test_sql_pagination_excludes_suppressed_before_limit(self):
        ids = [self.memory(f"M14 cursor synthetic {index}") for index in range(3)]
        with connect() as db:
            for index, memory_id in enumerate(ids):
                db.execute("UPDATE noah.memories SET created_at=now()+interval '10 years' "
                           "+ (%s * interval '1 minute') "
                           "WHERE id=%s", (index, memory_id))
        suppress_memory(str(ids[1]), {}, self.token)
        first = list_memories(self.token, "scope=user&limit=1")[1]
        self.assertEqual(first["memories"][0]["id"], str(ids[2]))
        self.assertIsNotNone(first["next_cursor"])
        second = list_memories(self.token,
            "scope=user&limit=1&cursor=" + first["next_cursor"])[1]
        self.assertEqual(second["memories"][0]["id"], str(ids[0]))
        self.assertNotIn(str(ids[1]), [x["id"] for x in first["memories"]+second["memories"]])

    def test_model_input_uncited_and_cited_races_withhold_entire_answer(self):
        for suppress_cited in (False, True):
            with self.subTest(suppress_cited=suppress_cited):
                term = "M14" + uuid4().hex[:10]
                cited = self.memory(term + " synthetic otter")
                uncited = self.memory(term + " synthetic blue")
                target = cited if suppress_cited else uncited
                model = QueryModel(term, cited, "synthetic otter",
                    before_evidence=lambda: suppress_memory(str(target), {}, self.token))
                status, body = query_memory({"question": "Find " + term + " note"},
                                            self.token, model=model)
                self.assertEqual((status, body["failure"]["code"], model.calls),
                                 (409, "MEMORY_CONTEXT_STALE", 2))
                for forbidden in ("answer", "evidence", "search_terms", "examined", "truncated"):
                    self.assertNotIn(forbidden, body)
                self.assertNotIn("synthetic otter", str(body))
                self.assertNotIn("synthetic blue", str(body))

    def test_routed_memory_rechecks_after_m3_internal_success(self):
        term = "M14" + uuid4().hex[:10]
        cited = self.memory(term + " synthetic otter")
        uncited = self.memory(term + " synthetic blue")
        model = QueryModel(term, cited, "synthetic otter")
        def runner(payload, token):
            status, result = query_memory(payload, token, model=model)
            self.assertEqual(status, 200)
            suppress_memory(str(uncited), {}, token)
            return status, result
        status, body = route_read_request({"question": "Find " + term + " note"},
            self.token, model=RouteModel(), memory_runner=runner,
            settings_provider=lambda: {"POSTGRES_PASSWORD": "synthetic-not-real"})
        self.assertEqual((status, body["failure"]["code"], body["result"]),
                         (409, "MEMORY_CONTEXT_STALE", None))
        self.assertNotIn("synthetic otter", str(body))
        self.assertEqual(model.calls, 2)

    def test_routed_final_check_follows_correlation_work(self):
        term = "M14" + uuid4().hex[:10]
        cited = self.memory(term + " synthetic otter")
        uncited = self.memory(term + " synthetic blue")
        model = QueryModel(term, cited, "synthetic otter")
        from noah import capability_route
        correlate_original = capability_route._delegate_correlation
        def correlate_then_suppress(*args):
            correlation = correlate_original(*args)
            suppress_memory(str(uncited), {}, self.token)
            return correlation
        with patch("noah.capability_route._delegate_correlation",
                   side_effect=correlate_then_suppress):
            status, body = route_read_request({"question": "Find " + term + " note"},
                self.token, model=RouteModel(),
                memory_runner=lambda payload, token: query_memory(payload, token, model=model),
                settings_provider=lambda: {"POSTGRES_PASSWORD": "synthetic-not-real"})
        self.assertEqual((status, body["failure"]["code"], body["result"]),
                         (409, "MEMORY_CONTEXT_STALE", None))
        self.assertNotIn("synthetic otter", str(body))

    def test_concurrent_calls_create_one_transition(self):
        memory_id = self.memory("M14 concurrent synthetic")
        with ThreadPoolExecutor(max_workers=2) as pool:
            responses = list(pool.map(lambda _: suppress_memory(str(memory_id), {}, self.token),
                                      range(2)))
        self.assertEqual(sorted(body["outcome"] for status, body in responses),
                         ["already_suppressed", "suppressed"])
        self.assertEqual(len(self.records(memory_id)), 1)

    def test_failure_rollback_and_commit_ack_unknown(self):
        for mode, code, expected_suppressed in (
            ("update", "SUPPRESSION_FAILED", False),
            ("readback", "VERIFICATION_FAILED", False),
            ("readback_error", "VERIFICATION_FAILED", False),
            ("unknown", "SUPPRESSION_OUTCOME_UNKNOWN", True),
        ):
            with self.subTest(mode=mode):
                memory_id = self.memory("M14 fault synthetic " + mode)
                status, body = suppress_memory(str(memory_id), {}, self.token,
                    connection_factory=lambda: FaultConnection(mode))
                self.assertEqual((status, body["failure"]["code"]),
                                 (503 if mode == "unknown" else 500, code))
                self.assertEqual((body["task_id"], body["execution_id"]), (None, None))
                self.assertEqual(body.get("outcome"), "unknown" if mode == "unknown" else None)
                self.assertEqual(read_memory(str(memory_id), self.token)[1]["memory"]["suppressed"],
                                 expected_suppressed)
                self.assertEqual(len(self.records(memory_id)), int(expected_suppressed))

    def test_m4_replay_and_m5_scope_remain_separate(self):
        key = "m14-" + uuid4().hex
        payload = {"action": "save_memory", "scope": "user",
                   "owner_user_id": str(self.owner), "content": "M14 replay synthetic"}
        status, saved = save_memory(payload, self.token, idempotency_key=key)
        self.assertEqual(status, 201)
        memory_id = saved["evidence"]["memory_id"]
        self.assertFalse(read_memory(memory_id, self.token)[1]["memory"]["suppressed"])
        suppressed = suppress_memory(memory_id, {}, self.token)[1]
        status, replay = save_memory(payload, self.token, idempotency_key=key)
        self.assertEqual((status, replay["replayed"], replay["evidence"]["memory_id"]),
                         (200, True, memory_id))
        self.assertEqual((replay["task_id"], replay["execution_id"]),
                         (saved["task_id"], saved["execution_id"]))
        self.assertEqual(read_memory(memory_id, self.token)[1]["memory"]["suppressed_at"],
                         suppressed["suppressed_at"])
        self.assertEqual(len(self.records(UUID(memory_id))), 1)
        report = triage_memory_writes()
        self.assertEqual(report["status"], "succeeded")
        self.assertNotIn(suppressed["execution_id"],
                         [item["execution_id"] for item in report["items"]])

    def test_http_endpoint_uses_explicit_id_without_model(self):
        memory_id = self.memory("M14 HTTP synthetic")
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            request = Request(f"http://127.0.0.1:{server.server_port}/memories/{memory_id}/suppress",
                data=b"{}", headers={"Authorization": "Bearer " + self.token,
                                       "Content-Type": "application/json; charset=utf-8"},
                method="POST")
            with urlopen(request, timeout=5) as response:
                body = json.load(response)
                self.assertEqual(response.status, 200)
            self.assertEqual((body["outcome"], body["memory_id"]),
                             ("suppressed", str(memory_id)))
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)
