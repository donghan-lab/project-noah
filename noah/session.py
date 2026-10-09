"""M16 user-owned Session lifecycle and bounded routing references."""

import base64
import binascii
import json
import re
from datetime import datetime
from urllib.parse import parse_qsl
from uuid import UUID, uuid4

import psycopg

from .db import connect
from .service import _actor_for_token, _failure


_CURSOR_TEXT = re.compile(r"[A-Za-z0-9_-]{1,512}\Z")
_LIMIT_TEXT = re.compile(r"[0-9]{1,3}\Z")


def canonical_session_id(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = UUID(value)
    except ValueError:
        return None
    return parsed if str(parsed) == value else None


def _public(row):
    return {"session_id": str(row["id"]),
            "status": "closed" if row["closed_at"] is not None else "active",
            "created_at": row["created_at"].isoformat(),
            "closed_at": row["closed_at"].isoformat() if row["closed_at"] else None}


def _success(request_id, outcome, row, interactions=None, next_cursor=None):
    body = {"status": "succeeded", "request_id": str(request_id),
            "task_id": None, "execution_id": None, "session": _public(row)}
    if outcome is not None:
        body["outcome"] = outcome
    if interactions is not None:
        body["interactions"] = interactions
        body["next_cursor"] = next_cursor
    return body


def _unknown(request_id, provisional_session_id=None):
    status, body = _failure(request_id, "SESSION_OUTCOME_UNKNOWN",
                            "Environment Failure", 503,
                            "Session outcome cannot be confirmed")
    body["outcome"] = "unknown"
    if provisional_session_id is not None:
        body["session_id"] = str(provisional_session_id)
    return status, body


def _storage_failure(request_id):
    return _failure(request_id, "SESSION_STORAGE_UNAVAILABLE", "Environment Failure",
                    503, "Session storage is unavailable")


def _rollback_confirmed(db):
    try:
        db.rollback()
        return True
    except (psycopg.Error, OSError):
        return False


def _open_actor(token, connection_factory):
    if not isinstance(token, str) or not token:
        return None, None
    db = connection_factory()
    try:
        return db, _actor_for_token(db, token)
    except (psycopg.Error, OSError, ValueError):
        _close(db)
        raise


def _close(db):
    if db is not None:
        try:
            db.close()
        except (psycopg.Error, OSError):
            pass


def create_session(payload, token, query="", connection_factory=connect):
    """Create one active Session; its ID exists before an uncertain commit."""
    request_id, session_id = uuid4(), uuid4()
    db = None
    try:
        db, actor = _open_actor(token, connection_factory)
        if actor is None:
            return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                            "Authentication required")
        if payload != {} or query:
            return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                            "An empty JSON object and no query parameters are required")
        try:
            row = db.execute("""INSERT INTO noah.sessions(id,owner_user_id)
                VALUES(%s,%s) RETURNING id,created_at,closed_at""",
                (session_id, actor)).fetchone()
            if row is None:
                raise ValueError("Session insert was not observed")
        except (psycopg.Error, OSError, ValueError):
            return (_storage_failure(request_id) if _rollback_confirmed(db)
                    else _unknown(request_id, session_id))
        try:
            db.commit()
        except (psycopg.Error, OSError):
            return _unknown(request_id, session_id)
        return 201, _success(request_id, "created", row)
    except (psycopg.Error, OSError, ValueError):
        return _storage_failure(request_id)
    finally:
        _close(db)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate cursor key")
        result[key] = value
    return result


def _encode_cursor(session_id, row):
    value = json.dumps({"s": str(session_id), "t": row["created_at"].isoformat(),
                        "r": str(row["router_id"])}, separators=(",", ":"))
    return base64.urlsafe_b64encode(value.encode("utf-8")).decode("ascii").rstrip("=")


def _decode_cursor(value, session_id):
    if not isinstance(value, str) or not _CURSOR_TEXT.fullmatch(value):
        raise ValueError("Invalid cursor")
    try:
        raw = base64.b64decode(value + "=" * (-len(value) % 4),
                               altchars=b"-_", validate=True)
        cursor = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object)
        if not isinstance(cursor, dict) or set(cursor) != {"s", "t", "r"}:
            raise ValueError("Invalid cursor shape")
        if cursor["s"] != str(session_id) or canonical_session_id(cursor["r"]) is None:
            raise ValueError("Cursor belongs to another Session")
        timestamp = datetime.fromisoformat(cursor["t"])
        if timestamp.tzinfo is None:
            raise ValueError("Cursor timestamp needs a timezone")
        return timestamp, UUID(cursor["r"])
    except (binascii.Error, UnicodeError, TypeError, ValueError, KeyError) as error:
        raise ValueError("Invalid cursor") from error


