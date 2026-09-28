"""M5 read-only triage against synthetic rows in the existing PostgreSQL."""

import unittest
from uuid import uuid4

import psycopg

from noah.db import connect
from noah.recovery import MEMORY_SAVE_GOAL, triage_memory_writes


class RecoveryTriageTests(unittest.TestCase):
    def test_database_unavailable_is_not_reported_as_empty(self):
        def unavailable():
            raise psycopg.OperationalError("synthetic connection failure with secret-like detail")

        result = triage_memory_writes(unavailable)
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["failure"]["code"], "DATABASE_UNAVAILABLE")
        self.assertNotIn("items", result)
        self.assertNotIn("secret-like", str(result))

    def test_synthetic_evidence_and_no_mutation(self):
        try:
            with connect() as db:
                db.execute("SELECT 1")
        except (psycopg.Error, OSError, ValueError) as error:
            self.skipTest(f"PostgreSQL unavailable: {type(error).__name__}")

        owner, other = uuid4(), uuid4()
        tasks, executions, memories, mappings = [], [], [], []
        cases = {}

        def add_case(db, name, task_status=None, verification=None, execution_status="running",
                     key=False, memory=False, memory_actor=None, execution_actor=None,
                     failure_code=None, verified=False, task_only=False):
            task_id, execution_id, request_id = uuid4(), uuid4(), uuid4()
            if task_status is not None:
                db.execute("""INSERT INTO noah.tasks
                    (id, actor_user_id, goal, status, verification_status)
                    VALUES (%s, %s, %s, %s, %s)""",
                    (task_id, owner, MEMORY_SAVE_GOAL, task_status, verification))
                tasks.append(task_id)
            memory_id = None
            if memory:
                memory_id = uuid4()
                db.execute("""INSERT INTO noah.memories
                    (id, owner_user_id, scope, content, created_by)
                    VALUES (%s, %s, 'user', %s, %s)""",
                    (memory_id, memory_actor or owner, "synthetic M5 " + name, memory_actor or owner))
                memories.append(memory_id)
            if not task_only:
                db.execute("""INSERT INTO noah.execution_records
                    (id, request_id, task_id, actor_user_id, capability, status,
                     failure_code, memory_id, verified_at)
                    VALUES (%s, %s, %s, %s, 'memory.save', %s, %s, %s,
                        CASE WHEN %s THEN now() ELSE NULL END)""",
                    (execution_id, request_id, task_id if task_status else None,
                     execution_actor or owner, execution_status, failure_code, memory_id, verified))
                executions.append(execution_id)
                if key:
                    digest = f"{len(mappings) + 1:064x}"
                    db.execute("""INSERT INTO noah.memory_write_requests
                        (actor_user_id, key_digest, request_fingerprint, execution_id)
                        VALUES (%s, %s, %s, %s)""", (owner, digest, "f" * 64, execution_id))
                    mappings.append(digest)
            cases[name] = {"task": task_id if task_status else None,
                           "execution": None if task_only else execution_id}

        try:
            with connect() as db:
                db.execute("INSERT INTO noah.users (id, label) VALUES (%s, %s), (%s, %s)",
                           (owner, "NOAH M5 synthetic", other, "NOAH M5 synthetic other"))
                add_case(db, "normal", "completed", "passed", "succeeded", memory=True, verified=True)
                add_case(db, "response_lost", "completed", "passed", "succeeded",
                         key=True, memory=True, verified=True)
                add_case(db, "reserved_then_stopped", "running", "pending", key=True)
                add_case(db, "running_without_key", "running", "pending")
                add_case(db, "definite_failure", "failed", "failed", "failed",
                         key=True, failure_code="DATABASE_WRITE_FAILED")
                add_case(db, "pretask_rejection", execution_status="failed",
                         failure_code="INVALID_REQUEST")
                add_case(db, "task_execution_mismatch", "completed", "passed", "running")
                add_case(db, "execution_memory_mismatch", "completed", "passed", "succeeded",
                         memory=True, memory_actor=other, verified=True)
                add_case(db, "missing_memory_ref", "completed", "passed", "succeeded",
                         verified=True)
                add_case(db, "missing_execution", "running", "pending", task_only=True)

            with connect() as db:
                before = {
                    table: db.execute(f"SELECT * FROM noah.{table} WHERE {column} = ANY(%s) ORDER BY id",
                        (ids,)).fetchall()
                    for table, column, ids in (
                        ("tasks", "id", tasks), ("execution_records", "id", executions),
                        ("memories", "id", memories))
                }
                before["mappings"] = db.execute("""SELECT * FROM noah.memory_write_requests
                    WHERE actor_user_id = %s ORDER BY key_digest""", (owner,)).fetchall()

            result = triage_memory_writes()
            self.assertEqual(result["status"], "succeeded")
            indexed = {item["execution_id"] or item["task_id"]: item for item in result["items"]}
            def case(name):
                row = cases[name]
                return indexed[str(row["execution"] or row["task"])]

            for name in ("normal", "response_lost"):
                self.assertEqual((case(name)["classification"], case(name)["outcome"]),
                                 ("verified_completed", "succeeded"))
            for name in ("reserved_then_stopped", "running_without_key"):
                self.assertEqual((case(name)["classification"], case(name)["outcome"]),
                                 ("unresolved_running", "unknown"))
            self.assertTrue(case("reserved_then_stopped")["idempotency_mapping_present"])
            self.assertFalse(case("running_without_key")["idempotency_mapping_present"])
            for name in ("definite_failure", "pretask_rejection"):
                self.assertEqual(case(name)["classification"], "recorded_failure")
            for name in ("task_execution_mismatch", "execution_memory_mismatch",
                         "missing_memory_ref", "missing_execution"):
                self.assertEqual(case(name)["classification"], "record_inconsistent")
            self.assertIn("MEMORY_ACTOR_MISMATCH", case("execution_memory_mismatch")["issues"])
            self.assertIn("MISSING_MEMORY_REFERENCE", case("missing_memory_ref")["issues"])
            self.assertIn("EXECUTION_NOT_FOUND", case("missing_execution")["issues"])
            self.assertNotIn("synthetic M5", str(result))

            with connect() as db:
                after = {
                    table: db.execute(f"SELECT * FROM noah.{table} WHERE {column} = ANY(%s) ORDER BY id",
                        (ids,)).fetchall()
                    for table, column, ids in (
                        ("tasks", "id", tasks), ("execution_records", "id", executions),
                        ("memories", "id", memories))
                }
                after["mappings"] = db.execute("""SELECT * FROM noah.memory_write_requests
                    WHERE actor_user_id = %s ORDER BY key_digest""", (owner,)).fetchall()
            self.assertEqual(before, after)
        finally:
            with connect() as db:
                db.execute("DELETE FROM noah.memory_write_requests WHERE actor_user_id = %s", (owner,))
                db.execute("DELETE FROM noah.execution_records WHERE id = ANY(%s)", (executions,))
                db.execute("DELETE FROM noah.memories WHERE id = ANY(%s)", (memories,))
                db.execute("DELETE FROM noah.tasks WHERE id = ANY(%s)", (tasks,))
                db.execute("DELETE FROM noah.users WHERE id IN (%s, %s)", (owner, other))


if __name__ == "__main__":
    unittest.main()
