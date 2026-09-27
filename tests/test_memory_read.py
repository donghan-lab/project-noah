"""Second-slice HTTP and PostgreSQL checks using test-owned identities only."""

import json
import threading
import unittest
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import psycopg

from noah.__main__ import Handler
from noah.db import connect
from noah.service import create_project, list_memories, provision_user, read_memory, save_memory


class MemoryReadIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.test_users = []
        cls.project_id = None
        cls.addClassCleanup(cls._cleanup)
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.users")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"PostgreSQL unavailable: {type(error).__name__}") from error

        cls.owner_id, cls.owner_token = provision_user("NOAH slice 2 test owner")
        cls.test_users.append(cls.owner_id)
        cls.reader_id, cls.reader_token = provision_user("NOAH slice 2 test reader")
        cls.test_users.append(cls.reader_id)
        cls.outsider_id, cls.outsider_token = provision_user("NOAH slice 2 test outsider")
        cls.test_users.append(cls.outsider_id)
        cls.project_id = create_project("NOAH slice 2 test project", str(cls.owner_id))
        with connect() as db:
            db.execute(
                "INSERT INTO noah.project_memberships (project_id, user_id, can_write) VALUES (%s, %s, false)",
                (cls.project_id, cls.reader_id),
            )

        cls.personal_ids = [cls._save(cls.owner_token, "user", cls.owner_id, f"slice 2 personal {n}") for n in range(4)]
        cls.project_ids = [cls._save(cls.owner_token, "project", cls.project_id, f"slice 2 project {n}") for n in range(2)]
        cls.reader_private_id = cls._save(cls.reader_token, "user", cls.reader_id, "slice 2 reader private")
        # Equal timestamps exercise the ID tie breaker across page boundaries.
        with connect() as db:
            db.execute(
                "UPDATE noah.memories SET created_at = (SELECT created_at FROM noah.memories WHERE id = %s) WHERE created_by = %s",
                (cls.personal_ids[0], cls.owner_id),
            )

    @classmethod
    def _save(cls, token, scope, target_id, content):
        payload = {"action": "save_memory", "scope": scope, "content": content}
        payload["owner_user_id" if scope == "user" else "project_id"] = str(target_id)
        status, result = save_memory(payload, token)
        if status != 201:
            raise AssertionError(f"Test fixture save failed: {result['failure']['code']}")
        return result["evidence"]["memory_id"]

    @classmethod
    def _cleanup(cls):
        if not cls.test_users:
            return
        with connect() as db:
            for user_id in cls.test_users:
                db.execute("DELETE FROM noah.execution_records WHERE actor_user_id = %s", (user_id,))
                db.execute("DELETE FROM noah.memories WHERE created_by = %s", (user_id,))
                db.execute("DELETE FROM noah.tasks WHERE actor_user_id = %s", (user_id,))
            if cls.project_id:
                db.execute("DELETE FROM noah.project_memberships WHERE project_id = %s", (cls.project_id,))
                db.execute("DELETE FROM noah.projects WHERE id = %s", (cls.project_id,))
            for user_id in cls.test_users:
                db.execute("DELETE FROM noah.api_tokens WHERE user_id = %s", (user_id,))
                db.execute("DELETE FROM noah.users WHERE id = %s", (user_id,))

    def test_owner_list_matches_individual_read(self):
        status, result = list_memories(self.owner_token)
        self.assertEqual(status, 200)
        self.assertEqual(result["status"], "succeeded")
        self.assertEqual({item["id"] for item in result["memories"]}, set(self.personal_ids + self.project_ids))
        self.assertIsNone(result["next_cursor"])
        for item in result["memories"]:
            single_status, single = read_memory(item["id"], self.owner_token)
            self.assertEqual(single_status, 200)
            self.assertEqual(item, single["memory"])

    def test_empty_user_and_private_memories(self):
        status, empty = list_memories(self.outsider_token)
        self.assertEqual(status, 200)
        self.assertEqual(empty, {"status": "succeeded", "memories": [], "next_cursor": None})
        _, owner = list_memories(self.owner_token)
        _, reader = list_memories(self.reader_token)
        self.assertNotIn(self.reader_private_id, {item["id"] for item in owner["memories"]})
        self.assertNotIn(self.personal_ids[0], {item["id"] for item in reader["memories"]})
        self.assertEqual(read_memory(self.reader_private_id, self.owner_token)[0], 404)
        self.assertEqual(read_memory(self.personal_ids[0], self.reader_token)[0], 404)

    def test_project_membership_grants_read_without_write(self):
        with connect() as db:
            membership = db.execute(
                "SELECT can_write FROM noah.project_memberships WHERE project_id = %s AND user_id = %s",
                (self.project_id, self.reader_id),
            ).fetchone()
        self.assertFalse(membership["can_write"])
        _, reader = list_memories(self.reader_token, "scope=project")
        self.assertEqual({item["id"] for item in reader["memories"]}, set(self.project_ids))
        _, outsider = list_memories(self.outsider_token, "scope=project")
        self.assertEqual(outsider["memories"], [])
        self.assertEqual(read_memory(self.project_ids[0], self.reader_token)[0], 200)
        self.assertEqual(read_memory(self.project_ids[0], self.outsider_token)[0], 404)
        try:
            with connect() as db:
                db.execute(
                    "DELETE FROM noah.project_memberships WHERE project_id = %s AND user_id = %s",
                    (self.project_id, self.reader_id),
                )
            self.assertEqual(list_memories(self.reader_token, "scope=project")[1]["memories"], [])
            self.assertEqual(read_memory(self.project_ids[0], self.reader_token)[0], 404)
        finally:
            with connect() as db:
                db.execute(
                    "INSERT INTO noah.project_memberships (project_id, user_id, can_write) VALUES (%s, %s, false) ON CONFLICT DO NOTHING",
                    (self.project_id, self.reader_id),
                )

    def test_unauthenticated_request_is_rejected(self):
        for token in ("", "invalid token"):
            with self.subTest(token_present=bool(token)):
                status, result = list_memories(token)
                self.assertEqual(status, 401)
                self.assertEqual(result["failure"]["code"], "UNAUTHENTICATED")
                self.assertNotIn("memories", result)

    def test_stable_pagination_and_scope_filters(self):
        with connect() as db:
            rows = db.execute(
                "SELECT id, created_at FROM noah.memories WHERE created_by = %s",
                (self.owner_id,),
            ).fetchall()
        expected = [str(row["id"]) for row in sorted(rows, key=lambda row: (row["created_at"], row["id"]), reverse=True)]
        seen = []
        cursor = None
        while True:
            query = urlencode({"limit": 2, **({"cursor": cursor} if cursor else {})})
            status, result = list_memories(self.owner_token, query)
            self.assertEqual(status, 200)
            self.assertLessEqual(len(result["memories"]), 2)
            seen.extend(item["id"] for item in result["memories"])
            cursor = result["next_cursor"]
            if cursor is None:
                break
        self.assertEqual(seen, expected)
        self.assertEqual(len(seen), len(set(seen)))
        _, personal = list_memories(self.owner_token, "scope=user")
        _, project = list_memories(self.owner_token, "scope=project")
        self.assertEqual({item["id"] for item in personal["memories"]}, set(self.personal_ids))
        self.assertEqual({item["id"] for item in project["memories"]}, set(self.project_ids))

    def test_invalid_list_parameters(self):
        for query, code in (
            ("scope=all", "INVALID_SCOPE"),
            ("limit=0", "INVALID_LIMIT"),
            ("limit=101", "INVALID_LIMIT"),
            ("cursor=bad", "INVALID_CURSOR"),
            ("scope=user&scope=project", "INVALID_QUERY"),
            ("unknown=1", "INVALID_QUERY"),
        ):
            with self.subTest(query=query):
                status, result = list_memories(self.owner_token, query)
                self.assertEqual(status, 400)
                self.assertEqual(result["failure"]["code"], code)

    def test_http_list_route(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_port}/memories?scope=user&limit=2"
            with urlopen(Request(url, headers={"Authorization": f"Bearer {self.owner_token}"}), timeout=5) as response:
                self.assertEqual(response.status, 200)
                result = json.load(response)
            self.assertEqual(len(result["memories"]), 2)
            self.assertIsNotNone(result["next_cursor"])
            with self.assertRaises(HTTPError) as error:
                urlopen(url, timeout=5)
            self.assertEqual(error.exception.code, 401)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()
