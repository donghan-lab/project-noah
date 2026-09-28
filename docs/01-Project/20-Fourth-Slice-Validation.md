# Fourth Vertical Slice Validation Record

Date: 2026-09-28 (Asia/Seoul)

## Environment and migration

The existing `noah-postgres` Docker Compose container ran PostgreSQL 17.10
with the existing `noah_noah-postgres-data` named volume. Before migration,
the `noah` schema had one user, one token, one personal memory, one completed
Task, and one succeeded execution record; projects and memberships were empty.
`python -m noah init` applied the additive `002_memory_write_idempotency.sql`
migration. Existing tables and rows were not rewritten. The new mapping table
started empty. No Compose teardown, volume reset, user reprovisioning, or
personal memory change was performed.

## Tests executed against Compose PostgreSQL 17

| Run | Result | Coverage |
| --- | --- | --- |
| `.venv\Scripts\python.exe -m unittest discover -s tests -p test_memory_idempotency.py -v` | 6 passed, 0 failures/errors/skips | First save, verified replay, conflicting body, distinct keys, per-user isolation, authentication and key validation, concurrent reservation, failed write rollback, lost commit acknowledgement, true server **process** restart |
| `$env:NOAH_RUN_OLLAMA_TESTS='1'; .venv\Scripts\python.exe -m unittest discover -s tests -q` (final rerun) | 30 passed, 0 failures/errors/skips; 48.480 seconds | Fourth Slice plus all prior Write, Read, and Local LLM Query tests, including the real loopback Ollama test using only synthetic PostgreSQL memories |

The concurrent test held the first request after committing its durable
reservation. The second received `pending`; only one memory and one key
reservation were created. A later retry returned the original evidence. The
process restart test terminated one NOAH Python server process, started a
second process, and received the same memory ID on replay. This is distinct
from the earlier M1 test that only recreated an HTTP server instance within
one Python process.

The rollback test caused a real PostgreSQL foreign-key failure. No memory row
survived; the Task and execution record were `failed`, and the same key
replayed that failure. The lost-acknowledgement test committed the final
transaction and then simulated a client-side commit error. NOAH reported an
uncertain outcome; replay found the completed Task, succeeded execution, and
single memory instead of writing another or recording a false Task failure.

The first draft of the new test suite had three failed assertions because its
mapping count included other synthetic cases in the same class. The count was
restricted to each case's key; the subsequent dedicated run and full suite
passed. Two anonymous rejection records left by those initial trial runs were
identified against the one-record baseline and removed by their exact test
IDs. The finalized test cleanup removes its own users, keys, memories, Tasks,
and execution records.

## User manual verification and read-only database audit

The user then exercised the updated NOAH server with a distinct, public test
note and an existing account. This was a separate manual check, not part of
the 30 automated tests. The first `POST /memories` returned HTTP 201. Repeating
the same body and `Idempotency-Key` returned HTTP 200 with `replayed: true`;
the memory, Task, and execution IDs were identical. Reusing that key with
different content returned HTTP 409 and `IDEMPOTENCY_CONFLICT`.

Read-only PostgreSQL queries compared the post-automation baseline with the
state after this manual test:

| Record | Before manual test | After manual test | Interpretation |
| --- | ---: | ---: | --- |
| Users | 1 | 1 | Existing user retained |
| Active API tokens | 1 | 1 | Existing token retained |
| Personal memories | 1 | 2 | Exactly one public test memory added |
| Tasks | 1 | 2 | One Task for the first save; none for replay or conflict |
| Execution records | 1 | 3 | One successful save and one failed conflict rejection; none for replay |
| Idempotency mappings | 0 | 1 | One durable mapping for the manual write key |

The mapping points to a `succeeded` execution record, its `completed` Task
with `verification_status=passed`, and the one new user-owned memory. The
conflict record has `failure_code=IDEMPOTENCY_CONFLICT` and no Task or memory
reference. Thus neither the identical retry nor the conflicting request
created another memory. There were zero `running` Tasks and zero `running`
execution records. The pre-existing personal memory remained as the older,
unmapped row; both personal memories belonged to the existing user. No memory
body or credential was printed during the database audit.

## Data and security checks

The tests used separate synthetic identities and notes. The previous user's
real memory and identity were not passed to Ollama or changed. The dedicated
Ollama listener was observed at `127.0.0.1:11435`; the existing 11434 service
was not changed. No API token, PostgreSQL password, or personal memory text is
included in this record. After **automated** test cleanup and before the
manual check, the baseline was one user, one token, one Task, one memory, one
execution, and zero key mapping rows. The later manual counts are recorded
above. The new table remains installed in the existing schema.

## Architectural scope and remaining limits

The mapping records only user, key digest, request fingerprint, and an
execution reference. `noah.tasks` remains canonical Task progress and
`noah.execution_records` remains the execution outcome and memory evidence,
consistent with DDR-001 and DDR-006. NOAH still authenticates and checks
scope before writing or replaying; LLM access is not part of this write path.

The key is optional for API compatibility, so unkeyed writes can still be
duplicated by retries. A stale `running` Task is conservatively returned as
`pending` until a separate recovery capability reconciles it. Definite failed
writes are sticky for their key. Previous keyless writes are not backfilled.
