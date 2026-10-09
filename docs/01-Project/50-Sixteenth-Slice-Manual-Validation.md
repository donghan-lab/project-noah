# M16 — Session Continuity Manual HTTP Validation

> Status: **PASSED** on 2026-10-09 (Asia/Seoul). Sections 1–12 completed in one fresh synthetic run; the separate stopped attempts are recorded below.
> Contract: [49-Sixteenth-Vertical-Slice.md](49-Sixteenth-Vertical-Slice.md).

## Scope and stop rule

Use PowerShell 5.1 window **A** for every variable, HTTP response, and verifier; window **B** for the NOAH server; window **C** only if this run must start dedicated Ollama `127.0.0.1:11435`. Execute each block in order and inspect its stated result before moving on. **STOP** on any mismatch, uncertain result, Python verifier error, unexpected model route, or lost response. Never resend a POST to make a result pass. A verifier failure may be investigated with the captured response and read-only DB queries; it does not authorize another HTTP request or automatic cleanup.

This run creates only one synthetic user/token, one Session, and two `no_action` routing audits. No Memory, project, mapping, document, Task, Execution, or Capability Evidence should be created. The two routing questions are public, synthetic, and unrelated to available capabilities. Actual model selection is a separate observation: if it selects anything other than `no_action`, stop without resending. Do not use existing users, tokens, Memories, or personal documents. Do not run `python -m noah init`, reset a DB, remove a Docker volume, broadly delete rows, or stop ordinary Ollama `11434`. Migration 012 remains installed after synthetic cleanup.

## 1. Window A — repository, listeners, PostgreSQL, and model preflight

The expected uncommitted paths are the seven reviewed M16 implementation/test files and this runbook. If the implementation working tree changes before the operator run, review the actual paths before updating this list; do not bypass the check.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python missing; STOP' }
if ((git branch --show-current) -ne 'main' -or $LASTEXITCODE -ne 0) {
    throw 'Unexpected branch; STOP'
}
$ContractCommit = 'b8ef7bd5333cd2641e65a687be3b9163f5ab1a93'
if ((git rev-parse HEAD) -ne $ContractCommit -or $LASTEXITCODE -ne 0) {
    throw 'M16 implementation baseline changed; STOP'
}
$ExpectedPaths = @(
    'database/012_session_continuity.sql',
    'docs/01-Project/50-Sixteenth-Slice-Manual-Validation.md',
    'noah/__main__.py','noah/capability_route.py','noah/db.py',
    'noah/routing_audit.py','noah/session.py','tests/test_session_continuity.py'
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
$FixtureAttempted = $false
$CreateSent = $false
$FirstRouteSent = $false
$SecondRouteSent = $false
$CloseSent = $false
$ClosedRouteSent = $false
$CleanupAttempted = $false
Write-Output 'M16 working tree, free 8080, PostgreSQL 17, and named volume confirmed'
```

Expected: the single safe confirmation line. **STOP** if the branch, paths, port, DB, or volume differs. Existing mapping is observed and hashed; it is never overwritten or removed.

The routing calls require the configured local model. Reuse a pre-existing loopback-only 11435 listener without taking ownership of it. If absent, start only a dedicated instance in window C; never pull or replace the model.

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
    Write-Output 'Existing dedicated 11435 found; leave it running after this run'
}
```

If absent, execute **only in window C** and leave that window open:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

Then return to A. If 11435 pre-existed, skip C and keep `$StartedDedicatedOllama` false.

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
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq $ModelName }).Count -ne 1) {
    throw 'Configured model unavailable on 11435; STOP'
}
Write-Output 'Loopback-only dedicated Ollama and current model confirmed'
```

Expected: one safe confirmation line. The tags request sends no user data. **STOP** on model or listener mismatch.

## 2. Window A — read-only 19-table baseline and migration 012 proof

Capture full-row SHA-256 fingerprints privately in A variables; print no row, digest, token, or private body. Multiline Python goes through stdin for PowerShell 5.1. Migration 012 must already be applied by the reviewed implementation/test setup; this procedure does not apply migrations. If absent, **STOP before fixture or HTTP work** and review a separate migration plan.

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
 'auto_document_quote_evidence','routing_audit','sessions'
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
        raise RuntimeError('NOAH table set or migration 012 differs; STOP')
    cols = {r['column_name']: r for r in db.execute("""
        SELECT column_name,data_type,is_nullable FROM information_schema.columns
        WHERE table_schema='noah' AND table_name='sessions'""")}
    if set(cols) != {'id','owner_user_id','created_at','closed_at'}:
        raise RuntimeError('M16 Session columns differ; STOP')
    fk = db.execute("""SELECT source_ns.nspname AS source_schema,
               source.relname AS source_table,
               source_attr.attname AS source_column,
               target_ns.nspname AS target_schema,
               target.relname AS target_table,
               target_attr.attname AS target_column,
               array_length(c.conkey,1) AS source_key_count,
               array_length(c.confkey,1) AS target_key_count,
               c.confdeltype
        FROM pg_constraint c
        JOIN pg_class source ON source.oid=c.conrelid
        JOIN pg_namespace source_ns ON source_ns.oid=source.relnamespace
        JOIN pg_class target ON target.oid=c.confrelid
        JOIN pg_namespace target_ns ON target_ns.oid=target.relnamespace
        LEFT JOIN pg_attribute source_attr
          ON source_attr.attrelid=c.conrelid AND source_attr.attnum=c.conkey[1]
        LEFT JOIN pg_attribute target_attr
          ON target_attr.attrelid=c.confrelid AND target_attr.attnum=c.confkey[1]
        WHERE source_ns.nspname='noah' AND c.contype='f'
          AND source.relname IN ('sessions','routing_audit')""").fetchall()
    audit_col = db.execute("""SELECT data_type,is_nullable FROM information_schema.columns
        WHERE table_schema='noah' AND table_name='routing_audit'
          AND column_name='session_id'""").fetchone()
    index = db.execute("""SELECT 1 FROM pg_indexes
        WHERE schemaname='noah' AND tablename='routing_audit'
          AND indexname='routing_audit_session_created_idx'""").fetchone()
    expected_fk = {
        ('noah','sessions','owner_user_id','noah','users','id'),
        ('noah','routing_audit','session_id','noah','sessions','id')
    }
    actual_fk = {(r['source_schema'],r['source_table'],r['source_column'],
                  r['target_schema'],r['target_table'],r['target_column'])
                 for r in fk}
    if (audit_col is None or audit_col['data_type'] != 'uuid'
            or audit_col['is_nullable'] != 'YES' or len(fk) != 2
            or actual_fk != expected_fk
            or any(r['source_key_count'] != 1 or r['target_key_count'] != 1
                   or r['confdeltype'] != 'a' for r in fk)
            or index is None):
        raise RuntimeError('M16 audit FK/index not confirmed; STOP')
    for name in tables:
        rows = db.execute('SELECT * FROM noah.' + name).fetchall()
        hashes = sorted(hashlib.sha256(json.dumps(row,sort_keys=True,default=str,
            ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count':len(rows),'rows':hashes}
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
function Assert-M16Delta([string]$CurrentJson, [hashtable]$Delta) {
    $Current = $CurrentJson | ConvertFrom-Json
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Extra = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Extra)) {
            throw "Unexpected DB delta in $Name; STOP"
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
    sessions=0; document_tool_evidence=0; document_read_evidence=0;
    document_answer_evidence=0; selected_document_answer_evidence=0;
    selected_document_source_evidence=0; selected_document_quote_evidence=0;
    auto_document_answer_evidence=0; auto_document_source_evidence=0;
    auto_document_quote_evidence=0 }
foreach ($Name in $Expected.Keys) {
    if ($Baseline.tables.PSObject.Properties[$Name].Value.count -ne $Expected[$Name]) {
        throw "Unexpected private baseline count in $Name; STOP"
    }
}
if ($Baseline.running_tasks -ne 0 -or
    $Baseline.running_execution_records -ne 0) {
    throw 'Pre-existing running Task/Execution; STOP'
}
Write-Output 'Migration 012 and original 18-table private baseline confirmed'
```

