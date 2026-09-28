# Fourth vertical slice: Memory Write Idempotency

This slice adds an optional, client supplied retry identifier to the existing
`POST /memories` route. It prevents a repeat of the same logical write across
concurrent requests and NOAH process restarts. The other Memory Write, Read,
and local LLM Query routes retain their contracts.

## Upgrade and run on Windows

Keep the existing PostgreSQL Compose container and volume. With the updated
code, run the additive migration once before restarting the NOAH server:

```powershell
.venv\Scripts\python.exe -m noah init
.venv\Scripts\python.exe -m noah serve
```

`init` applies `001_first_slice.sql` and then
`002_memory_write_idempotency.sql`. Both use `CREATE ... IF NOT EXISTS`. The
second file only creates `noah.memory_write_requests`; it does not rewrite or
backfill prior memories, Tasks, or execution records. Repeating `init` is
safe. A running server must be restarted to load the new code.

## API contract

For a new logical write, generate an opaque key once and retain it with that
request. Retry the **same body and same key** after a lost response. A new
intentional save, even with identical content, uses a new key. The header
accepts 1 to 128 ASCII letters, digits, `.`, `_`, `~`, and `-`; the first
character must be a letter or digit. NOAH stores only its SHA-256 digest.

```powershell
$key = [guid]::NewGuid().ToString()
$body = @{
    action = 'save_memory'
    scope = 'user'
    owner_user_id = $env:NOAH_USER_ID
    content = 'Synthetic note for an idempotency check'
} | ConvertTo-Json
$headers = @{
    Authorization = "Bearer $env:NOAH_API_TOKEN"
    'Idempotency-Key' = $key
}
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/memories' -Method Post `
    -Headers $headers -ContentType 'application/json' -Body $body
```

Save `$key` and `$body` until the outcome is known. Repeating the last command
returns the original request, Task, execution, and memory IDs without writing
a second memory. The first success is HTTP 201. A verified replay is HTTP 200
with `replayed: true`. While the original Task is still `running`, the same
request returns HTTP 202 with `status: pending` and its original IDs. The
client may retry the same key later; NOAH will not start another write for it.

If the key belongs to a different validated request from the same user, the
response is HTTP 409 with `IDEMPOTENCY_CONFLICT`. Missing or invalid bearer
credentials are rejected before looking up a key. Scope and write permission
are rechecked for every retry. An invalid key returns HTTP 400. Existing
clients that omit `Idempotency-Key` retain the earlier non-idempotent behavior
and HTTP 201 success contract.

The fingerprint covers the validated action, normalized content (the content
already stored after trimming), scope, and owner/project target. Unrelated
extra JSON properties do not alter the operation. A key is scoped to its
authenticated user. Definite failed writes remain failed under that key;
starting a new attempt after inspecting the failure requires a new key.

## Durable execution and uncertainty

NOAH authenticates and validates the request, checks write permission, then
creates the Task, running execution record, and key reservation in one
PostgreSQL transaction. The unique `(actor_user_id, key_digest)` primary key
serializes concurrent reservations. A second request reads the first Task and
execution outcome. A successful memory insert, database readback, Task
completion, and execution success commit together. A definite write error
rolls back the memory and records failed Task and execution states.

If the final database commit acknowledgement is lost, the write may already
exist. NOAH returns `WRITE_OUTCOME_UNKNOWN` and does not overwrite the
possibly successful Task with a false failure. A keyed client can retry the
same key to read the durable outcome. If a crash leaves a Task `running`,
retries return `pending` without a second write; resolving stale Tasks is a
separate Reliability slice. Prior writes without a key cannot be retroactively
deduplicated. This slice does not add Task Recovery, Memory Delete, or Memory
Edit.
