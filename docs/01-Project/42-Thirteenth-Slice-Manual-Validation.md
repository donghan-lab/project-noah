# M13 manual HTTP E2E validation — operator procedure

> **Status: COMPLETED (operator-reported, 2026-10-02).** This Windows
> PowerShell 5.1 procedure was used against the current, uncommitted M13
> working tree. The operator observations are recorded in section 12; this
> documentation update did not repeat HTTP requests or DB checks.
> Keep **window A** and its variables open through cleanup. Run the NOAH server
> in **window B**; use **window C** for the dedicated Ollama instance only if
> it was not already listening. Execute one block at a time. At every unexpected
> result, **STOP** and retain the captured response and DB state for review.
> Never retry an uncertain HTTP write, run cleanup by assumption, print a token
> or password, or use `docker compose down -v` / volume deletion.

This procedure uses one public synthetic user and token, one public synthetic
Memory, and one client-generated key. It sends **two deliberate write HTTP
requests** to `POST /requests/route`: first save, then a separate same-key,
same-body M4 replay **only after** the first result and DB state are proved.
The M13 contract explicitly asks for this controlled manual replay. The second
request is not an automatic retry and is never sent after an unexpected or
uncertain first result. One read-only `GET /memories/<id>` confirms the normal
read path. Total planned HTTP requests: **three**. `no_action` and failure
injection are already covered by automated tests and add no necessary evidence
to this actual-model write E2E. Do not send those requests here.

The model receives the routing question and a payload-present marker. The
distinct `memory_save.content` is the only stored-text source. A read-only DB
check can prove the stored value and audit contents; it cannot observe the
model's network payload directly. Automated tests separately check that model
messages exclude the content and key. Do not put private content in either
the question or the synthetic Memory.

## 1. Window A — read-only environment and working-tree preflight

Do not proceed unless the M13 files and migration are present, port 8080 is
free, Compose PostgreSQL 17 is healthy, and the existing named volume can be
identified. The `docker inspect | ConvertFrom-Json` form avoids PowerShell 5.1
Go-template quoting problems. This block makes no DB or service changes.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
foreach ($Relative in @('noah\capability_route.py','noah\routing_audit.py',
    'noah\service.py','database\009_memory_save_routing.sql')) {
    if (-not (Test-Path -LiteralPath (Join-Path $Repo $Relative))) {
        throw "M13 implementation file missing: $Relative; STOP"
    }
}
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python missing; STOP' }
if ((git branch --show-current) -ne 'main' -or $LASTEXITCODE -ne 0) {
    throw 'Unexpected Git branch; STOP'
}
if ((git rev-parse HEAD) -ne '16807dda51530a39ff07e7a9c108324579112f95' -or
    $LASTEXITCODE -ne 0) { throw 'Unexpected M13 contract base; STOP' }
