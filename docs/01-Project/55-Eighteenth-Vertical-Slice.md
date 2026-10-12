# M18 Bounded Durable Task Intake & Explicit Execution

> Status: **approved functional contract; M18 implementation, deterministic
> automated validation and isolated actual Ollama HTTP E2E passed**.
> Baseline: `main@f83ae156aa70103d5e7d404469f4be0c42c7d299`.
> Baseline facts and the implementation plan below retain their original
> pre-implementation reference point. Actual results are recorded in `56`/`57`;
> final commit/push state is established by Git. Personal DB deployment has
> not been performed.
> First task kind: `project.document.question`, an explicit single-document
> question. Constitution, Blueprints, Accepted DDR-001-006 and M1-M17 contracts
> remain authoritative. This document does not authorize implementation,
> migration application, model calls, or deployment.

## Goal and observable slice

An authenticated user explicitly supplies a project, one logical Markdown
document name, and a question. NOAH commits an independently owned Task in
`ready` state without an Execution, file read, model call, or routing audit.
After a process restart the user can inspect that same Task, explicitly run
it once, and receive a bounded verified answer. After another restart the
user can retrieve the stored result under current authorization without a
model call or current-file read.

This is durable work intake, explicit execution, and historical result
inspection. It does not implement arbitrary in-flight continuation. A Task
is not owned by a Session, HTTP handler, model, or Router. Closing a Session
has no effect on this Task. The caller uses the returned Task ID for later
operations; natural-language selection of a previously registered Task is
not part of M18.

## Baseline facts and ownership

`noah.tasks` currently has actor, fixed goal, status, verification status,
and timestamps; its status domain is `running | completed | failed`.
Existing document entry points create their own running Task/Execution pair.
There is no current user-facing Task intake/list/result API. M5 recovery
triage is read-only and specific to `memory.save`, including its fixed goal
label. M16 stores Session lifecycle and audit references. M17 creates a new
Task for a follow-up; it does not continue an earlier Task.

M18's Task row plus its immutable kind-specific definition are the work
contract. Task/Execution rows remain canonical state; Context is ephemeral
model-facing projection. Existing M7 `execute_document_read()` and
`validate_read_observation()`, and M8 `validate_question()`,
`model_messages()`, `verify_model_evidence()`, and `assemble_answer()` are
reusable primitives. Do not call the high-level `answer_project_document()`
or another M7-M17 execution-owning endpoint/function to run the registered
Task: that would create another Task or independent terminal boundary.

Reuse execution capability `project.documents.answer`; it already denotes
the one-document answer operation. `project.document.question` is a new
task-kind identifier, not an existing capability or routing-model choice.
The definition association identifies M18 Tasks; capability or goal text
alone is not enough. M18 has no Routing Audit, parent Task, Session FK,
generic dispatcher, or separate Artifact store.

## Exact HTTP request contract

Use four dedicated operations. They do not extend `POST /requests/route`.

| Operation | Request | Confirmed response |
| --- | --- | --- |
| Register | `POST /tasks/document-questions` with the exact object below | 201, `status=succeeded`, `outcome=task_registered`, confirmed registration facts and a coherent currently observed Task |
| List | `GET /tasks?limit=20&cursor=...` | 200, `status=succeeded`, `outcome=tasks_listed`, authorized M18 summaries and nullable `next_cursor` |
| Inspect | `GET /tasks/<task_id>` with no query | 200, `status=succeeded`, `outcome=task_inspected`, current committed state and authorized historical result if available |
| Execute | `POST /tasks/<task_id>/run` with exactly `{}` and no query | 200 on confirmed terminal answer, `status=succeeded`, `outcome=task_executed`, same Task, its one Execution and result |

```json
{"project_id":"<canonical project UUID>","document_name":"release.md","question":"이 문서의 배포 조건은 무엇인가?"}
```

Require one Bearer Authorization header on every operation. Reject duplicate
Authorization headers. The original credential in a revalidation below is
the credential of that HTTP operation, not a persisted registration token;
another currently valid token for the same owner may inspect/run the Task.
Require canonical lower-case, hyphenated UUIDs for
project and Task IDs. Reject extra/duplicate JSON keys, non-object JSON,
invalid UTF-8, more than 4,096 request-body bytes, client-supplied actor,
Task/Execution IDs, scope, capability, paths, instructions, or model output.
POST bodies are JSON encoded as UTF-8. Register/run do not accept query
parameters. These new paths reject any `Noah-Session-Id` or `Idempotency-Key`
header with 400 `INVALID_REQUEST`; neither existing mechanism applies.
Existing endpoints retain their existing header/parser behavior.

