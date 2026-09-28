"""Authenticated, bounded orchestration of one read-only project tool."""

import hashlib
import json
from pathlib import Path
import re
from datetime import datetime, timezone
from uuid import UUID, uuid4

import psycopg

from .db import connect
from .document_tool import (
    CAPABILITY, ToolFailure, ToolOutcomeUnknown, execute_document_tool,
    operator_root, validate_observation,
)
from .ollama import (
    OllamaClient, OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable,
    OllamaUnsafeBinding,
)
from .service import _actor_for_token, _failure


INTENT_SCHEMA = {
    "type": "object",
    "properties": {"intent": {"type": "string", "enum": ["list_project_documents", "unsupported"]}},
    "required": ["intent"],
    "additionalProperties": False,
}
INTENT_INSTRUCTIONS = (
    "Classify whether the user asks to list document names for the already selected project. "
    "Return only JSON with intent list_project_documents or unsupported. "
    "Never propose a path, file operation, command, or extra field."
)


def _project_readable(db, actor, project_id):
    return db.execute("""SELECT 1 FROM noah.project_memberships
        WHERE project_id = %s AND user_id = %s""", (project_id, actor)).fetchone() is not None


def _finish_failure(connection_factory, task_id, execution_id, failure):
    try:
        with connection_factory() as db:
            db.execute("""UPDATE noah.tasks SET status = 'failed',
                verification_status = 'failed', updated_at = now() WHERE id = %s""", (task_id,))
            db.execute("""UPDATE noah.execution_records SET status = 'failed',
                failure_category = %s, failure_code = %s, updated_at = now()
                WHERE id = %s""", (failure.category, failure.code, execution_id))
        return True
    except (psycopg.Error, OSError, ValueError):
        return False


def _model_failure(request_id, error):
    if isinstance(error, OllamaUnsafeBinding):
        return _failure(request_id, "OLLAMA_NOT_LOCAL", "Policy Violation", 503,
            "The dedicated model listener is not verified as local-only")
    if isinstance(error, OllamaTimeout):
        return _failure(request_id, "OLLAMA_TIMEOUT", "Timeout", 504,
            "The local model timed out")
    if isinstance(error, OllamaUnavailable):
        return _failure(request_id, "OLLAMA_UNAVAILABLE", "External Service Failure", 503,
            "The local model is unavailable")
    return _failure(request_id, "MODEL_OUTPUT_INVALID", "Verification Failure", 502,
        "The local model returned invalid structured output")


def query_project_documents(project_id, payload, token, connection_factory=connect,
                            model=None, root_provider=operator_root,
                            tool_runner=execute_document_tool):
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

    if (not isinstance(payload, dict) or set(payload) != {"question"}
            or not isinstance(payload["question"], str)
            or not 1 <= len(payload["question"].strip()) <= 500):
        return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
            "A question of 1 to 500 characters is required")
    question = payload["question"].strip()
    model = model if model is not None else OllamaClient()
    try:
        proposed = model.complete([
            {"role": "system", "content": INTENT_INSTRUCTIONS},
            {"role": "user", "content": question},
        ], INTENT_SCHEMA, 64)
    except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable, OllamaInvalidResponse) as error:
        return _model_failure(request_id, error)
    if (not isinstance(proposed, dict) or set(proposed) != {"intent"}
            or not isinstance(proposed["intent"], str)
            or proposed["intent"] not in {"list_project_documents", "unsupported"}):
        return _model_failure(request_id, OllamaInvalidResponse())
    if proposed["intent"] == "unsupported":
        return _failure(request_id, "UNSUPPORTED_INTENT", "Invalid Input", 422,
            "Only project document listing is supported")

    try:
        root_id, root = root_provider(project)
        if (not isinstance(root_id, str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", root_id)
                or not isinstance(root, Path) or not root.is_absolute()):
            raise ToolFailure("PROJECT_ROOT_CONFIG_INVALID")
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project document root is unavailable")

    # The second membership check is immediately before the tool reservation.
    try:
        with connection_factory() as db:
            actor_again = _actor_for_token(db, token)
            if actor_again != actor or not _project_readable(db, actor, project):
                return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                    "Project not found")
            task_id, execution_id = uuid4(), uuid4()
            db.execute("""INSERT INTO noah.tasks
                (id, actor_user_id, goal, status, verification_status)
                VALUES (%s, %s, %s, 'running', 'pending')""",
                (task_id, actor, "List project document names"))
            db.execute("""INSERT INTO noah.execution_records
                (id, request_id, task_id, actor_user_id, capability, status)
                VALUES (%s, %s, %s, %s, %s, 'running')""",
                (execution_id, request_id, task_id, actor, CAPABILITY))
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable", task_id, execution_id)

    try:
        observation = validate_observation(root, tool_runner(root))
    except ToolOutcomeUnknown:
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Timeout", 504,
            "Tool termination could not be verified", task_id, execution_id)
    except ToolFailure as failure:
        if not _finish_failure(connection_factory, task_id, execution_id, failure):
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                "Execution outcome could not be recorded", task_id, execution_id)
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Project document listing failed", task_id, execution_id)

    observed_at = datetime.now(timezone.utc)
    names = observation["filenames"]
    canonical = json.dumps({"project_id": str(project), "root_id": root_id,
        "filenames": names, "truncated": observation["truncated"]},
        ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    try:
        with connection_factory() as db:
            actor_again = _actor_for_token(db, token)
            if actor_again != actor or not _project_readable(db, actor, project):
                failure = ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
                raise failure
            db.execute("""INSERT INTO noah.document_tool_evidence
                (execution_id, project_id, root_id, observed_at, filenames,
                 result_count, truncated, result_sha256)
                VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s)""",
                (execution_id, project, root_id, observed_at,
                 json.dumps(names, ensure_ascii=False), len(names), observation["truncated"], digest))
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
        "answer": "확인된 문서: " + (", ".join(names) if names else "없음"),
        "files": names, "count": len(names), "truncated": observation["truncated"],
        "evidence": {"execution_id": str(execution_id), "root_id": root_id,
            "observed_at": observed_at.isoformat(), "result_sha256": digest},
    }
