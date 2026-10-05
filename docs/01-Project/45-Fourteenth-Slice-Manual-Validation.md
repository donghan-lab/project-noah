# M14 Controlled Memory Suppression — manual HTTP E2E runbook

> **Status: PASSED (executed 2026-10-06).** This is a Windows PowerShell 5.1 operator procedure
> for the uncommitted M14 working tree based on contract commit
> `11844fd9b4116ba0c1ccd37328f401da7a1b3b23`. The operator result is
> recorded below. Run one block at a time. Window A retains variables and runs
> checks; window B runs the NOAH server. **No Ollama window is needed.**
> On any unexpected result, **STOP**, preserve window A and the captured
> response, and investigate with read-only checks. Never resend an uncertain
> suppression request or start cleanup by assumption. Do not rerun the
> preflight block: it initializes the one-shot request guards only once.

## Planned HTTP requests and boundaries

| Order | Request | Mutation | Purpose |
| --- | --- | --- | --- |
| 1 | `GET /memories/<id>` | No | Active management object and exact synthetic content. |
| 2 | `GET /memories?scope=user&limit=100` | No | Active list item and its state fields. |
| 3 | `POST /memories/<id>/suppress` with exactly `{}` | **Yes — once only** | First verified transition. |
| 4 | `GET /memories/<id>` | No | Retained content and persisted suppression state. |
| 5 | `GET /memories?scope=user&limit=100` | No | Exclusion from a new normal list query. |
| 6 | Same suppression POST with `{}` | **Yes — once only, after DB proof** | Deliberate `already_suppressed` no-op. |

The second POST is a planned state-contract check **only after** the first
response and DB transaction are proved. It is not a retry of an uncertain
request. There are **six planned HTTP requests, exactly two mutations**.
Fixture creation is one direct, owned PostgreSQL transaction, not an M1/M4
HTTP save. The production `search_memories()` service is also checked
**read-only** with the synthetic term before and after suppression; it calls
neither HTTP nor Ollama. There is no model-free Memory search HTTP endpoint.
Do not add `POST /memories/query` or a dedicated Ollama instance to this run.

The M14 API contract is: first and repeat both HTTP 200 with top-level
`status=succeeded`. The first has `outcome=suppressed` and non-null new
`task_id`/`execution_id`; the repeat has `outcome=already_suppressed`, the
original `suppressed_at`, a new `request_id`, and null Task/Execution IDs.
Both include `memory_id` and the persisted ISO timestamp, never content.
Owner `GET /memories/<id>` returns a `memory` object containing the original
content and `suppressed`/`suppressed_at`. List items have the same state fields;
`next_cursor` is null for this one-row synthetic user. Structured failures
include `INVALID_TARGET`, `INVALID_REQUEST`, `UNAUTHENTICATED`,
`MEMORY_NOT_FOUND`, `UNSUPPORTED_SCOPE`, `SUPPRESSION_FAILED`,
`VERIFICATION_FAILED`, `DATABASE_UNAVAILABLE`, and
`SUPPRESSION_OUTCOME_UNKNOWN`. The last is HTTP 503 with
`status=failed`, `outcome=unknown`, and null Task/Execution IDs; it does
**not** prove that the mutation failed. Do not inject failures here.

No existing user or Memory is used. Do not print tokens, DB credentials,
private row values, or the snapshot JSON. Do not run Factory Reset,
`docker compose down -v`, volume pruning, broad DELETE, recursive filesystem
cleanup, or `python -m noah init`. No local fixture file or mapping is created.

## 1. Window A — working tree, listeners, PostgreSQL, and volume

Run this before creating anything. The expected Git paths include this new
runbook and the fourteen M14 implementation/validation files. If the
working tree has another path, **STOP** and review it; do not reset it.

```powershell
$ErrorActionPreference = 'Stop'
if ($RunbookInitialized) { throw 'This runbook already started in window A; STOP' }
$RunbookInitialized = $true
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python missing; STOP' }
if ((git branch --show-current) -ne 'main' -or $LASTEXITCODE -ne 0) {
    throw 'Unexpected Git branch; STOP'
}
if ((git rev-parse HEAD) -ne '11844fd9b4116ba0c1ccd37328f401da7a1b3b23' -or
    $LASTEXITCODE -ne 0) { throw 'Unexpected M14 contract baseline; STOP' }
$ExpectedPaths = @(
    'database/010_memory_suppression.sql',
    'docs/01-Project/43-Fourteenth-Vertical-Slice.md',
    'docs/01-Project/44-Fourteenth-Slice-Validation.md',
    'docs/01-Project/45-Fourteenth-Slice-Manual-Validation.md',
    'docs/01-Project/NOAH_DEV_STATUS.md',
    'docs/02-Architecture/Runtime/State.md',
    'noah/__main__.py','noah/capability_route.py','noah/db.py',
    'noah/memory_query.py','noah/memory_suppression.py','noah/service.py',
    'tests/test_capability_route.py','tests/test_memory_suppression.py',
    'tests/test_routing_audit.py'
) | Sort-Object
$GitBefore = @(git status --short)
if ($LASTEXITCODE -ne 0) { throw 'Git status failed; STOP' }
$ActualPaths = @(git status --porcelain=v1 |
    ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if ($LASTEXITCODE -ne 0 -or
    ($ActualPaths -join '|') -ne ($ExpectedPaths -join '|')) {
    throw 'Unexpected working-tree path; STOP'
}
foreach ($Relative in @('noah\memory_suppression.py',
    'database\010_memory_suppression.sql',
    'docs\01-Project\43-Fourteenth-Vertical-Slice.md')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repo $Relative))) {
        throw "Required M14 file missing: $Relative; STOP"
    }
}
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 is occupied; STOP'
}
$PgInfo = @(docker inspect noah-postgres | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or $PgInfo.Count -ne 1 -or
    $PgInfo[0].State.Status -ne 'running' -or
    $PgInfo[0].Config.Image -ne 'postgres:17') {
    throw 'Compose PostgreSQL 17 container is not running; STOP'
}
docker exec noah-postgres pg_isready -q
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL is not ready; STOP' }
function Get-NoahVolumeIdentity {
    $Info = @(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1) {
        throw 'PostgreSQL inspection failed; STOP'
    }
    $Volumes = @($Info[0].Mounts |
        Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" } | Sort-Object)
    if ($Volumes.Count -ne 1) { throw 'Expected one named volume; STOP' }
    return $Volumes[0]
}
$VolumeBefore = Get-NoahVolumeIdentity
if ($VolumeBefore -ne 'noah_noah-postgres-data|/var/lib/postgresql/data') {
    throw 'Unexpected PostgreSQL named volume; STOP'
}
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
$MappingExistedBefore = Test-Path -LiteralPath $Mapping
$MappingHashBefore = if ($MappingExistedBefore) {
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash
} else { $null }
$FirstSuppressionSent = $false
$FirstVerified = $false
$RepeatSuppressionSent = $false
$RepeatVerified = $false
$CleanupAttempted = $false
$FixtureAttempted = $false
$ActiveDirectSent = $false
$ActiveListSent = $false
$SuppressedDirectSent = $false
$SuppressedListSent = $false
$FirstResponse = $null
$RepeatResponse = $null
Write-Output 'M14 working tree, free 8080, PostgreSQL 17, and named volume confirmed'
```

