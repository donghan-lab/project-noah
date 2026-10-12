"""One immutable document work definition and one explicitly claimed attempt."""

import base64
import binascii
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl
from uuid import UUID, uuid4

import psycopg

from .db import connect, local_settings
from .document_answer import (CAPABILITY, MODEL_OUTPUT_TOKENS, MODEL_SCHEMA,
    OUTCOMES, assemble_answer, model_messages, reject_known_credentials,
    validate_question, verify_model_evidence)
from .document_answer_query import _model_error
from .document_query import _project_readable
from .document_read import (execute_document_read, validate_document_name,
    validate_read_observation)
from .document_tool import ToolFailure, ToolOutcomeUnknown, operator_root
from .ollama import (OllamaClient, OllamaInvalidResponse, OllamaTimeout,
    OllamaUnavailable, OllamaUnsafeBinding)
from .service import _actor_for_token, _failure

KIND = "project.document.question"
GOAL = "Answer an explicitly registered project document question"
_SELECT = """SELECT t.id,t.actor_user_id,t.goal,t.status,t.verification_status,
    t.created_at,t.updated_at,d.registration_request_id,d.project_id,
    d.document_name,d.question,d.execution_id
    FROM noah.tasks t JOIN noah.document_question_tasks d ON d.task_id=t.id"""


def _uuid(value):
    try:
        parsed = UUID(value) if isinstance(value, str) else None
        return parsed if parsed is not None and str(parsed) == value else None
    except ValueError:
        return None


def _error(request, error, task=None, execution=None):
    return _failure(request, error.code, error.category, error.http_status,
        "Document task operation could not be completed", task, execution)


def _unknown(request, task=None, execution=None):
    return _error(request, ToolFailure("TASK_OUTCOME_UNKNOWN"), task, execution)


def _storage_error(error):
    if isinstance(error, (psycopg.errors.LockNotAvailable,
            psycopg.errors.QueryCanceled, psycopg.errors.DeadlockDetected)):
        return ToolFailure("TASK_BUSY", "Timeout", 503)
    return ToolFailure("DATABASE_UNAVAILABLE")


def _close(db):
    if db is not None:
        try:
            db.close()
        except (psycopg.Error, OSError):
            pass


def _rollback(db):
    try:
        db.rollback()
        return True
    except (psycopg.Error, OSError):
        return False


def _begin(db, inspection=False):
    db.execute("SET TRANSACTION ISOLATION LEVEL " +
        ("REPEATABLE READ, READ ONLY" if inspection else "READ COMMITTED"))
    db.execute("SET LOCAL lock_timeout='3s'")
    db.execute("SET LOCAL statement_timeout='5s'")


def _actor(db, token):
    actor = _actor_for_token(db, token)
    if actor is None:
        raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
    return actor


def _options(query, forbidden):
    if forbidden or query:
        raise ToolFailure("INVALID_REQUEST", "Invalid Input", 400)


def _owned(db, actor, task):
    row = db.execute(_SELECT + " WHERE t.id=%s AND t.actor_user_id=%s",
        (task, actor)).fetchone()
    if row is None or not _project_readable(db, actor, row["project_id"]):
        raise ToolFailure("TASK_NOT_FOUND", "Permission Denied", 404)
    return row


def _inconsistent():
    raise ToolFailure("TASK_RECORD_INCONSISTENT", "Verification Failure", 502)


def _definition(row):
    return {"project_id": str(row["project_id"]),
        "document_name": row["document_name"], "question": row["question"]}


def _public(row):
    return {"id": str(row["id"]), "kind": KIND, "status": row["status"],
        "verification_status": row["verification_status"],
        "created_at": row["created_at"].isoformat(),
        "updated_at": row["updated_at"].isoformat(),
        "registration_request_id": str(row["registration_request_id"]),
        "definition": _definition(row)}


