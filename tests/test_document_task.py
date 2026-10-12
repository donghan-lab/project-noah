"""M18 deterministic tests. Require a verified disposable source and DB first."""

from datetime import datetime, timedelta, timezone
from email.message import Message
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

import psycopg

from noah import document_task as tasks
from noah.__main__ import Handler
from noah.db import ROOT, connect, initialize, local_settings
from noah.document_read import read_document_bytes
from noah.document_tool import ToolFailure, ToolOutcomeUnknown
from noah.ollama import OllamaTimeout
from noah.service import create_project, provision_user

CONTENT = "NOAH의 공개 테스트 동물은 수달이다.\nNOAH의 공개 테스트 색상은 파란색이다.\n"
QUOTE = CONTENT.splitlines()[0]
NAME = "m18-public.md"


class Model:
    def __init__(self, outcome="supported", callback=None, error=None, output=None):
        self.calls = []
        self.outcome, self.callback, self.error, self.output = outcome, callback, error, output

    def complete(self, messages, schema, tokens):
        self.calls.append((messages, schema, tokens))
        if self.callback:
            self.callback()
        if self.error:
            raise self.error
        if self.output is not None:
            return self.output
        quotes = [] if self.outcome in {"insufficient", "out_of_scope"} else [{"quote": QUOTE}]
        if self.outcome == "conflicting":
            quotes.append({"quote": CONTENT.splitlines()[1]})
        return {"outcome": self.outcome, "evidence": quotes}


class Proxy:
    """Wrap real PostgreSQL; inject only acknowledgement/control boundaries."""
    def __init__(self, db, execute=None, commit=None):
        self.db, self.execute_hook, self.commit_hook = db, execute, commit
        self.marked = False
        self.task = None

    def execute(self, sql, params=None):
        if self.execute_hook:
            self.execute_hook(self, sql, params, False)
        result = self.db.execute(sql, params)
        if self.execute_hook:
            self.execute_hook(self, sql, params, True)
        return result

    def commit(self):
        self.db.commit()
        if self.commit_hook:
            self.commit_hook(self)

    def rollback(self):
        return self.db.rollback()

    def close(self):
        return self.db.close()

    def __enter__(self):
        self.db.__enter__()
        return self

    def __exit__(self, *args):
        return self.db.__exit__(*args)


class DocumentTaskTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = os.environ.get("NOAH_DISPOSABLE_SOURCE", "")
        if os.environ.get("NOAH_ISOLATED_TEST_DB") != "1" or not source:
            raise unittest.SkipTest("M18 needs an explicitly verified disposable source")
        if ROOT.resolve() != Path(source).resolve():
            raise RuntimeError("Refusing original source/configuration BEFORE connection")
        settings = local_settings()
        if (settings["POSTGRES_DB"] != "noah_m17_isolated"
                or settings["POSTGRES_PORT"] != os.environ.get("NOAH_DISPOSABLE_PORT")):
            raise RuntimeError("Refusing unverified connection target")
        with connect() as db:
            if db.execute("SELECT current_database() AS name").fetchone()["name"] != settings["POSTGRES_DB"]:
                raise RuntimeError("Wrong disposable database")
        initialize()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="noah-m18-synthetic-")
        self.root = Path(self.directory.name)
        (self.root / NAME).write_bytes(CONTENT.encode("utf-8"))
        self.actor, self.token = provision_user("M18 synthetic " + str(uuid4()))
        self.other, self.other_token = provision_user("M18 synthetic outsider " + str(uuid4()))
        self.actors = [self.actor, self.other]
        self.project = create_project("M18 synthetic " + str(uuid4()), str(self.actor))
        self.projects = [self.project]
        self.addCleanup(self.directory.cleanup)
        self.addCleanup(self.cleanup)

    def cleanup(self):
        with connect() as db:
            ids = [r["id"] for r in db.execute("SELECT id FROM noah.tasks WHERE actor_user_id=ANY(%s)",
                (self.actors,)).fetchall()]
            for table in ("document_answer_evidence", "document_read_evidence"):
                db.execute(f"DELETE FROM noah.{table} WHERE execution_id IN"
                    " (SELECT id FROM noah.execution_records WHERE task_id=ANY(%s) OR actor_user_id=ANY(%s))",
                    (ids, self.actors))
            db.execute("DELETE FROM noah.document_question_tasks WHERE task_id=ANY(%s)", (ids,))
            db.execute("DELETE FROM noah.execution_records WHERE task_id=ANY(%s) OR actor_user_id=ANY(%s)",
                (ids, self.actors))
            db.execute("DELETE FROM noah.tasks WHERE id=ANY(%s)", (ids,))
            db.execute("DELETE FROM noah.project_memberships WHERE project_id=ANY(%s)", (self.projects,))
            db.execute("DELETE FROM noah.projects WHERE id=ANY(%s)", (self.projects,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id=ANY(%s)", (self.actors,))
            db.execute("DELETE FROM noah.users WHERE id=ANY(%s)", (self.actors,))

    def register(self, **options):
        payload = options.pop("payload", {"project_id": str(self.project),
            "document_name": NAME, "question": "  문서의 공개 테스트 동물은?  "})
        token = options.pop("token", self.token)
        return tasks.register_document_task(payload, token, **options)

    def ready(self):
        status, body = self.register()
        self.assertEqual(status, 201, body)
        return body["task_id"]

    def run_task(self, task, model=None, **options):
        options.setdefault("root_provider", lambda _: ("m18-synthetic-root", self.root))
        options.setdefault("read_runner", read_document_bytes)
        return tasks.run_document_task(task, {}, self.token, model=model or Model(), **options)

    def state(self, task):
        with connect() as db:
            row = db.execute(tasks._SELECT + " WHERE t.id=%s", (UUID(task),)).fetchone()
            executions = db.execute("SELECT * FROM noah.execution_records WHERE task_id=%s", (UUID(task),)).fetchall()
            counts = [db.execute(f"SELECT count(*) AS n FROM noah.{table} WHERE execution_id IN"
                " (SELECT id FROM noah.execution_records WHERE task_id=%s)", (UUID(task),)).fetchone()["n"]
                for table in ("document_read_evidence", "document_answer_evidence")]
            return row, executions, counts

    def counts(self):
        with connect() as db:
            return {r["table_name"]: db.execute('SELECT count(*) AS n FROM noah."' + r["table_name"] + '"').fetchone()["n"]
                for r in db.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='noah'").fetchall()}

    def test_registration_is_only_ready_definition(self):
        before = self.counts()
        with patch.object(tasks, "operator_root", side_effect=AssertionError("mapping forbidden")), \
                patch.object(tasks, "OllamaClient", side_effect=AssertionError("model forbidden")):
            status, body = self.register()
        self.assertEqual(status, 201)
        self.assertEqual(body["registration"], {"status": "confirmed", "initial_task_status": "ready",
            "initial_verification_status": "pending", "execution_created": False})
        self.assertEqual(body["task"]["definition"]["question"], "문서의 공개 테스트 동물은?")
        self.assertIsNone(body["execution"])
        self.assertIsNone(body["result"])
        after = self.counts()
        self.assertEqual({k: after[k]-before[k] for k in before if after[k] != before[k]},
            {"tasks": 1, "document_question_tasks": 1})

    def test_preflight_rejections_have_zero_delta(self):
        before = self.counts()
        for payload in (None, [], {}, {"project_id": str(self.project), "document_name": NAME,
                "question": "x", "model": "injected"},
                {"project_id": str(self.project), "document_name": "../bad.md", "question": "x"},
                {"project_id": str(self.project), "document_name": NAME, "question": "한" * 180},
                {"project_id": str(self.project).upper(), "document_name": NAME, "question": "x"}):
            self.assertIn(self.register(payload=payload)[0], (400, 415))
        self.assertEqual(self.register(token=self.other_token)[0], 404)
        self.assertEqual(self.register(token="not-a-token")[0], 401)
        self.assertEqual(self.register(forbidden_headers=True)[0], 400)
        self.assertEqual(self.register(query="x=1")[0], 400)
        for value in (self.token, local_settings()["POSTGRES_PASSWORD"]):
            self.assertEqual(self.register(payload={"project_id": str(self.project),
                "document_name": NAME, "question": value})[0], 422)
        self.assertEqual(before, self.counts())

    def test_authorized_list_pagination_and_non_enumeration(self):
        ids = [self.ready() for _ in range(3)]
        hidden = create_project("M18 hidden " + str(uuid4()), str(self.actor))
        self.projects.append(hidden)
        private = self.register(payload={"project_id": str(hidden), "document_name": NAME, "question": "private"})[1]["task_id"]
        with connect() as db:
            db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (hidden,))
        status, first = tasks.list_document_tasks(self.token, "limit=1")
        self.assertEqual(status, 200)
        self.assertEqual(len(first["items"]), 1)
        self.assertNotIn("question", first["items"][0])
        self.assertNotIn("문서의 공개 테스트 동물은?", str(first["items"]))
        all_ids, page = [], first
        while True:
            all_ids.extend(item["id"] for item in page["items"])
            if page["next_cursor"] is None:
                break
            status, page = tasks.list_document_tasks(self.token, "limit=1&cursor=" + page["next_cursor"])
            self.assertEqual(status, 200)
        self.assertEqual(set(all_ids), set(ids))
        self.assertNotIn(private, all_ids)
        for task, token in ((private, self.token), (ids[0], self.other_token), (str(uuid4()), self.token)):
            status, body = tasks.inspect_document_task(task, token)
            self.assertEqual((status, body["failure"]["code"]), (404, "TASK_NOT_FOUND"))
            self.assertIsNone(body["task_id"])
        for query in ("limit=0", "limit=101", "limit=1&limit=2", "extra=x", "cursor=bad!"):
            self.assertEqual(tasks.list_document_tasks(self.token, query)[0], 400)

    def test_all_answer_outcomes_and_one_execution(self):
        for outcome in sorted(tasks.OUTCOMES):
            with self.subTest(outcome=outcome):
                task, model = self.ready(), Model(outcome)
                status, body = self.run_task(task, model)
                self.assertEqual(status, 200, body)
                self.assertEqual(body["result"]["outcome"], outcome)
                self.assertEqual(body["task"]["status"], "completed")
                self.assertEqual(body["execution"]["observation"], "verified")
                self.assertEqual(body["result"]["temporal_scope"], "execution_observation")
                row, executions, counts = self.state(task)
                self.assertEqual((len(executions), counts), (1, [1, 1]))
                self.assertEqual(row["execution_id"], executions[0]["id"])
                self.assertEqual(len(model.calls), 1)
                self.assertEqual(self.run_task(task)[0], 409)
                self.assertNotIn(self.token, str(model.calls))
                self.assertNotIn(str(self.root), str(model.calls))
                for item in body["result"]["evidence"]:
                    self.assertEqual(CONTENT[item["start"]:item["end"]], item["quote"])

    def test_production_safe_read_worker(self):
        status, body = self.run_task(self.ready(), read_runner=tasks.execute_document_read)
        self.assertEqual(status, 200, body)

    def test_historical_inspection_never_reads_model_file_or_mapping(self):
        task = self.ready()
        result = self.run_task(task)[1]["result"]
        (self.root / NAME).unlink()
        with patch.object(tasks, "OllamaClient", side_effect=AssertionError("model")), \
                patch.object(tasks, "_read", side_effect=AssertionError("file")), \
                patch.object(tasks, "operator_root", side_effect=AssertionError("mapping")):
            before = self.counts()
            status, body = tasks.inspect_document_task(task, self.token)
        self.assertEqual(status, 200)
        self.assertEqual(body["result"], result)
        self.assertEqual(before, self.counts())
        self.assertNotEqual(body["request_id"], body["execution"]["request_id"])

    def test_ready_and_terminal_inspection_in_fresh_process(self):
        task = self.ready()
        def child():
            code = "import json,sys; from noah.document_task import inspect_document_task; " \
                "p=json.loads(sys.stdin.read()); s,b=inspect_document_task(p['id'],p['token']); " \
                "print(json.dumps({'http':s,'state':b['task']['status'],'observation':" \
                "b['execution']['observation'] if b['execution'] else None}))"
            run = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                input=json.dumps({"id": task, "token": self.token}), text=True,
                capture_output=True, timeout=15, check=True)
            return json.loads(run.stdout)
        self.assertEqual(child(), {"http": 200, "state": "ready", "observation": None})
        self.assertEqual(self.run_task(task)[0], 200)
        self.assertEqual(child(), {"http": 200, "state": "completed", "observation": "verified"})

    def test_registration_readback_accepts_terminal_advancement(self):
        observed = []
        def execute(proxy, sql, params, after):
            if after and "INSERT INTO noah.tasks" in sql:
                proxy.task = str(params[0])
        def committed(proxy):
            if proxy.task:
                observed.append(self.run_task(proxy.task))
        status, body = self.register(connection_factory=lambda: Proxy(connect(), execute, committed))
        self.assertEqual(status, 201, body)
        self.assertEqual(observed[0][0], 200)
        self.assertEqual(body["task"]["status"], "completed")
        self.assertFalse(body["registration"]["execution_created"])
        self.assertEqual(body["registration"]["initial_task_status"], "ready")
        self.assertEqual(self.state(body["task_id"])[2], [1, 1])

    def test_registration_readback_accepts_running_advancement(self):
        entered, release = threading.Event(), threading.Event()
        threads, result = [], []
        def blocking():
            entered.set()
            if not release.wait(10):
                raise AssertionError("model barrier")
        def execute(proxy, sql, params, after):
            if after and "INSERT INTO noah.tasks" in sql:
                proxy.task = str(params[0])
        def committed(proxy):
            if proxy.task:
                worker = threading.Thread(target=lambda: result.append(self.run_task(proxy.task, Model(callback=blocking))))
                threads.append(worker)
                worker.start()
                if not entered.wait(10):
                    raise AssertionError("claim was not observed")
        try:
            status, body = self.register(connection_factory=lambda: Proxy(connect(), execute, committed))
            self.assertEqual(status, 201, body)
            self.assertEqual(body["task"]["status"], "running")
            self.assertEqual(body["execution"]["observation"], "unconfirmed")
            self.assertIsNone(body["result"])
            self.assertFalse(body["registration"]["execution_created"])
        finally:
            release.set()
            for worker in threads:
                worker.join(10)
                self.assertFalse(worker.is_alive())
        self.assertEqual(result[0][0], 200)

    def test_two_claims_real_postgresql_lock_order(self):
        task, model = self.ready(), Model()
        locked, release, waiting = threading.Event(), threading.Event(), threading.Event()
        pids, results = {}, []
        def first(proxy, sql, params, after):
            if after and "FOR UPDATE" in sql:
                pids["first"] = proxy.db.info.backend_pid
                locked.set()
                if not release.wait(10):
                    raise AssertionError("Task lock barrier")
        def second(proxy, sql, params, after):
            if not after and "FOR UPDATE" in sql:
                pids["second"] = proxy.db.info.backend_pid
                waiting.set()
        a = threading.Thread(target=lambda: results.append(self.run_task(task, model,
            connection_factory=lambda: Proxy(connect(), execute=first))))
        b = threading.Thread(target=lambda: results.append(self.run_task(task, model,
            connection_factory=lambda: Proxy(connect(), execute=second))))
        try:
            a.start()
            self.assertTrue(locked.wait(10))
            b.start()
            self.assertTrue(waiting.wait(10))
            deadline, proved = time.monotonic() + 2, False
            while time.monotonic() < deadline:
                with connect() as db:
                    blockers = db.execute("SELECT pg_blocking_pids(%s) AS p", (pids["second"],)).fetchone()["p"]
                if pids["first"] in blockers:
                    proved = True
                    break
                time.sleep(0.01)
            self.assertTrue(proved, "Actual Task-row blocking must be observed")
            self.assertEqual(len(self.state(task)[1]), 0)
        finally:
            release.set()
            a.join(10)
            if b.ident:
                b.join(10)
        self.assertFalse(a.is_alive() or b.is_alive())
        self.assertEqual(sorted(r[0] for r in results), [200, 409])
        self.assertEqual(len(model.calls), 1)
        self.assertEqual((len(self.state(task)[1]), self.state(task)[2]), (1, [1, 1]))

    def test_register_unknown_ack_never_recreates(self):
        def lost(proxy):
            if proxy.marked:
                raise psycopg.OperationalError("synthetic acknowledgement loss")
        def mark(proxy, sql, params, after):
            if after and "INSERT INTO noah.document_question_tasks" in sql:
                proxy.marked = True
        status, body = self.register(connection_factory=lambda: Proxy(connect(), mark, lost))
        self.assertEqual((status, body["failure"]["code"]), (503, "TASK_OUTCOME_UNKNOWN"))
        self.assertFalse(body["failure"]["retryable"])
        self.assertEqual(self.state(body["task_id"])[0]["status"], "ready")
        self.assertEqual(self.state(body["task_id"])[1], [])

    def test_claim_unknown_ack_prevents_dispatch(self):
        task, model = self.ready(), Model()
        def mark(proxy, sql, params, after):
            if after and "SET execution_id=" in sql:
                proxy.marked = True
        def lost(proxy):
            if proxy.marked:
                raise psycopg.OperationalError("synthetic claim acknowledgement loss")
        status, body = self.run_task(task, model, connection_factory=lambda: Proxy(connect(), mark, lost))
        self.assertEqual((status, body["failure"]["code"]), (503, "TASK_OUTCOME_UNKNOWN"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self.state(task)[0]["status"], "running")
        self.assertEqual(len(self.state(task)[1]), 1)
        self.assertEqual(self.run_task(task, model)[0], 409)
        self.assertEqual(model.calls, [])

    def test_definite_claim_rollback_leaves_ready(self):
        task, model = self.ready(), Model()
        def fail(proxy, sql, params, after):
            if not after and "SET execution_id=" in sql:
                raise psycopg.errors.QueryCanceled("synthetic bounded timeout")
        self.assertEqual(self.run_task(task, model, connection_factory=lambda: Proxy(connect(), fail))[0], 503)
        self.assertEqual((self.state(task)[0]["status"], self.state(task)[1]), ("ready", []))
        self.assertEqual(model.calls, [])

    def test_terminal_ack_unknown_keeps_success_and_does_not_compensate(self):
        task, model = self.ready(), Model()
        def mark(proxy, sql, params, after):
            if after and "INSERT INTO noah.document_answer_evidence" in sql:
                proxy.marked = True
        def lost(proxy):
            if proxy.marked:
                raise psycopg.OperationalError("synthetic terminal acknowledgement loss")
        status, body = self.run_task(task, model, connection_factory=lambda: Proxy(connect(), mark, lost))
        self.assertEqual((status, body["failure"]["code"]), (503, "TASK_OUTCOME_UNKNOWN"))
        row, executions, counts = self.state(task)
        self.assertEqual((row["status"], executions[0]["status"], counts), ("completed", "succeeded", [1, 1]))
        self.assertEqual(len(model.calls), 1)
        self.assertEqual(tasks.inspect_document_task(task, self.token)[0], 200)
        self.assertEqual(self.run_task(task, model)[0], 409)

    def test_evidence_rollback_is_atomic_then_definite_failure(self):
        task = self.ready()
        def fail(proxy, sql, params, after):
            if not after and "INSERT INTO noah.document_answer_evidence" in sql:
                raise psycopg.errors.CheckViolation("synthetic evidence rejection")
        status, body = self.run_task(task, connection_factory=lambda: Proxy(connect(), fail))
        self.assertEqual((status, body["failure"]["code"]), (503, "EVIDENCE_WRITE_FAILED"))
        row, executions, counts = self.state(task)
        self.assertEqual((row["status"], executions[0]["status"], counts), ("failed", "failed", [0, 0]))

    def test_failure_record_ack_unknown_is_not_retried(self):
        task, model = self.ready(), Model(error=OllamaTimeout())
        def mark(proxy, sql, params, after):
            if after and "UPDATE noah.execution_records SET status=" in sql:
                proxy.marked = True
        def lost(proxy):
            if proxy.marked:
                raise psycopg.OperationalError("synthetic failure acknowledgement loss")
        status, body = self.run_task(task, model, connection_factory=lambda: Proxy(connect(), mark, lost))
        self.assertEqual((status, body["failure"]["code"]), (503, "TASK_OUTCOME_UNKNOWN"))
        self.assertEqual(self.state(task)[0]["status"], "failed")
        self.assertEqual(len(model.calls), 1)

    def test_uncertain_worker_leaves_running_not_failed(self):
        task, model = self.ready(), Model()
        def unknown(*args):
            raise ToolOutcomeUnknown()
        status, body = self.run_task(task, model, read_runner=unknown)
        self.assertEqual((status, body["failure"]["code"]), (504, "TOOL_OUTCOME_UNKNOWN"))
        self.assertEqual(self.state(task)[0]["status"], "running")
        self.assertEqual(self.state(task)[2], [0, 0])
        self.assertEqual(model.calls, [])
        self.assertEqual(self.run_task(task, model)[0], 409)

    def test_invalid_quote_and_context_fail_without_success_evidence(self):
        task = self.ready()
        self.assertEqual(self.run_task(task, Model(output={"outcome": "supported",
            "evidence": [{"quote": "not in source"}]}))[0], 502)
        self.assertEqual(self.state(task)[2], [0, 0])
        task, model = self.ready(), Model()
        (self.root / NAME).write_text("x" * 2049, encoding="utf-8")
        self.assertEqual(self.run_task(task, model)[0], 413)
        self.assertEqual(model.calls, [])

    def test_file_change_during_model_prevents_success(self):
        task = self.ready()
        model = Model(callback=lambda: (self.root / NAME).write_bytes(b"changed"))
        status, body = self.run_task(task, model)
        self.assertEqual((status, body["failure"]["code"]), (409, "DOCUMENT_CHANGED"))
        self.assertEqual(self.state(task)[2], [0, 0])

    def test_revocation_during_model_and_after_commit(self):
        for after_commit in (False, True):
            with self.subTest(after_commit=after_commit):
                with connect() as db:
                    db.execute("INSERT INTO noah.project_memberships(project_id,user_id) VALUES(%s,%s) ON CONFLICT DO NOTHING",
                        (self.project, self.actor))
                task = self.ready()
                def revoke():
                    with connect() as db:
                        db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s",
                            (self.project, self.actor))
                def mark(proxy, sql, params, after):
                    if after and "INSERT INTO noah.document_answer_evidence" in sql:
                        proxy.marked = True
                def committed(proxy):
                    if proxy.marked:
                        revoke()
                model = Model(callback=None if after_commit else revoke)
                opts = {"connection_factory": lambda: Proxy(connect(), mark, committed)} if after_commit else {}
                status, body = self.run_task(task, model, **opts)
                self.assertEqual(status, 404)
                self.assertNotIn("result", body)
                self.assertEqual(self.state(task)[0]["status"], "completed" if after_commit else "failed")
                self.assertEqual(self.state(task)[2], [1, 1] if after_commit else [0, 0])
                self.assertEqual(tasks.inspect_document_task(task, self.token)[0], 404)

    def test_token_revalidation_after_task_lock_wait(self):
        task, model = self.ready(), Model()
        def revoke(proxy, sql, params, after):
            if after and "FOR UPDATE" in sql:
                with connect() as db:
                    db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s", (self.actor,))
        self.assertEqual(self.run_task(task, model, connection_factory=lambda: Proxy(connect(), revoke))[0], 401)
        self.assertEqual(self.state(task)[0]["status"], "ready")
        self.assertEqual(self.state(task)[1], [])
        self.assertEqual(model.calls, [])

    def test_final_list_visibility_gate_withholds_entire_page(self):
        task = self.ready()
        original = tasks._disclose
        def revoked(factory, token, actor, rows):
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (self.project,))
            return original(factory, token, actor, rows)
        with patch.object(tasks, "_disclose", side_effect=revoked):
            status, body = tasks.list_document_tasks(self.token)
        self.assertEqual(status, 404)
        self.assertNotIn("items", body)
        self.assertNotIn(task, str(body))

    def test_corrupt_or_extra_execution_is_not_selected_or_repaired(self):
        task = self.ready()
        self.assertEqual(self.run_task(task)[0], 200)
        with connect() as db:
            db.execute("""INSERT INTO noah.execution_records(id,request_id,task_id,actor_user_id,capability,status)
                VALUES(%s,%s,%s,%s,'project.documents.answer','running')""",
                (uuid4(), uuid4(), UUID(task), self.actor))
        before = self.counts()
        status, body = tasks.inspect_document_task(task, self.token)
        self.assertEqual((status, body["failure"]["code"]), (502, "TASK_RECORD_INCONSISTENT"))
        self.assertEqual(before, self.counts())

    def test_migration_reapply_preserves_rows_and_non_cascading_fks(self):
        self.ready()
        with connect() as db:
            before = db.execute("SELECT row_to_json(t) AS r FROM noah.tasks t WHERE actor_user_id=%s ORDER BY id",
                (self.actor,)).fetchall()
        initialize()
        with connect() as db:
            after = db.execute("SELECT row_to_json(t) AS r FROM noah.tasks t WHERE actor_user_id=%s ORDER BY id",
                (self.actor,)).fetchall()
            foreign = db.execute("""SELECT confdeltype FROM pg_constraint
                WHERE conrelid='noah.document_question_tasks'::regclass AND contype='f'""").fetchall()
        self.assertEqual(before, after)
        self.assertEqual([r["confdeltype"] for r in foreign], ["a"] * 3)

    def test_http_parsing_is_offline_and_strict(self):
        def handler(raw, headers=None, path="/tasks/document-questions", method="POST"):
            instance = Handler.__new__(Handler)
            instance.path = path
            instance.headers = Message()
            for name, value in headers or [("Authorization", "Bearer " + self.token)]:
                instance.headers.add_header(name, value)
            instance.headers.add_header("Content-Length", str(len(raw)))
            instance.rfile = io.BytesIO(raw)
            observed = []
            instance._respond = lambda status, body: observed.append((status, body))
            getattr(instance, "do_" + method)()
            return observed[0]
        before = self.counts()
        for raw in (b'{"question":"a","question":"b"}', b'\xff', b'{}' * 2500):
            self.assertEqual(handler(raw)[0], 400)
        self.assertEqual(handler(b'{}', [("Authorization", "Bearer " + self.token),
            ("Authorization", "Bearer " + self.token)])[0], 401)
        self.assertEqual(handler(b'{}', [("Authorization", "Bearer " + self.token),
            ("Noah-Session-Id", str(uuid4()))])[0], 400)
        self.assertEqual(before, self.counts())
        payload = {"project_id": str(self.project), "document_name": NAME, "question": "문서의 동물은?"}
        status, body = handler(json.dumps(payload, ensure_ascii=False).encode("utf-8"))
        self.assertEqual(status, 201)
        with patch("noah.__main__.run_document_task", side_effect=lambda task, data, token, **kw:
                tasks.run_document_task(task, data, token, model=Model(), root_provider=lambda _:
                    ("m18-synthetic-root", self.root), read_runner=read_document_bytes, **kw)):
            self.assertEqual(handler(b'{}', path="/tasks/" + body["task_id"] + "/run")[0], 200)
        self.assertEqual(handler(b'', path="/tasks/" + body["task_id"], method="GET")[0], 200)

    def test_process_stopped_after_claim_cannot_be_reexecuted(self):
        task = self.ready()
        marker = self.root / "owned-claimed.marker"
        code = """import json,sys,threading
from pathlib import Path
from noah.document_task import run_document_task
from noah.document_read import read_document_bytes
p=json.loads(sys.stdin.read())
class BlockedModel:
 def complete(self,*args):
  Path(p['marker']).write_bytes(b'claimed')
  threading.Event().wait(30)
  raise RuntimeError('test owner should terminate this process')
run_document_task(p['id'],{},p['token'],root_provider=lambda _:('m18-synthetic-root',Path(p['root'])),read_runner=read_document_bytes,model=BlockedModel())
"""
        child = subprocess.Popen([sys.executable, "-c", code], cwd=ROOT,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            child.stdin.write(json.dumps({"id": task, "token": self.token,
                "root": str(self.root), "marker": str(marker)}))
            child.stdin.close()
            deadline = time.monotonic() + 10
            while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
                time.sleep(0.01)
            self.assertTrue(marker.exists(), "Real child must reach the post-claim model barrier")
            self.assertEqual(self.state(task)[0]["status"], "running")
        finally:
            if child.poll() is None:
                child.terminate()
            child.wait(timeout=10)
            child.stdout.close()
            child.stderr.close()
        status, body = tasks.inspect_document_task(task, self.token)
        self.assertEqual(status, 200)
        self.assertEqual(body["execution"]["observation"], "unconfirmed")
        model = Model()
        self.assertEqual(self.run_task(task, model)[0], 409)
        self.assertEqual(model.calls, [])
        self.assertEqual((len(self.state(task)[1]), self.state(task)[2]), (1, [0, 0]))

    def test_registration_rollback_and_readback_unavailable(self):
        before = self.counts()
        def fail_insert(proxy, sql, params, after):
            if not after and "INSERT INTO noah.document_question_tasks" in sql:
                raise psycopg.errors.CheckViolation("synthetic definition failure")
        self.assertEqual(self.register(connection_factory=lambda: Proxy(connect(), fail_insert))[0], 503)
        self.assertEqual(before, self.counts())
        def fail_readback(proxy, sql, params, after):
            if not after and sql.startswith(tasks._SELECT):
                raise psycopg.OperationalError("synthetic readback unavailable")
        status, body = self.register(connection_factory=lambda: Proxy(connect(), fail_readback))
        self.assertEqual((status, body["failure"]["code"]), (503, "TASK_OUTCOME_UNKNOWN"))
        self.assertEqual((self.state(body["task_id"])[0]["status"], self.state(body["task_id"])[1]), ("ready", []))

    def test_run_preflight_and_revoked_authority_have_zero_claims(self):
        task, model = self.ready(), Model()
        before = self.counts()
        for payload in (None, [], {"run": True}):
            self.assertEqual(tasks.run_document_task(task, payload, self.token, model=model)[0], 400)
        self.assertEqual(tasks.run_document_task(task, {}, self.other_token, model=model)[0], 404)
        self.assertEqual(tasks.run_document_task(task, {}, "invalid", model=model)[0], 401)
        for option in ({"forbidden_headers": True}, {"query": "x=1"}):
            self.assertEqual(tasks.run_document_task(task, {}, self.token, model=model, **option)[0], 400)
        self.assertEqual(before, self.counts())
        with connect() as db:
            db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (self.project,))
        self.assertEqual(self.run_task(task, model)[0], 404)
        self.assertEqual(self.state(task)[1], [])
        self.assertEqual(model.calls, [])

    def test_legacy_tasks_are_not_exposed_and_owner_change_blocks_claim(self):
        legacy = uuid4()
        with connect() as db:
            db.execute("""INSERT INTO noah.tasks(id,actor_user_id,goal,status,verification_status)
                VALUES(%s,%s,'Save explicitly requested memory','running','pending')""", (legacy, self.actor))
        self.assertEqual(tasks.inspect_document_task(str(legacy), self.token)[0], 404)
        self.assertEqual(tasks.list_document_tasks(self.token)[1]["items"], [])
        task, model = self.ready(), Model()
        def transfer(proxy, sql, params, after):
            if not after and "FOR UPDATE" in sql:
                with connect() as db:
                    db.execute("UPDATE noah.tasks SET actor_user_id=%s WHERE id=%s", (self.other, UUID(task)))
        self.assertEqual(self.run_task(task, model, connection_factory=lambda: Proxy(connect(), transfer))[0], 404)
        self.assertEqual(self.state(task)[1], [])
        self.assertEqual(model.calls, [])

    def test_corrupted_persisted_quote_is_rejected_without_a_file_read(self):
        task = self.ready()
        self.assertEqual(self.run_task(task)[0], 200)
        with connect() as db:
            db.execute("""UPDATE noah.document_answer_evidence SET quotes=%s::jsonb
                WHERE execution_id=%s""", (json.dumps([{"quote": QUOTE, "start": 1, "end": 1}]),
                    self.state(task)[0]["execution_id"]))
        with patch.object(tasks, "_read", side_effect=AssertionError("file inspection forbidden")):
            status, body = tasks.inspect_document_task(task, self.token)
        self.assertEqual((status, body["failure"]["code"]), (502, "TASK_RECORD_INCONSISTENT"))
        self.assertNotIn("result", body)

    def test_success_transaction_rechecks_token_before_evidence(self):
        task, model = self.ready(), Model()
        def revoke(proxy, sql, params, after):
            if after and "FOR UPDATE" in sql and model.calls:
                with connect() as db:
                    db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s", (self.actor,))
        status, body = self.run_task(task, model, connection_factory=lambda: Proxy(connect(), revoke))
        self.assertEqual(status, 401)
        self.assertEqual((self.state(task)[0]["status"], self.state(task)[2]), ("failed", [0, 0]))

    def test_connection_failure_before_claim_is_not_a_lock_timeout(self):
        task, model, calls = self.ready(), Model(), []
        def unavailable():
            calls.append(1)
            if len(calls) == 2:
                raise psycopg.OperationalError("synthetic unavailable claim connection")
            return connect()
        status, body = self.run_task(task, model, connection_factory=unavailable)
        self.assertEqual((status, body["failure"]["code"]), (503, "DATABASE_UNAVAILABLE"))
        self.assertEqual((self.state(task)[0]["status"], self.state(task)[1]), ("ready", []))
        self.assertEqual(model.calls, [])


if __name__ == "__main__":
    unittest.main()
