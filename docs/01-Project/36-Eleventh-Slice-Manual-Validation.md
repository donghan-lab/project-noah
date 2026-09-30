# M11 manual HTTP E2E validation — operator procedure

> Prepared 2026-10-01. M11 automated verification is recorded in
> [35-Eleventh-Slice-Validation.md](35-Eleventh-Slice-Validation.md). The
> user completed this manual E2E and cleanup; the observed results are recorded
> below. These blocks remain an operator procedure for a fresh synthetic run.
> Run them in order in Windows
> PowerShell 5.1. Keep window A and its variables open through cleanup. Window
> B runs NOAH; window C runs the dedicated Ollama instance if needed. Stop at
> any unexpected result. Never automatically resend a successful or failed
> request, and never run the cleanup transaction after an incomplete check.

## Contract and preparation-time state

`POST /requests/route` accepts exactly `question` and optional caller-supplied
`project_id`. Its top-level response has `status`, `routing`, and `result`.
`routing` has `outcome`, `capability`, and `stage`. On Memory selection,
`result` is the existing M3 body (`outcome`, `answer`, `evidence`, `scope`,
`search_terms`, `examined`, `truncated`) and creates no durable Task/Execution.
On Document selection, `result` is the existing M10 body with its own
`task_id`, `execution_id`, candidate observation, selected names, sources,
and exact quote Evidence. `no_action` returns HTTP 200 with
`routing.outcome=no_action`, null `result`, `task_id`, and `execution_id`.
M11 itself persists no route audit or duplicate Task/Execution. `supported`
and `partial` are both possible successful grounded M10 outcomes; neither
proves complete semantic truth.

At document preparation time, PostgreSQL reported 17.10 and counts of users
1, API tokens 1, memories 2, Tasks 2, Executions 3, M4 mappings 1;
projects, memberships, M6–M10 Evidence, and running Tasks/Executions were
all 0. The local mapping was absent. The `noah-postgres` container reported
`postgres:17` and was running. Neither port 8080 nor 11435 had a listener.
**These observations are not the execution-time baseline:** recheck them
below. No NOAH HTTP request or fixture creation was performed while writing
this guide.

This procedure creates a separate synthetic user and API token so M3 cannot
retrieve the existing user's private Memory. The synthetic token stays in a
PowerShell variable and is never printed. Only public synthetic Memory and
documents reach the local model. If any precondition differs, especially an
existing operator mapping, stop and review the state rather than replacing it.
Do not run `python -m noah init`, `docker compose down -v`, volume prune, or a
database reset.

## 1. Window A — read-only preflight and private baseline

