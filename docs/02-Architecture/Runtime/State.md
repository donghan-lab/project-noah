# NOAH State Contract — Current Memory Save and Tool Slices

> Status: current implementation contract, 2026-10-02. This documents the
> Memory Write path, M5 read-only recovery triage, and M6 read-only Tool
> execution, M7 restricted document read, M8 single-document answer, and M9
> two-document answer, M10 controlled selection, and M11 read-only routing.
> M10 uses existing stored states; M11 adds no Task/Execution state. Neither
> has an automatic recovery transition.
> M8 has its own Task/Execution and linked observation/answer evidence. This is
> not the complete future Task or Runtime state machine.
> [M12 routing audit](../../01-Project/37-Twelfth-Vertical-Slice.md) is
> implemented as separate operational metadata, with no new Task/Execution
> status value. M12 user manual HTTP E2E has been completed separately.
> [M13 explicit Memory Save routing](../../01-Project/40-Thirteenth-Vertical-Slice.md)
> connects the existing write path to the router; it adds no Task/Execution
> status value. Automated validation and separate manual HTTP E2E are complete.

The implemented [M9 two-document contract](../../01-Project/29-Ninth-Vertical-Slice.md)
does not change the stored Task/Execution state values or add an M9 recovery
mechanism.

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

## M9 two-document answer boundary

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

The M9-specific two-source Evidence structure does not reinterpret the current
M7/M8 one-observation-per-Execution tables. No new stored Task, Execution, or
verification status was introduced. M4 keyed write idempotency remains
`memory.save`-only. M5 read-only Recovery Triage neither inspects nor
recovers an M9 execution.

## M10 controlled-selection boundary — implemented

The [M10 contract and implementation](../../01-Project/31-Tenth-Vertical-Slice.md)
accepts one question in one authorized project. Authenticate, validate
the question, check read membership, and resolve the operator root before
reservation; rejection creates no M10 Task/Execution. Recheck token and
membership, then reserve **one** durable `running/pending` Task and **one**
`running` Execution before starting the M6-style candidate-list worker.
M10 reuses lower-level M6/M7/M8/M9 verification functions, not their
HTTP routes, Tasks, Executions, or Evidence rows.

Recheck permission before enumeration and before sending complete, bounded
filename data to the selection model. A truncated or over-budget list is a
definite scope failure, not evidence that no document is relevant. Verify
the model's zero-to-two exact-name proposal against the observed list before
any selected file open. Recheck permission before each M7-style safe read,
before a separate M8/M9-style answer-model call, before final commit, and
before response disclosure. Each selected file gets a fresh observation;
the filename list and reads are not an atomic filesystem snapshot. Model
selection cannot confer filesystem or project authority.

A complete empty candidate list or valid zero selection may produce a
normal `no_document_selected` selection result with no read, answer-model
call, source, or quote. Commit its complete candidate/selection Evidence,
Task `completed/passed`, and Execution `succeeded` with `verified_at`
together; `grounded=false` does not assert that no answer exists. For one or
two selected files, success requires all M7 observations, M8/M9-compatible
quote checks, M10-owned selection/source/answer Evidence, and the same
terminal states in one final transaction. This does **not** repurpose the
existing M6/M8/M9 Evidence tables. A valid quote-free answer outcome after
a read is distinct from zero selection. `passed` verifies the bounded
process, not semantic truth.

A definite post-reservation failure may record Task `failed/failed` and
Execution `failed` together when storage is available. A selection-model
failure and an answer-model failure remain distinct. Unconfirmed timeout,
connection or commit-acknowledgement loss, and response loss preserve only
provable durable state: **Unknown Outcome != Failed.** No new stored Task,
Execution, or verification status is added. M4 keyed idempotency remains
`memory.save`-only; M5 Recovery Triage does not inspect or recover M10.

## M11 read-only routing boundary — implemented

The [M11 contract and implementation](../../01-Project/34-Eleventh-Vertical-Slice.md)
accepts one authenticated request selecting either the existing M3 Memory
Query, the existing M10 Project Document Auto Answer, or no action. The routing
model proposes only a fixed allowlist choice. NOAH validates it and invokes at
most one internal function; no new generic invocation runtime is implied.

M11 creates no parent Task, Execution, or routing Evidence. A pre-delegation
rejection or `no_action` creates none. If M3 is selected, its existing
request-scoped result and verified in-response Memory quotes remain **without
durable Task/Execution**. If M10 is selected, M10 alone owns its existing
one Task/Execution pair and candidate/source/quote Evidence. No M3/M10 HTTP
endpoint, Task, Execution, or Evidence is duplicated by the route. Existing
permission checks, verification, and terminal transitions remain owned by the
selected function; the router additionally withholds disclosure if current
authorization is lost. A delegated failure or uncertain M10 result must not
be converted into a routing success, fallback, or retry.

At the M11 validation baseline there was no shared persistent decision record
for a route choice. M12 now adds a separate bounded routing audit, especially
for M3 and `no_action`; this does not establish durable multi-step
orchestration. **Unknown Outcome != Failed** still applies to any delegated
attempt. No new Task/Execution state values are added; M5 triage remains
limited to `memory.save` and does not recover M11/M12 or M10.

## M12 bounded routing audit — implemented

