# M14 — Controlled Memory Suppression (pre-implementation contract)

> Status: implemented and automatically validated on Compose PostgreSQL 17;
> **separate operator manual HTTP E2E remains pending**. Baseline: M13 on
> `main` at `083b3cb26576796a4edec7aa40d21d5e2c32adc9` (2026-10-03).
> This document narrows the existing [Memory Blueprint](../02-Architecture/Information/Memory.md)
> and Accepted DDR-001–006 for one user-controlled operation. It does not change
> the Blueprint, DDRs, or the historical M1–M13 validation results.

## Goal and boundary

An authenticated user explicitly names **one** Memory ID that belongs to that
user and has `scope=user`. NOAH makes that Memory unavailable to ordinary
retrieval while retaining its row, content, original provenance, creation
metadata, M1/M4 history, and references. Suppression is neither deletion nor a
change to the Memory content. It does not modify unrelated Task State,
Knowledge, Artifact, or protected Identity as a side effect; the M14 operation
has only its own Task/Execution records as specified below.

No model is involved. M14 does not use `POST /requests/route`, create a routing
audit, infer a target from a question, or authorize a project-scope Memory.

## Existing implementation and persistence

The current `noah.memories` table has `id`, `scope`, owner/project references,
`content`, `provenance`, `created_by`, and `created_at`, but no lifecycle state.
M1 saves a new row; M2 listing and M3 word search share the SQL visibility
predicate in `noah/service.py`. `GET /memories/<id>` performs a separate
authorized direct lookup. M11's Memory result disclosure also uses the shared
predicate. M4's write-key mapping and M5's read-only triage refer to existing
Memory rows, not to whether those rows are eligible for future retrieval.

The proposed additive migration adds **only** nullable
`noah.memories.suppressed_at timestamptz DEFAULT NULL` for this lifecycle
state. `NULL` means active; a non-null timestamp means suppressed. Existing rows
remain active without backfill. New M1/M13 saves default to active. M14 changes
only this field on its target. It does not repurpose `provenance`, change any
existing ID, add a general status enum, or delete a referenced row. A future
restore or hard-delete feature must separately define how historical
transitions remain traceable; M14 never clears `suppressed_at`.

## HTTP request and authorization

The proposed deterministic endpoint is `POST /memories/<memory_id>/suppress`
with an existing bearer token and an exact empty JSON object `{}`. No content,
reason, project ID, actor ID, model proposal, or optional operation argument is
accepted. The path segment must be a UUID. Request shape and token are checked
before any mutation. The authenticated actor must be the target row's actual
`owner_user_id` and the row must have `scope=user`. A project membership is
never suppression permission.

Malformed IDs or JSON/body shape return a structured 400. A missing or revoked bearer
token returns structured 401 `UNAUTHENTICATED`. An absent or inaccessible
Memory returns the same non-enumerating 404 `MEMORY_NOT_FOUND`, including a
different user's private Memory. A caller who is already authorized to read a
project-scope Memory receives 422 `UNSUPPORTED_SCOPE`; an unauthorized caller
still receives 404. All of these are pre-execution rejections: no Memory,
Task, or Execution change. Initial authentication alone does not authorize
the mutation. Inside the state-changing transaction, immediately before the
mutation, NOAH revalidates that the **same credential used for this request**
still exists, is not revoked, and is still bound to the initially authenticated
user. It then rechecks target existence, `scope=user`, and owner equality while
locking the row. A token revocation committed before this transactional
credential-revalidation statement prevents the mutation. A revocation that
concurrently commits later is resolved by database statement/transaction
ordering; M14 does not promise that a revocation occurring after the check
retroactively cancels a committed suppression. Rechecking owner/scope never
substitutes for rechecking the credential. No LLM or Router permission is
relevant.

## State transition and repeat request

