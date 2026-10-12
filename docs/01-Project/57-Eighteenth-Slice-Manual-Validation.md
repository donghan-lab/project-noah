# M18 Isolated Operator HTTP Validation

> Status: **FIFTH ISOLATED ACTUAL OLLAMA HTTP E2E PASSED on 2026-10-12;
> exact synthetic cleanup and isolated baseline restoration COMPLETE**.
> Earlier four STOP records and their cleanup remain historical below and in
> `56`; they are not combined with the fifth successful run. Personal DB
> deployment was not performed.
> Contract: `55-Eighteenth-Vertical-Slice.md`.
> Source baseline: `main@f83ae156aa70103d5e7d404469f4be0c42c7d299`, plus the
> reviewed uncommitted M18 implementation. Automated evidence is in `56`.
> This document is a procedure, not execution approval or a successful result.

## 0. Scope, windows, and STOP rules

Use **Windows PowerShell 5.1**, a new A window for private runtime state, B
for the owned NOAH server, and C for the owned dedicated Ollama. Do not enable
transcription, echo secret variables, print complete responses/configuration,
save DB fingerprints to disk, or copy a personal DB/configuration/mapping.

This is an **isolated-only** run. Do not inspect, connect to, back up, migrate,
or delete any existing PostgreSQL container, database, or named volume. Do not
reuse any old temporary directory. Never run `python -m noah init` from the
source repository. `serve` does **not** initialize migrations; Section 4
explicitly applies 001–014 only to the owned tmpfs database.

Planned business HTTP requests: **two POSTs and two GETs**:

1. Register exactly once (201); prove ready and Execution zero.
2. Restart, then GET that same ready Task (200).
3. Run exactly once (200), with grounded `supported` or `partial`.
4. Restart again, then GET the same historical result (200).

The dedicated Ollama `/api/tags` GET is an environment check, not an answer
model call. There is no Router or Session request, replay, second run, or
failure injection. A failed/uncertain response, unexpected model result,
commit uncertainty, wrong connection/owner, changed source, or DB mismatch
means **STOP immediately and preserve state**. Do not resend a POST, change
the question, reset a once-only flag, automatically clean up an uncertain
state, or classify an unknown outcome as failed. A verifier defect permits
only read-only rechecking of captured responses after separate review.

Every block requires all earlier gates to have passed. Expected output is a
safe confirmation line, with no secret/fingerprint. Any exception or nonzero
exit is a STOP; there is no automatic retry of mutations or cleanup.

## 1. A — fresh Git, listener, executable, and owned root gate

This block is read-only until the fresh restricted temporary root is created.
No previous variables or run flags may be reused.

```powershell
$ErrorActionPreference = 'Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) {
 throw 'Use Windows PowerShell 5.1 for this procedure'
}
$Repo = 'C:\Development\project-noah'
$BaselineCommit = 'f83ae156aa70103d5e7d404469f4be0c42c7d299'
$ExpectedPaths = @(
 'database/014_document_question_tasks.sql',
 'docs/01-Project/55-Eighteenth-Vertical-Slice.md',
 'docs/01-Project/56-Eighteenth-Slice-Validation.md',
 'docs/01-Project/57-Eighteenth-Slice-Manual-Validation.md',
 'noah/__main__.py','noah/db.py','noah/document_task.py','tests/test_document_task.py'
)
$GitBefore = @(git -C $Repo -c core.quotepath=false status --short)
if ($LASTEXITCODE -ne 0 -or
 (git -C $Repo branch --show-current) -cne 'main' -or
 (git -C $Repo rev-parse HEAD) -cne $BaselineCommit -or
 (git -C $Repo rev-parse origin/main) -cne $BaselineCommit -or
 @(git -C $Repo diff --cached --name-only).Count -ne 0 -or
 @(Compare-Object -ReferenceObject ($ExpectedPaths | Sort-Object) -DifferenceObject (@($GitBefore | ForEach-Object { $_.Substring(3) }) | Sort-Object)).Count -ne 0) {
 throw 'Git baseline/scope differs; STOP for review'
}
git -C $Repo diff --check
if ($LASTEXITCODE -ne 0) { throw 'Diff check failed' }
$Python = Join-Path $Repo '.venv\Scripts\python.exe'
$OllamaExe = (Get-Command ollama.exe -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python missing' }
$RunStart = Get-Date
$OrdinaryBefore = @(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 11434 } |
 ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
$DbPort = 57838
foreach ($Port in @(8080,11435,$DbPort)) {
 if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
   Where-Object { $_.LocalPort -eq $Port }).Count -ne 0) {
  throw 'Required isolated port occupied; do not stop its owner'
 }
}
$ImageId = [string](docker image inspect postgres:17 --format '{{.Id}}')
if ($LASTEXITCODE -ne 0 -or -not $ImageId.StartsWith('sha256:')) {
 throw 'Local PostgreSQL 17 image missing; no automatic pull'
}
$Run = 'noah-m18-e2e-' + [Guid]::NewGuid().ToString('N')
$RunRoot = Join-Path $env:TEMP $Run
if (Test-Path -LiteralPath $RunRoot) { throw 'Fresh root already exists' }
[void](New-Item -ItemType Directory -Path $RunRoot)
$UserSid = [Security.Principal.WindowsIdentity]::GetCurrent().User.Value
$Grant = '*' + $UserSid + ':(OI)(CI)F'
icacls $RunRoot /inheritance:r /grant:r $Grant | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Restricted ACL not established' }
$Source = Join-Path $RunRoot 'source'
$Container = $Run
$DbName = 'noah_m18_e2e'
$DbUser = 'm18_synthetic'
$Utf8 = New-Object System.Text.UTF8Encoding($false,$true)
$FixtureAttempted=$false; $RegisterSent=$false; $RunSent=$false
$CleanupAttempted=$false; $CleanupGatePassed=$false
Write-Output 'Fresh Git/listener/owned-root gate passed'
```

Expected: one confirmation. This runbook's eight-path expectation is the
implementation's seven paths plus this document. A later approved commit or
documentation change requires a reviewed gate update; do not silently alter
the baseline to make it pass. Review applicable `AGENTS.md` before execution.

## 2. A — allowlisted copy, synthetic settings, tmpfs PostgreSQL

Copy only public implementation modules and migrations, never `.git`, tests,
documents, `.noah`, existing `compose/.env`, or an existing mapping. Synthetic
credentials remain private in A and the access-restricted disposable files.