The [M12 contract](../../01-Project/37-Twelfth-Vertical-Slice.md) adds
one durable **routing audit** identity per eligible authenticated M11 request.
It has been automatically validated and separately checked by manual HTTP E2E.
Audit is operational correlation,
not canonical Task state, an Execution attempt, Capability Evidence, or proof
that model selection was semantically correct. M3 remains without durable
Task/Execution; M10 keeps exactly its own one pair and Evidence; `no_action`
still invokes no Capability and creates no Task/Execution/Evidence, although
M12 adds one routing audit row for that decision.

After authentication, input/credential bounds, and any caller-supplied
project read precheck, reserve the audit row in a short committed transaction
**before** the routing model call. Preflight denials create no row. The
implemented audit-only transitions are `reserved` → `route_validated` →
`dispatch_prepared` → `observed`, with direct `observed` transitions for
definite routing failure, `no_action`, or pre-delegate rejection.
`dispatch_prepared` records a committed intention to call the delegate; it
does not prove the call actually began. Persist the result observation only
when NOAH has it. Do not hold a DB transaction across model or delegate work.
These audit stages do **not** add DB Task/Execution/verification states.

If audit reservation or a pre-delegate update is definitely or uncertainly
unavailable, invoke no delegate. For `no_action`, a terminal update failure
after committed `route_validated` yields HTTP 503 with
`routing.audit_status=unconfirmed`; `route_validated` is the last provable
stage and no Capability ran. If final audit recording fails after an M3 or
M10 result, retain the delegate's actual status and result; report audit
uncertainty separately and do not rewrite M10's committed state. A lost
commit acknowledgement, process exit, `dispatch_prepared` row, or missing
final update does not prove failure or license a retry. An M10 uncertain
outcome remains uncertain. M5 Recovery Triage stays `memory.save`-only and
does not recover routing audit or M10.

## M13 explicit Memory Save routing — implemented and manually validated

For a request with an explicit `memory_save.content`, authentication, exact
request shape, user-only target, content, routing question, and required
`Idempotency-Key` are validated before any routing audit reservation. A
preflight rejection creates no audit, model call, or delegated write record.
The audit reservation must commit before local Ollama availability/binding
checks or a routing model call. A model-stage failure may be recorded as an
M12 routing failure but never starts `save_memory()` or creates a Memory,
Task, Execution, or M4 key mapping. The write-branch model may propose only
`memory.save` or `no_action`, and sees the question and a payload-present
marker, not the stored content or key.

A verified `memory.save` proposal requires a fresh token check, then committed
`route_validated` and `dispatch_prepared` audit stages before the router calls
the existing `save_memory()` internal function **once**. An uncertain audit
reservation or pre-delegate update stops before the write. `dispatch_prepared`
is an intention, not proof of invocation. The existing save path alone owns
Memory insertion, its Task/Execution, M4 mapping, readback, and terminal state.
The router adds no parent or duplicate Task/Execution. A valid `no_action`
adds only its M12 operational audit row.

After a returned save result, the router records only verified request and,
where present, Task/Execution IDs in the separate audit. An M1 rejection
Execution without a Task is not fabricated into an audit Task/Execution pair.
The original M1/M4 HTTP result, including replay, conflict, pending, and
`WRITE_OUTCOME_UNKNOWN`, remains authoritative. A failed final audit update
marks `routing.audit_status=unconfirmed` without changing or retrying that
result. The audit is not write-outcome evidence for M5; M5 remains read-only
and `memory.save`-only. **Unknown Outcome != Failed.**

## M14 explicit user Memory suppression — implemented, automated and manual validation

`POST /memories/<id>/suppress` is a deterministic owner-only operation outside
the Router and M12 audit. An authorized user-scope Memory remains durable, but
`suppressed_at` changes once from null to a persisted timestamp. A first real
transition creates one `memory.suppress` Task and Execution in the same short
transaction as the conditional update. NOAH rechecks the original credential,
owner, and scope, then reads the row back and verifies the unchanged original
fields before committing `completed/passed` and `succeeded` with `memory_id`
and `verified_at`. A repeat returns `already_suppressed` with the original
timestamp and creates no new Task/Execution. No persistent intermediate
`running` reservation or new DB status is introduced.

Before the first commit, a provably rolled-back update or readback failure
cannot leave a suppressed row or terminal Task/Execution. Lost commit
acknowledgement yields `SUPPRESSION_OUTCOME_UNKNOWN`: the response does not
claim success or a failed transition, return provisional Task/Execution IDs
as durable, or trigger automatic retry. M5 triage remains `memory.save`-only;
M4 save replay does not clear later suppression. M14 has no routing-audit row.

M2 ordinary list and M3 search filter suppressed rows in SQL before cursor,
ordering, limit, and model context. Owner direct lookup remains a management
read of the retained row and reports its suppression state. M3 direct and M11
routed Memory responses recheck every Memory actually sent to the model at
their respective final public-disclosure boundaries. If any is no longer
visible, they withhold the entire generated answer, citations, and search
metadata. These ephemeral IDs create no audit or parent Task. An ordinary
GET/list may still deliver a state observed before suppression committed.
Separate operator manual HTTP E2E for M14 completed on 2026-10-06.

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
executions; M9 and M10 are outside its scope too.
Triage can inspect
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