Expected: one safe line and no private rows/fingerprints printed. If any baseline differs, **STOP**. Schema 012 is an expected permanent additive change; synthetic cleanup later restores row state, not schema.

## 3. Window A — one synthetic user/token fixture

This is the first operator DB mutation. One short transaction creates exactly one synthetic principal and token hash. It creates no Memory. Token plaintext stays in A; it is never printed or written to a file.

```powershell
if ($FixtureAttempted) { throw 'Fixture already attempted; STOP' }
$FixtureAttempted = $true
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m16-manual-$RunId"
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
label = os.environ['NOAH_M16_LABEL']
token = os.environ['NOAH_M16_TOKEN']
if not re.fullmatch(r'm16-manual-[0-9a-f]{32}',label) or len(token)<32:
    raise RuntimeError('Synthetic fixture input invalid; STOP')
user_id = uuid4()
with connect() as db:
    db.execute('INSERT INTO noah.users(id,label) VALUES(%s,%s)',(user_id,label))
    db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES(%s,%s)',
        (hashlib.sha256(token.encode('utf-8')).hexdigest(),user_id))
    row = db.execute('SELECT label FROM noah.users WHERE id=%s',(user_id,)).fetchone()
    if row is None or row['label'] != label:
        raise RuntimeError('Synthetic user readback failed; STOP')
print(json.dumps({'user_id':str(user_id)}))
'@
$env:NOAH_M16_LABEL = $RunLabel
$env:NOAH_M16_TOKEN = $TestToken
try {
    $FixtureJson = $SetupCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or -not $FixtureJson) {
        throw 'Fixture transaction unconfirmed; STOP'
    }
} finally {
    Remove-Item Env:NOAH_M16_LABEL,Env:NOAH_M16_TOKEN -ErrorAction SilentlyContinue
}
$UserId = [string]($FixtureJson | ConvertFrom-Json).user_id
$AfterFixtureJson = Get-NoahSnapshot
Assert-M16Delta $AfterFixtureJson @{users=1;api_tokens=1}
Write-Output 'One owned synthetic user/token created; no Memory or execution created'
```

Expected: one safe line. If fixture commit or readback is uncertain, **STOP**. The same A window and its variables must remain open through cleanup.

## 4. Window B — run the current working-tree NOAH server

Start only the server in a separate PowerShell window B. Do not initialize the DB or change Ollama/PostgreSQL. Keep B open for the later deliberate restart.

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
& '.\.venv\Scripts\python.exe' -m noah serve
```

In A, verify one local listener before sending any HTTP request:

```powershell
$ServerNow = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($ServerNow.Count -ne 1 -or $ServerNow[0].LocalAddress -ne '127.0.0.1') {
    throw 'NOAH 8080 listener is not exclusively loopback; STOP'
}
$Headers = @{ Authorization = "Bearer $TestToken" }
$JsonType = 'application/json; charset=utf-8'
$EmptyJson = [System.Text.UTF8Encoding]::new($false).GetBytes('{}')
Write-Output 'Working-tree NOAH listening on loopback 8080'
```

Expected: one safe line. Do not display `$Headers` or `$TestToken`.

## 5. Session create — **one POST only; never re-run**

Create with exact `{}`. Capture the response in A without printing credentials. If it is lost, unexpected, or `SESSION_OUTCOME_UNKNOWN`, **STOP**; do not create a replacement Session or infer a failed commit.

```powershell
if ($CreateSent -or (Get-NoahSnapshot) -ne $AfterFixtureJson) {
    throw 'Create already attempted or DB changed; STOP'
}
$CreateSent = $true
$CreateHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/sessions' -Headers $Headers `
    -ContentType $JsonType -Body $EmptyJson -TimeoutSec 90
