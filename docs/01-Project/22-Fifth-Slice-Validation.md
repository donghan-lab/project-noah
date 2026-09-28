# M5 read-only Task Recovery Triage validation

> 2026-09-28, existing Docker Compose PostgreSQL 17. This report concerns
> M5 synthetic validation and a separate read-only inspection of existing
> records. No database migration or automatic recovery was performed.

## Environment and test result

- The existing `noah-postgres` Compose service was running with its named
  volume mounted. No container or volume reset was run.
- `python -m unittest tests.test_recovery -v`: **2 passed**, no skip or error.
- `python -m unittest discover -s tests -v`: **32 discovered, 31 passed, 1
  skipped, 0 failed/errors**. The skipped case is the opt-in call to a real
  local Ollama model. The other Memory Write, Read, LLM Query (with synthetic
  model), and Idempotency regression tests passed against the existing DB.
- M5 created synthetic users and records only for its integration test. It
  compared full synthetic Task, Execution, Memory, and mapping rows before
  and after triage; all were identical. The test then removed only its own
  synthetic rows. Existing user rows and personal memory were not changed.
- PostgreSQL reported version **17.10**. The triage transaction reported
  `transaction_read_only=on`. After the full suite and test-owned cleanup,
  the existing schema held **1 user, 1 token, 2 memories, 2 Tasks, 3
  Execution Records, and 1 key mapping**, with **0 running Tasks** and **0
  running Executions**. These match the documented post-M4 manual state.

## Evidence scenarios

| Synthetic scenario | Expected diagnostic | Result |
| --- | --- | --- |
| Verified completion | `verified_completed/succeeded` | Passed |
| Reservation committed, final result absent | `unresolved_running/unknown` | Passed |
| Final commit succeeded, response lost | `verified_completed/succeeded` | Passed |
| Definite rolled-back failure | `recorded_failure/failed` | Passed |
| Running with Idempotency mapping | `unresolved_running/unknown`, mapping present | Passed |
| Running without key | `unresolved_running/unknown`, mapping absent | Passed |
| Task/Execution status mismatch | `record_inconsistent/unknown` | Passed |
| Execution/memory actor mismatch | `record_inconsistent/unknown` | Passed |
| Succeeded Execution without a memory reference | `record_inconsistent/unknown` | Passed |
| Missing Execution for Memory Write Task | `record_inconsistent/unknown` | Passed |
| Database connection unavailable | `status: unavailable`, no items or empty-success claim | Passed |

The `running` scenarios are records constructed to represent the reservation
state. The diagnostic does not claim that a process stopped; it cannot infer
runtime liveness. The response-loss scenario uses durable successful rows and
tests their classification, rather than injecting an actual network fault.
No personal memory content was read or emitted by triage.

## Existing-record inspection

An explicit `python -m noah recovery-report` call on the existing database
returned `status: succeeded`, scanned **3** Memory Write Execution Records:
**2 `verified_completed`** and **1 `recorded_failure`** (a pre-Task rejection).
There were no `unresolved_running` or `record_inconsistent` items in that
snapshot. The report contained IDs and status/verification metadata, with no
memory body, token, key digest, or password. This is an inspection result,
separate from the synthetic test outcomes and earlier M4 manual verification.

## User manual verification (separate from automated tests)

The user ran `recovery-report` against the existing NOAH database on
2026-09-28 and reported `status: succeeded`, `scanned: 3`,
`verified_completed: 2`, and `recorded_failure: 1`. No
`unresolved_running` or `record_inconsistent` entry appeared. All three
items had `issues: []`. Both completed items reported Task `completed`,
Execution `succeeded`, verification `passed`, `verified_at_present: true`,
`memory_reference_present: true`, and `memory_exists: true`.

One completed item had an Idempotency mapping and the other did not. This is
consistent with the documented earlier unkeyed write and later M4 keyed
write; mapping presence alone does not establish a record's creation time.
These are the user's direct observations, recorded separately from the
synthetic automated cases and NOAH's earlier operator inspection. No memory
body, token, key digest, or password is reproduced here.

## Limits

Read-only triage cannot prove whether an unresolved Runtime is still alive,
whether an unseen write could commit, or whether a local failure log is
canonical. Timestamp age alone is never a failure signal. No automatic
`running -> failed`, replay, or repair path was added. The current Task goal
string identifies Memory Write Tasks; a future generalized capability needs
an explicit capability link and separately reviewed recovery contract.
