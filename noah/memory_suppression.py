"""Explicit, owner-only user Memory suppression without deleting provenance."""

from uuid import uuid4

import psycopg

from .db import connect
from .service import (_actor_for_token, _audit_db_failure, _authorized,
                      _failure, _uuid, RequestFailure)


_ORIGINAL_FIELDS = ("id", "scope", "owner_user_id", "project_id", "content",
                    "provenance", "created_by", "created_at")


def _unknown(request_id):
    _audit_db_failure(request_id, code="SUPPRESSION_OUTCOME_UNKNOWN")
    status, body = _failure(request_id, "SUPPRESSION_OUTCOME_UNKNOWN",
        "Environment Failure", 503, "Suppression outcome cannot be confirmed")
    body["outcome"] = "unknown"
    return status, body


def _rollback_confirmed(connection):
    try:
        connection.rollback()
        return True
    except (psycopg.Error, OSError):
        return False


def _denied_target(request_id, connection, actor, row):
    if row is None or not _authorized(connection, actor, row["scope"],
                                      row["owner_user_id"], row["project_id"], write=False):
        return _failure(request_id, "MEMORY_NOT_FOUND", "Permission Denied", 404,
                        "Memory not found")
    if row["scope"] != "user":
        return _failure(request_id, "UNSUPPORTED_SCOPE", "Invalid Input", 422,
                        "Only user-scope memories can be suppressed")
    if row["owner_user_id"] != actor:
        return _failure(request_id, "MEMORY_NOT_FOUND", "Permission Denied", 404,
                        "Memory not found")
    return None


def suppress_memory(memory_id, payload, token, connection_factory=connect):
    """Commit one verified transition and its Task/Execution in one transaction."""
    request_id = uuid4()
    parsed_id = _uuid(memory_id)
    if parsed_id is None:
        return _failure(request_id, "INVALID_TARGET", "Invalid Input", 400,
                        "Valid memory ID required")
    connection = None
    try:
        connection = connection_factory()
        actor = _actor_for_token(connection, token)
        if actor is None:
            return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                            "Authentication required")
        if payload != {}:
            return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                            "An empty JSON object is required")

        # This read is only preflight. No decision made here authorizes mutation.
        row = connection.execute("SELECT scope,owner_user_id,project_id FROM noah.memories "
                                 "WHERE id=%s", (parsed_id,)).fetchone()
        denial = _denied_target(request_id, connection, actor, row)
        if denial:
            return denial
        connection.commit()

        # A new transaction revalidates the original credential before locking
        # and changing the target. A revocation committed before this statement wins.
        if _actor_for_token(connection, token) != actor:
            return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                            "Authentication required")
        original = connection.execute("SELECT * FROM noah.memories WHERE id=%s FOR UPDATE",
                                      (parsed_id,)).fetchone()
        denial = _denied_target(request_id, connection, actor, original)
        if denial:
            return denial
        if original["suppressed_at"] is not None:
            return 200, {"status": "succeeded", "request_id": str(request_id),
                "outcome": "already_suppressed", "memory_id": str(parsed_id),
                "suppressed_at": original["suppressed_at"].isoformat(),
                "task_id": None, "execution_id": None}

        task_id, execution_id = uuid4(), uuid4()
        try:
            connection.execute("""INSERT INTO noah.tasks
                (id,actor_user_id,goal,status,verification_status)
                VALUES (%s,%s,'Suppress explicitly selected user memory','running','pending')""",
                (task_id, actor))
            connection.execute("""INSERT INTO noah.execution_records
                (id,request_id,task_id,actor_user_id,capability,status)
                VALUES (%s,%s,%s,%s,'memory.suppress','running')""",
                (execution_id, request_id, task_id, actor))
            updated = connection.execute("""UPDATE noah.memories
                SET suppressed_at=clock_timestamp()
                WHERE id=%s AND scope='user' AND owner_user_id=%s
                    AND suppressed_at IS NULL RETURNING suppressed_at""",
                (parsed_id, actor)).fetchone()
            try:
                stored = connection.execute("SELECT * FROM noah.memories WHERE id=%s",
                                            (parsed_id,)).fetchone()
            except (psycopg.Error, OSError) as error:
                raise RequestFailure("VERIFICATION_FAILED", "Verification Failure", 500,
                                     "Suppression readback failed") from error
            if (updated is None or stored is None or stored["suppressed_at"] is None
                    or stored["suppressed_at"] != updated["suppressed_at"]
                    or any(stored[key] != original[key] for key in _ORIGINAL_FIELDS)):
                raise RequestFailure("VERIFICATION_FAILED", "Verification Failure", 500,
                                     "Suppression could not be verified")
            task = connection.execute("""UPDATE noah.tasks SET status='completed',
                verification_status='passed',updated_at=now() WHERE id=%s
                RETURNING status,verification_status""", (task_id,)).fetchone()
            execution = connection.execute("""UPDATE noah.execution_records
                SET status='succeeded',memory_id=%s,verified_at=now(),updated_at=now()
                WHERE id=%s RETURNING status,memory_id,verified_at,capability""",
                (parsed_id, execution_id)).fetchone()
            if (task is None or task["status"] != "completed"
                    or task["verification_status"] != "passed" or execution is None
                    or execution["status"] != "succeeded" or execution["memory_id"] != parsed_id
                    or execution["verified_at"] is None
                    or execution["capability"] != "memory.suppress"):
                raise RequestFailure("VERIFICATION_FAILED", "Verification Failure", 500,
                                     "Suppression records could not be verified")
        except RequestFailure as error:
            if not _rollback_confirmed(connection):
                return _unknown(request_id)
            return _failure(request_id, error.code, error.category, error.http_status, str(error))
        except (psycopg.Error, OSError):
            if not _rollback_confirmed(connection):
                return _unknown(request_id)
            return _failure(request_id, "SUPPRESSION_FAILED", "Environment Failure", 500,
                            "Suppression was rolled back")

        try:
            connection.commit()
        except (psycopg.Error, OSError):
            # The server may have committed. Closing the connection must not retry.
            return _unknown(request_id)
        return 200, {"status": "succeeded", "request_id": str(request_id),
            "outcome": "suppressed", "memory_id": str(parsed_id),
            "suppressed_at": stored["suppressed_at"].isoformat(),
            "task_id": str(task_id), "execution_id": str(execution_id)}
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
                        "Storage is unavailable")
    finally:
        if connection is not None:
            try:
                connection.close()
            except (psycopg.Error, OSError):
                pass
