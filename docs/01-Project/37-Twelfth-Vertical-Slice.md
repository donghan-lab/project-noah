# M12 — Durable Read-Only Routing Audit and Correlation

> Status: **pre-implementation contract; not implemented or validated**.
> Baseline: M11 `main` commit `b3f7200f1226414f13b6202ca2bfc3ef6d1c1205`.
> Related: [M11 routing](34-Eleventh-Vertical-Slice.md),
> [Runtime state](../02-Architecture/Runtime/State.md),
> [DDR-001](../02-Architecture/Decisions/DDR-001-task-state-runtime-boundary.md),
> [DDR-002](../02-Architecture/Decisions/DDR-002-harness-boundary.md),
> [DDR-004](../02-Architecture/Decisions/DDR-004-artifact-architecture.md), and
> [DDR-006](../02-Architecture/Decisions/DDR-006-orchestration-contract.md).

## Goal and meaning

Persist one bounded operational account of an authenticated M11 routing
request. A server-generated router ID links NOAH's validated route decision
to the result it actually observes from **at most one** existing delegate.
This account is a routing audit, not a Task, Execution, Capability Evidence,
Artifact Store, semantic correctness proof, or recovery authorization.

M11 currently routes to M3 `query_memory()` (no durable Task/Execution), M10
`answer_auto_documents()` (its own one Task/Execution and M10 Evidence), or
`no_action` (no delegate). M12 preserves these distinct execution policies.
It does not claim that an M3 response became a durable execution or that a
model's choice, Memory claim, or document answer is semantically complete.

## Audit boundary and router identity

The router keeps its existing server-generated UUID `request_id`. On crossing
the audit boundary, this UUID becomes the immutable `router_id`; it is never a
Task ID or Execution ID. The UUID may be generated at request entry as it is
in M11, but **durable audit responsibility starts only after** token
authentication, request/question validation, known-credential and routing
prompt checks, and (when supplied) project UUID parsing and current read
membership precheck all succeed. The supplied project ID comes only from the
caller; the model cannot create or alter it. A separate, committed audit
reservation occurs **before the routing model call**. The model and delegates are not
called if reservation is definitely unsuccessful or its commit outcome is
uncertain.

Unauthenticated, malformed, invalid-project, and unreadable-project requests
retain M11's safe preflight behavior and create no routing audit row. The
operator must not infer that the absence of a row proves that no HTTP request
arrived. An unauthorized project's identity or question text is not exposed
through the audit. The existing M11 precheck does not replace M3/M10's own
authorization or M3's final disclosure check.

For a confirmed reservation, the response includes a top-level `router_id`
on `no_action`, routing-model failure, pre-delegate rejection, and delegated
success/failure. A reservation commit with an unknown acknowledgement may
return that UUID with `routing.audit_status=unconfirmed`; it is **not** proof
that the row exists. Definite pre-reservation failures retain the existing
response `request_id` and omit `router_id`. If the HTTP response itself is
lost, a client that never received the server ID cannot automatically link
its next request to this one: M12 has no client-supplied correlation ID or
idempotency key.

## Smallest stored model

Use **one mutable operational audit row per eligible router request**, not
an append-only event stream or a generic execution framework. Short database
transactions reserve and advance that row monotonically. There is no open
transaction across an Ollama call or an M3/M10 delegate call. The audit is
not DDR-004 Capability Evidence and does not replace existing append-only
document Evidence. No application delete path or automatic TTL is part of
M12; long-term retention and privacy policy need a later decision.

Proposed audit stages and permitted transitions:

| Stage | What a committed row establishes | Permitted next stage |
| --- | --- | --- |
| `reserved` | Eligible authenticated request reached the pre-model boundary. | `route_validated` or `observed` for definite routing failure. |
| `route_validated` | NOAH accepted one exact allowlisted model choice. Argument checks may still reject delegation. | `dispatch_prepared` or `observed` for `no_action` / pre-delegate rejection. |
| `dispatch_prepared` | NOAH committed its intent to call one delegate. It **does not prove that the call started or finished**. | `observed` after a result is actually available. |
| `observed` | NOAH durably recorded only the routing/result observation it could verify. | Terminal for this router request. |

