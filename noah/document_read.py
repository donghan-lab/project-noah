"""Bounded single-file read. The model never receives document bytes."""

import ctypes
import hashlib
import multiprocessing
import os
from pathlib import Path
import re
import stat

from .document_tool import ToolFailure, ToolOutcomeUnknown, _reparse_or_link


CAPABILITY = "project.documents.read"
MAX_BYTES = 65_536
TOOL_TIMEOUT_SECONDS = 5
_RESERVED = re.compile(r"(?i)^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\.|$)")


def validate_document_name(name):
    if not isinstance(name, str) or not name or len(name) > 255:
        raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400)
    if (name in {".", ".."} or name.startswith(".") or name[-1] in " ."
            or any(character in name for character in '/\\:<>"|?*')
            or any(ord(character) < 32 or ord(character) == 127 for character in name)
            or _RESERVED.match(name)):
        raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400)
    if not name.endswith(".md"):
        raise ToolFailure("UNSUPPORTED_FILE_TYPE", "Invalid Input", 415)
    return name


def _target(root, name):
    root = Path(root)
    if not root.is_absolute() or ".." in root.parts:
        raise ToolFailure("PROJECT_ROOT_INVALID")
    try:
        for component in reversed(root.parents):
            if component != Path(component.anchor) and _reparse_or_link(component, component.lstat()):
                raise ToolFailure("PROJECT_ROOT_INVALID")
        info = root.lstat()
        if _reparse_or_link(root, info) or not stat.S_ISDIR(info.st_mode):
            raise ToolFailure("PROJECT_ROOT_INVALID")
        with os.scandir(root) as entries:
            item = next((entry for entry in entries if entry.name == name), None)
            if item is None:
                raise ToolFailure("DOCUMENT_NOT_FOUND", "Invalid Input", 404)
            info = item.stat(follow_symlinks=False)
        if _reparse_or_link(root / name, info):
            raise ToolFailure("DOCUMENT_LINK_REJECTED", "Policy Violation", 422)
        if getattr(info, "st_file_attributes", 0) & getattr(stat, "FILE_ATTRIBUTE_HIDDEN", 0):
            raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400)
        if not stat.S_ISREG(info.st_mode):
            raise ToolFailure("UNSUPPORTED_FILE_TYPE", "Invalid Input", 415)
        return root / name
    except ToolFailure:
        raise
    except FileNotFoundError:
        raise ToolFailure("PROJECT_ROOT_NOT_FOUND") from None
    except PermissionError:
        raise ToolFailure("PROJECT_ROOT_ACCESS_DENIED") from None
    except OSError:
        raise ToolFailure("TOOL_EXECUTION_FAILED") from None