```powershell
foreach ($Directory in @('noah','database','compose','config')) {
 [void](New-Item -ItemType Directory -Path (Join-Path $Source $Directory))
}
$CodeHashes = @{}
foreach ($Directory in @('noah','database')) {
 $Filter = if ($Directory -eq 'noah') { '*.py' } else { '*.sql' }
 foreach ($File in @(Get-ChildItem -LiteralPath (Join-Path $Repo $Directory) -Filter $Filter -File)) {
  if (($File.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
   throw 'Source link found; STOP'
  }
  $Relative = $Directory + '/' + $File.Name
  Copy-Item -LiteralPath $File.FullName -Destination (Join-Path $Source $Relative)
  $CodeHashes[$Relative] = (Get-FileHash -LiteralPath $File.FullName).Hash.ToLowerInvariant()
 }
}
$Migrations = @(Get-ChildItem -LiteralPath (Join-Path $Source 'database') -Filter '*.sql' -File |
 Sort-Object Name)
if ($Migrations.Count -ne 14 -or
 ($Migrations[-1].Name -cne '014_document_question_tasks.sql')) { throw 'Migration set differs' }
$RandomBytes = New-Object byte[] 32
$Rng = [Security.Cryptography.RandomNumberGenerator]::Create()
$Rng.GetBytes($RandomBytes); $Rng.Dispose()
$DbPassword = [Convert]::ToBase64String($RandomBytes)
$SettingsPath = Join-Path $Source 'compose\.env'
[IO.File]::WriteAllText($SettingsPath,
 "POSTGRES_DB=$DbName`nPOSTGRES_USER=$DbUser`nPOSTGRES_PASSWORD=$DbPassword`nPOSTGRES_PORT=$DbPort`n",$Utf8)
$SettingsHash = (Get-FileHash -LiteralPath $SettingsPath).Hash
$Mapping = Join-Path $Source 'config\project_documents.local.json'
[IO.File]::WriteAllText($Mapping,'{"projects":{}}',$Utf8)
$env:POSTGRES_PASSWORD = $DbPassword
try {
 $ContainerId = [string](docker run --pull never --detach --name $Container `
  --label "noah.test.run=$Run" --tmpfs '/var/lib/postgresql/data:rw,size=1g' `
  --publish "127.0.0.1:${DbPort}:5432" `
  --env "POSTGRES_DB=$DbName" --env "POSTGRES_USER=$DbUser" `
  --env POSTGRES_PASSWORD $ImageId)
 if ($LASTEXITCODE -ne 0 -or $ContainerId -notmatch '^[0-9a-f]{64}$') {
  throw 'Container creation unconfirmed; do not retry'
 }
} finally { Remove-Item Env:POSTGRES_PASSWORD -ErrorAction SilentlyContinue }
$Manifest = @{
 run=$Run;source=$Source;container=$Container;container_id=$ContainerId;
 image=$ImageId;port=$DbPort;db=$DbName;user=$DbUser;code=$CodeHashes;
 doc_name='m18-synthetic.md';root_id='m18-synthetic-root';python=$Python
}
$ManifestPath = Join-Path $RunRoot 'manifest.json'
[IO.File]::WriteAllText($ManifestPath,($Manifest | ConvertTo-Json -Depth 5 -Compress),$Utf8)
$ManifestHash = (Get-FileHash -LiteralPath $ManifestPath).Hash
function Assert-M18ContainerIdentity($Observed) {
 if ($null -eq $Observed -or $Observed.Id -cne $ContainerId -or
  $Observed.Name -cne ('/' + $Container) -or $Observed.Image -cne $ImageId -or
  $Observed.Config.Labels.'noah.test.run' -cne $Run -or
  $Observed.State.Running -ne $true) { throw 'Container identity differs; STOP' }
}
function Assert-M18ContainerObservation($Observed, [string[]]$MountInfo) {
 Assert-M18ContainerIdentity $Observed
 $DataPath='/var/lib/postgresql/data'
 $Tmpfs=@($Observed.HostConfig.Tmpfs.PSObject.Properties)
 $Mounts=@($Observed.Mounts)
 $Ports=@($Observed.NetworkSettings.Ports.'5432/tcp')
 $PortKeys=@($Observed.NetworkSettings.Ports.PSObject.Properties)
 $PgData=@($Observed.Config.Env | Where-Object { $_ -clike 'PGDATA=*' })
 if ($Tmpfs.Count -ne 1 -or $Tmpfs[0].Name -cne $DataPath -or
  $Tmpfs[0].Value -cne 'rw,size=1g' -or
  $PgData.Count -ne 1 -or $PgData[0] -cne ('PGDATA=' + $DataPath) -or
  @($Observed.HostConfig.Binds | Where-Object { $null -ne $_ }).Count -ne 0 -or
  @($Observed.HostConfig.Mounts | Where-Object { $null -ne $_ }).Count -ne 0 -or
  $Observed.HostConfig.NetworkMode -cne 'bridge' -or
  @($Mounts | Where-Object { $_.Type -cne 'tmpfs' -or $_.Destination -cne $DataPath }).Count -ne 0 -or
  $Mounts.Count -gt 1 -or $PortKeys.Count -ne 1 -or
  $PortKeys[0].Name -cne '5432/tcp' -or $Ports.Count -ne 1 -or
  $Ports[0].HostIp -cne '127.0.0.1' -or
  $Ports[0].HostPort -cne [string]$DbPort) { throw 'Container/storage/port differs; STOP' }
 # --tmpfs can legitimately be absent from Docker's Mounts array.
 # Confirm the exact data directory's actual filesystem, not inspect text alone.
 $DataMounts=@($MountInfo | Where-Object { ($_ -split ' ')[4] -ceq $DataPath })
 if ($DataMounts.Count -ne 1) { throw 'Actual data mount missing/ambiguous; STOP' }
 $Parts=$DataMounts[0] -split ' - '
 $Before=$Parts[0] -split ' '
 if ($Parts.Count -ne 2 -or ($Parts[1] -split ' ')[0] -cne 'tmpfs' -or
  $Before[3] -cne '/' -or @($Before[5] -split ',') -cnotcontains 'rw') {
  throw 'Actual PostgreSQL data filesystem differs; STOP'
 }
}
function Assert-M18Container {
 $Raw=@(docker inspect $Container)
 if ($LASTEXITCODE -ne 0) { throw 'Container identity unavailable' }
 # PS 5.1 retains the JSON root array; do not wrap the pipeline in @(...) again.
 $Parsed=ConvertFrom-Json -InputObject ($Raw -join "`n")
 if (@($Parsed).Count -ne 1) { throw 'Container identity unavailable' }
 $Observed=$Parsed[0]
 Assert-M18ContainerIdentity $Observed  # Before any exec: only the owned ID is allowed.
 $MountInfo=@(docker exec $ContainerId cat /proc/self/mountinfo)
 if ($LASTEXITCODE -ne 0) { throw 'Actual mount inspection failed; STOP' }
 Assert-M18ContainerObservation $Observed $MountInfo
}
Assert-M18Container
$Ready=$false
for ($Attempt=0; $Attempt -lt 30; $Attempt++) {
 docker exec $Container pg_isready -U $DbUser -d $DbName | Out-Null
 if ($LASTEXITCODE -eq 0) { $Ready=$true; break }
 Start-Sleep -Milliseconds 500
}
if (-not $Ready) { throw 'Isolated PostgreSQL not ready; STOP' }
Set-Location -LiteralPath $Source
Write-Output 'Owned PostgreSQL tmpfs and synthetic source/configuration prepared'
```

Expected: one confirmation. Readiness polling is not a repeated mutation or
HTTP POST. `HostConfig.Tmpfs`, PGDATA, and `/proc/self/mountinfo` must agree;
`Mounts` may be empty, but any volume/bind or unexpected mount is a STOP.
Only the owned container is inspected/executed; no existing container/volume
is queried. Do not print raw inspect/configuration: it contains the synthetic password.

## 3. A — pinned helper and server entry point

The following helper belongs **only inside the disposable copy**. It is not
an application change. All invocations use its absolute path with Python
`-I -B`; `-I` ignores inherited `PYTHONPATH` and the source-repository cwd.
Nevertheless, a changed cwd is rejected, not silently corrected. Before any
DB connection it checks copy hashes, module origins, synthetic configuration,
owned Docker identity, actual loopback destination, database/user/version.
After source removal it cannot import or connect through the original repo.

The three counters record only operation labels, never arguments, content,
model output, credentials, or IDs. They wrap and forward the real primitives
unchanged, letting this run distinguish zero calls from a claim of zero calls.

```powershell
$Helper = Join-Path $Source 'operate_m18.py'
$HelperCode = @'
import hashlib, importlib.util, json, os, re, secrets, stat, subprocess, sys
from pathlib import Path
from uuid import UUID, uuid4

sys.excepthook = lambda *_: print('STOP: isolated helper failed; preserve state', file=sys.stderr)
SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parent
assert SOURCE.name == 'source' and ROOT.name.startswith('noah-m18-e2e-')
M = json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
COUNTERS = ROOT/'operation-counts.txt'

def source_gate():
    assert Path.cwd().resolve() == SOURCE == Path(M['source']).resolve()
    assert (SOURCE/'noah/db.py').is_file() and not (SOURCE/'.git').exists()
    for p in (SOURCE, *SOURCE.parents):
        s = p.lstat()
        assert not stat.S_ISLNK(s.st_mode) and not (getattr(s,'st_file_attributes',0) & 0x400)
    for name, digest in M['code'].items():
        p = SOURCE/name
        assert p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest() == digest
    for name, module in list(sys.modules.items()):
        if name == 'noah' or name.startswith('noah.'):
            assert Path(module.__file__).resolve().is_relative_to(SOURCE)

def container_gate():
    raw = subprocess.run(['docker','inspect',M['container']], check=True,
                         capture_output=True, timeout=5).stdout
    items = json.loads(raw)
    assert len(items) == 1
    c = items[0]
    assert c['Id'] == M['container_id'] and c['Image'] == M['image']
    assert c['Name'] == '/' + M['container']
    assert c['Config']['Labels']['noah.test.run'] == M['run'] and c['State']['Running'] is True
    data_path = '/var/lib/postgresql/data'
    h = c['HostConfig']
    assert h.get('Tmpfs') == {data_path:'rw,size=1g'}
    assert not h.get('Binds') and not h.get('Mounts') and h['NetworkMode'] == 'bridge'
    assert [e for e in c['Config']['Env'] if e.startswith('PGDATA=')] == ['PGDATA='+data_path]
    mounts = c['Mounts']
    assert len(mounts) <= 1 and all(x['Type']=='tmpfs' and x['Destination']==data_path for x in mounts)
    assert c['NetworkSettings']['Ports'] == {
        '5432/tcp':[{'HostIp':'127.0.0.1','HostPort':str(M['port'])}]}
    # Identity is confirmed before executing only inside this owned container.
    info = subprocess.run(['docker','exec',M['container_id'],'cat','/proc/self/mountinfo'],
                          check=True,capture_output=True,timeout=5).stdout.decode('utf-8','strict')
    lines = [line for line in info.splitlines() if line.split()[4] == data_path]
    assert len(lines) == 1
    before, after = lines[0].split(' - ')
    assert before.split()[3]=='/' and 'rw' in before.split()[5].split(',')
    assert after.split()[0] == 'tmpfs'

source_gate()
sys.path.insert(0,str(SOURCE))
assert Path(importlib.util.find_spec('noah').origin).resolve().parent == SOURCE/'noah'
from noah import db
assert db.ROOT.resolve() == SOURCE
native_connect = db.connect

def connect():
    source_gate(); container_gate()
    assert (db.ROOT/'compose/.env').resolve() == SOURCE/'compose/.env'
    settings = db.local_settings()
    assert (settings['POSTGRES_DB'],settings['POSTGRES_USER'],settings['POSTGRES_PORT']) == (
        M['db'],M['user'],str(M['port']))
    c = native_connect()
    try:
        assert (c.info.host,c.info.port,c.info.dbname) == ('127.0.0.1',M['port'],M['db'])
        c.autocommit = True
        row = c.execute("SELECT current_database() AS d,current_user AS u,current_setting('server_version_num') AS v").fetchone()
        assert row['d']==M['db'] and row['u']==M['user'] and 170000 <= int(row['v']) < 180000
        c.execute("SET lock_timeout='3s'")
        c.execute("SET statement_timeout='10s'")
        c.autocommit = False
        return c
    except BaseException:
        c.close()
        raise

db.connect = connect  # BEFORE importing modules whose defaults capture connect.
from noah import document_tool, document_read, ollama
assert (ollama.HOST,ollama.PORT,ollama.MODEL)==('127.0.0.1',11435,'gemma4:12b-it-qat')

def counted(name, original):
    def forward(*args, **kwargs):
        source_gate()
        with COUNTERS.open('a',encoding='ascii') as stream:
            stream.write(name+'\n')
        return original(*args, **kwargs)
    return forward

document_tool.operator_root = counted('mapping',document_tool.operator_root)
document_read.execute_document_read = counted('safe_read',document_read.execute_document_read)
ollama.OllamaClient.complete = counted('model',ollama.OllamaClient.complete)

TABLES = set('users api_tokens projects project_memberships tasks memories execution_records memory_write_requests document_tool_evidence document_read_evidence document_answer_evidence selected_document_answer_evidence selected_document_source_evidence selected_document_quote_evidence auto_document_answer_evidence auto_document_source_evidence auto_document_quote_evidence routing_audit sessions document_followup_evidence document_question_tasks'.split())

def counts():
    values = COUNTERS.read_text(encoding='ascii').splitlines() if COUNTERS.exists() else []
    assert set(values) <= {'mapping','safe_read','model'}
    return {k:values.count(k) for k in ('mapping','safe_read','model')}