Expected: the single confirmation line. The next block is allowed only after
all guards pass. Keep window A open through cleanup. An existing local mapping
is observed and hashed, never overwritten.

## 2. Window A — private read-only 18-table baseline and migration

This snapshot uses one repeatable-read, read-only transaction. It retains
complete-row SHA-256 fingerprints and each existing Memory's suppression
state in **window A variables only**; it prints no rows, IDs, or hashes.
Passing multiline Python by stdin avoids PowerShell 5.1 quoting damage.

```powershell
$SnapshotCode = @'
import hashlib, json
from noah.db import connect
tables = [
 'users','api_tokens','memories','tasks','execution_records','memory_write_requests',
 'projects','project_memberships','document_tool_evidence','document_read_evidence',
 'document_answer_evidence','selected_document_answer_evidence',
 'selected_document_source_evidence','selected_document_quote_evidence',
 'auto_document_answer_evidence','auto_document_source_evidence',
 'auto_document_quote_evidence','routing_audit'
]
out = {'tables': {}}
with connect() as db:
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    version = db.execute('SHOW server_version').fetchone()['server_version']
    if not version.startswith('17.'):
        raise RuntimeError('PostgreSQL 17 required; STOP')
    actual = [r['tablename'] for r in db.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='noah' ORDER BY tablename")]
    if sorted(actual) != sorted(tables):
        raise RuntimeError('NOAH table set changed; STOP')
    column = db.execute("""SELECT data_type,is_nullable,column_default
        FROM information_schema.columns WHERE table_schema='noah'
          AND table_name='memories' AND column_name='suppressed_at'""").fetchone()
    if (column is None or column['data_type'] != 'timestamp with time zone'
            or column['is_nullable'] != 'YES'):
        raise RuntimeError('M14 migration 010 not confirmed; STOP')
    for name in tables:
        rows = db.execute('SELECT * FROM noah.' + name).fetchall()
        hashes = sorted(hashlib.sha256(json.dumps(row, sort_keys=True,
            default=str, ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count': len(rows), 'rows': hashes}
    out['suppression'] = sorted([
        (str(r['id']), r['suppressed_at'].isoformat() if r['suppressed_at'] else None)
        for r in db.execute('SELECT id,suppressed_at FROM noah.memories')])
    out['suppressed_count'] = sum(value is not None for _, value in out['suppression'])
    for name in ('tasks','execution_records'):
        out['running_' + name] = db.execute(
            "SELECT count(*) AS n FROM noah." + name + " WHERE status='running'").fetchone()['n']
print(json.dumps(out, sort_keys=True, separators=(',', ':')))
'@
function Get-NoahSnapshot {
    $Value = $SnapshotCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $Value) {
        throw 'Read-only snapshot failed; STOP'
    }
    return [string]$Value
}
function Assert-M14Delta($CurrentJson, $Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Extra)) {
            throw "Unexpected DB row count in $Name; STOP"
        }
        $AfterHashes = @($Current.tables.PSObject.Properties[$Name].Value.rows)
        foreach ($OldHash in @($Property.Value.rows)) {
            if ($AfterHashes -notcontains $OldHash) {
                throw "An existing $Name row changed; STOP"
            }
        }
    }
    if ($Current.running_tasks -ne 0 -or
        $Current.running_execution_records -ne 0) {
        throw 'Running Task/Execution exists; STOP'
    }
}
$BaselineJson = Get-NoahSnapshot
$Baseline = $BaselineJson | ConvertFrom-Json
$Expected = @{ users=1; api_tokens=1; memories=2; tasks=2; execution_records=3;
    memory_write_requests=1; projects=0; project_memberships=0; routing_audit=0;
    document_tool_evidence=0; document_read_evidence=0; document_answer_evidence=0;
    selected_document_answer_evidence=0; selected_document_source_evidence=0;
    selected_document_quote_evidence=0; auto_document_answer_evidence=0;
    auto_document_source_evidence=0; auto_document_quote_evidence=0 }
foreach ($Name in $Expected.Keys) {
    if ($Baseline.tables.PSObject.Properties[$Name].Value.count -ne $Expected[$Name]) {
        throw "Unexpected baseline count in $Name; STOP"
    }
}
if ($Baseline.running_tasks -ne 0 -or
    $Baseline.running_execution_records -ne 0) {
    throw 'Pre-existing running Task/Execution; STOP'
}
if ($Baseline.suppressed_count -ne 0) {
    throw 'Existing suppression state differs from expected baseline; STOP'
}
Write-Output 'Migration 010 and private 18-table baseline confirmed'
```