def _materialize(db, row):
    """Use one snapshot; never read a document to reconstruct historic results."""
    try:
        if (row["goal"] != GOAL or validate_question(row["question"]) != row["question"]
                or validate_document_name(row["document_name"]) != row["document_name"]):
            _inconsistent()
    except (ToolFailure, UnicodeError, TypeError):
        _inconsistent()
    executions = db.execute("SELECT * FROM noah.execution_records WHERE task_id=%s",
        (row["id"],)).fetchall()
    if row["status"] == "ready":
        if executions or row["execution_id"] is not None or row["verification_status"] != "pending":
            _inconsistent()
        return None, None
    if len(executions) != 1:
        _inconsistent()
    execution = executions[0]
    if (execution["id"] != row["execution_id"]
            or execution["actor_user_id"] != row["actor_user_id"]
            or execution["capability"] != CAPABILITY or execution["memory_id"] is not None):
        _inconsistent()
    read = db.execute("SELECT * FROM noah.document_read_evidence WHERE execution_id=%s",
        (execution["id"],)).fetchone()
    answer = db.execute("SELECT * FROM noah.document_answer_evidence WHERE execution_id=%s",
        (execution["id"],)).fetchone()
    result = failure = None
    states = row["status"], row["verification_status"], execution["status"]
    if states == ("running", "pending", "running"):
        observation = "unconfirmed"
        if read or answer or execution["verified_at"] is not None or execution["failure_code"]:
            _inconsistent()
    elif states == ("failed", "failed", "failed"):
        observation = "recorded_failure"
        if read or answer or execution["verified_at"] is not None or not execution["failure_code"]:
            _inconsistent()
        failure = {"code": execution["failure_code"],
            "category": execution["failure_category"],
            "message": "Document question could not be completed"}
    elif states == ("completed", "passed", "succeeded"):
        observation = "verified"
        if (not read or not answer or execution["verified_at"] is None
                or execution["failure_code"] is not None
                or read["project_id"] != row["project_id"]
                or read["document_name"] != row["document_name"]
                or read["content_encoding"] != "utf-8"
                or not isinstance(read["bom_present"], bool)
                or not 0 <= read["byte_length"] <= 65536
                or not re.fullmatch(r"[0-9a-f]{64}", read["content_sha256"])
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", read["root_id"])):
            _inconsistent()
        outcome, quotes = answer["outcome"], answer["quotes"]
        if (outcome not in OUTCOMES or not isinstance(quotes, list) or len(quotes) > 3
                or (outcome in {"supported", "partial"} and not quotes)
                or (outcome == "conflicting" and len(quotes) < 2)
                or (outcome in {"insufficient", "out_of_scope"} and quotes)):
            _inconsistent()
        seen = set()
        for item in quotes:
            if (not isinstance(item, dict) or set(item) != {"quote", "start", "end"}
                    or not isinstance(item["quote"], str) or not item["quote"].strip()
                    or len(item["quote"]) > 240 or item["quote"] in seen
                    or type(item["start"]) is not int or type(item["end"]) is not int
                    or item["start"] < 0 or item["end"] != item["start"] + len(item["quote"])
                    or item["end"] > read["byte_length"]):
                _inconsistent()
            seen.add(item["quote"])
        result = {"capability": CAPABILITY, **{k: _definition(row)[k]
            for k in ("project_id", "document_name")}, "outcome": outcome,
            "grounded": bool(quotes), "answer": assemble_answer(outcome, quotes),
            "evidence": quotes, "temporal_scope": "execution_observation",
            "document": {"root_id": read["root_id"], "document_name": read["document_name"],
                "observed_at": read["observed_at"].isoformat(),
                "byte_length": read["byte_length"], "content_sha256": read["content_sha256"],
                "evidence_execution_id": str(execution["id"])}}
    else:
        _inconsistent()
    public = {"id": str(execution["id"]), "request_id": str(execution["request_id"]),
        "capability": CAPABILITY, "status": execution["status"],
        "created_at": execution["created_at"].isoformat(),
        "updated_at": execution["updated_at"].isoformat(),
        "verified_at": execution["verified_at"].isoformat() if execution["verified_at"] else None,
        "failure": failure, "observation": observation}
    return public, result


def _disclose(connection_factory, token, actor, rows):
    """A fresh transaction; legal claim/terminal advancement is not invisibility."""
    with connection_factory() as db:
        _begin(db, inspection=True)
        if _actor_for_token(db, token) != actor:
            raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
        for old in rows:
            current = _owned(db, actor, old["id"])
            if (_definition(current) != _definition(old)
                    or current["registration_request_id"] != old["registration_request_id"]
                    or (old["execution_id"] is not None
                        and current["execution_id"] != old["execution_id"])):
                _inconsistent()


def inspect_document_task(task_id, token, query="", forbidden_headers=False,
                          connection_factory=connect):
    request, db = uuid4(), None
    try:
        db = connection_factory()
        _begin(db, inspection=True)
        actor = _actor(db, token)
        _options(query, forbidden_headers)
        task = _uuid(task_id)
        if task is None:
            raise ToolFailure("INVALID_TASK_ID", "Invalid Input", 400)
        row = _owned(db, actor, task)
        execution, result = _materialize(db, row)
        db.rollback()
        _close(db)
        db = None
        _disclose(connection_factory, token, actor, [row])
        return 200, {"status": "succeeded", "request_id": str(request),
            "outcome": "task_inspected", "task_id": str(task),
            "execution_id": execution["id"] if execution else None,
            "task": _public(row), "execution": execution, "result": result}
    except ToolFailure as error:
        return _error(request, error)
    except (psycopg.Error, OSError, ValueError, TypeError, KeyError):
        return _error(request, ToolFailure("DATABASE_UNAVAILABLE"))
    finally:
        _close(db)


def _unique(pairs):
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise ValueError("Duplicate field")
        obj[key] = value
    return obj


def _list_options(query):
    if len(query) > 1024:
        raise ValueError("Invalid query")
    fields = parse_qsl(query, keep_blank_values=True, strict_parsing=True, max_num_fields=2)
    obj = _unique(fields)
    if set(obj) - {"limit", "cursor"}:
        raise ValueError("Invalid query")
    limit = obj.get("limit", "20")
    if not re.fullmatch(r"[0-9]{1,3}", limit) or not 1 <= int(limit) <= 100:
        raise ValueError("Invalid limit")
    cursor = None
    if "cursor" in obj:
        value = obj["cursor"]
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,256}", value):
            raise ValueError("Invalid cursor")
        raw = base64.b64decode(value + "=" * (-len(value) % 4), altchars=b"-_", validate=True)
        decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique)
        if not isinstance(decoded, dict) or set(decoded) != {"created_at", "id"}:
            raise ValueError("Invalid cursor")
        time = datetime.fromisoformat(decoded["created_at"])
        task = _uuid(decoded["id"])
        if time.tzinfo is None or time.utcoffset() is None or task is None:
            raise ValueError("Invalid cursor")
        cursor = time, task
    return int(limit), cursor


