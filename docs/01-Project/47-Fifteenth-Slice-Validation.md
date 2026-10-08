# M15 Controlled Explicit Memory Suppression Routing — automated validation

> Date: 2026-10-06 (Asia/Seoul). Contract baseline: `main@ca37c7a2d9481b96c618274abfaf5bad6f6cb765`.
> Status: implementation, deterministic automated verification, actual Ollama route-selection verification, and operator manual HTTP E2E are complete. Final implementation and validation were committed and pushed to GitHub `main` at `301ab567da29f9654799625f0de159596f0c962a`.

## Implemented boundary

`POST /requests/route` now accepts exactly `{"question":"...","memory_suppress":{"memory_id":"<UUID>"}}` as a separate request shape. The model sees the question and a fixed payload-present marker, never the structured target ID or Memory content. Its structured proposal for this shape is only `memory.suppress` or `no_action`; the existing payload-free read routes and M13 explicit save route remain separate. A selected route uses one internal `suppress_memory()` call with the caller's UUID, empty M14 payload, and original credential. The M14 primitive owns authorization, the state transition, and any Task/Execution. `no_action` reads no target and runs no delegate.

`011_memory_suppression_routing.sql` extends only the three bounded `routing_audit` CHECK constraints to admit `memory.suppress`. It adds no table, column, FK, Task, Execution, or target ID to the audit. An eligible request receives one operational audit row. Verified first-transition request/Task/Execution IDs are correlated to the M14 records and target. An authorized repeat correlates only the in-process returned request ID; its Task/Execution IDs remain null. The audit cannot reconstruct an exact repeat target after response loss. It is not the suppression outcome source of truth.

Authentication, exact JSON shape, question, and UUID syntax fail before audit reservation. Model failures occur after reservation and before M14, with zero suppression writes. Unconfirmed reservation or pre-delegate audit update prohibits M14 invocation. `dispatch_prepared` does not prove invocation. A final audit failure after M14 returns marks only `routing.audit_status=unconfirmed`; the delegate result is preserved. `SUPPRESSION_OUTCOME_UNKNOWN` is not converted into a definite failure or retried. M5 remains `memory.save`-only.

## Automatic verification actually run

| Run | Result | Scope |
| --- | --- | --- |
| M15 dedicated, Compose PostgreSQL 17 | **13 tests: 12 passed, 1 opt-in skipped, 0 failed** | Exact preflight and duplicate JSON keys, route allowlists and model failures, no-action without target lookup, first/repeat M14 ownership and correlation, routed suppression followed by fresh normal list/search exclusion, target ownership change after model selection and M14 denial, foreign/missing/project target denials, token revocation in M14 transaction, audit reservation/update/final failures, unknown outcome, no retry, and local HTTP parser. |
| Related M14/M15 tests, Compose PostgreSQL 17 | **24 tests: 23 passed, 1 opt-in skipped, 0 failed** | Existing M14 state/visibility/transaction tests and the strengthened M15 route tests. |
| Full M1–M15 suite, Compose PostgreSQL 17 | **180 tests: 170 passed, 10 opt-in skipped, 0 failed/errors** | M1–M14 regression plus M15 deterministic tests. |

## Actual Ollama route-selection verification

The first opt-in check with `gemma4:12b-it-qat` selected `memory.suppress` for the unrelated English question `What is the weather tomorrow?` despite expecting `no_action` (2 positive cases passed, 1 negative case failed). It was a semantic selection error with valid structured output; the request was not repeated. The M15 system instruction was then clarified: a payload-present marker means only that a caller-selected target is available, and unrelated, unsupported, or ambiguous questions require `no_action`. The prompt contains no test-specific question or answer.

After the prompt change, the three M11/M13/M15 route test modules passed deterministic verification: **40 tests, 37 passed, 3 opt-in skipped, 0 failed**. The existing opt-in selection test methods were then invoked directly without their DB-provisioning class fixtures, so only model proposals were tested. Each planned question was sent once to the existing `gemma4:12b-it-qat` model through the dedicated loopback-only `127.0.0.1:11435` listener:

