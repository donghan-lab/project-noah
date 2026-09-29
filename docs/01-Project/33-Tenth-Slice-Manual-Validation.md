# M10 manual E2E validation — operator procedure

> Prepared 2026-09-29. The first user-run attempt produced a valid
> `no_document_selected` result and **did not pass** the intended two-source
> E2E; targeted cleanup restored the DB baseline and removed the synthetic
> mapping, files, and root. After the filename-only selection fix, a second
> run with fresh synthetic IDs selected both files, returned two verified
> source quotes, `grounded=true`, and `partial`. This is a **successful
> two-source grounded execution** under the M9/M10 contract. The second run
> and its exact cleanup are recorded in the validation report. No repeat
> manual request is needed to validate the current runtime. If this procedure
> is used again later, create fresh synthetic IDs and send the request once.
> Keep PowerShell
> window A and its variables open through cleanup. Start NOAH in a separate
> window B. Stop at the first unexpected result; do not retry the successful
> M10 request or automatically continue cleanup after a failure.

## Read-only state observed while preparing this procedure

- `main` is still `0c7a1076bb4409337881f950a507113806a7346e`; only the
  uncommitted M10 implementation, test, validation, and contract files were
  present before this procedure document was added.
- `noah-postgres` was running `postgres:17`; SQL reported PostgreSQL 17.10.
  Migration 007's `auto_document_answer_evidence`,
  `auto_document_source_evidence`, and `auto_document_quote_evidence` tables
  and their declared columns exist.
- Counts: users 1, API tokens 1, memories 2, Tasks 2, Execution Records 3,
  M4 mappings 1; projects, memberships, M6–M10 Evidence, and running
  Tasks/Executions each 0. Read-only row fingerprints were computed without
  displaying private rows or token hashes. The commands below capture a fresh
  full baseline at execution time, then compare per-row fingerprints.
- Port 8080 had no listener. `127.0.0.1:11435` was listening, `/api/tags`
  responded, and `gemma4:12b-it-qat` was registered. The local project
  mapping did not exist. Recheck all of this immediately before setup.

The verified M10 API response has `status`, `task_id`, `execution_id`,
`capability`, `outcome`, `grounded`, `selected_document_names`,
`candidate_observation`, `sources`, and `evidence`. Migration 007's parent
has `project_id` and `root_id`; its source and quote children are joined by
`execution_id` and `source_id`. **Do not query a nonexistent project column
on either child table.**

## 1. Window A — strict precheck and private baseline

Run each block in the same Windows PowerShell 5.1 window. The Python source
in here-strings is ASCII-only and goes through stdin (`$Code | & $Python -`),
never multiline `-c`. Do not print `$Token` or the contents of `$BaselineJson`.

```powershell
$ErrorActionPreference = 'Stop'
$Repo = 'C:\Development\project-noah'
Set-Location -LiteralPath $Repo
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python)) { throw 'NOAH Python runtime missing' }
$Existing = Get-Variable -Name Token -ErrorAction SilentlyContinue
if ($null -ne $Existing -and -not [string]::IsNullOrWhiteSpace([string]$Existing.Value)) {
    $Token = [string]$Existing.Value
} elseif (-not [string]::IsNullOrWhiteSpace($env:NOAH_API_TOKEN)) {
    $Token = $env:NOAH_API_TOKEN
} else { throw 'Existing NOAH token variable is required; stop here' }
Write-Output 'Existing token available (value hidden)'

$Pg = @(docker ps --format '{{.Names}} {{.Image}} {{.Status}}' | Where-Object { $_ -match '^noah-postgres postgres:17 Up ' })
if ($LASTEXITCODE -ne 0 -or $Pg.Count -ne 1) { throw 'PostgreSQL container state unexpected' }
docker inspect noah-postgres --format '{{range .Mounts}}{{.Name}} {{.Destination}}{{end}}'
if ($LASTEXITCODE -ne 0) { throw 'Cannot verify existing named volume' }
$Net = @(netstat -ano -p tcp)
if (@($Net | Where-Object { $_ -match '^\s*TCP\s+\S+:8080\s+\S+\s+LISTENING\s+\d+' }).Count -ne 0) { throw 'Port 8080 already in use' }
if (@($Net | Where-Object { $_ -match '^\s*TCP\s+127\.0\.0\.1:11435\s+\S+\s+LISTENING\s+\d+' }).Count -ne 1) { throw 'Dedicated Ollama loopback listener missing' }
$Tags = Invoke-RestMethod -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 5
if (@($Tags.models | Where-Object { $_.name -eq 'gemma4:12b-it-qat' }).Count -ne 1) { throw 'M10 baseline model missing' }
$Mapping = Join-Path $Repo 'config\project_documents.local.json'
if (Test-Path -LiteralPath $Mapping) { throw 'Existing operator mapping must not be overwritten' }
```