def _read_windows(path):
    """Open the named entry itself, then reject reparse attributes on its handle."""
    from ctypes import wintypes

    class FileTime(ctypes.Structure):
        _fields_ = [("low", wintypes.DWORD), ("high", wintypes.DWORD)]

    class FileInfo(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("created", FileTime),
                    ("accessed", FileTime), ("modified", FileTime),
                    ("volume", wintypes.DWORD), ("size_high", wintypes.DWORD),
                    ("size_low", wintypes.DWORD), ("links", wintypes.DWORD),
                    ("index_high", wintypes.DWORD), ("index_low", wintypes.DWORD)]

    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                       ctypes.c_void_p, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    info_for = kernel.GetFileInformationByHandle
    info_for.argtypes = [ctypes.c_void_p, ctypes.POINTER(FileInfo)]
    info_for.restype = wintypes.BOOL
    read = kernel.ReadFile
    read.argtypes = [ctypes.c_void_p, ctypes.c_void_p, wintypes.DWORD,
                     ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    read.restype = wintypes.BOOL
    close = kernel.CloseHandle
    close.argtypes = [ctypes.c_void_p]
    close.restype = wintypes.BOOL

    # FILE_READ_DATA | FILE_READ_ATTRIBUTES, FILE_SHARE_READ, OPEN_EXISTING,
    # FILE_FLAG_OPEN_REPARSE_POINT. No write or delete permission is requested.
    handle = create(str(path), 0x1 | 0x80, 0x1, None, 3, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        error = ctypes.get_last_error()
        if error in (2, 3):
            raise ToolFailure("DOCUMENT_NOT_FOUND", "Invalid Input", 404)
        if error in (5, 32):
            raise ToolFailure("DOCUMENT_ACCESS_DENIED", "Permission Denied", 403)
        raise ToolFailure("TOOL_EXECUTION_FAILED")
    try:
        before = FileInfo()
        if not info_for(handle, ctypes.byref(before)):
            raise ToolFailure("TOOL_EXECUTION_FAILED")
        if before.attributes & 0x400:
            raise ToolFailure("DOCUMENT_LINK_REJECTED", "Policy Violation", 422)
        if before.attributes & 0x10:
            raise ToolFailure("UNSUPPORTED_FILE_TYPE", "Invalid Input", 415)
        if before.attributes & 0x2:
            raise ToolFailure("INVALID_DOCUMENT_IDENTIFIER", "Invalid Input", 400)
        size = (before.size_high << 32) | before.size_low
        if size > MAX_BYTES:
            raise ToolFailure("DOCUMENT_TOO_LARGE", "Resource Exhaustion", 413)
        buffer = ctypes.create_string_buffer(MAX_BYTES + 1)
        total = 0
        while total <= MAX_BYTES:
            count = wintypes.DWORD()
            if not read(handle, ctypes.byref(buffer, total), MAX_BYTES + 1 - total,
                        ctypes.byref(count), None):
                raise ToolFailure("TOOL_EXECUTION_FAILED")
            if count.value == 0:
                break
            total += count.value
        if total > MAX_BYTES:
            raise ToolFailure("DOCUMENT_TOO_LARGE", "Resource Exhaustion", 413)
        after = FileInfo()
        if not info_for(handle, ctypes.byref(after)):
            raise ToolFailure("TOOL_EXECUTION_FAILED")
        if (total != size or size != ((after.size_high << 32) | after.size_low)
                or (before.modified.low, before.modified.high) !=
                   (after.modified.low, after.modified.high)
                or (before.volume, before.index_high, before.index_low) !=
                   (after.volume, after.index_high, after.index_low)
                or after.attributes & 0x400):
            raise ToolFailure("DOCUMENT_CHANGED", "Verification Failure", 502)
        return buffer.raw[:total]
    finally:
        close(handle)


def _read_posix(path):
    if not hasattr(os, "O_NOFOLLOW"):
        raise ToolFailure("TOOL_EXECUTION_FAILED")
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_NONBLOCK", 0))
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise ToolFailure("UNSUPPORTED_FILE_TYPE", "Invalid Input", 415)
            if before.st_size > MAX_BYTES:
                raise ToolFailure("DOCUMENT_TOO_LARGE", "Resource Exhaustion", 413)
            chunks = bytearray()
            while len(chunks) <= MAX_BYTES:
                part = os.read(descriptor, MAX_BYTES + 1 - len(chunks))
                if not part:
                    break
                chunks.extend(part)
            after = os.fstat(descriptor)
            if len(chunks) > MAX_BYTES:
                raise ToolFailure("DOCUMENT_TOO_LARGE", "Resource Exhaustion", 413)
            if (len(chunks) != before.st_size or before.st_size != after.st_size
                    or before.st_mtime_ns != after.st_mtime_ns
                    or before.st_ino != after.st_ino):
                raise ToolFailure("DOCUMENT_CHANGED", "Verification Failure", 502)
            return bytes(chunks)
        finally:
            os.close(descriptor)
    except FileNotFoundError:
        raise ToolFailure("DOCUMENT_NOT_FOUND", "Invalid Input", 404) from None
    except PermissionError:
        raise ToolFailure("DOCUMENT_ACCESS_DENIED", "Permission Denied", 403) from None
    except OSError:
        raise ToolFailure("TOOL_EXECUTION_FAILED") from None


def read_document_bytes(root, name):
    validate_document_name(name)
    path = _target(root, name)
    return _read_windows(path) if os.name == "nt" else _read_posix(path)


def _worker(root, name, sender):
    try:
        sender.send(("ok", read_document_bytes(root, name)))
    except ToolFailure as error:
        sender.send(("error", error.code, error.category, error.http_status))
    except BaseException:
        sender.send(("error", "TOOL_EXECUTION_FAILED", "Environment Failure", 503))
    finally:
        sender.close()


def execute_document_read(root, name, timeout=TOOL_TIMEOUT_SECONDS):
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    worker = context.Process(target=_worker, args=(str(root), name, sender), daemon=True)
    try:
        worker.start()
        sender.close()
        # Receive before join: a 65 KiB observation can fill a process pipe.
        if receiver.poll(timeout):
            result = receiver.recv()
            worker.join(1)
            if worker.is_alive():
                worker.terminate()
                worker.join(1)
                if worker.is_alive():
                    worker.kill()
                    worker.join(1)
                if worker.is_alive():
                    raise ToolOutcomeUnknown()
                raise ToolFailure("TOOL_EXECUTION_FAILED")
        else:
            worker.join(0)
            if not worker.is_alive():
                raise ToolFailure("TOOL_EXECUTION_FAILED")
            worker.terminate()
            worker.join(1)
            if worker.is_alive():
                worker.kill()
                worker.join(1)
            if worker.is_alive():
                raise ToolOutcomeUnknown()
            raise ToolFailure("TOOL_TIMEOUT", "Timeout", 504)
        if result[0] == "error":
            raise ToolFailure(*result[1:])
        if result[0] != "ok":
            raise ToolFailure("TOOL_EXECUTION_FAILED")
        return result[1]
    except (OSError, EOFError):
        if worker.is_alive():
            worker.terminate()
            worker.join(1)
            if worker.is_alive():
                raise ToolOutcomeUnknown() from None
        raise ToolFailure("TOOL_EXECUTION_FAILED") from None
    finally:
        receiver.close()
        sender.close()


def validate_read_observation(root, name, raw):
    if not isinstance(raw, bytes) or len(raw) > MAX_BYTES:
        raise ToolFailure("TOOL_EVIDENCE_INVALID", "Verification Failure", 502)
    if raw != read_document_bytes(root, name):
        raise ToolFailure("TOOL_EVIDENCE_INVALID", "Verification Failure", 502)
    bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        content = raw.decode("utf-8-sig" if bom else "utf-8", errors="strict")
    except UnicodeDecodeError:
        raise ToolFailure("INVALID_UTF8", "Invalid Input", 422) from None
    if any(ord(char) < 32 and char not in "\t\n\r" or ord(char) == 127 for char in content):
        raise ToolFailure("UNSUPPORTED_CONTENT", "Invalid Input", 415)
    return {"content": content, "byte_length": len(raw),
            "content_sha256": hashlib.sha256(raw).hexdigest(), "bom_present": bom}