M14 supports `active → suppressed` only. The transition is a conditional,
owner-bound update under a row lock. Concurrent callers cannot both perform
the transition. On a first verified transition the exact success envelope is
HTTP 200 with top-level `status="succeeded"`, `outcome="suppressed"`, a new
server-generated `request_id`, `memory_id`, the persisted ISO 8601
`suppressed_at`, and the newly committed M14 `task_id` and `execution_id`
(both non-null). The response does not repeat the Memory content.

An authorized repeat finds the existing non-null `suppressed_at` and returns
HTTP 200 with top-level `status="succeeded"`, `outcome="already_suppressed"`,
a **new** server-generated `request_id` for this HTTP request, the same
`memory_id` and unchanged persisted ISO 8601 `suppressed_at`, and explicit
`task_id=null` and `execution_id=null`. It creates no second transition or
Task/Execution and does not replay the first Execution or its request ID. This
is **target-state idempotence**, not M4 key-based request replay: the response
cannot prove which earlier request suppressed the row.
M14 needs no `Idempotency-Key`, does not use the M4 mapping, and does not
automatically retry after an uncertain response. A different user still gets
404 even when the row is suppressed.

## Management lookup versus ordinary retrieval

An authorized `GET /memories/<id>` is a **management lookup**. It continues to
return both active and suppressed rows to their existing authorized readers,
including the owner of a suppressed user Memory. **Every Memory response
object**, whether a direct lookup object or a `GET /memories` list item, adds
`suppressed` (boolean) and `suppressed_at` (persisted ISO 8601 timestamp or
null). Active rows have `suppressed=false` and `suppressed_at=null`; an owner
direct lookup of a suppressed row has `suppressed=true` and its actual persisted
timestamp. Existing Memory fields remain unchanged. This is an additive
extension of M2's common single-object/list-item field contract, not a new
list shape. Do not turn a suppressed, authorized row into a false 404. Existing
access checks remain in force. The direct lookup may still return the retained
content to its owner; suppression limits ordinary use, not the owner's
inspection.

`GET /memories` and the SQL word search underlying `POST /memories/query`
exclude rows with non-null `suppressed_at` **in the SQL visibility predicate
before cursor filtering, ordering, LIMIT/pagination, snippets, or any model
context**. This includes user and project scopes even though M14 can suppress
only user rows. The shared ordinary-retrieval
predicate must enforce both existing ownership/membership and active state.
There is no `include_suppressed` option on list/search/query in M14.

M3 must retain the IDs of **every Memory snippet actually included in the
local model input** in ephemeral per-request execution context, including
snippets that the model does not cite. This does not create durable audit or
Evidence and does not copy Memory content. After model generation, immediately
before disclosing a direct M3 result to the user, NOAH revalidates the caller's
token and, for **all** those IDs, caller authorization, ownership/current
visibility under the existing user/project policy, and `suppressed_at IS NULL`
against the database. Checking only cited IDs is insufficient. If any used
Memory is no longer visible, NOAH returns deterministic HTTP 409
`MEMORY_CONTEXT_STALE` as a structured verification failure and withholds the
**entire** generated answer, all quotes/evidence, and search-result metadata;
it does not retry the model or store the rejected raw answer in a new audit.
If this final check cannot be completed because the database is unavailable,
return a structured 503 without disclosing those results.

The same full used-ID set must remain available ephemerally through an M11
routed `memory.query`. Even if M3's internal final check passed, M11's **last
public HTTP disclosure boundary** must recheck the token and every Memory
actually sent to the model, because suppression may have committed in between.
It applies the same whole-result withholding rule. No Memory content is copied
to the M12 audit, and no parent Task, retry, or fallback is added. Sending
content to a local model before suppression commits cannot be undone; this
contract prevents later **user disclosure of a result influenced by newly
invisible content when the final check observes that change**, not retroactive
removal of model input or an impossible lock on subsequent revocations.

