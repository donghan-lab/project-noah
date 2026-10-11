# M17 — Bounded Session Document Follow-Up Manual HTTP Validation

> Status: **isolated HTTP behavior verified on 2026-10-11; second-run cleanup incomplete**. See the separate operator records below. The private-DB path has not run.
> Contract: [52-Seventeenth-Vertical-Slice.md](52-Seventeenth-Vertical-Slice.md).
> Implementation baseline: `main@abd69ef5912109451255d3b4fe9fffeff1ff0fe0` plus the reviewed M17 working tree.

## Scope and stop rule

Use Windows PowerShell 5.1 window **A** for variables, HTTP responses, and verification; window **B** for the working-tree NOAH server; window **C** only if this run starts dedicated Ollama `127.0.0.1:11435`. Keep A open through cleanup. Run each block once, in order, and inspect its expected result before advancing. **STOP** on any unexpected model route, source count, HTTP status, permission, hash, DB delta, ownership, lost response, or uncertain commit. Do not resend a POST to obtain a passing result. A verifier defect permits only a read-only rerun against the captured response and DB, never an HTTP retry or inferred cleanup.

This run uses one newly created synthetic user/token, one project with read-only membership, one direct-child Markdown file, one active Session, one routed M10 answer, and one routed M17 follow-up. It never reads a personal Memory or document. The two answer outcomes may be `supported` or `partial`; exact source-aware quotes, not a claim of complete semantic truth, are the acceptance evidence. No M17 actual-model result is presumed in advance.

The existing PostgreSQL database and named volume are **not** a test database. Perform the isolated-first path in Section 0 before considering the private-DB path in Sections 1–12. The isolated run is a separate execution with fresh variables and synthetic data; it cannot approve a later private-DB change by itself. An operator must separately approve the existing DB backup, Migration 013 application, fixture creation, and private-DB HTTP run. First prove any private backup can restore into an isolated PostgreSQL 17 container with tmpfs. Keep backup files outside Git with access restricted to the current operator; never print or commit a dump, token, password, row fingerprint, private body, or local mapping. Migration 013 remains installed after synthetic cleanup.

## 0. Isolated-first E2E path — no connection to the private database

This path is feasible without changing NOAH code: `noah.db.ROOT` is derived from the imported source location, `connect()` reads only that root's `compose/.env`, `document_tool.operator_root()` reads that root's local mapping, and `serve --port 8080` is independent of database initialization. Copy **only** current M17 Python and SQL files into a new access-restricted directory outside Git, give that copy a synthetic `.env`, and use a new PostgreSQL 17 container with tmpfs and a loopback-only port. This exercises the actual working-tree M17 implementation, actual Ollama 11435, and actual HTTP route without connecting to the private DB or named volume. It does **not** test Migration 013 against existing private rows, so the later private-DB path still needs separate approval and backup/restore proof.

Start a **fresh A window** for this isolated run. Do not run Sections 1, 3, or the Migration-apply block in Section 4. Check the source tree, ports, and configured model without opening a private DB connection; stop if the known 8-path M17 working tree differs:

```powershell
$ErrorActionPreference='Stop'
$SourceRepo='C:\Development\project-noah'
Set-Location -LiteralPath $SourceRepo
$Python=Join-Path $SourceRepo '.venv\Scripts\python.exe'
if ((git -C $SourceRepo branch --show-current) -ne 'main' -or
    (git -C $SourceRepo rev-parse HEAD) -ne 'abd69ef5912109451255d3b4fe9fffeff1ff0fe0' -or
    -not (Test-Path -LiteralPath $Python)) { throw 'Source baseline differs; STOP' }
$ExpectedPaths=@('database/013_document_followup_evidence.sql',
    'docs/01-Project/52-Seventeenth-Vertical-Slice.md',
    'docs/01-Project/53-Seventeenth-Slice-Validation.md',
    'docs/01-Project/54-Seventeenth-Slice-Manual-Validation.md',
    'noah/capability_route.py','noah/db.py','noah/document_followup_query.py',
    'tests/test_document_followup.py') | Sort-Object
$GitBefore=@(git -C $SourceRepo status --short)
$ActualPaths=@(git -C $SourceRepo status --porcelain=v1 |
    ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if (($ActualPaths -join '|') -cne ($ExpectedPaths -join '|')) {
    throw 'Unexpected source-tree change; STOP'
}
$PrivatePort=(& $Python -c 'from noah.db import local_settings; print(local_settings()["POSTGRES_PORT"])').Trim()
$IsolatedPort=62417
if ($LASTEXITCODE -ne 0 -or $PrivatePort -eq [string]$IsolatedPort -or
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -in @(8080,$IsolatedPort) }).Count -ne 0) {
    throw 'Private DB port or HTTP/isolation port conflicts; STOP'
}
function Get-PrivateVolumeIdentity {
    $Info=@(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1) {
        throw 'Original PostgreSQL container identity unavailable; STOP'
    }
    $Volumes=@($Info[0].Mounts | Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" })
    if ($Volumes.Count -ne 1) { throw 'Original named volume differs; STOP' }
    return $Volumes[0]
}
$PrivateVolumeBefore=Get-PrivateVolumeIdentity
$Ollama11434Before=@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
$Ollama11435Before=@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($Ollama11435Before.Count -gt 1 -or
    ($Ollama11435Before.Count -eq 1 -and
     $Ollama11435Before[0].LocalAddress -ne '127.0.0.1')) {
    throw 'Dedicated Ollama listener is not exclusive loopback; STOP'
}
$ModelName=(& $Python -c 'from noah.ollama import MODEL; print(MODEL)').Trim()
if ($LASTEXITCODE -ne 0 -or $ModelName -ne 'gemma4:12b-it-qat') {
    throw 'Configured model differs; STOP'
}
$StartedOllama11435=$false
$CreateSent=$M10Sent=$M17Sent=$CleanupAttempted=$false
Write-Output 'Source, free ports, private DB port separation and model checked'
```

Expected: one safe line. The original `.env` is read **only for its port**, and no connection to its DB is opened. STOP on a different source tree, running 8080, or port conflict. Prepare a current-user-only temporary copy with synthetic credentials; never copy the private `.env`, mapping, docs, tests, or personal data:

```powershell
$IsolationId=[guid]::NewGuid().ToString('N')
$IsolatedRepo=Join-Path $env:TEMP ('noah-m17-isolated-'+$IsolationId)
if (Test-Path -LiteralPath $IsolatedRepo) { throw 'Isolated root exists; STOP' }
New-Item -ItemType Directory -Path $IsolatedRepo | Out-Null
$Acl=Get-Acl -LiteralPath $IsolatedRepo
$Acl.SetAccessRuleProtection($true,$false)
$Principal="${env:USERDOMAIN}\${env:USERNAME}"
$Acl.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule(
    $Principal,'FullControl','ContainerInherit,ObjectInherit','None','Allow')))
Set-Acl -LiteralPath $IsolatedRepo -AclObject $Acl
foreach ($Part in @('noah','database','compose','config')) {
    New-Item -ItemType Directory -Path (Join-Path $IsolatedRepo $Part) | Out-Null
}
$PythonFiles=@(Get-ChildItem -LiteralPath (Join-Path $SourceRepo 'noah') -File -Filter '*.py')
$SqlFiles=@(Get-ChildItem -LiteralPath (Join-Path $SourceRepo 'database') -File -Filter '*.sql')
if ($PythonFiles.Count -eq 0 -or $SqlFiles.Count -ne 13) {
    throw 'Isolated source inventory differs; STOP'
}
$PythonFiles | Copy-Item -Destination (Join-Path $IsolatedRepo 'noah')
$SqlFiles | Copy-Item -Destination (Join-Path $IsolatedRepo 'database')
$Random=[Security.Cryptography.RandomNumberGenerator]::Create()
try { $SecretBytes=New-Object byte[] 32; $Random.GetBytes($SecretBytes)
      $IsolatedPassword=[Convert]::ToBase64String($SecretBytes).TrimEnd('=').Replace('+','-').Replace('/','_') }
finally { if ($SecretBytes) { [Array]::Clear($SecretBytes,0,$SecretBytes.Length) }; $Random.Dispose() }
$Utf8=New-Object System.Text.UTF8Encoding($false,$true)
$IsolatedEnv="POSTGRES_DB=noah_m17`nPOSTGRES_USER=noah_m17`nPOSTGRES_PASSWORD=$IsolatedPassword`nPOSTGRES_PORT=$IsolatedPort`n"
[IO.File]::WriteAllText((Join-Path $IsolatedRepo 'compose\.env'),$IsolatedEnv,$Utf8)
[IO.File]::WriteAllText((Join-Path $IsolatedRepo '.m17-isolated'),$IsolationId,$Utf8)
$Repo=$IsolatedRepo
$Mapping=Join-Path $Repo 'config\project_documents.local.json'
if (Test-Path -LiteralPath $Mapping) { throw 'Unexpected isolated mapping; STOP' }
$env:PYTHONDONTWRITEBYTECODE='1'
Set-Location -LiteralPath $Repo
$env:NOAH_M17_EXPECTED_ROOT=$IsolatedRepo
try {
    & $Python -c 'import os; from pathlib import Path; from noah.db import ROOT,local_settings; s=local_settings(); assert ROOT.resolve()==Path(os.environ["NOAH_M17_EXPECTED_ROOT"]).resolve() and s["POSTGRES_PORT"]=="62417" and s["POSTGRES_DB"]=="noah_m17"'
    if ($LASTEXITCODE -ne 0) { throw 'Imported root/settings differ; STOP' }
} finally { Remove-Item Env:NOAH_M17_EXPECTED_ROOT -ErrorAction SilentlyContinue }
Write-Output "Isolated source root: $IsolatedRepo"
Write-Output "Isolated marker (nonsecret): $IsolationId"
```

Expected: the temporary root and marker only. Store neither the synthetic password nor private data in Git. **Before any `init` or fixture**, start and inspect only a uniquely named tmpfs container with a loopback binding; STOP if it gains a named volume or points to the private DB port:

