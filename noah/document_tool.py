"""Bounded, non-recursive document-name observation with no content reads."""

import json
import multiprocessing
import os
from pathlib import Path
import re
import stat

from .db import ROOT


CONFIG_PATH = ROOT / "config" / "project_documents.local.json"
CAPABILITY = "project.documents.list"
MAX_FILES = 50
TOOL_TIMEOUT_SECONDS = 5


class ToolFailure(Exception):
    def __init__(self, code, category="Environment Failure", http_status=503):
        self.code, self.category, self.http_status = code, category, http_status
        super().__init__(code)


class ToolOutcomeUnknown(ToolFailure):
    def __init__(self):
        super().__init__("TOOL_OUTCOME_UNKNOWN", "Timeout", 504)


def operator_root(project_id, config_path=CONFIG_PATH):
    """Only an operator-owned local file can bind a DB project to an OS root."""
    try:
        config = json.loads(Path(config_path).read_text(encoding="utf-8-sig"))
        projects = config["projects"]
        if not isinstance(projects, dict):
            raise ValueError
        entry = projects.get(str(project_id))
        if entry is None:
            raise ToolFailure("PROJECT_ROOT_UNREGISTERED")
        if (not isinstance(entry, dict) or set(entry) != {"root_id", "document_root"}
                or not isinstance(entry["root_id"], str)
                or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}", entry["root_id"])
                or not isinstance(entry["document_root"], str)
                or not Path(entry["document_root"]).is_absolute()
                or ".." in Path(entry["document_root"]).parts):
            raise ValueError
        return entry["root_id"], Path(entry["document_root"])
    except ToolFailure:
        raise
    except FileNotFoundError:
        raise ToolFailure("PROJECT_ROOT_UNREGISTERED") from None
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        raise ToolFailure("PROJECT_ROOT_CONFIG_INVALID") from None


def _reparse_or_link(path, metadata):
    return stat.S_ISLNK(metadata.st_mode) or bool(
        getattr(metadata, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def list_document_names(root, limit=MAX_FILES):
    """Observe direct regular Markdown children, never following symlinks."""
    try:
        root = Path(root)
        if not root.is_absolute() or ".." in root.parts:
            raise ToolFailure("PROJECT_ROOT_INVALID")
        for component in reversed(root.parents):
            if component == Path(component.anchor):
                continue
            ancestor = component.lstat()
            if _reparse_or_link(component, ancestor):
                raise ToolFailure("PROJECT_ROOT_INVALID")
        metadata = root.lstat()
        if _reparse_or_link(root, metadata) or not stat.S_ISDIR(metadata.st_mode):
            raise ToolFailure("PROJECT_ROOT_INVALID")
        names = []
        with os.scandir(root) as entries:
            for entry in entries:
                if entry.name.startswith(".") or not entry.name.lower().endswith(".md"):
                    continue
                item = entry.stat(follow_symlinks=False)
                attributes = getattr(item, "st_file_attributes", 0)
                if (_reparse_or_link(entry.path, item)
                        or attributes & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0)
                        or not stat.S_ISREG(item.st_mode)):
                    continue
                names.append(entry.name)
        names.sort(key=lambda name: (name.casefold(), name))
        return {"filenames": names[:limit], "truncated": len(names) > limit}
    except ToolFailure:
        raise
    except FileNotFoundError:
        raise ToolFailure("PROJECT_ROOT_NOT_FOUND") from None
    except PermissionError:
        raise ToolFailure("PROJECT_ROOT_ACCESS_DENIED") from None
    except OSError:
        raise ToolFailure("TOOL_EXECUTION_FAILED") from None


def _worker(root, limit, sender):
    try:
        sender.send(("ok", list_document_names(root, limit)))
    except ToolFailure as error:
        sender.send(("error", error.code))
    except BaseException:
        sender.send(("error", "TOOL_EXECUTION_FAILED"))
    finally:
        sender.close()


def execute_document_tool(root, limit=MAX_FILES, timeout=TOOL_TIMEOUT_SECONDS):
    """Run the fixed read-only adapter in a stoppable local worker process."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    worker = context.Process(target=_worker, args=(str(root), limit, sender), daemon=True)
    try:
        worker.start()
        sender.close()
        worker.join(timeout)
        if worker.is_alive():
            worker.terminate()
            worker.join(1)
            if worker.is_alive():
                worker.kill()
                worker.join(1)
            if worker.is_alive():
                raise ToolOutcomeUnknown()
            raise ToolFailure("TOOL_TIMEOUT", "Timeout", 504)
        if not receiver.poll(0.2):
            raise ToolFailure("TOOL_EXECUTION_FAILED")
        kind, result = receiver.recv()
        if kind == "error":
            raise ToolFailure(result)
        if kind != "ok":
            raise ToolFailure("TOOL_EXECUTION_FAILED")
        return result
    except (OSError, EOFError):
        raise ToolFailure("TOOL_EXECUTION_FAILED") from None
    finally:
        receiver.close()
        sender.close()


def validate_observation(root, result, limit=MAX_FILES):
    """Reject fabricated names and malformed output against a fresh scan."""
    if (not isinstance(result, dict) or set(result) != {"filenames", "truncated"}
            or not isinstance(result["filenames"], list)
            or type(result["truncated"]) is not bool
            or len(result["filenames"]) > limit
            or any(not isinstance(name, str) or not name or name.startswith(".")
                   or "/" in name or "\\" in name or ":" in name
                   or not name.lower().endswith(".md") for name in result["filenames"])):
        raise ToolFailure("TOOL_EVIDENCE_INVALID", "Verification Failure", 502)
    expected = list_document_names(root, limit)
    if result != expected:
        raise ToolFailure("TOOL_EVIDENCE_INVALID", "Verification Failure", 502)
    return result