$Create = $CreateHttp.Content | ConvertFrom-Json
if ($CreateHttp.StatusCode -ne 201 -or $Create.status -ne 'succeeded' -or
    $Create.outcome -ne 'created' -or $Create.session.status -ne 'active' -or
    $null -ne $Create.session.closed_at -or
    $null -ne $Create.task_id -or $null -ne $Create.execution_id) {
    throw 'Session create response differs; STOP'
}
$SessionId = [string]$Create.session.session_id
if ([guid]::Empty -eq [guid]$SessionId -or
    ([guid]$SessionId).ToString() -cne $SessionId) {
    throw 'Session ID is not canonical; STOP'
}
$AfterCreateJson = Get-NoahSnapshot
Assert-M16Delta $AfterCreateJson @{users=1;api_tokens=1;sessions=1}
Write-Output 'One active synthetic Session created; Task/Execution/audit delta zero'
```

Expected: the safe confirmation line. The returned Session ID is held only in A. The snapshot alone proves counts; the exact owner is checked by the read-only verifier in Section 7 after both routed requests.

## 6. Two scoped, safe routed requests — **each POST once only**

The two public questions deliberately ask for capabilities NOAH does not provide. The actual local model must select `no_action` for this specific run. The Session contract itself does not guarantee semantic model choice. A different valid model route is a **STOP**, with no retry or cleanup by inference. These requests contain no `project_id`, `memory_save`, `memory_suppress`, or idempotency key. Use UTF-8 bytes and the explicit charset for PowerShell 5.1.

```powershell
$ScopedHeaders = @{ Authorization = "Bearer $TestToken"; 'Noah-Session-Id' = $SessionId }
$FirstQuestion = 'What is the weather tomorrow?'
$SecondQuestion = '오늘 달의 위상은 무엇이야?'
function ConvertTo-NoahJsonBytes([string]$Question) {
    $Json = @{question=$Question} | ConvertTo-Json -Compress
    [byte[]]$Bytes = [System.Text.UTF8Encoding]::new($false).GetBytes($Json)
    return ,$Bytes # Keep byte[] as one pipeline object in Windows PowerShell 5.1.
}
$FirstBodyBytes = ConvertTo-NoahJsonBytes $FirstQuestion
$SecondBodyBytes = ConvertTo-NoahJsonBytes $SecondQuestion
$StrictUtf8 = [System.Text.UTF8Encoding]::new($false,$true)
foreach ($Case in @(
    @{ Question=$FirstQuestion; Body=$FirstBodyBytes },
    @{ Question=$SecondQuestion; Body=$SecondBodyBytes }
)) {
    if ($Case.Body -isnot [byte[]]) {
        throw 'JSON request body is not System.Byte[]; STOP before HTTP'
    }
    $Decoded = $StrictUtf8.GetString($Case.Body) | ConvertFrom-Json
    if (@($Decoded.PSObject.Properties).Count -ne 1 -or
        $Decoded.question -cne $Case.Question) {
        throw 'UTF-8 JSON question round-trip differs; STOP before HTTP'
    }
}
if ($FirstRouteSent -or (Get-NoahSnapshot) -ne $AfterCreateJson) {
    throw 'First routed request already attempted or DB changed; STOP'
}
$FirstRouteSent = $true
$FirstHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/requests/route' -Headers $ScopedHeaders `
    -ContentType $JsonType -Body $FirstBodyBytes -TimeoutSec 120
$First = $FirstHttp.Content | ConvertFrom-Json
if ($FirstHttp.StatusCode -ne 200 -or $First.status -ne 'succeeded' -or
    $First.routing.outcome -ne 'no_action' -or $null -ne $First.routing.capability -or
    $First.routing.audit_status -ne 'recorded' -or
    $null -ne $First.task_id -or $null -ne $First.execution_id -or
    $null -ne $First.result) {
    throw 'First route did not produce confirmed no_action; STOP; never resend'
}
$FirstRouterId = [string]$First.router_id
if (([guid]$FirstRouterId).ToString() -cne $FirstRouterId) {
    throw 'First router ID invalid; STOP'
}
$AfterFirstJson = Get-NoahSnapshot
Assert-M16Delta $AfterFirstJson @{users=1;api_tokens=1;sessions=1;routing_audit=1}
Write-Output 'First scoped no_action recorded once; no Task/Execution'
```

Expected: one safe confirmation line. Review the first response/DB state before executing the second block. If a verifier script is wrong, only re-run a read-only verifier against `$First`; never resend the request.

```powershell
if ($SecondRouteSent -or (Get-NoahSnapshot) -ne $AfterFirstJson) {
    throw 'Second routed request already attempted or DB changed; STOP'
}
$SecondRouteSent = $true
$SecondHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/requests/route' -Headers $ScopedHeaders `
    -ContentType $JsonType -Body $SecondBodyBytes -TimeoutSec 120