Ordinary GET/list reads have a narrower observation guarantee. An in-flight
GET/list may read an active row before suppression commits and deliver that
already observed result afterward. A new relevant database query begun after
the suppression commit excludes the row from normal retrieval. Owner direct
lookup reports active or suppressed according to the database state its query
observes. M14 does not claim a final-disclosure or linearizability guarantee
for ordinary GET/list comparable to the stronger M3/model-result gate.

## Task, Execution, verification, and commit

Unlike M2/M3 reads, suppression changes durable Memory state. An actual
`active → suppressed` transition therefore has **one** M14 Task and **one**
Execution Record using the existing stored states and a distinct
`memory.suppress` capability/goal. The Task and Execution are not M1 save
records or M12 routing audits. No parent Task, new Task/Execution status, or
DDR-004 Artifact/Evidence table is required. The Execution links the target
`memory_id` and records `verified_at`; it does not copy Memory content.

In one short PostgreSQL transaction, after the credential revalidation and
row-level ownership/scope confirmation above, NOAH locks the row, checks it is
active, creates the M14 Task/Execution, conditionally sets `suppressed_at`, and **reselects**
the same row. It verifies the ID, owner, scope, non-null timestamp, and that
content, provenance, and original creation metadata were not changed. Only
then may it set Task `completed/passed` and Execution `succeeded` with
`memory_id`/`verified_at` and commit them together with suppression. Mere
UPDATE row count is insufficient. The committed row plus matching terminal
Task/Execution is the success evidence. A normal crash before this commit
rolls back all three changes; unlike M1's two-transaction reservation, this
short DB-only operation does not intentionally persist an intermediate
`running` Task. A lost commit acknowledgement is still uncertain.

An already suppressed request performs no transition and creates no Task or
Execution. M5 remains scoped to `memory.save`; it must not classify or repair
M14 records. M12/M13 routing audit does not own or observe this endpoint.

## Failure and unknown outcome

| Situation | Contract |
| --- | --- |
| Invalid ID / invalid JSON or body shape | HTTP 400 `INVALID_TARGET` / `INVALID_REQUEST`, respectively; category `Invalid Input`. No M14 Task/Execution. |
| Missing/revoked token, foreign/absent target, unsupported scope for an authorized reader | Respectively HTTP 401 `UNAUTHENTICATED` / 404 `MEMORY_NOT_FOUND` (category `Permission Denied`), or HTTP 422 `UNSUPPORTED_SCOPE` (category `Invalid Input`). No M14 Task/Execution. Foreign/absent targets share the 404 without revealing content or scope. |
| Definite UPDATE error or failed database readback before commit | Roll back the entire transition, including provisional Task/Execution; HTTP 500 `SUPPRESSION_FAILED` (category `Environment Failure`) or `VERIFICATION_FAILED` (category `Verification Failure`), respectively. No partially committed suppressed row. |
| Database unavailable before a transaction begins, or a pre-commit error with provable rollback | HTTP 503 `DATABASE_UNAVAILABLE`, category `Environment Failure`; do not claim the Memory is missing or suppressed. |
| Commit acknowledgement lost or connection failure where commit cannot be ruled out | HTTP 503 `SUPPRESSION_OUTCOME_UNKNOWN`, category `Environment Failure`; do **not** mark the Task failed, assert that the update was rolled back, or automatically repeat the operation. A durable terminal Task/Execution may or may not exist. |
| Response lost after confirmed commit | The database remains source of truth. A later explicit owner management lookup can inspect the current suppressed state; a repeat suppression is safe but cannot identify the originating request. |