$GitBefore = @(git status --short)
if ($LASTEXITCODE -ne 0) { throw 'Git status failed; STOP' }
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Port 8080 is occupied; STOP before starting this server'
}
$Pg = @(docker ps --format '{{.Names}} {{.Image}} {{.Status}}' |
    Where-Object { $_ -match '^noah-postgres postgres:17 Up ' })
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1) {
    throw 'Compose PostgreSQL 17 is not ready; STOP'
}
function Get-NoahVolumeIdentity {
    $Info = @(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1) {
        throw 'Container inspection failed; STOP'
    }
    $Volumes = @($Info[0].Mounts | Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" } | Sort-Object)
    if ($Volumes.Count -ne 1) { throw 'Expected one PostgreSQL named volume; STOP' }
    return $Volumes[0]
}
$VolumeBefore = Get-NoahVolumeIdentity
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
$MappingExistedBefore = Test-Path -LiteralPath $Mapping
$MappingHashBefore = if ($MappingExistedBefore) {
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash
} else { $null }
$GenericOllamaBefore = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
Write-Output 'M13 working tree, free 8080, PostgreSQL 17, and named volume confirmed'
```

Expected: one safe confirmation line. Preserve `$GitBefore`, `$VolumeBefore`,
and `$MappingExistedBefore` in window A. Any guard failure means **STOP**; do
not create a fixture. An existing local document mapping is left untouched.

Read the configured model name from code. If 11435 was already running, it
must be loopback-only and is **not** owned by this procedure. If absent, start
only a new NOAH-dedicated instance in window C. Never change port 11434.

```powershell
$ModelName = (& $Python -c 'from noah.ollama import MODEL; print(MODEL)').Trim()
if ($LASTEXITCODE -ne 0 -or -not $ModelName) { throw 'Model setting unavailable; STOP' }
$ModelListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
$StartedDedicatedOllama = $false
if ($ModelListeners.Count -eq 0) {
    $OllamaExe = Join-Path $env:LOCALAPPDATA 'Programs\Ollama\ollama.exe'
    if (-not (Test-Path -LiteralPath $OllamaExe)) {
        throw 'Local Ollama binary missing; STOP'
    }
    Write-Output 'No 11435 listener: start the dedicated instance in window C'
} else {
    Write-Output 'Existing 11435 listener found: verify it, and do not stop it later'
}
```

Expected: configured model found, with exactly one of the two messages. If
there was no listener, run the following **only in window C**, then set
`$StartedDedicatedOllama = $true` in window A. If a listener already existed,
skip the window C block and keep the flag false.

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

In window A, after starting window C if needed:

```powershell
$ModelListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($ModelListeners.Count -ne 1 -or
    $ModelListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'Dedicated Ollama is not exclusively bound to 127.0.0.1:11435; STOP'
}
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq $ModelName }).Count -ne 1) {
    throw 'Configured model is not registered on 11435; STOP'
}
Write-Output 'Dedicated loopback Ollama and current model confirmed'
```

Expected: local listener and model confirmed. This `/api/tags` check sends no
Memory content. Stop if the binding or model differs.

## 2. Window A — private baseline for all NOAH tables

This read-only snapshot records counts and SHA-256 fingerprints of complete
rows for all 18 existing tables. It prints no row values. Multiline Python is
passed through **stdin** (`$SnapshotCode | & $Python -`) for PowerShell 5.1.
The counts shown below are the post-automation baseline reported in M13's
validation record; if they differ, **STOP and review**, never reset the DB.

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
        raise RuntimeError('PostgreSQL 17 required; STOP')
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
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw 'Read-only snapshot failed; STOP' }
    return [string]$Value
}
function Assert-Delta($CurrentJson, $Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Extra)) { throw "Unexpected DB delta: $Name; STOP" }
        $After = @($Current.tables.PSObject.Properties[$Name].Value.rows)
        foreach ($OldHash in @($Property.Value.rows)) {
            if ($After -notcontains $OldHash) { throw "Existing $Name row changed; STOP" }
        }
    }
    if ($Current.running_tasks -ne 0 -or $Current.running_execution_records -ne 0) {
        throw 'Unexpected running Task/Execution; STOP'
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
        throw "Unexpected baseline count: $Name; STOP"
    }
}
if ($Baseline.running_tasks -ne 0 -or $Baseline.running_execution_records -ne 0) {
    throw 'Running Task/Execution exists; STOP'
}
$MigrationCheck = @'
from noah.db import connect
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    rows = db.execute("""SELECT pg_get_constraintdef(c.oid) AS definition
        FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid
        JOIN pg_namespace n ON n.oid=t.relnamespace
        WHERE n.nspname='noah' AND t.relname='routing_audit'
          AND c.contype='c'""").fetchall()
    matched = [r['definition'] for r in rows if 'memory.save' in r['definition']]
    if len(matched) != 3:
        raise RuntimeError('M13 audit migration not confirmed; STOP')
print('M13 audit route constraints confirmed')
'@
$MigrationCheck | & $Python -
if ($LASTEXITCODE -ne 0) { throw 'M13 migration check failed; STOP' }
Write-Output 'All 18 baseline counts and private fingerprints retained in window A'
```

Expected: migration confirmation and baseline retention; no row contents.
This block does not run `noah init`. It requires zero running Task/Execution.
Keep `$BaselineJson` private and do not export it to a file.

## 3. Window A — create only a synthetic user and token

This is the first DB mutation **for the operator**, and only follows a passed
baseline. Generate a public run label and a cryptographically random token and
key. Neither is printed. The fixture transaction creates **one user and one
token only**; the Memory is created solely through M13 HTTP. There is no
project, membership, local mapping, document root, or fixture file to delete.

```powershell
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m13-manual-$RunId"
$Rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $TokenBytes = New-Object byte[] 32
    $KeyBytes = New-Object byte[] 32
    $Rng.GetBytes($TokenBytes)
    $Rng.GetBytes($KeyBytes)
} finally { $Rng.Dispose() }
$TestToken = [Convert]::ToBase64String($TokenBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
$IdempotencyKey = 'm13-' + [BitConverter]::ToString($KeyBytes).Replace('-','').ToLowerInvariant()
[Array]::Clear($TokenBytes, 0, $TokenBytes.Length)
[Array]::Clear($KeyBytes, 0, $KeyBytes.Length)
$Question = '내가 별도로 제공한 내용을 내 메모로 저장해줘.'
$MemoryText = "M13 공개 합성 기록 $RunId. 검증 동물은 수달이다."
if ($Question.Contains($MemoryText) -or $MemoryText.Length -gt 10000) {
    throw 'Distinct synthetic question/content check failed; STOP'
}
$SetupCode = @'
import hashlib, json, os
from uuid import uuid4
from noah.db import connect
label = os.environ['NOAH_M13_RUN_LABEL']
token = os.environ['NOAH_M13_TEST_TOKEN']
if not label.startswith('m13-manual-') or len(label) != len('m13-manual-') + 32:
    raise RuntimeError('Synthetic label invalid; STOP')
if len(token) < 32:
    raise RuntimeError('Synthetic token invalid; STOP')
user_id = uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES (%s,%s)', (user_id,label))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES (%s,%s)',
        (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
print(json.dumps({'user_id':str(user_id)}))
'@
$env:NOAH_M13_RUN_LABEL = $RunLabel
$env:NOAH_M13_TEST_TOKEN = $TestToken
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) { throw 'Fixture transaction failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M13_RUN_LABEL,Env:NOAH_M13_TEST_TOKEN -ErrorAction SilentlyContinue
}
$UserId = [string]($FixtureJson | ConvertFrom-Json).user_id
$AfterFixtureJson = Get-NoahSnapshot
Assert-Delta $AfterFixtureJson @{ users=1; api_tokens=1 }
Write-Output 'One synthetic user/token created; no token or key displayed'
```

