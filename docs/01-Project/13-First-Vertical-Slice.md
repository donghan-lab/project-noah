# First vertical slice: explicit memory save

This slice offers a local HTTP API backed by the existing PostgreSQL Compose service. It uses only an explicit `save_memory` action. The database account in `compose/.env` is read locally and is never sent in API responses. Run the commands from the repository root.

## Setup

```powershell
docker compose --env-file compose/.env -f compose/docker-compose.yml up -d
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m noah init
.venv\Scripts\python -m noah provision-user "Local user"
```

The provisioning command prints a new API token once. Store it privately and set it as `NOAH_API_TOKEN` in your local shell. Do not commit it. The returned user ID is the target for personal memories. To enable project memories, create a project with `.venv\Scripts\python -m noah create-project "Project name" <user-id>`; this grants that user write access.

Start the application:

```powershell
.venv\Scripts\python -m noah serve
```

Send a personal memory request from another shell (replace the target ID):

```powershell
$body = @{ action = 'save_memory'; scope = 'user'; owner_user_id = '<user-id>'; content = 'Remember this explicit note.' } | ConvertTo-Json
Invoke-RestMethod -Uri http://127.0.0.1:8080/memories -Method Post -Headers @{ Authorization = "Bearer $env:NOAH_API_TOKEN" } -ContentType 'application/json' -Body $body
```

Use `scope = 'project'` and `project_id = '<project-id>'` for a project memory. Read a saved memory with `GET /memories/<memory-id>` and the same bearer token. Only its owner or a member of its project may read it. Project writes require a membership with `can_write = true`.

## Execution contract

The API validates a bearer token against a hash stored in PostgreSQL. It then validates the explicit action, content and target, evaluates scope permission, creates a durable Task and execution record, inserts the memory, reads it back and commits a verified result. The write, verification and completion transition share one transaction. A failed write rolls back the memory and records a failed Task and execution. Rejected requests record a failed execution without a Task. If PostgreSQL is unavailable, the API returns 503 and writes a credential-free fallback event to ignored `.noah/failures.jsonl` when local storage is available.

The `users` table represents authenticated human principals, not NOAH's protected Identity Core. Memories remain distinct from Task State, Knowledge and Artifacts. No LLM, Agent runtime, retrieval index or autonomous memory extraction is used in this slice. The API binds to localhost by default; HTTPS and remote deployment are outside this local slice.

Memory writes are non-idempotent in this first slice. The server does not automatically retry them; after an uncertain connection failure, inspect the Task or execution record before sending the request again.

## Tests

```powershell
.venv\Scripts\python -m unittest discover -s tests -v
```

Integration tests need a running PostgreSQL instance configured by `compose/.env`. They create isolated test identities and clean up only their own records.
