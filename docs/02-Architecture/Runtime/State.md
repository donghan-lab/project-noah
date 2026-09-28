# NOAH State Contract — Current Memory Save and Tool Slices

> Status: current implementation contract, 2026-09-29. This documents the
> Memory Write path, M5 read-only recovery triage, and M6 read-only Tool
> execution, M7 restricted document read, and M8 single-document answer.
> M8 has its own Task/Execution and linked observation/answer evidence. This is
> not the complete future Task or Runtime state machine.

The [M9 two-document contract](../../01-Project/29-Ninth-Vertical-Slice.md)
below is **proposed and unimplemented**. It does not change the stored M1–M8
states or claim an M9 recovery mechanism.

## Boundaries

`noah.tasks` is durable canonical Task progress. `noah.execution_records` is
the durable result of an execution attempt. A Runtime or HTTP server process
can stop while the Task remains. Its termination is **not** evidence that the
Task failed. Memory is a separate side effect, not a replacement for Task
State. These boundaries follow DDR-001, DDR-002, and DDR-006.

The present `memory.save` implementation has one Task and one execution
attempt per authorized, validated new write. Rejections before Task creation
have a failed execution record with no Task. The M1 single-memory GET route,
M2 memory-list GET route, and M3 `POST /memories/query` do not create Tasks
or execution records. M6
`project.documents.list` does create both once its pre-Tool checks pass, as
specified below. Other future capabilities need their own side-effect and
retry rules.

## Stored states and transitions

The table describes the stored values and the `memory.save` transitions.
M6/M7 Tool transitions using the same values are specified below.

| Record | Current stored states | Transition and required evidence |
| --- | --- | --- |
| Task | `running`, `completed`, `failed` | A new authorized write starts `running` with verification `pending`. A verified memory readback permits `completed/passed`. A definite rolled-back write or verification failure permits `failed/failed`. |
| Execution record | `running`, `succeeded`, `failed` | A new write starts `running`. The same verified memory readback permits `succeeded` with `memory_id` and `verified_at`. A definite rolled-back error permits `failed` with a failure code. Pre-Task input or permission rejection is recorded directly as `failed` without a Task. |
| Task verification | `pending`, `passed`, `failed` | `pending` accompanies the new running Task; `passed` requires verified memory; `failed` accompanies a definite failure. |

The database constrains the allowed values, but it does not enforce this
entire transition graph. The current Memory Write service performs these
transitions. A terminal row must not be rewritten from a timestamp alone.

## Commit and evidence boundary

1. Authentication, input validation, and write permission precede Task
   creation and all memory side effects.
2. Task `running/pending`, execution `running`, and any user-scoped
   Idempotency-Key reservation commit together **before** the memory insert.
3. Memory insert, PostgreSQL readback, Task `completed/passed`, and execution
   `succeeded` with `memory_id` and `verified_at` commit together. A normal
   successful write cannot leave only one of these final updates committed.
4. A definite write or verification failure rolls back the memory transaction.
   Task `failed/failed` and execution `failed` with a failure code are then
   recorded together when PostgreSQL remains available.
5. If a commit acknowledgement or the database connection is lost, the
   outcome may be unknown. The service must not overwrite a possibly
   successful commit with a guessed failure.

For read-only triage, a confirmed success requires the completed/passed Task,
the succeeded execution, a non-null verification time, and an existing memory
whose creator and user owner match the actor where applicable. A confirmed
failure requires matching failed Task and execution states, a failure code,
and no memory reference. A failed pre-Task rejection is valid with no Task.
Missing or contradictory evidence is reported, not repaired by triage.

## Read-only Tool execution boundary

The following is the implemented M6 `project.documents.list` and M7
`project.documents.read` boundary. M7's byte and evidence checks are
specified in its [scope document](../../01-Project/25-Seventh-Vertical-Slice.md).

1. Authenticate the user, check project read membership, validate the request
   and model intent (M6), and resolve the operator-registered root before
   creating a Task. A rejection at these stages returns a structured error
   without a new Task or execution record. M7 has no model-intent stage.