Expected: only the safe confirmation line. If setup or fingerprint comparison
fails, **STOP**; do not run the normal cleanup block on an unverified partial
fixture. Retain the window A variables for later exact ownership checks.

## 4. Window B — launch the current working-tree NOAH server

Run the following in **window B**, only while 8080 remains free. Do not run
`python -m noah init` or start a second server. The current working tree is
the intended M13 code.

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

Expected: the process keeps running without a startup error. In **window A**,
confirm the listener is loopback-only before sending any request:

```powershell
$ServerListeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ServerListeners.Count -ne 1 -or
    $ServerListeners[0].LocalAddress -ne '127.0.0.1') {
    throw 'Expected this NOAH server on 127.0.0.1:8080 only; STOP'
}
Write-Output 'Current working-tree NOAH server is listening on loopback'
```

Expected: one loopback listener. If not, **STOP** without sending HTTP.

## 5. First routed save — **EXECUTE EXACTLY ONCE; NEVER RE-RUN**

PowerShell 5.1 sends **UTF-8 bytes** and explicit charset. Capture the exact
body and key in window A for the later *deliberate* M4 replay. Set the one-shot
flag before the network call, so even a connection loss cannot lead to an
accidental repeat. Do not print `$Headers`, `$BodyBytes`, `$TestToken`, or
`$IdempotencyKey`. A failed or uncertain response is an immediate **STOP**;
inspect the captured error and read-only DB, never resend this router request.

```powershell
if ($FirstWriteSent) { throw 'First routed write was already sent; STOP' }
$RequestObject = @{ question=$Question; memory_save=@{ content=$MemoryText } }
$RequestJson = $RequestObject | ConvertTo-Json -Depth 4 -Compress
$BodyBytes = [System.Text.Encoding]::UTF8.GetBytes($RequestJson)
$Headers = @{ Authorization="Bearer $TestToken"; 'Idempotency-Key'=$IdempotencyKey }
$FirstWriteSent = $true
try {
    $FirstHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
        -Uri 'http://127.0.0.1:8080/requests/route' -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body $BodyBytes -TimeoutSec 120
} catch {
    Write-Output 'First HTTP write returned an error or uncertain transport result; STOP, do not resend'
    if ($_.ErrorDetails.Message) {
        try {
            $FirstError = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Output ("Safe failure code: " + [string]$FirstError.failure.code)
        } catch { Write-Output 'Failure JSON could not be parsed; STOP' }
    }
    throw 'First write did not produce the required captured success; STOP'
}
$First = $FirstHttp.Content | ConvertFrom-Json
if ($FirstHttp.StatusCode -ne 201 -or $First.status -ne 'succeeded' -or
    $First.routing.outcome -ne 'selected' -or
    $First.routing.capability -ne 'memory.save' -or
    $First.routing.stage -ne 'delegated' -or
    $First.routing.audit_status -ne 'recorded' -or
    $First.result.status -ne 'succeeded' -or $First.result.replayed -eq $true -or
    $First.result.evidence.verification -ne 'database_readback' -or
    -not $First.router_id -or -not $First.result.request_id -or
    -not $First.result.task_id -or -not $First.result.execution_id -or
    -not $First.result.evidence.memory_id) {
    throw 'First routed save was not the expected confirmed M1/M13 result; STOP'
}
$FirstRouterId = [string]$First.router_id
$SaveRequestId = [string]$First.result.request_id
$TaskId = [string]$First.result.task_id
$ExecutionId = [string]$First.result.execution_id
$MemoryId = [string]$First.result.evidence.memory_id
Write-Output 'First routed save: HTTP 201, memory.save, verified M1 result, audit recorded'
```

Expected: exactly that confirmation. This is one real write request. A
verifier error after the HTTP response is **not** permission to run it again;
fix the verifier and recheck only the captured `$First` and read-only DB.

## 6. Read-only first-result verification before any replay

Define one reusable verifier. It receives only non-secret UUIDs as arguments;
the public content, synthetic token, question, and key are transient child
environment variables and are removed immediately afterward. It returns
only a safe success line. It checks exact row ownership, original M1/M4 IDs,
M13 audit correlation, forbidden data in audit, and zero synthetic legacy
Evidence. `mode=first` requires one audit row and a single write set;
`mode=replay` later requires two audit rows but the **same** write set.