Use M7's exact document-name validation: one allowed direct-child `.md`
name, at most 255 characters, no path separators, hidden/reserved name,
traversal, invalid control character, or name correction. Require valid
UTF-8 encoding. Use M8's `validate_question()` unchanged: strip surrounding
whitespace once, require a nonempty question of at most 300 Unicode
characters and 512 UTF-8 bytes, and reject disallowed controls. This
normalized question is the only execution question. Do not summarize,
extract, infer, or replace it from any other request or prior response.

Authenticate before domain operations. Validate shape and known-credential
exclusion before registration; recheck the original credential and current
project read membership in the registration transaction. Missing/unreadable
projects both return 404 `PROJECT_NOT_FOUND`. Successful registration does
not certify that the file exists, the root is configured, or the model is
available: no mapping lookup, filesystem read, or model availability probe
is needed to store the logical work definition. Those are execution checks.
Rejected preflight creates no Task, definition, Execution, Evidence, or audit.

## Public objects and response semantics

Every response carries a newly allocated HTTP-operation `request_id`.
Single-Task success responses also contain top-level `task_id`, nullable
`execution_id`, `task`, nullable `execution`, and nullable `result`.
The IDs in nested objects must equal the top-level IDs. Register's request
ID is persisted as `registration_request_id`; later GET request IDs do not
replace it. The winning run's request ID is the Execution's persisted
request ID and appears as `execution.request_id`. A GET request ID is never
presented as the request that executed the work.

Only registration success also contains `registration` with exactly
`status=confirmed`, `initial_task_status=ready`,
`initial_verification_status=pending`, and `execution_created=false`.
These describe the registration transaction, not the later readback.
`task`, `execution`, and `result` describe that readback's coherent snapshot:
they may already show running or terminal state after another explicit run.

`task` has exactly: `id`, `kind` (`project.document.question`), `status`,
`verification_status`, `created_at`, `updated_at`,
`registration_request_id`, and `definition`. `definition` has exactly
`project_id`, `document_name`, and normalized `question`. UUIDs are strings;
timestamps are timezone-aware ISO 8601 strings. The work's completion
criterion is fixed by this kind: complete the bounded observation/answer
protocol and verify the stored result, not prove every semantic demand.

`execution`, when present, has `id`, `request_id`, `capability`, `status`,
`created_at`, `updated_at`, nullable `verified_at`, nullable `failure`, and
`observation`. `failure` is a safe code/category/message object derived
from recorded failure fields, never raw exceptions. `observation` is a
non-persisted interpretation with exactly these values:

| Committed records | `execution.observation` | Result |
| --- | --- | --- |
| ready/pending, no Execution | No execution object | null |
| running/pending and running Execution | `unconfirmed` | null |
| completed/passed, succeeded/verified Execution and both validated Evidence rows | `verified` | Historical result |
| failed/failed and matching failed Execution | `recorded_failure` | null |

For running rows, `unconfirmed` means there is no confirmed terminal result;
it is not proof of a currently alive worker, a failed worker, or no model
call. GET can succeed at observing an unconfirmed Task: top-level
`status=succeeded` describes the read, not execution success.

`result` has exactly `capability`, `project_id`, `document_name`, `outcome`,
`grounded`, `answer`, `evidence`, `document`, and `temporal_scope`.
Use `temporal_scope=execution_observation`; this is not a claim that the
document is unchanged at response delivery. `document` contains `root_id`,
`document_name`, `observed_at`, `byte_length`, `content_sha256`, and
`evidence_execution_id`. Each evidence item is `{quote,start,end}` with
Unicode half-open positions. `answer` is reconstructed by M8's
`assemble_answer()` from the saved outcome/quotes, not persisted model prose.
The immediate run response uses this same historical object.

All five existing answer outcomes are preserved: `supported`, `partial`,
`insufficient`, `conflicting`, `out_of_scope`. `grounded` is `bool(quotes)`;
an outcome with no quotes can still be a completed, verified bounded
operation. Completion is not a promise of semantic completeness or
real-world truth. Never rewrite `partial` to `supported`.

