"""M16 durable Session contracts with isolated synthetic PostgreSQL owners."""

import io
import json
import os
import subprocess
import sys
import threading
import unittest
from datetime import datetime, timedelta, timezone
from email.message import Message
from uuid import UUID, uuid4

import psycopg

from noah.__main__ import Handler
from noah.capability_route import route_read_request
from noah.db import connect
from noah.routing_audit import AuditWriteError, RoutingAudit
from noah.service import provision_user
from noah.session import close_session, create_session, inspect_session


SETTINGS = lambda: {"POSTGRES_PASSWORD": "synthetic-not-a-real-password"}


class RouteModel:
    def __init__(self, callback=None):
        self.calls = []
        self.callback = callback

    def complete(self, messages, schema, max_tokens):
        self.calls.append((messages, schema, max_tokens))
        if self.callback:
            self.callback()
        return {"route": "no_action"}


class ConnectionProxy:
    def __init__(self, db, *, sql_marker=None, after_execute=None,
                 before_execute=None, fail_sql=None, lose_commit=False):
        self.db, self.sql_marker = db, sql_marker
        self.after_execute, self.before_execute = after_execute, before_execute
        self.fail_sql, self.lose_commit = fail_sql, lose_commit
        self.commit_calls = 0

    def execute(self, sql, params=None):
        if self.fail_sql and self.fail_sql in sql:
            raise psycopg.ProgrammingError("synthetic SQL failure")
        if self.sql_marker and self.sql_marker in sql and self.before_execute:
            self.before_execute()
        result = self.db.execute(sql, params)
        if self.sql_marker and self.sql_marker in sql and self.after_execute:
            self.after_execute()
        return result

    def commit(self):
        self.commit_calls += 1
        self.db.commit()
        if self.lose_commit:
            raise psycopg.OperationalError("synthetic lost acknowledgement")

    def rollback(self):
        return self.db.rollback()

    def close(self):
        return self.db.close()


class SessionContinuityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            with connect() as db:
                db.execute("SELECT 1 FROM noah.sessions")
        except (psycopg.Error, OSError, ValueError) as error:
            raise unittest.SkipTest(f"M16 PostgreSQL unavailable: {type(error).__name__}") from error

    def setUp(self):
        self.actors = []
        self.addCleanup(self._cleanup)
        self.user, self.token = self._actor()

    def _actor(self):
        user, token = provision_user("NOAH M16 synthetic " + str(uuid4()))
        self.actors.append(user)
        return user, token

    def _cleanup(self):
        with connect() as db:
            for user in self.actors:
                # All predicates are tied to the test-created actor, never private rows.
                db.execute("DELETE FROM noah.routing_audit WHERE actor_user_id=%s", (user,))
            for user in self.actors:
                db.execute("DELETE FROM noah.sessions WHERE owner_user_id=%s", (user,))
            for user in self.actors:
                db.execute("DELETE FROM noah.execution_records WHERE actor_user_id=%s", (user,))
                db.execute("DELETE FROM noah.tasks WHERE actor_user_id=%s", (user,))
                db.execute("DELETE FROM noah.api_tokens WHERE user_id=%s", (user,))
                db.execute("DELETE FROM noah.users WHERE id=%s", (user,))

    def _new_session(self, token=None):
        status, body = create_session({}, token or self.token)
        self.assertEqual(status, 201, body)
        return body["session"]["session_id"]

    def _counts(self):
        with connect() as db:
            return {name: db.execute(f"SELECT count(*) AS n FROM noah.{name} WHERE "
                    + ("actor_user_id=%s" if name != "sessions" else "owner_user_id=%s"),
                    (self.user,)).fetchone()["n"]
                    for name in ("sessions", "routing_audit", "tasks", "execution_records")}

    def _route(self, session_id=None, model=None, token=None, audit=None):
        headers = [session_id] if session_id is not None else None
        return route_read_request({"question": "A public synthetic unsupported request"},
            token if token is not None else self.token,
            model=model if model is not None else RouteModel(),
            settings_provider=SETTINGS, session_headers=headers, audit=audit)

    def test_create_auth_shape_and_minimal_schema(self):
        before = self._counts()
        self.assertEqual(create_session({}, "bad-token")[1]["failure"]["code"],
                         "UNAUTHENTICATED")
        for body, query in ((None, ""), ({"extra": 1}, ""), ({}, "x=1")):
            status, result = create_session(body, self.token, query)
            self.assertEqual((status, result["failure"]["code"]),
                             (400, "INVALID_REQUEST"))
        self.assertEqual(before, self._counts())
        status, result = create_session({}, self.token)
        self.assertEqual((status, result["status"], result["outcome"]),
                         (201, "succeeded", "created"))
        self.assertEqual(set(result["session"]),
                         {"session_id", "status", "created_at", "closed_at"})
        self.assertEqual((result["session"]["status"], result["session"]["closed_at"]),
                         ("active", None))
        self.assertEqual(result["task_id"], None)
        self.assertEqual(result["execution_id"], None)
        counts = self._counts()
        self.assertEqual((counts["sessions"], counts["routing_audit"],
                          counts["tasks"], counts["execution_records"]), (1, 0, 0, 0))
        with connect() as db:
            cols = {r["column_name"] for r in db.execute("""SELECT column_name
                FROM information_schema.columns WHERE table_schema='noah'
                AND table_name='sessions'""")}
            self.assertEqual(cols, {"id", "owner_user_id", "created_at", "closed_at"})

    def test_owner_non_enumeration_and_canonical_ids(self):
        session_id = self._new_session()
        _, other_token = self._actor()
        foreign = inspect_session(session_id, other_token)
        missing = inspect_session(str(uuid4()), other_token)
        self.assertEqual(foreign[0], 404)
        self.assertEqual(missing[0], 404)
        self.assertEqual(foreign[1]["failure"], missing[1]["failure"])
        self.assertEqual(inspect_session(session_id.upper(), self.token)[1]["failure"]["code"],
                         "INVALID_REQUEST")
        self.assertEqual(close_session("not-a-uuid", {}, self.token)[1]["failure"]["code"],
                         "INVALID_REQUEST")
        self.assertEqual(inspect_session(session_id, "bad-token")[0], 401)
        with connect() as db:
            db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s",
                       (self.user,))
        self.assertEqual(close_session(session_id, {}, self.token)[0], 401)

    def test_close_repeat_and_retained_references(self):
        session_id = self._new_session()
        model = RouteModel()
        routed = self._route(session_id, model=model)
        self.assertEqual(routed[0], 200)
        router_id = routed[1]["router_id"]
        before = self._counts()
        status, result = close_session(session_id, {}, self.token)
        self.assertEqual((status, result["outcome"], result["session"]["status"]),
                         (200, "closed", "closed"))
        closed_at = result["session"]["closed_at"]
        self.assertIsNotNone(closed_at)
        repeated = close_session(session_id, {}, self.token)
        self.assertEqual((repeated[0], repeated[1]["outcome"]), (200, "already_closed"))
        self.assertEqual(repeated[1]["session"]["closed_at"], closed_at)
        self.assertNotEqual(repeated[1]["request_id"], result["request_id"])
        self.assertEqual(before, self._counts())
        read = inspect_session(session_id, self.token)
        self.assertEqual(read[1]["session"]["status"], "closed")
        self.assertEqual(read[1]["interactions"][0]["router_id"], router_id)
        self.assertEqual(set(read[1]["interactions"][0]), {"router_id", "associated_at"})
        denied_model = RouteModel()
        denied = self._route(session_id, model=denied_model)
        self.assertEqual((denied[0], denied[1]["failure"]["code"]),
                         (409, "SESSION_CLOSED"))
        self.assertEqual(denied_model.calls, [])
        self.assertEqual(before, self._counts())

    def test_inspection_bounded_keyset_and_cursor_isolation(self):
        first, second = self._new_session(), self._new_session()
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        inserted = []
        with connect() as db:
            for i in range(25):
                router, stamp = uuid4(), start + timedelta(seconds=i // 2)
                db.execute("""INSERT INTO noah.routing_audit
                    (router_id,actor_user_id,stage,session_id,created_at)
                    VALUES(%s,%s,'reserved',%s,%s)""",
                    (router, self.user, first, stamp))
                inserted.append((stamp, router))
            db.execute("""INSERT INTO noah.routing_audit
                (router_id,actor_user_id,stage,session_id)
                VALUES(%s,%s,'reserved',%s)""", (uuid4(), self.user, second))
        expected = [str(router) for _, router in sorted(inserted, reverse=True)]
        status, page1 = inspect_session(first, self.token)
        self.assertEqual(status, 200)
        self.assertEqual(len(page1["interactions"]), 20)
        self.assertEqual([r["router_id"] for r in page1["interactions"]], expected[:20])
        self.assertIsNotNone(page1["next_cursor"])
        page2 = inspect_session(first, self.token, "cursor=" + page1["next_cursor"])[1]
        self.assertEqual([r["router_id"] for r in page2["interactions"]], expected[20:])
        self.assertIsNone(page2["next_cursor"])
        self.assertEqual(inspect_session(second, self.token,
            "cursor=" + page1["next_cursor"])[1]["failure"]["code"], "INVALID_REQUEST")
        self.assertEqual(len(inspect_session(first, self.token, "limit=1")[1]["interactions"]), 1)
        self.assertEqual(len(inspect_session(first, self.token, "limit=100")[1]["interactions"]), 25)
        for query in ("limit=0", "limit=101", "limit=abc", "limit=1&limit=2",
                      "unknown=1", "cursor=bad!"):
            self.assertEqual(inspect_session(first, self.token, query)[1]["failure"]["code"],
                             "INVALID_REQUEST")

    def test_inspection_rechecks_audit_actor_not_only_session_reference(self):
        session_id = self._new_session()
        other_user, _ = self._actor()
        foreign_router = uuid4()
        # A malformed association from another writer must not become visible
        # to the Session owner merely because its FK points at this Session.
        with connect() as db:
            db.execute("""INSERT INTO noah.routing_audit
                (router_id,actor_user_id,stage,session_id)
                VALUES(%s,%s,'reserved',%s)""",
                (foreign_router, other_user, session_id))
        result = inspect_session(session_id, self.token)[1]
        self.assertEqual(result["interactions"], [])
        self.assertIsNone(result["next_cursor"])
        self.assertNotIn(str(foreign_router), str(result))

    def test_two_scoped_routes_isolation_legacy_and_model_input(self):
        first, second = self._new_session(), self._new_session()
        model = RouteModel()
        before = self._counts()
        routed = [self._route(first, model=model), self._route(first, model=model),
                  self._route(second, model=model), self._route(model=model)]
        self.assertTrue(all(status == 200 for status, _ in routed), routed)
        ids = [body["router_id"] for _, body in routed]
        self.assertEqual(len(set(ids)), 4)
        self.assertEqual(len(inspect_session(first, self.token)[1]["interactions"]), 2)
        self.assertEqual(len(inspect_session(second, self.token)[1]["interactions"]), 1)
        with connect() as db:
            rows = db.execute("""SELECT router_id,session_id FROM noah.routing_audit
                WHERE actor_user_id=%s""", (self.user,)).fetchall()
        bound = {str(r["router_id"]): str(r["session_id"]) if r["session_id"] else None
                 for r in rows}
        self.assertEqual([bound[i] for i in ids], [first, first, second, None])
        self.assertEqual(self._counts()["tasks"], before["tasks"])
        self.assertEqual(self._counts()["execution_records"], before["execution_records"])
        for messages, schema, _ in model.calls:
            self.assertNotIn(first, str(messages))
            self.assertNotIn(second, str(messages))
            self.assertNotIn(str(self.user), str(messages))
            self.assertEqual(set(schema["properties"]), {"route"})

    def test_header_rejection_and_authentication_order(self):
        owned = self._new_session()
        foreign_user, _ = self._actor()
        with connect() as db:
            foreign = uuid4()
            db.execute("INSERT INTO noah.sessions(id,owner_user_id) VALUES(%s,%s)",
                       (foreign, foreign_user))
        before = self._counts()["routing_audit"]
        for headers, code in (([""], "INVALID_SESSION_ID"),
                              ([owned.upper()], "INVALID_SESSION_ID"),
                              ([owned, owned], "INVALID_SESSION_ID"),
                              ([owned + "," + owned], "INVALID_SESSION_ID"),
                              ([str(foreign)], "SESSION_NOT_FOUND"),
                              ([str(uuid4())], "SESSION_NOT_FOUND")):
            model = RouteModel()
            status, body = route_read_request({"question": "Read synthetic"}, self.token,
                model=model, settings_provider=SETTINGS, session_headers=headers)
            self.assertEqual(body["failure"]["code"], code)
            self.assertEqual(model.calls, [])
            self.assertEqual(self._counts()["routing_audit"], before)
        status, body = route_read_request({"question": "Read synthetic"}, "bad-token",
            model=RouteModel(), settings_provider=SETTINGS, session_headers=["bad"])
        self.assertEqual((status, body["failure"]["code"]), (401, "UNAUTHENTICATED"))

    def test_http_handler_detects_duplicate_session_headers(self):
        owned = self._new_session()
        handler = Handler.__new__(Handler)
        handler.path = "/requests/route"
        handler.headers = Message()
        handler.headers.add_header("Authorization", "Bearer " + self.token)
        handler.headers.add_header("Noah-Session-Id", owned)
        handler.headers.add_header("Noah-Session-Id", owned)
        payload = json.dumps({"question": "Read synthetic"}).encode("utf-8")
        handler.headers.add_header("Content-Length", str(len(payload)))
        handler.rfile = io.BytesIO(payload)
        observed = []
        handler._respond = lambda status, body: observed.append((status, body))
        handler.do_POST()
        self.assertEqual(len(observed), 1)
        self.assertEqual((observed[0][0], observed[0][1]["failure"]["code"]),
                         (400, "INVALID_SESSION_ID"))
        self.assertEqual(self._counts()["routing_audit"], 0)

    def test_token_revoked_between_auth_and_reservation(self):
        session_id = self._new_session()
        model = RouteModel()
        def revoke_then_settings():
            with connect() as db:
                db.execute("UPDATE noah.api_tokens SET revoked_at=now() WHERE user_id=%s",
                           (self.user,))
            return SETTINGS()
        status, body = route_read_request({"question": "Read synthetic"}, self.token,
            model=model, settings_provider=revoke_then_settings,
            session_headers=[session_id])
        self.assertEqual((status, body["failure"]["code"]), (401, "UNAUTHENTICATED"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self._counts()["routing_audit"], 0)

    def test_owner_changed_after_preflight_is_denied_at_reservation(self):
        session_id = self._new_session()
        other_user, _ = self._actor()
        model = RouteModel()
        def move_owner_then_settings():
            with connect() as db:
                db.execute("UPDATE noah.sessions SET owner_user_id=%s WHERE id=%s",
                           (other_user, session_id))
            return SETTINGS()
        status, body = route_read_request({"question": "Read synthetic"}, self.token,
            model=model, settings_provider=move_owner_then_settings,
            session_headers=[session_id])
        self.assertEqual((status, body["failure"]["code"]),
                         (404, "SESSION_NOT_FOUND"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self._counts()["routing_audit"], 0)

    def test_close_wins_before_reservation_with_barrier(self):
        session_id = self._new_session()
        locked, attempted, release = (threading.Event(), threading.Event(),
                                      threading.Event())
        result, routed = [], []
        def close_factory():
            return ConnectionProxy(connect(), sql_marker="FOR UPDATE",
                after_execute=lambda: (locked.set(), release.wait(10)))
        def audit_factory():
            return ConnectionProxy(connect(), sql_marker="FOR UPDATE",
                                   before_execute=attempted.set)
        def closing():
            result.append(close_session(session_id, {}, self.token,
                                        connection_factory=close_factory))
        def routing():
            routed.append(self._route(session_id, model=model,
                audit=RoutingAudit(audit_factory)))
        model = RouteModel()
        close_thread = threading.Thread(target=closing)
        route_thread = threading.Thread(target=routing)
        close_thread.start()
        try:
            self.assertTrue(locked.wait(10))
            route_thread.start()
            self.assertTrue(attempted.wait(10))
            # Close holds the row lock before the route attempts to take it.
            release.set()
            close_thread.join(10)
            route_thread.join(10)
            self.assertFalse(close_thread.is_alive())
            self.assertFalse(route_thread.is_alive())
            self.assertEqual(result[0][1]["outcome"], "closed")
            status, body = routed[0]
            self.assertEqual((status, body["failure"]["code"]),
                             (409, "SESSION_CLOSED"))
            self.assertEqual(model.calls, [])
            self.assertEqual(self._counts()["routing_audit"], 0)
        finally:
            release.set()
            close_thread.join(10)
            if route_thread.ident is not None:
                route_thread.join(10)

    def test_reservation_wins_then_close_does_not_cancel(self):
        session_id = self._new_session()
        locked, close_attempted, release = (threading.Event(), threading.Event(),
                                            threading.Event())
        routed, closures = [], []
        def audit_factory():
            return ConnectionProxy(connect(), sql_marker="FOR UPDATE",
                after_execute=lambda: (locked.set(), release.wait(10)))
        def close_factory():
            return ConnectionProxy(connect(), sql_marker="FOR UPDATE",
                                   before_execute=close_attempted.set)
        def routing():
            routed.append(self._route(session_id,
                audit=RoutingAudit(audit_factory)))
        def closing():
            closures.append(close_session(session_id, {}, self.token,
                                          connection_factory=close_factory))
        route_thread = threading.Thread(target=routing)
        close_thread = threading.Thread(target=closing)
        route_thread.start()
        try:
            self.assertTrue(locked.wait(10))
            close_thread.start()
            self.assertTrue(close_attempted.wait(10))
            # Reservation owns the row lock; its commit must precede close.
            release.set()
            route_thread.join(10)
            close_thread.join(10)
            self.assertFalse(route_thread.is_alive())
            self.assertFalse(close_thread.is_alive())
        finally:
            release.set()
            route_thread.join(10)
            if close_thread.ident is not None:
                close_thread.join(10)
        status, body = routed[0]
        self.assertEqual(status, 200)
        self.assertEqual(body["routing"]["outcome"], "no_action")
        self.assertEqual(closures[0][1]["outcome"], "closed")
        with connect() as db:
            row = db.execute("""SELECT stage,session_id FROM noah.routing_audit
                WHERE router_id=%s""", (UUID(body["router_id"]),)).fetchone()
        self.assertEqual((row["stage"], str(row["session_id"])), ("observed", session_id))

    def test_definite_and_uncertain_create_close(self):
        failed = create_session({}, self.token, connection_factory=lambda:
            ConnectionProxy(connect(), fail_sql="INSERT INTO noah.sessions"))
        self.assertEqual((failed[0], failed[1]["failure"]["code"]),
                         (503, "SESSION_STORAGE_UNAVAILABLE"))
        self.assertEqual(self._counts()["sessions"], 0)
        wrappers = []
        def uncertain_factory():
            wrapper = ConnectionProxy(connect(), lose_commit=True)
            wrappers.append(wrapper)
            return wrapper
        created = create_session({}, self.token, connection_factory=uncertain_factory)
        self.assertEqual(created[0], 503)
        self.assertEqual((created[1]["status"], created[1]["outcome"],
                          created[1]["failure"]["code"]),
                         ("failed", "unknown", "SESSION_OUTCOME_UNKNOWN"))
        self.assertEqual((created[1]["task_id"], created[1]["execution_id"]), (None, None))
        self.assertEqual(created[1]["failure"]["category"], "Environment Failure")
        self.assertEqual(created[1]["failure"]["retryable"], False)
        self.assertEqual(created[1]["failure"]["recoverable"], True)
        self.assertEqual(created[1]["failure"]["message"],
                         "Session outcome cannot be confirmed")
        self.assertNotIn("session", created[1])
        session_id = created[1]["session_id"]
        self.assertEqual(wrappers[0].commit_calls, 1)
        self.assertEqual(inspect_session(session_id, self.token)[1]["session"]["status"],
                         "active")
        definite_close = close_session(session_id, {}, self.token,
            connection_factory=lambda: ConnectionProxy(connect(), fail_sql="UPDATE noah.sessions"))
        self.assertEqual((definite_close[0], definite_close[1]["failure"]["code"]),
                         (503, "SESSION_STORAGE_UNAVAILABLE"))
        self.assertEqual(inspect_session(session_id, self.token)[1]["session"]["status"],
                         "active")
        unknown_close = close_session(session_id, {}, self.token,
                                      connection_factory=uncertain_factory)
        self.assertEqual((unknown_close[0], unknown_close[1]["outcome"],
                          unknown_close[1]["failure"]["code"]),
                         (503, "unknown", "SESSION_OUTCOME_UNKNOWN"))
        self.assertNotIn("session_id", unknown_close[1])
        self.assertEqual(wrappers[-1].commit_calls, 1)
        self.assertEqual(inspect_session(session_id, self.token)[1]["session"]["status"],
                         "closed")

    def test_audit_uncertainty_preserves_m12_and_no_delegate(self):
        session_id = self._new_session()
        class UncertainAudit(RoutingAudit):
            def reserve(self, *_args, **_kwargs):
                raise AuditWriteError(uncertain=True)
        model = RouteModel()
        status, body = self._route(session_id, model=model,
                                   audit=UncertainAudit(connect))
        self.assertEqual((status, body["failure"]["code"]),
                         (503, "ROUTING_AUDIT_OUTCOME_UNKNOWN"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self._counts()["routing_audit"], 0)
        class AfterCommitAudit(RoutingAudit):
            def reserve(self, *args, **kwargs):
                super().reserve(*args, **kwargs)
                raise AuditWriteError(uncertain=True)
        model = RouteModel()
        possible = self._route(session_id, model=model,
                               audit=AfterCommitAudit(connect))
        self.assertEqual((possible[0], possible[1]["failure"]["code"]),
                         (503, "ROUTING_AUDIT_OUTCOME_UNKNOWN"))
        self.assertEqual(model.calls, [])
        with connect() as db:
            rows = db.execute("""SELECT stage,session_id FROM noah.routing_audit
                WHERE actor_user_id=%s""", (self.user,)).fetchall()
        self.assertEqual(len(rows), 1)
        self.assertEqual((rows[0]["stage"], str(rows[0]["session_id"])),
                         ("reserved", session_id))
        def unavailable():
            raise OSError("synthetic connection failure")
        model = RouteModel()
        definite = self._route(session_id, model=model,
                               audit=RoutingAudit(unavailable))
        self.assertEqual((definite[0], definite[1]["failure"]["code"]),
                         (503, "ROUTING_AUDIT_UNAVAILABLE"))
        self.assertEqual(model.calls, [])
        self.assertEqual(self._counts()["routing_audit"], 1)

    def test_scoped_delegate_receives_only_original_arguments(self):
        session_id = self._new_session()
        received = []
        class MemoryModel(RouteModel):
            def complete(self, messages, schema, max_tokens):
                self.calls.append((messages, schema, max_tokens))
                return {"route": "memory.query"}
        def memory_runner(payload, token):
            received.append((payload, token))
            return 503, {"status": "failed", "request_id": str(uuid4()),
                         "failure": {"code": "SYNTHETIC_UNAVAILABLE"},
                         "task_id": None, "execution_id": None}
        model = MemoryModel()
        status, body = route_read_request({"question": "Ask about saved memories"},
            self.token, model=model, memory_runner=memory_runner,
            settings_provider=SETTINGS, session_headers=[session_id])
        self.assertEqual(status, 503)
        self.assertEqual(body["routing"]["capability"], "memory.query")
        self.assertEqual(received, [({"question": "Ask about saved memories"}, self.token)])
        self.assertNotIn(session_id, str(model.calls))
        self.assertEqual(self._counts()["tasks"], 0)
        self.assertEqual(self._counts()["execution_records"], 0)

    def test_scoped_write_shapes_and_existing_project_precheck(self):
        session_id = self._new_session()
        class FixedModel(RouteModel):
            def __init__(self, route):
                super().__init__()
                self.route = route

            def complete(self, messages, schema, max_tokens):
                self.calls.append((messages, schema, max_tokens))
                return {"route": self.route}

        save_model, suppress_model = FixedModel("no_action"), FixedModel("no_action")
        requests = (
            ({"question": "Do not save this", "memory_save": {"content": "synthetic"}},
             save_model, {"idempotency_key": "m16-synthetic-key"}),
            ({"question": "Do not suppress this", "memory_suppress": {
                "memory_id": str(uuid4())}}, suppress_model, {}),
        )
        for payload, model, options in requests:
            status, body = route_read_request(payload, self.token, model=model,
                settings_provider=SETTINGS, session_headers=[session_id], **options)
            self.assertEqual((status, body["routing"]["outcome"]), (200, "no_action"))
            with connect() as db:
                row = db.execute("SELECT session_id FROM noah.routing_audit WHERE router_id=%s",
                                 (UUID(body["router_id"]),)).fetchone()
            self.assertEqual(str(row["session_id"]), session_id)
            self.assertNotIn(session_id, str(model.calls))
        self.assertEqual(self._counts()["tasks"], 0)
        self.assertEqual(self._counts()["execution_records"], 0)
        before = self._counts()["routing_audit"]
        project_model = FixedModel("project.documents.answer.auto")
        status, body = route_read_request(
            {"question": "Read a private project", "project_id": str(uuid4())},
            self.token, model=project_model, settings_provider=SETTINGS,
            session_headers=[session_id])
        self.assertEqual((status, body["failure"]["code"]), (404, "PROJECT_NOT_FOUND"))
        self.assertEqual(project_model.calls, [])
        self.assertEqual(self._counts()["routing_audit"], before)

    def test_fresh_process_reads_durable_session(self):
        session_id = self._new_session()
        self._route(session_id)
        child_env = os.environ.copy()
        child_env["NOAH_M16_SYNTHETIC_TOKEN"] = self.token
        code = ("import os,sys; from noah.session import inspect_session; "
                "s,b=inspect_session(sys.argv[1],os.environ['NOAH_M16_SYNTHETIC_TOKEN']); "
                "print(s,len(b.get('interactions',[])))")
        child = subprocess.run([sys.executable, "-c", code, session_id],
                               env=child_env, capture_output=True, text=True, check=False)
        self.assertEqual((child.returncode, child.stdout.strip()), (0, "200 1"))


if __name__ == "__main__":
    unittest.main()