def snapshot(c):
    tables = {r['table_name'] for r in c.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='noah'").fetchall()}
    assert tables == TABLES
    result = {}
    for name in sorted(tables):
        rows = c.execute('SELECT row_to_json(t) AS r FROM noah."'+name+'" t').fetchall()
        hashes = sorted(hashlib.sha256(json.dumps(r['r'],sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest() for r in rows)
        result[name] = {'count':len(rows),'fingerprints':hashes}
    return result

def read_snapshot():
    with connect() as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
        return snapshot(c)

def catalog():
    with connect() as c:
        c.execute('SET TRANSACTION READ ONLY')
        rows=c.execute("""SELECT a.attname AS local,b.attname AS remote,n.nspname AS schema,
            t.relname AS target,k.confdeltype,k.conkey,k.confkey
            FROM pg_constraint k JOIN pg_class t ON t.oid=k.confrelid
            JOIN pg_namespace n ON n.oid=t.relnamespace
            JOIN pg_attribute a ON a.attrelid=k.conrelid AND a.attnum=k.conkey[1]
            JOIN pg_attribute b ON b.attrelid=k.confrelid AND b.attnum=k.confkey[1]
            WHERE k.conrelid='noah.document_question_tasks'::regclass AND k.contype='f'""").fetchall()
        assert len(rows)==3 and all(len(r['conkey'])==len(r['confkey'])==1 for r in rows)
        assert {(r['local'],r['schema'],r['target'],r['remote'],r['confdeltype']) for r in rows} == {
            ('task_id','noah','tasks','id','a'),('project_id','noah','projects','id','a'),
            ('execution_id','noah','execution_records','id','a')}
        check=c.execute("SELECT pg_get_constraintdef(oid) AS d FROM pg_constraint WHERE conrelid='noah.tasks'::regclass AND conname='tasks_status_check'").fetchone()['d']
        assert set(re.findall("'([^']+)'",check)) == {'ready','running','completed','failed'}
        cols={r['column_name']:r for r in c.execute("SELECT column_name,data_type,is_nullable,character_maximum_length FROM information_schema.columns WHERE table_schema='noah' AND table_name='document_question_tasks'").fetchall()}
        assert set(cols)=={'task_id','registration_request_id','project_id','document_name','question','execution_id'}
        for name in ('task_id','registration_request_id','project_id','execution_id'):
            assert cols[name]['data_type']=='uuid'
        for name in ('task_id','registration_request_id','project_id'):
            assert cols[name]['is_nullable']=='NO'
        for name in ('document_name','question'):
            assert cols[name]['data_type']=='text' and cols[name]['is_nullable']=='NO'
        assert cols['execution_id']['is_nullable']=='YES'
        constraints=c.execute("SELECT contype,conkey,pg_get_constraintdef(oid) AS d FROM pg_constraint WHERE conrelid='noah.document_question_tasks'::regclass").fetchall()
        attributes={r['attnum']:r['attname'] for r in c.execute("SELECT attnum,attname FROM pg_attribute WHERE attrelid='noah.document_question_tasks'::regclass AND attnum>0 AND NOT attisdropped").fetchall()}
        assert {tuple(attributes[k] for k in r['conkey']) for r in constraints if r['contype']=='p'}=={('task_id',)}
        assert {tuple(attributes[k] for k in r['conkey']) for r in constraints if r['contype']=='u'}=={('registration_request_id',),('execution_id',)}
        checks=[r['d'] for r in constraints if r['contype']=='c']
        assert len(checks)==2 and any('255' in s and 'document_name' in s for s in checks)
        assert any('300' in s and '512' in s and 'octet_length' in s for s in checks)
        idx=c.execute("SELECT pg_get_indexdef(i.indexrelid) AS d FROM pg_index i JOIN pg_class t ON t.oid=i.indexrelid WHERE i.indrelid='noah.tasks'::regclass AND t.relname='tasks_actor_created_id_idx'").fetchone()['d']
        assert '(actor_user_id, created_at DESC, id DESC)' in idx
    assert all(r['count']==0 for r in read_snapshot().values())

TEXT = 'NOAH\uc758 M18 \ud14c\uc2a4\ud2b8 \ub3d9\ubb3c\uc740 \uc218\ub2ec\uc774\ub2e4.\n'
QUESTION = '\uc774 \ud504\ub85c\uc81d\ud2b8 \ubb38\uc11c\uc758 NOAH M18 \ud14c\uc2a4\ud2b8 \ub3d9\ubb3c\uc744 \uadfc\uac70\uc640 \ud568\uaed8 \uc54c\ub824\uc918.'

def fixture():
    assert all(v['count']==0 for v in read_snapshot().values())
    user, project, token = uuid4(),uuid4(),secrets.token_urlsafe(32)
    with connect() as c:
        c.execute('INSERT INTO noah.users(id,label) VALUES(%s,%s)',(user,M['run']))
        c.execute('INSERT INTO noah.api_tokens(token_hash,user_id) VALUES(%s,%s)',(hashlib.sha256(token.encode()).hexdigest(),user))
        c.execute('INSERT INTO noah.projects(id,label) VALUES(%s,%s)',(project,M['run']))
        c.execute('INSERT INTO noah.project_memberships(project_id,user_id,can_write) VALUES(%s,%s,false)',(project,user))
        c.commit()  # A lost acknowledgement MUST stop, not repeat fixture creation.
    root=ROOT/'document'
    root.mkdir()
    path=root/M['doc_name']; path.write_bytes(TEXT.encode('utf-8'))
    mapping=SOURCE/'config/project_documents.local.json'
    mapping.write_text(json.dumps({'projects':{str(project):{'root_id':M['root_id'],'document_root':str(root)}}}),encoding='utf-8')
    return {'user':str(user),'project':str(project),'token':token,'question':QUESTION,
            'doc_hash':hashlib.sha256(path.read_bytes()).hexdigest(),
            'mapping_hash':hashlib.sha256(mapping.read_bytes()).hexdigest()}

def proof(c,p,phase):
    f=p['fixture']; body=p.get('body'); baseline=p['baseline']
    assert all(v['count']==0 for v in baseline.values()) and set(baseline)==TABLES
    expected={'users':1,'api_tokens':1,'projects':1,'project_memberships':1}
    if phase!='fixture': expected.update(tasks=1,document_question_tasks=1)
    if phase=='terminal': expected.update(execution_records=1,document_read_evidence=1,document_answer_evidence=1)
    snap=snapshot(c)
    assert all(snap[n]['count']==baseline[n]['count']+expected.get(n,0) for n in TABLES)
    assert all(snap[n]==baseline[n] for n in TABLES if n not in expected)
    user=c.execute('SELECT * FROM noah.users WHERE id=%s',(UUID(f['user']),)).fetchone()
    project=c.execute('SELECT * FROM noah.projects WHERE id=%s',(UUID(f['project']),)).fetchone()
    assert user['label']==project['label']==M['run']
    token=c.execute('SELECT * FROM noah.api_tokens WHERE token_hash=%s',(hashlib.sha256(f['token'].encode()).hexdigest(),)).fetchone()
    assert str(token['user_id'])==f['user'] and token['revoked_at'] is None
    member=c.execute('SELECT * FROM noah.project_memberships WHERE project_id=%s AND user_id=%s',(UUID(f['project']),UUID(f['user']))).fetchone()
    assert member is not None and member['can_write'] is False
    path=ROOT/'document'/M['doc_name']; mapping=SOURCE/'config/project_documents.local.json'
    assert path.read_bytes()==TEXT.encode('utf-8') and hashlib.sha256(path.read_bytes()).hexdigest()==f['doc_hash']
    assert hashlib.sha256(mapping.read_bytes()).hexdigest()==f['mapping_hash']
    assert json.loads(mapping.read_text(encoding='utf-8'))=={'projects':{f['project']:{'root_id':M['root_id'],'document_root':str(path.parent)}}}
    expected_calls={'mapping':2,'safe_read':2,'model':1} if phase=='terminal' else {'mapping':0,'safe_read':0,'model':0}
    assert counts()==expected_calls
    if phase=='fixture': return snap
    task_id=UUID(body['task_id'])
    t=c.execute('SELECT * FROM noah.tasks WHERE id=%s',(task_id,)).fetchone()
    d=c.execute('SELECT * FROM noah.document_question_tasks WHERE task_id=%s',(task_id,)).fetchone()
    assert str(t['actor_user_id'])==f['user'] and t['goal']=='Answer an explicitly registered project document question'
    assert str(d['project_id'])==f['project'] and d['document_name']==M['doc_name'] and d['question']==f['question']
    assert str(d['registration_request_id'])==p['registration_request']
    assert body['status']=='succeeded' and body['task']['id']==body['task_id']
    assert body['task']['definition']=={'project_id':f['project'],'document_name':M['doc_name'],'question':f['question']}
    assert body['task']['registration_request_id']==p['registration_request']
    assert not any(s and s in json.dumps(body,ensure_ascii=False) for s in (f['token'],hashlib.sha256(f['token'].encode()).hexdigest(),db.local_settings()['POSTGRES_PASSWORD'],str(ROOT)))
    if phase=='ready':
        assert t['status']==body['task']['status']=='ready' and t['verification_status']==body['task']['verification_status']=='pending'
        assert d['execution_id'] is None and body['execution_id'] is None and body['execution'] is None and body['result'] is None
        if body['outcome']=='task_registered':
            assert body['request_id']==p['registration_request']
            assert body['registration']=={'status':'confirmed','initial_task_status':'ready','initial_verification_status':'pending','execution_created':False}
        else: assert body['outcome']=='task_inspected'
    else:
        e=c.execute('SELECT * FROM noah.execution_records WHERE id=%s',(UUID(body['execution_id']),)).fetchone()
        read=c.execute('SELECT * FROM noah.document_read_evidence WHERE execution_id=%s',(e['id'],)).fetchone()
        answer=c.execute('SELECT * FROM noah.document_answer_evidence WHERE execution_id=%s',(e['id'],)).fetchone()
        assert t['status']==body['task']['status']=='completed' and t['verification_status']==body['task']['verification_status']=='passed'
        assert d['execution_id']==e['id'] and e['task_id']==task_id and str(e['actor_user_id'])==f['user']
        assert e['capability']=='project.documents.answer' and e['status']=='succeeded' and e['verified_at'] is not None
        assert e['failure_code'] is None and e['failure_category'] is None and e['memory_id'] is None
        assert body['execution']['id']==body['execution_id'] and body['execution']['request_id']==p['run_request']
        assert body['execution']['status']=='succeeded' and body['execution']['observation']=='verified'
        assert str(e['request_id'])==p['run_request']
        assert read['project_id']==UUID(f['project']) and read['root_id']==M['root_id'] and read['document_name']==M['doc_name']
        assert read['byte_length']==len(TEXT.encode('utf-8')) and read['content_sha256']==f['doc_hash']
        assert read['content_encoding']=='utf-8' and read['bom_present'] is False
        result=body['result']; quotes=answer['quotes']
        assert result['capability']==e['capability'] and result['project_id']==f['project'] and result['document_name']==M['doc_name']
        assert answer['outcome']==result['outcome'] and result['outcome'] in ('supported','partial')
        assert result['grounded'] is True and result['temporal_scope']=='execution_observation'
        assert quotes==result['evidence'] and 1 <= len(quotes) <= 3
        assert any('\uc218\ub2ec' in q['quote'] for q in quotes)
        for q in quotes:
            assert set(q)=={'quote','start','end'} and 0 < len(q['quote']) <= 240
            assert type(q['start']) is int and type(q['end']) is int
            assert q['start']==TEXT.find(q['quote']) >= 0 and q['end']==q['start']+len(q['quote'])
            assert TEXT[q['start']:q['end']]==q['quote']
        from noah.document_answer import assemble_answer
        assert result['answer']==assemble_answer(answer['outcome'],quotes)
        assert result['document']=={'root_id':read['root_id'],'document_name':read['document_name'],
            'observed_at':read['observed_at'].isoformat(),'byte_length':read['byte_length'],
            'content_sha256':read['content_sha256'],'evidence_execution_id':str(e['id'])}
    return snap

def cleanup(p):
    with connect() as c:
        c.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
        assert proof(c,p,'terminal')==p['before_cleanup']
        task=UUID(p['body']['task_id']); execution=UUID(p['body']['execution_id'])
        f=p['fixture']; user=UUID(f['user']); project=UUID(f['project'])
        deletions=[
            ('DELETE FROM noah.document_answer_evidence WHERE execution_id=%s RETURNING execution_id',(execution,)),
            ('DELETE FROM noah.document_read_evidence WHERE execution_id=%s AND project_id=%s RETURNING execution_id',(execution,project)),
            ('DELETE FROM noah.document_question_tasks WHERE task_id=%s AND execution_id=%s AND project_id=%s RETURNING task_id',(task,execution,project)),
            ('DELETE FROM noah.execution_records WHERE id=%s AND task_id=%s AND actor_user_id=%s AND request_id=%s RETURNING id',(execution,task,user,UUID(p['run_request']))),
            ('DELETE FROM noah.tasks WHERE id=%s AND actor_user_id=%s RETURNING id',(task,user)),
            ('DELETE FROM noah.project_memberships WHERE project_id=%s AND user_id=%s RETURNING project_id',(project,user)),
            ('DELETE FROM noah.projects WHERE id=%s AND label=%s RETURNING id',(project,M['run'])),
            ('DELETE FROM noah.api_tokens WHERE token_hash=%s AND user_id=%s RETURNING user_id',(hashlib.sha256(f['token'].encode()).hexdigest(),user)),
            ('DELETE FROM noah.users WHERE id=%s AND label=%s RETURNING id',(user,M['run']))]
        for sql,parameters in deletions:
            assert len(c.execute(sql,parameters).fetchall())==1
        assert snapshot(c)==p['baseline']
        c.commit()  # Unknown acknowledgement: STOP; never rerun cleanup.
    assert read_snapshot()==p['baseline']
    return {'baseline_restored':True,'deleted_rows':9}

def main():
    mode=sys.argv[1]
    if mode=='serve':
        source_gate(); container_gate()
        with connect() as c:
            destination = {'host':c.info.host,'port':c.info.port,
                           'name':c.info.dbname,'user':c.info.user}
            c.rollback()  # Verify this process's connection before binding the HTTP port.
        from noah.__main__ import main as serve
        source_gate()  # All loaded NOAH modules must still belong to the pinned copy.
        owner = {'run':M['run'],'pid':os.getpid(),'parent':os.getppid(),
                 'launcher':M['python'],'interpreter':sys.executable,
                 'base_interpreter':sys._base_executable,'source':str(SOURCE),
                 'module_root':str(db.ROOT.resolve()),
                 'settings_path':str((db.ROOT/'compose/.env').resolve()),
                 'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 'database':destination}
        (ROOT/'server-owner.json').write_text(json.dumps(owner),encoding='utf-8')
        sys.argv=['noah','serve','--port','8080']
        try:
            serve()
        except KeyboardInterrupt:
            pass  # The operator's owned-server Ctrl+C is the planned shutdown.
        return
    p=json.loads(sys.stdin.buffer.read().decode('utf-8') or '{}')
    if mode=='init':
        db.initialize(); catalog(); output=read_snapshot()
    elif mode=='fixture': output=fixture()
    elif mode=='snapshot': output=read_snapshot()
    elif mode=='proof':
        with connect() as c:
            c.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
            output=proof(c,p,p['phase'])
    elif mode=='cleanup':
        assert p.get('approve_exact_cleanup') is True
        output=cleanup(p)
    else: raise AssertionError('Unknown mode')
    print(json.dumps(output,separators=(',',':'),ensure_ascii=True))

if __name__=='__main__':
    main()
'@
[IO.File]::WriteAllText($Helper,$HelperCode,$Utf8)
$HelperHash = (Get-FileHash -LiteralPath $Helper).Hash
$ProbePath = Join-Path $RunRoot 'interpreter_probe.py'
$ProbeCode = @'
import json
import sys

print(json.dumps(dict(launcher=sys.executable, base=sys._base_executable)))
'@
[IO.File]::WriteAllText($ProbePath,$ProbeCode,$Utf8)
$ProbeHash = (Get-FileHash -LiteralPath $ProbePath).Hash
function Invoke-M18InterpreterProbe([string]$Exe) {
 if ($Exe -ine $Python -or (Get-Location).ProviderPath -cne $Source -or
  (Resolve-Path -LiteralPath $ProbePath).ProviderPath -cne (Join-Path $RunRoot 'interpreter_probe.py') -or
  ((Get-Item -LiteralPath $ProbePath).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
  (Get-FileHash -LiteralPath $ProbePath).Hash -cne $ProbeHash) {
  throw 'Pinned interpreter/probe path or hash differs'
 }
 # No Python source crosses native argument quoting: only the pinned file path.
 $Info=New-Object System.Diagnostics.ProcessStartInfo
 $Info.FileName=$Exe
 $Info.Arguments='-I -B "' + $ProbePath + '"'
 $Info.WorkingDirectory=$Source
 $Info.UseShellExecute=$false; $Info.CreateNoWindow=$true
 $Info.RedirectStandardOutput=$true; $Info.RedirectStandardError=$true
 $Native=New-Object System.Diagnostics.Process
 $Native.StartInfo=$Info
 if (-not $Native.Start()) { throw 'Interpreter probe did not start' }
 $Stdout=$Native.StandardOutput.ReadToEndAsync()
 $Stderr=$Native.StandardError.ReadToEndAsync()
 if (-not $Native.WaitForExit(10000)) { throw 'Interpreter probe timeout; preserve process, STOP' }
 $Text=$Stdout.Result; $ErrorText=$Stderr.Result; $Exit=$Native.ExitCode
 $Native.Dispose()
 if ($Exit -ne 0 -or $ErrorText.Length -ne 0) { throw 'Interpreter probe exit/stderr failed' }
 $Runtime=ConvertFrom-Json -InputObject $Text -ErrorAction Stop
 if (($Runtime.PSObject.Properties.Name | Sort-Object) -join ',' -cne 'base,launcher' -or
  $Runtime.launcher -ine $Exe -or -not [IO.Path]::IsPathRooted([string]$Runtime.base) -or
  -not (Test-Path -LiteralPath $Runtime.base -PathType Leaf)) {
  throw 'Interpreter probe JSON/path pair differs'
 }
 return $Runtime
}
function Assert-M18Boundary {
 if ((Get-Location).ProviderPath -cne $Source -or
  -not (Test-Path -LiteralPath $Helper -PathType Leaf) -or
  (Get-FileHash -LiteralPath $Helper).Hash -cne $HelperHash -or
  (Get-FileHash -LiteralPath $ProbePath).Hash -cne $ProbeHash -or
  (Get-FileHash -LiteralPath $ManifestPath).Hash -cne $ManifestHash -or
  (Get-FileHash -LiteralPath $SettingsPath).Hash -cne $SettingsHash -or
  (@(git -C $Repo -c core.quotepath=false status --short) -join "`n") -cne ($GitBefore -join "`n")) {
  throw 'Source/cwd/configuration/Git gate changed; STOP BEFORE connecting'
 }
 foreach ($Relative in $CodeHashes.Keys) {
  if ((Get-FileHash -LiteralPath (Join-Path $Source $Relative)).Hash.ToLowerInvariant() -cne $CodeHashes[$Relative]) {
   throw 'Disposable source hash changed'
  }
 }
 Assert-M18Container
}
function Invoke-M18Helper([string]$Mode,[object]$Payload) {
 Assert-M18Boundary
 $InputJson = if ($null -eq $Payload) { '{}' } else { $Payload | ConvertTo-Json -Depth 30 -Compress }
 $Output = @($InputJson | & $Python -I -B $Helper $Mode)
 if ($LASTEXITCODE -ne 0 -or $Output.Count -ne 1) { throw 'Helper failed; preserve state' }
 return ($Output[0] | ConvertFrom-Json)
}
# Python stdin is UTF-8 even in PowerShell 5.1. Never echo this input.
$OutputEncoding = New-Object System.Text.UTF8Encoding($false)
Assert-M18Boundary
Write-Output 'Pinned helper and fail-closed source/connection boundary prepared'
```

Expected: one confirmation. This block only writes the disposable helper and
stdlib interpreter probe; it does not itself migrate or query the DB. Keep
helper/probe/manifest hashes in A. The module-level gate also runs in M7's
spawned worker process. No helper
is ever invoked after the copy is removed. Do not run Python `-c` imports
or a snapshot helper from the source repository as a cleanup diagnostic.

## 4. A — migrations, catalog, full baseline, minimal fixture

Execute `init` **once** through the pinned helper. `db.initialize()` applies
001–014 in existing order in one transaction. The connection gate sets finite
lock/statement bounds. Migration 013 extends three Audit CHECKs and adds its
lineage table; 014 expands the Task CHECK and adds definition/FKs/index.
CHECK replacement can acquire strong table locks and validate rows. Here the
DB is new, empty, and exclusively owned; it is not a personal deployment.

```powershell
$Baseline = Invoke-M18Helper init $null
$BaselineJson = $Baseline | ConvertTo-Json -Depth 30 -Compress
if (@($Baseline.PSObject.Properties).Count -ne 21 -or
 @($Baseline.PSObject.Properties | Where-Object { $_.Value.count -ne 0 }).Count -ne 0) {
 throw 'Exact empty 21-table baseline not established; no fixture permitted'
}
if ($FixtureAttempted) { throw 'Fixture creation already attempted' }
$FixtureAttempted=$true
$Fixture = Invoke-M18Helper fixture $null
$FixtureProof = Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='fixture'}
$Headers = @{Authorization='Bearer ' + $Fixture.token}
$Question = [string]$Fixture.question
$ProjectId = [string]$Fixture.project
$DocName = 'm18-synthetic.md'
$DocPath = Join-Path (Join-Path $RunRoot 'document') $DocName
Write-Output '001–014 catalog, empty 21-table baseline and exact four-row fixture verified'
```

Expected: one confirmation. Baseline fingerprints are captured only in A's
variables; do not output `$Baseline`, `$Fixture`, or `$Headers`. Fixture uses
one user/token/project/read-only membership and one tiny synthetic Markdown
file. No Memory, Session, Task, Execution, or Audit exists yet. No private
DB backup or migration rollback is part of this isolated run.

## 5. C/B — dedicated model and owned NOAH process

Enter the **current A `$RunRoot` value** in each new window; it is a temporary
path, not a secret. Never use a previous root. Existing 11435 or 8080 means
STOP, not reuse/termination. Start C's dedicated Ollama in the foreground:

```powershell
# C only: substitute this run's exact root, without copying credentials.
$RunRoot = '<current A RunRoot>'
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Use Windows PowerShell 5.1' }
$M = Get-Content -LiteralPath (Join-Path $RunRoot 'manifest.json') -Raw | ConvertFrom-Json
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 11435 }).Count -ne 0) { throw '11435 occupied' }
$OllamaExe=(Get-Command ollama.exe -ErrorAction Stop).Source
@{run=$M.run;parent=$PID;exe=$OllamaExe} | ConvertTo-Json -Compress |
 Set-Content -LiteralPath (Join-Path $RunRoot 'ollama-owner.json') -Encoding Ascii
$env:OLLAMA_HOST='127.0.0.1:11435'
$env:OLLAMA_DEBUG='false'
& $OllamaExe serve
```

Leave C running. No model pull/download/replacement. In B:

```powershell
# B only: substitute this run's exact root. Keep this B window for restarts.
$RunRoot = '<current A RunRoot>'
$ErrorActionPreference='Stop'
if ($PSVersionTable.PSVersion.Major -ne 5 -or $PSVersionTable.PSVersion.Minor -ne 1) { throw 'Use Windows PowerShell 5.1' }
$M = Get-Content -LiteralPath (Join-Path $RunRoot 'manifest.json') -Raw | ConvertFrom-Json
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0) { throw '8080 occupied' }
Set-Location -LiteralPath $M.source
& $M.python -I -B (Join-Path $M.source 'operate_m18.py') serve
```

Expected: B and C stay in their foreground processes. They do not apply
migrations. In A, verify exact process ownership before any request:

```powershell
function Assert-M18ProcessObservation([int]$Port,$Owner,$Listeners,$Process,
 [string]$Sid,[string]$Exe,[string]$Entry,$Runtime) {
 $Listeners=@($Listeners)
 $Owners=@($Listeners | Select-Object -ExpandProperty OwningProcess -Unique)
 if ($Owner.run -cne $Run -or $Listeners.Count -lt 1 -or $Owners.Count -ne 1 -or
  @($Listeners | Where-Object { $_.LocalAddress -ne '127.0.0.1' -and $_.LocalAddress -ne '::1' }).Count -ne 0 -or
  $null -eq $Process -or $Process.ProcessId -ne $Owners[0] -or
  $Process.ParentProcessId -ne $Owner.parent -or $Process.CreationDate -lt $RunStart -or
  $Sid -cne $UserSid -or -not $Process.CommandLine.Contains($Entry)) {
  throw 'Owned process identity not proven'
 }
 if ($Port -eq 8080) {
  # Both permitted images come from the pinned launcher, not an owner-file allowlist.
  $ArgsPattern='(?i)\s-I\s+-B\s+"?' + [regex]::Escape($Entry) + '"?\s+serve\s*$'
  if ($null -eq $Runtime -or $Runtime.launcher -ine $Exe -or
   -not [IO.Path]::IsPathRooted([string]$Runtime.base) -or
   ($Process.ExecutablePath -ine $Exe -and $Process.ExecutablePath -ine $Runtime.base) -or
   $Process.ProcessId -ne $Owner.pid -or $Process.CommandLine -notmatch $ArgsPattern -or
   $Owner.launcher -ine $Exe -or $Owner.interpreter -ine $Runtime.launcher -or
   $Owner.base_interpreter -ine $Runtime.base -or $Owner.source -ine $Source -or
   $Owner.module_root -ine $Source -or $Owner.settings_path -ine $SettingsPath -or
   $Owner.helper_sha256 -cne $HelperHash.ToLowerInvariant() -or
   $Owner.database.host -cne '127.0.0.1' -or $Owner.database.port -ne $DbPort -or
   $Owner.database.name -cne $DbName -or $Owner.database.user -cne $DbUser) {
   throw 'Owned Python launcher/runtime/source/destination differs'
  }
 } elseif ($Process.ExecutablePath -ine $Exe) { throw 'Owned process executable differs' }
 return [int]$Process.ProcessId
}
function Assert-M18Process([int]$Port,[string]$OwnerFile,[string]$Exe,[string]$Entry) {
 $Owner=Get-Content -LiteralPath $OwnerFile -Raw | ConvertFrom-Json
 $Listeners=@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
  Where-Object { $_.LocalPort -eq $Port })
 $Owners=@($Listeners | Select-Object -ExpandProperty OwningProcess -Unique)
 if ($Owners.Count -ne 1) { throw 'Listener ownership differs' }
 $Process=Get-CimInstance Win32_Process -Filter "ProcessId=$($Owners[0])"
 if ($null -eq $Process) { throw 'Listener process disappeared' }
 $Sid=(Invoke-CimMethod -InputObject $Process -MethodName GetOwnerSid).Sid
 $Runtime=$null
 if ($Port -eq 8080) {
  # Stdlib only: -I/-B; no NOAH imports, configuration reads, DB or model calls.
  $Runtime=Invoke-M18InterpreterProbe $Exe
 }
 return (Assert-M18ProcessObservation $Port $Owner $Listeners $Process $Sid $Exe $Entry $Runtime)
}
Assert-M18Boundary
$OllamaPid=Assert-M18Process 11435 (Join-Path $RunRoot 'ollama-owner.json') $OllamaExe 'serve'
$ServerPid=Assert-M18Process 8080 (Join-Path $RunRoot 'server-owner.json') $Python $Helper
$Tags=Invoke-RestMethod -Method Get -Uri 'http://127.0.0.1:11435/api/tags' -TimeoutSec 10
if (@($Tags.models | Where-Object { $_.name -ceq 'gemma4:12b-it-qat' }).Count -ne 1) {
 throw 'Required installed model absent; STOP without pulling'
}
Write-Output 'Owned loopback NOAH and dedicated current-model Ollama verified'
```

Expected: one confirmation. Ordinary 11434 is never called or modified.
Record PID variables, not complete process command lines or Docker config.
The NOAH process may use the pinned virtual-environment launcher or its
stdlib-probed base interpreter. Its hashed helper records module/configuration
roots and the verified isolated DB destination before listening. Every restart
rewrites that record; PID/parent/user/creation/arguments/loopback and source/DB
checks remain mandatory. This probe imports only `sys`/`json`, never NOAH or
original repository settings. Its exact root path/hash are pinned in A; its
file invocation captures stdout/stderr separately and rejects nonzero exit,
any stderr, invalid JSON or a different launcher/path pair. No Python source
is passed with `-c`. It does not add an executable wildcard. Before starting
an E2E, execute this same function under PowerShell 5.1 with the same pinned
launcher and a newly owned offline root. Verify the normal result and reject
wrong launcher/base pairs, tampered hash, nonzero exit, stderr and invalid
JSON using synthetic probe files only. No DB/HTTP/Ollama is used for that gate.

## 6. A — offline byte-array proof; one registration POST

**EXACTLY ONCE; DO NOT REEXECUTE THE POST BLOCK.** This fixes the PowerShell
5.1 array-unrolling problem from M16. Both English and Korean are tested
offline, before the first POST.

```powershell
function ConvertTo-NoahJsonBytes([object]$Value) {
 $Json=ConvertTo-Json -InputObject $Value -Depth 10 -Compress
 [byte[]]$Bytes=$Utf8.GetBytes($Json)
 return ,$Bytes
}
foreach ($Text in @('Which animal is stated in this project document?',$Question)) {
 $Bytes=ConvertTo-NoahJsonBytes @{question=$Text}
 if ($Bytes.GetType().FullName -cne 'System.Byte[]' -or
  ($Utf8.GetString($Bytes) | ConvertFrom-Json).question -cne $Text) {
  throw 'Offline strict UTF-8/byte[] gate failed; no POST permitted'
 }
}
$RegisterBody=ConvertTo-NoahJsonBytes @{project_id=$ProjectId;document_name=$DocName;question=$Question}
if ($RegisterBody.GetType().FullName -cne 'System.Byte[]' -or $RegisterSent) { throw 'Registration once-only/body gate failed' }
Assert-M18Boundary
[void](Assert-M18Process 8080 (Join-Path $RunRoot 'server-owner.json') $Python $Helper)
$RegisterSent=$true # EXACTLY ONE POST; even an exception does not reset this flag.
$RegisterHttp=Invoke-WebRequest -UseBasicParsing -Method Post `
 -Uri 'http://127.0.0.1:8080/tasks/document-questions' -Headers $Headers `
 -ContentType 'application/json; charset=utf-8' -Body $RegisterBody -TimeoutSec 30