List responses have exactly `status`, `request_id`, `outcome`, `items`, and
`next_cursor`. Items have exactly `id`, `kind`, `status`,
`verification_status`, `created_at`, `updated_at`, `project_id`, and
`document_name`. No question,
quote, answer, failure detail, or Execution body appears in a list item.
`limit` is one decimal integer from 1 to 100, default 20. `cursor` is one
bounded (at most 256 characters), strictly decoded base64url JSON object
with exactly timezone-aware `created_at` and canonical `id`. Reject unknown
or repeated query fields. Order descending by `(tasks.created_at,tasks.id)`;
apply the owner, M18-definition, and current project visibility predicates
in SQL **before** keyset filtering and `LIMIT limit+1`. Return no total
count. The cursor is a position, never authority or snapshot continuity.
Concurrent state changes may be observed on later pages; registration time
and cursor order are not human conversation order.

## Persistence and minimal migration

Plan `database/014_document_question_tasks.sql`; write/apply it only after
separate implementation approval. Expand the existing `tasks_status_check`
to allow `ready` in addition to the three unchanged states. Do not rewrite
existing rows, goal labels, verification meanings, or Execution status
domains. A ready Task uses `verification_status=pending`.

Add one `noah.document_question_tasks` table, not a generic argument store:

| Column | Required semantics |
| --- | --- |
| `task_id` | UUID primary key, FK to `tasks.id`, `ON DELETE NO ACTION` |
| `registration_request_id` | Non-null unique server-generated UUID; correlation only, not idempotency |
| `project_id` | Non-null UUID FK to `projects.id`, `ON DELETE NO ACTION` |
| `document_name` | Non-null text, 1-255 characters; exact name rules also enforced in NOAH |
| `question` | Non-null normalized text, 1-300 characters and at most 512 UTF-8 bytes; application validation remains authoritative for normalization/controls |
| `execution_id` | Nullable unique UUID FK to `execution_records.id`, `ON DELETE NO ACTION`; assigned only at the first confirmed claim |

The immutable definition is project/name/question/registration request ID.
Only `execution_id` may move from null to the one allocated ID; never clear
or replace it. Actor/status/timestamps come from `tasks`, not duplicated
columns. Use the distinct fixed Task goal `Answer an explicitly registered
project document question`, so M5's existing fixed-goal classification is
unchanged. The question remains in the definition only; the composite work
contract supplies the user-specific objective and fixed completion criteria.

A Task owner/creation-time/ID index may support bounded listing. Add no
global uniqueness constraint on `execution_records.task_id`: existing
semantics and future attempts must not be changed for all Tasks. The unique
definition reference does not by itself prove that no extra Execution was
inserted. The locked claim, conditional state update, zero/one cross-record
validation and one internal execution path enforce that invariant. An
out-of-contract extra Execution is an integrity failure, not a candidate
for arbitrary latest-record selection.

Reuse `document_read_evidence` (004) and `document_answer_evidence` (005)
for this same `project.documents.answer` Execution. Insert exactly one of
each only at successful terminal commit. No new Evidence table, M17 lineage,
candidate/source table, routing-audit change, success-report blob, full
document, or generated answer is required. Existing Evidence and its exact
quote persistence remain explicit sensitive storage.

All new FKs use NO ACTION, with no cascade or deletion API. Registration
and Evidence follow existing durable retention; no TTL or automatic purge
is introduced. Future principal/project/task deletion must account for
these dependencies. M18 creates no general deletion policy.

Source schema after migrations 001-014 has 21 tables. This is not a claim
about the personal DB: its Migration 013 remains unapplied, and neither
013 nor 014 needs to be deployed there for M18 development. Replaying the
existing initialization sequence on an isolated DB must preserve rows.
CHECK replacement can acquire table locks/validate existing rows; use
bounded migration execution and review catalog/data preservation before
any separately approved existing-environment application. Do not use a
DB reset, schema rebuild, or volume removal to deploy this change.

## Registration, state transitions, and one execution claim

Registration commits one ready/pending Task and its definition together,
with null execution reference. Only a confirmed commit and consistent DB
readback authorize a 201 response. The post-commit readback is read-only,
checks the exact normalized inputs, registration request ID, and coherent
current state, and rechecks authorization. The registration transaction
itself creates zero Executions. After it commits, another authorized request
may discover and execute the Task before readback. A coherent running or
terminal state is normal advancement: return 201 with the confirmed
`registration` facts and current observed state; do not report registration
failure or `TASK_RECORD_INCONSISTENT` merely because an Execution now exists.
Test both running and terminal advancement deterministically. An actually
failed/unconfirmed readback is not permission to create
another Task or undo a possibly committed registration.