The row must not advance backward. Age, process exit, a missing terminal
update, or a `dispatch_prepared` row does not establish failure, successful
execution, or permission to retry. `observed` is not automatically
`succeeded`: its separate observation class distinguishes `no_action`, a
definite routing failure, an argument rejection, a returned delegate result,
an uncertain delegated result, and a final disclosure denial. A returned
delegate failure keeps its safe failure code and HTTP status. This is a new
audit-stage vocabulary only; M1–M11 Task, Execution, and verification status
values do not change.

The minimum stored information is `router_id`, authenticated `actor_user_id`,
creation/update and final-observation times, audit stage, validated route (or
null before selection), an indication of whether dispatch was prepared and a
delegate result was actually observed, the chosen delegate capability,
nullable delegate `request_id`/Task ID/Execution ID, and bounded safe
observation class, HTTP status, outcome or failure code. An optional
caller-supplied project UUID may be retained only when needed to verify the
authorized document route; it must not become a project existence oracle.
No question fingerprint is needed for this slice.

The audit **must not store** question or prompt text, raw model JSON, API
token or token hash, DB credential, Memory/document body or full quote,
absolute OS path, local root mapping, or generated answer. Audit access is
operator-only through read-only DB verification in M12; there is no public
audit-browsing HTTP endpoint. A UUID field is a correlation reference, not
an assertion that a referenced execution succeeded.

The M3 delegate `request_id` is response-scoped, not a database entity and
cannot have an FK. M10's existing execution and Task IDs can be checked
against returned data and storage when available, but M12 need not impose a
new hard FK that couples audit retention to their deletion. In particular,
do not add a strong project FK merely to block future project deletion.
Application validation and focused tests must detect impossible or swapped
IDs; the M10 Task/Execution/Evidence records remain the canonical durable
execution truth. Exact column types and constraints belong to the additive
migration implementation, not this contract.

## One-request sequence

1. Preserve M11 authentication, input bounds, optional project precheck,
   credential screening, and local-only model restrictions.
2. Commit the `reserved` audit row before any routing model call. A definite
   or uncertain reservation failure stops before the model and delegate.
3. Ask the local model for M11's unchanged strict three-choice proposal.
   NOAH validates the schema and allowlist. A definite model failure may be
   recorded as `observed` with no delegate.
4. Persist `route_validated` before acting on it. For `no_action`, persist a
   terminal routing observation and return HTTP 200 with no Capability
   execution. For an incompatible caller argument, persist the safe rejection
   and invoke no delegate.
5. Commit `dispatch_prepared` immediately before the one permitted internal
   function call. Recheck existing permissions as M11/M3/M10 require. This
   stage indicates **possible**, not proven, delegate invocation if the
   process subsequently disappears.
6. Observe the delegate's result. Store only safe correlation IDs and result
   class. Apply M11's Memory final-disclosure check before recording the
   public result and disclosing Memory excerpts. A disclosure denial must not
   be logged as a successful public Memory answer.
7. Commit the final `observed` audit update separately, then return the
   existing M11 envelope plus the router correlation fields. Do not rewrite
   the M3/M10 `result` body, its HTTP status, or its own Evidence.

At no point may M12 call both delegates, call either delegate by HTTP, create
a parent Task, or hold the audit transaction over model/tool execution.

## Branch-specific relationships