$Second = $SecondHttp.Content | ConvertFrom-Json
if ($SecondHttp.StatusCode -ne 200 -or $Second.status -ne 'succeeded' -or
    $Second.routing.outcome -ne 'no_action' -or $null -ne $Second.routing.capability -or
    $Second.routing.audit_status -ne 'recorded' -or
    $null -ne $Second.task_id -or $null -ne $Second.execution_id -or
    $null -ne $Second.result) {
    throw 'Second route did not produce confirmed no_action; STOP; never resend'
}
$SecondRouterId = [string]$Second.router_id
if (([guid]$SecondRouterId).ToString() -cne $SecondRouterId -or
    $SecondRouterId -eq $FirstRouterId) {
    throw 'Second router ID invalid or duplicated; STOP'
}
$AfterRoutesJson = Get-NoahSnapshot
Assert-M16Delta $AfterRoutesJson @{users=1;api_tokens=1;sessions=1;routing_audit=2}
Write-Output 'Second scoped no_action recorded once; two distinct router IDs'
```

Expected: one safe confirmation line. No routed HTTP request is retried after any uncertain or unexpected result.

## 7. Read-only Session/audit ownership proof before restart

This proof reads only the synthetic Session and its two audit rows. It rejects an unexpected actor, stage, result, delegate correlation, or extra owned audit without printing question, token, private rows, or fingerprints. Pass multiline Python through stdin.

```powershell
$ProofCode = @'
import sys
from uuid import UUID
from noah.db import connect
user, session, first, second, state = [UUID(x) if i<4 else x
    for i,x in enumerate(sys.argv[1:6])]
if first == second or state not in ('active','closed'):
    raise RuntimeError('Invalid proof arguments; STOP')
with connect() as db:
    db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    row = db.execute('SELECT * FROM noah.sessions WHERE id=%s',(session,)).fetchone()
    if row is None or row['owner_user_id'] != user:
        raise RuntimeError('Synthetic Session owner differs; STOP')
    if (row['closed_at'] is None) != (state == 'active'):
        raise RuntimeError('Session lifecycle differs; STOP')
    if row['closed_at'] is not None and row['closed_at'] < row['created_at']:
        raise RuntimeError('Invalid close timestamp; STOP')
    rows = db.execute('SELECT * FROM noah.routing_audit WHERE session_id=%s',
        (session,)).fetchall()
    if len(rows) != 2 or {r['router_id'] for r in rows} != {first,second}:
        raise RuntimeError('Session has unexpected audit references; STOP')
    other = db.execute('SELECT count(*) AS n FROM noah.routing_audit WHERE actor_user_id=%s',
        (user,)).fetchone()['n']
    if other != 2:
        raise RuntimeError('Synthetic actor has extra audit rows; STOP')
    for r in rows:
        if (r['actor_user_id'] != user or r['stage'] != 'observed'
                or r['validated_route'] != 'no_action'
                or r['observation_class'] != 'no_action'
                or r['outcome_code'] != 'no_action' or r['http_status'] != 200
                or r['dispatch_prepared'] or r['delegate_result_observed']
                or any(r[k] is not None for k in ('delegate_capability',
                    'delegate_request_id','delegate_task_id','delegate_execution_id'))):
            raise RuntimeError('M12 no_action audit semantics differ; STOP')
print('Owned Session and exactly two no_action audit references verified')
'@
function Invoke-M16Proof([string]$State) {
    $ProofCode | & $Python - $UserId $SessionId $FirstRouterId $SecondRouterId $State
    if ($LASTEXITCODE -ne 0) { throw 'Read-only M16 proof failed; STOP' }
}
Invoke-M16Proof active
```

Expected: the safe proof line. **STOP** if anything differs. Session create/read/close are not M12 routing audits; the two `no_action` requests own the only new audit rows.

## 8. Stop and restart NOAH; inspect the same Session

Stop window B with **Ctrl+C**. In A, require port 8080 to be free and the exact post-route DB snapshot to remain. Do not stop PostgreSQL or Ollama.

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
    (Get-NoahSnapshot) -ne $AfterRoutesJson) {
    throw 'NOAH not stopped or DB changed before restart; STOP'
}
Write-Output 'NOAH stopped; Session and audits remain durable'
```

Expected: safe line. Restart **the same command** in B:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
& '.\.venv\Scripts\python.exe' -m noah serve
```

In A, inspect bounded references as the same synthetic owner. `limit=1` exercises two pages, without creating an audit. The order is newest audit first; compare the set of IDs, not the order in which the HTTP calls were sent.

```powershell
$Restarted = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($Restarted.Count -ne 1 -or $Restarted[0].LocalAddress -ne '127.0.0.1') {
    throw 'Restarted NOAH listener mismatch; STOP'
}
$InspectUri = "http://127.0.0.1:8080/sessions/$SessionId"
$Page1Http = Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$InspectUri`?limit=1" -Headers $Headers -TimeoutSec 30
$Page1 = $Page1Http.Content | ConvertFrom-Json
if ($Page1Http.StatusCode -ne 200 -or $Page1.status -ne 'succeeded' -or
    $Page1.session.session_id -ne $SessionId -or
    $Page1.session.status -ne 'active' -or
    @($Page1.interactions).Count -ne 1 -or -not $Page1.next_cursor -or
    $null -ne $Page1.task_id -or $null -ne $Page1.execution_id) {
    throw 'First bounded Session inspection differs; STOP'
}
$Cursor = [uri]::EscapeDataString([string]$Page1.next_cursor)
$Page2Http = Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "$InspectUri`?limit=1&cursor=$Cursor" -Headers $Headers -TimeoutSec 30
$Page2 = $Page2Http.Content | ConvertFrom-Json
$ReturnedIds = @([string]$Page1.interactions[0].router_id,
                 [string]$Page2.interactions[0].router_id)
