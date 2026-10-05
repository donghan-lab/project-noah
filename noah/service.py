"""Harness-like boundary for one authorized memory capability."""

import base64
import binascii
import hashlib
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs
from uuid import UUID, uuid4

import psycopg

from .db import ROOT, connect


class RequestFailure(Exception):
    def __init__(self, code: str, category: str, http_status: int, message: str):
        super().__init__(message)
        self.code, self.category, self.http_status = code, category, http_status


def _failure(request_id, code, category, http_status, message, task_id=None, execution_id=None, retryable=False):
    return http_status, {
        "status": "failed",
        "request_id": str(request_id),
        "task_id": str(task_id) if task_id else None,
        "execution_id": str(execution_id) if execution_id else None,
        "failure": {
            "code": code,
            "category": category,
            "message": message,
            "recoverable": category in {"Environment Failure", "External Service Failure", "Timeout"},
            # A write may have committed before a connection failure was observed.
            "retryable": retryable,
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


def _actor_for_token(connection, token):
    token_hash = hashlib.sha256(token.encode()).hexdigest() if token else ""
    row = connection.execute(
        "SELECT user_id FROM noah.api_tokens WHERE token_hash = %s AND revoked_at IS NULL",
        (token_hash,),
    ).fetchone()
    return row["user_id"] if row else None


def _memory_result(row):
    return {
        "id": str(row["id"]), "scope": row["scope"], "content": row["content"],
        "owner_user_id": str(row["owner_user_id"]) if row["owner_user_id"] else None,
        "project_id": str(row["project_id"]) if row["project_id"] else None,
        "created_at": row["created_at"].isoformat(),
        "suppressed": row["suppressed_at"] is not None,
        "suppressed_at": row["suppressed_at"].isoformat() if row["suppressed_at"] else None,
    }


def _readable_memory_filter(actor):
    """The same user/project visibility rule for listing and word search."""
    return """m.suppressed_at IS NULL AND ((m.scope = 'user' AND m.owner_user_id = %s)
        OR (m.scope = 'project' AND EXISTS (
            SELECT 1 FROM noah.project_memberships membership
            WHERE membership.project_id = m.project_id AND membership.user_id = %s)))""", [actor, actor]


def _visible_memory_context(connection, actor, token, memory_ids):
    """Recheck every model-input Memory in one DB observation; keep content ephemeral."""
    if _actor_for_token(connection, token) != actor:
        return "UNAUTHENTICATED", {}
    try:
        ids = tuple(UUID(str(value)) for value in memory_ids)
    except (TypeError, ValueError, AttributeError):
        return "MEMORY_CONTEXT_STALE", {}
    if len(set(ids)) != len(ids):
        return "MEMORY_CONTEXT_STALE", {}
    if not ids:
        return None, {}
    visibility, params = _readable_memory_filter(actor)
    rows = connection.execute("SELECT m.id,m.content FROM noah.memories m "
        "WHERE m.id = ANY(%s) AND " + visibility, [list(ids), *params]).fetchall()
    if len(rows) != len(ids):
        return "MEMORY_CONTEXT_STALE", {}
    return None, {str(row["id"]): row["content"] for row in rows}


def _list_options(query):
    try:
        if len(query) > 1024:
            raise ValueError("Query too long")
        params = parse_qs(query, keep_blank_values=True, strict_parsing=True, max_num_fields=3)
    except ValueError:
        raise RequestFailure("INVALID_QUERY", "Invalid Input", 400, "Invalid list query") from None
    if set(params) - {"scope", "limit", "cursor"} or any(len(values) != 1 for values in params.values()):
        raise RequestFailure("INVALID_QUERY", "Invalid Input", 400, "Invalid list query")
    scope = params.get("scope", [None])[0]
    if scope is not None and scope not in {"user", "project"}:
        raise RequestFailure("INVALID_SCOPE", "Invalid Input", 400, "Scope must be user or project")
    raw_limit = params.get("limit", ["20"])[0]
    if not raw_limit or len(raw_limit) > 3 or any(char not in "0123456789" for char in raw_limit):
        raise RequestFailure("INVALID_LIMIT", "Invalid Input", 400, "Limit must be between 1 and 100")
    limit = int(raw_limit)
    if not 1 <= limit <= 100:
        raise RequestFailure("INVALID_LIMIT", "Invalid Input", 400, "Limit must be between 1 and 100")
    raw_cursor = params.get("cursor", [None])[0]
    if raw_cursor is None:
        return scope, limit, None
    try:
        if not raw_cursor or len(raw_cursor) > 256:
            raise ValueError("Invalid cursor length")
        decoded = base64.b64decode(raw_cursor + "=" * (-len(raw_cursor) % 4), altchars=b"-_", validate=True)
        position = json.loads(decoded)
        if not isinstance(position, dict) or set(position) != {"created_at", "id"}:
            raise ValueError("Invalid cursor shape")
        if not isinstance(position["created_at"], str) or not isinstance(position["id"], str):
            raise ValueError("Invalid cursor values")
        created_at = datetime.fromisoformat(position["created_at"])
        if created_at.tzinfo is None or created_at.utcoffset() is None:
            raise ValueError("Cursor timestamp must include timezone")
        memory_id = UUID(position["id"])
    except (ValueError, TypeError, UnicodeDecodeError, binascii.Error):
        raise RequestFailure("INVALID_CURSOR", "Invalid Input", 400, "Invalid page cursor") from None
    return scope, limit, (created_at, memory_id)


def _page_cursor(row):
    value = json.dumps({"created_at": row["created_at"].isoformat(), "id": str(row["id"])}, separators=(",", ":"))
    return base64.urlsafe_b64encode(value.encode()).decode().rstrip("=")


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


def _audit_db_failure(request_id, task_id=None, code="DATABASE_UNAVAILABLE"):
    """Minimal local record when PostgreSQL cannot record its own failure."""
    try:
        path = ROOT / ".noah" / "failures.jsonl"
        path.parent.mkdir(exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({
                "at": datetime.now(timezone.utc).isoformat(),
                "request_id": str(request_id),
                "task_id": str(task_id) if task_id else None,
                "status": "unknown" if code.endswith("_OUTCOME_UNKNOWN") else "failed",
                "category": "Environment Failure",
                "code": code,
            }) + "\n")
    except OSError:
        pass


def _write_fingerprint(content, scope, owner, project):
    request = {"action": "save_memory", "content": content, "scope": scope,
        "owner_user_id": str(owner) if owner else None, "project_id": str(project) if project else None}
    canonical = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _prior_write(connection, actor, key_digest, fingerprint, content, scope, owner, project, request_id):
    """Resolve one durable reservation without starting another write."""
    row = connection.execute("""SELECT w.request_fingerprint, e.id AS execution_id,
        e.request_id, e.task_id, e.status AS execution_status, e.memory_id,
        e.failure_code, e.failure_category, t.status AS task_status,
        t.verification_status, m.content, m.scope, m.owner_user_id, m.project_id
        FROM noah.memory_write_requests w
        JOIN noah.execution_records e ON e.id = w.execution_id
        JOIN noah.tasks t ON t.id = e.task_id
        LEFT JOIN noah.memories m ON m.id = e.memory_id
        WHERE w.actor_user_id = %s AND w.key_digest = %s""",
        (actor, key_digest)).fetchone()
    if row is None:
        return None
    if row["request_fingerprint"].strip() != fingerprint:
        return _record_rejection(connection, request_id, actor,
            RequestFailure("IDEMPOTENCY_CONFLICT", "Invalid Input", 409,
                "Idempotency-Key was already used for a different memory request"))
    original_request = row["request_id"]
    task_id, execution_id = row["task_id"], row["execution_id"]
    if row["execution_status"] == "running" and row["task_status"] == "running":
        return 202, {"status": "pending", "summary": "Original write has no final recorded outcome",
            "request_id": str(original_request), "task_id": str(task_id),
            "execution_id": str(execution_id), "retryable": True}
    if (row["execution_status"] == "succeeded" and row["task_status"] == "completed"
            and row["verification_status"] == "passed" and row["memory_id"]
            and row["content"] == content and row["scope"] == scope
            and row["owner_user_id"] == owner and row["project_id"] == project):
        return 200, {"status": "succeeded", "summary": "Memory saved and verified",
            "request_id": str(original_request), "task_id": str(task_id),
            "execution_id": str(execution_id), "replayed": True,
            "evidence": {"memory_id": str(row["memory_id"]), "verification": "database_readback"}}
    if (row["execution_status"] == "failed" and row["task_status"] == "failed"
            and row["verification_status"] == "failed" and row["failure_code"]):
        status, body = _failure(original_request, row["failure_code"],
            row["failure_category"] or "Environment Failure", 500,
            "Original memory write failed; use a new key for a new attempt",
            task_id, execution_id)
        body["replayed"] = True
        return status, body
    return _failure(original_request, "IDEMPOTENCY_STATE_INCONSISTENT", "Environment Failure", 503,
        "Original write state cannot be verified", task_id, execution_id)


def save_memory(payload, token, connection_factory=connect, insert_memory=None, idempotency_key=None):
    request_id = uuid4()
    task_id = execution_id = None
    key_digest = None
    try:
        with connection_factory() as connection:
            actor = _actor_for_token(connection, token)
            if not actor:
                return _record_rejection(connection, request_id, None,
                    RequestFailure("UNAUTHENTICATED", "Permission Denied", 401, "Authentication required"))
            try:
                content, scope, owner, project = _validate(payload)
                if not _authorized(connection, actor, scope, owner, project, write=True):
                    raise RequestFailure("SCOPE_DENIED", "Permission Denied", 403, "Memory scope is not writable")
                if idempotency_key is not None:
                    if not isinstance(idempotency_key, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._~-]{0,127}", idempotency_key):
                        raise RequestFailure("INVALID_IDEMPOTENCY_KEY", "Invalid Input", 400,
                            "Idempotency-Key must be 1 to 128 ASCII token characters")
                    key_digest = hashlib.sha256(idempotency_key.encode("ascii")).hexdigest()
            except RequestFailure as failure:
                return _record_rejection(connection, request_id, actor, failure)

            if key_digest:
                fingerprint = _write_fingerprint(content, scope, owner, project)
                prior = _prior_write(connection, actor, key_digest, fingerprint,
                    content, scope, owner, project, request_id)
                if prior is not None:
                    return prior

            task_id, execution_id, memory_id = uuid4(), uuid4(), uuid4()
            connection.execute(
                "INSERT INTO noah.tasks (id, actor_user_id, goal, status, verification_status) VALUES (%s, %s, %s, 'running', 'pending')",
                (task_id, actor, "Save explicitly requested memory"),
            )
            connection.execute(
                "INSERT INTO noah.execution_records (id, request_id, task_id, actor_user_id, status) VALUES (%s, %s, %s, %s, 'running')",
                (execution_id, request_id, task_id, actor),
            )
            if key_digest:
                reserved = connection.execute("""INSERT INTO noah.memory_write_requests
                    (actor_user_id, key_digest, request_fingerprint, execution_id)
                    VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING execution_id""",
                    (actor, key_digest, fingerprint, execution_id)).fetchone()
                if reserved is None:
                    connection.rollback()
                    prior = _prior_write(connection, actor, key_digest, fingerprint,
                        content, scope, owner, project, request_id)
                    if prior is not None:
                        return prior
                    return _failure(request_id, "IDEMPOTENCY_STATE_INCONSISTENT", "Environment Failure", 503,
                        "Original write state cannot be verified")
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
                    _audit_db_failure(request_id, task_id, "WRITE_OUTCOME_UNKNOWN")
                    return _failure(request_id, "WRITE_OUTCOME_UNKNOWN", "Environment Failure", 503,
                        "Storage outcome cannot be verified", task_id, execution_id, retryable=bool(key_digest))
                return _failure(request_id, code, category, 500, "Memory was not saved", task_id, execution_id)
            try:
                connection.commit()
            except psycopg.Error:
                # The commit may have succeeded server-side. Never overwrite it with failure.
                _audit_db_failure(request_id, task_id, "WRITE_OUTCOME_UNKNOWN")
                return _failure(request_id, "WRITE_OUTCOME_UNKNOWN", "Environment Failure", 503,
                    "Storage outcome cannot be verified", task_id, execution_id, retryable=bool(key_digest))
            return 201, {
                "status": "succeeded", "summary": "Memory saved and verified",
                "request_id": str(request_id), "task_id": str(task_id),
                "execution_id": str(execution_id),
                "evidence": {"memory_id": str(memory_id), "verification": "database_readback"},
            }
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id, task_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable", task_id, execution_id, retryable=bool(key_digest))


def read_memory(memory_id, token, connection_factory=connect):
    request_id = uuid4()
    parsed_id = _uuid(memory_id)
    if not parsed_id:
        return _failure(request_id, "INVALID_TARGET", "Invalid Input", 400, "Valid memory ID required")
    try:
        with connection_factory() as connection:
            actor = _actor_for_token(connection, token)
            if not actor:
                return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401, "Authentication required")
            row = connection.execute(
                "SELECT id, owner_user_id, project_id, scope, content, created_at, suppressed_at FROM noah.memories WHERE id = %s",
                (parsed_id,),
            ).fetchone()
            if not row or not _authorized(connection, actor, row["scope"], row["owner_user_id"], row["project_id"], write=False):
                return _failure(request_id, "MEMORY_NOT_FOUND", "Permission Denied", 404, "Memory not found")
            return 200, {"status": "succeeded", "memory": _memory_result(row)}
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503, "Storage is unavailable")