$Registered=$RegisterHttp.Content | ConvertFrom-Json
if ($RegisterHttp.StatusCode -ne 201 -or $Registered.outcome -ne 'task_registered') {
 throw 'Registration differs/uncertain; STOP without resending'
}
$TaskId=[string]$Registered.task_id
$RegistrationRequest=[string]$Registered.request_id
$ReadyProof=Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='ready';body=$Registered;registration_request=$RegistrationRequest}
Write-Output 'One registration: HTTP 201; ready Task/definition only; model/file/mapping calls zero'
```

Expected: one confirmation. This exclusively owned happy-path run must still
be ready. The general API may legitimately read back running/terminal after
another authorized run; that race is automated-test scope. Here such a state
would indicate an unexpected additional caller and requires STOP.

## 7. B/A — first restart and the same ready Task GET

In B press **Ctrl+C**, wait for the owned server to exit, then in A:

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
 (Get-Process -Id $ServerPid -ErrorAction SilentlyContinue)) { throw 'Owned server not stopped' }
Assert-M18Boundary
Write-Output 'Owned NOAH stopped; restart the same B command'
```

In B rerun **only** its Section 5 server command. Do not recreate a Task,
fixture, database, or Ollama process. Once the new listener appears, in A:

```powershell
$PreviousPid=$ServerPid
$ServerPid=Assert-M18Process 8080 (Join-Path $RunRoot 'server-owner.json') $Python $Helper
if ($ServerPid -eq $PreviousPid) { throw 'New server PID not proven' }
$ReadyHttp=Invoke-WebRequest -UseBasicParsing -Method Get `
 -Uri "http://127.0.0.1:8080/tasks/$TaskId" -Headers $Headers -TimeoutSec 30
