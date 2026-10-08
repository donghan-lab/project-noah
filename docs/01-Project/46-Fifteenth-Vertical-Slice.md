# M15 — Controlled Explicit Memory Suppression Routing (pre-implementation contract)

> Status: contract implemented and validated; deterministic automated verification, actual Ollama route-selection verification, and operator manual HTTP E2E completed on 2026-10-06. Results: [M15 validation](47-Fifteenth-Slice-Validation.md) and [manual HTTP E2E](48-Fifteenth-Slice-Manual-Validation.md). Final implementation and validation were committed and pushed to GitHub `main` at `301ab567da29f9654799625f0de159596f0c962a`. Baseline: M14 on `main` at `9566dc97e978c10cbe00e37bb96b2844256d5d20` (2026-10-06).
>
> Existing boundaries: [M11 routing](34-Eleventh-Vertical-Slice.md), [M12 routing audit](37-Twelfth-Vertical-Slice.md), [M13 explicit save routing](40-Thirteenth-Vertical-Slice.md), [M14 suppression](43-Fourteenth-Vertical-Slice.md), and [Runtime state](../02-Architecture/Runtime/State.md). Their validation histories remain unchanged.

## Why this direction follows M14

| Candidate | Existing primitive and smallest slice | User control and architecture risk | Relationship to later NOAH behavior |
| --- | --- | --- | --- |
| Controlled explicit suppression routing | Reuse M11–M13's bounded route/audit flow and call the existing M14 `suppress_memory()` once. Add one route to the bounded audit checks. | Caller names the exact Memory; model proposes only whether to use the capability. Mutation and permission remain in M14. The main risk is confusing routing/audit uncertainty with suppression outcome. | Tests a second controlled state-changing capability without inventing a general dispatcher or model-selected target. |
| Unsuppress/restore | Requires a new reverse transition and a decision about historical transition evidence, visibility races, and repeat behavior. | Affects the M14 one-way lifecycle contract; cannot reuse its mutation unchanged. | Useful after suppression, but a separate primitive and contract are needed first. |
| Project-scope Memory write | Requires a new write authorization target and membership/revocation rules across M1/M4/M5 and retrieval. | Broader authority and idempotency fingerprint implications than a bounded M14 delegate. | Expands collaboration rather than the current user-controlled lifecycle. |
| General lifecycle/orchestration | Introduces several operations and potentially shared execution abstractions. | Large authority, state, and recovery surface without a demonstrated need for a generic layer. | Defer until concrete operations require it. |

M15 is the smallest next end-to-end slice: **an authenticated user supplies one Memory ID, a local model proposes `memory.suppress` or `no_action`, NOAH validates that proposal, and only the existing M14 primitive can perform the transition.** A model never discovers, chooses, rewrites, or authorizes the target. This is a route connection, not a new suppression implementation.

## Exact request and preflight boundary

Extend the existing `POST /requests/route` with this exact JSON shape:

```json
{
  "question": "이 기억을 일반 조회에서 제외해 줘.",
  "memory_suppress": {"memory_id": "<caller-supplied UUID>"}
}
```

`question` follows the existing bounded M11/M13 question validation. The top-level object has exactly `question` and `memory_suppress`; the nested object has exactly one string `memory_id`, parseable as a UUID. NOAH may canonicalize that UUID for the internal call but must not derive a target from `question` or model output. Duplicate JSON keys, missing/extra fields, missing or malformed UUIDs, `project_id`, `memory_save`, scope/owner/force/content arguments, and both capability payloads together are rejected before audit reservation. Invalid target syntax uses M14's `INVALID_TARGET`; other invalid shape uses the existing routing `INVALID_REQUEST` style. The existing authentication and safe question screen precede the model. A failed preflight creates no routing audit, model call, delegate call, Memory mutation, Task, or Execution.

The M13 `Idempotency-Key` requirement applies **only** to `memory_save` requests. M15 suppression has no M4 key mapping; a supplied `Idempotency-Key` header is ignored for this branch, as it is for existing payload-free routes. Clients should omit it to avoid mistaking it for replay protection. Neither a router ID nor that header makes a suppression route request idempotent. Requests without `memory_suppress` retain the M11/M12 read-only schema and M13 explicit-save branch exactly as they are; a payload-free model proposal of `memory.suppress` is invalid and executes nothing.

### Target-check timing decision