| Request shape | Synthetic question class | Expected and observed |
| --- | --- | --- |
| `memory_suppress` | Korean and English explicit suppression | `memory.suppress` (2/2) |
| `memory_suppress` | Korean and English unrelated weather questions | `no_action` (2/2) |
| Payload-free M11 | Korean Memory query, Korean project document question, English unsupported action | `memory.query`, `project.documents.answer.auto`, `no_action` (3/3) |
| `memory_save` | Korean and English explicit save, English unsupported action | `memory.save`, `memory.save`, `no_action` (3/3) |

**Actual-model selection: 10 passed, 0 failed.** No router, delegate, HTTP API, Memory write/suppression, Task, Execution, or routing audit was invoked by these checks. The before/after 18-table counts and private row fingerprints matched exactly; running Task/Execution stayed at zero. The PostgreSQL named volume and general Ollama `11434` were unchanged. This verifies selection quality for these bounded synthetic prompts, not general routing accuracy or the operator HTTP E2E path.

## Persistent DB and volume preservation

Before migration and tests, read-only counts and private row fingerprints were captured for all 18 existing `noah` tables: users 1, api_tokens 1, memories 2, tasks 2, execution_records 3, memory_write_requests 1, project/membership and M6–M15 evidence/audit rows 0. Running Task and Execution counts were 0. Only migration 011 was applied to the existing PostgreSQL 17 database; `python -m noah init` was not run. After the dedicated and full suites cleaned their synthetic rows, all 18 table counts and private row fingerprints matched the baseline, and running Task/Execution remained 0. Existing user, token, Memories, Task/Execution, M4 mapping, and suppression states were preserved. The PostgreSQL named volume remained mounted; no Docker volume initialization or deletion occurred.

## Operator manual HTTP E2E actually run

On 2026-10-06, the operator executed [the M15 manual runbook](48-Fifteenth-Slice-Manual-Validation.md) once with one synthetic user, token, and active user-scope Memory. The run sent the five planned HTTP requests and exactly one mutating `POST /requests/route`; no API request was resent. Before mutation, owner direct GET, normal list, and production model-free `search_memories()` all observed the active synthetic Memory with zero read delta. The actual `gemma4:12b-it-qat` route selection chose `memory.suppress`; the routed request returned HTTP 200 / `succeeded`, `routing.audit_status=recorded`, and the delegated M14 result `suppressed`.

Read-only durable proof then confirmed the retained original Memory and persisted suppression timestamp, exactly one M14 Task, one M14 Execution, and one M15 Routing Audit with the returned correlation IDs. The audit minimization check found no prohibited target/content/question/token values or forbidden target columns, and M4/project/document Evidence remained unchanged. A fresh owner direct lookup retained the original Memory while a fresh normal list and production model-free search excluded it.

NOAH was stopped before cleanup. Read-only ownership verification passed, exactly six synthetic DB rows were removed in one transaction, and the original 18-table counts, private row fingerprints, and suppression states were restored exactly. The PostgreSQL named volume, local document mapping, Git working-tree snapshot, and ordinary Ollama `11434` were unchanged. The dedicated loopback-only `11435` listener started by this run was stopped only after restoration and its ownership/lifetime check passed.

## Remaining limits

The manual run deliberately did not repeat routed suppression. Deterministic tests cover the routed `already_suppressed` behavior. Audit commit acknowledgement uncertainty, `SUPPRESSION_OUTCOME_UNKNOWN`, final audit update uncertainty, token-revocation race, ownership-change race, and automatic retry/fallback prohibition paths remain automated-only checks rather than manually injected failures. No target Memory ID is stored in routing audit, so a no-op audit row alone cannot reconstruct its exact target after response loss. There is no automatic retry, fallback, or M5 recovery for suppression.