Expected: one confirmation line; no private data. A changed baseline is a
**STOP**, not a reason to initialize or reset PostgreSQL.

## 3. Window A — one synthetic user, token, and active Memory

This one DB transaction creates **only** a synthetic user, token hash, and
user-scope Memory. It deliberately bypasses M1 HTTP save so no fixture Task,
Execution, M4 key mapping, or Ollama call is mixed with M14 behavior. It
checks the new Memory is active before committing. Retain the random token
only in window A; do not print it.

```powershell
if ($FixtureAttempted) { throw 'Fixture transaction already attempted; STOP' }
$FixtureAttempted = $true
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m14-manual-$RunId"
$MemoryText = "M14 공개 합성 메모 $RunId. 검증 대상은 수달이다."
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $TokenBytes = New-Object byte[] 32
    $Rng.GetBytes($TokenBytes)
    $TestToken = [Convert]::ToBase64String($TokenBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
} finally {
    if ($TokenBytes) { [Array]::Clear($TokenBytes, 0, $TokenBytes.Length) }
    $Rng.Dispose()
}
$SetupCode = @'
import hashlib, json, os, re
from uuid import uuid4
from noah.db import connect
label = os.environ['NOAH_M14_LABEL']
text = os.environ['NOAH_M14_CONTENT']
token = os.environ['NOAH_M14_TOKEN']
if not re.fullmatch(r'm14-manual-[0-9a-f]{32}', label):
    raise RuntimeError('Synthetic label invalid; STOP')
if label[-32:] not in text or not text.strip() or len(text) > 10000:
    raise RuntimeError('Synthetic content invalid; STOP')
if len(token) < 32:
    raise RuntimeError('Synthetic token invalid; STOP')
user_id, memory_id = uuid4(), uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES (%s,%s)', (user_id,label))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES (%s,%s)',
        (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
    db.execute("""INSERT INTO noah.memories
        (id,owner_user_id,scope,content,created_by)
        VALUES (%s,%s,'user',%s,%s)""",(memory_id,user_id,text,user_id))
    row = db.execute("""SELECT scope,owner_user_id,created_by,project_id,
        content,provenance,suppressed_at FROM noah.memories WHERE id=%s""",
        (memory_id,)).fetchone()
    if (row is None or row['scope'] != 'user' or row['owner_user_id'] != user_id
            or row['created_by'] != user_id or row['project_id'] is not None
            or row['content'] != text or row['provenance'] != 'explicit_user_request'
            or row['suppressed_at'] is not None):
        raise RuntimeError('Synthetic readback failed; transaction rolls back')
    item = db.execute("""SELECT (to_jsonb(m)-'suppressed_at')::text AS item
        FROM noah.memories m WHERE m.id=%s""",(memory_id,)).fetchone()['item']
print(json.dumps({'user_id':str(user_id),'memory_id':str(memory_id),
    'original_fingerprint':hashlib.sha256(item.encode('utf-8')).hexdigest()}))
'@
$env:NOAH_M14_LABEL = $RunLabel
$env:NOAH_M14_CONTENT = $MemoryText
$env:NOAH_M14_TOKEN = $TestToken
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) {
        throw 'Fixture transaction unconfirmed; STOP'
    }
} finally {
    Remove-Item Env:NOAH_M14_LABEL,Env:NOAH_M14_CONTENT,Env:NOAH_M14_TOKEN -ErrorAction SilentlyContinue
}
$Fixture = $FixtureJson | ConvertFrom-Json
$UserId = [string]$Fixture.user_id
$MemoryId = [string]$Fixture.memory_id
$MemoryFingerprintBefore = [string]$Fixture.original_fingerprint
$AfterFixtureJson = Get-NoahSnapshot
Assert-M14Delta $AfterFixtureJson @{ users=1; api_tokens=1; memories=1 }
Write-Output 'One owned synthetic user/token/active Memory created'
```

Expected: only the safe confirmation line. If the fixture transaction or
snapshot is uncertain, **STOP**; do not run a presumed cleanup. No local file,
project, document mapping, key, or fixture Execution was created.

Define this **read-only** owner/state verifier once in window A. It checks
actual DB ownership, the token hash, unchanged original Memory fields, zero
unrelated owned records, and the production SQL search service without a
model. It never prints the token or content.

