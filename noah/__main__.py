"""Local operator commands and a small authenticated HTTP entry point."""

import argparse
import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import psycopg

from .db import initialize
from .document_query import query_project_documents
from .document_answer_query import answer_project_document
from .document_selected_query import answer_selected_documents
from .document_read_query import read_project_document
from .memory_query import query_memory
from .recovery import triage_memory_writes
from .service import create_project, list_memories, read_memory, provision_user, save_memory


class Handler(BaseHTTPRequestHandler):
    def log_message(self, _format, *_args):
        # Request bodies, credentials and database errors never enter access logs.
        pass

    def _respond(self, status, body):
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _token(self):
        value = self.headers.get("Authorization", "")
        return value[7:] if value.startswith("Bearer ") else ""

    def do_POST(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        project_route = re.fullmatch(r"/projects/([^/]+)/documents/query", path)
        read_route = re.fullmatch(r"/projects/([^/]+)/documents/read", path)
        answer_route = re.fullmatch(r"/projects/([^/]+)/documents/answer", path)
        selected_route = re.fullmatch(r"/projects/([^/]+)/documents/answer-selected", path)
        if parsed.query or (path not in {"/memories", "/memories/query"}
                            and not project_route and not read_route
                            and not answer_route and not selected_route):
            self._respond(404, {"status": "failed", "message": "Not found"})
            return
        if project_route:
            operation = lambda payload, token, **_options: query_project_documents(
                project_route.group(1), payload, token)
        elif read_route:
            operation = lambda payload, token, **_options: read_project_document(
                read_route.group(1), payload, token)
        elif answer_route:
            operation = lambda payload, token, **_options: answer_project_document(
                answer_route.group(1), payload, token)
        elif selected_route:
            operation = lambda payload, token, **_options: answer_selected_documents(
                selected_route.group(1), payload, token)
        else:
            operation = save_memory if path == "/memories" else query_memory
        options = {"idempotency_key": self.headers.get("Idempotency-Key")} if path == "/memories" else {}
        if path == "/memories" and len(self.headers.get_all("Idempotency-Key", [])) > 1:
            options["idempotency_key"] = ""
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > 40000:
            status, body = operation(None, self._token(), **options)
            self._respond(status, body)
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = None
        status, body = operation(payload, self._token(), **options)
        self._respond(status, body)

    def do_GET(self):
        parsed = urlsplit(self.path)
        path = parsed.path
        if path == "/memories":
            status, body = list_memories(self._token(), parsed.query)
            self._respond(status, body)
            return
        if not path.startswith("/memories/"):
            self._respond(404, {"status": "failed", "message": "Not found"})
            return
        status, body = read_memory(path.removeprefix("/memories/"), self._token())
        self._respond(status, body)


def main():
    parser = argparse.ArgumentParser(description="NOAH local memory API")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create NOAH tables without deleting existing data")
    user = commands.add_parser("provision-user", help="Local operator only; prints a token once")
    user.add_argument("label")
    project = commands.add_parser("create-project", help="Create a project and grant its owner write access")
    project.add_argument("label")
    project.add_argument("owner_user_id")
    server = commands.add_parser("serve", help="Serve the authenticated memory API")
    server.add_argument("--port", type=int, default=8080)
    commands.add_parser("recovery-report", help="Read-only memory.save recovery triage")
    args = parser.parse_args()
    try:
        if args.command == "init":
            initialize()
            print("NOAH schema ready")
        elif args.command == "provision-user":
            user_id, token = provision_user(args.label)
            print(f"User ID: {user_id}")
            print(f"Token (shown once; keep it private): {token}")
        elif args.command == "create-project":
            print(f"Project ID: {create_project(args.label, args.owner_user_id)}")
        elif args.command == "recovery-report":
            result = triage_memory_writes()
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result["status"] == "unavailable":
                parser.exit(1)
        else:
            ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    except (OSError, ValueError, psycopg.Error) as error:
        parser.exit(1, f"Unable to complete command: {type(error).__name__}\n")


if __name__ == "__main__":
    main()