$Ready=$ReadyHttp.Content | ConvertFrom-Json
if ($ReadyHttp.StatusCode -ne 200 -or $Ready.task_id -cne $TaskId -or
 $Ready.request_id -ceq $RegistrationRequest) { throw 'Ready inspection correlation differs' }
$ReadyAfterRestart=Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='ready';body=$Ready;registration_request=$RegistrationRequest}
if (($ReadyAfterRestart | ConvertTo-Json -Depth 30 -Compress) -cne
 ($ReadyProof | ConvertTo-Json -Depth 30 -Compress)) { throw 'Ready GET caused/unexpected DB delta' }
Write-Output 'Same ready Task after restart; Execution/model/file/mapping still zero'
```

Expected: one confirmation. Inspect is read-only and its fresh request ID
does not replace the persisted registration request ID.

## 8. A — one explicit run POST and terminal proof

**EXACTLY ONCE; DO NOT REEXECUTE THIS POST BLOCK.** No Idempotency-Key or
Noah-Session-Id header is sent. Accept the actual grounded outcome without
converting `partial` to `supported` or retrying for a better answer.

```powershell
$RunBody=ConvertTo-NoahJsonBytes @{}
if ($RunBody.GetType().FullName -cne 'System.Byte[]' -or $RunSent) { throw 'Run once-only/body gate failed' }
Assert-M18Boundary
[void](Assert-M18Process 8080 (Join-Path $RunRoot 'server-owner.json') $Python $Helper)
[void](Assert-M18Process 11435 (Join-Path $RunRoot 'ollama-owner.json') $OllamaExe 'serve')
$RunSent=$true # EXACTLY ONE POST; never reset, including timeout/response loss.
$RunHttp=Invoke-WebRequest -UseBasicParsing -Method Post `
 -Uri "http://127.0.0.1:8080/tasks/$TaskId/run" -Headers $Headers `
 -ContentType 'application/json; charset=utf-8' -Body $RunBody -TimeoutSec 180