| Validated choice | Router audit | Delegate relationship | Capability records |
| --- | --- | --- | --- |
| `memory.query` | Route, observed M3 response class and `request_id`. | Exactly one `query_memory()` call; M3's own result and final M11 disclosure check stay authoritative. | No new M3 Task/Execution; Memory quotes remain in the existing response, not audit storage. |
| `project.documents.answer.auto` | Route, observed M10 `request_id` and nullable returned Task/Execution IDs. | Exactly one `answer_auto_documents()` call using the caller's authorized `project_id`. | Only M10 owns its one Task/Execution and candidate/source/quote Evidence. |
| `no_action` | Terminal routing decision with no selected Capability and no delegate IDs. | None. | No Task, Execution, or Capability Evidence. The **routing audit row** is the only new durable metadata. |

M11's earlier “no durable route audit” and manual `no_action` database delta
of zero describe **M11 at its validation time**. M12 intentionally changes
only routing metadata: after implementation `no_action` may have one audit
row while still having zero Capability executions and zero Task/Execution/
Evidence rows. HTTP 200 means the routing decision completed, not that a
Capability succeeded.

## Response and failure contract

Keep `POST /requests/route`, its `status`/`routing`/`result` envelope, and
the delegated M3/M10 result body. Add only top-level `router_id` where the
audit boundary was crossed and `routing.audit_status` on responses carrying
that ID. `recorded` means the response's terminal `observed` audit update
has a confirmed durable commit; it says nothing about whether a delegate
succeeded, whether `no_action` ran a Capability, or whether an answer is
semantically correct. `unconfirmed` means that terminal audit observation
cannot be confirmed (including a definite update failure or lost commit
acknowledgement); it does **not** mean that a delegate failed or that its
durable result was rolled back. The existing
`request_id` on early errors remains a request diagnostic ID; it is not
evidence of an audit row. No new free-form answer is generated by the router.

| Boundary/failure | Required behavior |
| --- | --- |
| Before reservation: authentication, input, project, or prerequisite DB failure | Keep M11's safe status/code and non-enumerating project response. No audit/model/delegate. |
| Definite reservation failure | Safe 503 `ROUTING_AUDIT_UNAVAILABLE`; no model or delegate. Do not claim an audit row. |
| Reservation commit acknowledgement unknown | Safe 503 `ROUTING_AUDIT_OUTCOME_UNKNOWN` with unconfirmed router ID; no model or delegate, no automatic retry. |
| Routing model unavailable, timeout, malformed JSON, unknown route, or extra field | Retain M11's distinct model error where the audit can be finalized; zero delegate. If audit finalization is uncertain, report that uncertainty separately. |
| Route/argument audit update fails before delegation | No delegate. A known failure uses `ROUTING_AUDIT_UNAVAILABLE`; an unknown acknowledgement uses `ROUTING_AUDIT_OUTCOME_UNKNOWN`. Preserve whichever prior audit stage is provable. |
| `no_action` was durably `route_validated`, but its terminal `observed` update definitely fails | Return HTTP 503 `ROUTING_AUDIT_UNAVAILABLE`, top-level `status=failed`, `router_id`, `routing.outcome=failed`, `routing.stage=routing`, `routing.audit_status=unconfirmed`, and `result=null`. The last provable durable stage is `route_validated`; do not return the normal HTTP 200 `no_action` completion. Delegate/Task/Execution/Capability Evidence counts remain zero; no retry or fallback. |
| `no_action` was durably `route_validated`, but its terminal `observed` commit acknowledgement is lost | Return HTTP 503 `ROUTING_AUDIT_OUTCOME_UNKNOWN` with the same failed routing envelope, `router_id`, `routing.audit_status=unconfirmed`, and `result=null`. `route_validated` is the last **provable** durable stage; `observed` may or may not have committed. Delegate/Task/Execution/Capability Evidence counts remain zero; no retry or fallback. |
| `dispatch_prepared` commit acknowledgement unknown | Do **not** call the delegate; a committed marker, if any, proves only preparation. Return the safe audit-outcome-unknown result. |
| Returned M3 failure, definite M10 failure, or M10 `TOOL_OUTCOME_UNKNOWN` | Preserve the delegate HTTP status, safe code, IDs, and uncertainty. No fallback or retry. An audit observation is not a second execution result. |
| M3 returned evidence but the final token/visibility check denies disclosure | Return M11's existing safe disclosure failure, not the held M3 content. Record the public denial class separately from the delegate observation. |
| Delegate result returned but final audit update fails or its commit acknowledgement is unknown | Preserve the already approved public result and HTTP status, or the M11 safe disclosure denial when access was lost; add `routing.audit_status=unconfirmed` if a response can be sent. Never rewrite committed M10 Task/Execution/Evidence or label that work failed because the audit failed. |
| HTTP response lost | The row may show what NOAH durably observed, but absence of a final observation is not proof of failure. A client without the router ID cannot automatically correlate a replay. |