def list_document_tasks(token, query="", forbidden_headers=False, connection_factory=connect):
    request = uuid4()
    try:
        with connection_factory() as db:
            _begin(db, inspection=True)
            actor = _actor(db, token)
            if forbidden_headers:
                raise ToolFailure("INVALID_REQUEST", "Invalid Input", 400)
            try:
                limit, cursor = _list_options(query)
            except (ValueError, TypeError, UnicodeError, binascii.Error):
                raise ToolFailure("INVALID_REQUEST", "Invalid Input", 400) from None
            sql = _SELECT + """ WHERE t.actor_user_id=%s AND EXISTS
                (SELECT 1 FROM noah.project_memberships m
                 WHERE m.user_id=%s AND m.project_id=d.project_id)"""
            params = [actor, actor]
            if cursor is not None:
                sql += " AND (t.created_at,t.id)<(%s,%s)"
                params.extend(cursor)
            sql += " ORDER BY t.created_at DESC,t.id DESC LIMIT %s"
            rows = db.execute(sql, [*params, limit + 1]).fetchall()
            shown = rows[:limit]
        _disclose(connection_factory, token, actor, shown)
        next_cursor = None
        if len(rows) > limit:
            raw = json.dumps({"created_at": shown[-1]["created_at"].isoformat(),
                "id": str(shown[-1]["id"])}, separators=(",", ":")).encode()
            next_cursor = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        items = [{k: _public(row)[k] for k in
            ("id", "kind", "status", "verification_status", "created_at", "updated_at")}
            | {"project_id": str(row["project_id"]), "document_name": row["document_name"]}
            for row in shown]
        return 200, {"status": "succeeded", "request_id": str(request),
            "outcome": "tasks_listed", "items": items, "next_cursor": next_cursor}
    except ToolFailure as error:
        return _error(request, error)
    except (psycopg.Error, OSError, ValueError, TypeError):
        return _error(request, ToolFailure("DATABASE_UNAVAILABLE"))