```powershell
$VerifyCode = @'
import hashlib, json, os, sys
from uuid import UUID
from noah.db import connect, local_settings
from noah.service import _write_fingerprint
mode = sys.argv[1]
if mode not in ('first','replay','ownership'):
    raise RuntimeError('Invalid verifier mode')
user,request,task,execution,memory,router1 = map(UUID, sys.argv[2:8])
router2 = UUID(sys.argv[8]) if sys.argv[8] != '-' else None
label = sys.argv[9]
token = os.environ['NOAH_M13_VERIFY_TOKEN']
key = os.environ['NOAH_M13_VERIFY_KEY']
content = os.environ['NOAH_M13_VERIFY_CONTENT']
question = os.environ['NOAH_M13_VERIFY_QUESTION']
def require(ok, reason):
    if not ok: raise RuntimeError(reason)
with connect() as db:
    db.execute('SET TRANSACTION READ ONLY')
    u = db.execute('SELECT * FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens = db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s',(user,)).fetchall()
    memories = db.execute('SELECT * FROM noah.memories '
        'WHERE owner_user_id=%s OR created_by=%s',(user,user)).fetchall()
    tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT * FROM noah.execution_records '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    mappings = db.execute('SELECT * FROM noah.memory_write_requests '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    audits = db.execute('SELECT * FROM noah.routing_audit '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    require(u and u['label']==label and label.startswith('m13-manual-'),
            'Synthetic user mismatch')
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    key_digest = hashlib.sha256(key.encode('ascii')).hexdigest()
    require(len(tokens)==1 and tokens[0]['token_hash']==token_hash and
            tokens[0]['revoked_at'] is None,'Synthetic token mismatch')
    require(len(memories)==1 and memories[0]['id']==memory and
            memories[0]['scope']=='user' and memories[0]['project_id'] is None and
            memories[0]['owner_user_id']==user and memories[0]['created_by']==user and
            memories[0]['content']==content,'Stored Memory differs from explicit content')
    require(question not in memories[0]['content'] and '\uC218\uB2EC' in memories[0]['content'],
            'Question/content separation failed')
    require(len(tasks)==1 and tasks[0]['id']==task and
            tasks[0]['status']=='completed' and tasks[0]['verification_status']=='passed',
            'Expected one completed M1 Task')
    require(len(executions)==1 and executions[0]['id']==execution and
            executions[0]['task_id']==task and executions[0]['request_id']==request and
            executions[0]['actor_user_id']==user and
            executions[0]['capability']=='memory.save' and
            executions[0]['status']=='succeeded' and
            executions[0]['memory_id']==memory and executions[0]['verified_at'] is not None,
            'Expected one verified M1 Execution')
    require(len(mappings)==1 and mappings[0]['execution_id']==execution and
            mappings[0]['key_digest'].strip()==key_digest and
            mappings[0]['request_fingerprint'].strip()==
                _write_fingerprint(content.strip(),'user',user,None),
            'Expected one M4 key mapping')
    expected_ids = {router1} if mode=='first' else {router1,router2}
    require(None not in expected_ids and len(audits)==len(expected_ids) and
            {a['router_id'] for a in audits}==expected_ids,
            'Unexpected M13 audit count or router IDs')
    by_id = {a['router_id']:a for a in audits}
    for rid in expected_ids:
        a = by_id[rid]
        require(a['actor_user_id']==user and a['stage']=='observed' and
                a['validated_route']=='memory.save' and a['dispatch_prepared'] and
                a['delegate_result_observed'] and
                a['delegate_capability']=='memory.save' and
                a['delegate_request_id']==request and a['delegate_task_id']==task and
                a['delegate_execution_id']==execution and
                a['observation_class']=='delegate_returned' and
                a['outcome_code']=='succeeded' and a['observed_at'] is not None and
                a['http_status']==(201 if rid==router1 else 200),
                'Router-to-M1 correlation mismatch')
    allowed = {'router_id','actor_user_id','stage','validated_route',
        'dispatch_prepared','delegate_result_observed','delegate_capability',
        'delegate_request_id','delegate_task_id','delegate_execution_id',
        'observation_class','http_status','outcome_code','created_at','updated_at',
        'observed_at'}
    actual_columns = {r['column_name'] for r in db.execute("""SELECT column_name
        FROM information_schema.columns WHERE table_schema='noah'
        AND table_name='routing_audit'""")}
    require(actual_columns==allowed,'Routing Audit schema changed; inspect for payload columns')
    password = local_settings()['POSTGRES_PASSWORD']
    forbidden = [question,content,key,key_digest,token,token_hash,password]
    response = os.environ['NOAH_M13_VERIFY_RESPONSE']
    for a in audits:
        raw = json.dumps(a, default=str, ensure_ascii=False)
        require(all(value and (len(value)<8 or value not in raw) for value in forbidden),
                'Sensitive value appeared in Routing Audit')
    require(all(value and (len(value)<8 or value not in response) for value in forbidden),
            'Sensitive value appeared in API response')
    for name in ('document_tool_evidence','document_read_evidence',
        'document_answer_evidence','selected_document_answer_evidence',
        'selected_document_source_evidence','selected_document_quote_evidence',
        'auto_document_answer_evidence','auto_document_source_evidence',
        'auto_document_quote_evidence'):
        require(db.execute('SELECT count(*) AS n FROM noah.'+name+
            ' WHERE execution_id=%s',(execution,)).fetchone()['n']==0,
            'Unexpected document Evidence for M13 Execution')
    require(db.execute('SELECT count(*) AS n FROM noah.project_memberships '
        'WHERE user_id=%s',(user,)).fetchone()['n']==0,
        'Unexpected synthetic membership')
print('Read-only M13 '+mode+' ownership, correlation, and secrecy verified')
'@
function Invoke-M13Verifier($Mode, $SecondRouterId) {
    $env:NOAH_M13_VERIFY_TOKEN = $TestToken
    $env:NOAH_M13_VERIFY_KEY = $IdempotencyKey
    $env:NOAH_M13_VERIFY_CONTENT = $MemoryText
    $env:NOAH_M13_VERIFY_QUESTION = $Question
    $env:NOAH_M13_VERIFY_RESPONSE = $FirstHttp.Content + $(if ($ReplayHttp) { $ReplayHttp.Content } else { '' })
    try {
        $VerifyCode | & $Python - $Mode $UserId $SaveRequestId $TaskId `
            $ExecutionId $MemoryId $FirstRouterId $SecondRouterId $RunLabel
        if ($LASTEXITCODE -ne 0) { throw 'Read-only M13 verification failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M13_VERIFY_TOKEN,Env:NOAH_M13_VERIFY_KEY,Env:NOAH_M13_VERIFY_CONTENT,Env:NOAH_M13_VERIFY_QUESTION,Env:NOAH_M13_VERIFY_RESPONSE -ErrorAction SilentlyContinue
    }
}
Invoke-M13Verifier first '-'
$AfterFirstJson = Get-NoahSnapshot
Assert-Delta $AfterFirstJson @{ users=1; api_tokens=1; memories=1; tasks=1;
    execution_records=1; memory_write_requests=1; routing_audit=1 }