def _inspection_options(query, session_id):
    try:
        items = parse_qsl(query, keep_blank_values=True, max_num_fields=2)
    except ValueError as error:
        raise ValueError("Invalid query") from error
    options = {}
    for key, value in items:
        if key not in {"limit", "cursor"} or key in options:
            raise ValueError("Invalid query")
        options[key] = value
    limit_text = options.get("limit", "20")
    if not _LIMIT_TEXT.fullmatch(limit_text) or not 1 <= int(limit_text) <= 100:
        raise ValueError("Invalid limit")
    cursor = (_decode_cursor(options["cursor"], session_id)
              if "cursor" in options else None)
    return int(limit_text), cursor


def inspect_session(session_id, token, query="", connection_factory=connect):
    """Read only an owner's Session and bounded, source-neutral references."""
    request_id = uuid4()
    db = None
    try:
        db, actor = _open_actor(token, connection_factory)
        if actor is None:
            return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                            "Authentication required")
        parsed_id = canonical_session_id(session_id)
        if parsed_id is None:
            return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                            "Valid Session ID required")
        try:
            limit, cursor = _inspection_options(query, parsed_id)
        except ValueError:
            return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                            "Invalid Session inspection parameters")
        row = db.execute("""SELECT id,created_at,closed_at FROM noah.sessions
            WHERE id=%s AND owner_user_id=%s""", (parsed_id, actor)).fetchone()
        if row is None:
            return _failure(request_id, "SESSION_NOT_FOUND", "Permission Denied", 404,
                            "Session not found")
        if cursor is None:
            references = db.execute("""SELECT router_id,created_at
                FROM noah.routing_audit WHERE session_id=%s AND actor_user_id=%s
                ORDER BY created_at DESC,router_id DESC LIMIT %s""",
                (parsed_id, actor, limit + 1)).fetchall()
        else:
            references = db.execute("""SELECT router_id,created_at
                FROM noah.routing_audit WHERE session_id=%s AND actor_user_id=%s
                    AND (created_at,router_id)<(%s,%s)
                ORDER BY created_at DESC,router_id DESC LIMIT %s""",
                (parsed_id, actor, cursor[0], cursor[1], limit + 1)).fetchall()
        more = len(references) > limit
        shown = references[:limit]
        interactions = [{"router_id": str(ref["router_id"]),
                         "associated_at": ref["created_at"].isoformat()}
                        for ref in shown]
        next_cursor = _encode_cursor(parsed_id, shown[-1]) if more else None
        return 200, _success(request_id, None, row, interactions, next_cursor)
    except (psycopg.Error, OSError, ValueError):
        return _storage_failure(request_id)
    finally:
        _close(db)


def close_session(session_id, payload, token, query="", connection_factory=connect):
    """Lock and close an owned Session without changing linked execution truth."""
    request_id = uuid4()
    db = None
    try:
        db, actor = _open_actor(token, connection_factory)
        if actor is None:
            return _failure(request_id, "UNAUTHENTICATED", "Permission Denied", 401,
                            "Authentication required")
        parsed_id = canonical_session_id(session_id)
        if parsed_id is None or payload != {} or query:
            return _failure(request_id, "INVALID_REQUEST", "Invalid Input", 400,
                            "Valid Session ID and empty JSON object required")
        try:
            row = db.execute("""SELECT id,created_at,closed_at FROM noah.sessions
                WHERE id=%s AND owner_user_id=%s FOR UPDATE""",
                (parsed_id, actor)).fetchone()
            if row is None:
                return _failure(request_id, "SESSION_NOT_FOUND", "Permission Denied", 404,
                                "Session not found")
            if row["closed_at"] is not None:
                return 200, _success(request_id, "already_closed", row)
            updated = db.execute("""UPDATE noah.sessions
                SET closed_at=GREATEST(clock_timestamp(),created_at)
                WHERE id=%s AND closed_at IS NULL
                RETURNING id,created_at,closed_at""", (parsed_id,)).fetchone()
            if updated is None or updated["closed_at"] is None:
                raise ValueError("Session close was not verified")
        except (psycopg.Error, OSError, ValueError):
            return (_storage_failure(request_id) if _rollback_confirmed(db)
                    else _unknown(request_id))
        try:
            db.commit()
        except (psycopg.Error, OSError):
            return _unknown(request_id)
        return 200, _success(request_id, "closed", updated)
    except (psycopg.Error, OSError, ValueError):
        return _storage_failure(request_id)
    finally:
        _close(db)