$Executed=$RunHttp.Content | ConvertFrom-Json
if ($RunHttp.StatusCode -ne 200 -or $Executed.outcome -ne 'task_executed' -or
 $Executed.task_id -cne $TaskId) { throw 'Execution differs/uncertain; STOP without resending' }
$RunRequest=[string]$Executed.request_id
$TerminalProof=Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='terminal';body=$Executed;registration_request=$RegistrationRequest;run_request=$RunRequest}
Write-Output 'One explicit run: HTTP 200; same Task, one Execution, both verified Evidence rows'
```

Expected: one confirmation. Proof requires completed/passed and
succeeded/verified, exact definition/binding/request IDs, source hash/UTF-8/BOM,
exact first Unicode `[start,end)` quote positions, animal fact, and precisely
one real answer-model invocation. Other tables, including Memory, Session,
all legacy Evidence, and Routing Audit, remain at the empty baseline.
Atomicity under rollback/uncertain commits is automated-test evidence; this
happy-path DB readback alone does not reproduce those faults.

## 9. B/A — second restart and persisted historical result GET

Stop B with Ctrl+C and repeat Section 7's **stop verification only**. Restart
the same B server command again. Do not rerun the registration or run POST.

```powershell
$PreviousPid=$ServerPid
$ServerPid=Assert-M18Process 8080 (Join-Path $RunRoot 'server-owner.json') $Python $Helper
if ($ServerPid -eq $PreviousPid) { throw 'Second restart PID not proven' }
Assert-M18Boundary
$HistoricHttp=Invoke-WebRequest -UseBasicParsing -Method Get `
 -Uri "http://127.0.0.1:8080/tasks/$TaskId" -Headers $Headers -TimeoutSec 30
$Historic=$HistoricHttp.Content | ConvertFrom-Json
if ($HistoricHttp.StatusCode -ne 200 -or $Historic.outcome -ne 'task_inspected' -or
 $Historic.request_id -ceq $RunRequest -or $Historic.execution_id -cne $Executed.execution_id -or
 ($Historic.result | ConvertTo-Json -Depth 20 -Compress) -cne
 ($Executed.result | ConvertTo-Json -Depth 20 -Compress)) { throw 'Historical result/correlation differs' }
$HistoricProof=Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='terminal';body=$Historic;registration_request=$RegistrationRequest;run_request=$RunRequest}
if (($HistoricProof | ConvertTo-Json -Depth 30 -Compress) -cne
 ($TerminalProof | ConvertTo-Json -Depth 30 -Compress)) { throw 'Historical GET caused/unexpected DB delta' }
Write-Output 'Historical result survived second restart; zero new model/file/mapping calls or DB delta'
```

Expected: one confirmation. The operation-label counters remain model=1,
safe_read=2, mapping=2 across both restarts. Verification helpers may read
the owned synthetic file to check its hash; those reads are separate from
the application's counted safe-read/mapping path. A recorded result is an
execution-time observation, not a guarantee of current file contents.

## 10. B/A — read-only cleanup gate, then one exact transaction

Stop only B's owned server with Ctrl+C and verify 8080/PID absence as in
Section 7. Keep C running until final checks. Do not invoke Appendix/abort
cleanup from another milestone: a partial/uncertain M18 run needs separate
ownership review and approval.

First block is **read-only**:

```powershell
Assert-M18Boundary
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 8080 }).Count -ne 0 -or
 (Get-Process -Id $ServerPid -ErrorAction SilentlyContinue)) { throw 'Server still exists; no DELETE permitted' }
$BeforeCleanup=Invoke-M18Helper proof @{baseline=$Baseline;fixture=$Fixture;phase='terminal';body=$Historic;registration_request=$RegistrationRequest;run_request=$RunRequest}
if (($BeforeCleanup | ConvertTo-Json -Depth 30 -Compress) -cne
 ($TerminalProof | ConvertTo-Json -Depth 30 -Compress)) { throw 'Cleanup state changed; STOP' }
$CleanupGatePassed=$true
Write-Output 'Read-only exact nine-row ownership and full 21-table delta gate passed'
```

Only after that block passes, and only within the separately approved E2E
including normal cleanup, execute this mutation block **once**:

```powershell
if (-not $CleanupGatePassed -or $CleanupAttempted) { throw 'Cleanup not gated or already attempted' }
$CleanupAttempted=$true
$CleanupResult=Invoke-M18Helper cleanup @{
 approve_exact_cleanup=$true;baseline=$Baseline;fixture=$Fixture;phase='terminal';
 body=$Historic;registration_request=$RegistrationRequest;run_request=$RunRequest;
 before_cleanup=$BeforeCleanup
}
if (-not $CleanupResult.baseline_restored -or $CleanupResult.deleted_rows -ne 9) {
 throw 'Cleanup commit/baseline unconfirmed; do not repeat'
}
$AfterCleanup=Invoke-M18Helper snapshot $null
if (($AfterCleanup | ConvertTo-Json -Depth 30 -Compress) -cne $BaselineJson) {
 throw 'Full 21-table private baseline not restored'
}
Write-Output 'Exact nine synthetic rows deleted once; all 21-table counts/fingerprints restored'
```

The helper repeats ownership/delta proof in the SERIALIZABLE cleanup
transaction and checks each `DELETE ... RETURNING` count before commit.
Order: answer Evidence → read Evidence → definition (releases Execution FK)
→ Execution → Task → membership → project → token → user. No broad DELETE,
cascade, guessed ID, constraint disabling, or schema reversal is used. Any
error before commit rolls back; any unconfirmed commit stops without retry.
The 001–014 schema remains until this disposable container is removed.

## 11. A/C — owned resource removal and final environment proof

All DB observations occur **before** removing the copy/container. Once the
copy is gone, do not invoke the helper, import NOAH from the original repo,
or attempt DB diagnostics. Neither a private baseline nor private migration
deployment is claimed by the empty isolated baseline.