| Transition | Authorized operation |
| --- | --- |
| absent -> ready/pending | One confirmed registration transaction, zero Executions |
| ready/pending -> running/pending | One confirmed run claim plus one running Execution and definition binding |
| running/pending -> completed/passed | One confirmed atomic success Evidence/terminal transaction |
| running/pending -> failed/failed | Confirmed deterministic failure recording for this exact running attempt |

No completed/failed/running Task transitions back to ready, and no second
attempt, reset, pause, cancel, restore, or new question/version is allowed.
Registering an independently requested task is not retrying or continuing
this Task. Intake has no deduplication promise: two deliberate registrations
are two Tasks. Do not blindly register again after a lost/unknown response.

Run preflight validates authentication, path, empty object, owner and
current project authority. It does not choose a target with a model or
consult a Session. The authoritative claim is a short, explicit READ
COMMITTED transaction: validate the original credential, acquire the owned
M18 Task row `FOR UPDATE` in a separate statement, then freshly read the
definition, project membership, status and all Executions for that Task.
No code path locks an Execution or definition before the Task. Require
ready/pending, null binding and zero Executions; revalidate the credential
after waiting for the lock and before mutation. Insert one running
Execution with this run request ID, matching actor/Task and existing
capability; assign its ID to the definition and conditionally update the
same ready Task to running. Require exact affected-row counts. Commit all
three changes atomically.

The confirmed claim commit is the execution eligibility boundary. Do not
read the file, probe/call the model, or dispatch a worker unless it is
confirmed. No transaction or Task lock remains held during file/model work.
Use finite 3-second lock and 5-second statement timeouts for these short
DB operations, with no automatic transaction retry on deadlock or timeout.
These are DB-operation bounds, not model execution limits.

A concurrent loser reads fresh state after the lock, rather than relying
on its earlier preflight snapshot. Running returns 409
`TASK_EXECUTION_UNCONFIRMED`; completed/failed returns 409
`TASK_ALREADY_EXECUTED`. Neither returns a replayed answer or dispatches
anything; the caller can explicitly GET the Task. A lock timeout returns
503 `TASK_BUSY` without inferring what the other request did. A claim whose
rollback is definitely confirmed leaves ready state and zero new
Executions; only after an authorized GET proves that state may the user
make a separate explicit run decision. This is not automatic retry.

Credential/project checks guarantee that revocation visible before each
check blocks the subsequent protected operation. They do not promise
global linearizability against every concurrent revocation or withdraw
Context already delivered to the local model. Task registration is not a
durable authorization grant.

## Execution, Context, verification, and atomic terminal state

The new bounded execution path owns the already claimed Task and Execution.
Resolve the current operator mapping only after the claim, validate its
logical root and M7 safety rules, and freshly read the specified file using
the bounded no-follow worker and independent observation validation. Missing
or unsafe files and mapping errors are definite execution failures when
worker termination and failure recording can be confirmed. Do not search
for another document, use a previous quote, or substitute a root/name.

Registration does not pin document bytes. Execution uses the file observed
when it actually runs; a file changed between registration and execution
is not itself an error. Record the actual logical root/name, original-byte
length/SHA-256, UTF-8/BOM observation and timestamp in the read Evidence.
Retain M7's 65,536-byte read limit and M8's narrower 2,048-byte decoded
Context limit, 3,456-byte serialized system/user prompt limit, question
bounds, at most three quotes of at most 240 Unicode characters, exact quote
membership, duplicate rejection and first Unicode `[start,end)` computation.
Reject oversized Context rather than truncate it.

Recheck original credential and project permission before content reaches
the answer model. Reject the known caller credential and configured DB
password from question, document identifier and model-facing content;
rejected values are not logged or persisted as diagnostic text. This is a
known-credential guard, not universal personal-data/secret detection.
The caller is responsible for the explicitly submitted question; synthetic
data alone is used in validation. The model sees only the bounded question,
logical document identifier and verified document body under unchanged M8
untrusted-data instructions/schema. It receives no Task/user/project ID,
token, credential, OS path, prior answer, audit record, or Tool authority.