def register_document_task(payload, token, query="", forbidden_headers=False,
                           connection_factory=connect, settings_provider=local_settings):
    request, task, db = uuid4(), None, None
    commit_attempted = False
    try:
        db = connection_factory()
        _begin(db)
        actor = _actor(db, token)
        _options(query, forbidden_headers)
        if not isinstance(payload, dict) or set(payload) != {"project_id", "document_name", "question"}:
            raise ToolFailure("INVALID_REQUEST", "Invalid Input", 400)
        project = _uuid(payload["project_id"])
        if project is None:
            raise ToolFailure("INVALID_PROJECT", "Invalid Input", 400)
        if not _project_readable(db, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        name = validate_document_name(payload["document_name"])
        try:
            name.encode("utf-8")
        except UnicodeError:
            raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400) from None
        question = validate_question(payload["question"])
        credentials = token, settings_provider()["POSTGRES_PASSWORD"]
        reject_known_credentials(question, credentials)
        reject_known_credentials(name, credentials)
        if _actor_for_token(db, token) != actor:
            raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
        if not _project_readable(db, actor, project):
            raise ToolFailure("PROJECT_NOT_FOUND", "Permission Denied", 404)
        task = uuid4()
        db.execute("""INSERT INTO noah.tasks(id,actor_user_id,goal,status,verification_status)
            VALUES(%s,%s,%s,'ready','pending')""", (task, actor, GOAL))
        db.execute("""INSERT INTO noah.document_question_tasks
            (task_id,registration_request_id,project_id,document_name,question)
            VALUES(%s,%s,%s,%s,%s)""", (task, request, project, name, question))
        commit_attempted = True
        db.commit()
    except ToolFailure as error:
        if db is not None and not _rollback(db):
            return _unknown(request, task)
        return _error(request, error)
    except (psycopg.Error, OSError, ValueError, UnicodeError, KeyError) as error:
        if commit_attempted or (db is not None and not _rollback(db)):
            return _unknown(request, task)
        return _error(request, _storage_error(error))
    finally:
        _close(db)
    status, body = inspect_document_task(str(task), token, connection_factory=connection_factory)
    if status != 200:
        if status in (401, 404, 502):
            return status, {**body, "request_id": str(request)}
        return _unknown(request, task)
    if (body["task"]["registration_request_id"] != str(request)
            or body["task"]["definition"] != {"project_id": str(project),
                "document_name": name, "question": question}):
        return _error(request, ToolFailure("TASK_RECORD_INCONSISTENT", "Verification Failure", 502))
    return 201, {**body, "request_id": str(request), "outcome": "task_registered",
        "registration": {"status": "confirmed", "initial_task_status": "ready",
            "initial_verification_status": "pending", "execution_created": False}}


def _claim(task, token, request, connection_factory):
    db, execution, commit_attempted = None, None, False
    try:
        db = connection_factory()
        _begin(db)
        actor = _actor(db, token)
        locked = db.execute("SELECT id FROM noah.tasks WHERE id=%s AND actor_user_id=%s FOR UPDATE",
            (task, actor)).fetchone()
        if locked is None:
            raise ToolFailure("TASK_NOT_FOUND", "Permission Denied", 404)
        row = _owned(db, actor, task)
        _materialize(db, row)
        if row["status"] != "ready":
            raise ToolFailure("TASK_EXECUTION_UNCONFIRMED" if row["status"] == "running"
                else "TASK_ALREADY_EXECUTED", "Invalid Input", 409)
        if _actor_for_token(db, token) != actor:
            raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
        if not _project_readable(db, actor, row["project_id"]):
            raise ToolFailure("TASK_NOT_FOUND", "Permission Denied", 404)
        execution = uuid4()
        db.execute("""INSERT INTO noah.execution_records
            (id,request_id,task_id,actor_user_id,capability,status)
            VALUES(%s,%s,%s,%s,%s,'running')""", (execution, request, task, actor, CAPABILITY))
        bind = db.execute("""UPDATE noah.document_question_tasks SET execution_id=%s
            WHERE task_id=%s AND execution_id IS NULL""", (execution, task))
        advance = db.execute("""UPDATE noah.tasks SET status='running',updated_at=now()
            WHERE id=%s AND actor_user_id=%s AND status='ready' AND verification_status='pending'""",
            (task, actor))
        if bind.rowcount != 1 or advance.rowcount != 1:
            _inconsistent()
        row["execution_id"] = execution
        commit_attempted = True
        db.commit()
        return row, actor, execution, None
    except ToolFailure as error:
        response = (_error(request, error, task if error.http_status == 409 else None,
            row["execution_id"] if error.http_status == 409 else None)
            if db is None or _rollback(db) else _unknown(request, task, execution))
        return None, None, execution, response
    except (psycopg.Error, OSError, ValueError) as error:
        if commit_attempted or (db is not None and not _rollback(db)):
            response = _unknown(request, task, execution)
        else:
            response = _error(request, _storage_error(error))
        return None, None, execution, response
    finally:
        _close(db)