$ExpectedIdSet = @($FirstRouterId,$SecondRouterId) | Sort-Object
$ReturnedIdSet = @($ReturnedIds | Sort-Object)
if ($Page2Http.StatusCode -ne 200 -or $Page2.status -ne 'succeeded' -or
    $Page2.session.session_id -ne $SessionId -or
    @($Page2.interactions).Count -ne 1 -or $null -ne $Page2.next_cursor -or
    ($ReturnedIdSet -join '|') -ne ($ExpectedIdSet -join '|') -or
    (Get-NoahSnapshot) -ne $AfterRoutesJson) {
    throw 'Restart continuity or bounded references differ; STOP'
}
Invoke-M16Proof active
Write-Output 'Same active Session and two bounded router references survived restart'
```

Expected: the safe continuity line; no durable DB delta from inspection. **STOP** on cursor, ownership, reference, or snapshot mismatch. A verifier error can be corrected and rerun against the same GET responses/DB without sending a new routed POST.

## 9. Close Session — **one POST only; never re-run**

Close the same Session with exact `{}`. A lost or unknown close acknowledgement is **not** a proven failure; inspect read-only and stop for review rather than repeating close.

```powershell
if ($CloseSent -or (Get-NoahSnapshot) -ne $AfterRoutesJson) {
    throw 'Close already attempted or DB changed; STOP'
}
$CloseSent = $true
$CloseHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri "http://127.0.0.1:8080/sessions/$SessionId/close" `
    -Headers $Headers -ContentType $JsonType -Body $EmptyJson -TimeoutSec 90
$Close = $CloseHttp.Content | ConvertFrom-Json
if ($CloseHttp.StatusCode -ne 200 -or $Close.status -ne 'succeeded' -or
    $Close.outcome -ne 'closed' -or $Close.session.session_id -ne $SessionId -or
    $Close.session.status -ne 'closed' -or -not $Close.session.closed_at -or
    $null -ne $Close.task_id -or $null -ne $Close.execution_id) {
    throw 'Session close response differs; STOP'
}
$AfterCloseJson = Get-NoahSnapshot
Assert-M16Delta $AfterCloseJson @{users=1;api_tokens=1;sessions=1;routing_audit=2}
Invoke-M16Proof closed
$BeforeClose = $AfterRoutesJson | ConvertFrom-Json
$AfterClose = $AfterCloseJson | ConvertFrom-Json
if ((@($BeforeClose.tables.routing_audit.rows) -join '|') -ne
    (@($AfterClose.tables.routing_audit.rows) -join '|')) {
    throw 'Existing audit rows changed on Session close; STOP'
}
Write-Output 'Session closed once; two prior audit rows unchanged'
```

Expected: one safe line. Closure creates no Task, Execution, Evidence, or routing audit.

## 10. Closed Session denies a new association — **one POST only**

Use a third safe question only to confirm the closed header is rejected **before** model/audit/delegate. HTTP 409 `SESSION_CLOSED` is expected. Do not resend on error or uncertainty. In PowerShell 5.1, parse `ErrorDetails.Message` from the HTTP exception; the response stream may be empty.

```powershell
if ($ClosedRouteSent -or (Get-NoahSnapshot) -ne $AfterCloseJson) {
    throw 'Closed-Session probe already attempted or DB changed; STOP'
}
$ClosedRouteSent = $true
try {
    $Unexpected = Invoke-WebRequest -UseBasicParsing -Method Post `
        -Uri 'http://127.0.0.1:8080/requests/route' -Headers $ScopedHeaders `
        -ContentType $JsonType `
        -Body (ConvertTo-NoahJsonBytes 'What is the public tide forecast?') -TimeoutSec 120
    throw 'Closed Session unexpectedly accepted a routed request; STOP'
} catch [System.Net.WebException] {
    $ClosedHttpStatus = [int]$_.Exception.Response.StatusCode
    if (-not $_.ErrorDetails.Message) { throw 'Failure body unavailable; STOP' }
    $ClosedDenial = $_.ErrorDetails.Message | ConvertFrom-Json
}
if ($ClosedHttpStatus -ne 409 -or
    $ClosedDenial.failure.code -ne 'SESSION_CLOSED' -or
    $null -ne $ClosedDenial.task_id -or
    $null -ne $ClosedDenial.execution_id -or
    (Get-NoahSnapshot) -ne $AfterCloseJson) {
    throw 'Closed-Session denial or zero-delta check failed; STOP'
}
Invoke-M16Proof closed
Write-Output 'Closed Session rejected new association before audit/model/delegate'
```

Expected: one safe denial line. The full DB snapshot must be byte-for-byte equal to the post-close snapshot. No new audit row or capability record is permitted.

## 11. Stop NOAH; exact synthetic ownership and cleanup

Stop window B with **Ctrl+C**. Before any DELETE, confirm port 8080 is free, the named volume and post-close snapshot remain, and the exact synthetic owner/Session/router IDs still match. The verifier and deletion are **separate blocks**. If any check fails, **STOP** without attempting cleanup. No Session/migration rollback or recursive file cleanup is needed.

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
    (Get-NoahSnapshot) -ne $AfterCloseJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'NOAH still running or DB/volume changed before cleanup; STOP'
}
Invoke-M16Proof closed
Write-Output 'NOAH stopped; post-close state, exact owner, and volume retained'
```

