# M11 — Controlled Read-Only Capability Routing (pre-implementation contract)

> Status: **contract only; M11 is not implemented or validated**.
> Baseline: M10 `main` commit `12c28b4b9dca3a084f7a976b86f251ae7d3020e1`.
> Architecture: [Runtime state](../02-Architecture/Runtime/State.md),
> [DDR-001](../02-Architecture/Decisions/DDR-001-task-state-runtime-boundary.md),
> [DDR-002](../02-Architecture/Decisions/DDR-002-harness-boundary.md), and
> [DDR-006](../02-Architecture/Decisions/DDR-006-orchestration-contract.md).

## Goal and implemented starting point

One authenticated natural-language request may select **one** of two existing
read-only internal functions, or select no action. NOAH validates the model's
proposal and invokes the chosen function under its existing authorization,
execution, and result-verification contract. This is a small routing boundary,
not a generic Agent, Registry, Dispatcher, or Invocation Kernel.

The implemented M3 `query_memory(payload, token, ...)` handles
`POST /memories/query`; it authenticates before its own model call, searches
only memories readable by the current actor, and validates returned memory IDs
and exact quotes. It creates **no durable Task or Execution**. The implemented
M10 `answer_auto_documents(project_id, payload, token, ...)` handles
`POST /projects/<project_id>/documents/answer-auto`; it rechecks membership,
uses internal listing, safe-read, and grounding primitives, and owns **one**
durable Task/Execution and its M10 Evidence. The current HTTP entry point uses
explicit branches; there is no implemented common capability registry.

## Request and proposal

Proposed new API: `POST /requests/route` with a bearer token and exactly these
JSON fields:

```json
{"question":"..."}
```

For a document-capable request, the caller may additionally supply its own
`"project_id":"<UUID>"`; the model never fills this field.

`question` is required; `project_id` may be omitted. Unknown fields, duplicate
JSON keys, invalid types, and malformed JSON are invalid requests. Before any
model call, NOAH applies the shared input bound of **1–300 Unicode characters
after trimming and at most 512 UTF-8 bytes**, rejects forbidden control
characters, and rejects a question containing the known API token or DB
password. This bound fits both existing delegates; it narrows only the new M11
route, not either existing endpoint. The implementation must bound the routing
prompt and model output without truncating the question.

After authentication and input validation, a supplied `project_id` must parse
as a UUID and have current read membership. A nonexistent or unreadable project
returns the same non-enumerating `PROJECT_NOT_FOUND` response **before the
routing model is called**. The model receives the question and a fixed,
operator-defined description of the three choices only. It receives no
project ID or name, candidate filenames, OS path, credential, DB data, memory
body, or document body. Its proposal cannot create or alter a project ID.

The complete routing model JSON schema is:

```json
{
  "type": "object",
  "properties": {
    "route": {
      "type": "string",
      "enum": ["memory.query", "project.documents.answer.auto", "no_action"]
    }
  },
  "required": ["route"],
  "additionalProperties": false
}
```

`memory.query` is a **new M11 routing allowlist identifier** for the existing
M3 `query_memory()` function. M3 currently has no persisted Capability ID or
Task/Execution row; this document does not claim that `memory.query` already
exists in storage. `project.documents.answer.auto` is M10's existing
Capability ID. `no_action` is a routing result, **not** a Capability. The model
proposes no arguments; a field such as `arguments`, `project_id`, `path`, `sql`,
or `tool` makes its output invalid. NOAH passes only the validated original
question and, for M10, the original user-supplied project ID.

The routing instruction must choose `no_action` for an unsupported, ambiguous,
write-oriented, or insufficiently identifiable capability request rather than
guessing. A route to Memory is not proof that a memory exists; a route to
Documents is not proof that a filename or answer exists. Routing is a bounded
selection decision, not semantic verification of the eventual result.

## Dispatch and permission boundary

| Validated route | Argument rule | Single internal call |
| --- | --- | --- |
| `memory.query` | `project_id` **must be absent**. M3 has no exact project-ID filter; silently ignoring a supplied ID could search a wider scope than requested. | `query_memory({"question": question}, token)` |
| `project.documents.answer.auto` | A user-supplied, validated, currently readable `project_id` is required. If absent, return `PROJECT_ID_REQUIRED` without delegation. | `answer_auto_documents(project_id, {"question": question}, token)` |
| `no_action` | No delegate is invoked, irrespective of whether a readable project ID was supplied. | None |

