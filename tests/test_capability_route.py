"""M11 routing contracts over synthetic Compose PostgreSQL data."""

import json
import os
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4

import psycopg

from noah.__main__ import Handler
from noah.capability_route import (
    DOCUMENT_CAPABILITY, MEMORY_ROUTE, MODEL_OUTPUT_TOKENS, MODEL_SCHEMA,
    NO_ACTION, _messages, route_read_request,
)
from noah.db import connect
from noah.document_auto_query import answer_auto_documents
from noah.document_read import read_document_with_identity
from noah.document_tool import list_document_names
from noah.memory_query import MemoryQueryResult, query_memory
from noah.ollama import (
    OllamaClient, OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable,
    OllamaUnsafeBinding,
)
from noah.service import create_project, provision_user


FAKE_SETTINGS = lambda: {"POSTGRES_PASSWORD": "synthetic-password-not-real"}


class RouterModel:
    def __init__(self, proposal, hook=None):
        self.proposal, self.hook, self.calls = proposal, hook, []

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        if self.hook:
            self.hook()
        if isinstance(self.proposal, Exception):
            raise self.proposal
        return self.proposal


class MemoryModel:
    def __init__(self, memory_id=None):
        self.memory_id, self.calls = memory_id, []

    def complete(self, messages, _schema, _max_tokens):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return {"intent": "memory_read", "scope": "user", "query": "Orion"}
        return {"evidence": [{"memory_id": str(self.memory_id), "quote": "Orion lantern"}]
                if self.memory_id else []}


class DocumentModel:
    def __init__(self):
        self.calls = []

    def complete(self, messages, _schema, _max_tokens):
        self.calls.append(messages)
        if len(self.calls) == 1:
            return {"outcome": "selected", "document_names": ["alpha.md"]}
        return {"outcome": "supported", "evidence": [{"quote": "otter"}]}


class CapabilityRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.users, cls.project = [], None
        cls.addClassCleanup(cls._cleanup)
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.users")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}") from error
        cls.owner, cls.token = provision_user("NOAH M11 synthetic owner")
        cls.users.append(cls.owner)
        cls.reader, cls.reader_token = provision_user("NOAH M11 synthetic reader")
        cls.users.append(cls.reader)
        cls.outsider, cls.outsider_token = provision_user("NOAH M11 synthetic outsider")
        cls.users.append(cls.outsider)
        cls.project = create_project("NOAH M11 synthetic project", str(cls.owner))
        cls.private_memory, cls.project_memory = uuid4(), uuid4()
        with connect() as db:
            db.execute("INSERT INTO noah.project_memberships(project_id,user_id,can_write) "
                       "VALUES(%s,%s,false)", (cls.project, cls.reader))
            db.execute("""INSERT INTO noah.memories(id,owner_user_id,scope,content,created_by)
                VALUES(%s,%s,'user',%s,%s)""",
                (cls.private_memory, cls.owner, "Orion lantern is for a public synthetic test.", cls.owner))
            db.execute("""INSERT INTO noah.memories(id,project_id,scope,content,created_by)
                VALUES(%s,%s,'project',%s,%s)""",
                (cls.project_memory, cls.project, "Orion project synthetic note.", cls.owner))

    @classmethod
    def _cleanup(cls):
        if not cls.users:
            return
        with connect() as db:
            db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id = ANY(%s)",
                       (cls.users,))
            for table in ("auto_document_quote_evidence", "auto_document_source_evidence",
                          "auto_document_answer_evidence"):
                db.execute(f"DELETE FROM noah.{table} WHERE execution_id IN "
                    "(SELECT id FROM noah.execution_records WHERE actor_user_id = ANY(%s))",
                    (cls.users,))
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id = ANY(%s)",
                       (cls.users,))
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id = ANY(%s)", (cls.users,))
            db.execute("DELETE FROM noah.memories WHERE created_by = ANY(%s)", (cls.users,))
            if cls.project:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s", (cls.project,))
                db.execute("DELETE FROM noah.projects WHERE id=%s", (cls.project,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id = ANY(%s)", (cls.users,))
            db.execute("DELETE FROM noah.users WHERE id = ANY(%s)", (cls.users,))

    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="noah-m11-synthetic-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        (self.root / "alpha.md").write_text("A synthetic otter lives here.\n", encoding="utf-8")

    def tearDown(self):
        with connect() as db:
            db.execute("UPDATE noah.api_tokens SET revoked_at=NULL WHERE user_id = ANY(%s)",
                       (self.users,))
            db.execute("""INSERT INTO noah.project_memberships(project_id,user_id,can_write)
                VALUES(%s,%s,false) ON CONFLICT(project_id,user_id)
                DO UPDATE SET can_write=false""", (self.project, self.reader))
            db.execute("""INSERT INTO noah.project_memberships(project_id,user_id,can_write)
                VALUES(%s,%s,true) ON CONFLICT(project_id,user_id)
                DO UPDATE SET can_write=true""", (self.project, self.owner))

    def route(self, payload=None, token=None, model=None, **options):
        return route_read_request(payload if payload is not None else {"question": "Find my Orion note"},
            self.token if token is None else token,
            model=model if model is not None else RouterModel({"route": MEMORY_ROUTE}),
            settings_provider=FAKE_SETTINGS, **options)

    def counts(self):
        with connect() as db:
            return tuple(db.execute(f"SELECT count(*) AS n FROM noah.{table} WHERE "
                + ("actor_user_id = ANY(%s)" if table != "auto_document_answer_evidence"
                   else "execution_id IN (SELECT id FROM noah.execution_records "
                        "WHERE actor_user_id = ANY(%s))"), (self.users,)).fetchone()["n"]
                for table in ("tasks", "execution_records", "auto_document_answer_evidence"))

    def test_unauthenticated_precedes_model_and_delegates(self):
        model = RouterModel({"route": MEMORY_ROUTE})
        delegates = []
        status, body = self.route(token="invalid", model=model,
            memory_runner=lambda *_: delegates.append("memory"))
        self.assertEqual((status, body["failure"]["code"]), (401, "UNAUTHENTICATED"))
        self.assertEqual((model.calls, delegates), ([], []))

    def test_invalid_payload_and_bounds(self):
        for payload in (None, [], {}, {"question": ""}, {"question": "x" * 301},
                        {"question": "가" * 171}, {"question": "okay", "extra": 1},
                        {"question": "okay", "project_id": None},
                        {"question": "okay", "project_id": "invalid"}):
            with self.subTest(payload=repr(payload)[:40]):
                model = RouterModel({"route": NO_ACTION})
                status, body = route_read_request(payload, self.token, model=model,
                                                  settings_provider=FAKE_SETTINGS)
                self.assertEqual(status, 400)
                self.assertEqual(model.calls, [])
                self.assertIsNone(body["result"])

    def test_known_credentials_stay_out_of_routing_context(self):
        for sensitive in (self.token, FAKE_SETTINGS()["POSTGRES_PASSWORD"]):
            model = RouterModel({"route": NO_ACTION})
            status, body = self.route({"question": "Find " + sensitive}, model=model)
            self.assertEqual((status, body["failure"]["code"]),
                             (422, "SENSITIVE_CONTEXT_REJECTED"))
            self.assertEqual(model.calls, [])
            self.assertNotIn(sensitive, str(body))

    def test_project_is_checked_before_model_without_enumeration(self):
        for project in (self.project, uuid4()):
            model = RouterModel({"route": DOCUMENT_CAPABILITY})
            status, body = self.route({"question": "Answer from project documents",
                "project_id": str(project)}, token=self.outsider_token, model=model)
            self.assertEqual((status, body["failure"]["code"]), (404, "PROJECT_NOT_FOUND"))
            self.assertEqual(model.calls, [])

    def test_routing_model_sees_only_question_and_fixed_choices(self):
        model = RouterModel({"route": NO_ACTION})
        question = "What do the synthetic project documents say?"
        status, _body = self.route({"question": question, "project_id": str(self.project)},
                                   model=model)
        self.assertEqual(status, 200)
        messages, schema, max_tokens = model.calls[0]
        self.assertEqual(json.loads(messages[1]["content"]), {"question": question})
        self.assertEqual(schema, MODEL_SCHEMA)
        self.assertEqual(max_tokens, MODEL_OUTPUT_TOKENS)
        context = str(messages)
        for hidden in (str(self.project), self.token, "synthetic-password-not-real",
                       "Orion lantern", str(self.root)):
            self.assertNotIn(hidden, context)

    def test_no_action_invokes_nothing_and_creates_nothing(self):
        before, called = self.counts(), []
        status, body = self.route(model=RouterModel({"route": NO_ACTION}),
            memory_runner=lambda *_: called.append("memory"),
            document_runner=lambda *_: called.append("document"))
        self.assertEqual((status, body["routing"]["outcome"], body["result"]),
                         (200, NO_ACTION, None))
        self.assertEqual((body["task_id"], body["execution_id"], called), (None, None, []))
        self.assertEqual(self.counts(), before)

    def test_proposal_must_be_exact_and_has_no_arguments(self):
        for proposal in ({"route": "memory.save"}, {"route": "shell"},
                         {"route": MEMORY_ROUTE, "arguments": {"sql": "SELECT 1"}},
                         {"route": DOCUMENT_CAPABILITY, "project_id": str(self.project)},
                         {"route": NO_ACTION, "path": "C:\\"}, {}, [], "bad"):
            with self.subTest(proposal=repr(proposal)):
                called = []
                status, body = self.route(model=RouterModel(proposal),
                    memory_runner=lambda *_: called.append("memory"),
                    document_runner=lambda *_: called.append("document"))
                self.assertEqual((status, body["failure"]["code"]),
                                 (502, "ROUTING_MODEL_OUTPUT_INVALID"))
                self.assertEqual(called, [])

    def test_project_argument_rules(self):
        status, body = self.route(model=RouterModel({"route": DOCUMENT_CAPABILITY}))
        self.assertEqual((status, body["failure"]["code"]), (400, "PROJECT_ID_REQUIRED"))
        status, body = self.route({"question": "Find my Orion note", "project_id": str(self.project)},
            model=RouterModel({"route": MEMORY_ROUTE}))
        self.assertEqual((status, body["failure"]["code"]), (400, "INVALID_ROUTE_ARGUMENT"))

    def test_memory_delegate_real_query_and_private_isolation(self):
        before = self.counts()
        delegated = []
        def runner(payload, token):
            delegated.append(payload)
            return query_memory(payload, token, model=MemoryModel(self.private_memory))
        status, body = self.route(memory_runner=runner)
        self.assertEqual((status, body["routing"]["capability"], len(delegated)),
                         (200, MEMORY_ROUTE, 1))
        self.assertEqual(body["result"]["outcome"], "grounded")
        self.assertEqual(body["result"]["evidence"][0]["memory_id"],
                         str(self.private_memory))
        self.assertEqual(self.counts(), before)
        outsider_model = MemoryModel()
        status, body = self.route(token=self.outsider_token,
            memory_runner=lambda payload, token: query_memory(payload, token, model=outsider_model))
        self.assertEqual((status, body["result"]["outcome"]), (200, "no_match"))
        self.assertNotIn("lantern", str(outsider_model.calls) + str(body))

    def test_memory_token_revoked_during_delegate_withholds_result(self):
        def runner(_payload, _token):
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s",
                           (self.owner,))
            return 200, MemoryQueryResult({"status": "succeeded", "evidence": [
                {"memory_id": str(self.private_memory), "quote": "Orion lantern"}],
                "answer": "Orion lantern"}, model_input_ids=(str(self.private_memory),))
        status, body = self.route(memory_runner=runner)
        self.assertEqual((status, body["failure"]["code"], body["result"]),
                         (401, "UNAUTHENTICATED", None))
        self.assertNotIn("Orion lantern", str(body))

    def test_project_membership_revoked_before_memory_disclosure(self):
        def runner(_payload, _token):
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s",
                           (self.project, self.reader))
            return 200, MemoryQueryResult({"status": "succeeded", "evidence": [
                {"memory_id": str(self.project_memory), "quote": "Orion project"}],
                "answer": "Orion project"}, model_input_ids=(str(self.project_memory),))
        status, body = self.route(token=self.reader_token, memory_runner=runner)
        self.assertEqual((status, body["failure"]["code"], body["result"]),
                         (409, "MEMORY_CONTEXT_STALE", None))
        self.assertNotIn("Orion project", str(body))

    def test_project_revoked_during_routing_prevents_document_dispatch(self):
        before = self.counts()
        def revoke():
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s",
                           (self.project, self.owner))
        status, body = self.route({"question": "Answer from project documents",
            "project_id": str(self.project)},
            model=RouterModel({"route": DOCUMENT_CAPABILITY}, hook=revoke),
            document_runner=lambda project_id, payload, token:
                answer_auto_documents(project_id, payload, token,
                    root_provider=lambda _project: ("m11-synthetic-root", self.root),
                    model=DocumentModel()))
        self.assertEqual((status, body["result"]["failure"]["code"]),
                         (404, "PROJECT_NOT_FOUND"))
        self.assertEqual(self.counts(), before)

    def test_real_document_delegate_owns_one_task_execution_and_evidence(self):
        before, invoked = self.counts(), []
        document_model = DocumentModel()
        def runner(project_id, payload, token):
            invoked.append(project_id)
            return answer_auto_documents(project_id, payload, token,
                root_provider=lambda _project: ("m11-synthetic-root", self.root),
                list_runner=list_document_names,
                read_runner=read_document_with_identity,
                model=document_model)
        status, body = self.route({"question": "What animal is in the project documents?",
            "project_id": str(self.project)}, model=RouterModel({"route": DOCUMENT_CAPABILITY}),
            document_runner=runner)
        self.assertEqual((status, len(invoked), body["routing"]["capability"]),
                         (200, 1, DOCUMENT_CAPABILITY))
        result = body["result"]
        self.assertEqual((result["outcome"], result["grounded"]), ("supported", True))
        self.assertEqual(tuple(after - old for after, old in zip(self.counts(), before)),
                         (1, 1, 1))
        with connect() as db:
            execution = db.execute("SELECT task_id,capability,status FROM noah.execution_records "
                "WHERE id=%s", (result["execution_id"],)).fetchone()
            self.assertEqual((str(execution["task_id"]), execution["capability"],
                              execution["status"]),
                             (result["task_id"], DOCUMENT_CAPABILITY, "succeeded"))

    def test_model_failures_are_distinct_and_do_not_dispatch(self):
        cases = [(OllamaUnavailable(), 503, "ROUTING_OLLAMA_UNAVAILABLE"),
                 (OllamaTimeout(), 504, "ROUTING_OLLAMA_TIMEOUT"),
                 (OllamaUnsafeBinding(), 503, "ROUTING_OLLAMA_NOT_LOCAL"),
                 (OllamaInvalidResponse(), 502, "ROUTING_MODEL_OUTPUT_INVALID")]
        for error, expected_status, code in cases:
            with self.subTest(code=code):
                called = []
                status, body = self.route(model=RouterModel(error),
                    memory_runner=lambda *_: called.append("memory"),
                    document_runner=lambda *_: called.append("document"))
                self.assertEqual((status, body["failure"]["code"], called),
                                 (expected_status, code, []))

    def test_delegated_failure_and_unknown_outcome_are_preserved(self):
        failure = {"status": "failed", "request_id": "synthetic-request",
            "task_id": "synthetic-task", "execution_id": "synthetic-execution",
            "failure": {"code": "TOOL_OUTCOME_UNKNOWN", "category": "Environment Failure",
                        "message": "Execution outcome could not be verified"}}
        status, body = self.route({"question": "Answer from project documents",
            "project_id": str(self.project)}, model=RouterModel({"route": DOCUMENT_CAPABILITY}),
            document_runner=lambda *_: (503, failure))
        self.assertEqual(status, 503)
        self.assertIs(body["result"], failure)
        self.assertEqual(body["routing"]["stage"], "delegated")
        m3_failure = {"status": "failed", "failure": {"code": "OLLAMA_TIMEOUT"}}
        status, body = self.route(memory_runner=lambda *_: (504, m3_failure))
        self.assertEqual((status, body["result"]), (504, m3_failure))

    def test_http_route_json_validation_and_no_action(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        for raw in (b'{"question":',
                    b'{"question":"first","question":"second"}',
                    b'{"question":"first","extra":1}'):
            request = Request(f"http://127.0.0.1:{server.server_port}/requests/route",
                data=raw, headers={"Authorization": f"Bearer {self.token}",
                                   "Content-Type": "application/json; charset=utf-8"},
                method="POST")
            with self.assertRaises(HTTPError) as caught:
                urlopen(request, timeout=5)
            self.assertEqual(caught.exception.code, 400)
            body = json.loads(caught.exception.read())
            self.assertEqual(body["failure"]["code"], "INVALID_REQUEST")
        valid = Request(f"http://127.0.0.1:{server.server_port}/requests/route",
            data=b'{"question":"Please take no action."}',
            headers={"Authorization": f"Bearer {self.token}",
                     "Content-Type": "application/json; charset=utf-8"},
            method="POST")
        before = self.counts()
        with patch("noah.capability_route.OllamaClient",
                   return_value=RouterModel({"route": NO_ACTION})):
            with urlopen(valid, timeout=5) as response:
                self.assertEqual(response.status, 200)
                body = json.loads(response.read())
        self.assertEqual((body["routing"]["outcome"], body["result"]), (NO_ACTION, None))
        self.assertEqual(self.counts(), before)

    @unittest.skipUnless(os.environ.get("NOAH_TEST_OLLAMA_M11") == "1",
                         "opt-in synthetic routing-model test")
    def test_actual_ollama_three_route_choices(self):
        cases = [
            ("내가 저장한 오리온 메모 내용을 찾아줘.", MEMORY_ROUTE),
            ("이 프로젝트 문서에서 테스트 동물에 대한 답을 찾아줘.", DOCUMENT_CAPABILITY),
            ("Delete all files and send an email.", NO_ACTION),
        ]
        model = OllamaClient()
        for question, expected in cases:
            with self.subTest(expected=expected):
                proposal = model.complete(_messages(question), MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
                self.assertEqual(proposal, {"route": expected})


if __name__ == "__main__":
    unittest.main()