Expected: the proof line and safe confirmation line. Prepare the exact ownership verifier. It checks that this actor has only the one token, Session and two audits, and no Memory, Task, Execution, project, membership, or M4 mapping. It checks the synthetic label and token hash without printing them. The SQL DELETE predicates include the exact owner and IDs, and everything runs in one transaction.

```powershell
$CleanupCode = @'
import hashlib, os, re, sys
from uuid import UUID
from noah.db import connect
mode = sys.argv[1]
user,session,first,second = map(UUID,sys.argv[2:6])
label = os.environ['NOAH_M16_LABEL']
token_hash = hashlib.sha256(os.environ['NOAH_M16_TOKEN'].encode('utf-8')).hexdigest()
if mode not in ('verify','delete') or first == second or not re.fullmatch(
        r'm16-manual-[0-9a-f]{32}',label):
    raise RuntimeError('Cleanup input invalid; STOP')
with connect() as db:
    if mode == 'verify':
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    else:
        db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    actor = db.execute('SELECT id,label FROM noah.users WHERE id=%s',(user,)).fetchone()
    if actor is None or actor['label'] != label:
        raise RuntimeError('Synthetic user ownership differs; STOP')
    tokens = db.execute('SELECT token_hash FROM noah.api_tokens WHERE user_id=%s',
        (user,)).fetchall()
    if len(tokens) != 1 or tokens[0]['token_hash'] != token_hash:
        raise RuntimeError('Synthetic token ownership differs; STOP')
    sessions = db.execute('SELECT id,closed_at FROM noah.sessions WHERE owner_user_id=%s',
        (user,)).fetchall()
    if len(sessions) != 1 or sessions[0]['id'] != session or sessions[0]['closed_at'] is None:
        raise RuntimeError('Synthetic Session ownership/state differs; STOP')
    audits = db.execute('SELECT router_id,session_id,stage,validated_route,actor_user_id '
        'FROM noah.routing_audit WHERE actor_user_id=%s',(user,)).fetchall()
    if (len(audits) != 2 or {r['router_id'] for r in audits} != {first,second}
            or any(r['session_id'] != session or r['stage'] != 'observed'
                   or r['validated_route'] != 'no_action' for r in audits)):
        raise RuntimeError('Synthetic audit ownership differs; STOP')
    checks = {
        'memories':'owner_user_id','tasks':'actor_user_id',
        'execution_records':'actor_user_id',
        'memory_write_requests':'actor_user_id',
        'project_memberships':'user_id'
    }
    for table,column in checks.items():
        n = db.execute('SELECT count(*) AS n FROM noah.'+table+' WHERE '+column+'=%s',
            (user,)).fetchone()['n']
        if n != 0:
            raise RuntimeError('Unexpected synthetic dependent row; STOP')
    if mode == 'delete':
        def exact(sql,params,expected):
            rows = db.execute(sql+' RETURNING 1',params).fetchall()
            if len(rows) != expected:
                raise RuntimeError('Exact deletion count differs; rollback and STOP')
        exact('DELETE FROM noah.routing_audit WHERE actor_user_id=%s '
              'AND session_id=%s AND router_id IN (%s,%s)',
              (user,session,first,second),2)
        exact('DELETE FROM noah.sessions WHERE id=%s AND owner_user_id=%s '
              'AND closed_at IS NOT NULL',(session,user),1)
        exact('DELETE FROM noah.api_tokens WHERE user_id=%s AND token_hash=%s',
              (user,token_hash),1)
        exact('DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label),1)
print('Read-only M16 ownership verified' if mode=='verify' else
      'Only this run synthetic M16 rows removed in one transaction')
'@
function Invoke-M16Cleanup([string]$Mode) {
    $env:NOAH_M16_LABEL = $RunLabel
    $env:NOAH_M16_TOKEN = $TestToken
    try {
        $CleanupCode | & $Python - $Mode $UserId $SessionId $FirstRouterId $SecondRouterId
        if ($LASTEXITCODE -ne 0) { throw 'M16 cleanup ownership failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M16_LABEL,Env:NOAH_M16_TOKEN -ErrorAction SilentlyContinue
    }
}
Invoke-M16Cleanup verify
Write-Output 'Read-only exact ownership passed; no DELETE has run'
```

Expected: the two safe lines. If any count, identity, owner, audit, volume, or Session state differs, **STOP**. Only then run the separate deletion block **once**:

```powershell
if ($CleanupAttempted -or (Get-NoahSnapshot) -ne $AfterCloseJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'Cleanup already attempted or DB/volume changed; STOP'
}
$CleanupAttempted = $true
Invoke-M16Cleanup delete
$AfterCleanupJson = Get-NoahSnapshot
if ($AfterCleanupJson -ne $BaselineJson) {
    throw 'Original DB rows/fingerprints not exactly restored; STOP'
}
Write-Output 'Original 18-table private rows and empty M16 Session table exactly restored'
```

Expected: one exact transaction, then baseline equality across all 19 tables. On transaction/commit acknowledgement uncertainty, **STOP**; never run deletion again blindly. Migration 012 and its nullable audit FK/index remain installed.

## 12. Final environment restoration and operator record

No mapping or local fixture file was created. Compare final DB baseline, named volume, existing mapping state/hash, ordinary Ollama listener, and exact working-tree status. Clear the in-memory test token only after baseline equality. Stop dedicated 11435 **only if this run started it**; leave pre-existing 11435 and ordinary 11434 untouched.

