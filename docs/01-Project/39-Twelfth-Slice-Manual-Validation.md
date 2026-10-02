# M12 manual HTTP E2E validation — operator procedure

> **Manual validation status: COMPLETED (operator result reported 2026-10-02).**
> Prepared for **Windows PowerShell 5.1**. This document retains the operator
> procedure and records the completed HTTP E2E result below. M12 automated
> results are separate in [38-Twelfth-Slice-Validation.md](38-Twelfth-Slice-Validation.md).
> Keep PowerShell window A and its variables open through cleanup. Window B
> runs NOAH; use window C for the dedicated Ollama instance only if needed.
> **Unexpected result → STOP. Never resend an HTTP request automatically. Do
> not clean up while a result or ownership check is incomplete. Never print
> or record actual token/password values.**

This run sends exactly **three** public synthetic `POST /requests/route`
requests: Memory, Document, and No Action. It tests durable router correlation,
not the model's general semantic accuracy. A model choice or answer that does
not satisfy the stated criterion is recorded and investigated without a
retry. Do not use an existing person's Memory, project, or document. Do not
run `noah init`, reset PostgreSQL, remove a Docker volume, or change the
unrelated Ollama service on port 11434.

## Current response and storage contract

An eligible response has top-level `router_id` and
`routing.audit_status=recorded|unconfirmed`. `recorded` confirms its terminal
`observed` audit commit; `unconfirmed` does **not** mean the M3/M10 delegate
failed. Delegated responses retain `routing.outcome=selected`,
`routing.stage=delegated`, and the unchanged result body. The M3 result owns
a response-scoped `request_id` but no Task/Execution. M10 owns one Task,
Execution, and candidate/source/quote Evidence. `no_action` returns HTTP 200,
`routing.outcome=no_action`, `routing.capability=null`, `routing.stage=routing`,
null `result` and Task/Execution IDs; its sole durable delta is one M12 audit
row. M11's historical zero-delta `no_action` observation remains true **at
the M11 baseline**. See [37-Twelfth-Vertical-Slice.md](37-Twelfth-Vertical-Slice.md).

## 1. Window A — read-only preflight

Run one block at a time. The guards below deliberately stop if the expected
clean fixture environment has changed. They do not recreate or overwrite an
existing operator mapping. `docker inspect | ConvertFrom-Json` avoids the
Windows PowerShell 5.1 Docker Go-template quoting problem.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
foreach ($Relative in @('noah\capability_route.py','noah\routing_audit.py',
                         'database\008_routing_audit.sql','noah\document_auto_query.py')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repo $Relative))) {
        throw "M12 implementation file missing: $Relative"
    }
}
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH virtualenv Python missing' }
if (Test-Path -LiteralPath $Mapping) { throw 'Operator mapping exists; STOP without overwrite' }
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 is occupied; do not start another NOAH server'
}
$Pg = @(docker ps --format '{{.Names}} {{.Image}} {{.Status}}' |
    Where-Object { $_ -match '^noah-postgres postgres:17 Up ' })
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1) { throw 'Compose PostgreSQL 17 is not ready' }
function Get-NoahVolumeIdentity {
    $Info = @(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1) { throw 'Container inspection failed' }
    $Volumes = @($Info[0].Mounts | Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" } | Sort-Object)
    if ($Volumes.Count -ne 1) { throw 'Expected one PostgreSQL named volume' }
    return $Volumes[0]
}
$VolumeBefore = Get-NoahVolumeIdentity
$GitBefore = @(git status --short)
if ($LASTEXITCODE -ne 0) { throw 'Git status failed' }
Write-Output 'Implementation, free 8080, PostgreSQL 17, and named volume confirmed'
```

The current model name is read from `noah.ollama.MODEL`, not assumed from a
past report. If port 11435 is absent, verify the existing local Ollama binary
and start **only** a new NOAH-dedicated instance in window C. Record whether
you started it so that an unrelated pre-existing instance is not stopped.

```powershell
$ModelName = (& $Python -c 'from noah.ollama import MODEL; print(MODEL)').Trim()
if ($LASTEXITCODE -ne 0 -or -not $ModelName) { throw 'Cannot read configured model' }
$ModelListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
$StartedDedicatedOllama = $false
if ($ModelListeners.Count -eq 0) {
    $OllamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (-not (Test-Path -LiteralPath $OllamaExe)) { throw 'Local Ollama binary missing; STOP' }
    Write-Output 'Start the dedicated Ollama command in window C, then return here'
}
```

Only if the previous block reported no listener, run in **window C**:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

After starting window C, set `$StartedDedicatedOllama = $true` in window A.
Then run this read-only listener/model check in window A. The 11434 service
must not be modified.

```powershell
$ModelListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($ModelListeners.Count -ne 1 -or $ModelListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'Dedicated Ollama must have one 127.0.0.1:11435 listener'
}
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq $ModelName }).Count -ne 1) {
    throw 'Configured model is not registered on the dedicated instance'
}
Write-Output 'Dedicated loopback Ollama and current NOAH model confirmed'
```

## 2. Window A — private baseline snapshot

This Python is supplied through **stdin**, avoiding PowerShell 5.1 multiline
`-c` quoting. It performs a read-only transaction, includes the new
`routing_audit` table, and outputs only row counts and SHA-256 fingerprints
of serialized rows. Keep `$BaselineJson` private in window A. The expected
counts are the implementation-time baseline; any difference is a **STOP**, not
an instruction to reset data. There must be no running Task/Execution.

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
    db.execute('SET TRANSACTION READ ONLY')
    version = db.execute('SHOW server_version').fetchone()['server_version']
    if not version.startswith('17.'):
        raise RuntimeError('PostgreSQL 17 required')
    actual = [r['tablename'] for r in db.execute(
        "SELECT tablename FROM pg_tables WHERE schemaname='noah' ORDER BY tablename")]
    if sorted(actual) != sorted(tables):
        raise RuntimeError('NOAH table set changed; STOP')
    for name in tables:
        rows = db.execute('SELECT * FROM noah.' + name).fetchall()
        hashes = sorted(hashlib.sha256(json.dumps(row, sort_keys=True,
            default=str, ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count': len(rows), 'rows': hashes}
    for name in ('tasks','execution_records'):
        out['running_' + name] = db.execute(
            "SELECT count(*) AS n FROM noah." + name + " WHERE status='running'").fetchone()['n']
print(json.dumps(out, sort_keys=True, separators=(',', ':')))
'@
function Get-NoahSnapshot {
    $Value = $SnapshotCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw 'Read-only snapshot failed' }
    return [string]$Value
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
        throw "Unexpected baseline count: $Name; STOP"
    }
}
if ($Baseline.running_tasks -ne 0 -or $Baseline.running_execution_records -ne 0) {
    throw 'Running Task/Execution exists; STOP'
}
function Assert-Delta($CurrentJson, $Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Extra)) { throw "Unexpected DB delta: $Name" }
        $After = @($Current.tables.PSObject.Properties[$Name].Value.rows)
        foreach ($OldHash in @($Property.Value.rows)) {
            if ($After -notcontains $OldHash) { throw "Existing $Name row changed; STOP" }
        }
    }
    if ($Current.running_tasks -ne 0 -or $Current.running_execution_records -ne 0) {
        throw 'Unexpected running Task/Execution; STOP'
    }
}
Write-Output 'Private baseline counts/fingerprints retained without revealing row values'
```