```powershell
$VerifyCode = @'
import hashlib, os, sys
from datetime import datetime
from uuid import UUID, uuid4
from noah.db import connect
from noah.service import search_memories
mode = sys.argv[1]
if mode not in ('active','suppressed'):
    raise RuntimeError('Invalid verification mode; STOP')
user = UUID(os.environ['NOAH_M14_USER'])
memory = UUID(os.environ['NOAH_M14_MEMORY'])
token = os.environ['NOAH_M14_TOKEN']
text = os.environ['NOAH_M14_CONTENT']
label = os.environ['NOAH_M14_LABEL']
fingerprint = os.environ['NOAH_M14_FINGERPRINT']
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    owner = db.execute('SELECT label FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens = db.execute("""SELECT token_hash,revoked_at FROM noah.api_tokens
        WHERE user_id=%s""",(user,)).fetchall()
    row = db.execute('SELECT * FROM noah.memories WHERE id=%s',(memory,)).fetchone()
    item = db.execute("""SELECT (to_jsonb(m)-'suppressed_at')::text AS item
        FROM noah.memories m WHERE m.id=%s""",(memory,)).fetchone()
    tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT * FROM noah.execution_records WHERE actor_user_id=%s',
        (user,)).fetchall()
    mappings = db.execute("""SELECT count(*) AS n FROM noah.memory_write_requests
        WHERE actor_user_id=%s""",(user,)).fetchone()['n']
    audits = db.execute("""SELECT count(*) AS n FROM noah.routing_audit
        WHERE actor_user_id=%s""",(user,)).fetchone()['n']
    memberships = db.execute("""SELECT count(*) AS n FROM noah.project_memberships
        WHERE user_id=%s""",(user,)).fetchone()['n']
if (owner is None or owner['label'] != label or len(tokens) != 1
        or tokens[0]['token_hash'] != hashlib.sha256(token.encode()).hexdigest()
        or tokens[0]['revoked_at'] is not None or row is None or item is None
        or row['scope'] != 'user' or row['owner_user_id'] != user
        or row['created_by'] != user or row['project_id'] is not None
        or row['content'] != text or row['provenance'] != 'explicit_user_request'
        or hashlib.sha256(item['item'].encode()).hexdigest() != fingerprint
        or mappings != 0 or audits != 0 or memberships != 0):
    raise RuntimeError('Synthetic ownership/original fields mismatch; STOP')
if mode == 'active':
    if row['suppressed_at'] is not None or tasks or executions:
        raise RuntimeError('Fixture is not active and record-free; STOP')
else:
    expected_at = datetime.fromisoformat(os.environ['NOAH_M14_SUPPRESSED_AT'])
    if row['suppressed_at'] != expected_at or len(tasks) != 1 or len(executions) != 1:
        raise RuntimeError('Suppression state/count mismatch; STOP')
    task, execution = tasks[0], executions[0]
    if (str(task['id']) != os.environ['NOAH_M14_TASK']
            or task['actor_user_id'] != user
            or task['goal'] != 'Suppress explicitly selected user memory'
            or task['status'] != 'completed'
            or task['verification_status'] != 'passed'
            or str(execution['id']) != os.environ['NOAH_M14_EXECUTION']
            or str(execution['request_id']) != os.environ['NOAH_M14_REQUEST']
            or execution['actor_user_id'] != user
            or execution['task_id'] != task['id']
            or execution['memory_id'] != memory
            or execution['capability'] != 'memory.suppress'
            or execution['status'] != 'succeeded'
            or execution['verified_at'] is None):
        raise RuntimeError('M14 Task/Execution correlation invalid; STOP')
status, result = search_memories(token, 'user', (label[-32:],), uuid4())
if status != 200:
    raise RuntimeError('Read-only production search unavailable; STOP')
found = [m for m in result['memories'] if m['id'] == str(memory)]
if mode == 'active':
    if len(found) != 1 or found[0]['suppressed'] is not False:
        raise RuntimeError('Active Memory absent from search; STOP')
elif found:
    raise RuntimeError('Suppressed Memory present in search; STOP')
print('Synthetic ownership, state, records, and model-free SQL search verified')
'@
function Invoke-M14Verify([string]$Mode) {
    $env:NOAH_M14_USER = $UserId
    $env:NOAH_M14_MEMORY = $MemoryId
    $env:NOAH_M14_TOKEN = $TestToken
    $env:NOAH_M14_CONTENT = $MemoryText
    $env:NOAH_M14_LABEL = $RunLabel
    $env:NOAH_M14_FINGERPRINT = $MemoryFingerprintBefore
    $env:NOAH_M14_SUPPRESSED_AT = if ($FirstResponse) {
        $FirstSuppressedAtIso
    } else { '' }
    $env:NOAH_M14_TASK = if ($FirstResponse) {
        [string]$FirstResponse.task_id
    } else { '' }
    $env:NOAH_M14_EXECUTION = if ($FirstResponse) {
        [string]$FirstResponse.execution_id
    } else { '' }
    $env:NOAH_M14_REQUEST = if ($FirstResponse) {
        [string]$FirstResponse.request_id
    } else { '' }
    try {
        $VerifyCode | & $Python - $Mode
        if ($LASTEXITCODE -ne 0) { throw 'Read-only M14 verifier failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M14_USER,Env:NOAH_M14_MEMORY,Env:NOAH_M14_TOKEN,Env:NOAH_M14_CONTENT,Env:NOAH_M14_LABEL,Env:NOAH_M14_FINGERPRINT,Env:NOAH_M14_SUPPRESSED_AT,Env:NOAH_M14_TASK,Env:NOAH_M14_EXECUTION,Env:NOAH_M14_REQUEST -ErrorAction SilentlyContinue
    }
}
Invoke-M14Verify active
```

Expected: the verifier confirmation. It may be rerun against the captured
state if only the verifier is corrected; it sends **no HTTP mutation**.
Proceed only if this and the fixture snapshot pass.

## 4. Window B — start the working-tree NOAH server

Run **only in window B**. Do not call `noah init` and do not start Ollama.

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

Expected: the process stays running. In window A, confirm its loopback-only
listener and retain its process ID before the first HTTP request.

```powershell
$ServerListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ServerListeners.Count -ne 1 -or
    $ServerListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'Current NOAH server is not exclusively on 127.0.0.1:8080; STOP'
}
$ServerPid = $ServerListeners[0].OwningProcess
$BaseUri = 'http://127.0.0.1:8080'
$Headers = @{ Authorization = 'Bearer ' + $TestToken }
function Get-NoahIsoTimestamp([string]$JsonBody) {
    # ConvertFrom-Json can turn ISO strings into local DateTime objects.
    $Match = [regex]::Match($JsonBody, '"suppressed_at"\s*:\s*"([^"\\]+)"')
    if (-not $Match.Success) { throw 'Missing raw ISO suppression timestamp; STOP' }
    [void][datetimeoffset]::Parse($Match.Groups[1].Value,
        [System.Globalization.CultureInfo]::InvariantCulture)
    return $Match.Groups[1].Value
}
Write-Output 'Current working-tree NOAH server is listening on loopback'
```