In A, verify C ownership again, then press Ctrl+C **in that same C window**.
Back in A, verify 11435 and its previously owned PID are absent. An existing
or unrelated process is never stopped. Then:

```powershell
if (@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 11435 -or $_.LocalPort -eq 8080 }).Count -ne 0 -or
 (Get-Process -Id $OllamaPid -ErrorAction SilentlyContinue)) { throw 'Owned services not stopped' }
Assert-M18Boundary
$FinalSnapshot=Invoke-M18Helper snapshot $null
if (($FinalSnapshot | ConvertTo-Json -Depth 30 -Compress) -cne $BaselineJson) { throw 'Final isolated baseline differs' }
$OrdinaryAfter=@(Get-NetTCPConnection -State Listen -ErrorAction Stop |
 Where-Object { $_.LocalPort -eq 11434 } |
 ForEach-Object { "$($_.LocalAddress)|$($_.OwningProcess)" } | Sort-Object)
if (($OrdinaryAfter -join '|') -cne ($OrdinaryBefore -join '|')) { throw 'Ordinary Ollama listener identity changed; STOP' }
Assert-M18Container
docker stop --timeout 10 $Container | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Container stop uncertain; no automatic retry' }
docker rm $Container | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Container removal uncertain; no automatic retry' }
if (@(docker ps -a --filter "label=noah.test.run=$Run" --format '{{.ID}}').Count -ne 0 -or
 $LASTEXITCODE -ne 0) { throw 'Owned container absence not confirmed' }
# LEAVE the copy's cwd before deleting it. NEVER call Invoke-M18Helper again.
Set-Location -LiteralPath $env:TEMP
$Resolved=(Resolve-Path -LiteralPath $RunRoot).ProviderPath
$TempRoot=(Resolve-Path -LiteralPath $env:TEMP).ProviderPath
if ($Resolved -cne $RunRoot -or -not $Resolved.StartsWith($TempRoot+'\',[StringComparison]::OrdinalIgnoreCase) -or
 (Get-FileHash -LiteralPath $ManifestPath).Hash -cne $ManifestHash -or
 (Get-FileHash -LiteralPath $Helper).Hash -cne $HelperHash -or
 (Get-FileHash -LiteralPath $ProbePath).Hash -cne $ProbeHash -or
 (Get-FileHash -LiteralPath $SettingsPath).Hash -cne $SettingsHash -or
 (Get-FileHash -LiteralPath $DocPath).Hash.ToLowerInvariant() -cne $Fixture.doc_hash -or
 (Get-FileHash -LiteralPath $Mapping).Hash.ToLowerInvariant() -cne $Fixture.mapping_hash) {
 throw 'Exact local ownership/hash changed; do not delete'
}
$ExpectedFiles=@($CodeHashes.Keys | ForEach-Object { Join-Path $Source $_ }) + @(
 $ManifestPath,$Helper,$ProbePath,$SettingsPath,$Mapping,$DocPath,
 (Join-Path $RunRoot 'server-owner.json'),(Join-Path $RunRoot 'ollama-owner.json'),
 (Join-Path $RunRoot 'operation-counts.txt')
)
$Entries=@(Get-ChildItem -LiteralPath $RunRoot -Recurse -Force)
foreach ($Entry in @((Get-Item -LiteralPath $RunRoot)) + $Entries) {
 if (($Entry.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0 -or
  ($Entry.FullName -cne $RunRoot -and -not $Entry.FullName.StartsWith($RunRoot+'\',[StringComparison]::OrdinalIgnoreCase))) {
  throw 'Link or escaping entry found; STOP'
 }
}
if (@(Compare-Object -ReferenceObject ($ExpectedFiles | Sort-Object) -DifferenceObject (@($Entries | Where-Object { -not $_.PSIsContainer } | Select-Object -ExpandProperty FullName) | Sort-Object)).Count -ne 0) {
 throw 'Unexpected local file; no broad cleanup'
}
foreach ($File in $ExpectedFiles) { Remove-Item -LiteralPath $File -ErrorAction Stop }
foreach ($Directory in @($Entries | Where-Object { $_.PSIsContainer } |
 Sort-Object { $_.FullName.Length } -Descending)) {
 Remove-Item -LiteralPath $Directory.FullName -ErrorAction Stop # empty only, no -Recurse
}
Remove-Item -LiteralPath $RunRoot -ErrorAction Stop
if (Test-Path -LiteralPath $RunRoot) { throw 'Owned empty root remains; record incomplete cleanup' }
if ((@(git -C $Repo -c core.quotepath=false status --short) -join "`n") -cne ($GitBefore -join "`n")) {
 throw 'Repository changed during E2E'
}
$Headers=$null; $Fixture=$null; $DbPassword=$null
Write-Output 'Owned resources removed; Git and ordinary 11434 unchanged; no private DB helper invoked'
```

Expected: one confirmation. No volume-delete flag or recursive filesystem
delete is used. If removing an empty root fails, stop and record that fact;
do not retry or delete previous runs' directories. PostgreSQL named volumes
and personal mapping are protected by never reading/mounting/using them,
not by claiming an unperformed private-data comparison.

## Operator result record

### First attempt — historical, STOPPED at Section 1 (2026-10-12)

**Status: STOPPED BEFORE RESOURCE CREATION.**
One approved attempt used a fresh Windows PowerShell 5.1 control session.
Section 1 stopped at the multiline positional `Compare-Object` expression
in the Git path gate: runtime binding reported missing `DifferenceObject`
(`ParameterBindingException`). Its earlier AST syntax check passed, but
that does not prove runtime argument binding. No condition was relaxed,
no code or procedural expression was fixed, and the section was not rerun.

Independent read-only Git inspection confirmed the baseline and expected
eight paths. The Run ID/root allocation, PostgreSQL container, DB connection,
001–014 migration, 21-table snapshot, fixture, NOAH and dedicated Ollama
startup were never reached. Registration/run POST counts and Task GET counts
were all zero; the model/tags check was not reached. No cleanup was needed
or attempted, and no personal DB/settings/mapping or existing service was
used. The following later-stage results remain unperformed; do not replace
them with the prior automated results. A reviewed runbook correction and a
separately approved fresh attempt are required.

| First-attempt check | Actual result |
| --- | --- |
| Exact Git/source/configuration/connection and process ownership gates | Section 1 STOP: missing `DifferenceObject`; separate Git inspection matched baseline/eight paths; remaining gates not reached |
| PostgreSQL 17 tmpfs; 001–014 catalog; empty 21-table baseline | Not run; no container, connection, migration, or snapshot |
| Synthetic four-row fixture, Markdown and mapping | Not created |
| One registration POST: 201; ready; Execution/model/file/mapping zero | Not run; POST count 0 |
| First server restart; same ready Task GET; DB delta zero | Not run; Task GET count 0 |
| One explicit run POST: 200; actual supported/partial; grounded exact animal quote | Not run; POST/model count 0; no observed outcome |
| Same Task/one Execution/two Evidence rows; hash and Unicode positions; audit zero | Not run; no synthetic rows created |
| Second restart; historical GET; zero new model/file/mapping calls or DB delta | Not run; Task GET count 0 |
| Exact nine-row transaction cleanup and complete 21-table baseline restoration | Not applicable to this attempt; no mutation or baseline capture; no DELETE |
| Owned server/11435/container/copy removed; ordinary 11434 and Git unchanged | No resources created; existing services not used/changed; Git unchanged before result documentation |
| Actual POST/GET counts and any STOP/uncertainty | All HTTP requests 0; Section 1 runtime verifier error; no unknown DB commit or HTTP response loss |

### Second attempt — historical, STOPPED at Section 2 (2026-10-12)

Both path comparisons were minimally corrected to one-line explicit named
arguments. Their actual expressions passed identical/missing/extra synthetic
array execution under PowerShell 5.1; the six results and 15-block AST check
passed without DB/model/HTTP use. The first-attempt history above is unchanged.

A fresh Run ID was used. Section 1 passed; Section 2 created only the
restricted temporary copy/synthetic configuration/empty mapping and the
owned PostgreSQL container. `Assert-M18Container` then raised
`Container/storage/port differs; STOP`. No subsequent block was run.

Read-only inspection of this container verified its exact ID/image/label,
running state, and `127.0.0.1:57838` binding. Its actual tmpfs configuration
was `HostConfig.Tmpfs={"/var/lib/postgresql/data":"rw,size=1g"}` and
`Mounts=[]`. The runbook's one-entry `Mounts` requirement does not match
this representation of `--tmpfs`. The PowerShell 5.1 parsed root array also
remained nested in the outer `@(...)`, producing Mounts count one but null
Type/Destination in the failed gate. No named-volume/bind mount was found.
The gate was not bypassed or changed after this STOP.

At that STOP the container, temporary root, and fresh PowerShell A state
were preserved without printing credentials. The subsequent separately
approved cleanup is recorded in `56`; it did not resume this E2E. The personal DB, settings, mapping and named volume were not
read or modified. No NOAH/Ollama process was started; read-only listener
inspection found 8080/11435 absent and ordinary 11434 present. No DB helper
was created or run, and no migration/NOAH fixture/HTTP request/model call
occurred. Do not apply the normal nine-row cleanup to this partial setup.

| Second-attempt check | Actual result |
| --- | --- |
| Exact Git baseline/eight paths and free isolated ports | Passed Section 1 |
| Fresh source/synthetic settings and owned PostgreSQL container | Created; preserved after STOP |
| Storage gate | STOP: `--tmpfs` metadata is in `HostConfig.Tmpfs`; `Mounts` is empty; JSON array nesting also affects the PowerShell gate |
| Migration 001–014 / 21-table baseline / NOAH fixture | Not run / not captured / not created |
| Dedicated Ollama model / NOAH server / restarts | Not started or verified |
| Task registration/run POSTs and Task GETs | 0 / 0 / 0 |
| Task/Execution/Evidence and actual outcome | Not exercised; no observed answer outcome |
| Cleanup and baseline restoration | Not attempted; resources preserved; no baseline restoration claim |
| Existing personal environment | No DB/settings/mapping/volume access; no existing service modification; only ordinary listener metadata inspected |