2. Recheck authentication and project read membership immediately before
   reserving a `running/pending` Task and `running` execution in PostgreSQL.
   Their durable reservation precedes starting the Tool worker. A reserved
   attempt is distinguishable from a pre-Tool rejection even if no result was
   committed. M7 checks permission once more immediately before dispatch;
   revocation after reservation is a definite failed attempt with no file
   open. The Tool worker does not own canonical Task state.
3. M6 success requires a bounded, independently verified directory
   observation, a current permission check, and append-only Tool Evidence
   linked to the execution. Evidence, Task `completed/passed`, and execution
   `succeeded` with verification time commit together. M7 verifies bounded
   file bytes against the returned content and provenance before the same
   atomic final commit.
4. A **definite** Tool or verification failure means the worker has ended and
   the failure is established. If PostgreSQL is available, record Task
   `failed/failed` and execution `failed` with a failure code together. A
   failed Tool observation is not a successful result merely because the
   capability is read-only.

No new Task, execution, or verification database status is introduced by this
contract. M4 Idempotency-Key reservation applies to `memory.save`, not to an
M6 or M7 read. A fresh read is a new observation, not a replay of
earlier evidence.

## M8 single-document answer boundary

The implemented [M8 scope contract](../../01-Project/27-Eighth-Vertical-Slice.md) combines
one M7-style document observation with one bounded local model call. It does
not change the implemented M6/M7 routes or the stored status values. M8 must
not call the public M7 endpoint as a substitute for its own execution, since
that would create a separate completed Task and Execution.

1. Authenticate, check project read membership, validate the exact document
   basename and one bounded question, and confirm the operator mapping before
   reservation. A rejection here creates no M8 Task or Execution. Recheck
   token and membership before durably reserving one `running/pending` Task
   and one `running` M8 Execution. Reservation precedes the file-read worker.
2. Recheck permission immediately before the M7-style open. Verify the
   bounded original bytes, strict UTF-8 text, and source hash. A completed
   document observation is not yet an answered Task. Check the M8 Context cap
   without truncation, confirm permission again immediately before sending
   the verified text to the loopback-only local model, and pass no Tool-call
   authority, credential, or OS path.
3. Validate the model's limited outcome and up to three exact quote proposals
   against that same decoded text. NOAH calculates the Unicode character
   `[start, end)` positions; the model does not supply them. Recheck permission
   before final commit. A valid `insufficient` or `out_of_scope`
   response can have no quotes; `passed` means the bounded response contract
   was followed, not that absence of an answer in the document was proven.
4. Commit the source observation evidence, verified answer evidence, Task
   `completed/passed`, and Execution `succeeded` with verification time in one
   final transaction. Recheck permission immediately before the HTTP response;
   loss of access after commit withholds excerpts despite the durable success.
   A definite post-reservation
   failure may set Task `failed/failed` and Execution `failed` together with a
   safe code, if PostgreSQL is available. Do not expose a model answer or
   document excerpt when permission is lost before the response.

Model unavailability, timeout, invalid structured output, quote mismatch,
Context overrun, document-read failure, and storage failure remain distinct
failure reasons. A timeout without proof that execution cannot still finish,
lost DB connectivity or commit acknowledgement, and a lost HTTP response are
**unknown outcomes**, not evidence for `running -> failed` or an automatic
retry. M4's keyed write mapping does not apply to M8.

The implemented M8 document Context limit is 2,048 UTF-8 bytes after optional
BOM removal. `noah.document_read_evidence` stores the M8 execution's source
observation; `noah.document_answer_evidence` references that execution and
stores the outcome plus NOAH-verified quote/position array. Both rows and
terminal Task/Execution states commit together.

## Proposed M9 two-document answer boundary (not implemented)

An M9 request names exactly two distinct direct-child `.md` files in one
authorized project and one question. Authentication, project membership,
both document identifiers, the question, and the operator mapping are
preflight checks. Rejection before reservation creates no M9 Task or
Execution. Recheck token and membership, then durably reserve **one**
`running/pending` Task and **one** `running` Execution before either file-read
worker starts. This is an M9 execution, not two M7 or M8 HTTP executions.