A valid project ID on a Memory route yields `INVALID_ROUTE_ARGUMENT` without
calling M3. This is a new-route restriction; existing `POST /memories/query`
continues to support its own `user`/`project`/`all` scope policy. M3's model
still proposes scope and literal search terms only under its own validator.
M10 still verifies its project membership, operator mapping, filename
selection, safe-read observations, quotes, and final disclosure. M11 must call
the **internal Python functions**, not their HTTP endpoints, and must not
construct a second M10 Task, Execution, or Evidence set.

The M11 precheck does not replace delegated checks. Authentication must occur
before routing-model exposure. The provided project ID must be checked before
the model call and again by M10 before selection, reading, final commit, and
disclosure. For M3, its search-time token and memory-visibility filter remain
authoritative. The M11 response boundary must also recheck the token and each
referenced Memory Evidence ID immediately before disclosing Memory excerpts;
if access was revoked during a model call, withhold the result. A final
pre-disclosure denial does not rewrite any already committed M10 result.
Content already sent to the verified local model cannot be withdrawn after a
later permission revocation; this temporal limit does not permit subsequent
disclosure to the caller.
Credential checks and local-only Ollama binding must apply before transmitting
the routing question. The model never receives execution authority.

## Task, Execution, Evidence, and response

M11 creates **no parent Task or Execution** and no new Evidence table. One
request invokes zero or one delegated capability. A selected M3 request keeps
M3's response `request_id` and in-response verified memory quotes, with no
durable Task/Execution. A selected M10 request keeps exactly its own
Task/Execution pair and M10 candidate/source/quote Evidence, including the
normal `no_document_selected` or valid grounded/quote-free outcomes. M11 does
not turn these into new routing Evidence. Pre-delegation rejection and
`no_action` create no Task/Execution and must not be recorded as executed work.

The new endpoint returns a small envelope, preserving the selected function's
HTTP status and result body rather than replacing its answer. Top-level
`status` mirrors the delegated body's status (`succeeded` or `failed`):

```json
{
  "status": "succeeded",
  "routing": {"outcome":"selected","capability":"memory.query","stage":"delegated"},
  "result": {"...":"the unchanged M3 or M10 response body"}
}
```

For `no_action`, HTTP 200 means the **routing decision** completed, not that a
Capability executed: top-level `status=succeeded`,
`routing.outcome=no_action`, `routing.capability=null`,
`routing.stage=routing`, `result=null`, and null
Task/Execution IDs. A routing-stage failure has top-level `status=failed` and returns a
structured safe error with `routing.stage=routing` and no delegate result. A delegated
failure retains the delegate's HTTP status, failure code, category, message,
`request_id`, and any Task/Execution IDs inside `result`, with
`routing.outcome=selected` and `routing.stage=delegated`. The router must not fabricate
new grounded text, promote `partial` to `supported`, or claim that M3 has
durable Evidence. The exact field spelling of this small envelope is an M11
contract for implementation, not a claim about an existing API.

There is **no common durable audit record for the M11 route decision**. A
response can identify the selected branch, but after response loss an operator
cannot necessarily reconstruct that decision, especially for M3 or
`no_action`. Durable route correlation and parent/child execution structure
need separate review before multi-step orchestration; they are not silently
solved here.

## Failure and unknown-outcome contract

| Situation | Required behavior before delegation |
| --- | --- |
| Missing, invalid, or revoked token | `401 UNAUTHENTICATED`; no routing-model or delegate call. |
| Invalid request/question or supplied project UUID | `400 INVALID_REQUEST` or `INVALID_PROJECT`; no routing-model or delegate call. |
| Unreadable or absent supplied project | `404 PROJECT_NOT_FOUND`; same outward response, no model or delegate call. |
| Database unavailable during authentication or project precheck | `503 DATABASE_UNAVAILABLE`; no model or delegate call. This does not prove the project is absent. |
| Valid model `no_action` | HTTP 200 routing `no_action`; no delegate, Task, Execution, or Evidence. |
| Document route without project ID | `400 PROJECT_ID_REQUIRED`; no delegate. |
| Memory route with project ID | `400 INVALID_ROUTE_ARGUMENT`; no delegate. |
| Malformed **model** JSON, unknown route, or any extra model field/argument | `502 ROUTING_MODEL_OUTPUT_INVALID`; do not coerce to `no_action` or invoke a delegate. |
| Local model unavailable | `503 ROUTING_OLLAMA_UNAVAILABLE`; no delegate and no automatic retry. |
| Local model listener not verified local-only | `503 ROUTING_OLLAMA_NOT_LOCAL`; no delegate or question transmission. |
| Routing model timeout | `504 ROUTING_OLLAMA_TIMEOUT`; no delegate and no automatic retry. |