Before routing, validate **only** credential, request shape, question, and UUID syntax. Do not look up the target row or perform a second router-level ownership/scope check. A read-only precheck would duplicate M14 policy, create a check-to-use gap, reveal target information on a request that the model might route to `no_action`, and still not replace M14's transactional revalidation. After a valid `memory.suppress` proposal and confirmed pre-delegate audit stages, M14 remains the authoritative existence, ownership, user-scope, token, and state check. Its foreign/nonexistent non-enumerating 404 and authorized project-scope 422 results pass through unchanged. A selected route rechecks that the original token still belongs to the same actor before `route_validated`, as M13 does; the M14 delegate then revalidates it in the state-changing transaction. No claim is made that a later concurrent revocation retroactively cancels a completed transition.

## Model proposal and data visibility

The suppression branch uses a strict one-field structured proposal:

```json
{
  "type": "object",
  "properties": {"route": {"type": "string", "enum": ["memory.suppress", "no_action"]}},
  "required": ["route"],
  "additionalProperties": false
}
```

This is a **request-shape-specific restriction only**: the two-choice schema applies when the request contains `memory_suppress`. It does not replace the payload-free M11/M12 choices (`memory.query`, `project.documents.answer.auto`, `no_action`) or the M13 `memory_save` choices (`memory.save`, `no_action`). The suppression schema permits exactly either string value and no additional keys or arguments. A proposal of `memory.query`, `memory.save`, `project.documents.answer.auto`, an unknown route, an ID, or any extra field is a routing-model output error **for this suppression branch**, never an alternate delegate or fallback. The model receives the bounded routing `question`, fixed descriptions of the two choices, and a fixed `memory_suppress_present=true` marker. NOAH does **not** add the structured `memory_id`, Memory content, credential, key/header, database data, or path to the prompt. The server does not read the target's content for routing. A caller can put an ID or other private text **inside their own `question`**; that text remains visible to the verified local model under the existing question contract. Therefore the guarantee is about what NOAH adds to the prompt, not about arbitrary caller-authored question text. Do not put the question or raw model response into routing audit.

`no_action` is a valid decision, not a target failure. It returns the existing HTTP 200 routing `no_action` envelope with one terminal audit row when its final update is confirmed; there is no target lookup, M14 call, Memory change, suppression Task/Execution, or M4 mapping. A failure of the final no-action audit update follows M12's routing-stage HTTP 503 contract and does not call the delegate. Suppression payload never permits the model to select another read or write capability.

## One delegate, result ownership, and disclosure

After token recheck and confirmed `route_validated` and `dispatch_prepared` audit commits, call `suppress_memory()` **once by internal Python call**, passing the caller-supplied UUID, M14's exact empty payload, and the original credential. Do not call its HTTP endpoint internally. The router creates no parent or duplicate Task/Execution and does not reproduce M14's UPDATE, verification, or permission SQL. `dispatch_prepared` records intent only; it proves neither that the Python call began nor that suppression succeeded.

M14 remains the source of truth for Memory state and its result. Preserve the M14 HTTP status and exact result inside the existing router `result` envelope, alongside the selected route and separate `router_id`/`routing.audit_status` fields:

| M14 delegate result | M15 behavior and durable ownership |
| --- | --- |
| First verified transition: HTTP 200, `status=succeeded`, `outcome=suppressed` | Persisted `suppressed_at` and **one** `memory.suppress` Task/Execution belong to M14. Router adds only its one audit row; it does not claim a new operation outcome. |
| Authorized repeat: HTTP 200, `status=succeeded`, `outcome=already_suppressed` | M14 returns a new delegate request ID, original timestamp, and null Task/Execution IDs. No new Memory mutation or M14 Task/Execution; router has a new audit row for this separate request. This is target-state idempotence, not M4 replay. |
| Missing/foreign target, unsupported authorized project scope, revoked token, or definite delegate failure | Preserve M14's safe HTTP/failure result. A selected route is not proof of permission or success. No invented Task/Execution relation. |
| `SUPPRESSION_OUTCOME_UNKNOWN` | Preserve M14's HTTP 503 and `outcome=unknown`; its `status=failed` envelope means confirmation failed, **not** proven suppression failure. Do not retry or infer state from an audit row. |

No automatic reroute, fallback, repeat suppression, M4 key reservation, or M5 repair is added. After an uncertain transport/commit result, the caller can explicitly use the authorized direct management lookup to inspect current Memory state, but an `already_suppressed` response cannot identify which earlier request caused the transition. A lost response must never trigger an automatic second router request.

