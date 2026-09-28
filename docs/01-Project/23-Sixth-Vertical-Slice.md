# M6 first read-only Tool Execution: project document names

M6 adds one capability, `project.documents.list`. An authenticated user asks
for the selected project's document list in natural language. The local model
may propose only `list_project_documents` or `unsupported`; it cannot supply
an OS path. NOAH checks project membership again immediately before the Tool,
reads only direct regular `.md` filenames from an operator-registered root,
verifies the observation, and returns a deterministic answer. No file content
is opened or sent to the model or API response.

## Operator setup on Windows

Use the existing Docker Compose PostgreSQL and token. M6's additive evidence
table is installed by the existing safe initializer; it does not replace or
clear existing rows or the Docker volume.

```powershell
docker compose --env-file compose/.env -f compose/docker-compose.yml ps
.venv\Scripts\python.exe -m noah init
```

The DB currently has no real project or membership. To use M6 manually, an
operator must first create or select a project with the intended user as a
member. `create-project` creates one project and grants its owner membership;
run it only when a new project is intended:

```powershell
.venv\Scripts\python.exe -m noah create-project "My local docs" $env:NOAH_USER_ID
```

Keep the returned project ID. Copy
[`config/project_documents.example.json`](../../config/project_documents.example.json)
to `config/project_documents.local.json`, replace the example UUID with that
project ID, and set `document_root` to the **absolute path of its approved
document directory**. Choose an operator-controlled local directory and a
non-sensitive logical `root_id`. The local mapping is Git-ignored. API users
and the model cannot create or change it. The example's path is a placeholder,
not an operational path. Restart `noah serve` after changing code or mapping.

For Windows PowerShell 5.1, create the local mapping without a UTF-8 BOM.
Replace the project ID and approved directory before running this example:

```powershell
$env:NOAH_PROJECT_ID = '<existing-or-new-project-uuid>'
$projects = @{}
$projects[$env:NOAH_PROJECT_ID] = @{
    root_id = 'my-project-docs'
    document_root = 'C:\APPROVED_PROJECT\docs'
}
$mappingJson = @{ projects = $projects } | ConvertTo-Json -Depth 5
$mappingPath = Join-Path (Get-Location) 'config\project_documents.local.json'
[System.IO.File]::WriteAllText(
    $mappingPath, $mappingJson, [System.Text.UTF8Encoding]::new($false))
```

`Set-Content -Encoding utf8` in Windows PowerShell 5.1 writes a BOM. The
loader accepts UTF-8 with or without a BOM, but the example writes without one
for portability. Keep this machine-specific mapping out of Git.

The dedicated Ollama listener must pass the existing loopback-only check on
`127.0.0.1:11435`. M6 reuses the current `gemma4:12b-it-qat` adapter without
making it a permanent model choice.

## API

```powershell
$body = @{ question = '이 프로젝트의 문서 목록을 보여줘' } | ConvertTo-Json
$headers = @{ Authorization = "Bearer $env:NOAH_API_TOKEN" }
Invoke-RestMethod -Uri "http://127.0.0.1:8080/projects/$env:NOAH_PROJECT_ID/documents/query" `
    -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body $body
```

Windows PowerShell 5.1 can replace Korean characters when sending a string
body without an explicit UTF-8 charset. The identical Korean question above
passed the user's M6 manual verification after `charset=utf-8` was specified.

`NOAH_USER_ID`, `NOAH_API_TOKEN`, and `NOAH_PROJECT_ID` are local session
values. Do not paste token values into source or a report. The body accepts
only `question` (1–500 characters); OS path and directory fields are rejected.
The route returns `files`, `count`, `truncated`, Task/Execution IDs, and an
evidence reference with `root_id`, observation time, and result SHA-256. At
most **50** filenames are returned, sorted by case-folded name then exact
name. `truncated: true` means additional eligible names existed. An empty
directory returns a successful empty list. Names represent an observation at
that time, not a promise that the directory will remain unchanged.

## Durable execution boundary

The service authenticates and checks membership before the model sees the
question. It validates the model's exact one-field intent, resolves the
operator mapping, and rechecks the token and membership before reserving a
Task and `project.documents.list` Execution Record. A stoppable local worker
enumerates the fixed root without recursion or following symlinks. NOAH
independently re-enumerates and compares the bounded result. Membership is
checked again before the response can include filenames.

Successful Tool evidence, `completed/passed` Task, and `succeeded` Execution
commit together. The [additive evidence table](../../database/003_document_tool_evidence.sql)
stores execution/project IDs, logical root ID, observation time, sorted names,
count, truncation, and a hash of canonical metadata. It has no absolute path
or file body. Application code inserts evidence once and has no update/delete
route. Test-owned evidence is removed during synthetic test cleanup.

Definite Tool failure marks its Task and Execution failed. If worker
termination or database commit outcome cannot be confirmed, NOAH returns an
unknown-outcome failure and does not invent a terminal state. Pre-Tool
rejections have a structured response without a new Task/Execution. Existing
M4 keys apply only to `memory.save`; M5 Triage still inspects only
`memory.save` and cannot recover M6 records. A new document listing is a new
observation, not a replay of an old result.

## Security boundary and limits

The Tool accepts only an operator-mapped absolute root; client and model
inputs contain no path. It rejects roots that are links/reparse points and
checks ancestor components, skips direct children that are non-regular,
hidden, dot-prefixed, linked/reparse, or not `.md`, and never traverses a
child directory. It invokes no Shell and performs no file write. Error
responses contain safe codes rather than the absolute path, token, DB
password, or file body.

The M6 guarantee addresses path escape caused by remote input, the model,
or an API user. It does **not** guarantee containment against a malicious
local process running as the same Windows user that changes directory links
between checks and enumeration. Stronger protection would require an OS
access boundary or handle-based traversal and is a later security task.
