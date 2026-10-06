# M15 Controlled Explicit Memory Suppression Routing — operator HTTP E2E

> Status: **PASSED (2026-10-06)**. The procedure below was executed once as written; the operator result record is at the end.
> Contract: [M15](46-Fifteenth-Vertical-Slice.md). Automated and actual-model selection results: [M15 validation](47-Fifteenth-Slice-Validation.md).
> Windows PowerShell **5.1**. Keep window A open with its variables until final restoration. Run one block at a time; check the stated result before the next block. Any unexpected or uncertain result means **STOP** and review the captured response and read-only DB state. Never resend the routed suppression POST.

## Scope and safety

This run uses one synthetic user, token, and active user-scope Memory. It sends **five planned HTTP requests**: active direct GET, active normal list GET, **one** mutating `POST /requests/route`, suppressed direct GET, and suppressed normal list GET. A model-free `search_memories()` check runs locally before and after suppression; no Memory Query HTTP/LLM request is added. The routed POST is the **only mutation request**. M14 direct-repeat behavior was manually verified in M14, and M15 routed repeat behavior has deterministic test coverage; there is no deliberate repeat in this E2E.

Do not use an existing user, token, Memory, or personal text. Do not run `python -m noah init`, reset PostgreSQL, delete a volume, broadly delete rows, or touch ordinary Ollama `11434`. Do not print tokens, passwords, token hashes, DB fingerprints, or private row bodies. Do not try to reproduce commit uncertainty, token/ownership races, or `SUPPRESSION_OUTCOME_UNKNOWN` here. An uncertain response **does not** permit cleanup by inference or a second POST.

Windows: **A** holds variables and runs checks; **B** runs working-tree NOAH; **C** runs dedicated Ollama only if port `11435` was absent. No block below is executed merely by opening this document.

## 1. Window A — read-only environment preflight

```powershell
$ErrorActionPreference = 'Stop'
if ($M15RunStarted) { throw 'Runbook already started in window A; STOP' }
$M15RunStarted = $true
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python missing; STOP' }
if ((git branch --show-current) -ne 'main' -or $LASTEXITCODE -ne 0) {
    throw 'Unexpected branch; STOP'
}
$ContractCommit = 'ca37c7a2d9481b96c618274abfaf5bad6f6cb765'
git merge-base --is-ancestor $ContractCommit HEAD
if ($LASTEXITCODE -ne 0) { throw 'M15 contract baseline is not an ancestor; STOP' }
$ExpectedPaths = @(
    'database/011_memory_suppression_routing.sql',
    'docs/01-Project/46-Fifteenth-Vertical-Slice.md',
    'docs/01-Project/47-Fifteenth-Slice-Validation.md',
    'docs/01-Project/48-Fifteenth-Slice-Manual-Validation.md',
    'docs/01-Project/NOAH_DEV_STATUS.md',
    'docs/02-Architecture/Runtime/State.md',
    'noah/capability_route.py','noah/db.py',
    'tests/test_memory_suppression_route.py'
) | Sort-Object
$GitBefore = @(git status --short)
if ($LASTEXITCODE -ne 0) { throw 'Git status unavailable; STOP' }
$ActualPaths = @(git status --porcelain=v1 |
    ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if ($LASTEXITCODE -ne 0 -or
    ($ActualPaths -join '|') -ne ($ExpectedPaths -join '|')) {
    throw 'Unexpected working-tree paths; STOP'
}
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 is occupied; STOP'
}
$Pg = @(docker inspect noah-postgres | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1 -or
    $Pg[0].State.Status -ne 'running' -or
    $Pg[0].Config.Image -ne 'postgres:17') {
    throw 'Expected PostgreSQL 17 container unavailable; STOP'
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
    throw 'Unexpected PostgreSQL volume; STOP'
}
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
$MappingExistedBefore = Test-Path -LiteralPath $Mapping
$MappingHashBefore = if ($MappingExistedBefore) {
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash
} else { $null }
$GenericOllamaBefore = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
$MutationSent = $false
$MutationVerified = $false
$CleanupAttempted = $false
$FixtureAttempted = $false
$ActiveDirectSent = $false
$ActiveListSent = $false
$SuppressedDirectSent = $false
$SuppressedListSent = $false
$RoutedRaw = $null
$Routed = $null
Write-Output 'M15 working tree, free 8080, PostgreSQL 17, and named volume confirmed'
```

Expected: one safe line. The **eight implementation/validation paths plus this runbook** are the only allowed uncommitted paths; a clean tree is not expected. An existing mapping is observed and hashed, never overwritten. STOP on any mismatch.

Check the configured model and dedicated listener. If `11435` already exists, record its PID and **do not stop it later**. If absent, start only the existing Ollama binary in window C; do not pull or replace a model.

```powershell
$ModelName = (& $Python -c 'from noah.ollama import MODEL; print(MODEL)').Trim()
if ($LASTEXITCODE -ne 0 -or $ModelName -ne 'gemma4:12b-it-qat') {
    throw 'Unexpected configured model; STOP'
}
$DedicatedBefore = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
$StartedDedicatedOllama = $false
if ($DedicatedBefore.Count -gt 1 -or
    ($DedicatedBefore.Count -eq 1 -and
     $DedicatedBefore[0].LocalAddress -ne '127.0.0.1')) {
    throw '11435 is not exclusively loopback; STOP'
}
if ($DedicatedBefore.Count -eq 0) {
    $OllamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (-not (Test-Path -LiteralPath $OllamaExe)) {
        throw 'Installed Ollama binary missing; STOP'
    }
    Write-Output 'Start dedicated 11435 in window C, then continue'
} else {
    Write-Output 'Existing dedicated 11435 found; preserve its PID and lifetime'
}
```

If absent, run **only in window C** (leave it open), then set the ownership flag in A. If pre-existing, skip window C and leave the flag false:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