Capture counts and **SHA-256 fingerprints of entire rows**, never the rows.
This snapshot includes every current table, so success and cleanup can prove
that earlier records stayed unchanged. JSON comparison is stable because
tables and row digests are sorted. Migration absence causes this block to
stop. It performs only `SELECT` statements.

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
    version = db.execute('select current_setting(%s) as v', ('server_version',)).fetchone()['v']
    if not version.startswith('17.'):
        raise RuntimeError('PostgreSQL version mismatch')
    for name in tables:
        rows = db.execute('select * from noah.' + name).fetchall()
        fingerprints = sorted(hashlib.sha256(json.dumps(row, sort_keys=True,
            default=str, ensure_ascii=True).encode('utf-8')).hexdigest() for row in rows)
        out['tables'][name] = {'count': len(rows), 'rows': fingerprints}
    for table in ('tasks','execution_records'):
        out['running_' + table] = db.execute(
            'select count(*) as n from noah.' + table + " where status='running'").fetchone()['n']
print(json.dumps(out, sort_keys=True, separators=(',', ':')))
'@
$BaselineJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0 -or -not $BaselineJson) { throw 'Baseline snapshot failed' }
$Baseline = $BaselineJson | ConvertFrom-Json
$Expected = @{ users=1; api_tokens=1; memories=2; tasks=2; execution_records=3;
    memory_write_requests=1; projects=0; project_memberships=0;
    document_tool_evidence=0; document_read_evidence=0; document_answer_evidence=0;
    selected_document_answer_evidence=0; selected_document_source_evidence=0;
    selected_document_quote_evidence=0; auto_document_answer_evidence=0;
    auto_document_source_evidence=0; auto_document_quote_evidence=0 }
foreach ($Name in $Expected.Keys) {
    if ($Baseline.tables.PSObject.Properties[$Name].Value.count -ne $Expected[$Name]) {
        throw "Unexpected baseline count for $Name"
    }
}
if ($Baseline.running_tasks -ne 0 -or $Baseline.running_execution_records -ne 0) { throw 'Existing running work; stop' }
$Protected = @('users','api_tokens','memories','memory_write_requests','tasks','execution_records')
function Assert-OldRowsUnchanged($Current) {
    foreach ($Name in $Protected) {
        $Before = @($Baseline.tables.PSObject.Properties[$Name].Value.rows)
        $After = @($Current.tables.PSObject.Properties[$Name].Value.rows)
        foreach ($Fingerprint in $Before) {
            if ($After -notcontains $Fingerprint) { throw "Existing $Name row changed" }
        }
    }
}
function Assert-Delta($Current, $Delta) {
    foreach ($Property in $Baseline.tables.PSObject.Properties) {
        $Name = $Property.Name
        $Increment = if ($Delta.ContainsKey($Name)) { [int]$Delta[$Name] } else { 0 }
        if ($Current.tables.PSObject.Properties[$Name].Value.count -ne
            ($Property.Value.count + $Increment)) { throw "Unexpected row delta for $Name" }
    }
    if ($Current.running_tasks -ne 0 -or $Current.running_execution_records -ne 0) {
        throw 'Unexpected running work'
    }
    Assert-OldRowsUnchanged $Current
}
$UserCode = @'
from noah.db import connect
with connect() as db:
    rows = db.execute('select id from noah.users').fetchall()
    if len(rows) != 1: raise RuntimeError('Expected exactly one existing user')
    print(rows[0]['id'])
