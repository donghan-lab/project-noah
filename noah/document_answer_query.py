"""One authorized document observation and one grounded local-model response."""

import json
from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import UUID, uuid4

import psycopg

from .db import connect, local_settings
from .document_answer import (
    CAPABILITY, MODEL_OUTPUT_TOKENS, MODEL_SCHEMA, assemble_answer,
    model_messages, reject_known_credentials, validate_question,
    verify_model_evidence,
)
from .document_query import _finish_failure, _project_readable
from .document_read import (
    execute_document_read, validate_document_name, validate_read_observation,
)
from .document_tool import ToolFailure, ToolOutcomeUnknown, operator_root
from .ollama import (
    OllamaClient, OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable,
    OllamaUnsafeBinding,
)
from .service import _actor_for_token, _failure


def _permitted(connection_factory, token, actor, project):
    with connection_factory() as db:
        return _actor_for_token(db, token) == actor and _project_readable(db, actor, project)


def _record_failure(connection_factory, request_id, task_id, execution_id, failure):
    if not _finish_failure(connection_factory, task_id, execution_id, failure):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be recorded", task_id, execution_id)
    return _failure(request_id, failure.code, failure.category, failure.http_status,
        "Document question could not be completed", task_id, execution_id)


def _model_error(error):
    if isinstance(error, OllamaUnsafeBinding):
        return ToolFailure("OLLAMA_NOT_LOCAL", "Policy Violation", 503)
    if isinstance(error, OllamaTimeout):
        # The adapter is synchronous. Once it raises, no NOAH model callback
        # remains that could commit an answer for this attempt.
        return ToolFailure("OLLAMA_TIMEOUT", "Timeout", 504)
    if isinstance(error, OllamaUnavailable):
        return ToolFailure("OLLAMA_UNAVAILABLE", "External Service Failure", 503)
    return ToolFailure("MODEL_OUTPUT_INVALID", "Verification Failure", 502)


def answer_project_document(project_id, payload, token, connection_factory=connect,
                            root_provider=operator_root,
                            tool_runner=execute_document_read, model=None):
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

    if not isinstance(payload, dict) or set(payload) != {"document_name", "question"}:
        return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
            "One document name and question are required")
    try:
        name = validate_document_name(payload["document_name"])
        try:
            name.encode("utf-8")
        except UnicodeError:
            raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400) from None
        question = validate_question(payload["question"])
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Document name or question is invalid")

    try:
        credentials = (token, local_settings()["POSTGRES_PASSWORD"])
        reject_known_credentials(question, credentials)
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category, failure.http_status,
            "Question contains a protected credential")
    except (OSError, ValueError, KeyError):
        return _failure(request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Local configuration is unavailable")

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
                (task_id, actor, "Answer one project document question"))
            db.execute("""INSERT INTO noah.execution_records
                (id, request_id, task_id, actor_user_id, capability, status)
                VALUES (%s, %s, %s, %s, %s, 'running')""",
                (execution_id, request_id, task_id, actor, CAPABILITY))
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id,
            "TOOL_OUTCOME_UNKNOWN" if task_id else "DATABASE_UNAVAILABLE",
            "Environment Failure", 503, "Execution reservation could not be verified",
            task_id, execution_id)

    try:
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Permission could not be verified", task_id, execution_id)

    try:
        raw = tool_runner(root, name)
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        observation = validate_read_observation(root, name, raw)
        observed_at = datetime.now(timezone.utc)
        reject_known_credentials(observation["content"], credentials)
        messages = model_messages(question, name, observation["content"])
    except ToolOutcomeUnknown:
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Timeout", 504,
            "Tool termination could not be verified", task_id, execution_id)
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Document outcome could not be verified", task_id, execution_id)

    try:
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Permission could not be verified", task_id, execution_id)

    model = model if model is not None else OllamaClient()
    try:
        proposed = model.complete(messages, MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
        outcome, quotes = verify_model_evidence(proposed, observation["content"])
    except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable,
            OllamaInvalidResponse) as error:
        return _record_failure(connection_factory, request_id, task_id, execution_id,
            _model_error(error))
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (TypeError, ValueError, KeyError):
        return _record_failure(connection_factory, request_id, task_id, execution_id,
            ToolFailure("MODEL_OUTPUT_INVALID", "Verification Failure", 502))

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
            db.execute("""INSERT INTO noah.document_answer_evidence
                (execution_id, outcome, quotes) VALUES (%s, %s, %s::jsonb)""",
                (execution_id, outcome, json.dumps(quotes, ensure_ascii=False)))
            db.execute("""UPDATE noah.tasks SET status = 'completed',
                verification_status = 'passed', updated_at = now() WHERE id = %s""", (task_id,))
            db.execute("""UPDATE noah.execution_records SET status = 'succeeded',
                verified_at = now(), updated_at = now() WHERE id = %s""", (execution_id,))
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be verified", task_id, execution_id)

    # The final authorization check is after commit: a completed observation
    # may exist, but revoked access must never release its quotations.
    try:
        if not _permitted(connection_factory, token, actor, project):
            return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                "Project not found")
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Permission could not be verified")

    return 200, {
        "status": "succeeded", "request_id": str(request_id),
        "task_id": str(task_id), "execution_id": str(execution_id),
        "capability": CAPABILITY, "project_id": str(project),
        "document_name": name, "outcome": outcome, "grounded": bool(quotes),
        "answer": assemble_answer(outcome, quotes), "evidence": quotes,
        "document": {"root_id": root_id, "document_name": name,
            "observed_at": observed_at.isoformat(),
            "byte_length": observation["byte_length"],
            "content_sha256": observation["content_sha256"],
            "evidence_execution_id": str(execution_id)},
    }