```powershell
if ((Get-NoahSnapshot) -ne $BaselineJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -ne $MappingExistedBefore -or
    ($MappingExistedBefore -and
     (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHashBefore)) {
    throw 'Final DB/volume/mapping comparison failed; STOP'
}
$GenericOllamaAfter = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
if (($GenericOllamaAfter -join '|') -ne ($GenericOllamaBefore -join '|')) {
    throw 'Ordinary Ollama listener changed; inspect without stopping it'
}
$GitAfter = @(git status --short)
if ($LASTEXITCODE -ne 0 -or
    ($GitAfter -join "`n") -ne ($GitBefore -join "`n")) {
    throw 'Working tree changed during manual run; STOP'
}
$TestToken = $null
$Headers = $null
$ScopedHeaders = $null
Write-Output 'DB baseline restored; named volume, mapping, Git, and ordinary Ollama unchanged'
```

Expected: safe final confirmation. If `$StartedDedicatedOllama -eq $true`, stop window C with **Ctrl+C** now. PostgreSQL and its named volume remain running. Do not stop a 11435 listener that pre-existed this run.

### Operator result record

**Status: PASSED (2026-10-09, Asia/Seoul).** The fresh successful run completed Sections 1–12. Keep tokens, DB passwords, private row fingerprints, and raw personal content out of the record. Automated fault/race tests are not claimed as manual E2E.

| Check | Operator result |
| --- | --- |
| M16 working tree, free 8080, PostgreSQL 17, migration 012 FK/index, named volume, current model | PASS |
| All 19 table counts/private fingerprints before mutation; existing 18-table rows; running Task/Execution 0 | PASS |
| New synthetic user/token fixture; Memory/Task/Execution delta 0 | PASS |
| Session create POST once, HTTP 201; one active Session, audit/Task/Execution delta 0 | PASS |
| First scoped route POST once, HTTP 200 `no_action`, `routing.audit_status=recorded`; one audit, no delegate | PASS |
| Second scoped route POST once, HTTP 200 `no_action`, `routing.audit_status=recorded`; distinct router ID, same Session | PASS |
| Exact Session owner and two audit references; no Task/Execution/Evidence | PASS |
| Server stop/restart; same Session and both references in two `limit=1` pages | PASS |
| Session close POST once, HTTP 200; persisted `closed_at`; prior audits unchanged | PASS |
| Closed-Session routed POST once, HTTP 409 `SESSION_CLOSED`; no new audit/model/delegate | PASS |
| Exact synthetic ownership; two audits, one Session, one token, one user removed in one transaction | PASS |
| All 19 table counts/private fingerprints restored; named volume, mapping, Git, Ollama 11434 unchanged; NOAH 8080 and this run's Ollama 11435 stopped | PASS |

The successful run sent **exactly five POSTs**: Session create (201), two scoped routes (200 each), close (200), and the closed-Session rejection probe (409). Neither routed request was retried. The two bounded GET pages after restart were read-only. The 19-table post-cleanup snapshot exactly matched the fresh pre-fixture baseline; migration 012 remained installed.

### Earlier stopped attempts — separate from the passed run

1. An earlier attempt stopped in Section 2 before DB mutation because a string comparison against `pg_get_constraintdef()` expected a schema-qualified FK name that PostgreSQL omitted. The catalog-based FK check replaced that false-negative condition.
2. A separate partial attempt created one synthetic Session (201), then its first scoped route returned HTTP 400 `INVALID_REQUEST` because PowerShell 5.1 passed a JSON `System.Object[]` rather than one `System.Byte[]`. No further POST was sent. Separately authorized partial-run cleanup removed only its synthetic Session, token, and user; the original 19-table baseline was restored.
3. The fresh run reported in the table used the corrected catalog check and `ConvertTo-NoahJsonBytes` return shape. It completed the full E2E with new synthetic data; neither stopped attempt is counted in its five POSTs.

Record unexpected model selection as a stopped run, never as a passed M16 continuity result. Do not claim live token-revocation races, close-versus-reservation races, uncertain commit acknowledgement, or lost HTTP response were injected here; those belong to deterministic automated validation.

## Appendix A — partial-run abort cleanup plan (separate authorization only)

**Do not execute this appendix as part of the normal E2E flow or the current runbook repair.** It applies only when exactly one Session-create POST succeeded, the first routed POST was deterministically rejected before audit reservation, no later HTTP request was sent, and the synthetic Session remains **active** with zero associated audits. Section 11 requires a **closed** Session and two audits and must never be used for this state. Do not retry the failed routed POST or create a replacement Session. Obtain separate approval for cleanup after reviewing the captured response and read-only DB state. A lost response or uncertain database outcome is **not** this scenario.

Retain PowerShell A with `$BaselineJson`, `$AfterCreateJson`, `$RunLabel`, `$UserId`, `$SessionId`, `$TestToken`, and `$VolumeBefore`. Never print the token or either fingerprint snapshot. Stop only the NOAH server started in B with Ctrl+C, confirm 8080 is free, and leave PostgreSQL and unrelated Ollama 11434 alone. A dedicated 11435 started for this run may be stopped by its owner; a pre-existing one must be left alone. Nothing below creates a new Session or performs HTTP.

### A1. Read-only state gate

Run **only after separate authorization to prepare cleanup**. This gate has no DELETE. It requires the full 19-table snapshot to equal the captured post-create snapshot, and all original rows to retain their baseline fingerprints.

```powershell
if (-not $BaselineJson -or -not $AfterCreateJson -or -not $RunLabel -or
    -not $UserId -or -not $SessionId -or -not $TestToken -or
    -not $VolumeBefore -or -not $CreateSent -or -not $FirstRouteSent -or
    $SecondRouteSent -or $CloseSent -or $ClosedRouteSent) {
    throw 'Not the verified partial-run state; STOP'
}
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'NOAH still running or named volume changed; STOP'
}
$AbortBeforeJson = Get-NoahSnapshot
Assert-M16Delta $AbortBeforeJson @{users=1;api_tokens=1;sessions=1}
if ($AbortBeforeJson -ne $AfterCreateJson) {
    throw 'Partial-run DB state differs from captured post-create state; STOP'
}
Write-Output 'Partial-run full snapshot, original fingerprints, and volume verified'
```