'@
$UserId = $UserCode | & $Python -
if ($LASTEXITCODE -ne 0 -or -not $UserId) { throw 'Cannot identify existing user' }
Write-Output 'Baseline, migration, user, and running-state checks passed (private values hidden)'
```

## 2. Window A — create only synthetic M10 inputs

Exact names: `m10-test-animal.md`, `m10-test-color.md`. Exact question:
`NOAH의 M10 테스트 동물과 테스트 색상을 각각 알려줘.` The documents contain
public synthetic facts and extra lines so a short exact quote is not the
entire body. No personal Memory or existing project document is involved.

```powershell
$RunId = [guid]::NewGuid().ToString('N')
$ProjectId = [guid]::NewGuid().ToString()
$ProjectLabel = "m10-manual-$RunId"
$RootId = "m10-manual-$RunId"
$Root = Join-Path $Repo ".noah\m10-manual-$RunId"
$AnimalPath = Join-Path $Root 'm10-test-animal.md'
$ColorPath = Join-Path $Root 'm10-test-color.md'
if (Test-Path -LiteralPath $Root) { throw 'Synthetic root already exists' }
New-Item -ItemType Directory -Path $Root | Out-Null
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$AnimalText = @'
# M10 public animal test
NOAH의 M10 테스트 동물은 수달이다.
이 내용은 합성 검증 자료이다.
'@
$ColorText = @'
# M10 public color test
NOAH의 M10 테스트 색상은 파란색이다.
이 내용은 합성 검증 자료이다.
'@
[System.IO.File]::WriteAllText($AnimalPath, $AnimalText, $Utf8NoBom)
[System.IO.File]::WriteAllText($ColorPath, $ColorText, $Utf8NoBom)
$AnimalHash = (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant()
$ColorHash = (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant()
$AnimalBytes = [System.IO.File]::ReadAllBytes($AnimalPath).Length
$ColorBytes = [System.IO.File]::ReadAllBytes($ColorPath).Length
if ($AnimalBytes -le 0 -or $ColorBytes -le 0 -or ($AnimalBytes + $ColorBytes) -ge 2048) {
    throw 'Synthetic document byte budget invalid'
}
$Projects = @{}
$Projects[$ProjectId] = @{ root_id = $RootId; document_root = $Root }
$MappingJson = @{ projects = $Projects } | ConvertTo-Json -Depth 6 -Compress
[System.IO.File]::WriteAllText($Mapping, $MappingJson, $Utf8NoBom)
$MappingRaw = [System.IO.File]::ReadAllBytes($Mapping)
if ($MappingRaw.Length -ge 3 -and $MappingRaw[0] -eq 239 -and
    $MappingRaw[1] -eq 187 -and $MappingRaw[2] -eq 191) { throw 'Mapping contains a BOM' }
$MappingHash = (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant()
if (@(Get-ChildItem -LiteralPath $Root -Force).Count -ne 2) { throw 'Unexpected root entry' }
$SetupCode = @'
import sys
from uuid import UUID
from noah.db import connect
project, user, label = UUID(sys.argv[1]), UUID(sys.argv[2]), sys.argv[3]
with connect() as db:
    if db.execute('select 1 from noah.projects where id=%s', (project,)).fetchone():
        raise RuntimeError('Project ID already exists')
    if not db.execute('select 1 from noah.users where id=%s', (user,)).fetchone():
        raise RuntimeError('Existing user missing')
    db.execute('insert into noah.projects(id,label) values (%s,%s)', (project,label))
    db.execute('insert into noah.project_memberships(project_id,user_id,can_write) values (%s,%s,false)', (project,user))
print('Synthetic project and read-only membership created')
'@
$SetupCode | & $Python - $ProjectId $UserId $ProjectLabel
if ($LASTEXITCODE -ne 0) { throw 'Synthetic DB setup failed; stop' }
$SetupJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0) { throw 'Post-setup snapshot failed' }
$Setup = $SetupJson | ConvertFrom-Json
Assert-Delta $Setup @{ projects=1; project_memberships=1 }
Write-Output "Synthetic files ready; byte lengths: $AnimalBytes, $ColorBytes"
```

If any setup step fails, stop with the current state intact and inspect it
before deciding how to remove test-owned artifacts. Do not run the normal
cleanup block without successful validation.

## 3. Window B — start the current server; window A — one M10 request

In a **new** PowerShell window B, start the working-tree M10 code:

```powershell
Set-Location -LiteralPath 'C:\Development\project-noah'
.\.venv\Scripts\python.exe -m noah serve
```

Back in window A, confirm exactly one loopback 8080 listener, then send the
successful request **once**. UTF-8 bytes and the charset are both explicit.
If the model selects fewer than two documents or the request fails, stop;
do not try the same success request again to manufacture Evidence.

```powershell
$Listener = @(netstat -ano -p tcp | Where-Object { $_ -match '^\s*TCP\s+127\.0\.0\.1:8080\s+\S+\s+LISTENING\s+\d+' })
if ($Listener.Count -ne 1) { throw 'Exactly one local NOAH listener required' }
$Question = 'NOAH의 M10 테스트 동물과 테스트 색상을 각각 알려줘.'
$BodyJson = @{ question = $Question } | ConvertTo-Json -Compress
$BodyBytes = [System.Text.Encoding]::UTF8.GetBytes($BodyJson)
$Headers = @{ Authorization = "Bearer $Token" }
$Uri = "http://127.0.0.1:8080/projects/$ProjectId/documents/answer-auto"
$Web = Invoke-WebRequest -UseBasicParsing -Method Post -Uri $Uri -Headers $Headers -ContentType 'application/json; charset=utf-8' -Body $BodyBytes
$Result = $Web.Content | ConvertFrom-Json
if ($Web.StatusCode -ne 200 -or $Result.status -ne 'succeeded' -or
    $Result.capability -ne 'project.documents.answer.auto' -or
    $Result.grounded -ne $true -or
    @('supported','partial') -notcontains $Result.outcome -or
    -not $Result.task_id -or -not $Result.execution_id) { throw 'M10 success contract mismatch' }
$Selected = @($Result.selected_document_names)
$Sources = @($Result.sources)
$Quotes = @($Result.evidence)
if ($Selected.Count -ne 2 -or $Sources.Count -ne 2 -or
    $Quotes.Count -lt 2 -or $Quotes.Count -gt 3) { throw 'M10 selection/source/quote count mismatch' }
if ((@($Selected | Sort-Object) -join '|') -ne
    ((@('m10-test-animal.md','m10-test-color.md') | Sort-Object) -join '|')) {
    throw 'Wrong selected documents'
}
for ($i = 0; $i -lt 2; $i++) {
    if ($Sources[$i].source_id -ne "D$($i+1)" -or
        $Sources[$i].document_name -ne $Selected[$i]) { throw 'D1/D2 order mismatch' }
}
$AnimalSource = @($Sources | Where-Object { $_.document_name -eq 'm10-test-animal.md' })[0]
$ColorSource = @($Sources | Where-Object { $_.document_name -eq 'm10-test-color.md' })[0]
if (@($Quotes | Where-Object { $_.source_id -eq $AnimalSource.source_id -and $_.quote.Contains('수달') }).Count -eq 0 -or
    @($Quotes | Where-Object { $_.source_id -eq $ColorSource.source_id -and $_.quote.Contains('파란색') }).Count -eq 0) {
    throw 'Animal/color provenance missing'
}
if ($Web.Content.Contains($Root) -or $Web.Content.Contains($Token)) { throw 'Sensitive response content' }
Write-Output 'Single M10 HTTP 200 response has two source-aware grounded quotes'
```

Do not compare the whole natural-language `answer` string to a fixed phrase.
The next block checks exact quotes and Unicode positions against the actual
file bytes. With `partial`, the two exact source quotes still satisfy the
machine-verifiable grounded execution contract. The operator must inspect
whether the D1 animal quote and D2 color quote address the two parts of the
question; preserve `partial` as returned and do not relabel it `supported`.
`no_document_selected`, `insufficient`, `conflicting`, `out_of_scope`, timeout,
or malformed output are distinct outcomes and do not satisfy this particular
two-source success check. Stop and report them without resending the request.

## 4. Window A — source-aware DB Evidence and exact delta

This verifier contains no non-ASCII Python source literals. It reads the
actual UTF-8 files and the actual migration 007 columns. The response JSON
is passed as base64 of UTF-8 bytes; the existing token is supplied only to
this child process through a temporary environment variable, then removed.
It prints no token, password, private row, document body, or OS path.

```powershell
$Response64 = [Convert]::ToBase64String([System.Text.Encoding]::UTF8.GetBytes($Web.Content))
$VerifyCode = @'
import base64, hashlib, json, os, sys
from pathlib import Path
from noah.db import connect, local_settings
from noah.document_auto import candidate_hash

project, task_id, execution_id = sys.argv[1:4]
root, root_id, response64, user_id = sys.argv[4:8]
response = json.loads(base64.b64decode(response64).decode('utf-8'))
token = os.environ.get('NOAH_M10_VALIDATION_TOKEN', '')
password = local_settings()['POSTGRES_PASSWORD']
def require(condition, label):
    if not condition: raise RuntimeError(label)
names = ['m10-test-animal.md', 'm10-test-color.md']
raw = {name: (Path(root) / name).read_bytes() for name in names}
text = {name: raw[name].decode('utf-8', errors='strict') for name in names}
with connect() as db:
    task = db.execute('select * from noah.tasks where id=%s', (task_id,)).fetchone()
    execution = db.execute('select * from noah.execution_records where id=%s', (execution_id,)).fetchone()
    parent = db.execute('select * from noah.auto_document_answer_evidence where execution_id=%s',
                        (execution_id,)).fetchone()
    sources = db.execute('select * from noah.auto_document_source_evidence where execution_id=%s order by source_ordinal',
                         (execution_id,)).fetchall()
    quotes = db.execute('select * from noah.auto_document_quote_evidence where execution_id=%s order by quote_ordinal',
                        (execution_id,)).fetchall()
    require(task is not None and execution is not None and parent is not None, 'Missing M10 linked row')
    require(str(task['id']) == task_id and str(task['actor_user_id']) == user_id and
            task['status'] == 'completed' and task['verification_status'] == 'passed', 'Task mismatch')
    require(str(execution['task_id']) == task_id and str(execution['actor_user_id']) == user_id and
            execution['capability'] == 'project.documents.answer.auto' and
            execution['status'] == 'succeeded' and execution['verified_at'] is not None, 'Execution mismatch')
    require(db.execute('select count(*) as n from noah.execution_records where task_id=%s',
                       (task_id,)).fetchone()['n'] == 1, 'Extra execution for Task')
    require(str(parent['project_id']) == project and parent['root_id'] == root_id and
            parent['candidates_observed_at'] is not None and parent['candidate_names'] == names and
            parent['candidate_count'] == 2 and parent['truncated'] is False, 'Candidate observation mismatch')
    digest = candidate_hash(project, root_id, names)
    require(parent['candidate_sha256'].strip() == digest and
            response['candidate_observation']['sha256'] == digest, 'Candidate hash mismatch')
    selected = response['selected_document_names']
    require(response['outcome'] in ('supported','partial'), 'Answer outcome mismatch')
    require(parent['selection_model_called'] is True and parent['selection_outcome'] == 'selected' and
            parent['selected_count'] == 2 and parent['raw_candidate_names'] == selected and
            parent['selected_names'] == selected and parent['answer_outcome'] == response['outcome'],
            'Selection Evidence mismatch')
    require(len(sources) == 2 and len(quotes) == len(response['evidence']) and
            2 <= len(quotes) <= 3, 'Source/quote count mismatch')
    by_id = {}
    for ordinal, source in enumerate(sources, 1):
        source_id, name = 'D' + str(ordinal), selected[ordinal - 1]
        require(source['source_id'] == source_id and source['source_ordinal'] == ordinal and
                source['document_name'] == name and source['observed_at'] is not None and
                source['byte_length'] == len(raw[name]) and
                source['content_sha256'].strip() == hashlib.sha256(raw[name]).hexdigest() and
                source['content_encoding'] == 'utf-8' and source['bom_present'] is False,
                'Selected source observation mismatch')
        api_source = response['sources'][ordinal - 1]
        require(api_source['source_id'] == source_id and api_source['document_name'] == name and
                api_source['content_sha256'] == source['content_sha256'].strip(),
                'API source mismatch')
        by_id[source_id] = name
    observed_quote_sources = set()
    for ordinal, quote in enumerate(quotes, 1):
        source_id = quote['source_id']
        require(source_id in by_id and quote['quote_ordinal'] == ordinal, 'Quote source/order mismatch')
        excerpt = quote['quote']
        position = text[by_id[source_id]].find(excerpt)
        require(position >= 0 and quote['start_index'] == position and
                quote['end_index'] == position + len(excerpt) and 1 <= len(excerpt) <= 240,
                'Exact Unicode quote/position mismatch')
        api_quote = response['evidence'][ordinal - 1]
        require(api_quote['source_id'] == source_id and api_quote['quote'] == excerpt and
                api_quote['start'] == position and api_quote['end'] == position + len(excerpt) and
                api_quote['content_sha256'] == hashlib.sha256(raw[by_id[source_id]]).hexdigest(),
                'API quote mismatch')
        observed_quote_sources.add(source_id)
    require(observed_quote_sources == {'D1','D2'}, 'Both source quotes required')
    for table in ('document_tool_evidence','document_read_evidence',
                  'document_answer_evidence','selected_document_answer_evidence',
                  'selected_document_source_evidence','selected_document_quote_evidence'):
        require(db.execute('select count(*) as n from noah.' + table +
                           ' where execution_id=%s', (execution_id,)).fetchone()['n'] == 0,
                'Legacy Evidence attached to M10')
    persisted = json.dumps({'parent':parent,'sources':sources,'quotes':quotes},
                           default=str, ensure_ascii=False)
    exposure = persisted + json.dumps(response, ensure_ascii=False)
    require(all(body not in persisted for body in text.values()), 'Whole document persisted')
    require(root not in exposure and token and token not in exposure and
            password and password not in exposure, 'Path or credential exposure')
print('M10 Task/Execution/candidate/source/quote Evidence verified')
'@
$env:NOAH_M10_VALIDATION_TOKEN = $Token
try {
    $VerifyCode | & $Python - $ProjectId $Result.task_id $Result.execution_id $Root $RootId $Response64 $UserId
    if ($LASTEXITCODE -ne 0) { throw 'M10 Evidence verification failed' }
} finally {
    Remove-Item Env:NOAH_M10_VALIDATION_TOKEN -ErrorAction SilentlyContinue
}
$SuccessJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0) { throw 'Post-success snapshot failed' }
$Success = $SuccessJson | ConvertFrom-Json
Assert-Delta $Success @{ projects=1; project_memberships=1; tasks=1;
    execution_records=1; auto_document_answer_evidence=1;
    auto_document_source_evidence=2; auto_document_quote_evidence=$Quotes.Count }
Write-Output 'Success delta: project +1, membership +1, Task +1, Execution +1, M10 parent +1, source +2, quote +2..3; existing rows unchanged'
```

The expected quote delta is the actual verified evidence count (2 or 3),
because the model may return up to three exact excerpts. No manual malformed
selection, three-name, duplicate, timeout, or scope-limit request is needed:
the automated M10 tests already cover these cases. Avoid an extra negative
request during this one-success-run validation.

## 5. Stop the server, verify unchanged success state, then clean up

Only after every check above passes, stop window B with `Ctrl+C`. In window A,
require the 8080 listener to be absent. Confirm the success snapshot has not
changed and the synthetic mapping/files still match their original hashes.
Any mismatch is a stop; do not enter the deletion transaction.

```powershell
if (@(netstat -ano -p tcp | Where-Object { $_ -match '^\s*TCP\s+\S+:8080\s+\S+\s+LISTENING\s+\d+' }).Count -ne 0) {
    throw 'NOAH server still listening; stop window B first'
}
$BeforeCleanupJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0 -or $BeforeCleanupJson -ne $SuccessJson) {
    throw 'Success DB snapshot changed; stop cleanup'
}
if (-not (Test-Path -LiteralPath $Mapping) -or
    (Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash) {
    throw 'Synthetic mapping changed'
}
$MapObject = Get-Content -LiteralPath $Mapping -Raw -Encoding UTF8 | ConvertFrom-Json
$MapEntries = @($MapObject.projects.PSObject.Properties)
if ($MapEntries.Count -ne 1 -or $MapEntries[0].Name -ne $ProjectId -or
    $MapEntries[0].Value.root_id -ne $RootId -or
    $MapEntries[0].Value.document_root -ne $Root) { throw 'Mapping is not this run only' }
if (-not (Test-Path -LiteralPath $AnimalPath) -or -not (Test-Path -LiteralPath $ColorPath) -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Synthetic file changed'
}
$RootNames = @(Get-ChildItem -LiteralPath $Root -Force | Select-Object -ExpandProperty Name)
if ($RootNames.Count -ne 2 -or
    ((@($RootNames | Sort-Object) -join '|') -ne
     ((@('m10-test-animal.md','m10-test-color.md') | Sort-Object) -join '|'))) {
    throw 'Unexpected root entry; stop cleanup'
}
```

The following Python transaction verifies exact ownership and linkage first.
If a check or DELETE fails, the whole transaction rolls back. It deletes
**only** this execution's M10 quotes, sources, parent, Execution, Task,
membership, and project, in foreign-key order. It does not touch users,
tokens, memories, old Tasks/Executions, M4 mappings, or the Docker volume.
The source and quote tables have no `project_id` column; cleanup keys them
by `execution_id`.

```powershell
$CleanupCode = @'
import sys
from uuid import UUID
from noah.db import connect
project, user, task, execution = (UUID(value) for value in sys.argv[1:5])
label, expected_quotes = sys.argv[5], int(sys.argv[6])
def require(condition, label):
    if not condition: raise RuntimeError(label)
with connect() as db:
    p = db.execute('select * from noah.projects where id=%s', (project,)).fetchone()
    m = db.execute('select * from noah.project_memberships where project_id=%s', (project,)).fetchall()
    t = db.execute('select * from noah.tasks where id=%s', (task,)).fetchone()
    e = db.execute('select * from noah.execution_records where id=%s', (execution,)).fetchone()
    a = db.execute('select * from noah.auto_document_answer_evidence where execution_id=%s', (execution,)).fetchone()
    s = db.execute('select * from noah.auto_document_source_evidence where execution_id=%s', (execution,)).fetchall()
    q = db.execute('select * from noah.auto_document_quote_evidence where execution_id=%s', (execution,)).fetchall()
    require(p is not None and p['label'] == label and len(m) == 1 and
            m[0]['user_id'] == user and m[0]['can_write'] is False, 'Project/membership mismatch')
    require(t is not None and t['actor_user_id'] == user and t['status'] == 'completed' and
            t['verification_status'] == 'passed', 'Task mismatch')
    require(e is not None and e['task_id'] == task and e['actor_user_id'] == user and
            e['capability'] == 'project.documents.answer.auto' and e['status'] == 'succeeded',
            'Execution mismatch')
    require(a is not None and a['project_id'] == project and a['selected_count'] == 2 and
            len(s) == 2 and len(q) == expected_quotes, 'M10 Evidence mismatch')
    require(db.execute('select count(*) as n from noah.memories where project_id=%s',
                       (project,)).fetchone()['n'] == 0, 'Project has memory')
    require(db.execute('select count(*) as n from noah.execution_records where task_id=%s',
                       (task,)).fetchone()['n'] == 1, 'Task has extra Execution')
    def delete_exact(sql, params, expected):
        changed = db.execute(sql, params).rowcount
        require(changed == expected, 'Unexpected DELETE count')
    delete_exact('delete from noah.auto_document_quote_evidence where execution_id=%s', (execution,), expected_quotes)
    delete_exact('delete from noah.auto_document_source_evidence where execution_id=%s', (execution,), 2)
    delete_exact('delete from noah.auto_document_answer_evidence where execution_id=%s and project_id=%s',
                 (execution,project), 1)
    delete_exact('delete from noah.execution_records where id=%s and task_id=%s', (execution,task), 1)
    delete_exact('delete from noah.tasks where id=%s and actor_user_id=%s', (task,user), 1)
    delete_exact('delete from noah.project_memberships where project_id=%s and user_id=%s and can_write=false',
                 (project,user), 1)
    delete_exact('delete from noah.projects where id=%s and label=%s', (project,label), 1)
print('Only this run synthetic M10 database rows removed')
'@
$CleanupCode | & $Python - $ProjectId $UserId $Result.task_id $Result.execution_id $ProjectLabel $Quotes.Count
if ($LASTEXITCODE -ne 0) { throw 'DB cleanup failed or rolled back; stop' }
$AfterDbCleanupJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0 -or $AfterDbCleanupJson -ne $BaselineJson) {
    throw 'DB did not return to exact baseline; preserve local artifacts and stop'
}
Write-Output 'DB baseline row counts and private fingerprints restored'
```

Only after the DB baseline matches, remove the mapping and **only the two
known files**. No recursive delete is used; removing the root requires it
to be empty. The root was created under the repository's Git-ignored `.noah`
directory and must still be the same run-specific path.

```powershell
$ExpectedRoot = Join-Path $Repo ".noah\m10-manual-$RunId"
if ([System.IO.Path]::GetFullPath($Root) -ne [System.IO.Path]::GetFullPath($ExpectedRoot)) {
    throw 'Root path changed; stop'
}
if ((Get-FileHash -LiteralPath $Mapping -Algorithm SHA256).Hash.ToLowerInvariant() -ne $MappingHash -or
    (Get-FileHash -LiteralPath $AnimalPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $AnimalHash -or
    (Get-FileHash -LiteralPath $ColorPath -Algorithm SHA256).Hash.ToLowerInvariant() -ne $ColorHash) {
    throw 'Artifact changed after DB cleanup; stop'
}
Remove-Item -LiteralPath $Mapping
Remove-Item -LiteralPath $AnimalPath
Remove-Item -LiteralPath $ColorPath
if (@(Get-ChildItem -LiteralPath $Root -Force).Count -ne 0) { throw 'Root not empty; stop' }
Remove-Item -LiteralPath $Root
$FinalJson = $SnapshotCode | & $Python -
if ($LASTEXITCODE -ne 0 -or $FinalJson -ne $BaselineJson -or
    (Test-Path -LiteralPath $Mapping) -or (Test-Path -LiteralPath $Root)) {
    throw 'Final restoration check failed'
}
Write-Output 'DB restored; local mapping and synthetic M10 document root removed'
```

Do not run `docker compose down -v`, `docker volume prune`, database reset,
or any command that deletes the existing PostgreSQL volume. If the one M10
request does not meet the two-source criterion, retain the state and report
the result before planning an exact, separately reviewed cleanup.
