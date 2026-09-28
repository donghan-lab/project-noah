# NOAH State Contract — Current Memory Save Slice

> Status: current implementation contract, 2026-09-28. This documents the
> Memory Write path and read-only recovery triage. It does not define the
> complete future Task or Runtime state machine.

## Boundaries

`noah.tasks` is durable canonical Task progress. `noah.execution_records` is
the durable result of an execution attempt. A Runtime or HTTP server process
can stop while the Task remains. Its termination is **not** evidence that the
Task failed. Memory is a separate side effect, not a replacement for Task
State. These boundaries follow DDR-001, DDR-002, and DDR-006.

The present `memory.save` implementation has one Task and one execution
attempt per authorized, validated new write. Rejections before Task creation
have a failed execution record with no Task. Read and LLM query routes do not
create Tasks or execution records. This document must not be applied to other
future capabilities without defining their own side-effect and retry rules.

## Stored states and transitions

| Record | Current stored states | Transition and required evidence |
| --- | --- | --- |
| Task | `running`, `completed`, `failed` | A new authorized write starts `running` with verification `pending`. A verified memory readback permits `completed/passed`. A definite rolled-back write or verification failure permits `failed/failed`. |
| Execution record | `running`, `succeeded`, `failed` | A new write starts `running`. The same verified memory readback permits `succeeded` with `memory_id` and `verified_at`. A definite rolled-back error permits `failed` with a failure code. Pre-Task input or permission rejection is recorded directly as `failed` without a Task. |
| Task verification | `pending`, `passed`, `failed` | `pending` accompanies the new running Task; `passed` requires verified memory; `failed` accompanies a definite failure. |

The database constrains the allowed values, but it does not enforce this
entire transition graph. The current Memory Write service performs these
transitions. A terminal row must not be rewritten from a timestamp alone.

## Commit and evidence boundary

1. Authentication, input validation, and write permission precede Task
   creation and all memory side effects.
2. Task `running/pending`, execution `running`, and any user-scoped
   Idempotency-Key reservation commit together **before** the memory insert.
3. Memory insert, PostgreSQL readback, Task `completed/passed`, and execution
   `succeeded` with `memory_id` and `verified_at` commit together. A normal
   successful write cannot leave only one of these final updates committed.
4. A definite write or verification failure rolls back the memory transaction.
   Task `failed/failed` and execution `failed` with a failure code are then
   recorded together when PostgreSQL remains available.
5. If a commit acknowledgement or the database connection is lost, the
   outcome may be unknown. The service must not overwrite a possibly
   successful commit with a guessed failure.

For read-only triage, a confirmed success requires the completed/passed Task,
the succeeded execution, a non-null verification time, and an existing memory
whose creator and user owner match the actor where applicable. A confirmed
failure requires matching failed Task and execution states, a failure code,
and no memory reference. A failed pre-Task rejection is valid with no Task.
Missing or contradictory evidence is reported, not repaired by triage.

## Unknown outcome and idempotency

**Unknown Outcome != Failed.** `running` means no final durable result has
been recorded. It does not prove that a Runtime is still active, that it has
stopped, or that the side effect did not occur. Age and `updated_at` can
prioritize inspection but cannot establish success, failure, or permission to
retry. Client response loss also does not imply storage failure.

For a keyed write, `noah.memory_write_requests` maps one authenticated user
and key digest to the original execution and normalized request fingerprint.
A retry with the same key and request may return a verified terminal result.
If the original record remains running, M4 returns `pending` without another
write. A different request with that key conflicts. An unkeyed legacy write
has no durable retry identity, so content equality is never a deduplication
rule. The local `.noah/failures.jsonl` fallback is diagnostic, not canonical
Task or execution state.

## Read-only recovery triage

Triage reports `verified_completed`, `recorded_failure`,
`unresolved_running`, or `record_inconsistent`. It also reports an outcome of
`succeeded`, `failed`, or `unknown`. The last value is an assessment, **not**
a new database status. `interrupted` and `recovery_pending` are not current
database states and are not inferred from process absence or time alone.

Triage can inspect Task, execution, key mapping, memory reference and
verification metadata in a read-only PostgreSQL transaction. It does not
change those records, create or delete memory, or retry a capability. A
missing memory reference, mismatched actor, contradictory states, or missing
verification evidence must not be silently converted to success or failure.
Database unavailability means inspection was unavailable, not that no
unresolved work exists.

## Automatic recovery boundary

No automatic state transition or write retry is currently authorized for a
running or inconsistent record. In particular, process exit, server restart,
expired time threshold, absent visible memory, or a local failure log entry
alone cannot justify `running -> failed`. The current schema has no durable
runtime ownership, fencing, or heartbeat contract that could prove a prior
attempt cannot still commit. Any future automatic mutation needs a separately
reviewed state transition and side-effect reconciliation contract.