Expected: one safe line. Port ownership or binding mismatch means **STOP**.

## 5. Active direct GET and list — two read-only HTTP requests

These blocks are each run **once**. They must create no durable DB delta.
PowerShell 5.1 uses the server's JSON UTF-8 charset when decoding responses.
Do not print `$Headers`, a token, or response bodies.

```powershell
if ($ActiveDirectSent) { throw 'Active direct GET already sent; STOP' }
$ActiveDirectSent = $true
try {
    $ActiveRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories/$MemoryId" -TimeoutSec 15
    $Active = $ActiveRaw.Content | ConvertFrom-Json
} catch { throw 'Active direct GET failed; STOP without fixture cleanup' }
if ($ActiveRaw.StatusCode -ne 200 -or $Active.status -ne 'succeeded' -or
    $Active.memory.id -ne $MemoryId -or
    $Active.memory.owner_user_id -ne $UserId -or
    $Active.memory.scope -ne 'user' -or
    $Active.memory.content -cne $MemoryText -or
    $Active.memory.suppressed -ne $false -or
    $null -ne $Active.memory.suppressed_at) {
    throw 'Active direct Memory object mismatch; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFixtureJson) {
    throw 'Direct GET changed the DB; STOP'
}
Write-Output 'Active direct GET: HTTP 200, exact content, false/null, DB delta zero'
```

Expected: one confirmation. Only then send the active list request:

```powershell
if ($ActiveListSent) { throw 'Active list GET already sent; STOP' }
$ActiveListSent = $true
try {
    $ListRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories?scope=user&limit=100" -TimeoutSec 15
    $ActiveList = $ListRaw.Content | ConvertFrom-Json
} catch { throw 'Active list GET failed; STOP' }
$ActiveItems = @($ActiveList.memories)
if ($ListRaw.StatusCode -ne 200 -or $ActiveList.status -ne 'succeeded' -or
    $ActiveItems.Count -ne 1 -or $ActiveItems[0].id -ne $MemoryId -or
    $ActiveItems[0].content -cne $MemoryText -or
    $ActiveItems[0].suppressed -ne $false -or
    $null -ne $ActiveItems[0].suppressed_at -or
    $null -ne $ActiveList.next_cursor) {
    throw 'Active list response or cursor mismatch; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFixtureJson) {
    throw 'Active list changed the DB; STOP'
}
Write-Output 'Active list GET: one active item, false/null, null cursor, DB delta zero'
```

Expected: one synthetic list item and null cursor. This does not claim
multi-page snapshot isolation; existing automated tests cover pagination.

## 6. First suppression — **EXACTLY ONCE; NEVER RE-RUN**

Immediately before the mutating request, prove the current snapshot, owner,
volume, and server are still the ones above. Set the one-shot flag **before**
the network call. If transport fails, times out, produces an unexpected body,
or returns `SUPPRESSION_OUTCOME_UNKNOWN`, **STOP**. Preserve the captured
`$FirstRaw`/`$FirstResponse` if available; inspect only with read-only DB
queries. Never resend the POST or proceed to the deliberate repeat.

```powershell
if ($FirstSuppressionSent -or -not $ActiveDirectSent -or -not $ActiveListSent) {
    throw 'First suppression precondition/one-shot guard failed; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFixtureJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before first suppression; STOP'
}
Invoke-M14Verify active
$ServerListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ServerListeners.Count -ne 1 -or
    $ServerListeners[0].OwningProcess -ne $ServerPid -or
    $ServerListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'NOAH server changed before first suppression; STOP'
}
$FirstSuppressionSent = $true
$EmptyJsonBytes = [System.Text.Encoding]::UTF8.GetBytes('{}')
try {
    $FirstRaw = Invoke-WebRequest -UseBasicParsing -Method Post -Headers $Headers -ContentType 'application/json; charset=utf-8' -Body $EmptyJsonBytes -Uri "$BaseUri/memories/$MemoryId/suppress" -TimeoutSec 30
    $FirstResponse = $FirstRaw.Content | ConvertFrom-Json
    $FirstSuppressedAtIso = Get-NoahIsoTimestamp $FirstRaw.Content
} catch {
    throw 'First suppression HTTP result unconfirmed; STOP, do not resend'
}
if ($FirstRaw.StatusCode -ne 200 -or
    $FirstResponse.status -ne 'succeeded' -or
    $FirstResponse.outcome -ne 'suppressed' -or
    $FirstResponse.memory_id -ne $MemoryId -or
    -not $FirstSuppressedAtIso -or
    -not $FirstResponse.request_id -or
    -not $FirstResponse.task_id -or
    -not $FirstResponse.execution_id) {
    throw 'First suppression result unexpected or uncertain; STOP, do not resend'
}
foreach ($Value in @($FirstResponse.request_id,
    $FirstResponse.task_id,$FirstResponse.execution_id)) {
    $ParsedUuid = [guid]::Empty
    if (-not [guid]::TryParse([string]$Value,[ref]$ParsedUuid)) {
        throw 'First suppression correlation ID invalid; STOP'
    }
}
Write-Output 'First suppression HTTP 200 with verified response shape; DB proof is next'
```

The one safe line confirms **response shape only**. Do not send any other
mutation until the DB proof below passes.

## 7. Read-only DB proof of first transition

The verifier reselects the retained Memory, compares its persisted timestamp
with the API value, checks unchanged original fields, and proves exactly one
terminal `memory.suppress` Task/Execution with the returned IDs and actor.
The full snapshot proves only users/token/Memory fixture plus **Task +1,
Execution +1**; M4 mapping, Routing Audit, M6–M13 evidence, and all existing
private rows remain unchanged. No Task or Execution remains running.