Recheck membership immediately before each M7-style safe open. Record D1 and
D2 as separate verified observations with their own times and original-byte
hashes; reading them sequentially does not create one filesystem snapshot.
If either required observation fails, do not send only the other document as
a complete two-document Context. Check the combined Context budget without
truncation and recheck membership immediately before transmitting either
source to the local model. The model receives no Tool authority. Validate the
strict outcome and source-qualified exact quote proposals; NOAH computes
`[start,end)` in the claimed observed source. Recheck membership before
finalizing and again before disclosing the response.

Success, including a verified quote-free `insufficient` or `out_of_scope`
response, requires both source observations, valid model output, source-aware
verification, and append-only M9 Evidence. Commit both observations, answer
and quote Evidence, Task `completed/passed`, and Execution `succeeded` with
verification time in one transaction. `passed` verifies the bounded process,
not the semantic truth or completeness of the answer. A definite failure
after reservation can record Task `failed/failed` and Execution `failed` with
a safe failure code when storage is available. A denied pre-open check causes
no file access; a revoked final permission withholds the answer. An
unconfirmed timeout, DB connection/commit-acknowledgement loss, or response
loss leaves the outcome uncertain: **Unknown Outcome != Failed.** Do not
infer a terminal state or automatically retry.

The proposed two-source Evidence structure must not reinterpret the current
M7/M8 one-observation-per-Execution tables. No new stored Task, Execution, or
verification status is proposed. M4 keyed write idempotency remains
`memory.save`-only. M5 read-only Recovery Triage neither inspects nor
recovers a proposed M9 execution.

## Unknown outcome and idempotency

**Unknown Outcome != Failed.** `running` means no final durable result has
been recorded. It does not prove that a Runtime is still active, that it has
stopped, or that the side effect did not occur. Age and `updated_at` can
prioritize inspection but cannot establish success, failure, or permission to
retry. Client response loss also does not imply storage failure.

For implemented M6 and M7 Tool attempts, an execution timeout without proof that
the worker stopped, lost database connectivity or commit acknowledgement,
and a lost HTTP response do not establish failure or success. Retain the
durable state that can be proven and report uncertainty; do not infer a
terminal transition or silently rerun an uncertain attempt. A response may
be lost after a successful final commit, so inspect durable Task, execution,
and evidence before drawing conclusions.

For a keyed write, `noah.memory_write_requests` maps one authenticated user
and key digest to the original execution and normalized request fingerprint.
A retry with the same key and request may return a verified terminal result.
If the original record remains running, M4 returns `pending` without another
write. A different request with that key conflicts. An unkeyed legacy write
has no durable retry identity, so content equality is never a deduplication
rule. The local `.noah/failures.jsonl` fallback is diagnostic, not canonical
Task or execution state.

## Read-only recovery triage

Triage reports `verified_completed`, `recorded_failure`,
`unresolved_running`, or `record_inconsistent`. It also reports an outcome of
`succeeded`, `failed`, or `unknown`. The last value is an assessment, **not**
a new database status. `interrupted` and `recovery_pending` are not current
database states and are not inferred from process absence or time alone.

M5 triage currently selects `memory.save` only. It does not inspect or
automatically recover M6 `project.documents.list`, M7 Tool, or M8
executions; the proposed M9 is outside its scope too. Triage can inspect
Task, execution, key mapping, memory reference, and verification metadata
in a read-only PostgreSQL transaction. It does not
change those records, create or delete memory, or retry a capability. A
missing memory reference, mismatched actor, contradictory states, or missing
verification evidence must not be silently converted to success or failure.
Database unavailability means inspection was unavailable, not that no
unresolved work exists.

## Automatic recovery boundary

No automatic state transition or write retry is currently authorized for a
running or inconsistent record. In particular, process exit, server restart,
expired time threshold, absent visible memory, or a local failure log entry
alone cannot justify `running -> failed`. The current schema has no durable
runtime ownership, fencing, or heartbeat contract that could prove a prior
attempt cannot still commit. Any future automatic mutation needs a separately
reviewed state transition and side-effect reconciliation contract.