Write-Output 'First write produced exactly one M1/M4 row set and one M13 audit row'
```

Expected: verifier and delta confirmations. **STOP** on any mismatch. The
verifier can be corrected and rerun against `$First` and read-only DB without
another HTTP request. Do not treat a verifier typo as an API failure.

## 7. Deliberate M4 replay — **SECOND WRITE, EXECUTE EXACTLY ONCE**

This block is allowed **only after sections 5 and 6 pass**. It sends the
captured `$BodyBytes` and `$Headers` unchanged. It is an intentional second
request required by the M13 manual contract, not a retry after uncertainty.
Routing may choose `no_action` on a later request; router-level replay is **not
guaranteed**. If it does, record that observation, STOP, and do not send a
third write. If it selects `memory.save`, M4 must return the original IDs and
no new Memory/Task/Execution/mapping. Do not re-run this block.

```powershell
if (-not $FirstWriteSent -or -not $AfterFirstJson -or $ReplaySent) {
    throw 'Replay precondition missing or replay already sent; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterFirstJson) {
    throw 'DB changed since first verification; STOP without replay'
}
$ReplaySent = $true
try {
    $ReplayHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
        -Uri 'http://127.0.0.1:8080/requests/route' -Headers $Headers `
        -ContentType 'application/json; charset=utf-8' -Body $BodyBytes -TimeoutSec 120
} catch {
    Write-Output 'Replay returned an error or uncertain transport result; STOP, do not resend'
    if ($_.ErrorDetails.Message) {
        try {
            $ReplayError = $_.ErrorDetails.Message | ConvertFrom-Json
            Write-Output ("Safe failure code: " + [string]$ReplayError.failure.code)
        } catch { Write-Output 'Failure JSON could not be parsed; STOP' }
    }
    throw 'Deliberate replay did not produce a captured success; STOP'
}
$Replay = $ReplayHttp.Content | ConvertFrom-Json
if ($ReplayHttp.StatusCode -ne 200 -or $Replay.status -ne 'succeeded' -or
    $Replay.routing.capability -ne 'memory.save' -or
    $Replay.routing.outcome -ne 'selected' -or
    $Replay.routing.audit_status -ne 'recorded' -or
    $Replay.result.replayed -ne $true -or
    $Replay.result.status -ne 'succeeded' -or
    $Replay.result.request_id -ne $SaveRequestId -or
    $Replay.result.task_id -ne $TaskId -or
    $Replay.result.execution_id -ne $ExecutionId -or
    $Replay.result.evidence.memory_id -ne $MemoryId -or
    -not $Replay.router_id -or $Replay.router_id -eq $FirstRouterId) {
    throw 'Replay did not return original M4 IDs with a new router ID; STOP'
}
$ReplayRouterId = [string]$Replay.router_id
Write-Output 'Deliberate replay: HTTP 200, replayed true, original M4 IDs retained'
```

Expected: exactly that confirmation. If the model made a different choice,
record it as a routing observation; do not claim an M4 failure and do not
repeat the request. If the reply is uncertain, **STOP before cleanup**.

Verify the replay using only captured responses and a read-only DB snapshot:

```powershell
Invoke-M13Verifier replay $ReplayRouterId
$AfterReplayJson = Get-NoahSnapshot
Assert-Delta $AfterReplayJson @{ users=1; api_tokens=1; memories=1; tasks=1;
    execution_records=1; memory_write_requests=1; routing_audit=2 }
Write-Output 'Two audit rows correlate to one existing M1/M4 write set'
```

Expected: two audit rows but one Memory, Task, Execution, and M4 mapping.
Verifier failure means **STOP**; rerun only the read-only verifier after
review, never the HTTP write.

## 8. Read the synthetic Memory through the existing read API

This is the **third and final planned HTTP request**. It is a read-only GET,
uses only the synthetic token, and cannot create a Task or Execution. Keep
the response in window A; do not display the body, token, or headers.

```powershell
if (-not $AfterReplayJson -or $ReadSent) { throw 'Read precondition missing; STOP' }
$ReadSent = $true
try {
    $ReadHttp = Invoke-WebRequest -UseBasicParsing -Method Get `
        -Uri "http://127.0.0.1:8080/memories/$MemoryId" `
        -Headers @{ Authorization="Bearer $TestToken" } -TimeoutSec 15
} catch { throw 'Synthetic Memory read failed; STOP without write retry' }
$Read = $ReadHttp.Content | ConvertFrom-Json
if ($ReadHttp.StatusCode -ne 200 -or $Read.status -ne 'succeeded' -or
    $Read.memory.id -ne $MemoryId -or $Read.memory.scope -ne 'user' -or
    $Read.memory.owner_user_id -ne $UserId -or
    $Read.memory.content -cne $MemoryText) {
    throw 'Existing read path returned unexpected synthetic Memory; STOP'
}
if ((Get-NoahSnapshot) -ne $AfterReplayJson) {
    throw 'Read-only GET changed DB state or concurrent mutation occurred; STOP'
}
Write-Output 'Existing GET /memories/<id> returned exact synthetic content; DB delta zero'
```

Expected: the exact synthetic content is verified but not printed. **STOP**
on any mismatch; never resend either write.

## 9. Stop NOAH, then verify ownership before cleanup

After all three HTTP results and read-only checks pass, stop **only the NOAH
server in window B** with `Ctrl+C`. Leave PostgreSQL and its named volume
running. In window A, require no 8080 listener, unchanged post-run snapshot,
and unchanged volume. Do not proceed if any request outcome is uncertain.

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'NOAH server still listening; STOP cleanup'
}
if ((Get-NoahSnapshot) -ne $AfterReplayJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -ne $MappingExistedBefore -or
    ($MappingExistedBefore -and
     (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHashBefore)) {
    throw 'DB, volume, or pre-existing mapping changed; STOP cleanup'
}
Invoke-M13Verifier ownership $ReplayRouterId
Assert-Delta (Get-NoahSnapshot) @{ users=1; api_tokens=1; memories=1; tasks=1;
    execution_records=1; memory_write_requests=1; routing_audit=2 }
Write-Output 'Server stopped; exact synthetic ownership/delta and volume rechecked'
```

Expected: ownership passed. A pre-existing local mapping is never modified
by this M13 procedure. If anything differs, **STOP before DELETE**.

## 10. One exact synthetic DB cleanup transaction

The first block defines an ownership script with a **read-only `verify` mode**
and a separate `delete` mode. Run `verify` first. Both modes check the same
exact synthetic user, token hash, one Memory, one Task/Execution, one M4
mapping, and two router IDs. `delete` rechecks ownership within its own
transaction before deleting **only these rows** with exact row counts; any
failure rolls back the transaction. No broad predicates or volume operations
are used. Existing user, token, Memory, Task, Execution and M4 rows are not
targets.

```powershell
$CleanupCode = @'
import hashlib, os, sys
from uuid import UUID
from noah.db import connect
from noah.service import _write_fingerprint
mode = sys.argv[1]
if mode not in ('verify','delete'): raise RuntimeError('Invalid cleanup mode')
user,request,task,execution,memory,router1,router2 = map(UUID,sys.argv[2:9])
label = sys.argv[9]
token = os.environ['NOAH_M13_CLEAN_TOKEN']
key = os.environ['NOAH_M13_CLEAN_KEY']
content = os.environ['NOAH_M13_CLEAN_CONTENT']
def require(ok, reason):
    if not ok: raise RuntimeError(reason)
def exact_delete(db, sql, args, expected):
    require(db.execute(sql,args).rowcount==expected,'Unexpected DELETE count; rollback')
with connect() as db:
    if mode=='verify': db.execute('SET TRANSACTION READ ONLY')
    u = db.execute('SELECT * FROM noah.users WHERE id=%s',(user,)).fetchone()
    tokens = db.execute('SELECT * FROM noah.api_tokens WHERE user_id=%s',(user,)).fetchall()
    memories = db.execute('SELECT * FROM noah.memories '
        'WHERE owner_user_id=%s OR created_by=%s',(user,user)).fetchall()
    tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',(user,)).fetchall()
    executions = db.execute('SELECT * FROM noah.execution_records '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    mappings = db.execute('SELECT * FROM noah.memory_write_requests '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    audits = db.execute('SELECT * FROM noah.routing_audit '
        'WHERE actor_user_id=%s',(user,)).fetchall()
    token_hash = hashlib.sha256(token.encode('utf-8')).hexdigest()
    key_digest = hashlib.sha256(key.encode('ascii')).hexdigest()
    require(label.startswith('m13-manual-') and
            len(label)==len('m13-manual-')+32 and u and u['label']==label,
            'Synthetic user/label ownership mismatch')
    require(len(tokens)==1 and tokens[0]['token_hash']==token_hash and
            tokens[0]['revoked_at'] is None,'Synthetic token ownership mismatch')
    require(len(memories)==1 and memories[0]['id']==memory and
            memories[0]['scope']=='user' and memories[0]['owner_user_id']==user and
            memories[0]['created_by']==user and memories[0]['project_id'] is None and
            memories[0]['content']==content,'Synthetic Memory ownership mismatch')
    require(len(tasks)==1 and tasks[0]['id']==task and tasks[0]['status']=='completed' and
            tasks[0]['verification_status']=='passed','Synthetic Task mismatch')
    require(len(executions)==1 and executions[0]['id']==execution and
            executions[0]['request_id']==request and executions[0]['task_id']==task and
            executions[0]['actor_user_id']==user and
            executions[0]['capability']=='memory.save' and
            executions[0]['status']=='succeeded' and
            executions[0]['memory_id']==memory and executions[0]['verified_at'] is not None,
            'Synthetic Execution mismatch')
    require(len(mappings)==1 and mappings[0]['execution_id']==execution and
            mappings[0]['key_digest'].strip()==key_digest and
            mappings[0]['request_fingerprint'].strip()==
                _write_fingerprint(content.strip(),'user',user,None),
            'Synthetic M4 mapping mismatch')
    require(router1!=router2 and len(audits)==2 and
            {a['router_id'] for a in audits}=={router1,router2} and
            all(a['actor_user_id']==user and a['stage']=='observed' and
                a['validated_route']=='memory.save' and a['delegate_request_id']==request and
                a['delegate_task_id']==task and a['delegate_execution_id']==execution
                for a in audits),'Synthetic routing audit mismatch')
    require(db.execute('SELECT count(*) AS n FROM noah.project_memberships '
        'WHERE user_id=%s',(user,)).fetchone()['n']==0,'Unexpected membership')
    if mode=='delete':
        exact_delete(db,'DELETE FROM noah.routing_audit '
            'WHERE actor_user_id=%s AND router_id IN (%s,%s)',
            (user,router1,router2),2)
        exact_delete(db,'DELETE FROM noah.memory_write_requests '
            'WHERE actor_user_id=%s AND key_digest=%s AND execution_id=%s',
            (user,key_digest,execution),1)
        exact_delete(db,'DELETE FROM noah.execution_records '
            'WHERE id=%s AND actor_user_id=%s AND task_id=%s AND memory_id=%s',
            (execution,user,task,memory),1)
        exact_delete(db,'DELETE FROM noah.tasks WHERE id=%s AND actor_user_id=%s',
            (task,user),1)
        exact_delete(db,'DELETE FROM noah.memories '
            'WHERE id=%s AND owner_user_id=%s AND created_by=%s AND scope=%s',
            (memory,user,user,'user'),1)
        exact_delete(db,'DELETE FROM noah.api_tokens '
            'WHERE user_id=%s AND token_hash=%s',(user,token_hash),1)
        exact_delete(db,'DELETE FROM noah.users WHERE id=%s AND label=%s',
            (user,label),1)
print('Read-only synthetic M13 ownership verified' if mode=='verify' else
      'Only the synthetic M13 rows were removed in one transaction')
'@
function Invoke-M13Cleanup($Mode) {
    $env:NOAH_M13_CLEAN_TOKEN = $TestToken
    $env:NOAH_M13_CLEAN_KEY = $IdempotencyKey
    $env:NOAH_M13_CLEAN_CONTENT = $MemoryText
    try {
        $CleanupCode | & $Python - $Mode $UserId $SaveRequestId $TaskId `
            $ExecutionId $MemoryId $FirstRouterId $ReplayRouterId $RunLabel
        if ($LASTEXITCODE -ne 0) { throw 'M13 cleanup ownership failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M13_CLEAN_TOKEN,Env:NOAH_M13_CLEAN_KEY,Env:NOAH_M13_CLEAN_CONTENT -ErrorAction SilentlyContinue
    }
}
Invoke-M13Cleanup verify
Write-Output 'Read-only ownership passed; no DELETE has run'
```

Expected: read-only ownership pass. This step is safe to repeat if only the
verifier is corrected; it sends no HTTP request. **Only if every previous
step passed**, run the following **separate** mutating block once:

```powershell
if ($CleanupSent) { throw 'Cleanup transaction already attempted; STOP' }
if ((Get-NoahSnapshot) -ne $AfterReplayJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'DB or volume changed before cleanup; STOP'
}
$CleanupSent = $true
Invoke-M13Cleanup delete
$AfterCleanupJson = Get-NoahSnapshot
if ($AfterCleanupJson -ne $BaselineJson) {
    throw 'Original counts/private fingerprints not restored; STOP'
}
Write-Output 'Original 18-table counts and private row fingerprints exactly restored'
```

Expected: one transaction removes only this run's synthetic rows, then exact
baseline equality. If the transaction fails, **STOP**; do not run it again
blindly. If equality fails, retain the state for review. There is no local
fixture file, document root, or mapping created by this procedure.

## 11. Final volume, working-tree, and dedicated-model checks

No file removal is needed. Confirm the existing mapping state and named
volume identity have not changed. Compare `git status --short` with the
captured pre-run state; the pending M13 work and this procedure document must
still be present. Clear only the in-memory synthetic token/key variables
after the DB equality check.

```powershell
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -ne $MappingExistedBefore -or
    ($MappingExistedBefore -and
     (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHashBefore)) {
    throw 'Final DB/volume/mapping check failed; STOP'
}
$GenericOllamaAfter = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
if (($GenericOllamaAfter -join '|') -ne ($GenericOllamaBefore -join '|')) {
    throw 'General Ollama 11434 listener changed; inspect without stopping it'
}
$GitAfter = @(git status --short)
if ($LASTEXITCODE -ne 0 -or
    ($GitAfter -join "`n") -ne ($GitBefore -join "`n")) {
    throw 'Working tree changed during manual run; STOP'
}
$TestToken = $null
$IdempotencyKey = $null
$Headers = $null
$BodyBytes = $null
Write-Output 'DB restored; named volume and working tree unchanged; no local fixture files'
```

Expected: final confirmation, with no credentials printed. **Only if window C
was started by this procedure** (`$StartedDedicatedOllama -eq $true`), stop
that window with `Ctrl+C` now. If 11435 pre-existed, leave it running. Never
stop or reconfigure the unrelated 11434 service.

## 12. Operator result record

**Status: COMPLETED (operator-reported).** The operator executed exactly the
three planned HTTP requests: one first routed write, one deliberate replay
only after the first write and DB state were confirmed, and one read-only GET.
There was **no retry of an uncertain write and no extra router request**.
Keep actual tokens, keys, passwords, Memory bodies, and private fingerprints
out of this record. `no_action`, `WRITE_OUTCOME_UNKNOWN`, and audit failure
injection remained automated-test coverage; they were not invoked manually.

| Check | Operator observation |
| --- | --- |
| M13 working tree, free 8080, PostgreSQL 17, named volume, current model | Passed. The operator started the dedicated Ollama `127.0.0.1:11435` for this run and confirmed loopback-only binding and the current model. |
| Initial 18-table counts/private fingerprints, migration, running states | Passed. Baseline captured; M13 routing-audit constraints present; running Task and Execution were each 0. |
| Synthetic fixture and secret handling | One synthetic user and token created before HTTP. A strong client `Idempotency-Key` was generated; neither token nor key was printed. |
| First routed write, exactly once | HTTP 201, `status=succeeded`, `routing.capability=memory.save`, `routing.outcome=selected`, `routing.audit_status=recorded`; the existing M1 save path completed DB readback verification. |
| Explicit content and M1/M4 ownership | Read-only verifier confirmed the stored user-scope Memory exactly equaled `memory_save.content`, with no question-derived replacement. Memory, Task, Execution, and M4 mapping each increased by exactly one; the router created no additional Task/Execution. |
| First router correlation and sensitive-data boundary | One routing-audit row linked the actual M1/M4 request, Task, and Execution IDs. Routing Audit and API response checks found no question, Memory content, client key/hash, token/password, prompt, or raw model output. |
| Deliberate replay, exactly once after confirmed first result | HTTP 200, `replayed=true`; original request, Task, Execution, and Memory IDs were unchanged. This was a planned M4 replay, **not** a retry after an uncertain outcome. |
| Replay DB delta and router identity | A different router ID was created. Routing Audit total became two; Memory, Task, Execution, and M4 mapping remained one each. |
| Existing read path | One `GET /memories/<id>` returned HTTP 200 and the exact synthetic content; durable DB delta was zero. |
| Server shutdown and cleanup ownership | After stopping NOAH, the operator rechecked exact synthetic ownership, post-run delta, and named volume. The cleanup verifier confirmed one synthetic user/token/Memory/Task/Execution/M4 mapping and the two owned audit rows. |
| One-transaction cleanup and original DB restoration | Only this run's synthetic DB rows were deleted in one transaction. All original 18-table counts and private row fingerprints matched the initial baseline exactly. No local fixture file or mapping was created; the prior mapping state was unchanged. |
| Volume, Git, and Ollama isolation | PostgreSQL named volume and service remained; `git status --short` matched before and after. General Ollama `11434` was unchanged. Only this run's dedicated `11435` instance was stopped with `Ctrl+C` at the end. |