```powershell
if (-not $FirstSuppressionSent -or -not $FirstResponse) {
    throw 'No confirmed first response; STOP'
}
Invoke-M14Verify suppressed
$AfterFirstJson = Get-NoahSnapshot
Assert-M14Delta $AfterFirstJson @{
    users=1; api_tokens=1; memories=1; tasks=1; execution_records=1
}
$FirstVerified = $true
Write-Output 'One retained suppressed Memory and one verified M14 Task/Execution; unrelated delta zero'
```

Expected: owner/content/original fingerprint unchanged, response timestamp
equal to DB timestamp, matching Task/Execution, no M4/audit/evidence change,
and zero running records. If a verifier has a syntax or comparison error,
correct **only the read-only verifier** against the captured response and DB;
do not send the POST again.

## 8. Suppressed direct GET and normal list — two read-only HTTP requests

The direct management GET must still return the exact original body. A new
normal list must omit the target. Both requests leave the snapshot unchanged.

```powershell
if (-not $FirstVerified -or $SuppressedDirectSent) {
    throw 'Suppressed direct GET precondition/one-shot guard failed; STOP'
}
$SuppressedDirectSent = $true
try {
    $DirectRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories/$MemoryId" -TimeoutSec 15
    $Direct = $DirectRaw.Content | ConvertFrom-Json
    $DirectSuppressedAtIso = Get-NoahIsoTimestamp $DirectRaw.Content
} catch { throw 'Suppressed direct GET failed; STOP' }
if ($DirectRaw.StatusCode -ne 200 -or $Direct.status -ne 'succeeded' -or
    $Direct.memory.id -ne $MemoryId -or
    $Direct.memory.content -cne $MemoryText -or
    $Direct.memory.suppressed -ne $true -or
    $DirectSuppressedAtIso -ne $FirstSuppressedAtIso) {
    throw 'Suppressed direct management object mismatch; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFirstJson) {
    throw 'Suppressed direct GET changed DB; STOP'
}
Write-Output 'Suppressed direct GET: retained exact content and persisted true/timestamp'
```

Expected: HTTP 200, original content, `true` and the exact persisted
timestamp. Only then send the list GET:

```powershell
if (-not $FirstVerified -or $SuppressedListSent) {
    throw 'Suppressed list GET precondition/one-shot guard failed; STOP'
}
$SuppressedListSent = $true
try {
    $ListRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories?scope=user&limit=100" -TimeoutSec 15
    $SuppressedList = $ListRaw.Content | ConvertFrom-Json
} catch { throw 'Suppressed list GET failed; STOP' }
if ($ListRaw.StatusCode -ne 200 -or $SuppressedList.status -ne 'succeeded' -or
    @($SuppressedList.memories | Where-Object { $null -ne $_ }).Count -ne 0 -or
    $null -ne $SuppressedList.next_cursor) {
    throw 'Suppressed Memory appeared in normal list or cursor invalid; STOP'
}
Invoke-M14Verify suppressed
if ((Get-NoahSnapshot) -ne $AfterFirstJson) {
    throw 'Suppressed list/search verification changed DB; STOP'
}
Write-Output 'New normal list and model-free SQL search exclude the suppressed Memory'
```

Expected: empty list, null cursor, production model-free search omits the
Memory, and durable DB delta zero. `POST /memories/query` is deliberately
not called: it would require Ollama, while the suppression/search boundary
and M3/M11 races already have automated coverage.

## 9. Deliberate repeat — **EXACTLY ONCE AFTER VERIFIED FIRST RESULT**

This is not a retry. It is a separate request after sections 7–8 pass and the
first mutation was proved durable. Set its one-shot flag before the network
call. Any unexpected or uncertain result is a **STOP**, with no resend.

```powershell
if (-not $FirstVerified -or -not $SuppressedDirectSent -or
    -not $SuppressedListSent -or $RepeatSuppressionSent) {
    throw 'Repeat precondition/one-shot guard failed; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFirstJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before deliberate repeat; STOP'
}
Invoke-M14Verify suppressed
$RepeatSuppressionSent = $true
try {
    $RepeatRaw = Invoke-WebRequest -UseBasicParsing -Method Post -Headers $Headers -ContentType 'application/json; charset=utf-8' -Body $EmptyJsonBytes -Uri "$BaseUri/memories/$MemoryId/suppress" -TimeoutSec 30
    $RepeatResponse = $RepeatRaw.Content | ConvertFrom-Json
    $RepeatSuppressedAtIso = Get-NoahIsoTimestamp $RepeatRaw.Content
} catch {
    throw 'Repeat suppression HTTP result unconfirmed; STOP, do not resend'
}
$RepeatId = [guid]::Empty
if ($RepeatRaw.StatusCode -ne 200 -or
    $RepeatResponse.status -ne 'succeeded' -or
    $RepeatResponse.outcome -ne 'already_suppressed' -or
    $RepeatResponse.memory_id -ne $MemoryId -or
    $RepeatSuppressedAtIso -ne $FirstSuppressedAtIso -or
    -not [guid]::TryParse([string]$RepeatResponse.request_id,[ref]$RepeatId) -or
    $RepeatResponse.request_id -eq $FirstResponse.request_id -or
    $null -ne $RepeatResponse.task_id -or
    $null -ne $RepeatResponse.execution_id) {
    throw 'Repeat response violates already_suppressed contract; STOP'
}
Invoke-M14Verify suppressed
$AfterRepeatJson = Get-NoahSnapshot
if ($AfterRepeatJson -ne $AfterFirstJson) {
    throw 'Repeat changed Memory, Task, Execution, or another DB row; STOP'
}
$RepeatVerified = $true
Write-Output 'Deliberate repeat: HTTP 200, new request ID, same timestamp, no DB delta'
```

