"""Harness-like boundary for one authorized memory capability."""

import hashlib
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

import psycopg

from .db import ROOT, connect


class RequestFailure(Exception):
    def __init__(self, code: str, category: str, http_status: int, message: str):
        super().__init__(message)
        self.code, self.category, self.http_status = code, category, http_status


def _failure(request_id, code, category, http_status, message, task_id=None, execution_id=None):
    return http_status, {
        "status": "failed",
        "request_id": str(request_id),
        "task_id": str(task_id) if task_id else None,
        "execution_id": str(execution_id) if execution_id else None,
        "failure": {
            "code": code,
            "category": category,
            "message": message,
            "recoverable": category == "Environment Failure",
            # A write may have committed before a connection failure was observed.
            "retryable": False,
        },
    }


def _uuid(value):
    try:
        return UUID(value) if isinstance(value, str) else None
    except ValueError:
        return None


def _validate(payload):
    if not isinstance(payload, dict) or payload.get("action") != "save_memory":
        raise RequestFailure("INVALID_ACTION", "Invalid Input", 400, "Explicit save_memory action required")
    content = payload.get("content")
    if not isinstance(content, str) or not content.strip() or len(content) > 10000:
        raise RequestFailure("INVALID_CONTENT", "Invalid Input", 400, "Content must contain 1 to 10000 characters")
    scope = payload.get("scope")
    if scope == "user":
        owner = _uuid(payload.get("owner_user_id"))
        if not owner or payload.get("project_id") is not None:
            raise RequestFailure("INVALID_TARGET", "Invalid Input", 400, "Valid user target required")
        return content.strip(), scope, owner, None
    if scope == "project":
        project = _uuid(payload.get("project_id"))
        if not project or payload.get("owner_user_id") is not None:
            raise RequestFailure("INVALID_TARGET", "Invalid Input", 400, "Valid project target required")
        return content.strip(), scope, None, project
    raise RequestFailure("INVALID_SCOPE", "Invalid Input", 400, "Scope must be user or project")


def _authorized(connection, actor, scope, owner, project, write):
    if scope == "user":
        return actor == owner
    row = connection.execute(
        "SELECT can_write FROM noah.project_memberships WHERE user_id = %s AND project_id = %s",
        (actor, project),
    ).fetchone()
    return bool(row and (row["can_write"] or not write))


def _record_rejection(connection, request_id, actor, failure):
    execution_id = uuid4()
    connection.execute(
        """INSERT INTO noah.execution_records
        (id, request_id, actor_user_id, status, failure_category, failure_code)
        VALUES (%s, %s, %s, 'failed', %s, %s)""",
        (execution_id, request_id, actor, failure.category, failure.code),
    )
    connection.commit()
    return _failure(request_id, failure.code, failure.category, failure.http_status, str(failure), execution_id=execution_id)


def _audit_db_failure(request_id, task_id=None):
    """Minimal local record when PostgreSQL cannot record its own failure."""
    try:
        path = ROOT / ".noah" / "failures.jsonl"
        path.parent.mkdir(exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(),
                "request_id": str(request_id),
                "task_id": str(task_id) if task_id else None,
                "status": "failed",
                "category": "Environment Failure",
                "code": "DATABASE_UNAVAILABLE",
            }) + "\n")
    except OSError:
        pass