After the one synchronous model call, validate outcome/quotes through M8.
Recheck credential/project authority before the verification worker read.
Perform another bounded safe-read of the same current logical root/name
before the success transaction; require byte length, encoding/BOM and hash
to match the observation sent to the model. A mismatch/missing/replaced
mapping yields 409 `DOCUMENT_CHANGED` with no success Evidence. This checks
two observations, not a filesystem lock or immutable future content.

The success transaction locks this Task first, validates current original
credential/project authority and the exact definition/Execution binding,
then inserts the one read and one answer Evidence row and conditionally
updates Task to completed/passed and Execution to succeeded/verified.
Match actor, capability, request ID, Task, binding and expected running
states; require exact row counts. Commit once. If any insert/check/update
fails and rollback is confirmed, no successful Evidence/terminal subset
may remain. A separate deterministic failure transaction may mark this
same attempt failed only when the preceding result transaction is known
rolled back and no success can have committed. Never run such compensation
after unknown acknowledgement or ambiguous rollback.

Failure recording also uses Task-first lock order and matching running
rows/binding. It may record the already authenticated attempt's observed
authorization loss without releasing private input/output; it never writes
success Evidence or mutates the work definition. Failure detail is safe
category/code, not question, content, model output or exception text.

Confirm committed state and Evidence before publishing the result. Recheck
current token/project permission immediately before public disclosure.
Revocation or a failed authorization observation after success commit
withholds the response, but does not rewrite completed Task/Execution.
The published result is explicitly the historical execution observation;
later file changes are neither silently adopted nor a reason to mutate it.

## Result inspection, privacy, and current access

List/inspect/run are limited to Tasks with the M18 definition and this
authenticated actor. Legacy M1-M17 Task IDs, nonexistent IDs, other-user
IDs and an owner's now-unreadable project all return 404 `TASK_NOT_FOUND`
on inspect/run, without disclosing goal, question, existence, state or
Execution. Missing/invalid/revoked tokens return 401 `UNAUTHENTICATED`.
Current project read permission is sufficient; no project write privilege
or new role is introduced for this read-only document operation.

Inspection uses one explicit REPEATABLE READ, READ ONLY transaction for a
coherent snapshot of Task, definition, zero/one Execution and both Evidence
rows. Release it before the separate fresh final authorization check;
do not reuse its older permission snapshot as that final check.
Cross-check ownership, project, name, capability, binding, expected
status/verification, Evidence IDs,
hash/encoding/size fields, outcome and quote schema/positions. Completed
without the full verified set, ready with an Execution, wrong binding,
extra Executions or contradictory records yields 502
`TASK_RECORD_INCONSISTENT` and no definition/result body. Do not infer a
missing terminal result from a pagination prefix or read mixed snapshots.
Failed attempts have no success Evidence. Running records with terminal
Evidence are inconsistent, not an invitation to repair them.

Reconstruct the answer from persisted verified Evidence. Inspect does not
call a model, a safe-read worker, or local mapping and does not write data.
Exact quotes were checked against bytes during execution; since the whole
document is not stored, GET verifies durable record consistency, not fresh
quote membership against a potentially changed file. Display observation
time/hash and historical scope. A current file deletion/change does not
prevent historical result inspection while project authority remains.

Before exposing an inspect object or list page, freshly revalidate the
original token, current Task owner/definition binding and current project
authority for every object to be returned. If any selected page item loses
visibility, withhold the whole page with generic 404 `TASK_NOT_FOUND`;
do not expose counts/cursors or
silently return a filtered prefix. A DB error at this final boundary
returns 503 `DATABASE_UNAVAILABLE` with no private data. These checks
guarantee their observation times, not access after a later revocation.

Questions are opt-in private work inputs, not Memory, Knowledge, chat
history, Identity, or routing-audit data. Only an authorized owner can
receive them on inspect; lists omit them. Store no request body, credential
or credential hash, password, prompt, raw model JSON, full document, OS
path/mapping, or generated answer in the Task definition or diagnostics.
Existing API token hashing remains in its existing auth table. Evidence
contains the bounded source quotes by design, with the same current
owner/project disclosure gate. No public Task/Evidence browser is added.

## Exact failure, response-loss, and restart contract

Use existing `_failure`-style safe envelopes: `status=failed`, operation
`request_id`, nullable `task_id`/`execution_id`, and `failure` with code,
category, safe message, `recoverable`, and `retryable=false`. A known owned
Task ID may be included after authorization; preflight non-enumeration
failures have null IDs. After claim, confirmed failures carry this Task and
Execution. Never expose raw DB/model errors. New codes below are M18 API
decisions, not claims that they already exist in code.