## M12 routing audit and correlation

One eligible M15 router request gets one operational `noah.routing_audit` row with the existing monotonic stages `reserved → route_validated → dispatch_prepared → observed` where applicable. The audit is **not** a Task, Execution, DDR-004 Evidence, state-transition ledger, or suppression result source of truth. A model failure after durable reservation is an audit-bound routing failure with zero suppression delta; it is not an M14 failure. Reservation or pre-delegate update definite failure/unknown acknowledgement prohibits the delegate. A final `observed` update failure/unknown acknowledgement **after** the delegate returns preserves the obtained M14 result and sets only `routing.audit_status=unconfirmed`; `recorded` means the terminal audit commit was confirmed. Neither value asserts suppression success or failure. Keep audit uncertainty separate from `SUPPRESSION_OUTCOME_UNKNOWN`. There is no automatic retry at either boundary.

The current `008_routing_audit.sql` checks and M13's `009_memory_save_routing.sql` extension exclude `memory.suppress` from `validated_route`, `delegate_capability`, and dispatch-prepared routes. Implementation therefore needs **one minimal additive migration** extending only those three bounded CHECK constraints; existing rows and all other constraints retain their meaning. No new table, column, FK, target-ID field, Task status, or Evidence type is required. The migration is not written in this contract phase.

Only server-observed, validated IDs may be correlated. For the first verified transition, confirm that the returned `memory_id` equals the caller target and compare the returned M14 request/Task/Execution IDs with durable records, including actor, `memory.suppress` capability, Task relationship, Execution's target `memory_id`, and verified terminal state, before storing the request/Task/Execution IDs in audit. For `already_suppressed`, M14 has no Task/Execution: store at most the delegate request ID as an **in-process returned observation**, after validating its UUID and that the returned target matches the caller-supplied UUID; leave Task/Execution correlation null. That request ID is not backed by a durable Execution and must not be described as such. For pre-execution denial, definite failure, or `SUPPRESSION_OUTCOME_UNKNOWN`, correlate only independently verified durable IDs; do not invent a Task, Execution, or target relationship. A confirmed first transition or no-op uses the existing `delegate_returned` observation class; a returned `SUPPRESSION_OUTCOME_UNKNOWN` uses `delegate_uncertain` even when the audit itself is `recorded`. If returned IDs cannot be validated, omit them, use the existing `correlation_unverified` observation class where appropriate, and keep the original delegate result. M14 currently rolls back provisional Task/Execution on definite transaction failure and returns null durable IDs on commit uncertainty; this contract does not create a taskless failure Execution for M14.

Do **not** add `memory_id` to routing audit. A first transition can be traced indirectly through its verified M14 Execution's `memory_id`. An `already_suppressed` no-op has no Execution, so after a response is lost the durable audit alone cannot reconstruct the exact target. This is an explicit bounded-audit observability limit, not evidence that the target was absent or untouched. Stronger per-target lifecycle audit would require a separate need and contract. Audit stores no question, prompt, raw model JSON, Memory content, target ID column, Idempotency-Key or hash, token/token hash, password, generated answer, OS/local mapping path, or arbitrary payload.

## Failure and uncertainty matrix

| Boundary | Response/side-effect rule |
| --- | --- |
| Unauthenticated or malformed request, invalid question/UUID, conflicting payload, forbidden project/argument | Existing safe 401/400 preflight response. No model, audit, or delegate. |
| Dedicated Ollama unavailable/timeout or invalid proposal after reservation | Existing distinct M12 routing error and safe terminal audit observation when possible; no M14 delegate or Memory/Task/Execution change. |
| Valid `no_action` | Existing 200 no-action routing response; only one routing audit row if terminal update commits. |
| Reservation, `route_validated`, or `dispatch_prepared` commit definite failure/acknowledgement unknown | Report only last provable audit stage; **zero** delegate calls. Do not interpret preparation as execution. |
| M14 delegate returns a definite result, including first transition, repeat, or safe denial | Preserve its HTTP status/body; audit stores only permitted observation and verified correlation. |
| M14 delegate returns `SUPPRESSION_OUTCOME_UNKNOWN` | Preserve unknown outcome; no retry, fallback, or guessed failed state. Terminal audit may be recorded or unconfirmed independently. |
| Final audit update fails or acknowledgement is unknown after M14 returned | Preserve delegate HTTP status/body, set `routing.audit_status=unconfirmed`, and do not repeat M14. |
| Response is lost | A nonterminal audit or missing client-visible router ID cannot prove whether M14 began or committed. No automatic retry/recovery. |