```powershell
if ($DedicatedBefore.Count -eq 0) { $StartedDedicatedOllama = $true }
$DedicatedNow = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($DedicatedNow.Count -ne 1 -or
    $DedicatedNow[0].LocalAddress -ne '127.0.0.1' -or
    ($DedicatedBefore.Count -eq 1 -and
     $DedicatedNow[0].OwningProcess -ne $DedicatedBefore[0].OwningProcess)) {
    throw 'Dedicated Ollama binding/ownership mismatch; STOP'
}
$DedicatedPid = $DedicatedNow[0].OwningProcess
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq $ModelName }).Count -ne 1) {
    throw 'Configured model unavailable on 11435; STOP'
}
Write-Output 'Loopback-only dedicated Ollama and configured model confirmed'
```

Expected: one safe line. The tag request contains no Memory data. STOP unless the binding, owner, and model are exact.

## 2. Window A — private DB baseline and migration

Use one read-only repeatable-read snapshot. Store complete-row fingerprints **only in window A variables**; print no row, fingerprint, token, or private content. PowerShell 5.1 passes multiline Python through stdin.

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
    column = db.execute("""SELECT data_type,is_nullable FROM information_schema.columns
        WHERE table_schema='noah' AND table_name='memories'
          AND column_name='suppressed_at'""").fetchone()
    if column is None or column['data_type'] != 'timestamp with time zone' or column['is_nullable'] != 'YES':
        raise RuntimeError('M14 suppression column absent; STOP')
    checks = {r['conname']:r['definition'] for r in db.execute("""
        SELECT con.conname,pg_get_constraintdef(con.oid) AS definition
        FROM pg_constraint con JOIN pg_class c ON c.oid=con.conrelid
        JOIN pg_namespace n ON n.oid=c.relnamespace
        WHERE n.nspname='noah' AND c.relname='routing_audit'
          AND con.conname IN ('routing_audit_validated_route_check',
            'routing_audit_delegate_capability_check','routing_audit_check1')""")}
    if len(checks) != 3 or any('memory.suppress' not in value for value in checks.values()):
        raise RuntimeError('M15 migration 011 checks absent; STOP')
    for name in tables:
        rows = db.execute('SELECT * FROM noah.' + name).fetchall()
        hashes = sorted(hashlib.sha256(json.dumps(row,sort_keys=True,default=str,
            ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count':len(rows),'rows':hashes}
    out['suppression'] = sorted([
        (str(r['id']),r['suppressed_at'].isoformat() if r['suppressed_at'] else None)
        for r in db.execute('SELECT id,suppressed_at FROM noah.memories')])
    for name in ('tasks','execution_records'):
        out['running_'+name] = db.execute(
            "SELECT count(*) AS n FROM noah."+name+" WHERE status='running'").fetchone()['n']
print(json.dumps(out,sort_keys=True,separators=(',',':')))
'@
function Get-NoahSnapshot {
    $Value = $SnapshotCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw 'Read-only snapshot failed; STOP' }
    return [string]$Value
}
function Assert-M15Delta([string]$CurrentJson, [hashtable]$Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Extra)) {
            throw "Unexpected count in $Name; STOP"
        }
        foreach ($OldHash in @($Property.Value.rows)) {
            if (@($Current.tables.PSObject.Properties[$Name].Value.rows) -notcontains $OldHash) {
                throw "Existing $Name row changed; STOP"
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
        throw "Unexpected private baseline count in $Name; STOP"
    }
}
if ($Baseline.running_tasks -ne 0 -or
    $Baseline.running_execution_records -ne 0) {
    throw 'Pre-existing running Task/Execution; STOP'
}
Write-Output 'Migration 011 and private 18-table baseline confirmed'
```

Expected: one safe line. If the baseline has changed, STOP and review; do not initialize, reset, or remove data.

## 3. Window A — create one owned synthetic fixture

This **one fixture transaction** creates exactly a user, token hash, and active user-scope Memory. It deliberately avoids HTTP save, M4 mapping, Task/Execution, audit, project, and Ollama. The token and Memory body remain only in window A and process environment during each local verifier; never print them.

```powershell
if ($FixtureAttempted) { throw 'Fixture transaction already attempted; STOP' }
$FixtureAttempted = $true
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m15-manual-$RunId"
$MemoryText = "M15 공개 합성 메모 $RunId. 검증 주제는 수달이다."
$Question = '내가 지정한 이 기억을 앞으로 일반 기억 조회와 검색에서 제외해 줘.'
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $TokenBytes = New-Object byte[] 32
    $Rng.GetBytes($TokenBytes)
    $TestToken = [Convert]::ToBase64String($TokenBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
} finally {
    if ($TokenBytes) { [Array]::Clear($TokenBytes,0,$TokenBytes.Length) }
    $Rng.Dispose()
}
$SetupCode = @'
import hashlib, json, os, re
from uuid import uuid4
from noah.db import connect
label = os.environ['NOAH_M15_LABEL']
text = os.environ['NOAH_M15_CONTENT']
token = os.environ['NOAH_M15_TOKEN']
if not re.fullmatch(r'm15-manual-[0-9a-f]{32}',label):
    raise RuntimeError('Synthetic label invalid; STOP')
if label[-32:] not in text or not text.strip() or len(text)>10000 or len(token)<32:
    raise RuntimeError('Synthetic fixture input invalid; STOP')
user_id,memory_id=uuid4(),uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES(%s,%s)',(user_id,label))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES(%s,%s)',
        (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
    db.execute("""INSERT INTO noah.memories(id,owner_user_id,scope,content,created_by)
        VALUES(%s,%s,'user',%s,%s)""",(memory_id,user_id,text,user_id))
    row=db.execute('SELECT * FROM noah.memories WHERE id=%s',(memory_id,)).fetchone()
    if (row is None or row['owner_user_id']!=user_id or row['created_by']!=user_id
            or row['scope']!='user' or row['project_id'] is not None
            or row['content']!=text or row['suppressed_at'] is not None
            or row['provenance']!='explicit_user_request'):
        raise RuntimeError('Synthetic readback failed; transaction rolls back')
print(json.dumps({'user_id':str(user_id),'memory_id':str(memory_id)}))
'@
$env:NOAH_M15_LABEL = $RunLabel
$env:NOAH_M15_CONTENT = $MemoryText
$env:NOAH_M15_TOKEN = $TestToken
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) {
        throw 'Fixture transaction unconfirmed; STOP'
    }
} finally {
    Remove-Item Env:NOAH_M15_LABEL,Env:NOAH_M15_CONTENT,Env:NOAH_M15_TOKEN -ErrorAction SilentlyContinue
}
$Fixture = $FixtureJson | ConvertFrom-Json
$UserId = [string]$Fixture.user_id
$MemoryId = [string]$Fixture.memory_id
$AfterFixtureJson = Get-NoahSnapshot
Assert-M15Delta $AfterFixtureJson @{users=1;api_tokens=1;memories=1}
Write-Output 'One owned synthetic user/token/active Memory created'
```

Expected: one safe line. If fixture commit acknowledgement or readback is uncertain, STOP; do not guess ownership or run cleanup. No local fixture file or mapping is created.

Define this read-only state/search verifier once. It calls the production `search_memories()` SQL path without any model. It prints no token, hash, Memory content, or private row.

```powershell
$VerifyCode = @'
import hashlib, os, sys
from datetime import datetime
from uuid import UUID,uuid4
from noah.db import connect
from noah.service import search_memories
mode=sys.argv[1]
if mode not in ('active','suppressed'):
    raise RuntimeError('Invalid verifier mode; STOP')