## 3. Window A — create this run's public synthetic fixture

This is the first mutating step **for the operator**, and must only follow a
successful preflight. Generate a unique `RunId`; use it in the user/project
labels, Memory text, root ID, and both filenames. The token stays in a
PowerShell variable and a temporary child-process environment variable; it
is never printed. The DB fixture is one transaction. If any preparation step
fails, stop and inspect the partial state before a separately reviewed
cleanup. Do not run the normal cleanup block by assumption.

```powershell
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m12-manual-$RunId"
$RootId = $RunLabel
$Root = Join-Path $Repo ".noah\$RunLabel"
$AnimalName = "m12-test-animal-$RunId.md"
$ColorName = "m12-test-color-$RunId.md"
$AnimalPath = Join-Path $Root $AnimalName
$ColorPath = Join-Path $Root $ColorName
if ((Test-Path -LiteralPath $Root) -or (Test-Path -LiteralPath $Mapping)) {
    throw 'Synthetic root or operator mapping already exists; STOP'
}
$RandomBytes = New-Object byte[] 32
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try { $Rng.GetBytes($RandomBytes) } finally { $Rng.Dispose() }
$TestToken = [Convert]::ToBase64String($RandomBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
[Array]::Clear($RandomBytes, 0, $RandomBytes.Length)
$MemoryQuestion = '내가 저장한 Orion 메모의 테스트 탈것은 무엇이야?'
$MemoryText = "M12 공개 합성 Orion 메모. 질문: $MemoryQuestion 답: 테스트 탈것은 자전거이다. 식별자 $RunLabel."
$AnimalText = "# M12 public animal test $RunId`nNOAH의 M12 테스트 동물은 수달이다.`n합성 검증 자료이다.`n"
$ColorText = "# M12 public color test $RunId`nNOAH의 M12 테스트 색상은 파란색이다.`n합성 검증 자료이다.`n"
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
New-Item -ItemType Directory -Path $Root | Out-Null
[System.IO.File]::WriteAllText($AnimalPath, $AnimalText, $Utf8NoBom)
[System.IO.File]::WriteAllText($ColorPath, $ColorText, $Utf8NoBom)
$AnimalHash = (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$ColorHash = (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant()
$TotalBytes = [System.IO.File]::ReadAllBytes($AnimalPath).Length +
    [System.IO.File]::ReadAllBytes($ColorPath).Length
if ($TotalBytes -le 0 -or $TotalBytes -ge 2048 -or
    @(Get-ChildItem -LiteralPath $Root -Force).Count -ne 2) {
    throw 'Synthetic document root invalid; STOP'
}
```

Create only the synthetic DB rows. The command prints UUIDs, never the token
or Memory body. Its output is used to construct one BOM-free operator mapping.

```powershell
$SetupCode = @'
import hashlib, json, os
from uuid import uuid4
from noah.db import connect
label = os.environ['NOAH_M12_RUN_LABEL']
token = os.environ['NOAH_M12_TEST_TOKEN']
content = os.environ['NOAH_M12_MEMORY_TEXT']
if not label.startswith('m12-manual-') or len(token) < 32 or label not in content:
    raise RuntimeError('Fixture parameters invalid')
user_id, memory_id, project_id = uuid4(), uuid4(), uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES (%s,%s)', (user_id,label))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES (%s,%s)',
               (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
    db.execute('INSERT INTO noah.memories(id,owner_user_id,scope,content,created_by) '
               "VALUES (%s,%s,'user',%s,%s)", (memory_id,user_id,content,user_id))
    db.execute('INSERT INTO noah.projects(id,label) VALUES (%s,%s)', (project_id,label))
    db.execute('INSERT INTO noah.project_memberships(project_id,user_id,can_write) '
               'VALUES (%s,%s,false)', (project_id,user_id))
print(json.dumps({'user_id':str(user_id),'memory_id':str(memory_id),
                  'project_id':str(project_id)}))
'@
$env:NOAH_M12_RUN_LABEL = $RunLabel
$env:NOAH_M12_TEST_TOKEN = $TestToken
$env:NOAH_M12_MEMORY_TEXT = $MemoryText
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) { throw 'Fixture transaction failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M12_RUN_LABEL,Env:NOAH_M12_TEST_TOKEN,Env:NOAH_M12_MEMORY_TEXT `
        -ErrorAction SilentlyContinue
}
$Fixture = $FixtureJson | ConvertFrom-Json
$UserId = [string]$Fixture.user_id
$MemoryId = [string]$Fixture.memory_id
$ProjectId = [string]$Fixture.project_id
$Projects = @{}
$Projects[$ProjectId] = @{ root_id=$RootId; document_root=$Root }
$MappingJson = @{ projects=$Projects } | ConvertTo-Json -Depth 6 -Compress
if (Test-Path -LiteralPath $Mapping) { throw 'Operator mapping appeared; STOP without overwrite' }
[System.IO.File]::WriteAllText($Mapping, $MappingJson, $Utf8NoBom)
$MappingHash = (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant()
$MapBytes = [System.IO.File]::ReadAllBytes($Mapping)
if ($MapBytes.Length -ge 3 -and $MapBytes[0] -eq 239 -and
    $MapBytes[1] -eq 187 -and $MapBytes[2] -eq 191) { throw 'Mapping has a BOM; STOP' }
$FixtureSnapshotJson = Get-NoahSnapshot
Assert-Delta $FixtureSnapshotJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1 }
Write-Output 'Synthetic user, token, Memory, read-only project, mapping, and two documents ready'
```

## 4. Window B — start the working-tree server

In **window B**, start only this NOAH server. It must use the uncommitted M12
working tree, not a previously running process:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

In **window A**, require one loopback listener. The next block sends no API
request.

```powershell
$ApiListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ApiListeners.Count -ne 1 -or $ApiListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'This NOAH server must listen only on 127.0.0.1:8080'
}
$Uri = 'http://127.0.0.1:8080/requests/route'
$Headers = @{ Authorization = "Bearer $TestToken" }
Write-Output 'Working-tree NOAH listener confirmed; ready for one Memory request'
```

## 5. Memory route — send exactly once, then inspect the existing result

PowerShell 5.1 sends explicit UTF-8 bytes and
`application/json; charset=utf-8`. If the HTTP call throws, inspect the
captured error and **STOP**; it may have reached NOAH. Do not send it again.
The result checks use `@(...)` so one Evidence item is still counted as one.

```powershell
$MemoryJson = @{ question=$MemoryQuestion } | ConvertTo-Json -Compress
try {
    $MemoryWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($MemoryJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) {
        try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {}
    }
    throw "Memory HTTP result unexpected: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$MemoryResponse = $MemoryWeb.Content | ConvertFrom-Json
$MemoryEvidence = @($MemoryResponse.result.evidence)
$MemoryRouterId = [string]$MemoryResponse.router_id
try { $null = [guid]::Parse($MemoryRouterId) } catch { throw 'Invalid Memory router_id; STOP' }
if ($MemoryWeb.StatusCode -ne 200 -or $MemoryResponse.status -ne 'succeeded' -or
    $MemoryResponse.routing.outcome -ne 'selected' -or
    $MemoryResponse.routing.capability -ne 'memory.query' -or
    $MemoryResponse.routing.stage -ne 'delegated' -or
    $MemoryResponse.routing.audit_status -ne 'recorded' -or
    $MemoryResponse.result.status -ne 'succeeded' -or
    $MemoryResponse.result.outcome -ne 'grounded' -or
    $MemoryEvidence.Count -ne 1 -or $MemoryEvidence[0].memory_id -ne $MemoryId -or
    -not $MemoryText.Contains([string]$MemoryEvidence[0].quote) -or
    -not $MemoryEvidence[0].quote.Contains('자전거')) {
    throw 'Memory route or exact synthetic quote differs; STOP without retry'
}
if ($MemoryWeb.Content.Contains($TestToken) -or $MemoryWeb.Content.Contains($Root)) {
    throw 'Credential or OS path in Memory response; STOP'
}
Write-Output 'One Memory request returned grounded synthetic M3 Evidence and recorded router ID'
```

Read-only check: one terminal audit row belongs to the synthetic actor,
links the **M3 result** `request_id`, and has null Task/Execution IDs.
`delegate_result_observed=true` means NOAH received the M3 response; the
recorded row is not an M3 Execution Record. The audit must not contain the
question, Memory body/quote, answer, token/hash, password, prompt, or path.
The verifier receives the synthetic token only through a temporary
environment variable; it prints a verdict, not row contents.

```powershell
$MemoryAuditCode = @'
import hashlib, json, os, sys
from uuid import UUID
from noah.db import connect, local_settings
from noah.capability_route import SYSTEM_INSTRUCTIONS
router, user, m3_request = (UUID(x) for x in sys.argv[1:4])
question = os.environ['NOAH_M12_VERIFY_QUESTION']
body = os.environ['NOAH_M12_VERIFY_MEMORY']
quote = os.environ['NOAH_M12_VERIFY_QUOTE']
token = os.environ['NOAH_M12_VERIFY_TOKEN']
root = os.environ['NOAH_M12_VERIFY_ROOT']
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    rows = db.execute('SELECT * FROM noah.routing_audit WHERE router_id=%s',
                      (router,)).fetchall()
    if len(rows) != 1: raise RuntimeError('Memory router row count mismatch')
    a = rows[0]
    if not (a['actor_user_id']==user and a['stage']=='observed' and
            a['validated_route']=='memory.query' and a['dispatch_prepared'] is True and
            a['delegate_result_observed'] is True and
            a['delegate_capability']=='memory.query' and
            a['delegate_request_id']==m3_request and
            a['delegate_task_id'] is None and a['delegate_execution_id'] is None and
            a['observation_class']=='delegate_returned' and a['http_status']==200 and
            a['outcome_code']=='grounded' and a['observed_at'] is not None):
        raise RuntimeError('Memory audit correlation mismatch')
    stored = json.dumps(a,default=str,ensure_ascii=False)
    forbidden = (question,body,quote,token,hashlib.sha256(token.encode()).hexdigest(),
                 local_settings()['POSTGRES_PASSWORD'],root,SYSTEM_INSTRUCTIONS)
    if any(value and value in stored for value in forbidden):
        raise RuntimeError('Sensitive content in routing audit')
print('M12 Memory audit and M3 response request ID verified; no content stored')
'@
$env:NOAH_M12_VERIFY_QUESTION = $MemoryQuestion
$env:NOAH_M12_VERIFY_MEMORY = $MemoryText
$env:NOAH_M12_VERIFY_QUOTE = [string]$MemoryEvidence[0].quote
$env:NOAH_M12_VERIFY_TOKEN = $TestToken
$env:NOAH_M12_VERIFY_ROOT = $Root
try {
    $MemoryAuditCode | & $Python - $MemoryRouterId $UserId $MemoryResponse.result.request_id
    if ($LASTEXITCODE -ne 0) { throw 'Read-only Memory audit verification failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M12_VERIFY_QUESTION,Env:NOAH_M12_VERIFY_MEMORY, `
        Env:NOAH_M12_VERIFY_QUOTE,Env:NOAH_M12_VERIFY_TOKEN,Env:NOAH_M12_VERIFY_ROOT `
        -ErrorAction SilentlyContinue
}
$AfterMemoryJson = Get-NoahSnapshot
Assert-Delta $AfterMemoryJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1; routing_audit=1 }
Write-Output 'Memory route: routing audit +1, Task/Execution/Evidence +0; original rows unchanged'
```

The successful request checks the current token and Memory visibility. It
does not simulate a mid-request revocation; M11/M12 automated tests cover
that timing. A local verifier encoding/parsing error calls for read-only
reinspection of this captured response and DB row, **not** another API call.

## 6. Document route — send exactly once

The caller supplies only the synthetic project UUID. This question requires
both small documents. If the model selects fewer than both, returns a valid
zero-selection result, or provides ungrounded quotes, record the actual result
and STOP without retry. `supported` and `partial` are both valid successful
two-source grounded outcomes; neither proves complete semantic coverage.

```powershell
$DocumentQuestion = '이 프로젝트 문서에서 M12 테스트 동물과 테스트 색상을 각각 알려줘.'
$DocumentJson = @{ question=$DocumentQuestion; project_id=$ProjectId } | ConvertTo-Json -Compress
try {
    $DocumentWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($DocumentJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) {
        try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {}
    }
    throw "Document HTTP result unexpected: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$DocumentResponse = $DocumentWeb.Content | ConvertFrom-Json
$DocumentRouterId = [string]$DocumentResponse.router_id
try { $null = [guid]::Parse($DocumentRouterId) } catch { throw 'Invalid Document router_id; STOP' }
$Result = $DocumentResponse.result
$Selected = @($Result.selected_document_names)
$Sources = @($Result.sources)
$Quotes = @($Result.evidence)
if ($DocumentWeb.StatusCode -ne 200 -or $DocumentResponse.status -ne 'succeeded' -or
    $DocumentResponse.routing.outcome -ne 'selected' -or
    $DocumentResponse.routing.capability -ne 'project.documents.answer.auto' -or
    $DocumentResponse.routing.stage -ne 'delegated' -or
    $DocumentResponse.routing.audit_status -ne 'recorded' -or
    $Result.status -ne 'succeeded' -or
    $Result.capability -ne 'project.documents.answer.auto' -or
    $Result.project_id -ne $ProjectId -or -not $Result.task_id -or
    -not $Result.execution_id -or $Result.grounded -ne $true -or
    @('supported','partial') -notcontains $Result.outcome -or
    $Result.candidate_observation.count -ne 2 -or
    $Result.candidate_observation.truncated -ne $false -or
    $Selected.Count -ne 2 -or $Sources.Count -ne 2 -or
    $Quotes.Count -lt 2 -or $Quotes.Count -gt 3) {
    throw 'M12/M10 two-source result differs; STOP without retry'
}
$ExpectedSelected = @($AnimalName,$ColorName) | Sort-Object
if ((@($Selected | Sort-Object) -join '|') -ne ($ExpectedSelected -join '|')) {
    throw 'Selected filenames differ; STOP'
}
for ($i=0; $i -lt 2; $i++) {
    if ($Sources[$i].source_id -ne "D$($i+1)" -or
        $Sources[$i].document_name -ne $Selected[$i]) { throw 'D1/D2 order differs; STOP' }
}
$AnimalSource = @($Sources | Where-Object { $_.document_name -eq $AnimalName })[0]
$ColorSource = @($Sources | Where-Object { $_.document_name -eq $ColorName })[0]
if (@($Quotes | Where-Object {
        $_.source_id -eq $AnimalSource.source_id -and $_.quote.Contains('수달') }).Count -eq 0 -or
    @($Quotes | Where-Object {
        $_.source_id -eq $ColorSource.source_id -and $_.quote.Contains('파란색') }).Count -eq 0) {
    throw 'Expected source-aware public facts missing; STOP'
}
if ($DocumentWeb.Content.Contains($TestToken) -or $DocumentWeb.Content.Contains($Root)) {
    throw 'Credential or OS path in Document response; STOP'
}
Write-Output "One Document request selected two sources; outcome=$($Result.outcome)"
```

Inspect the public animal/color quotes for question relevance. Preserve the
returned `partial` if that is what M10 produced. The next block is only a
read-only verifier for this **already captured** response; it does not call
the API again. Korean fact checks inside Python use ASCII Unicode escapes,
which survived the prior PowerShell 5.1 stdin path.

```powershell
$DocumentResponse64 = [Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($DocumentWeb.Content))
$VerifyDocumentCode = @'
import base64, hashlib, json, os, sys
from pathlib import Path
from uuid import UUID
from noah.db import connect, local_settings
from noah.document_auto import candidate_hash
from noah.capability_route import SYSTEM_INSTRUCTIONS
project,user,router,task_id,execution_id = (UUID(x) for x in sys.argv[1:6])
root,root_id,animal_name,color_name,response64 = sys.argv[6:11]
response = json.loads(base64.b64decode(response64).decode('utf-8'))
result = response['result']
names = sorted((animal_name,color_name))
raw = {name:(Path(root)/name).read_bytes() for name in names}
body = {name:raw[name].decode('utf-8',errors='strict') for name in names}
def require(value, reason):
    if not value: raise RuntimeError(reason)
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    audit = db.execute('SELECT * FROM noah.routing_audit WHERE router_id=%s',(router,)).fetchone()
    task = db.execute('SELECT * FROM noah.tasks WHERE id=%s',(task_id,)).fetchone()
    execution = db.execute('SELECT * FROM noah.execution_records WHERE id=%s',(execution_id,)).fetchone()
    parent = db.execute('SELECT * FROM noah.auto_document_answer_evidence WHERE execution_id=%s',(execution_id,)).fetchone()
    sources = db.execute('SELECT * FROM noah.auto_document_source_evidence WHERE execution_id=%s ORDER BY source_ordinal',(execution_id,)).fetchall()
    quotes = db.execute('SELECT * FROM noah.auto_document_quote_evidence WHERE execution_id=%s ORDER BY quote_ordinal',(execution_id,)).fetchall()
    require(audit and task and execution and parent,'M12/M10 record missing')
    require(audit['actor_user_id']==user and audit['stage']=='observed' and
            audit['validated_route']=='project.documents.answer.auto' and
            audit['dispatch_prepared'] is True and audit['delegate_result_observed'] is True and
            audit['delegate_capability']=='project.documents.answer.auto' and
            audit['delegate_request_id']==UUID(result['request_id']) and
            audit['delegate_task_id']==task_id and audit['delegate_execution_id']==execution_id and
            audit['observation_class']=='delegate_returned' and audit['http_status']==200 and
            audit['outcome_code']==result['outcome'] and audit['observed_at'] is not None,
            'Router/delegate correlation mismatch')
    require(task['actor_user_id']==user and task['status']=='completed' and
            task['verification_status']=='passed','Task state/owner mismatch')
    require(execution['actor_user_id']==user and execution['task_id']==task_id and
            execution['request_id']==UUID(result['request_id']) and
            execution['capability']=='project.documents.answer.auto' and
            execution['status']=='succeeded' and execution['verified_at'] is not None,
            'M10 Execution mismatch')
    require(db.execute('SELECT count(*) AS n FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchone()['n']==1 and
            db.execute('SELECT count(*) AS n FROM noah.execution_records WHERE actor_user_id=%s',(user,)).fetchone()['n']==1,
            'Router created an extra Task/Execution')
    require(parent['project_id']==project and parent['root_id']==root_id and
            parent['candidate_names']==names and parent['candidate_count']==2 and
            parent['truncated'] is False and parent['selection_model_called'] is True and
            parent['selection_outcome']=='selected' and parent['selected_count']==2 and
            parent['selected_names']==result['selected_document_names'] and
            parent['raw_candidate_names']==result['selected_document_names'] and
            parent['answer_outcome']==result['outcome'] and
            parent['candidate_sha256'].strip()==candidate_hash(str(project),root_id,names) and
            result['candidate_observation']['sha256']==parent['candidate_sha256'].strip(),
            'M10 candidate/selection Evidence mismatch')
    require(len(sources)==2 and 2<=len(quotes)<=3 and len(quotes)==len(result['evidence']),
            'M10 source/quote count mismatch')
    by_id = {}
    for ordinal,source in enumerate(sources,1):
        sid = 'D'+str(ordinal)
        name = result['selected_document_names'][ordinal-1]
        digest = hashlib.sha256(raw[name]).hexdigest()
        api = result['sources'][ordinal-1]
        require(source['source_id']==sid and source['source_ordinal']==ordinal and
                source['document_name']==name and source['observed_at'] is not None and
                source['byte_length']==len(raw[name]) and source['content_sha256'].strip()==digest and
                source['content_encoding']=='utf-8' and source['bom_present'] is False and
                api['source_id']==sid and api['document_name']==name and
                api['byte_length']==len(raw[name]) and api['content_sha256']==digest,
                'M10 source observation mismatch')
        by_id[sid] = name
    seen = set()
    for ordinal,quote in enumerate(quotes,1):
        sid,excerpt = quote['source_id'],quote['quote']
        require(sid in by_id and quote['quote_ordinal']==ordinal,'Quote source/order mismatch')
        start = body[by_id[sid]].find(excerpt)
        api = result['evidence'][ordinal-1]
        require(start>=0 and quote['start_index']==start and
                quote['end_index']==start+len(excerpt) and 1<=len(excerpt)<=240 and
                api['source_id']==sid and api['quote']==excerpt and
                api['start']==start and api['end']==start+len(excerpt) and
                api['content_sha256']==hashlib.sha256(raw[by_id[sid]]).hexdigest(),
                'Exact quote/Unicode position mismatch')
        if by_id[sid]==animal_name: require('\uC218\uB2EC' in excerpt,'Animal fact absent')
        if by_id[sid]==color_name: require('\uD30C\uB780\uC0C9' in excerpt,'Color fact absent')
        seen.add(sid)
    require(seen=={'D1','D2'},'Both sources need quote Evidence')
    for name in ('document_tool_evidence','document_read_evidence','document_answer_evidence',
                 'selected_document_answer_evidence','selected_document_source_evidence',
                 'selected_document_quote_evidence'):
        require(db.execute('SELECT count(*) AS n FROM noah.'+name+' WHERE execution_id=%s',
                           (execution_id,)).fetchone()['n']==0,'Unexpected legacy Evidence')
    stored = json.dumps({'audit':audit,'parent':parent,'sources':sources,'quotes':quotes},
                        default=str,ensure_ascii=False)
    disclosed = json.dumps(response,ensure_ascii=False)
    token = os.environ['NOAH_M12_VERIFY_TOKEN']
    password = local_settings()['POSTGRES_PASSWORD']
    question = os.environ['NOAH_M12_VERIFY_QUESTION']
    require(all(text not in stored for text in body.values()),'Whole document persisted')
    require(all(value not in json.dumps(audit,default=str,ensure_ascii=False)
                for value in (question,token,hashlib.sha256(token.encode()).hexdigest(),
                              password,root,SYSTEM_INSTRUCTIONS,result['answer'])
                if value), 'Sensitive content in routing audit')
    require(root not in stored+disclosed and token not in stored+disclosed and
            password not in stored+disclosed,'Path/credential exposed')
print('M12 router linked exactly one M10 Task/Execution and source-aware Evidence')
'@
$env:NOAH_M12_VERIFY_TOKEN = $TestToken
$env:NOAH_M12_VERIFY_QUESTION = $DocumentQuestion
try {
    $VerifyDocumentCode | & $Python - $ProjectId $UserId $DocumentRouterId `
        $Result.task_id $Result.execution_id $Root $RootId $AnimalName $ColorName $DocumentResponse64
    if ($LASTEXITCODE -ne 0) { throw 'Read-only Document correlation failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M12_VERIFY_TOKEN,Env:NOAH_M12_VERIFY_QUESTION `
        -ErrorAction SilentlyContinue
}
$AfterDocumentJson = Get-NoahSnapshot
Assert-Delta $AfterDocumentJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1; routing_audit=2;
    tasks=1; execution_records=1; auto_document_answer_evidence=1;
    auto_document_source_evidence=2; auto_document_quote_evidence=$Quotes.Count }
Write-Output 'Document route: audit +1, existing M10 Task/Execution +1 pair, correct Evidence'
```

## 7. No Action — send exactly once

This public write-oriented request must route to `no_action`; it must not
write a Memory or invoke either read delegate. M12 adds **only** its third
audit row. A different model choice is an unexpected result: STOP, record
it, and do not automatically retry.

```powershell
$NoActionJson = @{ question='Delete all files and send an email.' } | ConvertTo-Json -Compress
try {
    $NoActionWeb = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' `
        -Body ([Text.Encoding]::UTF8.GetBytes($NoActionJson))
} catch {
    $FailureCode = $null
    if ($_.ErrorDetails.Message) {
        try { $FailureCode = ($_.ErrorDetails.Message | ConvertFrom-Json).failure.code } catch {}
    }
    throw "No Action HTTP result unexpected: HTTP $([int]$_.Exception.Response.StatusCode), code=$FailureCode; do not retry"
}
$NoActionResponse = $NoActionWeb.Content | ConvertFrom-Json
$NoActionRouterId = [string]$NoActionResponse.router_id
try { $null = [guid]::Parse($NoActionRouterId) } catch { throw 'Invalid No Action router_id; STOP' }
if ($NoActionWeb.StatusCode -ne 200 -or $NoActionResponse.status -ne 'succeeded' -or
    $NoActionResponse.routing.outcome -ne 'no_action' -or
    $NoActionResponse.routing.capability -ne $null -or
    $NoActionResponse.routing.stage -ne 'routing' -or
    $NoActionResponse.routing.audit_status -ne 'recorded' -or
    $NoActionResponse.result -ne $null -or
    $NoActionResponse.task_id -ne $null -or
    $NoActionResponse.execution_id -ne $null) {
    throw 'No Action response differs; STOP without retry'
}
$AfterNoActionJson = Get-NoahSnapshot
Assert-Delta $AfterNoActionJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1; routing_audit=3;
    tasks=1; execution_records=1; auto_document_answer_evidence=1;
    auto_document_source_evidence=2; auto_document_quote_evidence=$Quotes.Count }
Write-Output 'No Action: exactly one extra Routing Audit row; no Capability row delta'
```

## 8. Cross-request read-only correlation

This block uses the **three captured router IDs**. It checks one row per ID,
one actor, distinct IDs, exact route and delegate relationship, and no
cross-swapped M3/M10 request IDs. It checks that the only synthetic Task and
Execution belong to M10. It does not print private database rows.

```powershell
$CrossCheckCode = @'
import sys
from uuid import UUID
from noah.db import connect
user,memory_router,document_router,no_action_router = (UUID(x) for x in sys.argv[1:5])
m3_request,m10_request,task,execution = (UUID(x) for x in sys.argv[5:9])
ids = (memory_router,document_router,no_action_router)
if len(set(ids))!=3: raise RuntimeError('Router IDs are not distinct')
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    rows = db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s',
                      (user,)).fetchall()
    if len(rows)!=3 or {r['router_id'] for r in rows}!=set(ids):
        raise RuntimeError('Expected exactly three test-owned audit rows')
    by_id = {r['router_id']:r for r in rows}
    m,d,n = (by_id[i] for i in ids)
    if any(r['stage']!='observed' or r['observed_at'] is None for r in rows):
        raise RuntimeError('Terminal audit observation missing')
    if not (m['validated_route']=='memory.query' and
            m['delegate_request_id']==m3_request and
            m['delegate_task_id'] is None and m['delegate_execution_id'] is None and
            m['delegate_result_observed'] is True):
        raise RuntimeError('M3 audit correlation mismatch')
    if not (d['validated_route']=='project.documents.answer.auto' and
            d['delegate_request_id']==m10_request and
            d['delegate_task_id']==task and d['delegate_execution_id']==execution and
            d['delegate_result_observed'] is True):
        raise RuntimeError('M10 audit correlation mismatch')
    if not (n['validated_route']=='no_action' and
            n['observation_class']=='no_action' and n['delegate_request_id'] is None and
            n['delegate_task_id'] is None and n['delegate_execution_id'] is None and
            n['delegate_capability'] is None and n['dispatch_prepared'] is False and
            n['delegate_result_observed'] is False):
        raise RuntimeError('No Action audit correlation mismatch')
    tasks = db.execute('SELECT id FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT id,task_id FROM noah.execution_records '
                            'WHERE actor_user_id=%s',(user,)).fetchall()
    if tasks!=[{'id':task}] or executions!=[{'id':execution,'task_id':task}]:
        raise RuntimeError('Duplicate or swapped Task/Execution')
print('Three distinct M12 router IDs and only one M10 Task/Execution verified')
'@
$CrossCheckCode | & $Python - $UserId $MemoryRouterId $DocumentRouterId `
    $NoActionRouterId $MemoryResponse.result.request_id $Result.request_id `
    $Result.task_id $Result.execution_id
if ($LASTEXITCODE -ne 0) { throw 'Cross-request correlation failed; STOP' }
if ((Get-NoahSnapshot) -ne $AfterNoActionJson) {
    throw 'Database changed after cross-check; STOP'
}
Write-Output 'M12 three-route correlation and original row fingerprints confirmed'
```

If any route returned `routing.audit_status=unconfirmed`, do **not** call
that a delegate failure. Inspect its last provable audit stage and the
delegate's own result separately. `dispatch_prepared` alone cannot prove a
delegate call began or finished. Do not clean up until the uncertain outcome
has been separately diagnosed. A local PowerShell/Python verifier failure is
not evidence of an API failure; re-run only a corrected **read-only**
verifier against the captured response and existing DB rows.

## 9. Stop this NOAH server and verify ownership before cleanup

Only after all three requests and all read-only checks pass, stop window B
with `Ctrl+C`. Confirm no 8080 listener. Keep PostgreSQL and its named
volume running. Do not stop a pre-existing dedicated Ollama instance, and
never change the unrelated 11434 service. Confirm every synthetic local
artifact and the exact post-run DB delta **before** the first DELETE.

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'NOAH server still listening; STOP cleanup'
}
if ((Get-NoahSnapshot) -ne $AfterNoActionJson) {
    throw 'Post-run DB snapshot changed; STOP cleanup'
}
Assert-Delta $AfterNoActionJson @{ users=1; api_tokens=1; memories=1;
    projects=1; project_memberships=1; routing_audit=3;
    tasks=1; execution_records=1; auto_document_answer_evidence=1;
    auto_document_source_evidence=2; auto_document_quote_evidence=$Quotes.Count }
$ExpectedRoot = Join-Path $Repo ".noah\m12-manual-$RunId"
if ([IO.Path]::GetFullPath($Root) -ne [IO.Path]::GetFullPath($ExpectedRoot) -or
    -not (Test-Path -LiteralPath $Mapping) -or
    -not (Test-Path -LiteralPath $AnimalPath) -or
    -not (Test-Path -LiteralPath $ColorPath) -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Synthetic path or hash changed; STOP cleanup'
}
$MapObject = Get-Content -LiteralPath $Mapping -Raw -Encoding UTF8 | ConvertFrom-Json
$MapEntries = @($MapObject.projects.PSObject.Properties)
if ($MapEntries.Count -ne 1 -or $MapEntries[0].Name -ne $ProjectId -or
    $MapEntries[0].Value.root_id -ne $RootId -or
    $MapEntries[0].Value.document_root -ne $Root) {
    throw 'Mapping no longer belongs only to this run; STOP cleanup'
}
$RootNames = @(Get-ChildItem -LiteralPath $Root -Force | Select-Object -ExpandProperty Name)
$ExpectedNames = @($AnimalName,$ColorName) | Sort-Object
if ($RootNames.Count -ne 2 -or
    ((@($RootNames | Sort-Object) -join '|') -ne ($ExpectedNames -join '|'))) {
    throw 'Unexpected root entry; STOP cleanup'
}
if ((Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'PostgreSQL named volume changed; STOP cleanup'
}
Write-Output 'Server stopped; DB delta, local fixture ownership, hashes, and volume verified'
```

## 10. Exact DB ownership check, then one cleanup transaction

The following one Python block has a **read-only `verify` mode** and a
separate `delete` mode. Run `verify` first. Both modes check the same exact
user/token hash, Memory, project/membership, three router IDs, one M10
Task/Execution, M10 Evidence counts, and absence of extra test-owned rows.
Only `delete` mutates the DB; all its DELETE statements are inside **one
transaction** and require exact row counts. Any assertion/DELETE failure
rolls the transaction back. The existing user/token/Memories/M1–M11 records
and Docker volume are outside these predicates. Do not run this section if
any earlier step stopped or if a router outcome remains uncertain.

```powershell
$OwnershipCode = @'
import hashlib, os, sys
from uuid import UUID
from noah.db import connect
mode = sys.argv[1]
if mode not in ('verify','delete'): raise RuntimeError('Invalid ownership mode')
user,memory,project,task,execution = (UUID(x) for x in sys.argv[2:7])
label,root_id,animal_name,color_name = sys.argv[7:11]
quote_count = int(sys.argv[11])
memory_router,document_router,no_action_router = (UUID(x) for x in sys.argv[12:15])
m3_request,m10_request = (UUID(x) for x in sys.argv[15:17])
token = os.environ['NOAH_M12_OWN_TOKEN']
memory_text = os.environ['NOAH_M12_OWN_MEMORY']
def require(value, reason):
    if not value: raise RuntimeError(reason)
def exact_delete(db, sql, args, expected):
    require(db.execute(sql,args).rowcount==expected,'Unexpected DELETE count')
with connect() as db:
    if mode=='verify': db.execute('SET TRANSACTION READ ONLY')
    u = db.execute('SELECT * FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens = db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s',(user,)).fetchall()
    memories = db.execute('SELECT * FROM noah.memories '
        'WHERE owner_user_id=%s OR created_by=%s OR project_id=%s',
        (user,user,project)).fetchall()
    p = db.execute('SELECT * FROM noah.projects WHERE id=%s',(project,)).fetchone()
    memberships = db.execute('SELECT * FROM noah.project_memberships '
        'WHERE project_id=%s OR user_id=%s',(project,user)).fetchall()
    tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT * FROM noah.execution_records '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    audits = db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s',
                        (user,)).fetchall()
    parent = db.execute('SELECT * FROM noah.auto_document_answer_evidence '
                        'WHERE execution_id=%s',(execution,)).fetchone()
    sources = db.execute('SELECT * FROM noah.auto_document_source_evidence '
                         'WHERE execution_id=%s',(execution,)).fetchall()
    quotes = db.execute('SELECT * FROM noah.auto_document_quote_evidence '
                        'WHERE execution_id=%s',(execution,)).fetchall()
    require(label.startswith('m12-manual-') and len(label)==len('m12-manual-')+32 and
            root_id==label and label[-32:] in animal_name and label[-32:] in color_name,
            'RunId/filename ownership mismatch')
    require(u and u['label']==label,'Synthetic user mismatch')
    require(len(tokens)==1 and tokens[0]['revoked_at'] is None and
            tokens[0]['token_hash']==hashlib.sha256(token.encode('utf-8')).hexdigest(),
            'Synthetic token ownership mismatch')
    require(len(memories)==1 and memories[0]['id']==memory and
            memories[0]['owner_user_id']==user and memories[0]['created_by']==user and
            memories[0]['scope']=='user' and memories[0]['content']==memory_text,
            'Synthetic Memory ownership mismatch')
    require(p and p['label']==label and len(memberships)==1 and
            memberships[0]['project_id']==project and
            memberships[0]['user_id']==user and memberships[0]['can_write'] is False,
            'Synthetic project/read-only membership mismatch')
    require(len(tasks)==1 and tasks[0]['id']==task and
            tasks[0]['status']=='completed' and tasks[0]['verification_status']=='passed',
            'Expected exactly one completed M10 Task')
    require(len(executions)==1 and executions[0]['id']==execution and
            executions[0]['task_id']==task and executions[0]['request_id']==m10_request and
            executions[0]['capability']=='project.documents.answer.auto' and
            executions[0]['status']=='succeeded',
            'Expected exactly one succeeded M10 Execution')
    expected_ids = {memory_router,document_router,no_action_router}
    require(len(audits)==3 and {a['router_id'] for a in audits}==expected_ids and
            all(a['stage']=='observed' and a['actor_user_id']==user for a in audits),
            'Expected exactly three owned terminal M12 audit rows')
    by_id = {a['router_id']:a for a in audits}
    m,d,n = (by_id[i] for i in (memory_router,document_router,no_action_router))
    require(m['validated_route']=='memory.query' and
            m['delegate_request_id']==m3_request and m['delegate_task_id'] is None and
            m['delegate_execution_id'] is None and
            d['validated_route']=='project.documents.answer.auto' and
            d['delegate_request_id']==m10_request and d['delegate_task_id']==task and
            d['delegate_execution_id']==execution and
            n['validated_route']=='no_action' and n['delegate_request_id'] is None and
            n['delegate_task_id'] is None and n['delegate_execution_id'] is None,
            'Router/delegate ownership mismatch')
    require(parent and parent['project_id']==project and parent['root_id']==root_id and
            parent['selected_count']==2 and
            set(parent['selected_names'])=={animal_name,color_name} and
            len(sources)==2 and {s['document_name'] for s in sources}=={animal_name,color_name} and
            len(quotes)==quote_count and 2<=quote_count<=3,
            'M10 Evidence ownership mismatch')
    require(db.execute('SELECT count(*) AS n FROM noah.memory_write_requests '
        'WHERE actor_user_id=%s',(user,)).fetchone()['n']==0,
        'Unexpected synthetic write-key mapping')
    for name in ('document_tool_evidence','document_read_evidence','document_answer_evidence',
                 'selected_document_answer_evidence','selected_document_source_evidence',
                 'selected_document_quote_evidence'):
        require(db.execute('SELECT count(*) AS n FROM noah.'+name+' WHERE execution_id=%s',
                           (execution,)).fetchone()['n']==0,'Unexpected legacy Evidence')
    if mode=='delete':
        exact_delete(db,'DELETE FROM noah.auto_document_quote_evidence '
            'WHERE execution_id=%s',(execution,),quote_count)
        exact_delete(db,'DELETE FROM noah.auto_document_source_evidence '
            'WHERE execution_id=%s',(execution,),2)
        exact_delete(db,'DELETE FROM noah.auto_document_answer_evidence '
            'WHERE execution_id=%s AND project_id=%s',(execution,project),1)
        exact_delete(db,'DELETE FROM noah.execution_records '
            'WHERE id=%s AND actor_user_id=%s AND task_id=%s',(execution,user,task),1)
        exact_delete(db,'DELETE FROM noah.tasks WHERE id=%s AND actor_user_id=%s',(task,user),1)
        exact_delete(db,'DELETE FROM noah.routing_audit '
            'WHERE router_id = ANY(%s) AND actor_user_id=%s',(list(expected_ids),user),3)
        exact_delete(db,'DELETE FROM noah.project_memberships '
            'WHERE project_id=%s AND user_id=%s AND can_write=false',(project,user),1)
        exact_delete(db,'DELETE FROM noah.memories '
            'WHERE id=%s AND owner_user_id=%s AND created_by=%s',(memory,user,user),1)
        exact_delete(db,'DELETE FROM noah.projects WHERE id=%s AND label=%s',(project,label),1)
        exact_delete(db,'DELETE FROM noah.api_tokens '
            'WHERE user_id=%s AND token_hash=%s',
            (user,hashlib.sha256(token.encode('utf-8')).hexdigest()),1)
        exact_delete(db,'DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label),1)
print('Synthetic M12 ownership verified' if mode=='verify' else
      'Only this run synthetic M12/M10 DB rows deleted')
'@
$env:NOAH_M12_OWN_TOKEN = $TestToken
$env:NOAH_M12_OWN_MEMORY = $MemoryText
try {
    $OwnershipCode | & $Python - verify $UserId $MemoryId $ProjectId `
        $Result.task_id $Result.execution_id $RunLabel $RootId `
        $AnimalName $ColorName $Quotes.Count $MemoryRouterId $DocumentRouterId `
        $NoActionRouterId $MemoryResponse.result.request_id $Result.request_id
    if ($LASTEXITCODE -ne 0) { throw 'Read-only ownership verification failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M12_OWN_TOKEN,Env:NOAH_M12_OWN_MEMORY -ErrorAction SilentlyContinue
}
Write-Output 'Read-only ownership verification passed; DB still untouched by cleanup'
```

Only after the preceding block passes, run this **separate** mutating block.
It rechecks all ownership inside the same transaction before deleting. If it
fails, STOP; do not assume a partial cleanup or run another broad deletion.

```powershell
$env:NOAH_M12_OWN_TOKEN = $TestToken
$env:NOAH_M12_OWN_MEMORY = $MemoryText
try {
    $OwnershipCode | & $Python - delete $UserId $MemoryId $ProjectId `
        $Result.task_id $Result.execution_id $RunLabel $RootId `
        $AnimalName $ColorName $Quotes.Count $MemoryRouterId $DocumentRouterId `
        $NoActionRouterId $MemoryResponse.result.request_id $Result.request_id
    if ($LASTEXITCODE -ne 0) { throw 'Cleanup transaction failed or rolled back; STOP' }
} finally {
    Remove-Item Env:NOAH_M12_OWN_TOKEN,Env:NOAH_M12_OWN_MEMORY -ErrorAction SilentlyContinue
}
$AfterDbCleanupJson = Get-NoahSnapshot
if ($AfterDbCleanupJson -ne $BaselineJson) {
    throw 'Original DB counts/private fingerprints not restored; retain local files and STOP'
}
Write-Output 'All original DB table counts and private row fingerprints exactly restored'
```

## 11. Local cleanup only after exact DB restoration

Check the mapping and both original file hashes again. Remove only the one
owned mapping file and the two exact owned Markdown files. Remove the root
only if it is empty; **no recursive deletion**. Keep the existing PostgreSQL
container/volume running.

```powershell
if ([IO.Path]::GetFullPath($Root) -ne
    [IO.Path]::GetFullPath((Join-Path $Repo ".noah\m12-manual-$RunId")) -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Local fixture path/hash changed after DB cleanup; STOP'
}
$MapObject = Get-Content -LiteralPath $Mapping -Raw -Encoding UTF8 | ConvertFrom-Json
$MapEntries = @($MapObject.projects.PSObject.Properties)
if ($MapEntries.Count -ne 1 -or $MapEntries[0].Name -ne $ProjectId -or
    $MapEntries[0].Value.root_id -ne $RootId -or
    $MapEntries[0].Value.document_root -ne $Root) {
    throw 'Mapping ownership changed; STOP'
}
$RootNames = @(Get-ChildItem -LiteralPath $Root -Force | Select-Object -ExpandProperty Name)
if ($RootNames.Count -ne 2 -or
    ((@($RootNames | Sort-Object) -join '|') -ne ($ExpectedNames -join '|'))) {
    throw 'Unexpected root file; STOP'
}
Remove-Item -LiteralPath $Mapping
Remove-Item -LiteralPath $AnimalPath
Remove-Item -LiteralPath $ColorPath
if (@(Get-ChildItem -LiteralPath $Root -Force).Count -ne 0) {
    throw 'Synthetic root is not empty; STOP'
}
Remove-Item -LiteralPath $Root
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Test-Path -LiteralPath $Mapping) -or (Test-Path -LiteralPath $Root) -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'Final DB/local/volume restoration check failed; STOP'
}
$GitAfter = @(git status --short)
if ($LASTEXITCODE -ne 0 -or ($GitAfter -join "`n") -ne ($GitBefore -join "`n")) {
    throw 'Working-tree files changed during manual run; inspect before proceeding'
}
$TestToken = $null
$Headers = $null
Write-Output 'DB restored; synthetic M12 audit/fixture and local root removed; volume preserved'
```

If window C was started **by this procedure**, stop only that dedicated
Ollama window with `Ctrl+C` after the final check. If 11435 was already
running, leave it alone. Do not stop or reconfigure port 11434.

## 12. Completed operator result record

**Status: COMPLETED.** The observations below were reported after the separate
operator run. Updating this record did not repeat an API request or DB check.

| Check | Operator observation |
| --- | --- |
| Memory route: one HTTP request, M3 quote, router audit/request correlation | Passed. `memory.query` returned a grounded synthetic quote and `routing.audit_status=recorded`; M3 response `request_id` correlated with the M12 audit. Routing audit +1; Task/Execution/Evidence +0. |
| Document route: one HTTP request, M10 one Task/Execution, two source quotes, router correlation | Passed. `project.documents.answer.auto` selected both synthetic sources; actual `outcome=partial`. The M12 router correlated with exactly one M10 Task/Execution pair, and source-aware Evidence was verified. `partial` is retained as observed. |
| No Action: one HTTP request, one audit row, zero delegate/Task/Execution/Evidence delta | Passed. `no_action` produced one routing audit row, no delegate invocation, and no Task/Execution/Evidence addition. |
| Three distinct router IDs, original DB rows unchanged | Passed. All three router IDs differed; the synthetic user had exactly one M10 Task/Execution pair across the run. Verifiers used captured responses and read-only DB checks. |
| Targeted synthetic DB/local cleanup and exact baseline restoration | Passed. After NOAH stopped, ownership, path, hash, and volume checks passed. One cleanup transaction removed only synthetic M12/M10 rows; original table counts and private-row fingerprints matched the baseline exactly. The synthetic mapping, two Markdown files, and root were removed. |
| Named PostgreSQL volume retained; no unrelated Ollama change | Passed. PostgreSQL named volume remained. Only the dedicated `127.0.0.1:11435` Ollama started for this procedure was stopped last; the ordinary `11434` service and PostgreSQL were not changed. |
| Verifier-only corrections, if any (state explicitly **no API retry** where true) | No API retry. Each of the three requests was sent exactly once. The working-tree state was the same before and after the manual run. |

Never translate `unconfirmed` into a delegated failure, promote M10 `partial`
to `supported`, or treat a missing terminal audit row as permission to retry.
M5 Recovery Triage does not repair M12 audit rows.