def _permission(connection_factory, token, actor, row):
    _disclose(connection_factory, token, actor, [row])


def _read(row, root_provider, read_runner, credentials):
    root_id, root = root_provider(row["project_id"])
    if (not isinstance(root_id, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", root_id)
            or not isinstance(root, Path) or not root.is_absolute()):
        raise ToolFailure("PROJECT_ROOT_CONFIG_INVALID")
    observation = validate_read_observation(root, row["document_name"], read_runner(root, row["document_name"]))
    reject_known_credentials(observation["content"], credentials)
    return root_id, root, observation


def _finish(row, actor, token, request, connection_factory, observation=None,
            root_id=None, observed_at=None, outcome=None, quotes=None, failure=None):
    """Never use the legacy unconditional failure updater for this claimed Task."""
    db, commit_attempted = None, False
    try:
        db = connection_factory()
        _begin(db)
        locked = db.execute("SELECT id FROM noah.tasks WHERE id=%s AND actor_user_id=%s FOR UPDATE",
            (row["id"], actor)).fetchone()
        if locked is None:
            _inconsistent()
        current = db.execute(_SELECT + " WHERE t.id=%s", (row["id"],)).fetchone()
        if (current is None or _definition(current) != _definition(row)
                or current["execution_id"] != row["execution_id"]
                or current["registration_request_id"] != row["registration_request_id"]):
            _inconsistent()
        execution, _ = _materialize(db, current)
        if (current["status"] != "running" or execution["request_id"] != str(request)):
            _inconsistent()
        if failure is None:
            if _actor_for_token(db, token) != actor:
                raise ToolFailure("UNAUTHENTICATED", "Permission Denied", 401)
            if not _project_readable(db, actor, row["project_id"]):
                raise ToolFailure("TASK_NOT_FOUND", "Permission Denied", 404)
            db.execute("""INSERT INTO noah.document_read_evidence
                (execution_id,project_id,root_id,document_name,observed_at,byte_length,
                 content_sha256,content_encoding,bom_present)
                VALUES(%s,%s,%s,%s,%s,%s,%s,'utf-8',%s)""",
                (row["execution_id"], row["project_id"], root_id, row["document_name"], observed_at,
                    observation["byte_length"], observation["content_sha256"], observation["bom_present"]))
            db.execute("""INSERT INTO noah.document_answer_evidence(execution_id,outcome,quotes)
                VALUES(%s,%s,%s::jsonb)""", (row["execution_id"], outcome, json.dumps(quotes, ensure_ascii=False)))
        task_status, verification, execution_status = (("completed", "passed", "succeeded")
            if failure is None else ("failed", "failed", "failed"))
        task_update = db.execute("""UPDATE noah.tasks SET status=%s,verification_status=%s,updated_at=now()
            WHERE id=%s AND actor_user_id=%s AND status='running' AND verification_status='pending'""",
            (task_status, verification, row["id"], actor))
        execution_update = db.execute("""UPDATE noah.execution_records SET status=%s,
            failure_category=%s,failure_code=%s,verified_at=%s,updated_at=now()
            WHERE id=%s AND task_id=%s AND actor_user_id=%s AND capability=%s
                AND request_id=%s AND status='running'""",
            (execution_status, failure.category if failure else None, failure.code if failure else None,
                datetime.now(timezone.utc) if failure is None else None, row["execution_id"],
                row["id"], actor, CAPABILITY, request))
        if task_update.rowcount != 1 or execution_update.rowcount != 1:
            _inconsistent()
        commit_attempted = True
        db.commit()
        return None
    except ToolFailure as error:
        if db is not None and _rollback(db):
            return error
        return ToolFailure("TASK_OUTCOME_UNKNOWN")
    except (psycopg.Error, OSError, ValueError):
        if commit_attempted or (db is not None and not _rollback(db)):
            return ToolFailure("TASK_OUTCOME_UNKNOWN")
        return ToolFailure("EVIDENCE_WRITE_FAILED")
    finally:
        _close(db)


def run_document_task(task_id, payload, token, query="", forbidden_headers=False,
                      connection_factory=connect, root_provider=operator_root,
                      read_runner=execute_document_read, model=None, settings_provider=local_settings):
    request, task = uuid4(), None
    try:
        with connection_factory() as db:
            _actor(db, token)
        _options(query, forbidden_headers)
        task = _uuid(task_id)
        if task is None:
            raise ToolFailure("INVALID_TASK_ID", "Invalid Input", 400)
        if not isinstance(payload, dict) or payload != {}:
            raise ToolFailure("INVALID_REQUEST", "Invalid Input", 400)
    except ToolFailure as error:
        return _error(request, error)
    except (psycopg.Error, OSError, ValueError):
        return _error(request, ToolFailure("DATABASE_UNAVAILABLE"))
    row, actor, execution, refusal = _claim(task, token, request, connection_factory)
    if refusal is not None:
        return refusal
    try:
        _permission(connection_factory, token, actor, row)
        credentials = token, settings_provider()["POSTGRES_PASSWORD"]
        reject_known_credentials(row["question"], credentials)
        reject_known_credentials(row["document_name"], credentials)
        root_id, root, observation = _read(row, root_provider, read_runner, credentials)
        observed_at = datetime.now(timezone.utc)
        messages = model_messages(row["question"], row["document_name"], observation["content"])
        _permission(connection_factory, token, actor, row)
        model = model if model is not None else OllamaClient()
        proposed = model.complete(messages, MODEL_SCHEMA, MODEL_OUTPUT_TOKENS)
        outcome, quotes = verify_model_evidence(proposed, observation["content"])
        _permission(connection_factory, token, actor, row)
        try:
            next_root_id, next_root, second = _read(row, root_provider, read_runner, credentials)
        except ToolOutcomeUnknown:
            raise
        except ToolFailure:
            raise ToolFailure("DOCUMENT_CHANGED", "Verification Failure", 409) from None
        if (root_id != next_root_id or root != next_root
                or any(observation[k] != second[k] for k in
                    ("byte_length", "content_sha256", "bom_present"))):
            raise ToolFailure("DOCUMENT_CHANGED", "Verification Failure", 409)
    except ToolOutcomeUnknown as error:
        return _error(request, error, task, execution)
    except (OllamaTimeout, OllamaUnavailable, OllamaUnsafeBinding, OllamaInvalidResponse) as error:
        failure = _model_error(error)
    except ToolFailure as error:
        failure = error
    except (psycopg.Error, OSError, KeyError):
        return _unknown(request, task, execution)
    except (TypeError, ValueError):
        failure = ToolFailure("MODEL_OUTPUT_INVALID", "Verification Failure", 502)
    else:
        failure = _finish(row, actor, token, request, connection_factory, observation,
            root_id, observed_at, outcome, quotes)
        if failure is None:
            status, body = inspect_document_task(str(task), token, connection_factory=connection_factory)
            if status != 200:
                return (status, {**body, "request_id": str(request)}) if status in (401, 404, 502) else _unknown(request, task, execution)
            return 200, {**body, "request_id": str(request), "outcome": "task_executed"}
    if failure.code.endswith("_OUTCOME_UNKNOWN"):
        return _error(request, failure, task, execution)
    recorded = _finish(row, actor, token, request, connection_factory, failure=failure)
    if recorded is not None:
        return _unknown(request, task, execution)
    return _error(request, failure, task, execution)