Audit DB connection loss is not evidence that its reservation or update did
not commit. Do not recreate an audit row under a new ID, automatically call a
delegate, or reuse M4 `memory.save` idempotency. M5 Recovery Triage remains
`memory.save`-only and does not inspect or recover M12 or M10. There is no
automatic state repair for incomplete audit rows.

## Implementation and validation boundary

A small additive, separate routing-audit table is expected. It preserves all
existing data and does not alter `noah.tasks`, `noah.execution_records`, M3,
or M10 Evidence semantics. This document defines column meanings and stage
invariants, **not SQL**. The likely implementation changes are the router
module, additive migration registration, a focused M12 test module, the M12
validation/operator documents, Runtime state, and development status. The
existing HTTP entry point need not change unless the minimal response
envelope requires it. No new package, generic Registry, or public audit API
is justified.

Automated tests must prove: preflight failures create zero audit/model/
delegate calls; one distinct router ID per eligible request; one M3 call and
linked M3 request ID with zero Task/Execution delta; one M10 call and linked
existing request/Task/Execution IDs without duplicates; `no_action` produces
one audit row and no delegate/Task/Execution/Evidence; model failures have
zero delegation and the agreed audit stage; audit reservation, pre-delegate
update, post-delegate update, and uncertain commit failures preserve the
boundaries above. Scan stored rows for secrets, bodies, quotes, paths, and
prompts. Run the full M1–M11 regression. Use separate synthetic users,
projects, and documents; clean up only test-owned data and compare original
DB row counts/fingerprints.
Existing M11 `no_action` assertions about zero Task/Execution/Evidence remain
valid; any synthetic fixture cleanup or whole-DB snapshot assertion must be
updated to account for, and remove only, the new M12 audit rows. Historical
M11 zero-delta manual observations must not be rewritten as M12 results.

An opt-in actual Ollama/manual HTTP E2E should use public synthetic data for
one `memory.query`, one `project.documents.answer.auto`, and one `no_action`
request. Verify the router ID and durable correlation separately from model
selection quality; M3 still has no Task/Execution, M10 still has exactly its
one pair, and `no_action` has only the new routing audit metadata. Preserve
existing user data and the PostgreSQL named volume, and verify exact baseline
restoration after targeted cleanup.

M12 is complete only after the bounded audit/ID linkage, failure and unknown
outcome behavior, secret minimization, prior regression, real synthetic HTTP
verification, and cleanup have all been demonstrated. Completion does **not**
mean multi-step orchestration, general tracing, M3 execution persistence, or
automatic recovery is complete.

## Implementation details still to settle

The migration must choose exact column types, allowed-value constraints, and
indexes for the bounded stages above. The implementation must also specify
how an operator verifies an audit row without adding a public HTTP endpoint.
Those choices may not broaden stored content, introduce a parent Task, or
weaken the failure/uncertainty contract. Longer-term retention and privacy
governance are deferred; M12 has no automatic deletion policy.

## Explicit exclusions

No Memory+Document combined run, multi-step plan, parent Task, M3 durable
Task/Execution, common Invocation Kernel, generic Capability Registry,
Session/Context/Knowledge persistence, Artifact framework, Agent loop,
write-capability routing, retry/fallback, client idempotency, client-provided
correlation ID, public audit browsing API, automatic recovery, or M13 work.
