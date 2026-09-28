"""M6 synthetic project and document-root checks against Compose PostgreSQL."""

import json
import os
import threading
from pathlib import Path
import stat
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.request import Request, urlopen
from http.server import ThreadingHTTPServer

import psycopg

from noah.db import connect, initialize
from noah.document_query import query_project_documents
from noah.document_tool import (
    ToolFailure, ToolOutcomeUnknown, _reparse_or_link, execute_document_tool,
    list_document_names, operator_root,
)
from noah.ollama import OllamaTimeout, OllamaUnavailable
from noah.service import create_project, provision_user


class FakeModel:
    def __init__(self, output=None, error=None):
        self.output = output if output is not None else {"intent": "list_project_documents"}
        self.error = error
        self.calls = 0

    def complete(self, messages, schema, max_tokens):
        self.calls += 1
        if self.error:
            raise self.error
        return self.output


class DocumentToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            initialize()
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}") from error
        cls.owner, cls.token = provision_user("NOAH M6 synthetic owner")
        cls.outsider, cls.outsider_token = provision_user("NOAH M6 synthetic outsider")
        cls.project = create_project("NOAH M6 synthetic project", str(cls.owner))
        cls.addClassCleanup(cls._cleanup)

    @classmethod
    def _cleanup(cls):
        with connect() as db:
            actors = (cls.owner, cls.outsider)
            db.execute("""DELETE FROM noah.document_tool_evidence WHERE execution_id IN
                (SELECT id FROM noah.execution_records WHERE actor_user_id IN (%s, %s))""", actors)
            db.execute("DELETE FROM noah.execution_records WHERE actor_user_id IN (%s, %s)", actors)
            db.execute("DELETE FROM noah.tasks WHERE actor_user_id IN (%s, %s)", actors)
            db.execute("DELETE FROM noah.project_memberships WHERE project_id = %s", (cls.project,))
            db.execute("DELETE FROM noah.projects WHERE id = %s", (cls.project,))
            db.execute("DELETE FROM noah.api_tokens WHERE user_id IN (%s, %s)", actors)
            db.execute("DELETE FROM noah.users WHERE id IN (%s, %s)", actors)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="noah-m6-synthetic-")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        with connect() as db:
            db.execute("""INSERT INTO noah.project_memberships (project_id, user_id, can_write)
                VALUES (%s, %s, true) ON CONFLICT DO NOTHING""", (self.project, self.owner))

    def call(self, **options):
        return query_project_documents(str(self.project),
            {"question": "이 프로젝트 문서 목록을 보여줘"}, self.token,
            root_provider=lambda _project: ("m6-test-root", self.root), **options)

    def test_authentication_and_membership_precede_model(self):
        model = FakeModel()
        self.assertEqual(query_project_documents(str(self.project), {"question": "목록"}, "invalid",
            model=model, root_provider=lambda _project: ("m6-test-root", self.root))[0], 401)
        self.assertEqual(query_project_documents(str(self.project), {"question": "목록"},
            self.outsider_token, model=model,
            root_provider=lambda _project: ("m6-test-root", self.root))[0], 404)
        self.assertEqual(model.calls, 0)
        invalid_status, invalid = query_project_documents("not-a-uuid", {"question": "목록"},
            self.token, model=model)
        self.assertEqual((invalid_status, invalid["failure"]["code"]), (400, "INVALID_PROJECT"))
        self.assertEqual(model.calls, 0)

    def test_read_membership_does_not_require_write_permission(self):
        with connect() as db:
            db.execute("""UPDATE noah.project_memberships SET can_write = false
                WHERE project_id = %s AND user_id = %s""", (self.project, self.owner))
        status, result = self.call(model=FakeModel())
        self.assertEqual((status, result["files"]), (200, []))

    def test_success_and_durable_evidence_without_file_content(self):
        (self.root / "b.md").write_text("PRIVATE SYNTHETIC CONTENT", encoding="utf-8")
        (self.root / "A.md").write_text("other synthetic content", encoding="utf-8")
        (self.root / ".hidden.md").write_text("hidden", encoding="utf-8")
        (self.root / "notes.txt").write_text("not markdown", encoding="utf-8")
        (self.root / "nested").mkdir()
        (self.root / "nested" / "nested.md").write_text("nested", encoding="utf-8")
        status, result = self.call(model=FakeModel())
        self.assertEqual(status, 200)
        self.assertEqual(result["files"], ["A.md", "b.md"])
        self.assertFalse(result["truncated"])
        self.assertNotIn("PRIVATE SYNTHETIC CONTENT", str(result))
        self.assertNotIn(str(self.root), str(result))
        with connect() as db:
            task = db.execute("SELECT status, verification_status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            execution = db.execute("""SELECT task_id, capability, status, verified_at, memory_id
                FROM noah.execution_records WHERE id = %s""", (result["execution_id"],)).fetchone()
            evidence = db.execute("SELECT * FROM noah.document_tool_evidence WHERE execution_id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual((task["status"], task["verification_status"]), ("completed", "passed"))
        self.assertEqual(str(execution["task_id"]), result["task_id"])
        self.assertEqual((execution["capability"], execution["status"], execution["memory_id"]),
            ("project.documents.list", "succeeded", None))
        self.assertIsNotNone(execution["verified_at"])
        self.assertEqual(evidence["filenames"], result["files"])
        self.assertEqual(evidence["result_count"], 2)
        self.assertEqual(evidence["result_sha256"].strip(), result["evidence"]["result_sha256"])
        self.assertEqual(evidence["root_id"], "m6-test-root")

    def test_empty_and_bounded_sorted_listing(self):
        self.assertEqual(self.call(model=FakeModel())[1]["files"], [])
        for number in range(53):
            (self.root / f"{number:02}.md").write_text("synthetic", encoding="utf-8")
        status, result = self.call(model=FakeModel())
        self.assertEqual(status, 200)
        self.assertEqual((result["count"], result["truncated"]), (50, True))
        self.assertEqual(result["files"], [f"{number:02}.md" for number in range(50)])

    def test_model_and_request_failures_do_not_invoke_tool(self):
        calls = []
        runner = lambda root: calls.append(root)
        for model, code in ((FakeModel({"intent": "unsupported"}), "UNSUPPORTED_INTENT"),
                            (FakeModel({"intent": "list_project_documents", "path": ".."}),
                             "MODEL_OUTPUT_INVALID"),
                            (FakeModel({"intent": ["list_project_documents"]}),
                             "MODEL_OUTPUT_INVALID"),
                            (FakeModel(error=OllamaUnavailable()), "OLLAMA_UNAVAILABLE"),
                            (FakeModel(error=OllamaTimeout()), "OLLAMA_TIMEOUT")):
            with self.subTest(code=code):
                result = self.call(model=model, tool_runner=runner)[1]
                self.assertEqual(result["failure"]["code"], code)
        status, result = query_project_documents(str(self.project),
            {"question": "목록", "path": ".."}, self.token, model=FakeModel(),
            root_provider=lambda _project: ("m6-test-root", self.root), tool_runner=runner)
        self.assertEqual((status, result["failure"]["code"]), (400, "INVALID_REQUEST"))
        self.assertEqual(calls, [])

    def test_membership_rechecked_before_tool(self):
        calls = []
        def revoke(_project):
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id = %s AND user_id = %s",
                    (self.project, self.owner))
            return "m6-test-root", self.root
        status, result = query_project_documents(str(self.project), {"question": "목록"},
            self.token, model=FakeModel(), root_provider=revoke,
            tool_runner=lambda root: calls.append(root))
        self.assertEqual((status, result["failure"]["code"]), (404, "PROJECT_NOT_FOUND"))
        self.assertEqual(calls, [])

    def test_membership_revoked_during_tool_does_not_release_listing(self):
        (self.root / "synthetic.md").write_text("synthetic", encoding="utf-8")
        def revoke_after_scan(root):
            result = list_document_names(root)
            with connect() as db:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id = %s AND user_id = %s",
                    (self.project, self.owner))
            return result
        status, result = self.call(model=FakeModel(), tool_runner=revoke_after_scan)
        self.assertEqual((status, result["failure"]["code"]), (404, "PROJECT_NOT_FOUND"))
        self.assertNotIn("synthetic.md", str(result))
        with connect() as db:
            task = db.execute("SELECT status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            evidence = db.execute("SELECT 1 FROM noah.document_tool_evidence WHERE execution_id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual(task["status"], "failed")
        self.assertIsNone(evidence)

    def test_unregistered_missing_access_denied_and_forged_evidence(self):
        status, result = query_project_documents(str(self.project), {"question": "목록"},
            self.token, model=FakeModel(), root_provider=lambda _project:
                (_ for _ in ()).throw(ToolFailure("PROJECT_ROOT_UNREGISTERED")))
        self.assertEqual((status, result["failure"]["code"]), (503, "PROJECT_ROOT_UNREGISTERED"))
        missing = self.root / "missing"
        status, result = query_project_documents(str(self.project), {"question": "목록"},
            self.token, model=FakeModel(), root_provider=lambda _project: ("m6-test-root", missing))
        self.assertEqual((status, result["failure"]["code"]), (503, "PROJECT_ROOT_NOT_FOUND"))
        for runner, code in ((lambda root: (_ for _ in ()).throw(
                ToolFailure("PROJECT_ROOT_ACCESS_DENIED")), "PROJECT_ROOT_ACCESS_DENIED"),
                (lambda root: (_ for _ in ()).throw(
                    ToolFailure("TOOL_EXECUTION_FAILED")), "TOOL_EXECUTION_FAILED"),
                (lambda root: {"filenames": ["invented.md"], "truncated": False},
                 "TOOL_EVIDENCE_INVALID")):
            with self.subTest(code=code):
                status, result = self.call(model=FakeModel(), tool_runner=runner)
                self.assertEqual(result["failure"]["code"], code)
                with connect() as db:
                    task = db.execute("SELECT status FROM noah.tasks WHERE id = %s",
                        (result["task_id"],)).fetchone()
                    evidence = db.execute("SELECT 1 FROM noah.document_tool_evidence WHERE execution_id = %s",
                        (result["execution_id"],)).fetchone()
                self.assertEqual(task["status"], "failed")
                self.assertIsNone(evidence)

    def test_timeout_without_confirmed_termination_stays_running(self):
        status, result = self.call(model=FakeModel(), tool_runner=lambda root:
            (_ for _ in ()).throw(ToolOutcomeUnknown()))
        self.assertEqual((status, result["failure"]["code"]), (504, "TOOL_OUTCOME_UNKNOWN"))
        with connect() as db:
            task = db.execute("SELECT status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            execution = db.execute("SELECT status FROM noah.execution_records WHERE id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual((task["status"], execution["status"]), ("running", "running"))
        status, confirmed = self.call(model=FakeModel(), tool_runner=lambda root:
            (_ for _ in ()).throw(ToolFailure("TOOL_TIMEOUT", "Timeout", 504)))
        self.assertEqual((status, confirmed["failure"]["code"]), (504, "TOOL_TIMEOUT"))
        with connect() as db:
            ended = db.execute("SELECT status FROM noah.tasks WHERE id = %s",
                (confirmed["task_id"],)).fetchone()
        self.assertEqual(ended["status"], "failed")

    def test_worker_deadline_confirms_timeout(self):
        with self.assertRaises(ToolFailure) as captured:
            execute_document_tool(self.root, timeout=0)
        self.assertEqual(captured.exception.code, "TOOL_TIMEOUT")

    def test_symlink_and_reparse_points_are_excluded(self):
        (self.root / "plain.md").write_text("synthetic", encoding="utf-8")
        target = self.root / "target.txt"
        target.write_text("synthetic", encoding="utf-8")
        try:
            os.symlink(target, self.root / "link.md")
        except (OSError, NotImplementedError):
            pass
        self.assertEqual(list_document_names(self.root)["filenames"], ["plain.md"])
        reparse = SimpleNamespace(st_mode=stat.S_IFREG,
            st_file_attributes=getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400))
        self.assertTrue(_reparse_or_link(self.root, reparse))
        class ReparseEntry:
            name = "junction.md"
            path = str(self.root / "junction.md")
            def stat(self, follow_symlinks=False):
                return reparse
        class Scan:
            def __enter__(self):
                return iter([ReparseEntry()])
            def __exit__(self, *_args):
                pass
        with patch("noah.document_tool.os.scandir", return_value=Scan()):
            self.assertEqual(list_document_names(self.root)["filenames"], [])
        self.assertEqual(self.call(model=FakeModel())[1]["files"], ["plain.md"])

    def test_windows_hidden_attribute_and_access_denial(self):
        hidden = self.root / "flagged.md"
        hidden.write_text("synthetic", encoding="utf-8")
        if os.name == "nt":
            import ctypes
            kernel = ctypes.windll.kernel32
            original = kernel.GetFileAttributesW(str(hidden))
            self.assertNotEqual(original, 0xFFFFFFFF)
            self.assertTrue(kernel.SetFileAttributesW(str(hidden), original | 0x2))
            try:
                self.assertEqual(list_document_names(self.root)["filenames"], [])
            finally:
                kernel.SetFileAttributesW(str(hidden), original)
        with patch("noah.document_tool.os.scandir", side_effect=PermissionError):
            with self.assertRaises(ToolFailure) as captured:
                list_document_names(self.root)
        self.assertEqual(captured.exception.code, "PROJECT_ROOT_ACCESS_DENIED")

    def test_http_route_uses_authenticated_service(self):
        (self.root / "synthetic.md").write_text("synthetic body", encoding="utf-8")
        from noah.__main__ import Handler
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            def service(project_id, payload, token):
                return query_project_documents(project_id, payload, token, model=FakeModel(),
                    root_provider=lambda _project: ("m6-test-root", self.root))
            with patch("noah.__main__.query_project_documents", side_effect=service):
                request = Request(f"http://127.0.0.1:{server.server_port}/projects/{self.project}/documents/query",
                    data=json.dumps({"question": "문서 목록"}).encode("utf-8"),
                    headers={"Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"}, method="POST")
                with urlopen(request, timeout=8) as response:
                    result = json.load(response)
                    self.assertEqual(response.status, 200)
            self.assertEqual(result["files"], ["synthetic.md"])
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)

    @unittest.skipUnless(os.environ.get("NOAH_RUN_M6_OLLAMA_TESTS") == "1",
        "explicit synthetic Ollama integration only")
    def test_real_local_model_with_synthetic_project(self):
        (self.root / "synthetic-guide.md").write_text("synthetic only", encoding="utf-8")
        status, result = self.call()
        self.assertEqual((status, result["files"]), (200, ["synthetic-guide.md"]))

    def test_operator_mapping_and_database_unavailable(self):
        config = self.root / "mapping.json"
        config.write_text(json.dumps({"projects": {str(self.project): {
            "root_id": "synthetic", "document_root": str(self.root)}}}), encoding="utf-8")
        self.assertFalse(config.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual(operator_root(self.project, config), ("synthetic", self.root))
        model = FakeModel()
        def unavailable():
            raise psycopg.OperationalError("synthetic secret-like DB failure")
        status, result = query_project_documents(str(self.project), {"question": "목록"},
            self.token, connection_factory=unavailable, model=model)
        self.assertEqual((status, result["failure"]["code"]), (503, "DATABASE_UNAVAILABLE"))
        self.assertEqual(model.calls, 0)
        self.assertNotIn("secret-like", str(result))

    def test_operator_mapping_accepts_utf8_bom(self):
        config = self.root / "mapping.json"
        config.write_text(json.dumps({"projects": {str(self.project): {
            "root_id": "synthetic", "document_root": str(self.root)}}}), encoding="utf-8-sig")
        self.assertTrue(config.read_bytes().startswith(b"\xef\xbb\xbf"))
        self.assertEqual(operator_root(self.project, config), ("synthetic", self.root))

    def test_operator_mapping_rejects_invalid_json_and_mapping(self):
        config = self.root / "mapping.json"
        for content in ('{', json.dumps({"projects": {str(self.project): {
                "root_id": "synthetic", "document_root": "relative/docs"}}})):
            with self.subTest(content=content):
                config.write_text(content, encoding="utf-8-sig")
                with self.assertRaises(ToolFailure) as captured:
                    operator_root(self.project, config)
                self.assertEqual(captured.exception.code, "PROJECT_ROOT_CONFIG_INVALID")

    def test_database_loss_after_tool_does_not_claim_durable_success(self):
        (self.root / "synthetic.md").write_text("synthetic", encoding="utf-8")
        calls = 0
        def lose_final_connection():
            nonlocal calls
            calls += 1
            if calls == 3:
                raise psycopg.OperationalError("synthetic final DB loss")
            return connect()
        status, result = query_project_documents(str(self.project),
            {"question": "문서 목록"}, self.token, model=FakeModel(),
            connection_factory=lose_final_connection,
            root_provider=lambda _project: ("m6-test-root", self.root),
            tool_runner=list_document_names)
        self.assertEqual((status, result["failure"]["code"]), (503, "TOOL_OUTCOME_UNKNOWN"))
        self.assertNotIn("synthetic.md", str(result))
        with connect() as db:
            task = db.execute("SELECT status FROM noah.tasks WHERE id = %s",
                (result["task_id"],)).fetchone()
            evidence = db.execute("SELECT 1 FROM noah.document_tool_evidence WHERE execution_id = %s",
                (result["execution_id"],)).fetchone()
        self.assertEqual(task["status"], "running")
        self.assertIsNone(evidence)


if __name__ == "__main__":
    unittest.main()