The `Get-NetTCPConnection` check is local listener inspection; `/api/tags`
reads only model registration. If 11435 is absent, start the separate instance
in window C using the command after this block, then repeat the listener and
tag checks. Do not change the existing 11434 service. Port 8080 must be free
before starting the working-tree M11 server.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python runtime missing' }
if (-not (Test-Path -LiteralPath (Join-Path $Repo 'noah\capability_route.py')) -or
    -not (Test-Path -LiteralPath (Join-Path $Repo 'noah\document_auto_query.py'))) {
    throw 'M11 implementation files missing; stop'
}
if (Test-Path -LiteralPath $Mapping) { throw 'Existing operator mapping: stop; do not overwrite it' }
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 is already in use; inspect the process and stop here'
}
$Pg = @(docker ps --format '{{.Names}} {{.Image}} {{.Status}}' | Where-Object { $_ -match '^noah-postgres postgres:17 Up ' })
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1) { throw 'Existing PostgreSQL 17 container not ready' }
function Get-NoahVolumeIdentity {
    $ContainerInfo = @(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $ContainerInfo.Count -ne 1) { throw 'Container inspection failed' }
    $Volumes = @($ContainerInfo[0].Mounts | Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" } | Sort-Object)
    if ($Volumes.Count -ne 1) { throw 'Expected one named PostgreSQL volume' }
    return $Volumes[0]
}
$VolumeBefore = Get-NoahVolumeIdentity
Write-Output 'PostgreSQL 17, named volume, mapping absence, and free 8080 port confirmed'
```

If needed, in **window C** (a new PowerShell window), run:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

Then in **window A**:

```powershell
$ModelListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 11435 })
if ($ModelListeners.Count -ne 1 -or $ModelListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'Dedicated Ollama must listen only on 127.0.0.1:11435'
}
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq 'gemma4:12b-it-qat' }).Count -ne 1) {
    throw 'Validated local model unavailable'
}
Write-Output 'Dedicated local Ollama listener and model confirmed'
```

The following Python is passed through **stdin**, never multiline `-c`.
It opens one read-only transaction and outputs only counts and SHA-256
fingerprints of rows, never private row values. Keep `$BaselineJson` in window
A; do not print it. This block also checks that migration 007's three M10
Evidence tables exist. The baseline counts below are deliberate stop guards,
not a request to recreate or reset the database.

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
 'auto_document_quote_evidence'
]
out = {'tables': {}}
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    if not db.execute('SHOW server_version').fetchone()['server_version'].startswith('17.'):
        raise RuntimeError('PostgreSQL version mismatch')
    for name in tables:
        rows = db.execute('SELECT * FROM noah.' + name).fetchall()
        digests = sorted(hashlib.sha256(json.dumps(row, sort_keys=True,
            default=str, ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count': len(rows), 'rows': digests}
    for name in ('tasks','execution_records'):
        out['running_' + name] = db.execute(
            "SELECT count(*) AS n FROM noah." + name + " WHERE status='running'").fetchone()['n']
print(json.dumps(out, sort_keys=True, separators=(',', ':')))
'@
function Get-NoahSnapshot {
    $Value = $SnapshotCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw 'Read-only DB snapshot failed' }
    return [string]$Value
}
$BaselineJson = Get-NoahSnapshot
$Baseline = $BaselineJson | ConvertFrom-Json
$Expected = @{ users=1; api_tokens=1; memories=2; tasks=2; execution_records=3;
    memory_write_requests=1; projects=0; project_memberships=0;
    document_tool_evidence=0; document_read_evidence=0; document_answer_evidence=0;
    selected_document_answer_evidence=0; selected_document_source_evidence=0;
    selected_document_quote_evidence=0; auto_document_answer_evidence=0;
    auto_document_source_evidence=0; auto_document_quote_evidence=0 }
foreach ($Name in $Expected.Keys) {
    if ($Baseline.tables.PSObject.Properties[$Name].Value.count -ne $Expected[$Name]) {
        throw "Unexpected baseline count: $Name; stop without creating fixtures"
    }
}
if ($Baseline.running_tasks -ne 0 -or $Baseline.running_execution_records -ne 0) {
    throw 'Unresolved running work; stop'
}
function Assert-Delta($CurrentJson, $Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne ($Property.Value.count + $Extra)) {
            throw "Unexpected DB row delta: $Name"
        }
        $After = @($Current.tables.PSObject.Properties[$Name].Value.rows)
        foreach ($OldDigest in @($Property.Value.rows)) {
            if ($After -notcontains $OldDigest) { throw "Original $Name row changed; stop" }
        }
    }
    if ($Current.running_tasks -ne 0 -or $Current.running_execution_records -ne 0) {
        throw 'Unexpected running Task/Execution; stop'
    }
}
Write-Output 'Private baseline counts and fingerprints captured; no values displayed'
```

## 2. Window A — create only this run's synthetic fixtures

These are **operator test fixtures**, not a Memory Write API request. One
transaction creates a new user, one hashed synthetic token, one user-scoped
Memory, one project, and one read-only membership. The existing user, token,
Memory, Task, Execution, and M4 mapping are untouched. The synthetic token
is generated in PowerShell and supplied to only this setup child process via
a temporary environment variable; Python never prints it. The two filenames
give M10 its filename-only animal/color relevance signals. The Memory has a
unique run marker, and its question is scoped to the synthetic user.