| Condition | HTTP/code and durable meaning |
| --- | --- |
| Invalid shape/query/header/UUID | 400 `INVALID_REQUEST` or `INVALID_TASK_ID`/`INVALID_PROJECT`; no mutation/model/file work |
| Invalid document/question or known protected credential | Existing M7/M8 safe 400/415/422 code; no registration on rejected input |
| Unauthenticated; missing/unreadable project at registration | 401 `UNAUTHENTICATED`; 404 `PROJECT_NOT_FOUND`; no new records |
| Inaccessible/non-M18 Task | 404 `TASK_NOT_FOUND`, null IDs and no state disclosure |
| Storage unavailable before any mutation | 503 `DATABASE_UNAVAILABLE`; no inferred durable transition |
| Short transaction wait/deadlock with confirmed rollback | 503 `TASK_BUSY` (Timeout); no dispatch or automatic DB retry |
| Registration/claim/final/failure commit acknowledgement or rollback/readback unconfirmed | 503 `TASK_OUTCOME_UNKNOWN` (Environment Failure), provisional IDs where allocated; no guessed terminal state, compensation or retry |
| Run on running or terminal Task | 409 `TASK_EXECUTION_UNCONFIRMED` or `TASK_ALREADY_EXECUTED` (Invalid Input); zero new Execution/model/file work |
| Broken stored relation/result | 502 `TASK_RECORD_INCONSISTENT` (Verification Failure); withhold private object, no repair |
| Definite file/model/quote/Context error after confirmed claim | Preserve applicable M7/M8 safe code/status; this one failed attempt only if failure commit confirmed |
| File observation changed during answer work | 409 `DOCUMENT_CHANGED` (Verification Failure); failed attempt if confirmed, no success Evidence |
| Safe-read worker termination cannot be confirmed | Existing `TOOL_OUTCOME_UNKNOWN`/timeout status with allocated IDs; retain unconfirmed state, no second worker or model call |
| Definite Evidence transaction error with confirmed rollback | 503 `EVIDENCE_WRITE_FAILED` (Environment Failure); record failed attempt only if its failure transaction also confirms |
| Authority lost after confirmed success | 401 or generic 404; withhold result, keep canonical completed/succeeded/Evidence |

`TASK_OUTCOME_UNKNOWN` uses the repository's historical top-level failed
failure envelope. That transport envelope does **not** assert that the
stored Task or Execution is failed. Diagnostics must label codes ending
`_OUTCOME_UNKNOWN` as unknown, consistent with current `service.py`.
Registration unknown returns the provisional Task ID at top-level
`task_id`, `execution_id=null`, and no speculative Task object. Claim/final
unknown returns the authorized Task ID and provisional/known Execution ID
where allocated, with no speculative result. `recoverable=true` for this
Environment Failure denotes a need for investigation, not automatic
recovery or retry permission.

After a lost registration response without its server-generated ID, use
the bounded owner list/inspect for manual observation if possible. Matching
logical inputs is not proof of a unique registration or HTTP delivery;
M18 does not guarantee reconciliation of an ID the caller never received.
No M4 mapping, client idempotency key, new replay subsystem or inferred
input deduplication is introduced.

After lost run/terminal response, inspect the known Task. A coherent verified
terminal result is available without executing again. A coherent ready
Task with no Execution is an observation of no committed claim, not a
universal proof that an unknown transaction cannot later commit; do not
send another run merely to resolve an uncertain response. A running row
may represent a live request, a stopped process, or an uncertain terminal
commit. Do not decide from age, process restart, or absence of HTTP reply
that it failed. A successful claim proves reservation, not actual worker
start. Repeated run always refuses that committed attempt.

M18's authenticated GET is its read-only observation/diagnostic path. It
returns committed state, IDs/timestamps and the interpretation above;
unknown DB observations disclose no private object. No M5 recovery scope
extension, background watchdog, orphan reset, automatic resume, lease,
fencing protocol, cancel endpoint, or repair command is implemented. Ready
work and confirmed terminal results survive restart; unresolved running
work remains blocked for separate future recovery review.

## Compatibility and architecture rationale

DDR-001/006 support durable work contracts and independent canonical
Task/Execution state. DDR-002 permits a bounded logical Harness without
one shared physical execution layer. DDR-003 keeps this explicit input and
Evidence distinct from Memory/Knowledge promotion. DDR-004 does not require
a universal Artifact store for these existing observation records.
DDR-005's protected NOAH Identity is not replaced by the authenticated user.
No Accepted DDR or Blueprint change is required for this bounded contract.