Failures use NOAH's existing structured envelope: top-level `status="failed"`,
a new server-generated `request_id`, `task_id=null`, `execution_id=null`, and
`failure` with `code`, `category`, `message`, `recoverable`, and
`retryable=false`. A preflight or definite failure does not include the
target's Memory content or a `memory_id`/`suppressed_at` claim. For commit
uncertainty, add top-level `outcome="unknown"` to that same envelope; provisional
Task/Execution IDs are **not** returned as durable IDs because their commit is
unconfirmed. `status="failed"` and HTTP 503 mean **request confirmation
failed**, not that suppression definitely failed. The caller must not infer
success or failure from the audit, automatically retry, or fall back; a later
explicit owner management lookup may inspect the current row state. A safe,
credential-free local diagnostic may correlate by `request_id` without Memory
content or a guessed final outcome. Timestamp age does not resolve
uncertainty. This contract adds no automatic retry, fallback, recovery, or M5
repair for suppression.

## Compatibility and security

- M1/M13 continue to create active Memory with unchanged content, scope, and
  original provenance. M4 replay of a previously successful save remains a
  historical save replay with the original IDs even if that Memory was later
  suppressed; it must **not** clear `suppressed_at` or create another Memory.
- M5 must still find the preserved Memory row when checking an old
  `memory.save` Execution. Suppression is not evidence that the save failed.
- M2 pagination and M3 search use the active SQL predicate; suppression between
  pages may change what a later page sees, as M2 already permits changing
  visibility. M3 direct and M11 routed final disclosure revalidate the full
  model-input Memory set, not only citations.
- M10 document answering, M11/M12 read-only routing, M13 explicit routed save,
  and their existing Task/Execution/Evidence/audit ownership do not change.
  M14 is not a Router candidate.
- Do not store token, password, raw request, Memory content, or content hash in
  new audit/log data. The retained original `noah.memories.content` and M1/M4
  records remain under their existing access and retention rules. The M14
  response contains only bounded state metadata and IDs, never the body.

## Implementation validation contract

Use isolated synthetic users, user/project Memories, and preserved Compose
PostgreSQL data. Verify: additive migration and existing rows active; new save
active; owner transition and post-update readback; retained content/provenance
and old IDs; direct owner lookup with state; list/search/M3/M11 exclusion;
foreign owner and project-scope denial; missing/invalid input; no model call;
concurrent and repeated suppression with one transition/Task/Execution;
transactional token revalidation and a revocation committed before that check;
the same additive state fields on active list items and direct lookup objects;
verified terminal IDs; rollback on update and verification failure; unknown
commit outcome without guessed failure or automatic retry; M4 replay after
suppression without unsuppressing; M5 triage of original save unchanged; and
M1–M13 regression. Exercise suppression of an **uncited but model-sent**
Memory racing with both direct M3 and M11 routed answer disclosure: neither
the answer nor quotes/search metadata may be returned after the final
full-context visibility check denies it. Also cover a GET/list read observed
before commit but delivered afterward without treating it as an M3 guarantee.

For a later **separate** manual E2E, use a synthetic owner and Memory, one
explicit suppress request, owner direct lookup, ordinary list/query absence,
read-only DB verification of the retained row and one M14 Task/Execution, then
targeted cleanup of only synthetic records. Verify baseline row counts and
private fingerprints before/after. Do not suppress a real personal Memory,
delete an existing row, inject unknown outcomes into the live DB, or clear a
Docker volume. The implementation and automated HTTP/Compose tests are
recorded in [M14 validation](44-Fourteenth-Slice-Validation.md). Separate
operator manual HTTP E2E and its results are still pending.

## Explicit exclusions and architecture relationship

No LLM-selected target, Router connection, project-scope suppression,
model-derived payload, editing, restoring, deleting, hard deletion, automatic
Memory management, generic registry, invocation kernel, parent Task, agent
loop, multi-step orchestration, or new retry/fallback/recovery is included.
DDR-003 and the Memory Blueprint already distinguish retrieval suppression
from deletion. DDR-001/006 support a durable verified Task/Execution for a
state-changing operation, and DDR-002/005 keep authorization outside a model
and Memory distinct from protected Identity. DDR-004 does not require a new
Artifact Store for this one timestamp transition. No Accepted DDR change is
required for the bounded M14 contract.