```powershell
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m11-manual-$RunId"
$RootId = $RunLabel
$Root = Join-Path $Repo ".noah\$RunLabel"
$AnimalName = 'm11-test-animal.md'
$ColorName = 'm11-test-color.md'
$AnimalPath = Join-Path $Root $AnimalName
$ColorPath = Join-Path $Root $ColorName
if (Test-Path -LiteralPath $Root) { throw 'Synthetic root already exists' }
if (Test-Path -LiteralPath $Mapping) { throw 'Operator mapping appeared; stop' }
$RandomBytes = New-Object byte[] 32
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $Rng.GetBytes($RandomBytes) } finally { $Rng.Dispose() }
$TestToken = [Convert]::ToBase64String($RandomBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
[Array]::Clear($RandomBytes, 0, $RandomBytes.Length)
$MemoryQuestion = '내가 저장한 Orion 메모의 테스트 탈것은 무엇이야?'
$MemoryText = "M11 공개 합성 Orion 메모. 질문: $MemoryQuestion 답: 테스트 탈것은 자전거이다. 식별자 $RunLabel."
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
New-Item -ItemType Directory -Path $Root | Out-Null
$AnimalText = "# M11 public animal test`nNOAH의 M11 테스트 동물은 수달이다.`n합성 검증 자료이다.`n"
$ColorText = "# M11 public color test`nNOAH의 M11 테스트 색상은 파란색이다.`n합성 검증 자료이다.`n"
[System.IO.File]::WriteAllText($AnimalPath, $AnimalText, $Utf8NoBom)
[System.IO.File]::WriteAllText($ColorPath, $ColorText, $Utf8NoBom)
$AnimalHash = (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$ColorHash = (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant()
$TotalBytes = [System.IO.File]::ReadAllBytes($AnimalPath).Length + [System.IO.File]::ReadAllBytes($ColorPath).Length
if ($TotalBytes -le 0 -or $TotalBytes -ge 2048 -or
    @(Get-ChildItem -LiteralPath $Root -Force).Count -ne 2) { throw 'Synthetic document root invalid; stop' }
```

The preceding block deliberately stops **before writing the mapping**.
Complete the single DB fixture transaction first, then bind its returned
project UUID to the already created root. If file creation failed, do not
run the DB block or cleanup by assumption; inspect the partial fixture.

```powershell
$SetupCode = @'
import hashlib, json, os
from uuid import uuid4
from noah.db import connect
run = os.environ['NOAH_M11_RUN_LABEL']
token = os.environ['NOAH_M11_TEST_TOKEN']
content = os.environ['NOAH_M11_MEMORY_TEXT']
if not run.startswith('m11-manual-') or len(token) < 32:
    raise RuntimeError('Fixture parameters invalid')
user_id, memory_id, project_id = uuid4(), uuid4(), uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES (%s,%s)', (user_id,run))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES (%s,%s)',
               (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
    db.execute('INSERT INTO noah.memories(id,owner_user_id,scope,content,created_by) '
               "VALUES (%s,%s,'user',%s,%s)", (memory_id,user_id,content,user_id))
    db.execute('INSERT INTO noah.projects(id,label) VALUES (%s,%s)', (project_id,run))
    db.execute('INSERT INTO noah.project_memberships(project_id,user_id,can_write) '
               'VALUES (%s,%s,false)', (project_id,user_id))
print(json.dumps({'user_id':str(user_id),'memory_id':str(memory_id),
                  'project_id':str(project_id)}))
'@
$env:NOAH_M11_RUN_LABEL = $RunLabel
$env:NOAH_M11_TEST_TOKEN = $TestToken
$env:NOAH_M11_MEMORY_TEXT = $MemoryText
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) { throw 'Synthetic DB fixture transaction failed; stop' }
} finally {
    Remove-Item Env:NOAH_M11_RUN_LABEL,Env:NOAH_M11_TEST_TOKEN,Env:NOAH_M11_MEMORY_TEXT -ErrorAction SilentlyContinue
}
$Fixture = $FixtureJson | ConvertFrom-Json
$UserId = [string]$Fixture.user_id
$MemoryId = [string]$Fixture.memory_id
$ProjectId = [string]$Fixture.project_id
$Projects = @{}
$Projects[$ProjectId] = @{ root_id = $RootId; document_root = $Root }
$MappingJson = @{ projects = $Projects } | ConvertTo-Json -Depth 6 -Compress
if (Test-Path -LiteralPath $Mapping) { throw 'Operator mapping appeared; stop without overwrite' }
[System.IO.File]::WriteAllText($Mapping, $MappingJson, $Utf8NoBom)
$MappingHash = (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant()
$MapBytes = [System.IO.File]::ReadAllBytes($Mapping)
if ($MapBytes.Length -ge 3 -and $MapBytes[0] -eq 239 -and $MapBytes[1] -eq 187 -and $MapBytes[2] -eq 191) {
    throw 'Local mapping has UTF-8 BOM; stop'
}
$FixtureSnapshotJson = Get-NoahSnapshot
Assert-Delta $FixtureSnapshotJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1 }
Write-Output 'Synthetic user, token, Memory, project, read-only membership, and two files ready'
```

If any fixture step fails, retain the state and request a targeted recovery
review. Do not run the normal cleanup block until all its ownership checks
can pass.

## 3. Window B — start M11 server; window A — Memory route once

Start the **current working tree** in a new PowerShell window B:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

In window A, confirm a single loopback listener and send one synthetic
Memory request. UTF-8 bytes and charset are explicit. The `try/catch` reports
only an HTTP status and safe failure code; it does not resend or display a
potentially sensitive response. If routing or grounding differs, stop.

```powershell
$ApiListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 8080 })
if ($ApiListeners.Count -ne 1 -or $ApiListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'NOAH must listen only on 127.0.0.1:8080'
}
$Uri = 'http://127.0.0.1:8080/requests/route'
$Headers = @{ Authorization = "Bearer $TestToken" }
$MemoryJson = @{ question = $MemoryQuestion } | ConvertTo-Json -Compress
try {
    $MemoryWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($MemoryJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) { try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {} }
    throw "Memory request failed: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$MemoryResponse = $MemoryWeb.Content | ConvertFrom-Json
$MemoryEvidence = @($MemoryResponse.result.evidence)
if ($MemoryWeb.StatusCode -ne 200 -or $MemoryResponse.status -ne 'succeeded' -or
    $MemoryResponse.routing.outcome -ne 'selected' -or
    $MemoryResponse.routing.capability -ne 'memory.query' -or
    $MemoryResponse.routing.stage -ne 'delegated' -or
    $MemoryResponse.result.status -ne 'succeeded' -or
    $MemoryResponse.result.outcome -ne 'grounded' -or $MemoryEvidence.Count -ne 1 -or
    $MemoryEvidence[0].memory_id -ne $MemoryId -or
    -not $MemoryText.Contains([string]$MemoryEvidence[0].quote) -or
    -not $MemoryEvidence[0].quote.Contains('자전거')) {
    throw 'M3 routed result or exact synthetic Memory Evidence differs; stop'
}
if ($MemoryWeb.Content.Contains($TestToken) -or $MemoryWeb.Content.Contains($Root)) {
    throw 'Credential/path in Memory response; stop'
}
$AfterMemoryJson = Get-NoahSnapshot
if ($AfterMemoryJson -ne $FixtureSnapshotJson) { throw 'Memory route changed durable rows; stop' }
Write-Output 'M11 Memory route: grounded synthetic M3 quote; durable DB delta 0'
```

The Memory quote check confirms M3's existing exact quote and M11's final
read-access recheck for this still-valid token. **A static successful request
cannot simulate a token revoked between M3 and disclosure**; the dedicated
automatic test covers that timing. Do not revoke an existing user token here.

## 4. Window A — Document route once, then source-aware Evidence verification

This single request supplies the project UUID **from the synthetic fixture**.
The route model receives only the question, not a path or document body. M10
then observes names, selects at most two, safely reads them, and verifies
quotes. A valid `no_document_selected`, one-source choice, or ungrounded
answer does **not** satisfy this two-source manual E2E; record it and stop
without a retry. `supported` and `partial` are both accepted if each source
has an exact question-relevant quote.

```powershell
$DocumentQuestion = '이 프로젝트 문서에서 M11 테스트 동물과 테스트 색상을 각각 알려줘.'
$DocumentJson = @{ question = $DocumentQuestion; project_id = $ProjectId } | ConvertTo-Json -Compress
try {
    $DocumentWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($DocumentJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) { try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {} }
    throw "Document request failed: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$DocumentResponse = $DocumentWeb.Content | ConvertFrom-Json
$Result = $DocumentResponse.result
$Selected = @($Result.selected_document_names)
$Sources = @($Result.sources)
$Quotes = @($Result.evidence)
if ($DocumentWeb.StatusCode -ne 200 -or $DocumentResponse.status -ne 'succeeded' -or
    $DocumentResponse.routing.outcome -ne 'selected' -or
    $DocumentResponse.routing.capability -ne 'project.documents.answer.auto' -or
    $DocumentResponse.routing.stage -ne 'delegated' -or
    $Result.status -ne 'succeeded' -or $Result.capability -ne 'project.documents.answer.auto' -or
    $Result.project_id -ne $ProjectId -or -not $Result.task_id -or -not $Result.execution_id -or
    $Result.grounded -ne $true -or @('supported','partial') -notcontains $Result.outcome -or
    $Result.candidate_observation.count -ne 2 -or $Result.candidate_observation.truncated -ne $false -or
    $Selected.Count -ne 2 -or $Sources.Count -ne 2 -or $Quotes.Count -lt 2 -or $Quotes.Count -gt 3) {
    throw 'M11/M10 two-source result differs; stop without retry'
}
$ExpectedSelected = @($AnimalName,$ColorName) | Sort-Object
if ((@($Selected | Sort-Object) -join '|') -ne ($ExpectedSelected -join '|')) {
    throw 'Selected document names differ'
}
for ($i=0; $i -lt 2; $i++) {
    if ($Sources[$i].source_id -ne "D$($i+1)" -or $Sources[$i].document_name -ne $Selected[$i]) {
        throw 'D1/D2 source order differs'
    }
}
$AnimalSource = @($Sources | Where-Object { $_.document_name -eq $AnimalName })[0]
$ColorSource = @($Sources | Where-Object { $_.document_name -eq $ColorName })[0]
if (@($Quotes | Where-Object { $_.source_id -eq $AnimalSource.source_id -and $_.quote.Contains('수달') }).Count -eq 0 -or
    @($Quotes | Where-Object { $_.source_id -eq $ColorSource.source_id -and $_.quote.Contains('파란색') }).Count -eq 0) {
    throw 'Two source-aware facts not found; stop'
}
if ($DocumentWeb.Content.Contains($Root) -or $DocumentWeb.Content.Contains($TestToken)) {
    throw 'Credential/path in Document response; stop'
}
Write-Output "M11 Document route selected both sources; outcome=$($Result.outcome), Evidence=$($Quotes.Count)"
```

Inspect whether the two public quotes address the animal and color parts of
the question. Preserve `partial` as returned; do not relabel it `supported`.
The next **read-only** block checks exact Unicode `[start,end)` positions,
byte hashes, parent/source/quote Evidence, and absence of nested M6–M9
Evidence. It also verifies that neither the full document body nor machine
path or credentials were persisted or returned. It prints only a verdict.

```powershell
$Response64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DocumentWeb.Content))
$VerifyCode = @'
import base64, hashlib, json, os, sys
from pathlib import Path
from noah.db import connect, local_settings
from noah.document_auto import candidate_hash
project, user, task_id, execution_id, root, root_id, response64 = sys.argv[1:8]
response = json.loads(base64.b64decode(response64).decode('utf-8'))
result = response['result']
names = ['m11-test-animal.md', 'm11-test-color.md']
raw = {name:(Path(root)/name).read_bytes() for name in names}
body = {name:raw[name].decode('utf-8', errors='strict') for name in names}
def require(value, reason):
    if not value: raise RuntimeError(reason)
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    task = db.execute('SELECT * FROM noah.tasks WHERE id=%s',(task_id,)).fetchone()
    execution = db.execute('SELECT * FROM noah.execution_records WHERE id=%s',(execution_id,)).fetchone()
    parent = db.execute('SELECT * FROM noah.auto_document_answer_evidence WHERE execution_id=%s',(execution_id,)).fetchone()
    sources = db.execute('SELECT * FROM noah.auto_document_source_evidence WHERE execution_id=%s ORDER BY source_ordinal',(execution_id,)).fetchall()
    quotes = db.execute('SELECT * FROM noah.auto_document_quote_evidence WHERE execution_id=%s ORDER BY quote_ordinal',(execution_id,)).fetchall()
    require(task and execution and parent, 'Linked Task/Execution/parent missing')
    require(str(task['actor_user_id'])==user and task['status']=='completed' and
            task['verification_status']=='passed', 'Task state/owner mismatch')
    require(str(execution['task_id'])==task_id and str(execution['actor_user_id'])==user and
            execution['capability']=='project.documents.answer.auto' and
            execution['status']=='succeeded' and execution['verified_at'] is not None,
            'Execution state/link mismatch')
    require(db.execute('SELECT count(*) AS n FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchone()['n']==1 and
            db.execute('SELECT count(*) AS n FROM noah.execution_records WHERE actor_user_id=%s',(user,)).fetchone()['n']==1,
            'Extra Task/Execution; router must not create another')
    require(str(parent['project_id'])==project and parent['root_id']==root_id and
            parent['candidate_names']==names and parent['candidate_count']==2 and
            parent['truncated'] is False and parent['selection_model_called'] is True and
            parent['selection_outcome']=='selected' and parent['selected_count']==2 and
            parent['selected_names']==result['selected_document_names'] and
            parent['raw_candidate_names']==result['selected_document_names'] and
            parent['answer_outcome']==result['outcome'] and
            parent['candidate_sha256'].strip()==candidate_hash(project,root_id,names) and
            result['candidate_observation']['sha256']==parent['candidate_sha256'].strip(),
            'M10 candidate/selection Evidence mismatch')
    require(len(sources)==2 and 2<=len(quotes)<=3 and len(quotes)==len(result['evidence']),
            'Source/quote count mismatch')
    by_id = {}
    for ordinal, source in enumerate(sources,1):
        sid, name = 'D'+str(ordinal), result['selected_document_names'][ordinal-1]
        digest = hashlib.sha256(raw[name]).hexdigest()
        api = result['sources'][ordinal-1]
        require(source['source_id']==sid and source['source_ordinal']==ordinal and
                source['document_name']==name and source['observed_at'] is not None and
                source['byte_length']==len(raw[name]) and source['content_sha256'].strip()==digest and
                source['content_encoding']=='utf-8' and source['bom_present'] is False and
                api['source_id']==sid and api['document_name']==name and
                api['byte_length']==len(raw[name]) and api['content_sha256']==digest,
                'Source observation mismatch')
        by_id[sid]=name
    seen = set()
    for ordinal, quote in enumerate(quotes,1):
        sid = quote['source_id']
        require(sid in by_id and quote['quote_ordinal']==ordinal, 'Quote source/order mismatch')
        excerpt = quote['quote']
        start = body[by_id[sid]].find(excerpt)
        digest = hashlib.sha256(raw[by_id[sid]]).hexdigest()
        api = result['evidence'][ordinal-1]
        require(0<=start and quote['start_index']==start and
                quote['end_index']==start+len(excerpt) and 1<=len(excerpt)<=240 and
                api['source_id']==sid and api['quote']==excerpt and api['start']==start and
                api['end']==start+len(excerpt) and api['content_sha256']==digest,
                'Exact source quote/Unicode position mismatch')
        if 'animal' in by_id[sid]: require('\uC218\uB2EC' in excerpt, 'Animal quote missing fact')
        if 'color' in by_id[sid]: require('\uD30C\uB780\uC0C9' in excerpt, 'Color quote missing fact')
        seen.add(sid)
    require(seen=={'D1','D2'}, 'Both source facts required')
    for name in ('document_tool_evidence','document_read_evidence','document_answer_evidence',
                 'selected_document_answer_evidence','selected_document_source_evidence',
                 'selected_document_quote_evidence'):
        require(db.execute('SELECT count(*) AS n FROM noah.'+name+' WHERE execution_id=%s',
                           (execution_id,)).fetchone()['n']==0, 'Unexpected legacy Evidence')
    persisted = json.dumps({'parent':parent,'sources':sources,'quotes':quotes},
                           default=str,ensure_ascii=False)
    disclosed = json.dumps(response,ensure_ascii=False)
    token = os.environ['NOAH_M11_VERIFY_TOKEN']
    password = local_settings()['POSTGRES_PASSWORD']
    require(all(text not in persisted for text in body.values()), 'Whole document persisted')
    require(root not in persisted+disclosed and token not in persisted+disclosed and
            password not in persisted+disclosed, 'Path/credential exposed')
print('M11 routed M10 Task/Execution/candidate/source/quote Evidence verified')
'@
$env:NOAH_M11_VERIFY_TOKEN = $TestToken
try {
    $VerifyCode | & $Python - $ProjectId $UserId $Result.task_id $Result.execution_id $Root $RootId $Response64
    if ($LASTEXITCODE -ne 0) { throw 'Read-only M10 Evidence check failed; stop' }
} finally {
    Remove-Item Env:NOAH_M11_VERIFY_TOKEN -ErrorAction SilentlyContinue
}
$AfterDocumentJson = Get-NoahSnapshot
Assert-Delta $AfterDocumentJson @{ users=1; api_tokens=1; memories=1; projects=1;
    project_memberships=1; tasks=1; execution_records=1;
    auto_document_answer_evidence=1; auto_document_source_evidence=2;
    auto_document_quote_evidence=$Quotes.Count }
Write-Output 'Exactly one M10 Task/Execution and linked Evidence; original rows unchanged'
```

## 5. Window A — No Action once

The unsupported **write** request is public and contains no credentials or
private content. M11 must not execute a write, invoke M3/M10, or add durable
rows. A model that chooses a different route fails this manual criterion;
stop without an automatic retry.

```powershell
$NoActionJson = @{ question = 'Delete all files and send an email.' } | ConvertTo-Json -Compress
try {
    $NoActionWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body ([Text.Encoding]::UTF8.GetBytes($NoActionJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) { try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {} }
    throw "No Action request failed: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$NoActionResponse = $NoActionWeb.Content | ConvertFrom-Json
if ($NoActionWeb.StatusCode -ne 200 -or $NoActionResponse.status -ne 'succeeded' -or
    $NoActionResponse.routing.outcome -ne 'no_action' -or
    $NoActionResponse.routing.stage -ne 'routing' -or
    $null -ne $NoActionResponse.routing.capability -or
    $null -ne $NoActionResponse.result -or
    $null -ne $NoActionResponse.task_id -or $null -ne $NoActionResponse.execution_id) {
    throw 'No Action contract mismatch; stop'
}
$AfterNoActionJson = Get-NoahSnapshot
if ($AfterNoActionJson -ne $AfterDocumentJson) { throw 'No Action changed durable rows; stop' }
Write-Output 'M11 No Action: no delegated capability or durable DB delta'
```

## 6. Stop server; ownership and baseline checks before cleanup

After all three checks pass, stop window B with `Ctrl+C`. In window A,
require port 8080 to be free. Do not stop or alter PostgreSQL, its named
volume, or the existing 11434 Ollama service. Confirm the exact post-test DB
snapshot, the original row fingerprints, and the local artifact hashes.
The mapping must contain **only this run's one project**; if it changed,
stop. This verification must pass before any DELETE.

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop | Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'NOAH server still listening; stop window B first'
}
if ((Get-NoahSnapshot) -ne $AfterNoActionJson) { throw 'Post-test DB snapshot changed; stop cleanup' }
Assert-Delta $AfterNoActionJson @{ users=1; api_tokens=1; memories=1; projects=1;
    project_memberships=1; tasks=1; execution_records=1;
    auto_document_answer_evidence=1; auto_document_source_evidence=2;
    auto_document_quote_evidence=$Quotes.Count }
$ExpectedRoot = Join-Path $Repo ".noah\m11-manual-$RunId"
if ([IO.Path]::GetFullPath($Root) -ne [IO.Path]::GetFullPath($ExpectedRoot) -or
    -not (Test-Path -LiteralPath $Mapping) -or -not (Test-Path -LiteralPath $AnimalPath) -or
    -not (Test-Path -LiteralPath $ColorPath) -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Synthetic path or bytes changed; stop cleanup'
}
$MapObject = Get-Content -LiteralPath $Mapping -Raw -Encoding UTF8 | ConvertFrom-Json
$MapEntries = @($MapObject.projects.PSObject.Properties)
if ($MapEntries.Count -ne 1 -or $MapEntries[0].Name -ne $ProjectId -or
    $MapEntries[0].Value.root_id -ne $RootId -or
    $MapEntries[0].Value.document_root -ne $Root) { throw 'Mapping is not owned by this run' }
$RootNames = @(Get-ChildItem -LiteralPath $Root -Force | Select-Object -ExpandProperty Name)
if ($RootNames.Count -ne 2 -or
    ((@($RootNames | Sort-Object) -join '|') -ne ($ExpectedSelected -join '|'))) {
    throw 'Unexpected root entry; stop cleanup'
}
$VolumeAfter = Get-NoahVolumeIdentity
if ($VolumeAfter -ne $VolumeBefore) { throw 'PostgreSQL volume identity changed; stop' }
Write-Output 'Server stopped; original row fingerprints, DB delta, synthetic files/mapping, and named volume verified'
```

## 7. Exact synthetic DB cleanup, then local artifacts

This is the **only deletion transaction**. It verifies exact ownership,
status, relationship, and row counts again inside the transaction. If any
assertion or DELETE fails, the transaction rolls back. All Evidence and
Execution deletion predicates use the synthetic `execution_id`; the M10
source and quote tables do not have `project_id`. Existing users, tokens,
memories, Tasks, Executions, M4 mappings, and the Docker volume are outside
these predicates. Do not run this block if a previous section stopped.

```powershell
$CleanupCode = @'
import hashlib, os, sys
from uuid import UUID
from noah.db import connect
user, memory, project, task, execution = (UUID(x) for x in sys.argv[1:6])
label, quote_count = sys.argv[6], int(sys.argv[7])
root_id = sys.argv[8]
def require(value, reason):
    if not value: raise RuntimeError(reason)
def delete_exact(db, sql, args, expected):
    require(db.execute(sql,args).rowcount==expected, 'Unexpected DELETE count')
with connect() as db:
    u = db.execute('SELECT * FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens = db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s',(user,)).fetchall()
    memories = db.execute('SELECT * FROM noah.memories WHERE owner_user_id=%s OR created_by=%s',(user,user)).fetchall()
    p = db.execute('SELECT * FROM noah.projects WHERE id=%s',(project,)).fetchone()
    memberships = db.execute('SELECT * FROM noah.project_memberships WHERE project_id=%s OR user_id=%s',(project,user)).fetchall()
    tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT * FROM noah.execution_records WHERE actor_user_id=%s',(user,)).fetchall()
    parent = db.execute('SELECT * FROM noah.auto_document_answer_evidence WHERE execution_id=%s',(execution,)).fetchone()
    sources = db.execute('SELECT * FROM noah.auto_document_source_evidence WHERE execution_id=%s',(execution,)).fetchall()
    quotes = db.execute('SELECT * FROM noah.auto_document_quote_evidence WHERE execution_id=%s',(execution,)).fetchall()
    token = os.environ['NOAH_M11_CLEANUP_TOKEN']
    require(u and u['label']==label and len(tokens)==1 and tokens[0]['revoked_at'] is None and
            tokens[0]['token_hash'].strip()==hashlib.sha256(token.encode('utf-8')).hexdigest(),
            'Synthetic user/token ownership mismatch')
    require(len(memories)==1 and memories[0]['id']==memory and memories[0]['scope']=='user' and
            memories[0]['owner_user_id']==user and memories[0]['created_by']==user and
            memories[0]['provenance']=='explicit_user_request' and label in memories[0]['content'],
            'Synthetic Memory ownership mismatch')
    require(p and p['label']==label and len(memberships)==1 and
            memberships[0]['project_id']==project and memberships[0]['user_id']==user and
            memberships[0]['can_write'] is False, 'Project/membership ownership mismatch')
    require(len(tasks)==1 and tasks[0]['id']==task and tasks[0]['status']=='completed' and
            tasks[0]['verification_status']=='passed' and
            len(executions)==1 and executions[0]['id']==execution and
            executions[0]['task_id']==task and executions[0]['status']=='succeeded' and
            executions[0]['capability']=='project.documents.answer.auto' and
            executions[0]['memory_id'] is None,
            'M10 Task/Execution ownership mismatch')
    require(parent and parent['project_id']==project and parent['root_id']==root_id and
            parent['selected_count']==2 and
            len(sources)==2 and len(quotes)==quote_count,
            'M10 Evidence ownership mismatch')
    require(db.execute('SELECT count(*) AS n FROM noah.memories WHERE project_id=%s',(project,)).fetchone()['n']==0,
            'Unexpected project Memory; stop')
    require(db.execute('SELECT count(*) AS n FROM noah.memory_write_requests WHERE actor_user_id=%s',(user,)).fetchone()['n']==0,
            'Unexpected synthetic write-key mapping; stop')
    for name in ('document_tool_evidence','document_read_evidence','document_answer_evidence',
                 'selected_document_answer_evidence','selected_document_source_evidence',
                 'selected_document_quote_evidence'):
        require(db.execute('SELECT count(*) AS n FROM noah.'+name+' WHERE execution_id=%s',
                           (execution,)).fetchone()['n']==0, 'Unexpected legacy Evidence')
    delete_exact(db,'DELETE FROM noah.auto_document_quote_evidence WHERE execution_id=%s',(execution,),quote_count)
    delete_exact(db,'DELETE FROM noah.auto_document_source_evidence WHERE execution_id=%s',(execution,),2)
    delete_exact(db,'DELETE FROM noah.auto_document_answer_evidence WHERE execution_id=%s AND project_id=%s',(execution,project),1)
    delete_exact(db,'DELETE FROM noah.execution_records WHERE id=%s AND actor_user_id=%s AND task_id=%s',(execution,user,task),1)
    delete_exact(db,'DELETE FROM noah.tasks WHERE id=%s AND actor_user_id=%s',(task,user),1)
    delete_exact(db,'DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s AND can_write=false',(project,user),1)
    delete_exact(db,'DELETE FROM noah.memories WHERE id=%s AND owner_user_id=%s',(memory,user),1)
    delete_exact(db,'DELETE FROM noah.projects WHERE id=%s AND label=%s',(project,label),1)
    delete_exact(db,'DELETE FROM noah.api_tokens WHERE user_id=%s',(user,),1)
    delete_exact(db,'DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label),1)
print('Only this run synthetic M11/M10 database rows removed')
'@
$env:NOAH_M11_CLEANUP_TOKEN = $TestToken
try {
    $CleanupCode | & $Python - $UserId $MemoryId $ProjectId $Result.task_id $Result.execution_id $RunLabel $Quotes.Count $RootId
    if ($LASTEXITCODE -ne 0) { throw 'Cleanup transaction failed or rolled back; stop' }
} finally {
    Remove-Item Env:NOAH_M11_CLEANUP_TOKEN -ErrorAction SilentlyContinue
}
$AfterDbCleanupJson = Get-NoahSnapshot
if ($AfterDbCleanupJson -ne $BaselineJson) {
    throw 'Original DB counts/fingerprints not restored; retain local artifacts and stop'
}
Write-Output 'Existing DB baseline and private row fingerprints exactly restored'
```

Only after the DB baseline matches, delete this run's mapping and **exactly
two known files**. Recheck bytes before deletion. There is no recursive
delete; removal of the root requires an empty directory.

```powershell
if ([IO.Path]::GetFullPath($Root) -ne [IO.Path]::GetFullPath((Join-Path $Repo ".noah\m11-manual-$RunId")) -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Synthetic path/hash changed after DB cleanup; stop'
}
Remove-Item -LiteralPath $Mapping
Remove-Item -LiteralPath $AnimalPath
Remove-Item -LiteralPath $ColorPath
if (@(Get-ChildItem -LiteralPath $Root -Force).Count -ne 0) { throw 'Root not empty; stop' }
Remove-Item -LiteralPath $Root
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Test-Path -LiteralPath $Mapping) -or (Test-Path -LiteralPath $Root)) {
    throw 'Final DB/local restoration check failed'
}
$VolumeFinal = Get-NoahVolumeIdentity
if ($VolumeFinal -ne $VolumeBefore) { throw 'Volume identity changed' }
$TestToken = $null
$Headers = $null
Write-Output 'DB restored; synthetic mapping, files, and root removed; PostgreSQL volume unchanged'
```

The three successful requests are intentionally separate. M3's result is
read-only and has no durable audit; M10 alone records one Task/Execution;
`no_action` records neither. This user-run procedure checks current access
and Evidence but does not recreate a mid-request permission race. Timing
revocation, malformed model output, model timeout, and cross-user isolation
remain covered by the M11 automated tests. A human should still review the
route choice and the relevance of the two exact quotes.

## Completed user-run record

The user reported one successful HTTP E2E run through each route using only
synthetic inputs:

- Memory: `routing.capability=memory.query`; M3 returned a grounded exact
  synthetic Memory quote. The durable database snapshot did not change.
- Document: `routing.capability=project.documents.answer.auto`; M10 selected
  two sources and returned `outcome=partial` with two source-aware Evidence
  quotes. Read-only DB verification confirmed exactly one M10 Task/Execution
  pair, candidate/source/quote Evidence, exact Unicode positions and source
  hashes, and no legacy Evidence attached to that execution. `partial` is a
  valid two-source grounded outcome and is not rewritten as `supported`.
- No Action: `routing.outcome=no_action`; no delegate ran and the durable
  database snapshot did not change.

After targeted cleanup, the original row counts and private row fingerprints
matched the pre-run baseline exactly. The synthetic mapping, two `.md` files,
and their root were removed, and the PostgreSQL named volume was retained.
The existing user, token, personal Memories, and M1–M10 records remained.

Two **procedure/delivery** issues occurred without a runtime contract change.
The original Docker Go-template command with `eq .Type "volume"` failed under
Windows PowerShell 5.1 with `function "volume" not defined`. The user verified
the same volume identity through `docker inspect noah-postgres |
ConvertFrom-Json`, filtering `.Mounts` for `Type=volume`; the blocks above
now use that method. During Evidence verification, a chat-delivered copy of
the Python block changed its original ASCII Unicode escapes for the Korean
fact words into Korean source literals. PowerShell 5.1's native stdin encoding
then caused a false `Animal quote missing fact`. The user reran **only the
read-only verifier** with the original `\uC218\uB2EC` and
`\uD30C\uB780\uC0C9` escapes; it passed against the existing response and
database rows. There was **no API retry** or second Document execution.