`Unknown Outcome != Failed` applies to both suppression and audit confirmation. M5 Recovery Triage remains `memory.save` only and cannot classify or repair M15/M14 from the routing audit.

## Automated and actual-model validation contract

Use synthetic users and Memories while preserving the existing PostgreSQL baseline and named volume. Deterministic tests must cover:

- Authentication before any model exposure; strict/duplicate-key JSON and exact payload shape, UUID syntax, conflicting `memory_save`/`memory_suppress`, `project_id`, extra arguments, and no payload with a proposed `memory.suppress` all cause zero delegate work.
- A bounded prompt contains only the question, fixed route descriptions, and presence marker added by NOAH; it never adds the structured target UUID, target content, key/header, token, or DB data. Strict selected/no-action schema rejects foreign route, arbitrary arguments, malformed JSON, and extra fields.
- Exactly zero or one M14 internal call, with original credential and caller target; foreign/nonexistent targets use the same non-enumerating M14 404, authorized project scope uses M14 422, and a target-changing concurrent/credential revocation check is authoritative in M14.
- First suppression creates exactly one M14 Task/Execution and one routing audit, preserves original Memory content/history, and excludes the row from ordinary retrieval; `already_suppressed` adds only the audit row with no new Task/Execution/Memory mutation. No suppression M4 mapping and no router parent Task.
- Audit reservation, model, route validation, preparation, final update, and acknowledgement-unknown failures respect the zero-delegate/preparation boundary and preserve any already-returned delegate result. `SUPPRESSION_OUTCOME_UNKNOWN` and audit `unconfirmed` remain independent, without automatic retry or fallback.
- Verified first-transition correlation, no-op request-only observation, invalid-ID correlation omission, audit secret/payload minimization, and the response-loss target-observability limit. M5 stays `memory.save` only.
- Existing `memory.query`, document-auto, `memory.save`, and `no_action` routing and their Task/Execution/audit behavior remain unchanged, followed by full M1–M14 regression.

Separately opt in to actual local Ollama **route-selection quality** checks using public synthetic Korean and English questions for `memory.query`, `project.documents.answer.auto`, `memory.save`, `memory.suppress`, and `no_action`. Assert the proposed route under the appropriate payload branch; do not confuse correct selection with authorization or mutation success, and do not require five live HTTP mutations. Production and test selection settings should match. Deterministic tests remain the source for failure injection and provenance/side-effect counts.

## Operator manual HTTP E2E after implementation

With a synthetic user/token and one active user-scope synthetic Memory, capture the existing PostgreSQL counts/private fingerprints, named-volume identity, and local model boundary. Send **one** routed suppression request with an explicit Memory UUID; do not send a real personal Memory to the model. If the model selects `memory.suppress` and the M14 result is confirmed, verify the retained row and original content, persisted suppression timestamp, exactly one M14 Task/Execution, one safely correlated routing audit, normal retrieval exclusion, and direct management lookup. Verify the audit contains no prohibited text or target column. Stop on any unexpected or uncertain response; do not resend the router request. An actual-model repeat is not a manual requirement because it adds a fresh routing choice and is covered deterministically; M14's direct repeat was separately validated in M14. Clean up only test-owned rows after ownership checks and restore exact baseline counts/private fingerprints and volume identity. Do not inject audit/commit uncertainty into a real manual run.

## Explicit exclusions and architecture relationship

No restore/unsuppress, hard delete, edit, bulk or “forget all”, target discovery/search, model-selected ID, project-scope suppression/write, Memory content exposure to the router, generic Capability Registry, Invocation Kernel, parent orchestration Task, multi-step plan, multiple delegate calls, automatic retry/fallback/recovery, Agent loop, or Session/Knowledge persistence expansion is included. M14's one-way state transition, M4 save replay, M5 read-only save triage, M11/M12/M13 historical behavior, and DDR-001/002/004/006 boundaries remain in force. A bounded new route and CHECK extension do not require a new Accepted DDR. If implementation reveals a need for durable target audit or a new permission authority, stop and review that separately rather than silently enlarging M15.