Expected: new HTTP `request_id`, original persisted timestamp, null repeat
Task/Execution IDs, and byte-for-byte identical private snapshot. The first
Task/Execution identities remain in `$FirstResponse` only; the repeat does
not replay them. No M4 mapping or Routing Audit was created.

## 10. Stop only the NOAH server; verify exact cleanup ownership

Only after all six HTTP results and both DB proofs pass, press `Ctrl+C` in
**window B**. Do not stop PostgreSQL or any Ollama service. In window A:

```powershell
if (-not $RepeatVerified) { throw 'Manual verification incomplete; STOP' }
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 still has a listener; STOP before cleanup'
}
if ((Get-NoahSnapshot) -ne $AfterRepeatJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before cleanup ownership check; STOP'
}
Write-Output 'NOAH stopped; PostgreSQL and exact post-repeat state retained'
```

Expected: no 8080 listener and unchanged DB/volume. Define a separate
ownership verifier and deletion transaction below. The `verify` mode is
read-only; the `delete` mode rechecks ownership **inside one transaction**
and deletes only exact synthetic IDs in FK order. If any SELECT, count, or
DELETE differs, the transaction rolls back and cleanup stops.

```powershell
$CleanupCode = @'
import hashlib, os, sys
from datetime import datetime
from uuid import UUID
from noah.db import connect
mode = sys.argv[1]
if mode not in ('verify','delete'):
    raise RuntimeError('Invalid cleanup mode; STOP')
user = UUID(os.environ['NOAH_M14_USER'])
memory = UUID(os.environ['NOAH_M14_MEMORY'])
task = UUID(os.environ['NOAH_M14_TASK'])
execution = UUID(os.environ['NOAH_M14_EXECUTION'])
request = UUID(os.environ['NOAH_M14_REQUEST'])
label = os.environ['NOAH_M14_LABEL']
text = os.environ['NOAH_M14_CONTENT']
token_hash = hashlib.sha256(os.environ['NOAH_M14_TOKEN'].encode()).hexdigest()
fingerprint = os.environ['NOAH_M14_FINGERPRINT']
suppressed_at = datetime.fromisoformat(os.environ['NOAH_M14_SUPPRESSED_AT'])
lock = ' FOR UPDATE' if mode == 'delete' else ''
with connect() as db:
    if mode == 'verify':
        db.execute('SET TRANSACTION READ ONLY')
    else:
        db.execute("SET LOCAL lock_timeout = '3s'")
    owner = db.execute('SELECT * FROM noah.users WHERE id=%s' + lock,(user,)).fetchone()
    tokens = db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s' + lock,
        (user,)).fetchall()
    row = db.execute('SELECT * FROM noah.memories WHERE id=%s' + lock,
        (memory,)).fetchone()
    task_rows = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s' + lock,
        (user,)).fetchall()
    execution_rows = db.execute(
        'SELECT * FROM noah.execution_records WHERE actor_user_id=%s' + lock,
        (user,)).fetchall()
    item = db.execute("""SELECT (to_jsonb(m)-'suppressed_at')::text AS item
        FROM noah.memories m WHERE m.id=%s""",(memory,)).fetchone()
    extra = {
        'owned_memories': db.execute("""SELECT count(*) AS n FROM noah.memories
            WHERE owner_user_id=%s OR created_by=%s""",(user,user)).fetchone()['n'],
        'memory_executions': db.execute("""SELECT count(*) AS n
            FROM noah.execution_records WHERE memory_id=%s""",(memory,)).fetchone()['n'],
        'm4': db.execute("""SELECT count(*) AS n FROM noah.memory_write_requests
            WHERE actor_user_id=%s""",(user,)).fetchone()['n'],
        'audit': db.execute("""SELECT count(*) AS n FROM noah.routing_audit
            WHERE actor_user_id=%s""",(user,)).fetchone()['n'],
        'membership': db.execute("""SELECT count(*) AS n FROM noah.project_memberships
            WHERE user_id=%s""",(user,)).fetchone()['n'],
    }
    if (owner is None or owner['label'] != label or len(tokens) != 1
            or tokens[0]['token_hash'] != token_hash or tokens[0]['revoked_at'] is not None
            or row is None or row['scope'] != 'user'
            or row['owner_user_id'] != user or row['created_by'] != user
            or row['project_id'] is not None or row['content'] != text
            or row['suppressed_at'] != suppressed_at or item is None
            or hashlib.sha256(item['item'].encode()).hexdigest() != fingerprint
            or len(task_rows) != 1 or len(execution_rows) != 1
            or extra != {'owned_memories':1,'memory_executions':1,
                         'm4':0,'audit':0,'membership':0}):
        raise RuntimeError('Synthetic cleanup ownership mismatch; rollback/STOP')
    t,e = task_rows[0],execution_rows[0]
    if (t['id'] != task or t['actor_user_id'] != user
            or t['goal'] != 'Suppress explicitly selected user memory'
            or t['status'] != 'completed' or t['verification_status'] != 'passed'
            or e['id'] != execution or e['request_id'] != request
            or e['task_id'] != task or e['actor_user_id'] != user
            or e['memory_id'] != memory or e['capability'] != 'memory.suppress'
            or e['status'] != 'succeeded' or e['verified_at'] is None):
        raise RuntimeError('Task/Execution not owned by this M14 run; rollback/STOP')
    if mode == 'delete':
        def exact_delete(sql, values):
            cursor = db.execute(sql, values)
            if cursor.rowcount != 1:
                raise RuntimeError('Exact DELETE count mismatch; rollback/STOP')
        exact_delete("""DELETE FROM noah.execution_records
            WHERE id=%s AND request_id=%s AND task_id=%s AND actor_user_id=%s
              AND memory_id=%s AND capability='memory.suppress' AND status='succeeded'""",
            (execution,request,task,user,memory))
        exact_delete("""DELETE FROM noah.tasks
            WHERE id=%s AND actor_user_id=%s AND status='completed'
              AND verification_status='passed'""",(task,user))
        exact_delete("""DELETE FROM noah.memories
            WHERE id=%s AND owner_user_id=%s AND created_by=%s AND scope='user'
              AND content=%s AND suppressed_at=%s""",
            (memory,user,user,text,suppressed_at))
        exact_delete("""DELETE FROM noah.api_tokens
            WHERE user_id=%s AND token_hash=%s""",(user,token_hash))
        exact_delete('DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label))
print('Read-only synthetic ownership verified' if mode=='verify' else
      'Only the five synthetic rows removed in one transaction')
'@
function Invoke-M14Cleanup([string]$Mode) {
    $env:NOAH_M14_USER = $UserId
    $env:NOAH_M14_MEMORY = $MemoryId
    $env:NOAH_M14_TASK = [string]$FirstResponse.task_id
    $env:NOAH_M14_EXECUTION = [string]$FirstResponse.execution_id
    $env:NOAH_M14_REQUEST = [string]$FirstResponse.request_id
    $env:NOAH_M14_LABEL = $RunLabel
    $env:NOAH_M14_CONTENT = $MemoryText
    $env:NOAH_M14_TOKEN = $TestToken
    $env:NOAH_M14_FINGERPRINT = $MemoryFingerprintBefore
    $env:NOAH_M14_SUPPRESSED_AT = $FirstSuppressedAtIso
    try {
        $CleanupCode | & $Python - $Mode
        if ($LASTEXITCODE -ne 0) {
            throw 'Synthetic ownership/cleanup transaction failed; STOP'
        }
    } finally {
        Remove-Item Env:NOAH_M14_USER,Env:NOAH_M14_MEMORY,Env:NOAH_M14_TASK,Env:NOAH_M14_EXECUTION,Env:NOAH_M14_REQUEST,Env:NOAH_M14_LABEL,Env:NOAH_M14_CONTENT,Env:NOAH_M14_TOKEN,Env:NOAH_M14_FINGERPRINT,Env:NOAH_M14_SUPPRESSED_AT -ErrorAction SilentlyContinue
    }
}
Invoke-M14Cleanup verify
Write-Output 'Read-only cleanup ownership passed; no DELETE has run'
```

