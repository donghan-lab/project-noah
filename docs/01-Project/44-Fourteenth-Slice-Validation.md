# M14 Controlled Memory Suppression — automated validation

> Date: 2026-10-05 (Asia/Seoul). Contract baseline:
> `main@11844fd9b4116ba0c1ccd37328f401da7a1b3b23`.
> Status: implementation and automated Compose PostgreSQL 17 verification
> complete in the uncommitted working tree. **Separate operator manual HTTP
> E2E, final review, Git commit, and Push are pending.**

## Implemented boundary

`010_memory_suppression.sql` adds only nullable
`noah.memories.suppressed_at timestamptz DEFAULT NULL`. Existing and newly
saved rows are active. No suppression table, FK, Task status, or DDR change was
added. `POST /memories/<memory_id>/suppress` accepts an authenticated owner,
one user-scope UUID target, and exactly `{}`. It uses no model or Router.

The first verified transition commits the timestamp and exactly one
`memory.suppress` Task/Execution together. The transaction rechecks the
original token and target ownership/scope, conditionally updates the row,
reselects unchanged content/provenance/creation fields, and verifies terminal
Task/Execution records. An authorized repeat returns the original timestamp
with new request correlation and null Task/Execution IDs. A failed update or
verification with confirmed rollback leaves no transition; uncertain commit
acknowledgement returns `SUPPRESSION_OUTCOME_UNKNOWN` without guessing the
durable outcome or retrying.
The local failure diagnostic now marks both `WRITE_OUTCOME_UNKNOWN` and
`SUPPRESSION_OUTCOME_UNKNOWN` as `status=unknown`; definite diagnostic failures
remain `status=failed`. The M14 HTTP envelope and Task/Execution records did
not change.

Direct owner lookup retains the content and reports `suppressed=true` with the
persisted timestamp. Every active Memory list/direct object has
`suppressed=false` and `suppressed_at=null`. Ordinary list and M3 word search
exclude suppressed rows in their SQL predicate before ordering, cursor, and
limit. M3 stores all model-input Memory IDs only in request memory and checks
the whole set before direct disclosure. The M11 routed result carries that
same ephemeral ID set through the M11 final disclosure check. A changed,
uncited model-input Memory blocks the entire answer, quotes, and search
metadata; neither path invokes the model again or persists its rejected text.

## Automatic verification actually run

| Run | Result | Relevant checks |
| --- | --- | --- |
| M14 dedicated, Compose PostgreSQL 17 | **11 passed, 0 skipped** | First/repeat, exact timestamp, one verified Task/Execution, owner/project/token denial, transaction-time token revocation, SQL pagination, direct M3 cited and uncited races, M11 post-M3 and post-correlation races, concurrent transition, rollback/readback and lost commit acknowledgement, M4 replay, M5 scope, local HTTP endpoint, and local diagnostic status classification. |
| Related M1–M5 and M11–M13 regression groups | **69 passed, 3 opt-in skipped** across 72 tests | Existing save/read/query, idempotency, recovery, routing, routing audit, and explicit save routing. |
| Full M1–M14 suite after final code change | **167 tests: 158 passed, 9 opt-in skipped, 0 failures/errors** | All existing and M14 tests. |

The nine skipped opt-in tests require a separately started local Ollama model.
M14 changes SQL visibility and final disclosure, not model prompt/schema or
model selection; deterministic stub tests cover the new races. No actual
Ollama run or user-operated manual HTTP E2E is claimed here. The M14 automated
HTTP test uses only a local test server and a synthetic user/Memory.

## Persistent DB preservation

Before migration, read-only fingerprints and counts were captured for all
**18** existing `noah` tables: users 1, api_tokens 1, memories 2, tasks 2,
execution_records 3, memory_write_requests 1, and project/membership/M6–M13
Evidence/routing audit 0. Running Task and Execution counts were both 0.
`python -m noah init` applied the additive migration to the existing Compose
PostgreSQL 17 instance. Both original Memories remained active. Comparing the
original row JSON with the new nullable field excluded showed identical row
fingerprints and counts immediately after migration.

Tests created separate synthetic users and records, then removed only their
own rows. After the final full suite, all 18 table counts and private row
fingerprints matched the pretest baseline; running Task/Execution and
suppressed original Memory counts were 0. The existing container remained
running with named volume `noah_noah-postgres-data` mounted at
`/var/lib/postgresql/data`. No existing personal Memory, user, token, Docker
volume, or global Ollama configuration was deleted or initialized.

## Remaining verification

Operator manual HTTP E2E is **not yet run**. It must use only a synthetic
owner and Memory, verify first suppression, repeat semantics if planned,
management lookup versus normal retrieval, Task/Execution linkage, and exact
cleanup/baseline restoration. Commit and Push await that review. M14 does not
provide restore/delete/edit, project-scope suppression, Router selection,
automatic retry, or M5 recovery for `memory.suppress`.