user=UUID(os.environ['NOAH_M15_USER'])
memory=UUID(os.environ['NOAH_M15_MEMORY'])
token=os.environ['NOAH_M15_TOKEN']
text=os.environ['NOAH_M15_CONTENT']
label=os.environ['NOAH_M15_LABEL']
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    owner=db.execute('SELECT label FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens=db.execute('SELECT token_hash,revoked_at FROM noah.api_tokens WHERE user_id=%s',
        (user,)).fetchall()
    row=db.execute('SELECT * FROM noah.memories WHERE id=%s',(memory,)).fetchone()
    tasks=db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions=db.execute('SELECT * FROM noah.execution_records WHERE actor_user_id=%s',
        (user,)).fetchall()
    audits=db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s',
        (user,)).fetchall()
    m4=db.execute('SELECT count(*) AS n FROM noah.memory_write_requests WHERE actor_user_id=%s',
        (user,)).fetchone()['n']
    membership=db.execute('SELECT count(*) AS n FROM noah.project_memberships WHERE user_id=%s',
        (user,)).fetchone()['n']
if (owner is None or owner['label']!=label or len(tokens)!=1
        or tokens[0]['token_hash']!=hashlib.sha256(token.encode('utf-8')).hexdigest()
        or tokens[0]['revoked_at'] is not None or row is None
        or row['scope']!='user' or row['owner_user_id']!=user
        or row['created_by']!=user or row['project_id'] is not None
        or row['content']!=text or row['provenance']!='explicit_user_request'
        or m4!=0 or membership!=0):
    raise RuntimeError('Synthetic owner/token/Memory mismatch; STOP')
if mode=='active':
    if row['suppressed_at'] is not None or tasks or executions or audits:
        raise RuntimeError('Fixture is not active and record-free; STOP')
else:
    at=datetime.fromisoformat(os.environ['NOAH_M15_SUPPRESSED_AT'])
    if (row['suppressed_at']!=at or len(tasks)!=1 or len(executions)!=1
            or len(audits)!=1):
        raise RuntimeError('Suppression state or record count mismatch; STOP')
    task,execution,audit=tasks[0],executions[0],audits[0]
    if (str(task['id'])!=os.environ['NOAH_M15_TASK']
            or task['actor_user_id']!=user
            or task['goal']!='Suppress explicitly selected user memory'
            or task['status']!='completed' or task['verification_status']!='passed'
            or str(execution['id'])!=os.environ['NOAH_M15_EXECUTION']
            or str(execution['request_id'])!=os.environ['NOAH_M15_REQUEST']
            or execution['actor_user_id']!=user or execution['task_id']!=task['id']
            or execution['memory_id']!=memory
            or execution['capability']!='memory.suppress'
            or execution['status']!='succeeded' or execution['verified_at'] is None
            or str(audit['router_id'])!=os.environ['NOAH_M15_ROUTER']
            or audit['actor_user_id']!=user or audit['stage']!='observed'
            or audit['validated_route']!='memory.suppress'
            or audit['delegate_capability']!='memory.suppress'
            or not audit['dispatch_prepared'] or not audit['delegate_result_observed']
            or audit['delegate_request_id']!=execution['request_id']
            or audit['delegate_task_id']!=task['id']
            or audit['delegate_execution_id']!=execution['id']
            or audit['observation_class']!='delegate_returned'
            or audit['outcome_code']!='suppressed' or audit['http_status']!=200
            or audit['observed_at'] is None):
        raise RuntimeError('M14/M15 correlation mismatch; STOP')
status,result=search_memories(token,'user',(label[-32:],),uuid4())
if status!=200:
    raise RuntimeError('Production model-free search unavailable; STOP')
found=[m for m in result['memories'] if m['id']==str(memory)]
if mode=='active' and (len(found)!=1 or found[0]['suppressed'] is not False):
    raise RuntimeError('Active Memory absent from normal search; STOP')
if mode=='suppressed' and found:
    raise RuntimeError('Suppressed Memory present in normal search; STOP')
