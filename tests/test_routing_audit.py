"""M12 audit transitions and correlation on synthetic PostgreSQL fixtures."""

from pathlib import Path
import tempfile
import unittest
from uuid import UUID, uuid4

import psycopg

from noah.capability_route import DOCUMENT_CAPABILITY, MEMORY_ROUTE, NO_ACTION, route_read_request
from noah.db import connect
from noah.document_auto_query import answer_auto_documents
from noah.document_read import read_document_with_identity
from noah.document_tool import list_document_names
from noah.ollama import OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable
from noah.routing_audit import AuditWriteError, RoutingAudit
from noah.service import create_project, provision_user

FAKE_SETTINGS = lambda: {"POSTGRES_PASSWORD": "synthetic-password-not-real"}


class RouterModel:
    def __init__(self, proposal):
        self.proposal, self.calls = proposal, []

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        if isinstance(self.proposal, Exception):
            raise self.proposal
        return self.proposal


class DocumentModel:
    def __init__(self):
        self.calls = 0

    def complete(self, *_args):
        self.calls += 1
        return ({"outcome": "selected", "document_names": ["synthetic.md"]}
                if self.calls == 1 else
                {"outcome": "supported", "evidence": [{"quote": "otter"}]})


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


class RoutingAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.routing_audit")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"M12 PostgreSQL unavailable: {type(error).__name__}") from error
        cls.user, cls.token = provision_user("NOAH M12 synthetic actor")
        cls.project = create_project("NOAH M12 synthetic project", str(cls.user))
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _cleanup(cls):
        with connect() as db:
            db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id=%s", (cls.user,))
            for table in ("auto_document_quote_evidence", "auto_document_source_evidence",
                          "auto_document_answer_evidence"):
                db.execute(f"DELETE FROM noah.{table} WHERE execution_id IN "
                    "(SELECT id FROM noah.execution_records WHERE actor_user_id=%s)", (cls.user,))
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (cls.project,))
            db.execute("DELETE FROM noah.projects WHERE id=%s", (cls.project,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id=%s", (cls.user,))
            db.execute("DELETE FROM noah.users WHERE id=%s", (cls.user,))

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="noah-m12-synthetic-")
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        (self.root / "synthetic.md").write_text("A public synthetic otter appears.\n", encoding="utf-8")

    def route(self, route=NO_ACTION, payload=None, model=None, **kwargs):
        return route_read_request(payload or {"question": "Read a public synthetic note"},
            self.token, model=model if model is not None else RouterModel({"route": route}),
            settings_provider=FAKE_SETTINGS, **kwargs)

    def row(self, router_id):
        with connect() as db:
            return db.execute("SELECT * FROM noah.routing_audit WHERE router_id=%s",
                              (router_id,)).fetchone()

    def counts(self):
        with connect() as db:
            return tuple(db.execute(f"SELECT count(*) AS n FROM noah.{table} WHERE "
                + ("actor_user_id=%s" if table != "auto_document_answer_evidence"
                   else "execution_id IN (SELECT id FROM noah.execution_records "
                        "WHERE actor_user_id=%s)"), (self.user,)).fetchone()["n"]
                for table in ("tasks", "execution_records", "auto_document_answer_evidence"))

    def test_preflight_creates_no_audit_or_model_or_delegate(self):
        with connect() as db:
            before = db.execute("SELECT count(*) AS n FROM noah.routing_audit WHERE actor_user_id=%s",
                                (self.user,)).fetchone()["n"]
        for payload, token, expected in (
            ({"question": "Read a note"}, "not-a-token", "UNAUTHENTICATED"),
            ({"question": ""}, self.token, "INVALID_REQUEST"),
            ({"question": "Read", "project_id": str(uuid4())}, self.token, "PROJECT_NOT_FOUND"),
            ({"question": "Read", "project_id": "bad"}, self.token, "INVALID_PROJECT"),
        ):
            model, called = RouterModel({"route": MEMORY_ROUTE}), []
            status, body = route_read_request(payload, token, model=model,
                memory_runner=lambda *_: called.append("memory"), settings_provider=FAKE_SETTINGS)
            self.assertEqual(body["failure"]["code"], expected)
            self.assertNotIn("router_id", body)
            self.assertEqual((model.calls, called), ([], []))
        with connect() as db:
            after = db.execute("SELECT count(*) AS n FROM noah.routing_audit WHERE actor_user_id=%s",
                               (self.user,)).fetchone()["n"]
        self.assertEqual((before, after), (before, before))

    def test_no_action_distinct_router_ids_and_no_capability_records(self):
        before = self.counts()
        responses = [self.route() for _ in range(2)]
        ids = [body["router_id"] for status, body in responses]
        self.assertEqual(len(set(ids)), 2)
        for status, body in responses:
            self.assertEqual((status, body["routing"]["outcome"], body["routing"]["audit_status"]),
                             (200, NO_ACTION, "recorded"))
            row = self.row(body["router_id"])
            self.assertEqual((row["stage"], row["validated_route"], row["observation_class"],
                              row["dispatch_prepared"], row["delegate_result_observed"]),
                             ("observed", NO_ACTION, "no_action", False, False))
            self.assertIsNotNone(row["observed_at"])
        self.assertEqual(self.counts(), before)

    def test_memory_delegate_links_request_without_task(self):
        before, called, m3_request = self.counts(), [], uuid4()
        def runner(*_args):
            called.append(1)
            return 200, {"status": "succeeded", "request_id": str(m3_request),
                         "outcome": "no_match", "evidence": [], "answer": "Synthetic no match"}
        status, body = self.route(MEMORY_ROUTE, memory_runner=runner)
        row = self.row(body["router_id"])
        self.assertEqual((status, len(called), body["routing"]["audit_status"]), (200, 1, "recorded"))
        self.assertEqual((row["validated_route"], row["delegate_request_id"],
                          row["delegate_task_id"], row["delegate_execution_id"],
                          row["observation_class"]),
                         (MEMORY_ROUTE, m3_request, None, None, "delegate_returned"))
        self.assertEqual(self.counts(), before)

    def test_document_delegate_links_existing_one_pair(self):
        before, called = self.counts(), []
        def runner(project, payload, token):
            called.append(1)
            return answer_auto_documents(project, payload, token,
                root_provider=lambda _project: ("m12-synthetic-root", self.root),
                list_runner=list_document_names, read_runner=read_document_with_identity,
                model=DocumentModel())
        status, body = self.route(DOCUMENT_CAPABILITY,
            payload={"question": "Which animal is in the project documents?",
                     "project_id": str(self.project)}, document_runner=runner)
        self.assertEqual((status, len(called)), (200, 1))
        result, row = body["result"], self.row(body["router_id"])
        self.assertEqual((row["delegate_request_id"], row["delegate_task_id"],
                          row["delegate_execution_id"]),
                         tuple(UUID(result[key]) for key in
                               ("request_id", "task_id", "execution_id")))
        self.assertEqual((row["stage"], row["delegate_result_observed"],
                          row["observation_class"]), ("observed", True, "delegate_returned"))
        self.assertEqual(tuple(a-b for a,b in zip(self.counts(), before)), (1, 1, 1))

    def test_model_failure_is_terminal_without_delegate(self):
        cases = ((OllamaUnavailable(), "ROUTING_OLLAMA_UNAVAILABLE"),
                 (OllamaTimeout(), "ROUTING_OLLAMA_TIMEOUT"),
                 (OllamaInvalidResponse(), "ROUTING_MODEL_OUTPUT_INVALID"),
                 ({"route": "shell"}, "ROUTING_MODEL_OUTPUT_INVALID"),
                 ({"route": MEMORY_ROUTE, "extra": 1}, "ROUTING_MODEL_OUTPUT_INVALID"))
        for proposal, code in cases:
            with self.subTest(code=code):
                called = []
                status, body = self.route(model=RouterModel(proposal),
                    memory_runner=lambda *_: called.append(1))
                row = self.row(body["router_id"])
                self.assertEqual((body["failure"]["code"], row["observation_class"],
                                  row["outcome_code"], row["delegate_result_observed"], called),
                                 (code, "routing_failed", code, False, []))
                self.assertEqual(body["routing"]["audit_status"], "recorded")

    def test_argument_rejection_is_terminal_without_delegate(self):
        for route, payload, code in (
            (MEMORY_ROUTE, {"question": "Read", "project_id": str(self.project)},
             "INVALID_ROUTE_ARGUMENT"),
            (DOCUMENT_CAPABILITY, {"question": "Read"}, "PROJECT_ID_REQUIRED"),
        ):
            called = []
            status, body = self.route(route, payload, memory_runner=lambda *_: called.append(1),
                                      document_runner=lambda *_: called.append(1))
            row = self.row(body["router_id"])
            self.assertEqual((status, body["failure"]["code"], row["stage"],
                              row["observation_class"], called),
                             (400, code, "observed", "argument_rejected", []))

    def test_reservation_failures_never_call_model_or_delegate(self):
        for uncertain, after_commit, code, row_expected in (
            (False, False, "ROUTING_AUDIT_UNAVAILABLE", False),
            (True, True, "ROUTING_AUDIT_OUTCOME_UNKNOWN", True),
        ):
            with self.subTest(code=code):
                model, called = RouterModel({"route": MEMORY_ROUTE}), []
                status, body = self.route(model=model,
                    audit=FaultAudit(connect, "reserve", uncertain, after_commit),
                    memory_runner=lambda *_: called.append(1))
                self.assertEqual((status, body["failure"]["code"], model.calls, called),
                                 (503, code, [], []))
                self.assertEqual("router_id" in body, row_expected)
                if row_expected:
                    self.assertEqual(self.row(body["router_id"])["stage"], "reserved")

    def test_predelegate_update_failures_stop_dispatch(self):
        for phase, uncertain, after_commit, stage in (
            ("route_validated", False, False, "reserved"),
            ("dispatch_prepared", False, False, "route_validated"),
            ("dispatch_prepared", True, True, "dispatch_prepared"),
        ):
            with self.subTest(phase=phase, uncertain=uncertain):
                called = []
                status, body = self.route(MEMORY_ROUTE,
                    audit=FaultAudit(connect, phase, uncertain, after_commit),
                    memory_runner=lambda *_: called.append(1))
                self.assertEqual((status, body["routing"]["audit_status"], called),
                                 (503, "unconfirmed", []))
                self.assertEqual(self.row(body["router_id"])["stage"], stage)
                self.assertEqual(body["failure"]["code"],
                    "ROUTING_AUDIT_OUTCOME_UNKNOWN" if uncertain else "ROUTING_AUDIT_UNAVAILABLE")

    def test_no_action_final_failure_preserves_last_provable_stage(self):
        before = self.counts()
        for uncertain, after_commit, actual_stage in (
            (False, False, "route_validated"), (True, True, "observed")):
            status, body = self.route(audit=FaultAudit(connect, "observed", uncertain, after_commit))
            self.assertEqual((status, body["status"], body["routing"]["outcome"],
                              body["routing"]["stage"], body["routing"]["audit_status"],
                              body["result"]),
                             (503, "failed", "failed", "routing", "unconfirmed", None))
            self.assertEqual(self.row(body["router_id"])["stage"], actual_stage)
        self.assertEqual(self.counts(), before)

    def test_delegate_result_survives_final_audit_failure(self):
        request_id = uuid4()
        result = {"status": "succeeded", "request_id": str(request_id),
                  "outcome": "no_match", "evidence": [], "answer": "Synthetic no match"}
        for uncertain, after_commit, actual_stage in (
            (False, False, "dispatch_prepared"), (True, True, "observed")):
            called = []
            def runner(*_args):
                called.append(1)
                return 200, result
            status, body = self.route(MEMORY_ROUTE,
                audit=FaultAudit(connect, "observed", uncertain, after_commit),
                memory_runner=runner)
            self.assertEqual((status, body["result"], body["routing"]["audit_status"], called),
                             (200, result, "unconfirmed", [1]))
            self.assertEqual(self.row(body["router_id"])["stage"], actual_stage)

    def test_mismatched_m10_ids_are_not_trusted_for_correlation(self):
        bad = {"status": "failed", "request_id": str(uuid4()),
               "task_id": str(uuid4()), "execution_id": str(uuid4()),
               "failure": {"code": "TOOL_OUTCOME_UNKNOWN"}}
        status, body = self.route(DOCUMENT_CAPABILITY,
            payload={"question": "Read documents", "project_id": str(self.project)},
            document_runner=lambda *_: (503, bad))
        row = self.row(body["router_id"])
        self.assertEqual((status, body["result"], row["observation_class"],
                          row["delegate_request_id"], row["delegate_task_id"],
                          row["delegate_execution_id"]),
                         (503, bad, "correlation_unverified", None, None, None))

    def test_final_memory_disclosure_denial_is_recorded_without_content(self):
        def runner(*_args):
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s",
                           (self.user,))
            return 200, {"status": "succeeded", "request_id": str(uuid4()),
                         "outcome": "grounded", "answer": "Synthetic held content",
                         "evidence": []}
        try:
            status, body = self.route(MEMORY_ROUTE, memory_runner=runner)
            row = self.row(body["router_id"])
            self.assertEqual((status, body["failure"]["code"], body["result"],
                              row["observation_class"], row["outcome_code"]),
                             (401, "UNAUTHENTICATED", None, "disclosure_denied", "UNAUTHENTICATED"))
            self.assertNotIn("Synthetic held content", str(body) + str(row))
        finally:
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=NULL WHERE user_id=%s",
                           (self.user,))

    def test_audit_row_omits_private_content_and_paths(self):
        secret_question = "Synthetic private test marker Ganymede"
        status, body = self.route(payload={"question": secret_question})
        with connect() as db:
            row = db.execute("SELECT to_jsonb(a)::text AS text FROM noah.routing_audit a "
                             "WHERE router_id=%s", (body["router_id"],)).fetchone()["text"]
        for forbidden in (secret_question, self.token, "synthetic-password-not-real",
                          "A public synthetic otter appears.", str(self.root),
                          "Select exactly one read-only route"):
            self.assertNotIn(forbidden, row)
        self.assertEqual(status, 200)


if __name__ == "__main__":
    unittest.main()
