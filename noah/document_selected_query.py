"""One authorized execution for two explicitly selected project documents."""

from datetime import datetime, timezone
from pathlib import Path
import re
from uuid import UUID, uuid4

import psycopg

from .db import connect, local_settings
from .document_answer import reject_known_credentials, validate_question
from .document_answer_query import _model_error, _permitted, _record_failure
from .document_query import _project_readable
from .document_read import (
    execute_document_read_with_identity, validate_document_name,
    validate_read_observation,
)
from .document_selected_answer import (
    CAPABILITY, MODEL_OUTPUT_TOKENS, MODEL_SCHEMA, assemble_answer,
    model_messages, verify_model_evidence,
)
from .document_tool import ToolFailure, ToolOutcomeUnknown, operator_root
from .ollama import (
    OllamaClient, OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable,
    OllamaUnsafeBinding,
)
from .service import _actor_for_token, _failure


def _source_failure(error, source_id):
    """Keep the original failure kind and identify which required read failed."""
    return ToolFailure(f"{source_id}_{error.code}", error.category, error.http_status)


def _checked_identity(value):
    if (not isinstance(value, tuple) or len(value) not in (2, 3)
            or any(type(part) is not int or part < 0 for part in value)
            or not any(value)):
        raise ToolFailure("DOCUMENT_IDENTITY_UNAVAILABLE", "Verification Failure", 502)
    return value