print('Synthetic ownership, M14/M15 state, and model-free search verified')
'@
function Invoke-M15Verify([string]$Mode) {
    $env:NOAH_M15_USER = $UserId
    $env:NOAH_M15_MEMORY = $MemoryId
    $env:NOAH_M15_TOKEN = $TestToken
    $env:NOAH_M15_CONTENT = $MemoryText
    $env:NOAH_M15_LABEL = $RunLabel
    $env:NOAH_M15_SUPPRESSED_AT = if ($Routed) { $SuppressedAtIso } else { '' }
    $env:NOAH_M15_TASK = if ($Routed) { [string]$Routed.result.task_id } else { '' }
    $env:NOAH_M15_EXECUTION = if ($Routed) { [string]$Routed.result.execution_id } else { '' }
    $env:NOAH_M15_REQUEST = if ($Routed) { [string]$Routed.result.request_id } else { '' }
    $env:NOAH_M15_ROUTER = if ($Routed) { [string]$Routed.router_id } else { '' }
    try {
        $VerifyCode | & $Python - $Mode
        if ($LASTEXITCODE -ne 0) { throw 'Read-only M15 verifier failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M15_USER,Env:NOAH_M15_MEMORY,Env:NOAH_M15_TOKEN,Env:NOAH_M15_CONTENT,Env:NOAH_M15_LABEL,Env:NOAH_M15_SUPPRESSED_AT,Env:NOAH_M15_TASK,Env:NOAH_M15_EXECUTION,Env:NOAH_M15_REQUEST,Env:NOAH_M15_ROUTER -ErrorAction SilentlyContinue
    }
}
Invoke-M15Verify active
```

Expected: one safe line. Continue only after fixture delta and active search pass. If this verifier itself has a bug, repair only its read-only code against captured data; do not create another fixture.

## 4. Window B — start current working-tree NOAH

Run only in **window B**; do not run `noah init`. Leave the process attached to B:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

Expected: server remains running. Back in A, verify loopback binding and retain its PID:

```powershell
$ServerListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ServerListeners.Count -ne 1 -or
    $ServerListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'NOAH server is not exclusively loopback-bound; STOP'
}
$ServerPid = $ServerListeners[0].OwningProcess
$BaseUri = 'http://127.0.0.1:8080'
$Headers = @{ Authorization = 'Bearer ' + $TestToken }
function Get-NoahIsoTimestamp([string]$JsonBody) {
    # ConvertFrom-Json may turn ISO strings into local DateTime objects.
    $Match = [regex]::Match($JsonBody,'"suppressed_at"\s*:\s*"([^"\\]+)"')
    if (-not $Match.Success) { throw 'Missing ISO suppression timestamp; STOP' }
    [void][datetimeoffset]::Parse($Match.Groups[1].Value,
        [System.Globalization.CultureInfo]::InvariantCulture)
    return $Match.Groups[1].Value
}
Write-Output 'Working-tree NOAH server listening only on 127.0.0.1:8080'
```

Expected: one safe line. A different listener or PID is a STOP.

## 5. Active observations — direct GET, list GET, model-free search

The next **two HTTP requests are read-only**. Send each once and compare the full DB snapshot to the fixture snapshot after each. Do not print the responses or bearer header.

```powershell
if ($ActiveDirectSent) { throw 'Active direct GET already sent; STOP' }
$ActiveDirectSent = $true
try {
    $ActiveRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories/$MemoryId" -TimeoutSec 15
    $Active = $ActiveRaw.Content | ConvertFrom-Json
} catch { throw 'Active direct GET failed; STOP' }
if ($ActiveRaw.StatusCode -ne 200 -or $Active.status -ne 'succeeded' -or
    $Active.memory.id -ne $MemoryId -or $Active.memory.owner_user_id -ne $UserId -or
    $Active.memory.scope -ne 'user' -or $Active.memory.content -cne $MemoryText -or
    $Active.memory.suppressed -ne $false -or $null -ne $Active.memory.suppressed_at) {
    throw 'Active direct Memory mismatch; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFixtureJson) {
    throw 'Active direct GET changed DB; STOP'
}
Write-Output 'Active direct GET: HTTP 200, exact synthetic content, false/null; DB unchanged'
```

Expected: one safe line. Only then send the list request:

```powershell
if ($ActiveListSent) { throw 'Active list already sent; STOP' }
$ActiveListSent = $true
try {
    $ListRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories?scope=user&limit=100" -TimeoutSec 15
    $ActiveList = $ListRaw.Content | ConvertFrom-Json
} catch { throw 'Active list GET failed; STOP' }
$ActiveItems = @($ActiveList.memories | Where-Object { $null -ne $_ })
if ($ListRaw.StatusCode -ne 200 -or $ActiveList.status -ne 'succeeded' -or
    $ActiveItems.Count -ne 1 -or $ActiveItems[0].id -ne $MemoryId -or
    $ActiveItems[0].content -cne $MemoryText -or
    $ActiveItems[0].suppressed -ne $false -or
    $null -ne $ActiveItems[0].suppressed_at -or
    $null -ne $ActiveList.next_cursor) {
    throw 'Active normal list mismatch; STOP'
}
Invoke-M15Verify active
if ((Get-NoahSnapshot) -ne $AfterFixtureJson) {
    throw 'Active list/search observation changed DB; STOP'
}
Write-Output 'Active list and model-free search include exactly the synthetic Memory'
```

Expected: one active item and production `search_memories()` match; both reads have DB delta zero. Continue only after both blocks pass.

## 6. Routed suppression — **EXECUTE EXACTLY ONCE; NEVER RE-RUN**

This is the **only mutating HTTP request** in this runbook. The question contains no UUID; the structured ID is caller-supplied. PowerShell 5.1 sends UTF-8 bytes with `application/json; charset=utf-8`. The one-shot flag is set **before** network transmission. If the request times out, transport fails, returns an unexpected route/result, or has uncertain outcome: **STOP. Do not resend**, including after a verifier problem. Preserve `$RoutedRaw`/`$Routed` if captured and use only read-only DB checks for diagnosis.

```powershell
if ($MutationSent -or -not $ActiveDirectSent -or -not $ActiveListSent) {
    throw 'Routed suppression one-shot/precondition guard failed; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFixtureJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before mutation; STOP'
}
Invoke-M15Verify active
$ServerNow = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
$ModelNow = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($ServerNow.Count -ne 1 -or $ServerNow[0].OwningProcess -ne $ServerPid -or
    $ServerNow[0].LocalAddress -ne '127.0.0.1' -or
    $ModelNow.Count -ne 1 -or $ModelNow[0].OwningProcess -ne $DedicatedPid -or
    $ModelNow[0].LocalAddress -ne '127.0.0.1') {
    throw 'Server or dedicated model listener changed; STOP'
}
$Payload = [ordered]@{
    question = $Question
    memory_suppress = [ordered]@{ memory_id = $MemoryId }
}
$Json = $Payload | ConvertTo-Json -Depth 4 -Compress
$JsonBytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Json)
$MutationSent = $true
try {
    $RoutedRaw = Invoke-WebRequest -UseBasicParsing -Method Post -Headers $Headers -ContentType 'application/json; charset=utf-8' -Body $JsonBytes -Uri "$BaseUri/requests/route" -TimeoutSec 180
    $Routed = $RoutedRaw.Content | ConvertFrom-Json
    $SuppressedAtIso = Get-NoahIsoTimestamp $RoutedRaw.Content
} catch {
    throw 'Routed suppression HTTP result unconfirmed; STOP, never resend'
}
if ($RoutedRaw.StatusCode -ne 200 -or
    $Routed.status -ne 'succeeded' -or
    $Routed.routing.outcome -ne 'selected' -or
    $Routed.routing.capability -ne 'memory.suppress' -or
    $Routed.routing.stage -ne 'delegated' -or
    $Routed.routing.audit_status -ne 'recorded' -or
    $Routed.result.status -ne 'succeeded' -or
    $Routed.result.outcome -ne 'suppressed' -or
    $Routed.result.memory_id -ne $MemoryId -or
    -not $SuppressedAtIso) {
    throw 'Routed suppression result unexpected or uncertain; STOP, never resend'
}
foreach ($Value in @($Routed.router_id,$Routed.result.request_id,
    $Routed.result.task_id,$Routed.result.execution_id)) {
    $ParsedUuid = [guid]::Empty
    if (-not [guid]::TryParse([string]$Value,[ref]$ParsedUuid)) {
        throw 'Routed/M14 correlation ID invalid; STOP'
    }
}
if ($RoutedRaw.Content.Contains($TestToken) -or
    $RoutedRaw.Content.Contains($MemoryText)) {
    throw 'Unexpected secret or full Memory content in routed response; STOP'
}
Write-Output 'One routed POST: HTTP 200, selected memory.suppress, recorded audit, M14 suppressed response'
```

Expected: one safe line. This checks **response shape**, not yet durable truth. Do not send another POST.

## 7. Read-only durable proof, correlation, and audit minimization

This verifier proves one retained Memory, one M14 Task/Execution, and one M15 routing audit with exact returned IDs, actor, terminal status, and original content. It also rejects prohibited values or columns in the audit without printing them. The full 18-table snapshot must show only fixture **user/token/Memory +1** and routed **Task/Execution/audit +1**; M4 mapping and all project/document Evidence remain unchanged.

```powershell
if (-not $MutationSent -or -not $Routed) {
    throw 'No captured confirmed routed response; STOP'
}
Invoke-M15Verify suppressed
$AuditSecrecyCode = @'
import hashlib,json,os
from uuid import UUID
from noah.db import connect,local_settings
from noah.capability_route import SUPPRESS_SYSTEM_INSTRUCTIONS
user=UUID(os.environ['NOAH_M15_USER'])
router=UUID(os.environ['NOAH_M15_ROUTER'])
target=os.environ['NOAH_M15_MEMORY']
question=os.environ['NOAH_M15_QUESTION']
content=os.environ['NOAH_M15_CONTENT']
token=os.environ['NOAH_M15_TOKEN']
password=local_settings()['POSTGRES_PASSWORD']
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    rows=db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s',(user,)).fetchall()
    names={r['column_name'] for r in db.execute("""SELECT column_name
        FROM information_schema.columns WHERE table_schema='noah'
          AND table_name='routing_audit'""")}
