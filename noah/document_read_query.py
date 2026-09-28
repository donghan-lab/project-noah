"""Authenticated orchestration for a verified, single-document read."""

from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import UUID, uuid4

import psycopg

from .db import connect
from .document_query import _finish_failure, _project_readable
from .document_read import (
    CAPABILITY, execute_document_read, validate_document_name,
    validate_read_observation,
)
from .document_tool import ToolFailure, ToolOutcomeUnknown, operator_root
from .service import _actor_for_token, _failure


def read_project_document(project_id, payload, token, connection_factory=connect,
                          root_provider=operator_root,
                          tool_runner=execute_document_read):
    request_id = uuid4()
    task_id = execution_id = None
    try:
        with connection_factory() as db:
            actor = _actor_for_token(db, token)
            if actor is None:
                return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                    "Authentication required")
            try:
                project = UUID(project_id)
            except (ValueError, TypeError, AttributeError):
                return _failure(request_id, "INVALID_PROJECT", "Invalid Input", 400,
                    "Valid project ID required")
            if not _project_readable(db, actor, project):
                return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                    "Project not found")
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable")

    if not isinstance(payload, dict) or set(payload) != {"document_name"}:
        return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
            "One document name is required")
    try:
        name = validate_document_name(payload["document_name"])
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Document name is invalid")

    try:
        root_id, root = root_provider(project)
        if (not isinstance(root_id, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", root_id)
                or not isinstance(root, Path) or not root.is_absolute()):
            raise ToolFailure("PROJECT_ROOT_CONFIG_INVALID")
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project document root is unavailable")

    try:
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                    "Project not found")
            task_id, execution_id = uuid4(), uuid4()
            db.execute("""INSERT INTO noah.tasks
                (id, actor_user_id, goal, status, verification_status)
                VALUES (%s, %s, %s, 'running', 'pending')""",
                (task_id, actor, "Read one project document"))
            db.execute("""INSERT INTO noah.execution_records
                (id, request_id, task_id, actor_user_id, capability, status)
                VALUES (%s, %s, %s, %s, %s, 'running')""",
                (execution_id, request_id, task_id, actor, CAPABILITY))
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable", task_id, execution_id)

    # The reservation is durable; check again just before dispatching the
    # worker that opens the file. No document path is accessed on revocation.
    try:
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
    except ToolFailure as failure:
        if not _finish_failure(connection_factory, task_id, execution_id, failure):
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                "Execution outcome could not be recorded", task_id, execution_id)
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project not found", task_id, execution_id)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be verified", task_id, execution_id)

    try:
        raw = tool_runner(root, name)
        # Validation opens the document again; revoke-before-verify must not read it.
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        observation = validate_read_observation(root, name, raw)
    except ToolOutcomeUnknown:
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Timeout", 504,
            "Tool termination could not be verified", task_id, execution_id)
    except ToolFailure as failure:
        if not _finish_failure(connection_factory, task_id, execution_id, failure):
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                "Execution outcome could not be recorded", task_id, execution_id)
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project document read failed", task_id, execution_id)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be verified", task_id, execution_id)

    observed_at = datetime.now(timezone.utc)
    try:
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            db.execute("""INSERT INTO noah.document_read_evidence
                (execution_id, project_id, root_id, document_name, observed_at,
                 byte_length, content_sha256, content_encoding, bom_present)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 'utf-8', %s)""",
                (execution_id, project, root_id, name, observed_at,
                 observation["byte_length"], observation["content_sha256"],
                 observation["bom_present"]))
            db.execute("""UPDATE noah.tasks SET status = 'completed',
                verification_status = 'passed', updated_at = now() WHERE id = %s""", (task_id,))
            db.execute("""UPDATE noah.execution_records SET status = 'succeeded',
                verified_at = now(), updated_at = now() WHERE id = %s""", (execution_id,))
    except ToolFailure as failure:
        if not _finish_failure(connection_factory, task_id, execution_id, failure):
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                "Execution outcome could not be recorded", task_id, execution_id)
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project not found", task_id, execution_id)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be verified", task_id, execution_id)

    return 200, {
        "status": "succeeded", "request_id": str(request_id),
        "task_id": str(task_id), "execution_id": str(execution_id),
        "capability": CAPABILITY, "project_id": str(project),
        "document_name": name, "content": observation["content"],
        "byte_length": observation["byte_length"],
        "content_sha256": observation["content_sha256"],
        "evidence": {"execution_id": str(execution_id), "root_id": root_id,
            "document_name": name, "observed_at": observed_at.isoformat(),
            "byte_length": observation["byte_length"],
            "content_sha256": observation["content_sha256"],
            "content_encoding": "utf-8", "bom_present": observation["bom_present"]},
    }