```powershell
$IsolatedPgName='noah-m17-isolated-'+$IsolationId.Substring(0,12)
docker run --rm -d --name $IsolatedPgName `
    --tmpfs /var/lib/postgresql/data:rw,size=256m `
    -p "127.0.0.1:$($IsolatedPort):5432" `
    -e POSTGRES_DB=noah_m17 -e POSTGRES_USER=noah_m17 `
    -e "POSTGRES_PASSWORD=$IsolatedPassword" postgres:17 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Isolated PostgreSQL startup failed; STOP' }
function Get-NoahVolumeIdentity {
    $Info=@(docker inspect $IsolatedPgName | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1 -or
        $Info[0].State.Status -ne 'running' -or
        $Info[0].Config.Image -ne 'postgres:17' -or
        @($Info[0].Mounts | Where-Object { $_.Type -eq 'volume' }).Count -ne 0) {
        throw 'Isolated container/volume identity differs; STOP'
    }
    $Tmpfs=$Info[0].HostConfig.Tmpfs.PSObject.Properties['/var/lib/postgresql/data'].Value
    if (-not $Tmpfs) { throw 'Isolated PostgreSQL data is not tmpfs; STOP' }
    return "$($Info[0].Id)|$Tmpfs"
}
$VolumeBefore=Get-NoahVolumeIdentity
$Ready=$false
for ($Attempt=0; $Attempt -lt 30; $Attempt++) {
    docker exec $IsolatedPgName pg_isready -q -U noah_m17 -d noah_m17
    if ($LASTEXITCODE -eq 0) { $Ready=$true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $Ready) { throw 'Isolated PostgreSQL not ready; STOP' }
& $Python -m noah init
if ($LASTEXITCODE -ne 0) { throw 'Isolated 001–013 initialization failed; STOP' }
Write-Output 'Only the tmpfs PostgreSQL received migrations 001–013'
```

Expected: isolated schema initialization only. In A, run the **first definition block** in Section 2 (`$SnapshotCode` and `Get-NoahSnapshot`) and the **catalog-proof block** in Section 4 (`$SchemaCode` and its invocation), with the working directory still `$IsolatedRepo`. Do not run Section 2's `pre` block or Section 4's private Migration application or old-row comparison. Then establish the isolated **20-table empty** baseline and file manifest:

```powershell
$BaselineJson=Get-NoahSnapshot post
$Baseline=$BaselineJson | ConvertFrom-Json
if (@($Baseline.tables.PSObject.Properties).Count -ne 20 -or
    @($Baseline.tables.PSObject.Properties | Where-Object { $_.Value.count -ne 0 }).Count -ne 0 -or
    $Baseline.running_tasks -ne 0 -or $Baseline.running_execution_records -ne 0) {
    throw 'Isolated baseline not empty; STOP'
}
$IsolatedManifest=@(Get-ChildItem -LiteralPath $IsolatedRepo -Recurse -File |
    ForEach-Object { [pscustomobject]@{Path=$_.FullName;
        Hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash} })
if ($IsolatedManifest.Count -ne ($PythonFiles.Count+$SqlFiles.Count+2)) {
    throw 'Isolated source/config inventory differs; STOP'
}
Write-Output 'M17 catalog and empty 20-table baseline checked in tmpfs PostgreSQL'
```

Next, use Section 1's dedicated 11435 **start block only if 11435 was absent**, and always use its listener/model tag-check block. Then run Sections 5–11 with the isolated A variables. In B use the isolated-server alternative in Section 6, and use it again after the Section 8 restart. Each POST remains one-shot; stop on an unexpected model result. Section 11 must restore the isolated `$BaselineJson` exactly before stopping this run's server/container. After the Section 11 mapping/document cleanup, compare every copied file against `$IsolatedManifest`, reject any extra files, and remove the exact copy **file by file** and each empty directory without recursive deletion. Then stop **only** `$IsolatedPgName` (its `--rm` tmpfs container); do not stop `noah-postgres` or alter its named volume. Stop 11435 only if this run started it. A private-DB run, if later approved, starts in a **new A window** at Section 1 with new IDs and fresh baseline; no isolated variable, token, response, or completion flag is reused.

```powershell
if ((Get-NoahSnapshot post) -cne $BaselineJson -or
    (Get-NoahVolumeIdentity) -cne $VolumeBefore -or
    (Get-PrivateVolumeIdentity) -cne $PrivateVolumeBefore -or
    @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
      Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) {
    throw 'Isolated post-cleanup state or server differs; STOP'
}
$CurrentFiles=@(Get-ChildItem -LiteralPath $IsolatedRepo -Recurse -File)
if ($CurrentFiles.Count -ne $IsolatedManifest.Count) {
    throw 'Unexpected isolated file; STOP'
}
foreach ($Entry in $IsolatedManifest) {
    if (-not (Test-Path -LiteralPath $Entry.Path) -or
        (Get-FileHash -LiteralPath $Entry.Path -Algorithm SHA256).Hash -cne $Entry.Hash) {
        throw 'Isolated source/config changed; STOP'
    }
}
Set-Location -LiteralPath $SourceRepo
foreach ($Entry in $IsolatedManifest) { Remove-Item -LiteralPath $Entry.Path }
foreach ($Part in @('noah','database','compose','config')) {
    $Dir=Join-Path $IsolatedRepo $Part
    if (@(Get-ChildItem -LiteralPath $Dir -Force).Count -ne 0) {
        throw 'Isolated directory not empty; STOP'
    }
    Remove-Item -LiteralPath $Dir
}
if (@(Get-ChildItem -LiteralPath $IsolatedRepo -Force).Count -ne 0) {
    throw 'Isolated root not empty; STOP'
}
Remove-Item -LiteralPath $IsolatedRepo
docker stop $IsolatedPgName | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Isolated container stop unconfirmed; STOP' }
if ((@(git -C $SourceRepo status --short) -join "`n") -cne ($GitBefore -join "`n")) {
    throw 'Source Git status changed; STOP'
}
Write-Output 'Isolated synthetic rows, source copy and tmpfs container removed; private DB untouched'
```

Expected: one safe line after a successful isolated E2E and exact cleanup. If any state or commit acknowledgement is uncertain, **do not** run this final cleanup by guess. The private path below is independent and remains unapproved until the operator explicitly authorizes it.

## 1. A — repository, service, and model preflight (read only)

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
$SourceRepo = $Repo
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python) -or
    (git branch --show-current) -ne 'main' -or
    (git rev-parse HEAD) -ne 'abd69ef5912109451255d3b4fe9fffeff1ff0fe0') {
    throw 'Repository or Python baseline differs; STOP'
}
$ExpectedPaths = @(
    'database/013_document_followup_evidence.sql',
    'docs/01-Project/52-Seventeenth-Vertical-Slice.md',
    'docs/01-Project/53-Seventeenth-Slice-Validation.md',
    'docs/01-Project/54-Seventeenth-Slice-Manual-Validation.md',
    'noah/capability_route.py','noah/db.py','noah/document_followup_query.py',
    'tests/test_document_followup.py'
) | Sort-Object
$GitBefore = @(git status --short)
$ActualPaths = @(git status --porcelain=v1 |
    ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if ($LASTEXITCODE -ne 0 -or ($ActualPaths -join '|') -ne ($ExpectedPaths -join '|')) {
    throw 'Unexpected working-tree change; STOP'
}
$Port8080 = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 })
if ($Port8080.Count -ne 0) { throw 'Port 8080 belongs to another process; STOP' }
$Pg = @(docker inspect noah-postgres | ConvertFrom-Json)
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1 -or
    $Pg[0].State.Status -ne 'running' -or $Pg[0].Config.Image -ne 'postgres:17') {
    throw 'Expected PostgreSQL 17 container absent; STOP'
}
docker exec noah-postgres pg_isready -q
if ($LASTEXITCODE -ne 0) { throw 'PostgreSQL is not ready; STOP' }
function Get-NoahVolumeIdentity {
    $Info = @(docker inspect noah-postgres | ConvertFrom-Json)
    if ($LASTEXITCODE -ne 0 -or $Info.Count -ne 1) { throw 'Docker inspect failed; STOP' }
    $Volumes = @($Info[0].Mounts | Where-Object { $_.Type -eq 'volume' } |
        ForEach-Object { "$($_.Name)|$($_.Destination)" } | Sort-Object)
    if ($Volumes.Count -ne 1) { throw 'Unexpected PostgreSQL mounts; STOP' }
    return $Volumes[0]
}
$VolumeBefore = Get-NoahVolumeIdentity
if ($VolumeBefore -ne 'noah_noah-postgres-data|/var/lib/postgresql/data') {
    throw 'Named volume identity differs from compose/docker-compose.yml; STOP'
}
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
$MappingExistedBefore = Test-Path -LiteralPath $Mapping
if ($MappingExistedBefore) { throw 'Existing local mapping must not be overwritten; STOP' }
$Ollama11434Before = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
$ModelName = (& $Python -c 'from noah.ollama import MODEL; print(MODEL)').Trim()
if ($LASTEXITCODE -ne 0 -or $ModelName -ne 'gemma4:12b-it-qat') {
    throw 'Configured local model differs; STOP'
}
$Ollama11435Before = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($Ollama11435Before.Count -gt 1 -or
    ($Ollama11435Before.Count -eq 1 -and
     $Ollama11435Before[0].LocalAddress -ne '127.0.0.1')) {
    throw 'Dedicated Ollama is not exclusively loopback; STOP'
}
$StartedOllama11435 = $false
$CreateSent = $M10Sent = $M17Sent = $CleanupAttempted = $false
Write-Output 'M17 working tree, free 8080, PostgreSQL 17, volume, and model checked'
```

Expected: one safe confirmation line. **STOP** if any path, process, volume, or mapping differs. A pre-existing loopback 11435 belongs to its original operator and must not be stopped by this run. If absent, start only the dedicated listener in C:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

Back in A, verify that the current model is installed without pulling or replacing it:

```powershell
if ($Ollama11435Before.Count -eq 0) { $StartedOllama11435 = $true }
$Now11435 = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11435 })
if ($Now11435.Count -ne 1 -or $Now11435[0].LocalAddress -ne '127.0.0.1' -or
    ($Ollama11435Before.Count -eq 1 -and
     $Now11435[0].OwningProcess -ne $Ollama11435Before[0].OwningProcess)) {
    throw 'Dedicated listener ownership changed; STOP'
}
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq $ModelName }).Count -ne 1) {
    throw 'Configured model missing on dedicated listener; STOP'
}
Write-Output 'Dedicated loopback model available; ordinary Ollama untouched'
```

Expected: one safe line. `/api/tags` does not send a user question or start M17 E2E. **STOP** if the configured model is absent.

## 2. A — pre-013 schema and private-data baseline (read only)

The initial database should contain the M16 set of **19 tables** and no M17 table. Capture *every* table row count and full-row private fingerprint in variables; print no row or digest. This step precedes any fixture or Migration 013 write. A changed baseline requires investigation, never changing these checks to match it.

```powershell
$SnapshotCode = @'
import hashlib, json, sys
from noah.db import connect
old = ['users','api_tokens','memories','tasks','execution_records',
 'memory_write_requests','projects','project_memberships',
 'document_tool_evidence','document_read_evidence','document_answer_evidence',
 'selected_document_answer_evidence','selected_document_source_evidence',
 'selected_document_quote_evidence','auto_document_answer_evidence',
 'auto_document_source_evidence','auto_document_quote_evidence',
 'routing_audit','sessions']