Delegated M3/M10 failures remain delegated failures with their original safe
codes and status. No fallback to the other capability follows a failure,
timeout, empty answer, insufficient evidence, or M10 zero-document result.
On M3's final disclosure check, a revoked token yields `401 UNAUTHENTICATED`,
an Evidence memory that is no longer readable yields non-enumerating
`404 MEMORY_NOT_FOUND`, and unavailable storage yields
`503 DATABASE_UNAVAILABLE`; none may disclose the held excerpts. A project
membership revoked during M10 is handled by M10's existing permission checks
and its original safe result is preserved.
Where M10 reports `TOOL_OUTCOME_UNKNOWN` or durable commit/response status is
uncertain, preserve its IDs and uncertainty: **Unknown Outcome != Failed**.
Do not mark a `running` record failed, repeat an uncertain attempt, or apply
M4 Memory Write idempotency to M11. M5 Recovery Triage remains
`memory.save`-only and does not recover M11 or M10.

## Security boundary and excluded work

The route model receives an authenticated, bounded user question, never
private retrieved data. Its JSON is untrusted. NOAH alone selects the
allowlisted function, derives arguments from validated user input, enforces
permission, and returns the delegate's verified result. Neither route nor
delegate may reveal API tokens, DB credentials, machine paths, or unauthorized
Memory/Document content in an error or log.

M11 excludes Memory Write, file write, shell, external mutation, multi-step
plans, multiple capability calls, automatic retry/fallback, arbitrary model
arguments, generic registry/framework, Agent loop, and new Knowledge or
Session persistence. Existing M1–M10 endpoints and contracts remain intact.

## Remaining implementation checks

The exact routing prompt byte budget, output-token cap, and timeout must be
chosen with synthetic Korean/English inputs on the current local Ollama model
before M11 is declared validated. The proposed `/requests/route` name and
response envelope are fixed here for a reviewable first implementation, not
claims about existing endpoints. The final Memory disclosure check needs a
bounded implementation that reuses current visibility rules rather than a
second, weaker policy. Uniform durable routing audit and cross-capability
request correlation are explicitly deferred; if those become mandatory for
this first Slice, the Task/Execution contract must be reconsidered before
implementation.

## Implementation and verification plan — not yet performed

Expected code scope: one small routing module (for example
`noah/capability_route.py`) and a single new branch in `noah/__main__.py`.
The existing `noah.memory_query.query_memory` and
`noah.document_auto_query.answer_auto_documents` are the delegates; their
HTTP routes are not invoked internally. Tests belong in a focused M11 test
module plus the existing M1–M10 regression suite. No migration, broad
refactor, or new package is part of this contract.

Deterministic tests must cover authentication before model exposure, safe
question/project validation, unreadable project non-enumeration, exact routing
schema and extra-field rejection, `no_action`, exactly one delegate call,
missing/mismatched project argument, private Memory and project Document
isolation, permission revocation before delegation and disclosure, local-model
failure/timeout, delegated failure/uncertainty preservation, zero duplicate
Task/Execution/Evidence rows, and unchanged existing endpoints. Synthetic
users, memories, projects, and documents must be separated from real data and
cleaned up; the M1–M10 regression must pass.

Opt-in actual Ollama checks must separately demonstrate a synthetic Memory
question selecting `memory.query`, a synthetic project document question
selecting `project.documents.answer.auto`, and an unsupported request
selecting `no_action`, using Korean and English formulations where useful.
Assert **routing selection quality** separately from successful authorized
delegate execution and verified evidence. A Docker Compose PostgreSQL 17
end-to-end check must preserve baseline data and prove that each selected
branch calls only its existing function and that M10 alone creates its one
Task/Execution. No real personal Memory or document is needed for these tests.

M11 is complete only after the bounded route, denial/failure behavior,
permission timing, actual model selection, delegated results, persistent
record counts, full regression, and synthetic-data cleanup are verified and
recorded in an M11 validation report. This document alone does not establish
those results.
