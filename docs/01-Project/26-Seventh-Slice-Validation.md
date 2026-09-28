# M7 restricted document read validation

> 2026-09-28. Synthetic users, project, membership, and temporary document
> roots only. No real personal memory or existing Docker volume was modified
> or removed. Automated tests and subsequent user manual verification are
> reported separately below.

## Contract and implementation

The new `project.documents.read` API accepts an exact `.md` basename, not an
OS path. Authentication and project read membership precede mapping access.
Membership is checked again before Task/Execution reservation, after that
reservation immediately before Tool dispatch, before the independent
verification read, and before evidence and terminal state commit.
Pre-reservation rejections create no Task/Execution. A revocation after
reservation but before Tool dispatch records a failed attempt without opening
the file. The Tool runs in a bounded,
stoppable process and returns at most 65,536 raw bytes. Successful content is
strict UTF-8 (an optional leading BOM is removed for returned text). SHA-256
and byte length describe the **original** bytes, including a BOM. The server
compares a second bounded read to the worker result before recording evidence.
Document text is data only and is never sent to Ollama.

Windows opens the final file entry with `CreateFileW` and
`FILE_FLAG_OPEN_REPARSE_POINT`, checks reparse/directory/hidden attributes on
the resulting handle, and reads from that handle. Ancestors and the registered
root are checked for reparse points before open. This satisfies the stated
remote-input boundary; it does not protect against an adversarial process
running as the same Windows user replacing ancestors between checks and open.
The no-follow choice follows Microsoft's documented
[CreateFileW symbolic-link behavior](https://learn.microsoft.com/en-us/windows/win32/api/fileapi/nf-fileapi-createfilew).

`database/004_document_read_evidence.sql` adds one append-only application
evidence row per execution. It records execution/project IDs, logical root
and filename, observation time, original byte count and SHA-256, UTF-8 and
BOM metadata. It does not store the body or absolute path. The evidence row,
Task `completed/passed`, and Execution `succeeded`/`verified_at` commit in one
transaction. A definite Tool failure records matching failed states. Unclear
worker termination or final DB commit returns `TOOL_OUTCOME_UNKNOWN` without
guessing a terminal state. M5 triage remains `memory.save`-only.

## Automated tests on Docker Compose PostgreSQL 17

| Run | Result | Scope |
| --- | --- | --- |
| M7 focused | 13 passed, 0 failed, 0 skipped | Authentication, permission revocation, direct-child/identifier rules, real Windows junction, simulated reparse, missing root/hidden/access failure, size edge, UTF-8/BOM/binary, forged bytes, Task/Execution/evidence, DB/Tool failures, HTTP |
| M1–M7 full suite with real local Ollama opt-ins | 63 passed, 0 failed, 0 skipped | M1–M6 regressions including synthetic M3/M6 Ollama calls, plus M7 |

The 65,536-byte file succeeded; 65,537 bytes failed. Invalid UTF-8 and NUL
content failed. A UTF-8 BOM was accepted: returned text omitted only the BOM,
while byte length and SHA-256 included it. A prompt-like synthetic sentence
was returned literally and caused no Tool selection or command. A forged
worker byte result was rejected against the actual file. Confirmed timeout
was a definite failure; an unconfirmed outcome stayed `running` in the
synthetic case until test cleanup. The service never returned file bytes on a
permission-revocation failure.

The Windows test account could create a real junction, which was rejected
both as a target entry and as the configured root. It could not create a real
file symlink; the symlink/reparse classification branch was tested with
synthetic reparse metadata, and the Win32 no-follow open path is explicitly
implemented. This is a test-environment limitation, not a claim of a real
symlink integration test.

## User manual verification (separate from automated tests)

The user exercised the actual NOAH server and API with one temporary synthetic
project and a public `.md` document. The successful response contained the
exact file content with UTF-8 preserved; its original byte length and SHA-256
matched the source bytes. The response exposed no absolute path. The user
verified that exactly one Task, one Execution Record, and one Document Read
Evidence row were created and correctly linked. Evidence contained neither
the full document body nor an absolute path. Existing Memory and M6 Evidence
rows were unchanged.

A separate request for `../<document>` returned HTTP 400 with
`INVALID_DOCUMENT_IDENTIFIER` and null `task_id` and `execution_id`.
The database snapshot before and after this rejected request was identical.

On Windows PowerShell 5.1, the user's `GetResponseStream()` inspection
returned an empty error body. Parsing
`$_.ErrorDetails.Message | ConvertFrom-Json` exposed the expected failure
code. This was a client-side error-inspection issue; the API failure contract
and database behavior were correct. The [M7 PowerShell example](25-Seventh-Vertical-Slice.md)
now uses the working method.

The user checked the cleanup targets, removed only the synthetic M7 project,
membership, Task, Execution, Evidence, temporary document root, and local
mapping, then verified that baseline row counts and IDs were restored.
Token, memory, and M4 mapping fingerprints also matched their pre-test values.
No existing user data or Docker volume was removed.

## Existing-data preservation

Read-only counts before and after the M7 focused and full regression runs:

| Table | Before | After |
| --- | ---: | ---: |
| `noah.users` | 1 | 1 |
| `noah.api_tokens` | 1 | 1 |
| `noah.projects` | 0 | 0 |
| `noah.project_memberships` | 0 | 0 |
| `noah.memories` | 2 | 2 |
| `noah.tasks` | 2 | 2 |
| `noah.execution_records` | 3 | 3 |
| `noah.memory_write_requests` | 1 | 1 |
| `noah.document_tool_evidence` | 0 | 0 |
| `noah.document_read_evidence` | 0 | 0 |

Synthetic rows and temporary roots were removed by test cleanup. Existing
user, token, memories, prior Task/Execution IDs, M4 mapping, Compose
container, and Docker volume were not deleted or initialized. The M7 table
remains present with zero rows. No actual user project is registered yet.

## Remaining boundary

The same-Windows-user malicious local filesystem replacement race is outside
the M7 guarantee, as established before implementation. A production use
case that treats such a process as an attacker needs an OS/handle-based
ancestor traversal boundary. M7 does not summarize documents or ingest them
as Knowledge.