phase = sys.argv[1]
if phase not in ('pre','post'): raise RuntimeError('Invalid snapshot phase; STOP')
tables = old + (['document_followup_evidence'] if phase == 'post' else [])
out = {'tables':{}}
with connect() as db:
 db.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
 if not db.execute('SHOW server_version').fetchone()['server_version'].startswith('17.'):
  raise RuntimeError('PostgreSQL 17 required; STOP')
 actual = [r['tablename'] for r in db.execute(
  "SELECT tablename FROM pg_tables WHERE schemaname='noah' ORDER BY tablename")]
 if sorted(actual) != sorted(tables): raise RuntimeError('NOAH schema/table set differs; STOP')
 if phase == 'pre':
  checks = db.execute("""SELECT conname,pg_get_expr(conbin,conrelid) AS expr
   FROM pg_constraint WHERE conrelid='noah.routing_audit'::regclass
   AND contype='c' AND conname IN ('routing_audit_validated_route_check',
    'routing_audit_delegate_capability_check','routing_audit_check1')""").fetchall()
  if (len(checks)!=3 or {r['conname'] for r in checks} != {
      'routing_audit_validated_route_check',
      'routing_audit_delegate_capability_check','routing_audit_check1'} or
      any('project.documents.answer.followup' in r['expr'] for r in checks)):
   raise RuntimeError('Pre-013 routing CHECK state differs; STOP')
 for name in tables:
  rows = db.execute('SELECT * FROM noah.'+name).fetchall()
  out['tables'][name] = {'count':len(rows),'rows':sorted(
   hashlib.sha256(json.dumps(r,sort_keys=True,default=str,
    ensure_ascii=True).encode('utf-8')).hexdigest() for r in rows)}
 for name in ('tasks','execution_records'):
  out['running_'+name] = db.execute(
   "SELECT count(*) AS n FROM noah."+name+" WHERE status='running'").fetchone()['n']
print(json.dumps(out,sort_keys=True,separators=(',',':')))
'@
function Get-NoahSnapshot([string]$Phase) {
    $Value = $SnapshotCode | & $Python - $Phase
    if ($LASTEXITCODE -ne 0 -or -not $Value) { throw 'Snapshot failed; STOP' }
    return [string]$Value
}
```

For the private-DB path, immediately run the next block. For the isolated-first path, use only the function-definition block above and take a `post` snapshot in Section 0; do **not** run the following `pre` snapshot against the private DB.

```powershell
$Before013Json = Get-NoahSnapshot pre
$Before013 = $Before013Json | ConvertFrom-Json
if ($Before013.running_tasks -ne 0 -or
    $Before013.running_execution_records -ne 0 -or
    $Before013.tables.sessions.count -ne 0 -or
    $Before013.tables.routing_audit.count -ne 0) {
    throw 'Unexpected running/synthetic baseline; STOP'
}
Write-Output 'Original 19-table counts and private fingerprints held in window A'
```

Expected: one safe line. The original rows remain private in A. **STOP** if any table differs, a running Task/Execution exists, or Session/Audit state is unexpected. Existing personal row counts are not guessed in this procedure.

## 3. Separate approval gate — restricted backup and isolated restore

**Do not execute this section without separate approval to back up the existing database.** PostgreSQL's container environment already supplies `POSTGRES_USER` and `POSTGRES_DB` from `compose/docker-compose.yml`; no database password is printed. The archive goes to a current-user-only directory outside the repository. Never redirect binary `pg_dump` output through PowerShell 5.1 text streams. Inspect local backup policy and storage encryption before choosing the destination.

```powershell
$BackupDir = Join-Path $env:LOCALAPPDATA ('NOAH\m17-backup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $BackupDir | Out-Null
$Acl = Get-Acl -LiteralPath $BackupDir
$Acl.SetAccessRuleProtection($true,$false)
$Principal = "${env:USERDOMAIN}\${env:USERNAME}"
$Rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
    $Principal,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
$Acl.AddAccessRule($Rule)
Set-Acl -LiteralPath $BackupDir -AclObject $Acl
$BackupFile = Join-Path $BackupDir 'pre-013.dump'
$ContainerBackup = '/tmp/noah-m17-pre013.dump'
docker exec noah-postgres sh -c 'test ! -e /tmp/noah-m17-pre013.dump'
if ($LASTEXITCODE -ne 0) { throw 'Container backup path already exists; STOP' }
docker exec noah-postgres sh -c 'pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f /tmp/noah-m17-pre013.dump'
if ($LASTEXITCODE -ne 0) { throw 'Backup failed; STOP before migration' }
docker cp "noah-postgres:$ContainerBackup" $BackupFile
if ($LASTEXITCODE -ne 0 -or (Get-Item -LiteralPath $BackupFile).Length -le 0) {
    throw 'Backup archive missing; STOP before migration'
}
$BackupHash = (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash
Write-Output 'Restricted pre-013 archive captured; hash retained privately'
```

Expected: one safe line, without dump contents, digest, or credentials. Verify the resulting ACL locally. Restore into a **new disposable PostgreSQL 17 container with tmpfs and no published port**; do not restore into `noah-postgres` or its named volume. The restore container must have a unique name, then be stopped only after archive/table inspection succeeds:

```powershell
$RestoreName = 'noah-m17-restore-' + [guid]::NewGuid().ToString('N').Substring(0,12)
docker run --rm -d --name $RestoreName --network none `
    --tmpfs /var/lib/postgresql/data:rw,size=256m `
    -e POSTGRES_DB=noah_restore -e POSTGRES_USER=noah_restore `
    -e POSTGRES_PASSWORD=m17-isolated-restore-only postgres:17 | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Isolated restore container failed; STOP' }
docker cp $BackupFile "${RestoreName}:/tmp/pre-013.dump"
if ($LASTEXITCODE -ne 0) { throw 'Cannot copy archive to isolated DB; STOP' }
$Ready=$false
for ($Attempt=0; $Attempt -lt 30; $Attempt++) {
    docker exec $RestoreName pg_isready -q
    if ($LASTEXITCODE -eq 0) { $Ready=$true; break }
    Start-Sleep -Milliseconds 500
}
if (-not $Ready) { throw 'Isolated DB not ready; STOP' }
docker exec $RestoreName pg_restore --exit-on-error --clean --if-exists --no-owner --no-acl `
    -U noah_restore -d noah_restore /tmp/pre-013.dump
if ($LASTEXITCODE -ne 0) { throw 'Isolated restore failed; STOP' }
$RestoredTables = @(docker exec $RestoreName psql -U noah_restore -d noah_restore `
    -qAt -c "SELECT tablename FROM pg_tables WHERE schemaname='noah' ORDER BY tablename")
if ($LASTEXITCODE -ne 0 -or $RestoredTables.Count -ne 19 -or
    @($RestoredTables | Where-Object { $_ -eq 'sessions' }).Count -ne 1) {
    throw 'Restored schema differs; STOP'
}
foreach ($Entry in $Before013.tables.PSObject.Properties) {
    $Count = @(docker exec $RestoreName psql -U noah_restore -d noah_restore `
        -qAt -c "SELECT count(*) FROM noah.$($Entry.Name)")
    if ($LASTEXITCODE -ne 0 -or $Count.Count -ne 1 -or
        [int]$Count[0] -ne $Entry.Value.count) {
        throw "Restored $($Entry.Name) count differs; STOP"
    }
}
$OriginalDbUser=@(docker exec noah-postgres printenv POSTGRES_USER)
$OriginalDbName=@(docker exec noah-postgres printenv POSTGRES_DB)
if ($LASTEXITCODE -ne 0 -or $OriginalDbUser.Count -ne 1 -or
    $OriginalDbName.Count -ne 1 -or -not $OriginalDbUser[0] -or
    -not $OriginalDbName[0]) { throw 'Original DB identity unavailable; STOP' }
foreach ($Entry in $Before013.tables.PSObject.Properties) {
    $Name=$Entry.Name
    if ($Name -cnotmatch '^[a-z_]+$') { throw 'Unexpected table identifier; STOP' }
    $RowDigestSql="SELECT encode(sha256(convert_to(to_jsonb(t)::text,'UTF8')),'hex') FROM noah.$Name AS t ORDER BY 1"
    $OriginalRows=@(docker exec noah-postgres psql -X -qAt -v ON_ERROR_STOP=1 `
        -U $OriginalDbUser[0] -d $OriginalDbName[0] `
        -c "SET TIME ZONE 'UTC'" -c $RowDigestSql)
    if ($LASTEXITCODE -ne 0) { throw "Original $Name digest query failed; STOP" }
    $RestoredRows=@(docker exec $RestoreName psql -X -qAt -v ON_ERROR_STOP=1 `
        -U noah_restore -d noah_restore `
        -c "SET TIME ZONE 'UTC'" -c $RowDigestSql)
    if ($LASTEXITCODE -ne 0 -or $OriginalRows.Count -ne $Entry.Value.count -or
        $RestoredRows.Count -ne $Entry.Value.count -or
        @($OriginalRows | Where-Object { $_ -cnotmatch '^[0-9a-f]{64}$' }).Count -ne 0 -or
        @($RestoredRows | Where-Object { $_ -cnotmatch '^[0-9a-f]{64}$' }).Count -ne 0 -or
        ($OriginalRows -join '|') -cne ($RestoredRows -join '|')) {
        throw "Original/restored full-row digests differ in $Name; STOP"
    }
}
if ((Get-NoahSnapshot pre) -cne $Before013Json) {
    throw 'Original private row baseline moved during backup/restore; STOP'
}
docker stop $RestoreName | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Restore container cleanup unconfirmed; STOP' }
docker exec noah-postgres rm -f $ContainerBackup
if ($LASTEXITCODE -ne 0) { throw 'Original-container temporary archive cleanup unconfirmed; STOP' }
if ((Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash -ne $BackupHash) {
    throw 'Backup archive changed; STOP'
}
Write-Output 'Pre-013 archive restored in isolated PostgreSQL; original volume untouched'
```

Expected: one safe line. An interrupted restore is a **STOP** requiring inspection of only the uniquely named disposable container. For every one of the original 19 tables, the query computes a SHA-256 digest of **each complete row** in a UTC session on the original and restored DB, sorts those digests, and compares the entire multisets privately in A. The original Python snapshot must also remain byte-for-byte unchanged. No row content or digest is printed or written to a file. A successful `pg_restore`, identical table inventory/counts/full-row digests, and unchanged archive hash establish the backup/restore prerequisite. Keep the restricted archive until the E2E and baseline verification finish. This procedure does not silently restore or reset the original DB.

## 4. Separate approval gate — apply only Migration 013, then inspect catalog

**Do not execute without separate approval to change the existing DB schema.** `python -m noah serve` does not apply migrations; `python -m noah init` replays all migrations, so this procedure executes **only** reviewed `013_document_followup_evidence.sql` in one transaction. Its three `routing_audit` CHECK replacements require an `ACCESS EXCLUSIVE` table lock and validation of existing rows; a busy table can make this step wait or fail. Use a maintenance window, no concurrent NOAH server, finite lock/statement timeouts, and STOP on any unexpected state. Never retry an uncertain commit automatically.

```powershell
if ((Get-NoahSnapshot pre) -ne $Before013Json -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Get-FileHash -LiteralPath $BackupFile -Algorithm SHA256).Hash -ne $BackupHash) {
    throw 'Pre-migration DB/volume/backup changed; STOP'
}
$MigrationCode = @'
from pathlib import Path
from noah.db import ROOT, connect
sql = (ROOT/'database'/'013_document_followup_evidence.sql').read_text(encoding='utf-8')
with connect() as db:
 db.execute("SET LOCAL lock_timeout = '5s'")
 db.execute("SET LOCAL statement_timeout = '30s'")
 db.execute(sql)
print('Migration 013 transaction acknowledged')
'@
$MigrationCode | & $Python -
if ($LASTEXITCODE -ne 0) { throw 'Migration failed or acknowledgement unknown; STOP' }
```

Expected: one acknowledgement line. If the connection or acknowledgement is lost, **STOP** and inspect catalog read-only; do not rerun migration by guess. The following catalog proof checks the precise three CHECK names and five non-cascading FKs using PostgreSQL object identifiers, rather than schema spelling in `pg_get_constraintdef()`:

```powershell
$SchemaCode = @'
from noah.db import connect
expected = {
 ('execution_id','execution_records','id'),
 ('current_router_id','routing_audit','router_id'),
 ('prior_router_id','routing_audit','router_id'),
 ('prior_execution_id','execution_records','id'),
 ('project_id','projects','id')}
with connect() as db:
 db.execute('SET TRANSACTION READ ONLY')
 names = {r['tablename'] for r in db.execute(
  "SELECT tablename FROM pg_tables WHERE schemaname='noah'")}
 if len(names) != 20 or 'document_followup_evidence' not in names:
  raise RuntimeError('M17 table inventory differs; STOP')
 checks = db.execute("""SELECT conname, pg_get_expr(conbin,conrelid) AS expr
  FROM pg_constraint WHERE conrelid='noah.routing_audit'::regclass AND contype='c'
  AND conname IN ('routing_audit_validated_route_check',
                  'routing_audit_delegate_capability_check','routing_audit_check1')""").fetchall()
 required = {
  'routing_audit_validated_route_check':(
   'memory.query','project.documents.answer.auto','memory.save',
   'memory.suppress','project.documents.answer.followup','no_action'),
  'routing_audit_delegate_capability_check':(
   'memory.query','project.documents.answer.auto','memory.save',
   'memory.suppress','project.documents.answer.followup'),
  'routing_audit_check1':(
   'memory.query','project.documents.answer.auto','memory.save',
   'memory.suppress','project.documents.answer.followup')}
 if (len(checks) != 3 or {r['conname'] for r in checks} != set(required) or
     any(any(route not in r['expr'] for route in required[r['conname']])
         for r in checks)):
  raise RuntimeError('M17 routing CHECK constraints differ; STOP')
 fks = db.execute("""SELECT sa.attname AS source_column,tn.nspname AS target_schema,
  tc.relname AS target_table,ta.attname AS target_column,c.confdeltype,
  array_length(c.conkey,1) AS source_keys,array_length(c.confkey,1) AS target_keys
  FROM pg_constraint c JOIN pg_class sc ON sc.oid=c.conrelid
  JOIN pg_namespace sn ON sn.oid=sc.relnamespace
  JOIN pg_class tc ON tc.oid=c.confrelid
  JOIN pg_namespace tn ON tn.oid=tc.relnamespace
  JOIN pg_attribute sa ON sa.attrelid=c.conrelid AND sa.attnum=c.conkey[1]
  JOIN pg_attribute ta ON ta.attrelid=c.confrelid AND ta.attnum=c.confkey[1]
  WHERE sn.nspname='noah' AND sc.relname='document_followup_evidence'
    AND c.contype='f'""").fetchall()
 actual = {(r['source_column'],r['target_table'],r['target_column']) for r in fks}
 if len(fks) != 5 or actual != expected or any(
   r['target_schema']!='noah' or r['confdeltype']!='a' or
   r['source_keys']!=1 or r['target_keys']!=1 for r in fks):
  raise RuntimeError('M17 lineage FK/delete policy differs; STOP')
print('Migration 013 table, route CHECKs and five NO ACTION FKs confirmed')
'@
$SchemaCode | & $Python -
if ($LASTEXITCODE -ne 0) { throw 'Post-migration catalog proof failed; STOP' }
```

The catalog-proof block above is also used for the **isolated-first** database after its private-copy `init`. For the separately approved private-DB path, continue with the following baseline comparison; it must show that Migration 013 did not change any of the original 19 tables' rows:

```powershell
$BaselineJson = Get-NoahSnapshot post
$Baseline = $BaselineJson | ConvertFrom-Json
if ($Baseline.tables.document_followup_evidence.count -ne 0 -or
    $Baseline.running_tasks -ne 0 -or
    $Baseline.running_execution_records -ne 0) { throw 'Post-migration baseline differs; STOP' }
foreach ($Name in $Before013.tables.PSObject.Properties.Name) {
    if (($Baseline.tables.PSObject.Properties[$Name].Value | ConvertTo-Json -Compress) -cne
        ($Before013.tables.PSObject.Properties[$Name].Value | ConvertTo-Json -Compress)) {
        throw "Existing $Name rows changed by migration; STOP"
    }
}
Write-Output 'Permanent M17 schema installed; prior 19-table row baseline preserved'
```

Expected: catalog and row-state confirmation only. Keep `$Before013Json` and `$BaselineJson` privately in A. The final synthetic cleanup compares **all 20 post-migration tables** with `$BaselineJson`; Migration 013 is not rolled back by cleanup.

If Migration 013 fails with a confirmed transaction rollback, retain the pre-013 snapshot and inspect the schema read-only before any further action. If its commit acknowledgement or post-migration proof is uncertain, keep NOAH stopped and preserve the backup and named volume for a separate recovery decision. Do not rerun 013 or restore the original DB automatically. A restore into the original DB would itself require a separate approved recovery plan and an exact target-state check.

## 5. A — prepare only owned synthetic fixtures

Create one user, token hash, project, and read-only membership in one transaction. A cryptographically generated token is held only in A. Make the document and BOM-free local mapping only if the mapping was absent at preflight. The root is new, outside Git, and contains one direct-child `.md` under the 2,048 UTF-8-byte M8 Context limit. Do not use or copy a personal document.

```powershell
$RunId = [guid]::NewGuid().ToString('N')
$RunLabel = "m17-manual-$RunId"
$RootId = "m17-$($RunId.Substring(0,16))"
$DocName = 'm17-animal-color.md'
$DocRoot = Join-Path $env:TEMP $RunLabel
if ((Test-Path -LiteralPath $DocRoot) -or (Test-Path -LiteralPath $Mapping)) {
    throw 'Synthetic root/mapping already exists; STOP'
}
$Random = [System.Security.Cryptography.RandomNumberGenerator]::Create()
try {
    $TokenBytes = New-Object byte[] 32
    $Random.GetBytes($TokenBytes)
    $TestToken = [Convert]::ToBase64String($TokenBytes).TrimEnd('=').Replace('+','-').Replace('/','_')
} finally {
    if ($TokenBytes) { [Array]::Clear($TokenBytes,0,$TokenBytes.Length) }
    $Random.Dispose()
}
$FixtureCode = @'
import hashlib, os, re
from uuid import uuid4
from noah.db import connect
label,token = os.environ['NOAH_M17_LABEL'],os.environ['NOAH_M17_TOKEN']
if not re.fullmatch(r'm17-manual-[0-9a-f]{32}',label) or len(token)<32:
 raise RuntimeError('Fixture identifiers invalid; STOP')
user,project=uuid4(),uuid4()
with connect() as db:
 db.execute('INSERT INTO noah.users(id,label) VALUES (%s,%s)',(user,label))
 db.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES (%s,%s)',
  (hashlib.sha256(token.encode('utf-8')).hexdigest(),user))
 db.execute('INSERT INTO noah.projects(id,label) VALUES (%s,%s)',(project,label))
 db.execute('INSERT INTO noah.project_memberships(project_id,user_id,can_write) '
            'VALUES (%s,%s,false)',(project,user))
 print(str(user)+'|'+str(project))