The storage/JSON verifier was subsequently corrected and the approved
exact-owner cleanup completed (see `56`). A fresh E2E still requires
separate approval. Do not automatically continue this stopped run or alter the
M18 implementation to address a procedural metadata issue.

Concurrency, revocation races, process-crash handling, rollback, response loss,
and commit-acknowledgement uncertainty remain deterministic automated evidence.
Do not claim they were manually injected. This run also does not validate
personal DB deployment, generic orchestration/recovery, universal model
semantic accuracy, or immunity to every concurrent revocation/file change.

### Third attempt — historical, STOPPED at Section 5 (2026-10-12)

**Status: STOPPED BEFORE HTTP REQUESTS; STATE PRESERVED.**
A newly approved attempt used a fresh PowerShell 5.1 A session and new owned
resources. Sections 1–4 passed, including the corrected path comparison and
storage/JSON gates, actual writable tmpfs mount, pinned source/connection
isolation, migrations 001–014/catalog and the empty 21-table private baseline.
The minimal four-row synthetic fixture and one Markdown were verified.
The two previous stopped attempts remain historical; their results are not
combined with this attempt into a successful run.

Section 5 started the owned dedicated Ollama and NOAH processes. The Ollama
process ownership check passed, but `Assert-M18Process` for NOAH 8080 stopped
with `Owned process identity not proven`. Read-only process-record comparison
confirmed run/PID/parent/user/helper/loopback fields, but the actual listener
executable was the virtual environment's base Python interpreter, not the
launcher path expected by `$Python`. The executable-path test failed.
No gate was modified, bypassed or rerun, and no later block was executed.

| Third-attempt check | Actual result |
| --- | --- |
| Sections 1–4 | Passed; isolated PostgreSQL 17 tmpfs, migrations/catalog, private empty 21-table baseline, exact four-row fixture |
| Dedicated Ollama 11435 process ownership | Passed; tags/model call not reached |
| NOAH 8080 process ownership | STOP: base interpreter executable differs from expected virtual-environment launcher |
| Registration / run POST / Task GET counts | 0 / 0 / 0 |
| Ready/result/restart/Task–Execution–Evidence verification | Not reached; no actual answer/outcome |
| Cleanup/baseline restoration | Not attempted; fixture and private baseline preserved |
| Residual resources | This run's container, temporary copy/document, four fixture rows, NOAH 8080 and dedicated Ollama 11435 remain |
| Existing environment | No personal DB/settings/mapping/volume access; ordinary 11434 not called/changed |

At that STOP A was blocked and retained private baseline/fixture/once-only
state for separately approved exact-owner inspection and cleanup. Do not apply the
normal nine-row cleanup to this four-row partial setup. Do not resume the
stopped controller or send a POST after changing the process test. The process verifier correction and approved partial cleanup were later
completed (see `56`). A new E2E still requires separate approval. No M18 implementation, migration or contract change was made;
no staging, commit or push was performed.

### Fourth attempt — STOPPED at Section 5; safe abort cleanup complete (2026-10-12)

A fresh approved isolated attempt passed Sections 1–4 with new resources,
synthetic configuration and PostgreSQL 17 tmpfs. Migrations 001–014/catalog,
the empty 21-table private baseline and the exact four-row fixture/document
were verified. Source/module/configuration/container/destination gates ran
before DB helpers and the owned server's startup connection.

Dedicated Ollama and NOAH started. Ollama ownership passed, but the NOAH
interpreter probe in Section 5 failed with Python
`NameError: name 'launcher' is not defined`; A stopped with
`Pinned interpreter probe failed`. Actual PowerShell 5.1 native `-c` argument
transport removed the embedded JSON-key double quotes. The offline metadata
predicate tests had not executed this native probe transport. No command,
condition or question was changed to continue; the section was not retried.

| Fourth-attempt check | Actual result |
| --- | --- |
| Sections 1–4/source/settings/container/DB/migrations/catalog | Passed, isolated resources only |
| Private empty 21-table baseline and four-row fixture | Captured/verified |
| Section 5 process/model gate | STOP at native interpreter probe after Ollama ownership passed; tags not reached |
| Task registration / explicit run POST / Task GET / model invocation | 0 / 0 / 0 / 0 |
| Ready, restarts, terminal Evidence, supported/partial, historical result | Not exercised; no outcome observed |
| Safe abort transaction | Exact membership/project/token/user 4 rows deleted once; original 21-table counts/private fingerprints restored |
| Owned services/container/copy | Normally stopped and exactly removed; no remaining fourth-run resources |
| Ordinary Ollama 11434 | No request or modification; listener/process matched original A record |

Safe cleanup was explicitly authorized in this attempt. A's original private
baseline and fixture, full snapshot ownership/delta proof, live process chain,
container/mount/destination and pinned file hashes/ACL/non-link paths were
revalidated. The E2E controller remained blocked. Only a read-only ownership
diagnostic used a quote-free stdlib expression; it did not replace the failed
gate or send a request. One exact four-row cleanup transaction restored the
baseline before resource removal. The normal nine-row cleanup was not used.
All DB observations preceded removal; no original-repository DB helper was
called afterward. No personal DB/settings/mapping/volume was accessed.

This attempt changes only execution records, not the probe or implementation.
A separately reviewed native-argument quoting correction and real PowerShell
5.1 command-transport check are needed before another approved fresh attempt.
Do not resume this stopped run. Actual M18 model/HTTP acceptance remains
incomplete at that stop; no staging, commit or push was performed.

### Fifth attempt — isolated actual Ollama HTTP E2E PASSED (2026-10-12)

**Status: PASSED; exact synthetic cleanup and owned resource removal COMPLETE.**
This was one newly approved run with a fresh PowerShell 5.1 A session, new
Run ID and new disposable source/configuration/database. The four earlier
stops and their cleanups remain separate historical attempts above.

Before E2E resource creation, the native probe was changed from quoted
inline Python `-c` source to a pinned `interpreter_probe.py` file. The exact
runbook `Invoke-M18InterpreterProbe` function ran under Windows PowerShell
5.1 using the designated virtual-environment launcher, `-I -B`, a path
containing spaces and separately captured stdout/stderr. Fifteen native,
process-pair and offline UTF-8 assertions passed: normal JSON/path output,
wrong launcher, changed file hash, nonzero exit, stderr on zero exit,
invalid JSON, wrong launcher/base output, both allowed process images,
wrong process/base combinations and English/Korean byte-array bodies.
All 15 PowerShell blocks passed AST checks. The offline harness initially
stopped while preparing its ACL, before Python execution; using the same
SID-based `icacls` preparation as Section 1 fixed that harness setup. Both
offline roots were verified and removed. This did not start an E2E attempt
or relax a process/source/connection predicate.

Sections 5–9 contain no other inline native Python source. Helper calls
remain pinned absolute `.py` invocations with private UTF-8 JSON on stdin;
their actual transport was exercised by this run's proofs and cleanup.
The file probe and unchanged ownership predicate also passed against each
real server process, including both restarts. Probe/source/manifest/settings
hashes were rechecked; no original-repository helper was used afterward.

| Fifth-attempt check | Actual result |
| --- | --- |
| Sections 1–4: Git, source, settings, container and connection | PASS; expected eight paths/no staging; owned PostgreSQL 17 tmpfs, exclusive loopback port and synthetic DB/role; no private configuration copied |
| Migration 001–014, FK/CHECK/index catalog and baseline | PASS in disposable DB only; complete empty 21-table counts/private fingerprints captured in A |
| Minimal fixture and document | PASS; exact synthetic user/token/project/read-only membership four rows and one small Markdown |
| Section 5 real native/process/current-model gate | PASS; owned loopback NOAH and dedicated Ollama `127.0.0.1:11435`, installed `gemma4:12b-it-qat`; no pull or model replacement |
| Section 6 registration | One POST, HTTP 201 `task_registered`; one ready/pending Task and definition; Execution 0; model/file/mapping calls 0 |
| Section 7 first restart and inspection | One GET, HTTP 200; same ready Task and definition; new inspection request ID; exact DB snapshot unchanged |
| Section 8 explicit execution | One POST, HTTP 200 `task_executed`; actual grounded outcome `supported`; same Task, exactly one Execution |
| Terminal Evidence/result | PASS; completed/passed Task, succeeded/verified Execution; one read and one answer Evidence; exact request/binding/project/document identity, SHA-256, UTF-8/BOM, quote text and Unicode `[start,end)` positions |
| Section 9 second restart and historical inspection | One GET, HTTP 200; same execution and historical result; `temporal_scope=execution_observation`; DB snapshot unchanged |
| Application operation counters | Model 1, safe read 2, mapping 2 after execution; unchanged by historical GET or restarts; registration and ready GET had all 0 |
| Section 10 cleanup ownership and transaction | PASS; exact nine synthetic rows verified, deleted once in one SERIALIZABLE transaction in documented FK order; before-commit and fresh after-commit checks matched baseline |
| Final isolated baseline | All 21 table counts/private fingerprints exactly restored; no Task/Execution or unexpected durable test state remained |
| Section 11 resource/environment checks | PASS; exact owned container, source/probe/fixture files and empty root removed; owned NOAH/11435 stopped; ordinary 11434 listener/process and Git status matched preflight |
| Business HTTP counts | Registration POST 1 (201), run POST 1 (200), Task GET 2 (200 each); no repeated POST, response loss or unknown commit observed |

The dedicated tags GET was one environment check; the real answer-model
invocation was exactly one. There was no Router/Session request. The read-only
helpers' synthetic-file hash checks are separate from the application's
counted read path. Safe success readback verified committed coherence;
rollback, commit uncertainty, races and revocation were not manually injected
and remain automated-test evidence. This run did not manually test bounded
Task listing, unsupported outcomes or concurrent execution claims.

No personal PostgreSQL/container/named volume/settings/mapping was inspected,
connected, copied or changed. That protection was established by pinned source
and connection isolation, not a private fingerprint comparison. Ordinary
Ollama 11434 received no request and was not controlled. All DB observations
finished before the owned container/source removal. No fifth-run temporary
resource remains. Personal DB migration/deployment and Git staging/commit/push
remain unperformed and require separate approval. The implementation,
migrations, approved functional contract and automated test results are
unchanged; only this procedure and the execution record in `56` were updated.
