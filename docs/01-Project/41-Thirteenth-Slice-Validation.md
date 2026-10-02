# M13 Controlled Explicit Memory Save Routing — validation record

> Date: 2026-10-02 (Asia/Seoul). Contract baseline:
> `main@16807dda51530a39ff07e7a9c108324579112f95`.
> Status: local implementation and automated Compose PostgreSQL 17 validation
> complete; actual-model selection and separate user manual HTTP E2E complete;
> Git commit and Push pending.

## Implemented path

`POST /requests/route` retains the M11/M12 read-only branch for requests
without `memory_save`. Its new write branch requires exactly `question` and
`memory_save: {content}`, plus one valid `Idempotency-Key` header. Token,
shape, content, user-only target, question bounds, and known-credential checks
precede audit reservation. The only source of stored text is the caller's
`memory_save.content`; it is not included in the routing model messages.

After a durable M12 audit reservation, the model sees the bounded question,
a fixed payload-present marker, and only `memory.save | no_action`. Local
Ollama/model failures are observed as routing failures without starting a
write. NOAH validates the proposal, rechecks the token, and confirms
`route_validated` and `dispatch_prepared` before a single internal
`save_memory()` call. `dispatch_prepared` does not prove the call began.
M1/M4 alone own the Memory, Task, Execution, and key mapping. M13 verifies
their returned correlation before writing IDs to the separate M12 audit.
An M1 rejection Execution without a Task can yield only a verified request
ID in that audit. A failed final audit update cannot replace the returned
write result; `routing.audit_status=unconfirmed` describes audit uncertainty.
The router never retries or falls back. M5 remains read-only and covers
`memory.save` records, not routing-audit recovery.

## Schema and API

`009_memory_save_routing.sql` expands only three bounded CHECK constraints
on `noah.routing_audit` so `memory.save` can be a validated and prepared
delegate route. It creates no table, column, Task state, FK, or Capability
Evidence. The migration was applied through `python -m noah init` to the
existing Compose PostgreSQL 17.10 database without replacing rows or
initializing the named volume. The schema still has 18 tables.

Example shape, using a synthetic value and a caller-generated key:

```http
POST /requests/route
Authorization: Bearer <existing-token>
Idempotency-Key: <unique-client-key>
Content-Type: application/json; charset=utf-8

{"question":"내가 명시한 내용을 내 메모로 저장해줘.","memory_save":{"content":"공개용 합성 메모"}}
```

A first verified write retains the M1 HTTP 201 result inside `result`, keyed
replay retains HTTP 200 and original IDs, and an M4 conflict retains HTTP
409. The top level adds `router_id` and `routing.audit_status` only after
the eligible audit boundary. `no_action` writes an audit row but no Memory,
Task, Execution, or M4 mapping. A model-stage failure has an audit row when
its terminal update commits, but no delegated write. A preflight rejection
has neither audit nor write side effects.

## Automated verification

| Run | Result | Covered boundary |
| --- | --- | --- |
| M13 dedicated, Compose PostgreSQL 17.10 | 9 passed, 1 opt-in skipped | New write, exact M1/M4 row set, replay, conflict, different key, audit correlation, user-only storage, prompt/key secrecy, `no_action`, preflight and model failure, audit-stage fault injection, token revocation, final-audit uncertainty, `WRITE_OUTCOME_UNKNOWN` no retry, HTTP header path. |
| M1–M13 full regression, Compose PostgreSQL 17.10 | 156 tests: 147 passed, 9 opt-in skipped, 0 failed/errors | Existing M1–M12 behavior plus M13 dedicated tests. |
| M13 actual Ollama selection opt-in, `gemma4:12b-it-qat` on dedicated loopback `127.0.0.1:11435` | 1 passed separately | Public synthetic Korean and English explicit-save questions selected `memory.save`; unrelated write request selected `no_action`. This checked model choice only, not an actual-model HTTP write E2E. |

The dedicated Ollama process started for this opt-in test was stopped after
the test; the listener is no longer present. The generic `11434` service was
not changed. Deterministic PostgreSQL tests used synthetic users and stubbed
routing proposals so permission, transaction, and correlation assertions do
not depend on model selection quality.

## Separate user manual HTTP E2E

The operator completed the [M13 manual procedure](42-Thirteenth-Slice-Manual-Validation.md)
against the working-tree NOAH HTTP server, Compose PostgreSQL 17, and a
dedicated loopback Ollama `127.0.0.1:11435` with the current model. This is
distinct from both the deterministic automated suite and the opt-in
actual-model **selection-only** test above. The operator reported exactly
three HTTP requests, without an API retry after an uncertain result:

| Request | Observed result and read-only verification |
| --- | --- |
| First `POST /requests/route` | Sent once; HTTP 201, selected `memory.save`, audit `recorded`, existing M1 DB readback passed. Stored text exactly matched explicit `memory_save.content`, not the routing question. One Memory, Task, Execution, M4 mapping, and correlated routing-audit row were created. |
| Deliberate same-key/body M4 replay | Sent once **after** first-result and DB confirmation; HTTP 200, `replayed=true`, original M1 request/Task/Execution/Memory IDs retained. A new router ID and second audit row appeared, with no second write set. This was not a retry of an uncertain write. |
| `GET /memories/<id>` | Sent once; HTTP 200 with exact synthetic Memory content and zero DB delta. |

The operator's read-only verifier confirmed the audit-to-M1/M4 correlation,
absence of duplicate router Task/Execution, and no forbidden question,
content, key/hash, token/password, prompt, or raw model output in the audit
or API response. After server shutdown and exact ownership/delta checks, one
transaction removed only this run's synthetic user/token/Memory/Task/
Execution/M4 mapping and two audit rows. Original counts and private row
fingerprints across all 18 tables matched the baseline. No local fixture
file or mapping was created. The named PostgreSQL volume, existing mapping
state, Git working tree, general Ollama `11434`, and PostgreSQL service were
unchanged; only the dedicated `11435` instance started for this run was
stopped. `no_action`, `WRITE_OUTCOME_UNKNOWN`, and audit failure injection
were not exercised manually; their failure boundaries remain automated-test
results.

## Data preservation and current limits

Read-only before/after fingerprints of all 18 `noah` tables matched exactly.
Counts remained: user 1, API token 1, Memory 2, Task 2, Execution 3, M4
mapping 1; project, membership, routing audit, and M6–M10 Evidence 0.
`running` Task and Execution counts were each 0. Test-owned synthetic rows
were removed; existing personal Memory, token, and Docker named volume were
not deleted or reset. The Compose service remained running.

The separate actual-model route-choice test did not itself prove an HTTP
write; the operator E2E above supplied that evidence. A repeated routed
request is not itself idempotent: M4 replay
applies only if the same explicit request and key reach `save_memory()` again.
An uncertain write outcome still requires the existing M4/M5 process; the
audit row cannot establish that a write failed or license automatic retry.
