"""One authorized M10 execution: complete names, bounded selection, grounded answer."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from uuid import UUID, uuid4

import psycopg

from .db import connect, local_settings
from .document_answer import (
    MODEL_OUTPUT_TOKENS as ONE_TOKENS, MODEL_SCHEMA as ONE_SCHEMA,
    assemble_answer as assemble_one, model_messages as messages_one,
    reject_known_credentials, validate_question, verify_model_evidence as verify_one,
)
from .document_answer_query import _model_error, _permitted, _record_failure
from .document_auto import (
    CAPABILITY, MODEL_OUTPUT_TOKENS, MODEL_SCHEMA, candidate_hash,
    eligible_candidates, selection_messages, verify_selection,
)
from .document_query import _project_readable
from .document_read import execute_document_read_with_identity, validate_read_observation
from .document_selected_answer import (
    MODEL_OUTPUT_TOKENS as TWO_TOKENS, MODEL_SCHEMA as TWO_SCHEMA,
    assemble_answer as assemble_two, model_messages as messages_two,
    verify_model_evidence as verify_two,
)
from .document_selected_query import _checked_identity
from .document_tool import (
    ToolFailure, ToolOutcomeUnknown, execute_document_tool, operator_root,
    validate_observation,
)
from .ollama import (
    OllamaClient, OllamaInvalidResponse, OllamaTimeout, OllamaUnavailable,
    OllamaUnsafeBinding,
)
from .service import _actor_for_token, _failure


def _uncertain(request_id, task_id, execution_id, message="Execution outcome could not be verified"):
    return _failure(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                    message, task_id, execution_id)


def _model_failure(error, phase):
    failure = _model_error(error)
    if failure.code.startswith("OLLAMA_"):
        return ToolFailure(f"{phase}_{failure.code}", failure.category, failure.http_status)
    return ToolFailure(f"{phase}_MODEL_OUTPUT_INVALID", failure.category, failure.http_status)


def answer_auto_documents(project_id, payload, token, connection_factory=connect,
                          root_provider=operator_root, list_runner=execute_document_tool,
                          read_runner=execute_document_read_with_identity, model=None):
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
    if not isinstance(payload, dict) or set(payload) != {"question"}:
        return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                        "One question is required")
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
                (task_id, actor, "Answer with controlled project document selection"))
            db.execute("""INSERT INTO noah.execution_records
                (id, request_id, task_id, actor_user_id, capability, status)
                VALUES (%s, %s, %s, %s, %s, 'running')""",
                (execution_id, request_id, task_id, actor, CAPABILITY))
    except (psycopg.Error, OSError, ValueError):
        return _uncertain(request_id, task_id, execution_id) if task_id else _failure(
            request_id, "DATABASE_UNAVAILABLE", "Environment Failure", 503,
            "Storage is unavailable")

    try:
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        observation = validate_observation(root, list_runner(root))
        observed_at = datetime.now(timezone.utc)
        candidates = eligible_candidates(observation)
        for name in candidates:
            reject_known_credentials(name, credentials)
        digest = candidate_hash(project, root_id, candidates)
        selection_prompt = selection_messages(question, candidates)
    except ToolOutcomeUnknown:
        return _uncertain(request_id, task_id, execution_id,
                          "Tool termination could not be verified")
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError, UnicodeError):
        return _uncertain(request_id, task_id, execution_id)

    model = model if model is not None else OllamaClient()
    if candidates:
        try:
            if not _permitted(connection_factory, token, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            proposal = model.complete(selection_prompt, MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
            selection_outcome, selected = verify_selection(proposal, candidates)
        except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable,
                OllamaInvalidResponse) as error:
            return _record_failure(connection_factory, request_id, task_id, execution_id,
                                   _model_failure(error, "SELECTION"))
        except ToolFailure as failure:
            return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
        except (psycopg.Error, OSError, ValueError):
            return _uncertain(request_id, task_id, execution_id)
    else:
        selection_outcome, selected = "none", []

    sources, identities, quotes = {}, {}, []
    answer_outcome = None
    if selected:
        for source_id, name in zip(("D1", "D2"), selected):
            try:
                if not _permitted(connection_factory, token, actor, project):
                    raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
                raw, identity = read_runner(root, name)
                identity = _checked_identity(identity)
                if not _permitted(connection_factory, token, actor, project):
                    raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
                item = validate_read_observation(root, name, raw)
                reject_known_credentials(item["content"], credentials)
                identities[source_id] = identity
                sources[source_id] = {"document_name": name, "observed_at": datetime.now(timezone.utc),
                    "content": item["content"], "byte_length": item["byte_length"],
                    "content_sha256": item["content_sha256"], "bom_present": item["bom_present"]}
            except ToolOutcomeUnknown:
                return _uncertain(request_id, task_id, execution_id,
                                  "Document termination could not be verified")
            except ToolFailure as failure:
                return _record_failure(connection_factory, request_id, task_id, execution_id,
                    ToolFailure(f"{source_id}_{failure.code}", failure.category, failure.http_status))
            except (psycopg.Error, OSError, ValueError, TypeError):
                return _uncertain(request_id, task_id, execution_id)
        if len(selected) == 2 and identities["D1"] == identities["D2"]:
            return _record_failure(connection_factory, request_id, task_id, execution_id,
                ToolFailure("DOCUMENT_ALIAS", "Invalid Input", 409))
        try:
            if len(selected) == 1:
                messages = messages_one(question, selected[0], sources["D1"]["content"])
                schema, tokens = ONE_SCHEMA, ONE_TOKENS
            else:
                messages = messages_two(question, sources)
                schema, tokens = TWO_SCHEMA, TWO_TOKENS
            if not _permitted(connection_factory, token, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            answer_proposal = model.complete(messages, schema, tokens)
            if len(selected) == 1:
                answer_outcome, verified = verify_one(answer_proposal, sources["D1"]["content"])
                quotes = [{"source_id": "D1", **item} for item in verified]
            else:
                answer_outcome, quotes = verify_two(answer_proposal, sources)
        except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable,
                OllamaInvalidResponse) as error:
            return _record_failure(connection_factory, request_id, task_id, execution_id,
                                   _model_failure(error, "ANSWER"))
        except ToolFailure as failure:
            return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
        except (psycopg.Error, OSError, ValueError, TypeError, KeyError):
            return _uncertain(request_id, task_id, execution_id)

    try:
        with connection_factory() as db:
            if _actor_for_token(db, token) != actor or not _project_readable(db, actor, project):
                raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
            db.execute("""INSERT INTO noah.auto_document_answer_evidence
                (execution_id, project_id, root_id, candidates_observed_at,
                 candidate_names, candidate_count, truncated, candidate_sha256,
                 selection_model_called, selection_outcome, raw_candidate_names,
                 selected_names, selected_count, answer_outcome)
                VALUES (%s,%s,%s,%s,%s::jsonb,%s,false,%s,%s,%s,%s::jsonb,%s::jsonb,%s,%s)""",
                (execution_id, project, root_id, observed_at,
                 json.dumps(candidates, ensure_ascii=False), len(candidates), digest,
                 bool(candidates), selection_outcome, json.dumps(selected, ensure_ascii=False),
                 json.dumps(selected, ensure_ascii=False), len(selected), answer_outcome))
            for ordinal, name in enumerate(selected, 1):
                source_id, item = f"D{ordinal}", sources[f"D{ordinal}"]
                db.execute("""INSERT INTO noah.auto_document_source_evidence
                    (execution_id, source_id, source_ordinal, document_name, observed_at,
                     byte_length, content_sha256, content_encoding, bom_present)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,'utf-8',%s)""",
                    (execution_id, source_id, ordinal, name, item["observed_at"],
                     item["byte_length"], item["content_sha256"], item["bom_present"]))
            for ordinal, item in enumerate(quotes, 1):
                db.execute("""INSERT INTO noah.auto_document_quote_evidence
                    (execution_id, quote_ordinal, source_id, quote, start_index, end_index)
                    VALUES (%s,%s,%s,%s,%s,%s)""",
                    (execution_id, ordinal, item["source_id"], item["quote"],
                     item["start"], item["end"]))
            db.execute("""UPDATE noah.tasks SET status='completed',
                verification_status='passed', updated_at=now() WHERE id=%s""", (task_id,))
            db.execute("""UPDATE noah.execution_records SET status='succeeded',
                verified_at=now(), updated_at=now() WHERE id=%s""", (execution_id,))
    except ToolFailure as failure:
        return _record_failure(connection_factory, request_id, task_id, execution_id, failure)
    except (psycopg.Error, OSError, ValueError):
        return _uncertain(request_id, task_id, execution_id)

    try:
        if not _permitted(connection_factory, token, actor, project):
            return _failure(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                            "Project not found")
    except (psycopg.Error, OSError, ValueError):
        return _uncertain(request_id, task_id, execution_id)

    if not selected:
        answer = "이번 후보 관찰에서 모델이 문서를 선택하지 않았습니다."
        outcome = "no_document_selected"
    elif len(selected) == 1:
        answer, outcome = assemble_one(answer_outcome, quotes), answer_outcome
    else:
        answer, outcome = assemble_two(answer_outcome, quotes), answer_outcome
    return 200, {
        "status": "succeeded", "request_id": str(request_id), "task_id": str(task_id),
        "execution_id": str(execution_id), "capability": CAPABILITY,
        "project_id": str(project), "outcome": outcome, "grounded": bool(quotes),
        "answer": answer, "selected_document_names": selected,
        "candidate_observation": {"root_id": root_id, "observed_at": observed_at.isoformat(),
            "count": len(candidates), "truncated": False, "sha256": digest,
            "evidence_execution_id": str(execution_id)},
        "sources": [{"source_id": f"D{i}", "document_name": name,
            "root_id": root_id, "observed_at": sources[f"D{i}"]["observed_at"].isoformat(),
            "byte_length": sources[f"D{i}"]["byte_length"],
            "content_sha256": sources[f"D{i}"]["content_sha256"],
            "content_encoding": "utf-8", "bom_present": sources[f"D{i}"]["bom_present"]}
            for i, name in enumerate(selected, 1)],
        "evidence": [{**item, "content_sha256": sources[item["source_id"]]["content_sha256"]}
                     for item in quotes],
    }
