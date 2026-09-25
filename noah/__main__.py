"""Local operator commands and a small authenticated HTTP entry point."""

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

import psycopg

from .db import initialize
from .service import create_project, read_memory, provision_user, save_memory


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
        if urlsplit(self.path).path != "/memories":
            self._respond(404, {"status": "failed", "message": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > 40000:
            status, body = save_memory(None, self._token())
            self._respond(status, body)
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            payload = None
        status, body = save_memory(payload, self._token())
        self._respond(status, body)

    def do_GET(self):
        path = urlsplit(self.path).path
        if not path.startswith("/memories/"):
            self._respond(404, {"status": "failed", "message": "Not found"})
            return
        status, body = read_memory(path.removeprefix("/memories/"), self._token())
        self._respond(status, body)


def main():
    parser = argparse.ArgumentParser(description="NOAH first memory vertical slice")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create NOAH tables without deleting existing data")
    user = commands.add_parser("provision-user", help="Local operator only; prints a token once")
    user.add_argument("label")
    project = commands.add_parser("create-project", help="Create a project and grant its owner write access")
    project.add_argument("label")
    project.add_argument("owner_user_id")
    server = commands.add_parser("serve", help="Serve the authenticated memory API")
    server.add_argument("--port", type=int, default=8080)
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
        else:
            ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
    except (OSError, ValueError, psycopg.Error) as error:
        parser.exit(1, f"Unable to complete command: {type(error).__name__}\n")


if __name__ == "__main__":
    main()