if len(rows)!=1 or rows[0]['router_id']!=router:
    raise RuntimeError('Routing audit ownership/count mismatch; STOP')
forbidden_columns={'question','prompt','raw_model_output','raw_model_json',
                   'payload','response','memory_id','target_memory_id',
                   'token','token_hash','password','content'}
if names & forbidden_columns:
    raise RuntimeError('Forbidden routing audit column exists; STOP')
audit_json=json.dumps(rows[0],sort_keys=True,default=str,ensure_ascii=False)
for value in (question,content,target,token,hashlib.sha256(token.encode()).hexdigest(),
              password,SUPPRESS_SYSTEM_INSTRUCTIONS,'{"route":"memory.suppress"}'):
    if value and value in audit_json:
        raise RuntimeError('Sensitive value copied into routing audit; STOP')
print('Routing audit contains only permitted correlation metadata')
'@
$env:NOAH_M15_USER = $UserId
$env:NOAH_M15_ROUTER = [string]$Routed.router_id
$env:NOAH_M15_MEMORY = $MemoryId
$env:NOAH_M15_QUESTION = $Question
$env:NOAH_M15_CONTENT = $MemoryText
$env:NOAH_M15_TOKEN = $TestToken
try {
    $AuditSecrecyCode | & $Python -
    if ($LASTEXITCODE -ne 0) { throw 'Read-only audit secrecy check failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M15_USER,Env:NOAH_M15_ROUTER,Env:NOAH_M15_MEMORY,Env:NOAH_M15_QUESTION,Env:NOAH_M15_CONTENT,Env:NOAH_M15_TOKEN -ErrorAction SilentlyContinue
}
$AfterMutationJson = Get-NoahSnapshot
Assert-M15Delta $AfterMutationJson @{
    users=1;api_tokens=1;memories=1;tasks=1;execution_records=1;routing_audit=1
}
$MutationVerified = $true
Write-Output 'One M14 Task/Execution and one M15 audit correlated; original Memory retained; unrelated delta zero'
```

Expected: both safe lines; `running` Task/Execution zero. A verifier syntax or comparison mistake is **not** permission to resend the POST. Correct only the read-only verifier against the captured response and DB.

## 8. New suppressed observations — direct GET, normal list, search

These are **two read-only HTTP requests**, followed by the same model-free production SQL search. The direct management lookup must retain the original body and persisted timestamp; fresh normal retrieval must exclude the target.

```powershell
if (-not $MutationVerified -or $SuppressedDirectSent) {
    throw 'Suppressed direct GET precondition/one-shot guard failed; STOP'
}
$SuppressedDirectSent = $true
try {
    $DirectRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories/$MemoryId" -TimeoutSec 15
    $Direct = $DirectRaw.Content | ConvertFrom-Json
    $DirectAtIso = Get-NoahIsoTimestamp $DirectRaw.Content
} catch { throw 'Suppressed direct GET failed; STOP' }
if ($DirectRaw.StatusCode -ne 200 -or $Direct.status -ne 'succeeded' -or
    $Direct.memory.id -ne $MemoryId -or
    $Direct.memory.content -cne $MemoryText -or
    $Direct.memory.suppressed -ne $true -or
    $DirectAtIso -ne $SuppressedAtIso) {
    throw 'Suppressed direct management Memory mismatch; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterMutationJson) {
    throw 'Suppressed direct GET changed DB; STOP'
}
Write-Output 'Suppressed direct GET: original content retained and true/persisted timestamp'
```

Expected: one safe line. Then check new normal list and production model-free search:

```powershell
if (-not $MutationVerified -or $SuppressedListSent) {
    throw 'Suppressed list precondition/one-shot guard failed; STOP'
}
$SuppressedListSent = $true
try {
    $ListRaw = Invoke-WebRequest -UseBasicParsing -Method Get -Headers $Headers -Uri "$BaseUri/memories?scope=user&limit=100" -TimeoutSec 15
    $SuppressedList = $ListRaw.Content | ConvertFrom-Json
} catch { throw 'Suppressed list GET failed; STOP' }
if ($ListRaw.StatusCode -ne 200 -or $SuppressedList.status -ne 'succeeded' -or
    @($SuppressedList.memories | Where-Object { $null -ne $_ }).Count -ne 0 -or
    $null -ne $SuppressedList.next_cursor) {
    throw 'Suppressed target appeared in normal list; STOP'
}
Invoke-M15Verify suppressed
if ((Get-NoahSnapshot) -ne $AfterMutationJson) {
    throw 'Suppressed list/search observation changed DB; STOP'
}
Write-Output 'Fresh normal list and model-free search exclude the suppressed target'
```

Expected: empty normal list, no search match, unchanged DB. Do **not** add `/memories/query` or a routed repeat.

## 9. Stop NOAH; verify exact synthetic ownership before cleanup

Only after the one routed result, DB proof, and all read-only observations pass, press **Ctrl+C in window B**. Do not stop PostgreSQL or either Ollama yet. In A:

```powershell
if (-not $MutationVerified -or -not $SuppressedDirectSent -or -not $SuppressedListSent) {
    throw 'Manual proof incomplete; STOP'
}
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'NOAH still listens on 8080; STOP before cleanup'
}
if ((Get-NoahSnapshot) -ne $AfterMutationJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'Post-suppression state or named volume changed; STOP'
}
Write-Output 'NOAH stopped; exact post-suppression DB state and volume retained'
```

Expected: one safe line. Define a **separate** cleanup verifier. Its `verify` mode is read-only. Its `delete` mode rechecks ownership under row locks, then deletes exactly six synthetic rows in one transaction: M15 audit, M14 Execution, M14 Task, Memory, token, user. Every DELETE must affect exactly one row. A failed check rolls back and stops.

```powershell
$CleanupCode = @'
import hashlib, os, sys
from datetime import datetime
from uuid import UUID
from noah.db import connect
mode=sys.argv[1]
if mode not in ('verify','delete'):
    raise RuntimeError('Invalid cleanup mode; STOP')
