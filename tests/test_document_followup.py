"""M17 deterministic contracts; run only against a disposable PostgreSQL DB."""

import hashlib
import json
import os
from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from uuid import UUID, uuid4

import psycopg

from noah.capability_route import FOLLOWUP_ROUTE, route_read_request
from noah.db import connect, initialize
from noah.document_auto import candidate_hash
from noah.document_auto_query import answer_auto_documents
from noah.document_followup_query import answer_followup_document
from noah.document_read import read_document_with_identity
from noah.document_tool import list_document_names
from noah.routing_audit import AuditWriteError, RoutingAudit
from noah.service import create_project, provision_user
from noah.session import close_session, create_session


SETTINGS = lambda: {"POSTGRES_PASSWORD": "m17-disposable-test-password"}
CONTENT = "NOAH의 공개 테스트 동물은 수달이다.\nNOAH의 공개 테스트 색상은 파란색이다.\n"
NAME = "m17-public.md"


class Model:
    def __init__(self, route=FOLLOWUP_ROUTE, outcome="supported"):
        self.route, self.outcome = route, outcome
        self.calls = []

    def complete(self, messages, schema, tokens):
        self.calls.append((messages, schema, tokens))
        if len(self.calls) == 1:
            return {"route": self.route}
        return {"outcome": self.outcome, "evidence":
            [{"quote": "NOAH의 공개 테스트 색상은 파란색이다."}]}


class FollowupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("NOAH_ISOLATED_TEST_DB") != "1":
            raise unittest.SkipTest("M17 tests require an explicit isolated DB")
        with connect() as db:
            name = db.execute("SELECT current_database() AS n").fetchone()["n"]
            if name != "noah_m17_isolated":
                raise RuntimeError("Refusing non-isolated PostgreSQL")
        initialize()

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="noah-m17-public-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / NAME).write_bytes(CONTENT.encode("utf-8"))
        self.actor, self.token = provision_user("M17 synthetic " + str(uuid4()))
        self.project = create_project("M17 synthetic " + str(uuid4()), str(self.actor))
        self.session = UUID(create_session({}, self.token)[1]["session"]["session_id"])
        self.extra_projects = []
        self.addCleanup(self._cleanup)

    def _cleanup(self):
        with connect() as db:
            db.execute("""DELETE FROM noah.document_followup_evidence
                WHERE execution_id IN (SELECT id FROM noah.execution_records
                    WHERE actor_user_id=%s)""", (self.actor,))
            for table in ("auto_document_quote_evidence", "auto_document_source_evidence",
                          "auto_document_answer_evidence"):
                db.execute(f"""DELETE FROM noah.{table} WHERE execution_id IN
                    (SELECT id FROM noah.execution_records WHERE actor_user_id=%s)""",
                    (self.actor,))
            db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id=%s", (self.actor,))
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id=%s", (self.actor,))
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id=%s", (self.actor,))
            db.execute("DELETE FROM noah.sessions WHERE owner_user_id=%s", (self.actor,))
            db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (self.project,))
            db.execute("DELETE FROM noah.projects WHERE id=%s", (self.project,))
            for project in self.extra_projects:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (project,))
                db.execute("DELETE FROM noah.projects WHERE id=%s", (project,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id=%s", (self.actor,))
            db.execute("DELETE FROM noah.users WHERE id=%s", (self.actor,))

    def _prior(self, *, project=None, selected_count=1, outcome="supported",
               stage="observed", source=True, router=None, connection=None,
               audit_reserved=False):
        project = project or self.project
        router, task, execution, request = router or uuid4(), uuid4(), uuid4(), uuid4()
        raw = CONTENT.encode("utf-8")
        digest = hashlib.sha256(raw).hexdigest()
        owned = connection is None
        db = connection if connection is not None else connect()
        try:
            db.execute("""INSERT INTO noah.tasks
                (id,actor_user_id,goal,status,verification_status)
                VALUES (%s,%s,'synthetic prior M10','completed','passed')""",
                (task, self.actor))
            db.execute("""INSERT INTO noah.execution_records
                (id,request_id,task_id,actor_user_id,capability,status,verified_at)
                VALUES (%s,%s,%s,%s,'project.documents.answer.auto','succeeded',now())""",
                (execution, request, task, self.actor))
            names = [NAME] if selected_count == 1 else [NAME, "other.md"]
            db.execute("""INSERT INTO noah.auto_document_answer_evidence
                (execution_id,project_id,root_id,candidates_observed_at,
                 candidate_names,candidate_count,truncated,candidate_sha256,
                 selection_model_called,selection_outcome,raw_candidate_names,
                 selected_names,selected_count,answer_outcome)
                VALUES (%s,%s,'m17-test-root',now(),%s::jsonb,%s,false,%s,
                    true,'selected',%s::jsonb,%s::jsonb,%s,%s)""",
                (execution, project, json.dumps(names), len(names),
                 candidate_hash(project, "m17-test-root", names),
                 json.dumps(names), json.dumps(names), selected_count, outcome))
            if source:
                db.execute("""INSERT INTO noah.auto_document_source_evidence
                    (execution_id,source_id,source_ordinal,document_name,
                     observed_at,byte_length,content_sha256,content_encoding,bom_present)
                    VALUES (%s,'D1',1,%s,now(),%s,%s,'utf-8',false)""",
                    (execution, NAME, len(raw), digest))
                db.execute("""INSERT INTO noah.auto_document_quote_evidence
                    (execution_id,quote_ordinal,source_id,quote,start_index,end_index)
                    VALUES (%s,1,'D1',%s,0,%s)""",
                    (execution, CONTENT.splitlines()[0], len(CONTENT.splitlines()[0])))
            if selected_count == 2:
                db.execute("""INSERT INTO noah.auto_document_source_evidence
                    (execution_id,source_id,source_ordinal,document_name,
                     observed_at,byte_length,content_sha256,content_encoding,bom_present)
                    VALUES (%s,'D2',2,'other.md',now(),1,%s,'utf-8',false)""",
                    (execution, "b" * 64))
            if audit_reserved:
                updated = db.execute("""UPDATE noah.routing_audit SET
                    stage='observed',validated_route='project.documents.answer.auto',
                    dispatch_prepared=true,delegate_result_observed=true,
                    delegate_capability='project.documents.answer.auto',
                    delegate_request_id=%s,delegate_task_id=%s,
                    delegate_execution_id=%s,observation_class='delegate_returned',
                    http_status=200,outcome_code=%s,observed_at=now()
                    WHERE router_id=%s AND stage='dispatch_prepared'""",
                    (request, task, execution, outcome, router))
                self.assertEqual(updated.rowcount, 1)
            elif stage == "observed":
                db.execute("""INSERT INTO noah.routing_audit
                    (router_id,actor_user_id,session_id,stage,validated_route,
                     dispatch_prepared,delegate_result_observed,delegate_capability,
                     delegate_request_id,delegate_task_id,delegate_execution_id,
                     observation_class,http_status,outcome_code,observed_at)
                    VALUES (%s,%s,%s,'observed','project.documents.answer.auto',
                        true,true,'project.documents.answer.auto',%s,%s,%s,
                        'delegate_returned',200,%s,now())""",
                    (router, self.actor, self.session, request, task, execution, outcome))
            else:
                db.execute("""INSERT INTO noah.routing_audit
                    (router_id,actor_user_id,session_id,stage,validated_route)
                    VALUES (%s,%s,%s,'route_validated','project.documents.answer.auto')""",
                    (router, self.actor, self.session))
            if owned:
                db.commit()
        finally:
            if owned:
                db.close()
        return router, execution

    def _route(self, model=None, **kwargs):
        model = model or Model()
        def runner(project, question, token, actor, session, router, **options):
            return answer_followup_document(project, question, token, actor,
                session, router, root_provider=lambda _: ("m17-test-root", self.root),
                read_runner=read_document_with_identity, **options)
        return route_read_request({"question": "그 문서의 테스트 색상은?",
            "project_id": str(self.project), "document_follow_up": True},
            self.token, model=model, settings_provider=SETTINGS,
            session_headers=[str(self.session)], followup_runner=runner, **kwargs)

    def _delta(self):
        with connect() as db:
            return tuple(db.execute(f"""SELECT count(*) AS n FROM noah.{table}
                WHERE {predicate}""", (self.actor,)).fetchone()["n"]
                for table, predicate in (("tasks", "actor_user_id=%s"),
                    ("execution_records", "actor_user_id=%s"),
                    ("routing_audit", "actor_user_id=%s")))

    def test_success_lineage_one_execution_and_fresh_quotes(self):
        old_router, old_execution = self._prior()
        model = Model()
        status, body = self._route(model)
        self.assertEqual(status, 200, body)
        result = body["result"]
        self.assertEqual((result["outcome"], result["grounded"]), ("supported", True))
        self.assertEqual(result["context_source"],
                         {"prior_router_id": str(old_router),
                          "prior_execution_id": str(old_execution)})
        self.assertEqual((result["evidence"][0]["start"],
                          result["evidence"][0]["end"]),
                         (CONTENT.index("NOAH의 공개 테스트 색상은 파란색이다."), len(CONTENT) - 1))
        self.assertEqual(self._delta(), (2, 2, 2))
        self.assertEqual(body["routing"]["audit_status"], "recorded")
        self.assertNotIn(CONTENT, str(model.calls[0]))
        self.assertNotIn(str(self.session), str(model.calls))
        self.assertNotIn(str(old_router), str(model.calls))
        with connect() as db:
            evidence = db.execute("SELECT * FROM noah.document_followup_evidence WHERE execution_id=%s",
                                  (result["execution_id"],)).fetchone()
            execution = db.execute("SELECT status,verified_at FROM noah.execution_records WHERE id=%s",
                                   (result["execution_id"],)).fetchone()
        self.assertEqual(evidence["prior_execution_id"], old_execution)
        self.assertEqual(evidence["current_router_id"], UUID(body["router_id"]))
        self.assertEqual(execution["status"], "succeeded")
        self.assertIsNotNone(execution["verified_at"])

    def test_real_m10_evidence_is_used_after_a_separate_routed_request(self):
        class M10Model:
            def __init__(self):
                self.calls = 0
            def complete(self, *_args):
                self.calls += 1
                if self.calls == 1:
                    return {"route": "project.documents.answer.auto"}
                if self.calls == 2:
                    return {"outcome": "selected", "document_names": [NAME]}
                return {"outcome": "partial", "evidence":
                    [{"quote": CONTENT.splitlines()[0]}]}
        model = M10Model()
        def m10_runner(project, payload, token):
            return answer_auto_documents(project, payload, token,
                root_provider=lambda _: ("m17-test-root", self.root),
                list_runner=list_document_names,
                read_runner=read_document_with_identity, model=model)
        status, first = route_read_request({"question": "테스트 동물은?",
            "project_id": str(self.project)}, self.token, model=model,
            document_runner=m10_runner, settings_provider=SETTINGS,
            session_headers=[str(self.session)])
        self.assertEqual(status, 200, first)
        self.assertEqual(first["result"]["outcome"], "partial")
        status, second = self._route()
        self.assertEqual(status, 200, second)
        self.assertEqual(second["result"]["context_source"],
            {"prior_router_id": first["router_id"],
             "prior_execution_id": first["result"]["execution_id"]})
        self.assertEqual(self._delta(), (2, 2, 2))

    def test_no_source_ambiguous_and_in_progress_create_no_task(self):
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_NOT_FOUND"))
        self.assertEqual(self._delta(), (0, 0, 1))
        self._prior()
        self._prior()
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_AMBIGUOUS"))
        self.assertEqual(self._delta()[:2], (2, 2))
        self._prior(stage="route_validated")
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_CONTEXT_UNCONFIRMED"))

    def test_no_action_and_preflight_do_not_execute(self):
        before = self._delta()
        status, body = self._route(model=Model(route="no_action"))
        self.assertEqual((status, body["routing"]["outcome"]), (200, "no_action"))
        self.assertEqual(self._delta(), (before[0], before[1], before[2] + 1))
        bad = {"question": "Follow up", "project_id": str(self.project),
               "document_follow_up": "true"}
        status, body = route_read_request(bad, self.token, model=Model(),
            settings_provider=SETTINGS, session_headers=[str(self.session)])
        self.assertEqual((status, body["failure"]["code"]), (400, "INVALID_REQUEST"))
        self.assertEqual(self._delta()[2], before[2] + 1)

    def test_missing_session_idempotency_and_unreadable_project_are_preflight(self):
        payload = {"question": "그 문서의 색상은?", "project_id": str(self.project),
                   "document_follow_up": True}
        before = self._delta()
        for token, headers, key, project, expected in (
                (self.token, [], None, self.project, "SESSION_ID_REQUIRED"),
                (self.token, [str(self.session)], "synthetic-key", self.project,
                 "INVALID_REQUEST"),
                (self.token, [str(self.session)], None, uuid4(),
                 "PROJECT_NOT_FOUND"),
                ("bad-token", [str(self.session)], None, self.project,
                 "UNAUTHENTICATED")):
            model = Model()
            status, body = route_read_request({**payload, "project_id": str(project)},
                token, model=model, settings_provider=SETTINGS,
                session_headers=headers, idempotency_key=key)
            self.assertIn(status, (400, 401, 404))
            self.assertEqual(body["failure"]["code"], expected)
            self.assertEqual(model.calls, [])
            self.assertEqual(self._delta(), before)

    def test_quote_free_prior_does_not_supply_context(self):
        _, execution = self._prior()
        with connect() as db:
            db.execute("DELETE FROM noah.auto_document_quote_evidence WHERE execution_id=%s",
                       (execution,))
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_NOT_FOUND"))
        self.assertEqual(self._delta()[:2], (1, 1))

    def test_close_after_reservation_does_not_cancel(self):
        self._prior()
        def close_after_choice():
            status, _ = close_session(str(self.session), {}, self.token)
            self.assertEqual(status, 200)
        class ClosingModel(Model):
            def complete(inner, messages, schema, tokens):
                if not inner.calls:
                    inner.calls.append((messages, schema, tokens))
                    close_after_choice()
                    return {"route": FOLLOWUP_ROUTE}
                return super().complete(messages, schema, tokens)
        status, body = self._route(model=ClosingModel())
        self.assertEqual(status, 200, body)

    def test_changed_source_and_final_audit_uncertainty(self):
        self._prior()
        (self.root / NAME).write_bytes(b"changed\n")
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_CHANGED"))
        self.assertEqual(self._delta()[:2], (2, 2))
        (self.root / NAME).write_bytes(CONTENT.encode("utf-8"))
        class FinalAuditFailure(RoutingAudit):
            def observed(self, *args, **kwargs):
                raise AuditWriteError(uncertain=True)
        status, body = self._route(audit=FinalAuditFailure(connect))
        self.assertEqual(status, 200, body)
        self.assertEqual(body["routing"]["audit_status"], "unconfirmed")
        self.assertEqual(body["result"]["status"], "succeeded")

    def test_other_project_does_not_make_source_ambiguous(self):
        other = create_project("M17 other synthetic " + str(uuid4()), str(self.actor))
        self.extra_projects.append(other)
        self._prior(project=other, selected_count=2)
        old_router, _ = self._prior()
        status, body = self._route()
        self.assertEqual(status, 200, body)
        self.assertEqual(body["result"]["context_source"]["prior_router_id"], str(old_router))

    def test_same_project_two_source_is_ambiguous(self):
        self._prior(selected_count=2)
        status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_AMBIGUOUS"))
        self.assertEqual(self._delta()[:2], (1, 1))

    def test_corrupt_prior_quote_is_never_used_as_answer(self):
        _, prior_execution = self._prior()
        with connect() as db:
            db.execute("""UPDATE noah.auto_document_quote_evidence SET start_index=1,
                end_index=%s WHERE execution_id=%s""",
                (len(CONTENT.splitlines()[0]) + 1, prior_execution))
        model = Model()
        status, body = self._route(model)
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (502, "FOLLOWUP_PROVENANCE_INVALID"))
        self.assertEqual(len(model.calls), 1)  # Answer model never sees bad provenance.

    def test_malformed_safe_read_identity_blocks_answer_model(self):
        self._prior()
        router = uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(router, FOLLOWUP_ROUTE)
        class AnswerOnly:
            def __init__(self):
                self.calls = 0
            def complete(self, *_args):
                self.calls += 1
                return {"outcome": "supported", "evidence": []}
        model = AnswerOnly()
        status, body = answer_followup_document(str(self.project), "그 문서의 색상은?",
            self.token, self.actor, self.session, router,
            root_provider=lambda _: ("m17-test-root", self.root),
            read_runner=lambda *_: (CONTENT.encode("utf-8"), None),
            model=model, settings_provider=SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (502, "DOCUMENT_IDENTITY_UNAVAILABLE"))
        self.assertEqual(model.calls, 0)

    def test_candidate_snapshot_after_waiting_session_lock(self):
        router = uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(router, FOLLOWUP_ROUTE)
        acquired, release = threading.Event(), threading.Event()
        failures = []
        def concurrent_m10():
            try:
                with connect() as db:
                    db.execute("SELECT id FROM noah.sessions WHERE id=%s FOR UPDATE",
                               (self.session,)).fetchone()
                    self._prior(connection=db)
                    acquired.set()
                    if not release.wait(5):
                        raise AssertionError("test lock release timed out")
            except BaseException as error:
                failures.append(error)
                acquired.set()
        worker = threading.Thread(target=concurrent_m10)
        worker.start()
        self.assertTrue(acquired.wait(5))
        self.assertFalse(failures)
        timer = threading.Timer(0.2, release.set)
        timer.start()
        try:
            class AnswerOnly:
                def complete(self, *_args):
                    return {"outcome": "supported", "evidence":
                        [{"quote": "NOAH의 공개 테스트 색상은 파란색이다."}]}
            status, body = answer_followup_document(str(self.project),
                "그 문서의 색상은?", self.token, self.actor, self.session, router,
                root_provider=lambda _: ("m17-test-root", self.root),
                read_runner=read_document_with_identity, model=AnswerOnly(),
                settings_provider=SETTINGS)
        finally:
            release.set()
            worker.join(5)
            timer.join(5)
        self.assertFalse(failures)
        self.assertEqual(status, 200, body)
        self.assertEqual(self._delta(), (2, 2, 2))

    def test_new_m10_reservation_waits_for_m17_snapshot_lock(self):
        old_router, _ = self._prior()
        current_router, new_m10_router = uuid4(), uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(current_router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(current_router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(current_router, FOLLOWUP_ROUTE)

        from noah import document_followup_query as followup
        original_classify = followup._classify
        snapshot_ready, release_snapshot = threading.Event(), threading.Event()
        m10_pid_ready = threading.Event()
        pids, results, errors = {}, {}, []

        def hold_after_snapshot(rows, project, actor):
            snapshot_ready.set()
            if not release_snapshot.wait(8):
                raise AssertionError("M17 snapshot barrier timed out")
            return original_classify(rows, project, actor)

        def m17_connection():
            db = connect()
            if "m17" not in pids:
                pids["m17"] = db.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
            return db

        def m10_connection():
            db = connect()
            if "m10" not in pids:
                pids["m10"] = db.execute("SELECT pg_backend_pid() AS pid").fetchone()["pid"]
                m10_pid_ready.set()
            return db

        class AnswerOnly:
            def complete(self, *_args):
                return {"outcome": "supported", "evidence":
                    [{"quote": "NOAH의 공개 테스트 색상은 파란색이다."}]}

        def run_m17():
            try:
                results["m17"] = answer_followup_document(str(self.project),
                    "그 문서의 색상은?", self.token, self.actor, self.session,
                    current_router, connection_factory=m17_connection,
                    root_provider=lambda _: ("m17-test-root", self.root),
                    read_runner=read_document_with_identity, model=AnswerOnly(),
                    settings_provider=SETTINGS)
            except BaseException as error:
                errors.append(error)

        def run_m10():
            try:
                m10_audit = RoutingAudit(m10_connection)
                m10_audit.reserve(new_m10_router, self.actor,
                    session_id=self.session, token=self.token)
                m10_audit.route_validated(new_m10_router, "project.documents.answer.auto")
                m10_audit.dispatch_prepared(new_m10_router, "project.documents.answer.auto")
                self._prior(router=new_m10_router, audit_reserved=True)
            except BaseException as error:
                errors.append(error)

        with patch.object(followup, "_classify", side_effect=hold_after_snapshot):
            m17 = threading.Thread(target=run_m17)
            m10 = threading.Thread(target=run_m10)
            m17.start()
            try:
                self.assertTrue(snapshot_ready.wait(5), errors)
                m10.start()
                self.assertTrue(m10_pid_ready.wait(5), errors)
                deadline = time.monotonic() + 3
                blocked = False
                while time.monotonic() < deadline:
                    with connect() as db:
                        lock = db.execute("""SELECT wait_event_type,
                            pg_blocking_pids(pid) AS blockers
                            FROM pg_stat_activity WHERE pid=%s""",
                            (pids["m10"],)).fetchone()
                    if (lock is not None and lock["wait_event_type"] == "Lock"
                            and pids["m17"] in lock["blockers"]):
                        blocked = True
                        break
                    time.sleep(0.02)
                self.assertTrue(blocked, "M10 did not wait on the M17 Session lock")
                with connect() as db:
                    absent = db.execute("SELECT 1 FROM noah.routing_audit WHERE router_id=%s",
                                        (new_m10_router,)).fetchone()
                self.assertIsNone(absent, "M10 audit committed before the M17 snapshot")
            finally:
                release_snapshot.set()
                m17.join(8)
                if m10.ident is not None:
                    m10.join(8)
        self.assertFalse(m17.is_alive())
        self.assertFalse(m10.is_alive())
        self.assertFalse(errors, errors)
        status, body = results["m17"]
        self.assertEqual(status, 200, body)
        self.assertEqual(body["context_source"]["prior_router_id"], str(old_router))
        with connect() as db:
            later = db.execute("SELECT stage FROM noah.routing_audit WHERE router_id=%s",
                               (new_m10_router,)).fetchone()
            lineage = db.execute("""SELECT prior_router_id FROM noah.document_followup_evidence
                WHERE execution_id=%s""", (body["execution_id"],)).fetchone()
        self.assertEqual(later["stage"], "observed")
        self.assertEqual(lineage["prior_router_id"], old_router)
        self.assertEqual(self._delta(), (3, 3, 3))

    def test_nonterminal_snapshot_is_not_reinterpreted_after_update(self):
        router, _ = self._prior(stage="route_validated")
        from noah import document_followup_query as followup
        original = followup._classify
        def complete_after_snapshot(rows, project, actor):
            with connect() as db:
                db.execute("""UPDATE noah.routing_audit SET stage='dispatch_prepared',
                    dispatch_prepared=true,delegate_capability='project.documents.answer.auto'
                    WHERE router_id=%s""", (router,))
            return original(rows, project, actor)
        with patch.object(followup, "_classify", side_effect=complete_after_snapshot):
            status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_CONTEXT_UNCONFIRMED"))
        self.assertEqual(self._delta()[:2], (1, 1))

    def test_reservation_commit_ack_unknown_does_not_retry(self):
        self._prior()
        router = uuid4()
        with connect() as db:
            db.execute("""INSERT INTO noah.routing_audit
                (router_id,actor_user_id,session_id,stage,validated_route,
                 dispatch_prepared,delegate_capability)
                VALUES (%s,%s,%s,'dispatch_prepared',%s,true,%s)""",
                (router, self.actor, self.session, FOLLOWUP_ROUTE, FOLLOWUP_ROUTE))
        class LostAck:
            def __init__(self, db):
                self.db = db
            def execute(self, *args):
                return self.db.execute(*args)
            def commit(self):
                self.db.commit()
                raise psycopg.OperationalError("synthetic lost acknowledgement")
            def rollback(self):
                return self.db.rollback()
            def close(self):
                return self.db.close()
        model = Model()
        status, body = answer_followup_document(str(self.project), "그 문서의 색상은?",
            self.token, self.actor, self.session, router,
            connection_factory=lambda: LostAck(connect()), model=model,
            settings_provider=SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "TOOL_OUTCOME_UNKNOWN"))
        self.assertIsNotNone(body["task_id"])
        self.assertIsNotNone(body["execution_id"])
        self.assertEqual(model.calls, [])
        self.assertEqual(self._delta()[:2], (2, 2))

    def test_incomplete_candidate_query_fails_closed_without_task(self):
        self._prior()
        router = uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(router, FOLLOWUP_ROUTE)
        class TimedQuery:
            def __init__(self, db):
                self.db = db
            def execute(self, sql, params=None):
                if "FROM noah.routing_audit a" in sql:
                    raise psycopg.errors.QueryCanceled("synthetic bounded timeout")
                return self.db.execute(sql, params)
            def commit(self):
                return self.db.commit()
            def rollback(self):
                return self.db.rollback()
            def close(self):
                return self.db.close()
        status, body = answer_followup_document(str(self.project), "그 문서의 색상은?",
            self.token, self.actor, self.session, router,
            connection_factory=lambda: TimedQuery(connect()), model=Model(),
            settings_provider=SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "FOLLOWUP_CONTEXT_UNAVAILABLE"))
        self.assertEqual((body["task_id"], body["execution_id"]), (None, None))
        self.assertEqual(self._delta()[:2], (1, 1))

    def test_permission_loss_before_answer_model(self):
        self._prior()
        from noah import document_followup_query as followup
        original = followup._read_same
        def revoke_after_read(*args):
            result = original(*args)
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s",
                           (self.project, self.actor))
            return result
        model = Model()
        with patch.object(followup, "_read_same", side_effect=revoke_after_read):
            status, body = self._route(model)
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (404, "PROJECT_NOT_FOUND"))
        self.assertEqual(len(model.calls), 1)

    def test_file_change_during_answer_model_blocks_success_evidence(self):
        self._prior()
        class ChangingModel(Model):
            def complete(inner, messages, schema, tokens):
                if len(inner.calls) == 1:
                    (self.root / NAME).write_bytes(b"changed after model input\n")
                return super().complete(messages, schema, tokens)
        status, body = self._route(model=ChangingModel())
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (409, "FOLLOWUP_SOURCE_CHANGED"))
        with connect() as db:
            row = db.execute("""SELECT count(*) AS n FROM noah.document_followup_evidence
                WHERE execution_id=%s""", (body["result"]["execution_id"],)).fetchone()
        self.assertEqual(row["n"], 0)

    def test_invalid_route_and_predelegate_audit_failure_never_run_delegate(self):
        self._prior()
        before = self._delta()
        status, body = self._route(model=Model(route="memory.save"))
        self.assertEqual((status, body["failure"]["code"]),
                         (502, "ROUTING_MODEL_OUTPUT_INVALID"))
        self.assertEqual(self._delta(), (before[0], before[1], before[2] + 1))
        class RejectDispatch(RoutingAudit):
            def dispatch_prepared(self, *_args):
                raise AuditWriteError(uncertain=False)
        status, body = self._route(audit=RejectDispatch(connect))
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "ROUTING_AUDIT_UNAVAILABLE"))
        self.assertEqual(self._delta()[:2], before[:2])

    def test_close_before_reservation_rejects_without_model(self):
        self._prior()
        self.assertEqual(close_session(str(self.session), {}, self.token)[0], 200)
        model = Model()
        before = self._delta()
        status, body = self._route(model=model)
        self.assertEqual((status, body["failure"]["code"]), (409, "SESSION_CLOSED"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self._delta(), before)

    def test_definite_final_evidence_failure_rolls_back_then_marks_failed(self):
        self._prior()
        router = uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(router, FOLLOWUP_ROUTE)
        class FailEvidence:
            def __init__(self, db):
                self.db = db
            def __enter__(self):
                self.db.__enter__()
                return self
            def __exit__(self, *args):
                return self.db.__exit__(*args)
            def execute(self, sql, params=None):
                if "INSERT INTO noah.document_followup_evidence" in sql:
                    raise psycopg.errors.CheckViolation("synthetic definite evidence failure")
                return self.db.execute(sql, params)
            def commit(self):
                return self.db.commit()
            def rollback(self):
                return self.db.rollback()
            def close(self):
                return self.db.close()
        class AnswerOnly:
            def complete(self, *_args):
                return {"outcome": "supported", "evidence":
                    [{"quote": "NOAH의 공개 테스트 색상은 파란색이다."}]}
        status, body = answer_followup_document(str(self.project), "그 문서의 색상은?",
            self.token, self.actor, self.session, router,
            connection_factory=lambda: FailEvidence(connect()),
            root_provider=lambda _: ("m17-test-root", self.root),
            read_runner=read_document_with_identity, model=AnswerOnly(),
            settings_provider=SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "EVIDENCE_WRITE_FAILED"))
        with connect() as db:
            task = db.execute("SELECT status FROM noah.tasks WHERE id=%s",
                              (body["task_id"],)).fetchone()
            execution = db.execute("SELECT status FROM noah.execution_records WHERE id=%s",
                                   (body["execution_id"],)).fetchone()
            evidence = db.execute("SELECT 1 FROM noah.document_followup_evidence WHERE execution_id=%s",
                                  (body["execution_id"],)).fetchone()
        self.assertEqual((task["status"], execution["status"], evidence),
                         ("failed", "failed", None))

    def test_final_commit_ack_unknown_keeps_canonical_success_untouched(self):
        self._prior(outcome="partial")
        router = uuid4()
        audit = RoutingAudit(connect)
        audit.reserve(router, self.actor, session_id=self.session, token=self.token)
        audit.route_validated(router, FOLLOWUP_ROUTE)
        audit.dispatch_prepared(router, FOLLOWUP_ROUTE)
        class LostFinalAck:
            def __init__(self, db):
                self.db, self.saw_evidence = db, False
            def __enter__(self):
                self.db.__enter__()
                return self
            def __exit__(self, *args):
                return self.db.__exit__(*args)
            def execute(self, sql, params=None):
                if "INSERT INTO noah.document_followup_evidence" in sql:
                    self.saw_evidence = True
                return self.db.execute(sql, params)
            def commit(self):
                self.db.commit()
                if self.saw_evidence:
                    raise psycopg.OperationalError("synthetic lost final acknowledgement")
            def rollback(self):
                return self.db.rollback()
            def close(self):
                return self.db.close()
        class AnswerOnly:
            def __init__(self):
                self.calls = 0
            def complete(self, *_args):
                self.calls += 1
                return {"outcome": "partial", "evidence":
                    [{"quote": "NOAH의 공개 테스트 색상은 파란색이다."}]}
        model = AnswerOnly()
        status, body = answer_followup_document(str(self.project), "그 문서의 색상은?",
            self.token, self.actor, self.session, router,
            connection_factory=lambda: LostFinalAck(connect()),
            root_provider=lambda _: ("m17-test-root", self.root),
            read_runner=read_document_with_identity, model=model,
            settings_provider=SETTINGS)
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "TOOL_OUTCOME_UNKNOWN"))
        self.assertEqual(model.calls, 1)
        with connect() as db:
            evidence = db.execute("SELECT outcome FROM noah.document_followup_evidence WHERE execution_id=%s",
                                  (body["execution_id"],)).fetchone()
            execution = db.execute("SELECT status FROM noah.execution_records WHERE id=%s",
                                   (body["execution_id"],)).fetchone()
        self.assertEqual((evidence["outcome"], execution["status"]),
                         ("partial", "succeeded"))

    def test_revocation_during_last_read_withholds_committed_answer(self):
        self._prior()
        from noah import document_followup_query as followup
        original = followup._read_same
        reads = 0
        def revoke_on_last_read(*args):
            nonlocal reads
            result = original(*args)
            reads += 1
            if reads == 3:
                with connect() as db:
                    db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s",
                               (self.project, self.actor))
            return result
        with patch.object(followup, "_read_same", side_effect=revoke_on_last_read):
            status, body = self._route()
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (404, "PROJECT_NOT_FOUND"))
        self.assertEqual(reads, 3)
        self.assertEqual(self._delta()[:2], (2, 2))
        with connect() as db:
            evidence = db.execute("""SELECT count(*) AS n FROM noah.document_followup_evidence
                WHERE execution_id=%s""", (body["result"]["execution_id"],)).fetchone()
        self.assertEqual(evidence["n"], 1)


if __name__ == "__main__":
    unittest.main()