def save_memory(payload, token, connection_factory=connect, insert_memory=None):
    request_id = uuid4()
    task_id = execution_id = None
    try:
        with connection_factory() as connection:
            token_hash = hashlib.sha256(token.encode()).hexdigest() if token else ""
            row = connection.execute(
                "SELECT user_id FROM noah.api_tokens WHERE token_hash = %s AND revoked_at IS NULL",
                (token_hash,),
            ).fetchone()
            if not row:
                return _record_rejection(connection, request_id, None,
                    RequestFailure("UNAUTHENTICATED", "Permission Denied", 401, "Authentication required"))
            actor = row["user_id"]
            try:
                content, scope, owner, project = _validate(payload)
                if not _authorized(connection, actor, scope, owner, project, write=True):
                    raise RequestFailure("SCOPE_DENIED", "Permission Denied", 403, "Memory scope is not writable")
            except RequestFailure as failure:
                return _record_rejection(connection, request_id, actor, failure)

            task_id, execution_id, memory_id = uuid4(), uuid4(), uuid4()
            connection.execute(
                "INSERT INTO noah.tasks (id, actor_user_id, goal, status, verification_status) VALUES (%s, %s, %s, 'running', 'pending')",
                (task_id, actor, "Save explicitly requested memory"),
            )
            connection.execute(
                "INSERT INTO noah.execution_records (id, request_id, task_id, actor_user_id, status) VALUES (%s, %s, %s, %s, 'running')",
                (execution_id, request_id, task_id, actor),
            )
            connection.commit()

            try:
                if insert_memory is None:
                    connection.execute(
                        """INSERT INTO noah.memories
                        (id, owner_user_id, project_id, scope, content, created_by)
                        VALUES (%s, %s, %s, %s, %s, %s)""",
                        (memory_id, owner, project, scope, content, actor),
                    )
                else:
                    insert_memory(connection, memory_id, owner, project, scope, content, actor)
                stored = connection.execute(
                    "SELECT id, owner_user_id, project_id, scope, content FROM noah.memories WHERE id = %s",
                    (memory_id,),
                ).fetchone()
                if not stored or stored["content"] != content or stored["scope"] != scope or stored["owner_user_id"] != owner or stored["project_id"] != project:
                    raise RequestFailure("VERIFICATION_FAILED", "Verification Failure", 500, "Stored memory could not be verified")
                connection.execute(
                    "UPDATE noah.tasks SET status = 'completed', verification_status = 'passed', updated_at = now() WHERE id = %s",
                    (task_id,),
                )
                connection.execute(
                    """UPDATE noah.execution_records SET status = 'succeeded', memory_id = %s,
                    verified_at = now(), updated_at = now() WHERE id = %s""",
                    (memory_id, execution_id),
                )
                connection.commit()
                return 201, {
                    "status": "succeeded", "summary": "Memory saved and verified",
                    "request_id": str(request_id), "task_id": str(task_id),
                    "execution_id": str(execution_id),
                    "evidence": {"memory_id": str(memory_id), "verification": "database_readback"},
                }
            except (psycopg.Error, RequestFailure) as error:
                connection.rollback()
                category = error.category if isinstance(error, RequestFailure) else "Environment Failure"
                code = error.code if isinstance(error, RequestFailure) else "DATABASE_WRITE_FAILED"
                try:
                    connection.execute(
                        "UPDATE noah.tasks SET status = 'failed', verification_status = 'failed', updated_at = now() WHERE id = %s",
                        (task_id,),
                    )
                    connection.execute(
                        """UPDATE noah.execution_records SET status = 'failed', failure_category = %s,
                        failure_code = %s, updated_at = now() WHERE id = %s""",
                        (category, code, execution_id),
                    )
                    connection.commit()
                except psycopg.Error:
                    _audit_db_failure(request_id, task_id)
                return _failure(request_id, code, category, 500, "Memory was not saved", task_id, execution_id)
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id, task_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable", task_id, execution_id)


def read_memory(memory_id, token, connection_factory=connect):
    request_id = uuid4()
    parsed_id = _uuid(memory_id)
    if not parsed_id:
        return _failure(request_id, "INVALID_TARGET", "Invalid Input", 400, "Valid memory ID required")
    try:
        with connection_factory() as connection:
            token_hash = hashlib.sha256(token.encode()).hexdigest() if token else ""
            actor_row = connection.execute(
                "SELECT user_id FROM noah.api_tokens WHERE token_hash = %s AND revoked_at IS NULL", (token_hash,),
            ).fetchone()
            if not actor_row:
                return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401, "Authentication required")
            row = connection.execute(
                "SELECT id, owner_user_id, project_id, scope, content, created_at FROM noah.memories WHERE id = %s",
                (parsed_id,),
            ).fetchone()
            if not row or not _authorized(connection, actor_row["user_id"], row["scope"], row["owner_user_id"], row["project_id"], write=False):
                return _failure(request_id, "MEMORY_NOT_FOUND", "Permission Denied", 404, "Memory not found")
            return 200, {"status": "succeeded", "memory": {
                "id": str(row["id"]), "scope": row["scope"], "content": row["content"],
                "owner_user_id": str(row["owner_user_id"]) if row["owner_user_id"] else None,
                "project_id": str(row["project_id"]) if row["project_id"] else None,
                "created_at": row["created_at"].isoformat(),
            }}
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503, "Storage is unavailable")


def provision_user(label, connection_factory=connect):
    """Local operator command. Returns the token only once; database stores its hash."""
    if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
        raise ValueError("User label must contain 1 to 100 characters")
    user_id, token = uuid4(), secrets.token_urlsafe(32)
    with connection_factory() as connection:
        connection.execute("INSERT INTO noah.users (id, label) VALUES (%s, %s)", (user_id, label.strip()))
        connection.execute("INSERT INTO noah.api_tokens (token_hash, user_id) VALUES (%s, %s)",
            (hashlib.sha256(token.encode()).hexdigest(), user_id))
    return user_id, token


def create_project(label, owner_user_id, connection_factory=connect):
    owner = _uuid(owner_user_id)
    if not owner or not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
        raise ValueError("Valid project label and owner user ID required")
    project_id = uuid4()
    with connection_factory() as connection:
        connection.execute("INSERT INTO noah.projects (id, label) VALUES (%s, %s)", (project_id, label.strip()))
        connection.execute("INSERT INTO noah.project_memberships (project_id, user_id, can_write) VALUES (%s, %s, true)",
            (project_id, owner))
    return project_id