user=UUID(os.environ['NOAH_M15_USER'])
memory=UUID(os.environ['NOAH_M15_MEMORY'])
task=UUID(os.environ['NOAH_M15_TASK'])
execution=UUID(os.environ['NOAH_M15_EXECUTION'])
request=UUID(os.environ['NOAH_M15_REQUEST'])
router=UUID(os.environ['NOAH_M15_ROUTER'])
label=os.environ['NOAH_M15_LABEL']
text=os.environ['NOAH_M15_CONTENT']
token_hash=hashlib.sha256(os.environ['NOAH_M15_TOKEN'].encode('utf-8')).hexdigest()
suppressed_at=datetime.fromisoformat(os.environ['NOAH_M15_SUPPRESSED_AT'])
lock=' FOR UPDATE' if mode=='delete' else ''
with connect() as db:
    if mode=='verify':
        db.execute('SET TRANSACTION READ ONLY')
    else:
        db.execute("SET LOCAL lock_timeout='3s'")
    owner=db.execute('SELECT * FROM noah.users WHERE id=%s'+lock,(user,)).fetchone()
    tokens=db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s'+lock,
        (user,)).fetchall()
    row=db.execute('SELECT * FROM noah.memories WHERE id=%s'+lock,(memory,)).fetchone()
    tasks=db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s'+lock,
        (user,)).fetchall()
    executions=db.execute('SELECT * FROM noah.execution_records WHERE actor_user_id=%s'+lock,
        (user,)).fetchall()
    audits=db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s'+lock,
        (user,)).fetchall()
    extra={
        'owned_memories':db.execute("""SELECT count(*) AS n FROM noah.memories
            WHERE owner_user_id=%s OR created_by=%s""",(user,user)).fetchone()['n'],
        'memory_executions':db.execute("""SELECT count(*) AS n FROM noah.execution_records
            WHERE memory_id=%s""",(memory,)).fetchone()['n'],
        'm4':db.execute("""SELECT count(*) AS n FROM noah.memory_write_requests
            WHERE actor_user_id=%s""",(user,)).fetchone()['n'],
        'membership':db.execute("""SELECT count(*) AS n FROM noah.project_memberships
            WHERE user_id=%s""",(user,)).fetchone()['n'],
    }
    if (owner is None or owner['label']!=label or len(tokens)!=1
            or tokens[0]['token_hash']!=token_hash or tokens[0]['revoked_at'] is not None
            or row is None or row['scope']!='user' or row['owner_user_id']!=user
            or row['created_by']!=user or row['project_id'] is not None
            or row['content']!=text or row['provenance']!='explicit_user_request'
            or row['suppressed_at']!=suppressed_at
            or len(tasks)!=1 or len(executions)!=1 or len(audits)!=1
            or extra!={'owned_memories':1,'memory_executions':1,'m4':0,'membership':0}):
        raise RuntimeError('Synthetic cleanup ownership/count mismatch; rollback/STOP')
    t,e,a=tasks[0],executions[0],audits[0]
    if (t['id']!=task or t['actor_user_id']!=user
            or t['goal']!='Suppress explicitly selected user memory'
            or t['status']!='completed' or t['verification_status']!='passed'
            or e['id']!=execution or e['request_id']!=request or e['task_id']!=task
            or e['actor_user_id']!=user or e['memory_id']!=memory
            or e['capability']!='memory.suppress' or e['status']!='succeeded'
            or e['verified_at'] is None
            or a['router_id']!=router or a['actor_user_id']!=user
            or a['stage']!='observed' or a['validated_route']!='memory.suppress'
            or a['delegate_capability']!='memory.suppress'
            or not a['dispatch_prepared'] or not a['delegate_result_observed']
            or a['delegate_request_id']!=request or a['delegate_task_id']!=task
            or a['delegate_execution_id']!=execution
            or a['observation_class']!='delegate_returned'
            or a['outcome_code']!='suppressed' or a['http_status']!=200
            or a['observed_at'] is None):
        raise RuntimeError('M14/M15 execution/audit not owned by this run; rollback/STOP')
    if mode=='delete':
        def exact_delete(sql,values):
            cursor=db.execute(sql,values)
            if cursor.rowcount!=1:
                raise RuntimeError('Exact DELETE count mismatch; rollback/STOP')
        exact_delete("""DELETE FROM noah.routing_audit
            WHERE router_id=%s AND actor_user_id=%s AND stage='observed'
              AND validated_route='memory.suppress'
              AND delegate_execution_id=%s""",(router,user,execution))
        exact_delete("""DELETE FROM noah.execution_records
            WHERE id=%s AND request_id=%s AND task_id=%s AND actor_user_id=%s
              AND memory_id=%s AND capability='memory.suppress' AND status='succeeded'""",
            (execution,request,task,user,memory))
        exact_delete("""DELETE FROM noah.tasks WHERE id=%s AND actor_user_id=%s
            AND status='completed' AND verification_status='passed'""",(task,user))
        exact_delete("""DELETE FROM noah.memories WHERE id=%s AND owner_user_id=%s
            AND created_by=%s AND scope='user' AND content=%s AND suppressed_at=%s""",
            (memory,user,user,text,suppressed_at))
        exact_delete('DELETE FROM noah.api_tokens WHERE user_id=%s AND token_hash=%s',
            (user,token_hash))
        exact_delete('DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label))
print('Read-only synthetic ownership verified' if mode=='verify' else
      'Exactly six synthetic DB rows removed in one transaction')
'@
function Invoke-M15Cleanup([string]$Mode) {
    $env:NOAH_M15_USER = $UserId
    $env:NOAH_M15_MEMORY = $MemoryId
    $env:NOAH_M15_TASK = [string]$Routed.result.task_id
    $env:NOAH_M15_EXECUTION = [string]$Routed.result.execution_id
    $env:NOAH_M15_REQUEST = [string]$Routed.result.request_id
    $env:NOAH_M15_ROUTER = [string]$Routed.router_id
    $env:NOAH_M15_LABEL = $RunLabel
    $env:NOAH_M15_CONTENT = $MemoryText
    $env:NOAH_M15_TOKEN = $TestToken
    $env:NOAH_M15_SUPPRESSED_AT = $SuppressedAtIso
    try {
        $CleanupCode | & $Python - $Mode
        if ($LASTEXITCODE -ne 0) {
            throw 'Synthetic ownership/cleanup transaction failed; STOP'
        }
    } finally {
        Remove-Item Env:NOAH_M15_USER,Env:NOAH_M15_MEMORY,Env:NOAH_M15_TASK,Env:NOAH_M15_EXECUTION,Env:NOAH_M15_REQUEST,Env:NOAH_M15_ROUTER,Env:NOAH_M15_LABEL,Env:NOAH_M15_CONTENT,Env:NOAH_M15_TOKEN,Env:NOAH_M15_SUPPRESSED_AT -ErrorAction SilentlyContinue
    }
}
Invoke-M15Cleanup verify
Write-Output 'Read-only cleanup ownership passed; no DELETE has run'
```

Expected: the two safe lines. If any count, ID, owner, status, timestamp, audit, or volume differs, STOP. Only after this verifier passes, run the separate deletion block **once**:

```powershell
if ($CleanupAttempted -or -not $MutationVerified) {
    throw 'Cleanup already attempted or mutation not verified; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterMutationJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before cleanup transaction; STOP'
}
$CleanupAttempted = $true
Invoke-M15Cleanup delete
$AfterCleanupJson = Get-NoahSnapshot
if ($AfterCleanupJson -ne $BaselineJson) {
    throw 'Original private DB baseline not exactly restored; STOP'
}
Write-Output 'Original 18-table counts, private fingerprints, and suppression states restored'
```

Expected: six exact DELETEs in one transaction and exact baseline restoration. A transaction/commit acknowledgement problem means STOP; do not blindly retry cleanup. No broad DELETE, recursive file deletion, PostgreSQL volume action, or existing private-row modification is permitted.

## 10. Final environment restoration and operator record

No local fixture file or document mapping was created. Compare mapping existence/hash, original named volume, full DB snapshot, ordinary Ollama listener, and exact Git working-tree snapshot. Then clear only this window's synthetic secret variables.

```powershell
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -ne $MappingExistedBefore -or
    ($MappingExistedBefore -and
     (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHashBefore)) {
    throw 'Final DB/volume/mapping restoration failed; STOP'
}
$GenericOllamaAfter = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
if (($GenericOllamaAfter -join '|') -ne ($GenericOllamaBefore -join '|')) {
    throw 'Ordinary Ollama 11434 changed; STOP'
}
$GitAfter = @(git status --short)
if ($LASTEXITCODE -ne 0 -or
    ($GitAfter -join '|') -ne ($GitBefore -join '|')) {
    throw 'Working tree changed during manual run; STOP'
}
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'NOAH server still listening; STOP'
}
$TestToken = $null
$Headers = $null
$JsonBytes = $null
Write-Output 'DB baseline restored; named volume, mapping, Git, and ordinary Ollama unchanged'
```

Expected: one safe line. **Only now**, if `$StartedDedicatedOllama` is true, press **Ctrl+C in window C** and check in A that no `11435` listener remains. If `11435` pre-existed, leave it running with the same PID:

```powershell
$DedicatedAfter = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($StartedDedicatedOllama) {
    if ($DedicatedAfter.Count -ne 0) {
        throw 'This run started 11435, but it is still listening; STOP'
    }
} elseif ($DedicatedAfter.Count -ne 1 -or
          $DedicatedAfter[0].LocalAddress -ne '127.0.0.1' -or
          $DedicatedAfter[0].OwningProcess -ne $DedicatedPid) {
    throw 'Pre-existing dedicated Ollama changed; STOP'
}
Write-Output 'Dedicated Ollama ownership/lifetime verified'
```

Expected: the final safe line. Leave PostgreSQL and ordinary Ollama unchanged.

### Operator result record

**Status: PASSED (2026-10-06).** The table below records only the actual operator run; automated-only failure paths remain explicitly excluded.

| Check | Result / evidence |
| --- | --- |
| Working tree, 8080, PostgreSQL 17, migration 011, named volume, model, listener ownership | PASS — `main`; only the expected nine M15 working-tree paths were present; 8080 was initially free; PostgreSQL 17 was ready; migration 011 checks were present; the named volume matched; `gemma4:12b-it-qat` was available on loopback-only 11435 and listener ownership was verified. |
| Original 18-table counts/private fingerprints, suppression states, running records | PASS — the expected private 18-table baseline and suppression states were captured without printing private rows or fingerprints; running Task/Execution counts were zero. |
| Exactly one owned synthetic user/token/active Memory fixture | PASS — one synthetic user, token, and active user-scope Memory were created in one owned transaction; only `users`, `api_tokens`, and `memories` increased by one. |
| Active direct/list/model-free search and zero read delta | PASS — direct GET returned HTTP 200 with the exact active synthetic Memory; normal list and production model-free search both included it; all read-only observations left the DB unchanged. |
| One actual-model routed suppression POST; HTTP/status/route/M14 result | PASS — exactly one routed POST returned HTTP 200 / `succeeded`; the actual model selected `memory.suppress`, routing audit status was `recorded`, and the delegated M14 result was `suppressed`. No resend occurred. |
| One retained Memory, one M14 Task/Execution, one M15 audit; exact ID correlation | PASS — the original Memory was retained with suppression state, exactly one M14 Task, one Execution, and one M15 Routing Audit were present, and returned correlation IDs matched the durable records. |
| Audit minimization and no M4/project/document Evidence delta | PASS — prohibited audit columns/values were absent; target Memory content, token, question, and target identifier were not copied into the audit; M4 mapping and project/document Evidence remained unchanged. |
| Suppressed direct lookup and fresh normal list/search exclusion | PASS — owner direct lookup retained the original content and persisted suppression timestamp, while a fresh normal list and production model-free search excluded the suppressed Memory; read-only checks caused no DB delta. |
| NOAH stopped; exact six-row synthetic ownership/cleanup transaction | PASS — NOAH was stopped before cleanup; read-only ownership verification passed; exactly six owned synthetic rows were removed in one transaction. |
| Original DB baseline, volume, mapping, Git, and ordinary 11434 restored | PASS — original 18-table counts, private fingerprints, and suppression states were restored exactly; named volume, local mapping, Git working tree, and ordinary Ollama 11434 were unchanged; NOAH no longer listened on 8080. |
| Dedicated 11435 stopped only if started by this run | PASS — this run started the dedicated 11435 listener, it was stopped only after final restoration, and no 11435 listener remained; ownership/lifetime verification passed. |
| Unexpected or uncertain result and any read-only verifier rerun (no API resend) | PASS — no unexpected or uncertain result occurred. No API request was resent and no corrective verifier rerun outside the planned runbook checks was required. |

Automated-only: audit commit acknowledgement uncertainty, `SUPPRESSION_OUTCOME_UNKNOWN`, final audit update uncertainty, token-revocation race, ownership-change race, automatic retry/fallback prohibition paths, and routed `already_suppressed` repeat. This manual run does **not** inject or prove those conditions.