Expected: the read-only ownership confirmation. Only if this succeeds,
run the **separate deletion block exactly once**:

```powershell
if ($CleanupAttempted -or -not $RepeatVerified) {
    throw 'Cleanup already attempted or verification incomplete; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterRepeatJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before cleanup transaction; STOP'
}
$CleanupAttempted = $true
Invoke-M14Cleanup delete
$AfterCleanupJson = Get-NoahSnapshot
if ($AfterCleanupJson -ne $BaselineJson) {
    throw 'Original private baseline not exactly restored; STOP'
}
Write-Output 'All original 18-table counts, fingerprints, and suppression states restored'
```

Expected: only this run's **one user, one token, one Memory, one M14 Task,
and one M14 Execution** removed in one transaction. All five DELETE counts
must equal 1. No M4 mapping, routing audit, project, membership, evidence,
existing user/Memory/Task/Execution, or named volume is deleted. If the
cleanup transaction fails or commit acknowledgement is uncertain, **STOP**;
do not repeat deletion without a fresh ownership audit.

## 11. Final restoration and operator record

There are no local fixture files to remove. Confirm the mapping's original
existence/hash, named volume, all private DB row fingerprints and original
suppression states, running counts, and Git working tree are identical to
preflight. Then clear the synthetic token from window A.

```powershell
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -ne $MappingExistedBefore -or
    ($MappingExistedBefore -and
     (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHashBefore)) {
    throw 'Final DB/volume/mapping restoration failed; STOP'
}
$GitAfter = @(git status --short)
if ($LASTEXITCODE -ne 0 -or
    ($GitAfter -join "|") -ne ($GitBefore -join "|")) {
    throw 'Working tree changed during manual run; STOP'
}
$TestToken = $null
$Headers = $null
$EmptyJsonBytes = $null
Write-Output 'DB baseline restored; volume, mapping, and working tree unchanged'
```

Expected: one safe confirmation. Leave PostgreSQL and any existing Ollama
service running; this procedure started no Ollama process. An unexpected
result at any earlier stage is recorded and reviewed separately rather than
being relabeled as a pass.

### Operator result record

**Status: PASSED (2026-10-06).** The operator completed the procedure and recorded the results below.
Do not paste a token, password, private Memory body, row fingerprint, or
raw exception that may contain a credential into the record.

| Check | Result |
| --- | --- |
| M14 working tree, 8080, PostgreSQL 17, migration 010, named volume | PASS |
| Original 18-table counts/fingerprints, suppression states, running counts | PASS |
| One synthetic user/token/active user Memory fixture | PASS |
| Active direct GET and list; content/state fields; read-only DB delta | PASS |
| First suppression POST exactly once; HTTP status/outcome/IDs/timestamp | PASS |
| First DB readback; Memory preserved, one Task/Execution, no other delta | PASS |
| Suppressed direct GET, normal list, and model-free search exclusion | PASS |
| Deliberate repeat POST once after proof; new request ID, same timestamp | PASS |
| Repeat DB delta zero; no replayed Task/Execution | PASS |
| Server stop; exact synthetic ownership and five-row cleanup | PASS |
| Baseline counts/private fingerprints/suppression states and volume restored | PASS |
| Mapping, local files, Git working tree, and unrelated Ollama unchanged | PASS |

The following remain **automated-only**, not claims of this manual run:
M3 model-input cited/uncited suppression races, M11 routed final-disclosure
race, token-revocation race, rollback/fault injection, and uncertain commit
acknowledgement. The planned normal HTTP and DB verifiers do not reproduce
those timing-sensitive cases.