def list_memories(token, query="", connection_factory=connect):
    """List only memories readable by the current principal using keyset pagination."""
    request_id = uuid4()
    try:
        with connection_factory() as connection:
            actor = _actor_for_token(connection, token)
            if not actor:
                return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401, "Authentication required")
            try:
                scope, limit, position = _list_options(query)
            except RequestFailure as error:
                return _failure(request_id, error.code, error.category, error.http_status, str(error))
            visibility, params = _readable_memory_filter(actor)
            sql = """SELECT m.id, m.owner_user_id, m.project_id, m.scope, m.content, m.created_at, m.suppressed_at
                FROM noah.memories m WHERE """ + visibility
            if scope:
                sql += " AND m.scope = %s"
                params.append(scope)
            if position:
                sql += " AND (m.created_at, m.id) < (%s, %s)"
                params.extend(position)
            sql += " ORDER BY m.created_at DESC, m.id DESC LIMIT %s"
            params.append(limit + 1)
            rows = connection.execute(sql, params).fetchall()
            page = rows[:limit]
            return 200, {
                "status": "succeeded",
                "memories": [_memory_result(row) for row in page],
                "next_cursor": _page_cursor(page[-1]) if len(rows) > limit else None,
            }
    except (psycopg.Error, OSError, ValueError):
        _audit_db_failure(request_id)
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503, "Storage is unavailable")


def search_memories(token, scope, terms, request_id, connection_factory=connect, limit=5):
    """Bounded literal word search over the existing authorized Memory scope."""
    try:
        with connection_factory() as connection:
            actor = _actor_for_token(connection, token)
            if not actor:
                return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401, "Authentication required")
            visibility, params = _readable_memory_filter(actor)
            sql = """SELECT m.id, m.owner_user_id, m.project_id, m.scope, m.content, m.created_at, m.suppressed_at
                FROM noah.memories m WHERE """ + visibility
            if scope != "all":
                sql += " AND m.scope = %s"
                params.append(scope)
            for term in terms:
                sql += " AND strpos(lower(m.content), lower(%s)) > 0"
                params.append(term)
            sql += " ORDER BY m.created_at DESC, m.id DESC LIMIT %s"
            params.append(limit + 1)
            rows = connection.execute(sql, params).fetchall()
            return 200, {
                "memories": [_memory_result(row) for row in rows[:limit]],
                "truncated": len(rows) > limit,
            }
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