def answer_selected_documents(project_id, payload, token, connection_factory=connect,
                              root_provider=operator_root,
                              tool_runner=execute_document_read_with_identity,
                              model=None):
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

    if not isinstance(payload, dict) or set(payload) != {"document_names", "question"}:
        return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
            "Two document names and one question are required")
    names = payload["document_names"]
    if not isinstance(names, list) or len(names) != 2:
        return _failure(request_id, "INVALID_DOCUMENT_COUNT", "Invalid Input", 400,
            "Exactly two document names are required")
    for source_id, name in zip(("D1", "D2"), names):
        try:
            validate_document_name(name)
            name.encode("utf-8")
        except ToolFailure as error:
            failure = _source_failure(error, source_id)
            return _failure(request_id, failure.code, failure.category,
                failure.http_status, "Document name is invalid")
        except UnicodeError:
            return _failure(request_id, f"{source_id}_INVALID_DOCUMENT_IDENTIFIER",
                "Invalid Input", 400, "Document name is invalid")
    if names[0].casefold() == names[1].casefold():
        return _failure(request_id, "DUPLICATE_DOCUMENT_NAME", "Invalid Input", 400,
            "Two distinct document names are required")
    try:
        question = validate_question(payload["question"])
        credentials = (token, local_settings()["POSTGRES_PASSWORD"])
        reject_known_credentials(question, credentials)
    except ToolFailure as failure:
        return _failure(request_id, failure.code, failure.category,
            failure.http_status, "Question is invalid")
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
        return _failure(request_id, failure.code, failure.category,
            failure.http_status, "Project document root is unavailable")
    except (OSError, ValueError, TypeError):
        return _failure(request_id, "PROJECT_ROOT_CONFIG_INVALID", "Environment Failure", 503,
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
                (task_id, actor, "Answer two selected project documents"))
            db.execute("""INSERT INTO noah.execution_records
                (id, request_id, task_id, actor_user_id, capability, status)
                VALUES (%s, %s, %s, %s, %s, 'running')""",
                (execution_id, request_id, task_id, actor, CAPABILITY))
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id,
            "TOOL_OUTCOME_UNKNOWN" if task_id else "DATABASE_UNAVAILABLE",
            "Environment Failure", 503, "Execution reservation could not be verified",
            task_id, execution_id)

    sources, identities = {}, {}
    for source_id, name in zip(("D1", "D2"), names):
        try:
            if not _permitted(connection_factory, token, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            result = tool_runner(root, name)
            if not isinstance(result, tuple) or len(result) != 2:
                raise ToolFailure("DOCUMENT_IDENTITY_UNAVAILABLE", "Verification Failure", 502)
            raw, identity = result
            identity = _checked_identity(identity)
            # Verification reopens the path; permission must precede that read.
            if not _permitted(connection_factory, token, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            observation = validate_read_observation(root, name, raw)
            reject_known_credentials(observation["content"], credentials)
            identities[source_id] = identity
            sources[source_id] = {"document_name": name, "content": observation["content"],
                "byte_length": observation["byte_length"],
                "content_sha256": observation["content_sha256"],
                "bom_present": observation["bom_present"],
                "observed_at": datetime.now(timezone.utc)}
        except ToolOutcomeUnknown:
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Timeout", 504,
                "Document termination could not be verified", task_id, execution_id)
        except ToolFailure as error:
            return _record_failure(connection_factory, request_id, task_id,
                execution_id, _source_failure(error, source_id))
        except (psycopg.Error, OSError, ValueError):
            return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                "Document outcome could not be verified", task_id, execution_id)

    if identities["D1"] == identities["D2"]:
        return _record_failure(connection_factory, request_id, task_id, execution_id,
            ToolFailure("DOCUMENT_ALIAS", "Invalid Input", 409))

    try:
        messages = model_messages(question, sources)
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Permission could not be verified", task_id, execution_id)

    model = model if model is not None else OllamaClient()
    try:
        proposal = model.complete(messages, MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
        outcome, quotes = verify_model_evidence(proposal, sources)
    except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable,
            OllamaInvalidResponse) as error:
        return _record_failure(connection_factory, request_id, task_id,
            execution_id, _model_error(error))
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (TypeError, ValueError, KeyError):
        return _record_failure(connection_factory, request_id, task_id, execution_id,
            ToolFailure("MODEL_OUTPUT_INVALID", "Verification Failure", 502))

    try:
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            db.execute("""INSERT INTO noah.selected_document_answer_evidence
                (execution_id, project_id, outcome) VALUES (%s, %s, %s)""",
                (execution_id, project, outcome))
            for source_ordinal, source_id in enumerate(("D1", "D2"), 1):
                item = sources[source_id]
                db.execute("""INSERT INTO noah.selected_document_source_evidence
                    (execution_id, source_id, source_ordinal, root_id, document_name,
                     observed_at, byte_length, content_sha256, content_encoding, bom_present)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'utf-8', %s)""",
                    (execution_id, source_id, source_ordinal, root_id,
                     item["document_name"], item["observed_at"], item["byte_length"],
                     item["content_sha256"], item["bom_present"]))
            for quote_ordinal, item in enumerate(quotes, 1):
                db.execute("""INSERT INTO noah.selected_document_quote_evidence
                    (execution_id, quote_ordinal, source_id, quote, start_index, end_index)
                    VALUES (%s, %s, %s, %s, %s, %s)""",
                    (execution_id, quote_ordinal, item["source_id"], item["quote"],
                     item["start"], item["end"]))
            db.execute("""UPDATE noah.tasks SET status = 'completed',
                verification_status = 'passed', updated_at = now() WHERE id = %s""", (task_id,))
            db.execute("""UPDATE noah.execution_records SET status = 'succeeded',
                verified_at = now(), updated_at = now() WHERE id = %s""", (execution_id,))
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Execution outcome could not be verified", task_id, execution_id)

    try:
        if not _permitted(connection_factory, token, actor, project):
            return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                "Project not found")
    except (psycopg.Error, OSError, ValueError):
        return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
            "Permission could not be verified")

    evidence = [{**item, "content_sha256": sources[item["source_id"]]["content_sha256"]}
                for item in quotes]
    source_result = [{"source_id": source_id, "root_id": root_id,
        "document_name": sources[source_id]["document_name"],
        "observed_at": sources[source_id]["observed_at"].isoformat(),
        "byte_length": sources[source_id]["byte_length"],
        "content_sha256": sources[source_id]["content_sha256"],
        "content_encoding": "utf-8", "bom_present": sources[source_id]["bom_present"],
        "evidence_execution_id": str(execution_id)} for source_id in ("D1", "D2")]
    return 200, {
        "status": "succeeded", "request_id": str(request_id),
        "task_id": str(task_id), "execution_id": str(execution_id),
        "capability": CAPABILITY, "project_id": str(project),
        "outcome": outcome, "grounded": bool(quotes),
        "answer": assemble_answer(outcome, quotes),
        "sources": source_result, "evidence": evidence,
    }