'@
if ((Get-NoahSnapshot post) -ne $BaselineJson) { throw 'Baseline moved; STOP' }
$env:NOAH_M17_LABEL = $RunLabel
$env:NOAH_M17_TOKEN = $TestToken
try {
    $Ids = $FixtureCode | & $Python -
    if ($LASTEXITCODE -ne 0 -or @($Ids).Count -ne 1) { throw 'Fixture commit uncertain; STOP' }
} finally {
    Remove-Item Env:NOAH_M17_LABEL,Env:NOAH_M17_TOKEN -ErrorAction SilentlyContinue
}
$UserId,$ProjectId = ([string]$Ids).Split('|')
if (([guid]$UserId).ToString() -cne $UserId -or
    ([guid]$ProjectId).ToString() -cne $ProjectId) { throw 'Fixture IDs invalid; STOP' }
New-Item -ItemType Directory -Path $DocRoot | Out-Null
$DocPath = Join-Path $DocRoot $DocName
$DocText = "NOAH의 M17 테스트 동물은 수달이다.`nNOAH의 M17 테스트 색상은 파란색이다.`n"
$Utf8 = [System.Text.UTF8Encoding]::new($false,$true)
[System.IO.File]::WriteAllBytes($DocPath,$Utf8.GetBytes($DocText))
if ((Get-Item -LiteralPath $DocPath).Length -ge 2048) { throw 'Synthetic document too large; STOP' }
$DocHash = (Get-FileHash -LiteralPath $DocPath -Algorithm SHA256).Hash.ToLowerInvariant()
$MappingObject = @{projects=@{ $ProjectId=@{root_id=$RootId;document_root=$DocRoot} }}
$MappingJson = $MappingObject | ConvertTo-Json -Depth 5 -Compress
[System.IO.File]::WriteAllText($Mapping,$MappingJson,$Utf8)
$MappingHash = (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash
$AfterFixtureJson = Get-NoahSnapshot post
foreach ($Entry in $Baseline.tables.PSObject.Properties) {
    $Extra=if (@('users','api_tokens','projects','project_memberships') -contains
        $Entry.Name) { 1 } else { 0 }
    $Now=($AfterFixtureJson | ConvertFrom-Json).tables.PSObject.Properties[$Entry.Name].Value
    if ($Now.count -ne ($Entry.Value.count+$Extra)) {
        throw "Unexpected fixture delta in $($Entry.Name); STOP"
    }
    foreach ($OldHash in @($Entry.Value.rows)) {
        if (@($Now.rows) -notcontains $OldHash) {
            throw "Pre-existing $($Entry.Name) row changed; STOP"
        }
    }
}
$FixtureProofCode = @'
import hashlib, os
from uuid import UUID
from noah.db import connect
user, project = UUID(os.environ['NOAH_M17_USER']), UUID(os.environ['NOAH_M17_PROJECT'])
label = os.environ['NOAH_M17_LABEL']
token_hash = hashlib.sha256(os.environ['NOAH_M17_TOKEN'].encode('utf-8')).hexdigest()
with connect() as db:
 db.execute('SET TRANSACTION READ ONLY')
 u = db.execute('SELECT label FROM noah.users WHERE id=%s',(user,)).fetchone()
 t = db.execute('SELECT token_hash,revoked_at FROM noah.api_tokens WHERE user_id=%s',
  (user,)).fetchall()
 p = db.execute('SELECT label FROM noah.projects WHERE id=%s',(project,)).fetchone()
 m = db.execute('SELECT user_id,can_write FROM noah.project_memberships '
  'WHERE project_id=%s',(project,)).fetchall()
 if (u is None or u['label']!=label or len(t)!=1 or
     t[0]['token_hash']!=token_hash or t[0]['revoked_at'] is not None or
     p is None or p['label']!=label or len(m)!=1 or
     m[0]['user_id']!=user or m[0]['can_write'] is not False):
  raise RuntimeError('Synthetic fixture ownership differs; STOP')
print('Synthetic fixture ownership verified read-only')
'@
$env:NOAH_M17_USER=$UserId
$env:NOAH_M17_PROJECT=$ProjectId
$env:NOAH_M17_LABEL=$RunLabel
$env:NOAH_M17_TOKEN=$TestToken
try {
    $FixtureProofCode | & $Python -
    if ($LASTEXITCODE -ne 0) { throw 'Fixture ownership proof failed; STOP' }
} finally {
    @('NOAH_M17_USER','NOAH_M17_PROJECT','NOAH_M17_LABEL','NOAH_M17_TOKEN') |
        ForEach-Object { Remove-Item -Path ("Env:"+$_) -ErrorAction SilentlyContinue }
}
Write-Output 'One synthetic user/token/project/read-only membership and one public document prepared'
```

Expected: two safe lines. The read-only ownership proof and 20-table snapshot must pass before server start; expected deltas are exactly `users+1`, `api_tokens+1`, `projects+1`, `project_memberships+1`, with no Task/Execution/Audit/Evidence. If DB fixture acknowledgement or file ownership is uncertain, **STOP**. Keep A variables; do not infer cleanup eligibility from a count alone.

## 6. B — start working-tree NOAH; A — create one Session

For the **private-DB path**, B runs only the server (no `init`) and leaves the window open. Record the B PowerShell PID printed before launching Python:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
Write-Output "B PowerShell PID: $PID"
& '.\.venv\Scripts\python.exe' -m noah serve --port 8080
```

For the **isolated-first path**, B uses the exact temporary root and marker printed in Section 0. Enter those two nonsecret values in B; do not point B at the source repo. The original virtualenv supplies packages, while `-m noah` imports the copied working-tree modules from the temporary root:

```powershell
$RunRoot=Read-Host 'Paste the exact isolated source root from A'
$RunMarker=Read-Host 'Paste the exact isolated marker from A'
$Python='C:\Development\project-noah\.venv\Scripts\python.exe'
$Resolved=(Resolve-Path -LiteralPath $RunRoot).Path
$TempRoot=(Resolve-Path -LiteralPath $env:TEMP).Path
if (-not $Resolved.StartsWith($TempRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or
    -not (Split-Path -Leaf $Resolved).StartsWith('noah-m17-isolated-') -or
    (Get-Content -LiteralPath (Join-Path $Resolved '.m17-isolated') -Raw -Encoding UTF8) -cne $RunMarker) {
    throw 'B does not own the exact isolated source copy; STOP'
}
Set-Location -LiteralPath $Resolved
$env:PYTHONDONTWRITEBYTECODE='1'
$env:NOAH_M17_EXPECTED_ROOT=$Resolved
try {
    & $Python -c 'import os; from pathlib import Path; from noah.db import ROOT,local_settings; s=local_settings(); assert ROOT.resolve()==Path(os.environ["NOAH_M17_EXPECTED_ROOT"]).resolve() and s["POSTGRES_PORT"]=="62417" and s["POSTGRES_DB"]=="noah_m17"'
    if ($LASTEXITCODE -ne 0) { throw 'B import root/DB target differs; STOP' }
} finally { Remove-Item Env:NOAH_M17_EXPECTED_ROOT -ErrorAction SilentlyContinue }
Write-Output "B PowerShell PID: $PID"
& $Python -m noah serve --port 8080
```

Run **only one** of those B blocks. Before the first HTTP request, A must bind the 8080 listener to the B PowerShell process and the exact Python executable. Enter the PID shown in B (a nonsecret identifier). The later restart must pass the same ownership check again with a new Python listener PID:

```powershell
$BPowerShellPid=[int](Read-Host 'Enter the B PowerShell PID shown above')
function Assert-OwnedNoahListener([int]$PriorServerPid=0) {
    $Listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
        Where-Object { $_.LocalPort -eq 8080 })
    if ($Listeners.Count -ne 1 -or $Listeners[0].LocalAddress -ne '127.0.0.1' -or
        ($PriorServerPid -ne 0 -and $Listeners[0].OwningProcess -eq $PriorServerPid)) {
        throw '8080 listener is missing, duplicated, non-loopback or stale; STOP'
    }
    $Process=Get-CimInstance Win32_Process -Filter ("ProcessId=$($Listeners[0].OwningProcess)")
    $ExpectedPython=(Resolve-Path -LiteralPath $Python).Path
    if ($null -eq $Process -or $Process.ParentProcessId -ne $BPowerShellPid -or
        -not $Process.ExecutablePath.Equals($ExpectedPython,[StringComparison]::OrdinalIgnoreCase) -or
        $Process.CommandLine -notmatch '\-m\s+noah\s+serve\s+--port\s+8080(\s|$)') {
        throw "8080 is not owned by this run's B/Python server; STOP"
    }
    return [int]$Listeners[0].OwningProcess
}
$NoahServerPid=Assert-OwnedNoahListener
Write-Output "One loopback 8080 listener belongs to this run's B/Python process"
```

Expected: one safe ownership line. If the executable path, command line, parent B PID or listener differs, **STOP**; do not stop or reuse an unrelated 8080 service. PowerShell 5.1 must send explicit UTF-8 bytes and `application/json; charset=utf-8`:

```powershell
$JsonType = 'application/json; charset=utf-8'
$Headers = @{Authorization="Bearer $TestToken"}
function ConvertTo-NoahJsonBytes($Value) {
    $Json = $Value | ConvertTo-Json -Depth 6 -Compress
    [byte[]]$Bytes = [System.Text.UTF8Encoding]::new($false,$true).GetBytes($Json)
    return ,$Bytes
}
$EmptyBody = ConvertTo-NoahJsonBytes @{}
if ($EmptyBody -isnot [byte[]] -or
    [System.Text.UTF8Encoding]::new($false,$true).GetString($EmptyBody) -cne '{}') {
    throw 'PowerShell JSON bytes differ; STOP before HTTP'
}
if ($CreateSent) { throw 'Session POST already attempted; STOP' }
$CreateSent = $true # EXACTLY ONE POST; NEVER RE-RUN THIS BLOCK.
$CreateHttp = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/sessions' -Headers $Headers `
    -ContentType $JsonType -Body $EmptyBody -TimeoutSec 90
$Created = $CreateHttp.Content | ConvertFrom-Json
if ($CreateHttp.StatusCode -ne 201 -or $Created.status -ne 'succeeded' -or
    $Created.outcome -ne 'created' -or $Created.session.status -ne 'active') {
    throw 'Session creation differs; STOP without another POST'
}
$SessionId = [string]$Created.session.session_id
if (([guid]$SessionId).ToString() -cne $SessionId) { throw 'Session ID invalid; STOP' }
$ScopedHeaders = @{Authorization="Bearer $TestToken";'Noah-Session-Id'=$SessionId}
$SessionOwnerCode = @'
import os
from uuid import UUID
from noah.db import connect
user, session = UUID(os.environ['NOAH_M17_USER']), UUID(os.environ['NOAH_M17_SESSION'])
with connect() as db:
 db.execute('SET TRANSACTION READ ONLY')
 rows = db.execute('SELECT id,closed_at FROM noah.sessions '
  'WHERE owner_user_id=%s',(user,)).fetchall()
 audits = db.execute('SELECT count(*) AS n FROM noah.routing_audit '
  'WHERE actor_user_id=%s',(user,)).fetchone()['n']
 if len(rows)!=1 or rows[0]['id']!=session or rows[0]['closed_at'] is not None or audits!=0:
  raise RuntimeError('Session ownership or pre-route audit state differs; STOP')
print('One active synthetic Session owned by caller; no routing audit')
'@
$env:NOAH_M17_USER=$UserId
$env:NOAH_M17_SESSION=$SessionId
try {
    $SessionOwnerCode | & $Python -
    if ($LASTEXITCODE -ne 0) { throw 'Session ownership proof failed; STOP' }
} finally {
    Remove-Item Env:NOAH_M17_USER,Env:NOAH_M17_SESSION -ErrorAction SilentlyContinue
}
Write-Output 'Exactly one active synthetic Session created'
```

Expected: two safe lines, with one owned Session and no new Task/Execution/Audit. A lost response or `SESSION_OUTCOME_UNKNOWN` is a **STOP**, not a reason to create another Session.

## 7. A — first routed M10 answer, exactly one POST

The first question requires one fact from the one synthetic file. Model choice and answer are observations, not guarantees. Check the prepared byte array's round-trip and expected DB delta before sending:

```powershell
$FirstQuestion = '이 프로젝트 문서에서 NOAH의 M17 테스트 동물이 무엇인지 근거를 찾아 알려줘.'
$FirstBody = ConvertTo-NoahJsonBytes @{question=$FirstQuestion;project_id=$ProjectId}
$FirstDecoded = [System.Text.UTF8Encoding]::new($false,$true).GetString($FirstBody) |
    ConvertFrom-Json
if ($FirstBody -isnot [byte[]] -or $FirstDecoded.question -cne $FirstQuestion -or
    $FirstDecoded.project_id -cne $ProjectId -or $M10Sent) {
    throw 'M10 request encoding/once-only guard failed; STOP'
}
$M10Sent = $true # EXACTLY ONE M10 POST; NEVER RE-RUN THIS BLOCK.
$M10Http = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/requests/route' -Headers $ScopedHeaders `
    -ContentType $JsonType -Body $FirstBody -TimeoutSec 180
$M10 = $M10Http.Content | ConvertFrom-Json
if ($M10Http.StatusCode -ne 200 -or $M10.status -ne 'succeeded' -or
    $M10.routing.outcome -ne 'selected' -or
    $M10.routing.capability -ne 'project.documents.answer.auto' -or
    $M10.routing.audit_status -ne 'recorded' -or
    $M10.result.status -ne 'succeeded' -or
    @('supported','partial') -notcontains $M10.result.outcome -or
    -not $M10.result.grounded -or @($M10.result.sources).Count -ne 1 -or
    @($M10.result.evidence).Count -lt 1 -or
    @($M10.result.evidence).Count -gt 3) {
    throw 'M10 did not yield one verified grounded source; STOP; never resend'
}
$M10RouterId = [string]$M10.router_id
$M10ExecutionId = [string]$M10.result.execution_id
$M10TaskId = [string]$M10.result.task_id
Write-Output 'One scoped M10 answer captured; verify DB lineage before restart'
```

Expected: one safe line. Read-only verification must prove M10 Audit owner/Session, one M10 Task/Execution, parent candidate/selection evidence, one D1 source for `$DocName`, 1–3 exact D1 quotes including the animal fact, UTF-8 byte length and original-file SHA-256, and no M17 Evidence yet. If the actual model selects `no_action`, two sources, or an unrelated quote, **STOP**. Recheck a verifier against the captured `$M10`; never resend the POST.

Use this one verifier for the M10 checkpoint, the later M17 checkpoint, and the exact cleanup gate. It prints only a generic confirmation; response JSON, token, document, and fingerprint remain in A. In `delete` mode, all the same ownership checks run **before** one transaction deletes anything.

```powershell
$ProofCode = @'
import hashlib, json, os, sys
from pathlib import Path
from uuid import UUID
from noah.db import connect, local_settings
from noah.document_auto import candidate_hash
mode = sys.argv[1]
if mode not in ('m10','final','delete'): raise RuntimeError('Proof mode invalid; STOP')
actor,project,session = map(UUID,(os.environ['NOAH_M17_USER'],
 os.environ['NOAH_M17_PROJECT'],os.environ['NOAH_M17_SESSION']))
m10 = json.loads(os.environ['NOAH_M17_M10'])
m17 = json.loads(os.environ['NOAH_M17_M17']) if mode != 'm10' else None
label,root_id,name = (os.environ['NOAH_M17_LABEL'],
 os.environ['NOAH_M17_ROOT_ID'],os.environ['NOAH_M17_DOC_NAME'])
token_hash = hashlib.sha256(os.environ['NOAH_M17_TOKEN'].encode()).hexdigest()
root = Path(os.environ['NOAH_M17_DOC_ROOT'])
raw = (root/name).read_bytes()
if raw.startswith(b'\xef\xbb\xbf'): raise RuntimeError('Synthetic BOM changed; STOP')
content = raw.decode('utf-8',errors='strict')
digest = hashlib.sha256(raw).hexdigest()
if digest != os.environ['NOAH_M17_DOC_HASH'] or len(raw)>=2048:
 raise RuntimeError('Synthetic document changed; STOP')
def need(condition, message):
 if not condition: raise RuntimeError(message+'; STOP')
def exact(db, sql, params, count):
 found = db.execute(sql+' RETURNING 1',params).fetchall()
 need(len(found)==count,'Exact cleanup row count differs')
with connect() as db:
 db.execute('SET TRANSACTION ISOLATION LEVEL '+
  ('SERIALIZABLE' if mode=='delete' else 'REPEATABLE READ READ ONLY'))
 user = db.execute('SELECT label FROM noah.users WHERE id=%s',(actor,)).fetchone()
 need(user is not None and user['label']==label,'User ownership')
 tokens = db.execute('SELECT token_hash,revoked_at FROM noah.api_tokens WHERE user_id=%s',
  (actor,)).fetchall()
 need(len(tokens)==1 and tokens[0]['token_hash']==token_hash and
  tokens[0]['revoked_at'] is None,'Token ownership')
 projects = db.execute('SELECT id,label FROM noah.projects WHERE id=%s',
  (project,)).fetchall()
 need(len(projects)==1 and projects[0]['label']==label,'Project ownership')
 memberships = db.execute('SELECT user_id,can_write FROM noah.project_memberships '
  'WHERE project_id=%s',(project,)).fetchall()
 need(len(memberships)==1 and memberships[0]['user_id']==actor and
  memberships[0]['can_write'] is False,'Read-only membership')
 sessions = db.execute('SELECT id,closed_at FROM noah.sessions WHERE owner_user_id=%s',
  (actor,)).fetchall()
 need(len(sessions)==1 and sessions[0]['id']==session and
  sessions[0]['closed_at'] is None,'Active Session owner')
 audits = db.execute('SELECT * FROM noah.routing_audit WHERE actor_user_id=%s',
  (actor,)).fetchall()
 tasks = db.execute('SELECT * FROM noah.tasks WHERE actor_user_id=%s',
  (actor,)).fetchall()
 executions = db.execute('SELECT * FROM noah.execution_records WHERE actor_user_id=%s',
  (actor,)).fetchall()
 expected = 1 if mode=='m10' else 2
 need(len(audits)==expected and len(tasks)==expected and
  len(executions)==expected,'Exactly one execution per routed answer')
 by_router = {r['router_id']:r for r in audits}
 by_task = {r['id']:r for r in tasks}
 by_execution = {r['id']:r for r in executions}
 def execution_proof(body,capability):
  route,task_id,execution_id,request_id = map(UUID,(body['router_id'],
   body['result']['task_id'],body['result']['execution_id'],
   body['result']['request_id']))
  a,t,e = by_router.get(route),by_task.get(task_id),by_execution.get(execution_id)
  need(a is not None and t is not None and e is not None,'Recorded IDs')
  need(a['actor_user_id']==actor and a['session_id']==session and
   a['stage']=='observed' and a['validated_route']==capability and
   a['delegate_capability']==capability and a['dispatch_prepared'] and
   a['delegate_result_observed'] and a['observation_class']=='delegate_returned' and
   a['http_status']==200 and a['outcome_code']==body['result']['outcome'] and
   a['delegate_request_id']==request_id and a['delegate_task_id']==task_id and
   a['delegate_execution_id']==execution_id,'Audit correlation')
  need(t['actor_user_id']==actor and t['status']=='completed' and
   t['verification_status']=='passed' and e['actor_user_id']==actor and
   e['task_id']==task_id and e['request_id']==request_id and
   e['capability']==capability and e['status']=='succeeded' and
   e['verified_at'] is not None,'Task/Execution truth')
  return route,execution_id
 prior_router,prior_execution = execution_proof(m10,'project.documents.answer.auto')
 p = db.execute('SELECT * FROM noah.auto_document_answer_evidence WHERE execution_id=%s',
  (prior_execution,)).fetchone()
 sources = db.execute('SELECT * FROM noah.auto_document_source_evidence '
  'WHERE execution_id=%s',(prior_execution,)).fetchall()
 old_quotes = db.execute('SELECT * FROM noah.auto_document_quote_evidence '
  'WHERE execution_id=%s ORDER BY quote_ordinal',(prior_execution,)).fetchall()
 need(p is not None and p['project_id']==project and p['root_id']==root_id and
  p['candidate_count']==1 and p['candidate_names']==[name] and
  p['candidate_sha256']==candidate_hash(project,root_id,[name]) and
  p['selection_outcome']=='selected' and p['selected_count']==1 and
  p['selected_names']==[name] and p['raw_candidate_names']==[name] and
  p['truncated'] is False and p['answer_outcome'] in ('supported','partial') and
  len(sources)==1 and sources[0]['source_id']=='D1' and
  sources[0]['source_ordinal']==1 and sources[0]['document_name']==name and
  sources[0]['byte_length']==len(raw) and sources[0]['content_sha256']==digest and
  sources[0]['content_encoding']=='utf-8' and sources[0]['bom_present'] is False,
  'M10 parent/source provenance')
 need(1<=len(old_quotes)<=3 and len(old_quotes)==len(m10['result']['evidence']),
  'M10 quote count')
 for index,(stored,shown) in enumerate(zip(old_quotes,m10['result']['evidence']),1):
  quote = stored['quote']
  need(stored['quote_ordinal']==index and stored['source_id']=='D1' and
   quote==shown['quote'] and shown['source_id']=='D1' and
   stored['start_index']==shown['start']==content.find(quote) and
   stored['end_index']==shown['end']==stored['start_index']+len(quote),
   'M10 exact Unicode quote')
 need(any('\uC218\uB2EC' in r['quote'] for r in old_quotes),'Animal fact quote')
 follow_rows = db.execute('SELECT * FROM noah.document_followup_evidence '
  'WHERE prior_execution_id=%s',(prior_execution,)).fetchall()
 if mode=='m10':
  need(len(follow_rows)==0,'Premature M17 Evidence')
 else:
  current_router,current_execution = execution_proof(
   m17,'project.documents.answer.followup')
  need(len(follow_rows)==1,'M17 Evidence count')
  f = follow_rows[0]
  need(f['execution_id']==current_execution and
   f['current_router_id']==current_router and
   f['prior_router_id']==prior_router and f['prior_execution_id']==prior_execution and
   f['project_id']==project and f['root_id']==root_id and
   f['document_name']==name and f['prior_content_sha256']==digest and
   f['content_sha256']==digest and f['byte_length']==len(raw) and
   f['content_encoding']=='utf-8' and f['bom_present'] is False and
   f['outcome']==m17['result']['outcome'],'M17 exact lineage/observation')
  need(1<=len(f['quotes'])<=3 and len(f['quotes'])==len(m17['result']['evidence']),
   'M17 quote count')
  for stored,shown in zip(f['quotes'],m17['result']['evidence']):
   quote=stored['quote']
   need(quote==shown['quote'] and
    stored['start']==shown['start']==content.find(quote) and
    stored['end']==shown['end']==stored['start']+len(quote),
    'M17 exact Unicode quote')
  need(any('\uD30C\uB780\uC0C9' in r['quote'] for r in f['quotes']),'Color fact quote')
  metadata=json.dumps({'audit':audits,'m10_parent':p,'m10_sources':sources,
   'm10_quotes':old_quotes,'followup':f},default=str,ensure_ascii=False)
  forbidden=(os.environ['NOAH_M17_TOKEN'],token_hash,str(root),content,
   local_settings()['POSTGRES_PASSWORD'])
  need(all(value not in metadata for value in forbidden if value),
   'Forbidden Audit/Evidence content')
 if mode=='delete':
  exact(db,'DELETE FROM noah.document_followup_evidence WHERE execution_id=%s '
   'AND current_router_id=%s AND prior_execution_id=%s',
   (current_execution,current_router,prior_execution),1)
  exact(db,'DELETE FROM noah.auto_document_quote_evidence WHERE execution_id=%s',
   (prior_execution,),len(old_quotes))
  exact(db,'DELETE FROM noah.auto_document_source_evidence WHERE execution_id=%s '
   'AND source_id=%s',(prior_execution,'D1'),1)
  exact(db,'DELETE FROM noah.auto_document_answer_evidence WHERE execution_id=%s '
   'AND project_id=%s',(prior_execution,project),1)
  exact(db,'DELETE FROM noah.routing_audit WHERE router_id IN (%s,%s) '
   'AND actor_user_id=%s AND session_id=%s',
   (prior_router,current_router,actor,session),2)
  exact(db,'DELETE FROM noah.execution_records WHERE id IN (%s,%s) '
   'AND actor_user_id=%s',(prior_execution,current_execution,actor),2)
  exact(db,'DELETE FROM noah.tasks WHERE id IN (%s,%s) AND actor_user_id=%s',
   (UUID(m10['result']['task_id']),UUID(m17['result']['task_id']),actor),2)
  exact(db,'DELETE FROM noah.sessions WHERE id=%s AND owner_user_id=%s '
   'AND closed_at IS NULL',(session,actor),1)
  exact(db,'DELETE FROM noah.project_memberships WHERE project_id=%s '
   'AND user_id=%s AND can_write=false',(project,actor),1)
  exact(db,'DELETE FROM noah.projects WHERE id=%s AND label=%s',(project,label),1)
  exact(db,'DELETE FROM noah.api_tokens WHERE user_id=%s AND token_hash=%s',
   (actor,token_hash),1)
  exact(db,'DELETE FROM noah.users WHERE id=%s AND label=%s',(actor,label),1)
print('Exact synthetic ownership and provenance verified' if mode!='delete'
 else 'Exact synthetic rows removed in one transaction')
'@
function Invoke-M17Proof([string]$Mode) {
    $env:NOAH_M17_USER=$UserId
    $env:NOAH_M17_PROJECT=$ProjectId
    $env:NOAH_M17_SESSION=$SessionId
    $env:NOAH_M17_M10=$M10Http.Content
    $env:NOAH_M17_M17=$(if ($Mode -eq 'm10') { '' } else { $M17Http.Content })
    $env:NOAH_M17_LABEL=$RunLabel
    $env:NOAH_M17_ROOT_ID=$RootId
    $env:NOAH_M17_DOC_NAME=$DocName
    $env:NOAH_M17_DOC_ROOT=$DocRoot
    $env:NOAH_M17_DOC_HASH=$DocHash
    $env:NOAH_M17_TOKEN=$TestToken
    try {
        $ProofCode | & $Python - $Mode
        if ($LASTEXITCODE -ne 0) { throw 'Ownership/provenance verifier failed; STOP' }
    } finally {
        @('NOAH_M17_USER','NOAH_M17_PROJECT','NOAH_M17_SESSION','NOAH_M17_M10',
          'NOAH_M17_M17','NOAH_M17_LABEL','NOAH_M17_ROOT_ID','NOAH_M17_DOC_NAME',
          'NOAH_M17_DOC_ROOT','NOAH_M17_DOC_HASH','NOAH_M17_TOKEN') |
          ForEach-Object {
            Remove-Item -Path ("Env:"+$_) -ErrorAction SilentlyContinue
          }
    }
}
function Assert-M17Delta([string]$CurrentJson,[hashtable]$Delta) {
    $Current=$CurrentJson | ConvertFrom-Json
    foreach ($Entry in $Baseline.tables.PSObject.Properties) {
        $Name=$Entry.Name
        $Extra=if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        $Now=$Current.tables.PSObject.Properties[$Name].Value
        if ($Now.count -ne ($Entry.Value.count+$Extra)) {
            throw "Unexpected durable delta in $Name; STOP"
        }
        foreach ($OldHash in @($Entry.Value.rows)) {
            if (@($Now.rows) -notcontains $OldHash) {
                throw "Pre-existing $Name row changed; STOP"
            }
        }
    }
    if ($Current.running_tasks -ne 0 -or
        $Current.running_execution_records -ne 0) {
        throw 'Running Task/Execution remains; STOP'
    }
}
Invoke-M17Proof m10
$AfterM10Json=Get-NoahSnapshot post
Assert-M17Delta $AfterM10Json @{
    users=1;api_tokens=1;projects=1;project_memberships=1;sessions=1;
    routing_audit=1;tasks=1;execution_records=1;
    auto_document_answer_evidence=1;auto_document_source_evidence=1;
    auto_document_quote_evidence=@($M10.result.evidence).Count
}
```

Expected: safe verifier line and no exception; no M17 Evidence yet. This step is **read-only** and may be rerun against the *same captured* `$M10` if its verifier code needs repair.

## 8. B — stop and restart; A — inspect same Session

Stop only the owned server in B with **Ctrl+C**. Confirm 8080 has no listener before restarting the **same chosen B command** (private or isolated). Do not restart PostgreSQL or either Ollama. In A, run `$NoahServerPid=Assert-OwnedNoahListener $NoahServerPid` after the new listener appears; it must be a new Python PID with the same B parent. After that ownership proof, inspect the existing Session without creating a new one:

```powershell
$InspectHttp = Invoke-WebRequest -UseBasicParsing -Method Get `
    -Uri "http://127.0.0.1:8080/sessions/$SessionId" -Headers $Headers -TimeoutSec 30
$Inspected = $InspectHttp.Content | ConvertFrom-Json
if ($InspectHttp.StatusCode -ne 200 -or $Inspected.status -ne 'succeeded' -or
    $Inspected.session.session_id -cne $SessionId -or
    $Inspected.session.status -ne 'active') {
    throw 'Session continuity after restart differs; STOP'
}
Write-Output 'The same active Session is visible after NOAH restart'
```

Expected: one safe line. Read-only DB verification must still find the confirmed M10 Audit and its Evidence in the same Session. A service restart is not an API retry.

## 9. A — natural M17 follow-up, exactly one POST

```powershell
$FollowQuestion = '그 문서의 M17 테스트 색상은 무엇이야?'
$FollowBody = ConvertTo-NoahJsonBytes @{
    question=$FollowQuestion;project_id=$ProjectId;document_follow_up=$true
}
$FollowDecoded = [System.Text.UTF8Encoding]::new($false,$true).GetString($FollowBody) |
    ConvertFrom-Json
if ($FollowBody -isnot [byte[]] -or
    $FollowDecoded.question -cne $FollowQuestion -or
    $FollowDecoded.project_id -cne $ProjectId -or
    $FollowDecoded.document_follow_up -ne $true -or $M17Sent) {
    throw 'M17 UTF-8/request-shape/once-only guard failed; STOP'
}
$M17Sent = $true # EXACTLY ONE M17 POST; NEVER RE-RUN THIS BLOCK.
$M17Http = Invoke-WebRequest -UseBasicParsing -Method Post `
    -Uri 'http://127.0.0.1:8080/requests/route' -Headers $ScopedHeaders `
    -ContentType $JsonType -Body $FollowBody -TimeoutSec 180
$M17 = $M17Http.Content | ConvertFrom-Json
if ($M17Http.StatusCode -ne 200 -or $M17.status -ne 'succeeded' -or
    $M17.routing.outcome -ne 'selected' -or
    $M17.routing.capability -ne 'project.documents.answer.followup' -or
    $M17.routing.audit_status -ne 'recorded' -or
    $M17.result.status -ne 'succeeded' -or
    @('supported','partial') -notcontains $M17.result.outcome -or
    -not $M17.result.grounded -or
    @($M17.result.evidence).Count -lt 1 -or
    @($M17.result.evidence).Count -gt 3 -or
    $M17.result.context_source.prior_router_id -cne $M10RouterId -or
    $M17.result.context_source.prior_execution_id -cne $M10ExecutionId -or
    $M17.result.document.document_name -cne $DocName -or
    $M17.result.document.content_sha256 -cne $DocHash) {
    throw 'M17 result/provenance differs; STOP; never resend'
}
$M17RouterId = [string]$M17.router_id
$M17ExecutionId = [string]$M17.result.execution_id
$M17TaskId = [string]$M17.result.task_id
Write-Output 'One grounded M17 follow-up captured; verify lineage and quotes read-only'
```

Expected: one safe line. The D1 prior source is reused only as an identity reference; M17 reads the current file again. For each returned quote, compare exact decoded text and first Unicode `[start,end)` position in **this** file; at least one quote should contain `파란색`. A valid `partial` remains `partial`. Reject unexpected route, malformed output, source mismatch, no quote, DB uncertainty, or model timeout without retry.

## 10. A — read-only ownership, Evidence, and baseline delta proof

Use the captured IDs and this run's user/project/Session. Query through a repeatable-read, read-only transaction. Check exact SQL relationships rather than trusting HTTP IDs. The verifier must assert:

- two distinct Session-scoped `routing_audit` rows owned by `$UserId`, both `observed`, with validated routes M10 and M17 and `delegate_returned`; their request/Task/Execution IDs match captured responses;
- exactly one M10 and one M17 Task/Execution, both completed/passed and succeeded/verified; no unrelated Capability Execution or extra Evidence;
- the M10 parent has `selection_outcome=selected`, `selected_count=1`, one D1 source; candidate and selected logical filenames match `$DocName`, original byte length/SHA-256 and 1–3 D1 exact quotes/positions match the file;
- `document_followup_evidence.execution_id=$M17ExecutionId`, `current_router_id=$M17RouterId`, `prior_router_id=$M10RouterId`, `prior_execution_id=$M10ExecutionId`, `project_id=$ProjectId`, root/name/hash/byte length and exact quote positions match the freshly read file;
- Audit/Evidence contain no question, complete document text, OS absolute path, token/hash, DB credential, raw model output, or previous answer; do not print any private baseline row or fingerprint.

The expected post-request row delta from the 20-table post-migration baseline is: `users+1`, `api_tokens+1`, `projects+1`, `project_memberships+1`, `sessions+1`, `routing_audit+2`, `tasks+2`, `execution_records+2`, M10 parent/source `+1` each, M10 quote `+1..3`, M17 Evidence `+1`, and every other table unchanged. For each pre-existing row, its private fingerprint must still be present. A verifier exception is not proof of an API failure. **STOP** before cleanup on any unexpected row, ID, status, source, quote, path/secret, or delta.

```powershell
Invoke-M17Proof final
$AfterM17Json=Get-NoahSnapshot post
Assert-M17Delta $AfterM17Json @{
    users=1;api_tokens=1;projects=1;project_memberships=1;sessions=1;
    routing_audit=2;tasks=2;execution_records=2;
    auto_document_answer_evidence=1;auto_document_source_evidence=1;
    auto_document_quote_evidence=@($M10.result.evidence).Count;
    document_followup_evidence=1
}
if ((Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHash -or
    (Get-FileHash -LiteralPath $DocPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $DocHash) {
    throw 'Volume/mapping/document changed; STOP'
}
Write-Output 'M17 lineage, source-aware quotes, and full 20-table delta verified'
```

Expected: two safe confirmation lines. No API call is made by this verifier. The row fingerprints remain in A variables and are never printed.

## 11. B — stop server; A — exact synthetic cleanup

Stop only the server in B with **Ctrl+C** and confirm port 8080 is free. Before any DELETE, repeat the read-only Section 10 ownership/lineage verifier, check the named volume, mapping hash, document hash, and current post-request snapshot. The cleanup transaction must verify this run's unique user label, token hash, project/read-only membership, active Session, both Audit IDs, both Task/Execution IDs, M10 parent/source/quote rows, and the single M17 Evidence row. If any other row belongs to this user/project or any ID belongs to a different owner, **STOP**.

Delete only by those exact IDs and verified owners in one transaction, with `RETURNING` row counts checked before commit. FK order is **M17 Evidence first** (it references both Audit rows, the M17 and prior M10 Executions, and the project), then M10 quote → source → parent Evidence, then the two Audit rows, two Executions, two Tasks, Session, membership, project, token, user. Never use a broad table DELETE, cascade, or recursive filesystem deletion. On uncertain cleanup commit, do not repeat DELETE automatically; inspect state read-only and request separate review.

The `Invoke-M17Proof` function above performs the exact owner, source, and row-count checks before its `delete` mode. These are separate operator blocks: first a read-only gate, then one deliberately authorized delete attempt. Stop B and confirm no 8080 listener before the first block:

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
    (Get-NoahSnapshot post) -ne $AfterM17Json -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHash -or
    (Get-FileHash -LiteralPath $DocPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $DocHash) {
    throw 'Cleanup preflight differs or server still runs; STOP'
}
Invoke-M17Proof final
Write-Output 'Read-only cleanup ownership gate passed; no DELETE performed'
```

Expected: exact ownership and current state confirmed. **Only if this block passes**, execute the next block **once**. The Python transaction checks ownership again before deleting.

```powershell
if ($CleanupAttempted -or (Get-NoahSnapshot post) -ne $AfterM17Json -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore) {
    throw 'Cleanup already attempted or state moved; STOP'
}
$CleanupAttempted=$true # EXACTLY ONE TRANSACTION; NEVER BLINDLY RETRY.
Invoke-M17Proof delete
$AfterCleanupJson=Get-NoahSnapshot post
if ($AfterCleanupJson -cne $BaselineJson) {
    throw 'Original 20-table private row baseline not restored; STOP'
}
Write-Output 'Only exact synthetic rows removed; 20-table row baseline restored'
```

Expected: exact synthetic deletes followed by full baseline equality. The 013 schema stays installed. If commit acknowledgement is uncertain, **STOP** without rerunning the delete block.

After a confirmed DB cleanup, compare the entire 20-table row-count/private-fingerprint snapshot byte-for-byte with `$BaselineJson`, including an empty M17 Evidence table and running Task/Execution zero. Migration 013 stays installed. Compare `$DocHash` and `$MappingHash` to the created files, delete **only** this mapping and `.md`, then remove `$DocRoot` **only if empty**. Check the named volume, ordinary Ollama 11434 listener identity, and exact Git working-tree status against Section 1. Leave PostgreSQL running. Stop window C with **Ctrl+C only if this run started 11435**; leave any pre-existing 11435 alone. Keep the restricted backup until the operator's retention decision; never put it under Git.

```powershell
if ((Get-NoahSnapshot post) -cne $BaselineJson -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash -ne $MappingHash -or
    (Get-FileHash -LiteralPath $DocPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $DocHash) {
    throw 'Local cleanup preflight differs; STOP'
}
$ResolvedRoot = (Resolve-Path -LiteralPath $DocRoot).Path
$ResolvedTemp = (Resolve-Path -LiteralPath $env:TEMP).Path
if (-not $ResolvedRoot.StartsWith($ResolvedTemp+'\',[System.StringComparison]::OrdinalIgnoreCase) -or
    -not $ResolvedRoot.Equals($DocRoot,[System.StringComparison]::OrdinalIgnoreCase) -or
    @(Get-ChildItem -LiteralPath $DocRoot -Force).Count -ne 1 -or
    (Get-ChildItem -LiteralPath $DocRoot -Force)[0].Name -cne $DocName) {
    throw 'Synthetic root ownership/contents differ; STOP'
}
Remove-Item -LiteralPath $Mapping
Remove-Item -LiteralPath $DocPath
if (@(Get-ChildItem -LiteralPath $DocRoot -Force).Count -ne 0) {
    throw 'Root is not empty after deleting the one owned file; STOP'
}
Remove-Item -LiteralPath $DocRoot
$Ollama11434After = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
    Where-Object { $_.LocalPort -eq 11434 } |
    ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
if (($Ollama11434After -join '|') -cne ($Ollama11434Before -join '|') -or
    (Get-NoahVolumeIdentity) -ne $VolumeBefore -or
    (Test-Path -LiteralPath $Mapping) -or (Test-Path -LiteralPath $DocRoot) -or
    (Get-NoahSnapshot post) -cne $BaselineJson -or
    (@(git -C $SourceRepo status --short) -join "`n") -cne ($GitBefore -join "`n")) {
    throw 'Final environment or Git state differs; STOP'
}
$TestToken=$null
$Headers=$null
$ScopedHeaders=$null
Write-Output 'Private row baseline restored; mapping, root, named volume, Git, and 11434 checked'
```

Expected: one safe line. Then stop C with **Ctrl+C only when `$StartedOllama11435` is true**. Do not stop an Ollama service that predated this run. Leave PostgreSQL and its named volume untouched.

## Operator result record

**Second isolated run (2026-10-11): HTTP/Evidence checks PASSED; environmental cleanup INCOMPLETE.** A new Run ID, access-restricted source copy, loopback-only PostgreSQL 17 tmpfs container, synthetic user/project/document, and dedicated `gemma4:12b-it-qat` on 11435 were used. Migration 001–013 catalog checks and an empty 20-table baseline passed. The revised, source-explicit M10 question was sent once after one successful Session creation POST (HTTP 201). M10 returned HTTP 200, selected `project.documents.answer.auto`, `outcome=supported`, one D1 source, and one exact animal quote. The owned NOAH server was restarted; the same active Session remained readable. The natural M17 follow-up was sent once without an internal Router or Execution ID. It returned HTTP 200, selected `project.documents.answer.followup`, `outcome=supported`, and one exact color quote. Read-only checks passed for both observed Session Audits, exactly one Task/Execution per answer, M10 candidate/source/quote Evidence, M17 lineage Evidence, current document SHA-256, Unicode quote positions, and the exact 20-table synthetic delta. No POST was repeated.

After the owned server stopped, the exact-ownership cleanup gate passed. One transaction removed only this run's synthetic DB rows and a snapshot check confirmed restoration of the isolated empty 20-table baseline. The synthetic mapping, document, and copied source/config files were removed after hash checks. Removal of the now-empty **current-run** temporary source root failed; no second removal was attempted. The owned tmpfs container and dedicated 11435 listener were then stopped, with 8080 and the isolated PostgreSQL port absent and the pre-existing 11434 listener unchanged. This run's empty source root remains for separate ownership review. The previous run's reported empty root was not touched.

The private-DB path, private backup, and private Migration 013 were not run. A post-copy-removal read-only diagnostic inadvertently invoked the snapshot helper after changing the working directory back to the source repository. Its Python entry point loaded the source repository's DB settings and called `connect()`; successful authentication and any SQL read remain unconfirmed because no connection/statement log was available. No private DB write was requested, and there is no concrete evidence of private-data mutation or external disclosure. This run **does not claim that the private database was never accessed**. Do not treat the isolated HTTP success as private-DB acceptance or the environmental cleanup as fully complete.

**Status: ISOLATED ATTEMPT STOPPED (2026-10-11); M17 E2E NOT PASSED.**
The private-DB path was not run. The isolated attempt sent one Session creation
POST (HTTP 201) and one Session-scoped M10 routed POST (HTTP 200). The actual
model returned `no_action` for the M10 request, so the required document
answer, server restart, and M17 follow-up were not attempted. No POST was
repeated. A read-only check found one observed `no_action` Audit and no
Task, Execution, or M17 Evidence. Exact-owned abort cleanup removed six
synthetic rows in one transaction and restored the isolated empty 20-table
baseline. The owned tmpfs container, NOAH 8080, and Ollama 11435 were stopped;
the existing 11434 listener was unchanged. The synthetic mapping, document,
and source-copy files were removed. One empty temporary source directory
remained after a removal attempt and was not retried. The personal DB and
named volume were neither connected to nor inspected.

Record the two isolated attempts and any later private-DB execution separately.
Isolated HTTP success is not private-DB Migration/backup success. Do not turn
isolated automated tests into HTTP E2E results.

| Second isolated run check | Actual result |
| --- | --- |
| Session creation; M10; restart; M17 follow-up | HTTP 201, HTTP 200 `supported`, same Session, HTTP 200 `supported`; each POST sent once |
| Actual model routes and source-aware proof | M10 auto answer and M17 follow-up selected; one exact quote each; two Audits, two Task/Execution pairs and verified M10→M17 lineage |
| Synthetic DB and owned services | Exact-owned DB deletion and empty 20-table baseline confirmed; 8080, 11435 and tmpfs container stopped; 11434 unchanged |
| Final environment isolation and source root | Empty current-run source root remained; later diagnostic loaded source DB settings and called `connect()`; successful DB connection/SQL read unconfirmed |

First isolated attempt (historical, stopped at M10 routing):

| Isolated-first check | Actual result |
| --- | --- |
| Source copy/root/port ownership; PostgreSQL 17 tmpfs and empty 20-table baseline | Passed before HTTP |
| Migration 013 CHECK/FK catalog proof in isolated DB | Passed |
| Actual 11435 model: one M10 response, NOAH restart, one M17 follow-up | Stopped: M10 selected `no_action`; restart and M17 not run |
| Exact Audit/Task/Execution/Evidence and quote/hash/position proof | One `no_action` Audit, Task/Execution/Evidence 0; M10/M17 quote proof not reached |
| Exact synthetic cleanup, empty baseline restoration, owned container/copy removal | Six rows removed; baseline and container cleanup passed; files removed; empty temporary source directory remained |

Private-DB path (execute only after separate approval and an isolated-first result review):

| Check | Actual result |
| --- | --- |
| Preflight: working tree, PostgreSQL 17, named volume, listeners/model | Pending |
| Original 19-table private baseline, backup, isolated restore | Pending |
| Migration 013 CHECK/FK catalog proof; unchanged old rows; 20-table baseline | Pending |
| Synthetic user/token/project/read-only membership/file/mapping/Session | Pending |
| One M10 routed POST: selected one source, exact D1 quote and SHA-256 | Pending |
| NOAH stop/restart; same active Session and M10 provenance | Pending |
| One M17 routed POST: prior lineage, fresh exact quote/position/hash | Pending |
| Exact M10/M17 Task/Execution/Evidence and two Audit links | Pending |
| Exact-owned cleanup and complete 20-table private baseline restoration | Pending |
| Named volume, mapping, Git, 11434 unchanged; owned services stopped | Pending |

Automated failure injection, lock races, commit acknowledgement uncertainty, and actual-model semantic accuracy are separate evidence categories. This run does not induce those faults. It also does not prove a strict human conversation-turn order: M17 selects a source at its specified DB statement snapshot.