Expected: one safe line; any difference is a STOP, not a reason to alter a baseline. The following verifier checks the **exact** synthetic label, actor ID, token hash, active Session ID, zero audit rows, and absence of actor-owned Memory/Task/Execution/M4/membership. Full-snapshot equality above also rejects unexpected rows in every Evidence and project table. It prints no secret or fingerprint.

```powershell
$AbortCleanupCode = @'
import hashlib, os, re, sys
from uuid import UUID
from noah.db import connect
mode = sys.argv[1]
user, session = map(UUID,sys.argv[2:4])
label = os.environ['NOAH_M16_LABEL']
token_hash = hashlib.sha256(os.environ['NOAH_M16_TOKEN'].encode('utf-8')).hexdigest()
if mode not in ('verify','delete') or not re.fullmatch(r'm16-manual-[0-9a-f]{32}',label):
    raise RuntimeError('Abort-cleanup input invalid; STOP')
with connect() as db:
    if mode == 'verify':
        db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
    else:
        db.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
    users = db.execute('SELECT id,label FROM noah.users WHERE id=%s',
        (user,)).fetchall()
    tokens = db.execute('SELECT token_hash FROM noah.api_tokens WHERE user_id=%s',
        (user,)).fetchall()
    sessions = db.execute('SELECT id,closed_at FROM noah.sessions WHERE owner_user_id=%s',
        (user,)).fetchall()
    if (len(users)!=1 or users[0]['label']!=label or len(tokens)!=1
            or tokens[0]['token_hash']!=token_hash or len(sessions)!=1
            or sessions[0]['id']!=session or sessions[0]['closed_at'] is not None):
        raise RuntimeError('Synthetic ownership or active Session differs; STOP')
    audits = db.execute('SELECT count(*) AS n FROM noah.routing_audit '
        'WHERE actor_user_id=%s OR session_id=%s',(user,session)).fetchone()['n']
    if audits != 0:
        raise RuntimeError('Partial run has an audit; STOP')
    checks = {'memories':'owner_user_id','tasks':'actor_user_id',
              'execution_records':'actor_user_id',
              'memory_write_requests':'actor_user_id',
              'project_memberships':'user_id'}
    for table,column in checks.items():
        n = db.execute('SELECT count(*) AS n FROM noah.'+table+
                       ' WHERE '+column+'=%s',(user,)).fetchone()['n']
        if n != 0:
            raise RuntimeError('Unexpected synthetic dependent row; STOP')
    if mode == 'delete':
        def exact(sql,params):
            if len(db.execute(sql+' RETURNING 1',params).fetchall()) != 1:
                raise RuntimeError('Exact DELETE count differs; rollback and STOP')
        exact('DELETE FROM noah.sessions WHERE id=%s AND owner_user_id=%s '
              'AND closed_at IS NULL',(session,user))
        exact('DELETE FROM noah.api_tokens WHERE user_id=%s AND token_hash=%s',
              (user,token_hash))
        exact('DELETE FROM noah.users WHERE id=%s AND label=%s',(user,label))
print('Read-only partial-run ownership verified' if mode=='verify' else
      'Exactly one synthetic Session, token, and user deleted in one transaction')
'@
function Invoke-M16AbortCleanup([string]$Mode) {
    $env:NOAH_M16_LABEL = $RunLabel
    $env:NOAH_M16_TOKEN = $TestToken
    try {
        $AbortCleanupCode | & $Python - $Mode $UserId $SessionId
        if ($LASTEXITCODE -ne 0) { throw 'Abort-cleanup verification failed; STOP' }
    } finally {
        Remove-Item Env:NOAH_M16_LABEL,Env:NOAH_M16_TOKEN -ErrorAction SilentlyContinue
    }
}
Invoke-M16AbortCleanup verify
Write-Output 'Partial-run ownership verified read-only; no DELETE has run'
```

Expected: two safe lines. An error is a STOP. The deletion block below is intentionally gated by a variable **not set anywhere in the normal runbook**. Only after separate authorization and a successful A1 verification may an operator set `$PartialAbortApproval` to the displayed phrase and execute it once. This is not authorization to do so now.

### A2. Separately authorized deletion — **NOT PART OF THE NORMAL RUN**

```powershell
if ($PartialAbortApproval -cne 'APPROVE_M16_PARTIAL_ABORT_ONLY' -or
    $PartialAbortCleanupAttempted -or -not $AbortBeforeJson -or
    (Get-NoahSnapshot) -ne $AfterCreateJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Partial-abort approval or exact state missing; STOP'
}
$PartialAbortCleanupAttempted = $true
Invoke-M16AbortCleanup delete
$AbortAfterJson = Get-NoahSnapshot
if ($AbortAfterJson -ne $BaselineJson) {
    throw 'Original 19-table counts/fingerprints not restored; STOP'
}
Write-Output 'Original 19-table baseline restored; migration 012 remains installed'
```

Expected after a separately approved run: exactly three synthetic rows removed in one transaction, then full baseline equality. An error or uncertain commit acknowledgement is a STOP; do not automatically retry this DELETE transaction. Preserve original private rows, migration 012, mapping, PostgreSQL named volume, and unrelated services. Compare Git and volume identity again before declaring restoration.
