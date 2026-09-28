# M5 first step: read-only Task Recovery Triage

This slice adds an **operator diagnostic**, not automatic recovery. It covers
the current `memory.save` Task/Execution contract only. It does not alter the
database schema, user data, Task or Execution states, or retry a write.

## Run on Windows PowerShell

From the NOAH repository root, ensure Docker Desktop and the existing Compose
PostgreSQL service are running. The command uses the existing ignored
`compose/.env` settings; do not print that file or put credentials on the
command line.

```powershell
docker compose --env-file compose/.env -f compose/docker-compose.yml ps
.venv\Scripts\python.exe -m noah recovery-report
```

The second command produces JSON. `status: succeeded` means **the inspection
ran**, not that all Tasks succeeded. Check `counts` and `items`. A healthy
completed write is `verified_completed`; a durably failed attempt is
`recorded_failure`. `unresolved_running` means no terminal evidence exists.
`record_inconsistent` means records disagree or required evidence is missing.
Both latter classes have `outcome: unknown` and require operator review. No
class triggers a state update or write retry. A keyed running write remains
pending under the M4 API contract. A keyless running write lacks a durable
retry identity.

The output includes Task and Execution IDs, states, verification metadata,
whether a key mapping and memory reference exist, issue codes, and why NOAH
took no action. It omits token values, key digests, database credentials,
memory contents, and user IDs. Treat Task/Execution IDs as operational data.

If PostgreSQL cannot be inspected, the command exits nonzero and reports
`status: unavailable` with `DATABASE_UNAVAILABLE`. It does **not** report an
empty or healthy database. The command does not need `noah init` because M5
has no migration. The HTTP server does not need restarting to use this
separate command; run it from the updated checkout. It does not expose a new
HTTP route.

## Inspection boundary

NOAH reads the current Memory Write Tasks, `memory.save` Execution Records,
Idempotency mappings, and referenced memory **metadata** in one PostgreSQL
`REPEATABLE READ, READ ONLY` transaction. It does not fetch memory content.
Normal M4 writes commit reservation records first, then verified memory and
terminal records atomically. Therefore a completed, verified Task with a
matching succeeded Execution and existing memory supports a confirmed
success. A matching failed Task and Execution with a failure code and no
memory reference supports a recorded failure. A rejected request may have a
failed Execution without a Task. Any missing or contradictory evidence is
reported, never guessed from age or process state.

The fixed Task goal identifies the current Memory Write implementation. A
future capability must define its own durable record and reconciliation
contract before extending this diagnostic. See the current state contract in
[`Runtime/State.md`](../02-Architecture/Runtime/State.md) and the test record
in [M5 Validation](22-Fifth-Slice-Validation.md).