M1 save, M2 list, M3 query, M4 replay, M5 triage, M6-M10 document endpoints,
M11-M15 routing, M16 Session and M17 follow-up retain their inputs, Task
ownership, status/result semantics and Evidence/audit relations. Their
Tasks still start running; only M18 intake creates ready Tasks. In
particular the new fixed goal must not match M5's memory-save goal, and new
inspection/list endpoints do not silently expose legacy Task records.
No Router prompt/candidate/schema or `routing_audit` change is needed.

## Deterministic validation and isolated actual E2E plan

At initial contract drafting, no M18 test, migration, model call or E2E had
been performed. The following remain acceptance requirements; completed
validation results and their limits are recorded separately in `56`/`57`.

| Boundary | Required deterministic proof |
| --- | --- |
| HTTP/preflight | Exact/duplicate/extra JSON keys, UUIDs, query/header rules, UTF-8/size/control limits, no authenticated-input leakage, unauthorized/invalid requests have zero new records or calls |
| Intake | One Task/definition atomic commit/readback, normalized question exactness, ready/pending, zero Execution/Evidence/Audit/file/model calls; definite rollback versus acknowledgement/readback unknown |
| Disclosure | Owner/project isolation for all four operations; SQL visibility before list limit; no question in list; fresh final page/object recheck; revoked access after completion withholds result without rewriting truth |
| Claim | Real PostgreSQL 17 barrier/event concurrency: two runs, Task lock wait, fresh post-lock state, exactly one bound Execution and model attempt; timeout/deadlock/rollback/unknown never dispatch automatically |
| Definition/state | Immutable input/binding, disallowed re-run/transitions, no duplicate Task, zero/one Execution cross-check, wrong actor/capability/request/project/Evidence rejected |
| Answer | Current safe file/mapping checks, M8 Context/quote limits and all five outcomes, malformed model/injection/credentials rejected, exact Unicode/hash/BOM, changed file before terminal prevents success |
| Atomicity | Both Evidence and both terminal updates commit together; actual FK/constraint rollback, failure recording rollback, unknown acknowledgements and guarded failure recording never fabricate success/failure or compensate blindly |
| Restart/inspection | Fresh-process ready read and run, fresh-process terminal read, response IDs distinguished, answer reconstruction with zero model/file/mapping calls, changed/deleted current file leaves authorized historical result readable |
| Process interruption | Confirmed claim then process termination leaves one running attempt; inspect unconfirmed, another run refuses, no guessed failure/recovery; unknown registration/run responses are not automatically resent |
| Regression | Full M1-M18 and focused M4/M5/M8/M11-M17; legacy Task statuses/goal triage/replay, M3 no Task, M10 own pair, M12 audit and M16/M17 Session semantics unchanged |

Every test runner and every operator DB helper must first prove the loaded
module root, synthetic configuration path, actual connection destination,
and resource ownership. Do not assume a safe working directory implies a
safe imported module or captured connection factory. Use an allowlisted
temporary source copy excluding `.git`, private `compose/.env`, `.noah`,
mapping, dumps, private documents and credentials. Supply only synthetic
configuration and mapping. A separate PostgreSQL 17 tmpfs container has
no existing named-volume mounts and exposes only an owned loopback port.
Inspect the configured destination before connecting, and verify database/
container identity through that isolated connection only. A helper loading
the original source/configuration stops **before** connecting. Apply 001-014
only there. Recheck this gate after process restart and before cleanup or
diagnostics, including when removing/changing the source-copy directory.

The actual-model HTTP run uses installed `gemma4:12b-it-qat` on owned
loopback-only `127.0.0.1:11435`, never ordinary `11434`; no automatic model
download/replacement. Use a conflict-free owned NOAH process, one synthetic
user/token, project/read membership, and one small `.md` with public facts.
Capture the full isolated 21-table row-count/private-fingerprint baseline
in private runtime memory before fixture creation; output neither private
values nor fingerprints. Verify POST encoding offline on PowerShell 5.1
as a single `System.Byte[]`, including Korean strict UTF-8 JSON.

Minimal planned live flow:

1. Register once (201); read-only proof of one ready Task/definition and
   zero Executions/Evidence/Audits/model calls.
