"""M17: one Session-bound follow-up to one verified M10 document source."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from uuid import UUID, uuid4

import psycopg

from .db import connect, local_settings
from .document_answer import (MODEL_OUTPUT_TOKENS, MODEL_SCHEMA, assemble_answer,
    model_messages, reject_known_credentials,
    verify_model_evidence)
from .document_answer_query import _model_error, _permitted, _record_failure
from .document_auto import candidate_hash
from .document_query import _project_readable
from .document_read import (execute_document_read_with_identity,
    validate_document_name, validate_read_observation)
from .document_selected_query import _checked_identity
from .document_tool import ToolFailure, ToolOutcomeUnknown, operator_root
from .ollama import (OllamaClient, OllamaInvalidResponse, OllamaTimeout,
    OllamaUnavailable, OllamaUnsafeBinding)
from .service import _actor_for_token, _failure


CAPABILITY = "project.documents.answer.followup"
_M10 = "project.documents.answer.auto"


class ReservationFailure(Exception):
    def __init__(self, failure, task_id=None, execution_id=None):
        self.failure, self.task_id, self.execution_id = failure, task_id, execution_id
        super().__init__(failure.code)
_SOURCE_QUERY = """SELECT a.router_id,a.stage,a.validated_route,a.dispatch_prepared,
    a.delegate_result_observed,a.delegate_capability,a.delegate_request_id,
    a.delegate_task_id,a.delegate_execution_id,a.observation_class,a.http_status,
    a.outcome_code,
    e.request_id AS execution_request_id,e.task_id AS execution_task_id,
    e.actor_user_id AS execution_actor,e.capability AS execution_capability,
    e.status AS execution_status,e.verified_at,
    t.actor_user_id AS task_actor,t.status AS task_status,
    t.verification_status AS task_verification,
    p.project_id,p.root_id,p.candidate_names,p.candidate_count,p.candidate_sha256,
    p.selection_outcome,p.raw_candidate_names,p.selected_count,p.selected_names,
    p.answer_outcome,p.truncated,
    (SELECT count(*) FROM noah.auto_document_source_evidence s
        WHERE s.execution_id=e.id) AS source_count,
    s.source_id,s.source_ordinal,s.document_name,s.byte_length,
    s.content_sha256,s.content_encoding,s.bom_present,
    (SELECT jsonb_agg(jsonb_build_object('ordinal',q.quote_ordinal,
        'source_id',q.source_id,'quote',q.quote,'start',q.start_index,
        'end',q.end_index) ORDER BY q.quote_ordinal)
        FROM noah.auto_document_quote_evidence q WHERE q.execution_id=e.id) AS quotes
    FROM noah.routing_audit a
    LEFT JOIN noah.execution_records e ON e.id=a.delegate_execution_id
    LEFT JOIN noah.tasks t ON t.id=e.task_id
    LEFT JOIN noah.auto_document_answer_evidence p ON p.execution_id=e.id
    LEFT JOIN noah.auto_document_source_evidence s
        ON s.execution_id=e.id AND s.source_id='D1'
    WHERE a.session_id=%s AND a.actor_user_id=%s AND a.router_id<>%s"""


def _error(request_id, code, category, http_status, message, task_id=None, execution_id=None):
    return _failure(request_id, code, category, http_status, message,
                    task_id, execution_id)


def _unknown(request_id, task_id=None, execution_id=None):
    return _error(request_id, "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503,
                  "Follow-up outcome could not be confirmed", task_id, execution_id)


def _source_failure(code):
    descriptions = {
        "FOLLOWUP_SOURCE_NOT_FOUND": ("Invalid Input", 409),
        "FOLLOWUP_SOURCE_AMBIGUOUS": ("Invalid Input", 409),
        "FOLLOWUP_CONTEXT_UNCONFIRMED": ("Verification Failure", 409),
        "FOLLOWUP_PROVENANCE_INVALID": ("Verification Failure", 502),
    }
    category, status = descriptions[code]
    raise ToolFailure(code, category, status)


def _classify(rows, project, actor):
    """Classify the entire committed statement snapshot; never choose newest."""
    selected = []
    for row in rows:
        route = row["validated_route"]
        if row["stage"] != "observed":
            if route in (None, _M10):
                _source_failure("FOLLOWUP_CONTEXT_UNCONFIRMED")
            continue
        if route != _M10:
            continue
        if row["observation_class"] in ("delegate_uncertain", "correlation_unverified"):
            _source_failure("FOLLOWUP_CONTEXT_UNCONFIRMED")
        # A definite unsuccessful M10 attempt has no usable source.
        if row["http_status"] != 200 or row["observation_class"] != "delegate_returned":
            continue
        if row["project_id"] is None:
            _source_failure("FOLLOWUP_CONTEXT_UNCONFIRMED")
        if (not row["dispatch_prepared"] or not row["delegate_result_observed"]
                or row["delegate_capability"] != _M10
                or row["delegate_request_id"] is None
                or row["delegate_task_id"] is None
                or row["delegate_execution_id"] is None
                or row["execution_request_id"] != row["delegate_request_id"]
                or row["execution_task_id"] != row["delegate_task_id"]
                or row["execution_actor"] != actor or row["task_actor"] != actor
                or row["execution_capability"] != _M10
                or row["execution_status"] != "succeeded" or row["verified_at"] is None
                or row["task_status"] != "completed" or row["task_verification"] != "passed"
                or row["truncated"] is not False):
            _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        if row["project_id"] != project:
            # A different project is irrelevant only after its binding to
            # this actor's real M10 Execution/parent has been established.
            continue
        if row["selection_outcome"] == "none" and row["selected_count"] == 0:
            continue
        if row["selected_count"] == 2:
            _source_failure("FOLLOWUP_SOURCE_AMBIGUOUS")
        if (not isinstance(row["root_id"], str)
                or not isinstance(row["candidate_names"], list)
                or row["candidate_count"] != len(row["candidate_names"])
                or row["candidate_sha256"] != candidate_hash(
                    project, row["root_id"], row["candidate_names"])
                or row["outcome_code"] != row["answer_outcome"]):
            _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        if (row["selection_outcome"] != "selected" or row["selected_count"] != 1
                or not isinstance(row["selected_names"], list)
                or len(row["selected_names"]) != 1 or row["source_count"] != 1
                or row["source_id"] != "D1" or row["source_ordinal"] != 1
                or row["selected_names"][0] != row["document_name"]
                or row["raw_candidate_names"] != row["selected_names"]
                or row["document_name"] not in row["candidate_names"]):
            _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        if row["answer_outcome"] not in ("supported", "partial"):
            continue
        quotes = row["quotes"]
        if quotes is None or quotes == []:
            continue
        if (not isinstance(quotes, list) or not 1 <= len(quotes) <= 3
                or not isinstance(row["root_id"], str)
                or not isinstance(row["content_sha256"], str)
                or row["content_encoding"] != "utf-8"
                or not isinstance(row["bom_present"], bool)):
            _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        try:
            validate_document_name(row["document_name"])
        except ToolFailure:
            _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        for ordinal, item in enumerate(quotes, 1):
            if (not isinstance(item, dict) or item.get("ordinal") != ordinal
                    or item.get("source_id") != "D1"
                    or not isinstance(item.get("quote"), str)
                    or not 1 <= len(item["quote"]) <= 240
                    or not isinstance(item.get("start"), int)
                    or not isinstance(item.get("end"), int)
                    or item["start"] < 0 or item["end"] <= item["start"]):
                _source_failure("FOLLOWUP_PROVENANCE_INVALID")
        selected.append(row)
    if len(selected) > 1:
        _source_failure("FOLLOWUP_SOURCE_AMBIGUOUS")
    if not selected:
        _source_failure("FOLLOWUP_SOURCE_NOT_FOUND")
    return selected[0]


def _reserve_source(connection_factory, token, actor, session_id, router_id,
                    project, request_id):
    """Session lock, fresh complete statement snapshot, and reservation in one tx."""
    task_id = execution_id = None
    db = None
    commit_attempted = False
    try:
        db = connection_factory()
        db.execute("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        db.execute("SET LOCAL lock_timeout = '3s'")
        db.execute("SET LOCAL statement_timeout = '5s'")
        if _actor_for_token(db, token) != actor:
            raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
        # This lock may wait. The candidate query below starts a NEW statement
        # snapshot after it is acquired, as required by READ COMMITTED.
        session = db.execute("""SELECT owner_user_id FROM noah.sessions
            WHERE id=%s AND owner_user_id=%s FOR UPDATE""",
            (session_id, actor)).fetchone()
        if session is None:
            raise ToolFailure("SESSION_NOT_FOUND", "Permission Denied", 404)
        current = db.execute("""SELECT actor_user_id,session_id,stage,
            validated_route,dispatch_prepared FROM noah.routing_audit
            WHERE router_id=%s""", (router_id,)).fetchone()
        if (current is None or current["actor_user_id"] != actor
                or current["session_id"] != session_id
                or current["stage"] != "dispatch_prepared"
                or current["validated_route"] != CAPABILITY
                or not current["dispatch_prepared"]):
            _source_failure("FOLLOWUP_CONTEXT_UNCONFIRMED")
        rows = db.execute(_SOURCE_QUERY, (session_id, actor, router_id)).fetchall()
        prior = _classify(rows, project, actor)
        if _actor_for_token(db, token) != actor:
            raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
        if not _project_readable(db, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        task_id, execution_id = uuid4(), uuid4()
        db.execute("""INSERT INTO noah.tasks
            (id,actor_user_id,goal,status,verification_status)
            VALUES (%s,%s,%s,'running','pending')""",
            (task_id, actor, "Answer a verified project document follow-up"))
        db.execute("""INSERT INTO noah.execution_records
            (id,request_id,task_id,actor_user_id,capability,status)
            VALUES (%s,%s,%s,%s,%s,'running')""",
            (execution_id, request_id, task_id, actor, CAPABILITY))
        commit_attempted = True
        db.commit()
        return prior, task_id, execution_id
    except ToolFailure as error:
        if db is not None:
            try:
                db.rollback()
            except (psycopg.Error, OSError):
                raise ReservationFailure(ToolFailure(
                    "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503),
                    task_id, execution_id) from None
        raise ReservationFailure(error) from None
    except (psycopg.OperationalError, psycopg.InterfaceError, OSError):
        # A query/lock timeout with a confirmed rollback is an unavailable
        # candidate set. Only a lost commit/rollback acknowledgement is unknown.
        if not commit_attempted:
            try:
                if db is not None:
                    db.rollback()
            except (psycopg.Error, OSError):
                pass
            else:
                raise ReservationFailure(ToolFailure(
                    "FOLLOWUP_CONTEXT_UNAVAILABLE", "Environment Failure", 503)) from None
        raise ReservationFailure(ToolFailure(
            "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503),
            task_id, execution_id) from None
    except (psycopg.Error, ValueError):
        try:
            if db is not None:
                db.rollback()
        except (psycopg.Error, OSError):
            raise ReservationFailure(ToolFailure(
                "TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503),
                task_id, execution_id) from None
        raise ReservationFailure(ToolFailure(
            "FOLLOWUP_CONTEXT_UNAVAILABLE", "Environment Failure", 503)) from None
    finally:
        if db is not None:
            try:
                db.close()
            except (psycopg.Error, OSError):
                pass


def _same_source(prior, observation, root_id):
    return (root_id == prior["root_id"]
            and observation["byte_length"] == prior["byte_length"]
            and observation["content_sha256"] == prior["content_sha256"]
            and observation["bom_present"] == prior["bom_present"])


def _read_same(prior, project, root_provider, read_runner, credentials):
    root_id, root = root_provider(project)
    if (not isinstance(root_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", root_id)
            or not isinstance(root, Path) or not root.is_absolute()
            or root_id != prior["root_id"]):
        raise ToolFailure("FOLLOWUP_SOURCE_CHANGED", "Verification Failure", 409)
    name = prior["document_name"]
    try:
        raw, identity = read_runner(root, name)
        _checked_identity(identity)
        observation = validate_read_observation(root, name, raw)
    except ToolFailure as error:
        if error.code == "DOCUMENT_NOT_FOUND":
            raise ToolFailure("FOLLOWUP_SOURCE_CHANGED", "Verification Failure", 409) from None
        raise
    if not _same_source(prior, observation, root_id):
        raise ToolFailure("FOLLOWUP_SOURCE_CHANGED", "Verification Failure", 409)
    content = observation["content"]
    for item in prior["quotes"]:
        quote = item["quote"]
        if (content.find(quote) != item["start"]
                or item["end"] != item["start"] + len(quote)):
            raise ToolFailure("FOLLOWUP_PROVENANCE_INVALID", "Verification Failure", 502)
    reject_known_credentials(name, credentials)
    reject_known_credentials(content, credentials)
    return observation


def _commit_success(connection_factory, token, actor, project, task_id,
                    execution_id, router_id, prior, observation, observed_at,
                    outcome, quotes):
    """Evidence and both terminal states have one confirmed commit boundary."""
    db = None
    try:
        db = connection_factory()
        if (_actor_for_token(db, token) != actor
                or not _project_readable(db, actor, project)):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        db.execute("""INSERT INTO noah.document_followup_evidence
            (execution_id,current_router_id,prior_router_id,prior_execution_id,
             project_id,root_id,document_name,prior_content_sha256,
             content_sha256,byte_length,content_encoding,bom_present,
             observed_at,outcome,quotes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'utf-8',%s,%s,%s,%s::jsonb)""",
            (execution_id, router_id, prior["router_id"], prior["delegate_execution_id"],
             project, prior["root_id"], prior["document_name"],
             prior["content_sha256"], observation["content_sha256"],
             observation["byte_length"], observation["bom_present"],
             observed_at, outcome, json.dumps(quotes, ensure_ascii=False)))
        task = db.execute("""UPDATE noah.tasks SET status='completed',
            verification_status='passed',updated_at=now()
            WHERE id=%s AND actor_user_id=%s AND status='running'""",
            (task_id, actor))
        execution = db.execute("""UPDATE noah.execution_records SET status='succeeded',
            verified_at=now(),updated_at=now()
            WHERE id=%s AND task_id=%s AND actor_user_id=%s AND status='running'
                AND capability=%s""", (execution_id, task_id, actor, CAPABILITY))
        if task.rowcount != 1 or execution.rowcount != 1:
            raise ToolFailure("FOLLOWUP_PROVENANCE_INVALID", "Verification Failure", 502)
        db.commit()
    except ToolFailure:
        try:
            if db is not None:
                db.rollback()
        except (psycopg.Error, OSError):
            raise ToolFailure("TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503) from None
        raise
    except (psycopg.OperationalError, psycopg.InterfaceError, OSError):
        raise ToolFailure("TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503) from None
    except (psycopg.Error, ValueError):
        try:
            if db is not None:
                db.rollback()
        except (psycopg.Error, OSError):
            raise ToolFailure("TOOL_OUTCOME_UNKNOWN", "Environment Failure", 503) from None
        raise ToolFailure("EVIDENCE_WRITE_FAILED", "Environment Failure", 503) from None
    finally:
        if db is not None:
            try:
                db.close()
            except (psycopg.Error, OSError):
                pass


def answer_followup_document(project_id, question, token, actor, session_id,
                             router_id, connection_factory=connect,
                             root_provider=operator_root,
                             read_runner=execute_document_read_with_identity,
                             model=None, settings_provider=local_settings):
    """A single M17 delegate call, with no M10/M8 HTTP or Task nesting."""
    request_id = uuid4()
    task_id = execution_id = None
    project = UUID(project_id)
    try:
        prior, task_id, execution_id = _reserve_source(
            connection_factory, token, actor, session_id, router_id, project, request_id)
    except ReservationFailure as reservation:
        error = reservation.failure
        return _error(request_id, error.code, error.category, error.http_status,
                      "Follow-up source could not be established",
                      reservation.task_id, reservation.execution_id)
    try:
        credentials = (token, settings_provider()["POSTGRES_PASSWORD"])
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        observation = _read_same(prior, project, root_provider, read_runner, credentials)
        observed_at = datetime.now(timezone.utc)
        messages = model_messages(question, prior["document_name"], observation["content"])
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        model = model if model is not None else OllamaClient()
        output = model.complete(messages, MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
        outcome, quotes = verify_model_evidence(output, observation["content"])
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        second = _read_same(prior, project, root_provider, read_runner, credentials)
        if second["content_sha256"] != observation["content_sha256"]:
            raise ToolFailure("FOLLOWUP_SOURCE_CHANGED", "Verification Failure", 409)
        _commit_success(connection_factory, token, actor, project, task_id,
                        execution_id, router_id, prior, observation, observed_at,
                        outcome, quotes)
    except (OllamaUnsafeBinding, OllamaTimeout, OllamaUnavailable,
            OllamaInvalidResponse) as error:
        return _record_failure(connection_factory, request_id, task_id, execution_id,
                               _model_error(error))
    except ToolOutcomeUnknown:
        return _unknown(request_id, task_id, execution_id)
    except ToolFailure as error:
        if error.code == "TOOL_OUTCOME_UNKNOWN":
            return _unknown(request_id, task_id, execution_id)
        return _record_failure(connection_factory, request_id, task_id, execution_id, error)
    except (psycopg.Error, OSError, ValueError, TypeError, KeyError):
        return _unknown(request_id, task_id, execution_id)
    try:
        if not _permitted(connection_factory, token, actor, project):
            return _error(request_id, "PROJECT_NOT_FOUND", "Permission Denied", 404,
                          "Project not found", task_id, execution_id)
        final = _read_same(prior, project, root_provider, read_runner, credentials)
        if final["content_sha256"] != observation["content_sha256"]:
            raise ToolFailure("FOLLOWUP_SOURCE_CHANGED", "Verification Failure", 409)
        if not _permitted(connection_factory, token, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
    except ToolFailure as error:
        return _error(request_id, error.code, error.category, error.http_status,
                      "Project not found" if error.code == "PROJECT_NOT_FOUND"
                      else "Follow-up source changed before disclosure",
                      task_id, execution_id)
    except (psycopg.Error, OSError, ValueError):
        return _unknown(request_id, task_id, execution_id)
    return 200, {"status": "succeeded", "request_id": str(request_id),
        "task_id": str(task_id), "execution_id": str(execution_id),
        "capability": CAPABILITY, "project_id": str(project),
        "outcome": outcome, "grounded": bool(quotes),
        "answer": assemble_answer(outcome, quotes),
        "document": {"root_id": prior["root_id"],
            "document_name": prior["document_name"],
            "byte_length": observation["byte_length"],
            "content_sha256": observation["content_sha256"],
            "observed_at": observed_at.isoformat(),
            "evidence_execution_id": str(execution_id)},
        "context_source": {"prior_router_id": str(prior["router_id"]),
            "prior_execution_id": str(prior["delegate_execution_id"])},
        "evidence": quotes}