2. Stop/restart only the owned server; GET this same ready Task (200).
3. Run once with `{}` (200). Accept `supported` or `partial` with a
   question-relevant exact quote; do not force supported or retry for it.
   Check one same Task/Execution, definition binding, both Evidence rows,
   observed hash/Unicode positions and zero routing audits.
4. Stop/restart the owned server; GET the same historical result (200),
   unchanged IDs/Evidence and zero new model/file/DB mutation.
5. Stop the owned server; prove exact fixture ownership and whole DB delta.
   In one reviewed transaction delete answer Evidence, read Evidence,
   definition (releasing its Execution FK), Execution, Task, membership,
   project, token and user, using exact IDs/bindings/counts. On mismatch
   roll back; no broad DELETE or retry of unknown commit. Restore the
   original isolated baseline exactly before removing owned disposable
   resources. Keep source schema; do not reverse migrations as data cleanup.

There are exactly two planned POSTs (one register and one run), and two
GETs. Running after registration/restart is the first execution, not a
replay. Failure injection and concurrency are deterministic-test scope,
not live fault injection. Unexpected response/model result, uncertain
commit, ownership mismatch or destination ambiguity stops immediately;
do not resend, switch a question, automatically clean up an unknown state,
or claim completion. Only separately verified owned processes/resources
may be stopped/deleted; no recursive filesystem deletion is required.

Do not access the existing personal PostgreSQL/named volume, private
settings/mapping/data, or ordinary Ollama 11434. M17's personal-DB deployment
and environmental cleanup limitations remain separate. Existing-environment
backup, migration 013/014 application and E2E require separate approval;
they are not prerequisites or accomplishments of this isolated M18 plan.

## Implementation sequence, expected files, and acceptance

After independent contract review and separate implementation approval:

1. Add migration 014 and register it in `noah/db.py`; verify additive schema
   and non-cascading catalog relationships in the isolated DB.
2. Add bounded `noah/document_task.py` for intake, authorized list/inspect,
   claim, primitive-based execution and terminal/result consistency. These
   proposed names do not claim current functions exist.
3. Add the four HTTP routes and strict parsing in `noah/__main__.py`, leaving
   old routing/endpoint behavior unchanged. No `capability_route.py` or
   `routing_audit.py` semantic change is planned.
4. Add `tests/test_document_task.py`; execute focused and full regressions
   only under the explicit isolated-destination gate.
5. Record actually performed results in a later M18 validation document and
   create/review an operator runbook before separately approved real E2E.
   Update DEV_STATUS/Runtime-State only at their authorized implementation
   documentation stage, distinguishing contract, code, validation and
   personal deployment. No such update belongs to this contract-only task.
6. Run one separately approved isolated actual-model HTTP flow; record
   outcome/quotes, restarts, calls, cleanup and omissions accurately.
7. Independent final review, explicit approval, then commit/push separately.

Expected implementation paths are migration 014, `noah/db.py`,
`noah/__main__.py`, new `noah/document_task.py`, new focused tests and later
M18 validation/runbook/status documentation. Any required production change
to existing M7/M8/M17 primitive semantics, ownership or accepted architecture
must be reported rather than hidden in a broad refactor.

Acceptance requires one persistent ready work definition, one explicit
confirmed execution claim, one same Task/Execution terminal result with
atomic verified Evidence, fresh-process inspection without model calls,
current authorization at all disclosure boundaries, deterministic
race/uncertainty/regression coverage, and separately reported isolated actual
HTTP success with exact baseline restoration. No validation is complete
until it has actually run. No personal deployment or universal recovery is
implied by this acceptance.

## Explicit exclusions and remaining review scope

Exclude general Task Planner, Agent loop, schedule/background execution,
multi-step/parent Task, multiple attempts, autonomous execution, model
task/target selection, Router integration, conversation persistence,
generic Context/Capability/Invocation framework, Artifact store, Shell,
external mutations/MCP, automatic retry/fallback/recovery, Memory changes,
Session ownership of Task, edit/cancel/delete/retention subsystem, new
Identity/Knowledge foundation, client idempotency or M4/M5 scope changes.

The approved choices of explicit run, bounded question persistence and no
in-flight recovery are fixed here. No unresolved architecture decision is
needed to begin implementation after review. Actual migration catalog
compatibility, isolation gates and claim/final-commit invariants must be
proved by implementation tests. If they cannot be satisfied, stop and
report the conflict; do not relax the contract or expand the slice.
