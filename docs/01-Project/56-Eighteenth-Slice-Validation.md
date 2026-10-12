# M18 Automated Validation — Durable Document Task Intake

> Status: **stage-1 implementation and deterministic automated validation passed**.
> Executed: 2026-10-11.
> Contract: `55-Eighteenth-Vertical-Slice.md`; repository baseline
> `main@f83ae156aa70103d5e7d404469f4be0c42c7d299`.
> Isolated operator attempts on 2026-10-12: first **STOPPED at Section 1
> before resource creation**; second **STOPPED at Section 2's storage gate**.
> Third isolated attempt on 2026-10-12: **STOPPED at Section 5's NOAH process
> identity gate**, before any HTTP request or model invocation. Sections 1–4
> passed, including isolated migrations, baseline and four-row fixture.
> Third-run exact-owner four-row cleanup and full isolated baseline restoration
> were subsequently approved and completed; all third-run resources removed.
> The prior Section 2 verifier repair and second-run cleanup remain complete.
> Fourth isolated attempt on 2026-10-12: **STOPPED at Section 5's native
> interpreter probe** (PowerShell 5.1 argument quoting); HTTP/model calls zero.
> Approved safe abort cleanup restored the original isolated 21-table baseline
> and removed all fourth-run owned resources; HTTP acceptance was incomplete at that stop.
> Fifth isolated actual Ollama HTTP E2E on 2026-10-12: **PASSED** after the
> native file-probe correction and actual PowerShell 5.1 preflight. Registration
> 201, ready inspection 200, explicit execution 200 (`supported`), historical
> inspection 200; exact nine-row cleanup and empty 21-table baseline restored.
> Owned temporary resources were removed; earlier four attempts remain historical.
> This validation record precedes final Git closeout; verify final commit/push
> state from Git. Personal-DB deployment was not performed.

## Implemented boundary

The four dedicated APIs register, list, inspect, and explicitly run an
independent `project.document.question` Task:

| API | Implemented behavior |
| --- | --- |
| `POST /tasks/document-questions` | One ready/pending Task and immutable definition; no Execution, file read, model call, or Routing Audit |
| `GET /tasks` | Bounded owner/project-visible keyset listing, with visibility predicates before the SQL limit |
| `GET /tasks/<id>` | Authorized committed state and historical result reconstruction; no model, file, or mapping read |
| `POST /tasks/<id>/run` | Explicit claim of the same Task and at most one Execution; bounded M7/M8 primitives and atomic terminal Evidence |

The registration/readback contract was minimally clarified: another explicit
run may commit between registration and readback. A coherent running or
terminal observation is valid. The response's `registration` facts describe
the confirmed intake transaction; its Task/Execution/result describe the
readback snapshot. No Task is recreated or rolled back to ready.

Implementation paths are `noah/document_task.py`, `noah/__main__.py`,
`noah/db.py`, `database/014_document_question_tasks.sql`, and
`tests/test_document_task.py`. This record and the Minor clarification in
the M18 contract and the isolated manual procedure in `57` are the additional
document paths; later execution records do not change the implementation.

## Persistence, claims, and result truth

Migration 014 adds `ready` to the existing Task status CHECK, adds one
kind-specific definition table, and adds an owner/time/ID listing index.
It does not rewrite existing rows or change Execution status domains.
The definition's three FKs reference Task, project, and Execution with
`ON DELETE NO ACTION`. Catalog inspection verified the exact tables/columns,
deletion behavior, Task states, and index in the disposable database.
Migration reapplication with synthetic rows also preserved their contents.

READ COMMITTED claim transactions lock the owned Task first, then freshly
validate its definition, authority, state, and zero/one Execution relation.
One running Execution, its definition binding, and the ready-to-running
transition commit together. No worker/model dispatch follows an unconfirmed
claim. Running and terminal Tasks refuse a second run.

The execution path reuses M7 safe reads and M8 Context/quote validation,
without calling the high-level function that owns another Task/Execution.
The read and answer Evidence rows and both success terminal updates share
one transaction. Definite failure recording is guarded against the same
claimed attempt. Unknown commit acknowledgements do not trigger compensation,
retry, or guessed failure. A stopped process leaves an observable running
attempt; it is not automatically resumed.

Stored results preserve all five M8 outcomes, including `partial`.
`temporal_scope=execution_observation` identifies historical Evidence,
not the current document. Fresh disclosure checks require the original
operation's credential, Task owner, and current project access. Revocation
after a success commit withholds the result without rewriting stored truth.

## Executed deterministic results

| Validation | Passed | Opt-in skipped | Failed/errors | Total |
| --- | --- | --- | --- | --- |
| M18 focused | 32 | 0 | 0 | 32 |
| Full M1–M18 | 243 | 10 | 0 | 253 |
| Existing M1–M17 within the full run | 211 | 10 | 0 | 221 |

The focused suite directly verifies:

- Exact intake, normalization, zero registration Execution/Evidence/Audit,
  authentication, request/header/query rejection, and known-credential guards.
- Bounded listing, owner/project non-enumeration, final page disclosure,
  and exclusion of legacy Tasks from M18 APIs.
- Registration readback after both running and terminal advancement.
- Two competing runs using real PostgreSQL row locks and blocking-PID
  observations, with events controlling commit order and one model attempt.
- Token revalidation after a Task-lock wait, permission loss during model
  work, token loss before terminal Evidence, and disclosure loss after commit.
- All five answer outcomes, production safe-read worker execution, exact
  quotes/positions/hash, Context limits, malformed quotes, and changed files.
- Ready and terminal inspection from fresh Python processes, historical
  retrieval after deleting the synthetic file, and offline HTTP parsing.
- Process termination after a confirmed claim, retained running state,
  refusal to reexecute, corrupt stored relations, and malformed stored quotes.
- Registration/claim rollback, readback unavailability, genuine Evidence
  transaction rollback, and acknowledgement loss after real registration,
  claim, success, and failure commits. No automatic redispatch occurs.
- Connection failure before claim remains `DATABASE_UNAVAILABLE`, distinct
  from lock/statement timeout handling.

An initial development run exposed two test-harness issues: a list assertion
matched the word `question` inside the task-kind value, and an unguarded
temporary runner reentered under Windows multiprocessing spawn. Both were
corrected before the final 32-test focused and 253-test full runs. The initial
run also restored its disposable baseline; it is not the reported final pass.

## Isolation and cleanup evidence

Tests used an allowlisted temporary source copy, synthetic configuration
and mapping, and a separate PostgreSQL 17 container with tmpfs-only storage
and an owned loopback port. No `.git`, personal configuration, mapping,
document, or database dump was copied.

A process-start and per-connection gate checked the loaded module root,
configuration identity, database name/user/port, and actual connection
destination. It rejected original-source loading and use after source-copy
removal. Actual Ollama calls were explicitly blocked; all opt-in flags were
disabled. Existing automated HTTP fixtures belong to regression tests, not
an operator HTTP E2E or an existing NOAH service.

Both final runs captured the disposable 21-table baseline in private runtime
memory. All table counts and row fingerprints matched it after each run;
running Tasks and Executions were both zero. Fingerprints, passwords, and
tokens were not printed or recorded here.

The container ID/ownership label, tmpfs-only mount, and loopback binding were
rechecked before stopping and removing that container. Only the verified
run-owned scratch files and empty directories were removed, without recursive
filesystem deletion. No temporary source/configuration from this run remains.

The existing personal PostgreSQL, named volume, private settings/mapping,
ordinary Ollama 11434, and existing NOAH services were not accessed or changed.
No private-environment fingerprint comparison is claimed: protection was
provided by destination/source isolation, not by connecting to that database.
Migration 013/014 application to the personal database remains unperformed.
M17's separately recorded environmental limitations are unchanged.

## Historical acceptance and Git state before final closeout

Independent implementation review found Critical 0 / Major 0 / Minor 1.
The Minor concerns the contract's historical pre-implementation status text;
its functional contract and the implementation were not changed.

The first approved isolated operator attempt on 2026-10-12 stopped in
Section 1 of `57`, at the Git changed-path comparison. Under Windows
PowerShell 5.1, the newline between the two positional `Compare-Object`
arguments ended the invocation before `DifferenceObject` was bound.
It raised `ParameterBindingException` for the missing mandatory parameter.
The earlier AST syntax check had accepted the text, but did not exercise
runtime parameter binding. The section was not rerun and its verifier was
not bypassed or corrected during this attempt.

Separate read-only Git inspection confirmed main/HEAD/origin/main remained
at the baseline with the expected eight M18 paths and no staged files.
No Run ID, temporary root, container, baseline snapshot, synthetic fixture,
server, or dedicated Ollama was created. No PostgreSQL connection/migration,
model call, business HTTP request, or cleanup transaction was performed.
Existing personal PostgreSQL/settings/mapping, named volumes, ordinary
Ollama, and existing NOAH services were not accessed or changed by the attempt.
There were no first-attempt synthetic rows or disposable resources to remove.

For the separately approved second attempt, both multiline `Compare-Object`
expressions in `57` were changed to one-line explicit `-ReferenceObject` /
`-DifferenceObject` calls, preserving the same sorted arrays and STOP checks.
The actual expressions were executed under Windows PowerShell 5.1 with
synthetic identical, missing, and unexpected-extra arrays: all six checks
passed without binding errors. All 15 blocks also passed AST validation.

The second run used a fresh Run ID and passed Section 1. Section 2 created
an allowlisted source copy, synthetic settings/empty mapping, and a separate
PostgreSQL 17 container, then stopped at `Assert-M18Container` before
readiness polling, helper creation, migration, baseline capture, or fixture
creation. No DB connection, model call, or HTTP request was performed.

Read-only inspection of that exact owned container confirmed the expected
ID/image/label and loopback port. The `--tmpfs` configuration was present at
`HostConfig.Tmpfs` for `/var/lib/postgresql/data` with `rw,size=1g`, while
Docker returned `Mounts=[]`. The runbook required one tmpfs entry in `Mounts`,
so its storage verifier rejected a different valid metadata representation.
PowerShell 5.1 additionally retained the top-level JSON array inside
`@(ConvertFrom-Json ...)`; its nested empty Mounts array produced a misleading
count of one with null Type/Destination. These are procedural verification
issues, not evidence of an M18 execution/model/DB failure. No check was
weakened and no further correction or retry was made during this run.

At the second-run STOP, the container and restricted temporary copy were
preserved; no stop/removal, filesystem deletion, or DB cleanup was attempted
during that run. The separately approved later cleanup is recorded below.
No NOAH 8080 or dedicated Ollama 11435 was started. Listener inspection found
those ports absent and the isolated PostgreSQL loopback port present;
ordinary 11434 was inspected only for listener metadata, never called or
modified. No existing PostgreSQL/settings/mapping/named volume was accessed.
The empty 21-table baseline was not established, so no baseline restoration
is claimed. No NOAH migrations or synthetic application rows were created.

No actual M18 model answer or operator HTTP request has been executed.
The isolated HTTP acceptance flow remains unverified:
register once, restart/read ready, explicitly run once, restart/read the
historical result, and verify exact synthetic cleanup/baseline restoration.
It must accept grounded `supported` or `partial` without retrying for success.

Race and commit-uncertainty checks above are deterministic fault-injection
tests, not live operator fault injection. No automatic recovery, Router
integration, Session dependency, planner, or new generic execution layer was
added. No unresolved contract change was needed beyond the approved intake
readback clarification. The binding error is corrected and dynamically
verified; the storage/JSON verifier correction and approved exact-owner
cleanup are now complete. A new isolated E2E still requires separate approval;
no M18 implementation or architecture change is inferred from this stop.
Staging, commit, push, and personal deployment remain unperformed.

## Section 2 verifier correction and approved residual-resource cleanup — 2026-10-12

This was a procedural repair and abort cleanup, not another E2E attempt.
The Section 2 gate now parses Docker's JSON root array directly under
PowerShell 5.1 and verifies exact container ID/name/image/run label before
any owned-container `exec`. It checks the exact `HostConfig.Tmpfs` data path
and options, matching PGDATA, no unexpected volume/bind mount or shared
network, and the sole loopback port. `/proc/self/mountinfo` must prove one
writable tmpfs mount at the PostgreSQL data directory. An empty `Mounts`
array is accepted only alongside those independent checks. The embedded
per-connection helper had the same invalid one-entry assumption; its storage
gate was minimally synchronized to the same invariant. No application,
migration, contract, or production test changed.

Actual Windows PowerShell 5.1 execution passed two valid representations
(empty `Mounts` and an optional matching tmpfs entry), 17 rejection cases,
and the Docker JSON-root/empty-array normalization check: **20 passed**.
The rejection cases covered missing/wrong tmpfs configuration, wrong PGDATA,
missing/non-tmpfs/read-only actual mount, volume/bind configuration, wrong
ID/label/name/image, non-loopback/wrong/multiple port bindings, and shared
container networking. All 15 PowerShell blocks passed AST parsing. The
embedded helper parsed as Python and its extracted storage gate passed
11 offline synthetic cases without application imports, DB connections,
Docker mutations, HTTP, or model calls. These checks do not replace or rerun
the previously recorded M18 automated suite.

Read-only inspection of the exact second-run container confirmed its
recorded identity, PostgreSQL 17 image, `bridge` network, and loopback port.
`HostConfig.Tmpfs` contained only `/var/lib/postgresql/data:rw,size=1g`,
PGDATA matched that path, and actual mountinfo reported writable `tmpfs`
with size `1048576k`. `Mounts=[]`; no volume/bind was attached. The repaired
PowerShell gate passed against this actual observation before cleanup.

The preserved blocked PowerShell A state confirmed no fixture, baseline,
registration/run POST, server, or dedicated Ollama attempt. Exact manifest
identity, UTC-normalized creation times, restricted current-user ACL,
non-reparse root/ancestors/entries, and the complete file/directory allowlist
were checked. All public source/migration hashes matched the manifest and
reviewed source; synthetic configuration matched only this owned container;
the temporary mapping was empty. No helper, document, fixture, private
configuration, dump, or unexpected file was present. An auxiliary timestamp
check initially mixed local time with UTC; normalization confirmed matching
creation records before any deletion. No mismatching resource was removed.

Under this cleanup approval, the exact owned container was stopped normally
once and removed once, without force or volume deletion. Its 40 verified
files, five empty subdirectories, and exact empty root were removed by
literal paths without recursive filesystem cleanup. Container and root
absence were confirmed; the preserved A process then exited normally.
There are **no remaining resources from this stopped second run**. No DB
DELETE or NOAH schema operation was performed: migrations and application
fixtures had never been reached. No 21-table baseline had been captured,
so baseline restoration is not claimed for this partial setup.

Listener inspection confirmed 8080, 11435, and the owned DB port absent
following cleanup. Ordinary 11434 listener addresses/process identity stayed
unchanged, and Git status was unchanged during cleanup. The existing personal
PostgreSQL, named volume, private configuration/mapping were neither inspected
nor connected to; no private-environment fingerprint check is claimed.
No new HTTP E2E, migration, actual Ollama invocation, test-suite rerun,
staging, commit, or push occurred. The corrected runbook is ready for a
separately approved fresh isolated attempt, subject to its unchanged gates;
actual M18 operator/model acceptance remains **NOT RUN**.

## Third isolated operator attempt — STOPPED at Section 5 (2026-10-12)

This separately approved attempt used a fresh Windows PowerShell 5.1 A
session, new Run ID, source copy, synthetic settings/mapping, and a different
owned PostgreSQL 17 tmpfs container. It did not reuse the previous run.
Sections 1–4 passed: main/HEAD/origin baseline, expected eight changed paths,
no staged files, free ports, restricted root, exact container ID/name/image/
label, actual writable data tmpfs, no volume/bind mount, and sole loopback
binding. The pinned helper checked source/module/configuration and owned
container identity before connecting only to the isolated database.
Migrations 001–014, catalog checks, and the empty 21-table private count/
fingerprint baseline passed. One synthetic user/token/project/read-only
membership and one small synthetic Markdown were created and verified.
The baseline, credentials, captured fixture and once-only flags remain only
in the preserved A runtime; no fingerprint or token is recorded here.

Section 5 started only this run's dedicated Ollama 11435 and NOAH 8080.
Ollama's exact process/parent/user/loopback ownership check passed. NOAH's
check then raised `Owned process identity not proven`. Read-only diagnosis
compared its owner record with the listener process: run label, PID, parent
PID, current user, helper entry path and loopback binding matched. Its actual
executable was the base interpreter launched by the Windows virtual-
environment Python launcher, whereas the runbook expected the launcher
executable itself. Executable equality was false. The condition was neither
relaxed nor corrected during this attempt; the gate was not rerun.
The helper's server-start connection had checked the isolated source and
DB destination before binding. This observation is not a completed HTTP
or model acceptance test and does not establish an approved replacement
process-identity rule.

| Third-attempt check | Actual result |
| --- | --- |
| Git/fresh environment/container/storage gates | Passed Sections 1–2 |
| Helper module/configuration/connection isolation | Passed; no original-source DB helper used |
| Migration 001–014/catalog/empty 21-table baseline | Passed; isolated database only |
| Four-row synthetic fixture and document | Created; read-only exact fixture proof passed |
| Dedicated Ollama ownership | Passed; no tags/model invocation reached |
| NOAH ownership | STOP at executable-path comparison; other inspected owner fields matched |
| Registration POST / run POST / Task GET | 0 / 0 / 0; not sent |
| Ready Task / restart / Execution / terminal Evidence / stored result | Not reached; no application answer observed |
| Model/file/mapping operation counters | No counter file created; no counted operation observed |
| Cleanup / 21-table restoration | Not attempted; baseline and four-row fixture preserved |
| Services/resources | Owned NOAH 8080, Ollama 11435, container and source remain; no stop/removal retry |

No application code, migration, contract, or process gate was changed.
No POST was repeated, no automatic cleanup was attempted, and no commit or
HTTP uncertainty was observed. At that STOP the controller was blocked and retained the
private baseline and exact fixture for separate ownership review/cleanup
approval; the later approved cleanup is recorded below. The existing personal PostgreSQL, named volume, private settings/
mapping were not accessed; ordinary Ollama 11434 was not called or changed.
No private-environment baseline comparison is claimed.

The Windows launcher/process gate was subsequently corrected and the
approved exact-owner third-run cleanup completed (below). A new explicit
E2E approval is still required before another attempt. Actual M18 HTTP/model
acceptance remains unverified. No architecture or implementation defect is
inferred from this procedural gate failure. Staging/commit/push and personal
migration deployment remain unperformed.

## Process verifier correction, third-run abort cleanup and offline preflight — 2026-10-12

This approval covered the preserved third run's cleanup and procedural
verification only; no new isolated environment, migration, HTTP E2E or
actual model invocation was performed.

The preserved A process and its original private baseline, token, fixture
and once-only flags were accessed in that same runspace without printing
secret values. The E2E controller stayed blocked: no request stage resumed.
Read-only proof matched all 21 tables to the original four-row fixture
snapshot, including exact labels/token ownership/read-only membership,
unchanged document/mapping, and zero Task/Execution/Evidence/Audit/model
operations. Manifest/helper/settings/document/mapping hashes were checked
against A's captured values. Current container ID/image/label, writable
actual tmpfs, loopback destination, live PID/parent/user/helper command,
stdlib-probed base interpreter, restricted ACL, all code hashes and the
complete non-reparse temporary file/directory set passed before cleanup.

The owned NOAH was stopped through its foreground Ctrl+C; exact PID/8080
absence was confirmed. A reviewed one-time partial cleanup helper was added
only to that existing owned copy. It reused A's original private values,
rechecked full fixture proof in one SERIALIZABLE transaction, and deleted
exactly one membership, project, token and user in that order. Each precise
WHERE/RETURNING had to delete one row. Counts/private fingerprints matched
the original empty 21-table baseline before commit and in fresh read-only
observations after commit. A independently compared its original baseline
JSON with the post-cleanup snapshot. No guessed values, broad deletion,
recovery retry or normal nine-row E2E cleanup was used.

The exact owned container was then stopped normally and removed once without
volume flags. Dedicated Ollama's current process ownership was rechecked,
and only that foreground 11435 process received Ctrl+C. Both owned PIDs and
8080/11435/DB-port listeners were absent. Ordinary 11434 listener addresses
and process identity matched A's original preflight record. A left the
source cwd before deletion. Exactly 45 owned files (including the one-time
cleanup helper), six empty subdirectories and the exact empty root were
removed using literal paths without recursive deletion. A's private payload
was cleared and the control/inspection sessions exited. **No third-run
resource remains.** No DB helper was invoked after container/source removal.

Section 5 now accepts only the pinned Windows virtual-environment launcher
or the base interpreter returned by an isolated stdlib-only `sys`/`json`
probe of that exact launcher. It does not accept arbitrary Python paths.
Existing listener PID/parent/user/creation/command/loopback guards remain.
The related server helper records launcher/runtime, source/module/configuration
roots, helper SHA-256 and the already verified isolated DB destination after
importing the HTTP entry point and rechecking all loaded NOAH module origins.
The process checker binds this record to the hashed copy and expected
synthetic DB. It is rerun against fresh ownership metadata on each restart.
No production implementation, migration or contract semantics changed.

Performed offline verification, distinguished from real E2E:

| Check | Actual result |
| --- | --- |
| Windows PowerShell 5.1 process metadata | 27 passed: valid base/launcher/Ollama images and rejection of wrong image, forged runtime, PID/parent/run/user/creation/entry/arguments, non-loopback/multiple owners, original source/config/module root, wrong helper hash and DB identity |
| UTF-8 JSON bodies | 3 passed: English/Korean registration and empty run object return a single System.Byte[]; no HTTP |
| Remaining Sections 6–9 | Exact blocks executed using in-memory HTTP/helper/process doubles; planned two POST/two GET parameter bindings and duplicate-POST rejection passed; real request count zero |
| Private baseline serialization/path normalization | 3 passed: 21-table JSON/empty-array roundtrip, changed-count detection, Windows Join-Path normalization |
| Extracted Python proof | 10 synthetic in-memory cases passed: fixture/ready/inspection/supported/partial/historical plus ownership/quote/hash/binding rejection; no DB or filesystem fixtures |
| Static checks | All 15 PowerShell blocks parse; full embedded helper Python syntax valid; API fields/SQL columns/FK cleanup order cross-checked against implementation and migrations |

The offline bodies and rows are synthetic test doubles, not observed M18
HTTP/model results or an additional run of the automated suite. No further
procedural error was identified in this bounded preflight. Actual process
startup with the corrected ownership record, real model output, both server
restarts, terminal Evidence and historical GET remain to be verified by a
separately approved fresh isolated E2E. Existing deterministic 32 focused /
243 full passed / 10 opt-in skipped results were not rerun here.

The existing personal PostgreSQL, named volume, private configuration and
mapping were neither accessed nor changed. No private-environment DB baseline
comparison is claimed. No model/tags/business HTTP request, migration rerun,
staging, commit or push occurred. Actual M18 model/HTTP acceptance and
personal deployment remain incomplete; process correction and third-run
cleanup are complete.

## Fourth isolated attempt — Section 5 native probe STOP and safe cleanup (2026-10-12)

A new Run ID, Windows PowerShell 5.1 A session, allowlisted source copy,
synthetic configuration/mapping and PostgreSQL 17 tmpfs container were used.
The previous three attempts and their separately recorded cleanups are not
combined with this attempt into a successful E2E. Sections 1–4 passed:
main/HEAD/origin baseline and expected eight paths/no staging, free isolated
ports, exact owned container/image/label, actual writable tmpfs and exclusive
loopback port, pinned module/configuration/destination gates, migrations
001–014/catalog, empty 21-table private baseline and four-row synthetic
fixture with one small Markdown. Connections used only the owned loopback
port 57838, synthetic database `noah_m18_e2e` and role `m18_synthetic`.
No existing PostgreSQL/container/volume/configuration/mapping was inspected.

The dedicated Ollama and NOAH processes started. Ollama's process ownership
check passed. NOAH's stdlib interpreter probe then raised:
`NameError: name 'launcher' is not defined`, followed by
`Pinned interpreter probe failed`. Under actual PowerShell 5.1 native
`python -c` argument transport, the JSON key double quotes were lost and
`launcher` was interpreted as a Python name. The earlier 27 metadata tests
exercised the pure process predicate; they did not exercise this native
probe's argument quoting. The gate was not changed, rerun or bypassed.
No POST, Task GET, tags GET or actual answer-model invocation occurred.
No task registration, ready inspection, run claim, answer/Evidence or server
restart behavior was exercised. No commit uncertainty or response loss was
observed; the setup fixture had been confirmed by read-only proof.

Read-only ownership diagnosis confirmed the live server PID/parent/user,
helper hash/entry, source/module/settings roots and previously verified
isolated DB identity against its current ownership record. A quote-free
stdlib-only interpreter identity query was used solely for cleanup ownership
diagnosis, not to repair/reexecute the failed E2E gate. The original A state
and exact fixture were retained; full 21-table fixture proof and pinned
manifest/helper/settings/document/mapping hashes matched the captured values.
The root and all entries had the expected owner/restricted ACL, no links or
escaping paths, and the exact allowlisted public/synthetic contents.

This request explicitly permitted safe owned-resource cleanup after a stop.
Only after those proofs passed was the owned NOAH stopped with foreground
Ctrl+C and its exact listener/PID absence confirmed. A one-time partial
cleanup helper inside the existing owned copy received A's original baseline,
fixture and token privately through stdin. In one SERIALIZABLE transaction,
it repeated complete fixture/delta proof and deleted exactly one membership,
project, token and user by precise ID/label/hash/ownership predicates. Each
DELETE RETURNING had one row; snapshots before commit and fresh observations
after commit matched the original empty 21-table counts/private fingerprints.
A independently compared the captured original baseline with the restored
snapshot. No guessed values, broad deletion, normal nine-row cleanup,
unconfirmed commit retry or additional fixture were used.

The exact owned tmpfs container was stopped normally and removed once,
without volume flags. The dedicated Ollama's current ownership was rechecked
before its foreground Ctrl+C. Owned 8080/11435/DB-port listeners and PIDs
were absent; ordinary 11434 listener addresses/process identity matched A's
preflight record. A left the source cwd, then exactly 45 owned files (including
the partial cleanup helper), six empty subdirectories and this exact root
were removed by literal paths without recursive deletion. Private payloads
were cleared and control/inspection sessions exited. **No fourth-run resource
remains.** No DB helper was called after container/source removal.

| Fourth-attempt acceptance | Actual result |
| --- | --- |
| Isolated source/config/container/DB gates | Passed Sections 1–4; original personal environment not used |
| Migration/catalog/empty 21-table baseline | Passed; only the owned disposable DB |
| Four-row fixture/document | Created and verified, later exactly cleaned |
| Dedicated Ollama/NOAH startup | Started; Ollama ownership passed; NOAH native probe STOP |
| Register POST / run POST / Task GET | 0 / 0 / 0; no HTTP status or answer outcome observed |
| Model invocation / tags GET | 0 / 0; installed-model tags gate not reached |
| Ready/restarts/one Execution/terminal Evidence/historical GET | Not reached |
| Safe abort cleanup | One four-row transaction; original 21-table baseline restored |
| Temporary resources and ordinary 11434 | Owned resources absent; ordinary listener/process unchanged |

Permanent changes in this attempt are execution records in `56`/`57` only.
The production implementation, migrations, contract and process/probe command
were not modified. No automated suite rerun, model replacement/pull, personal
DB deployment, staging, commit or push occurred. No private baseline
comparison or universal environmental immutability is claimed: protection
was through never accessing the private DB/settings/mapping/volume.

Before a new E2E, the native interpreter probe needs a separately reviewed
PowerShell 5.1 quoting correction and actual command-transport validation.
A quote-free `dict(launcher=..., base=...)` expression or stdlib stdin probe
is a possible minimal correction; neither is applied to the runbook here.
Any new isolated HTTP E2E requires separate approval. Actual M18 HTTP/model
acceptance remained **NOT COMPLETED at this fourth-run stop**; this stop is not a model or task failure.

## Native file probe and fifth isolated HTTP E2E — PASSED (2026-10-12)

The separately approved correction is procedural only. A hashed stdlib
`interpreter_probe.py` file replaces the quoted inline `python -c` command.
The runbook's exact `Invoke-M18InterpreterProbe` invocation uses the pinned
launcher and `-I -B`, captures stdout/stderr separately and fails closed on
path/hash differences, nonzero exit, any stderr or invalid JSON/path pair.
PID/parent/user/creation/command/loopback checks, both allowed interpreter
images, loaded source/settings roots and isolated database identity remain
mandatory. Probe hashes are also checked at restart and final file cleanup.

Before E2E, actual Windows PowerShell 5.1 execution passed 15 native/offline
assertions, including normal output, wrong launcher/base, tampered hash,
nonzero exit, stderr despite zero exit, invalid JSON, allowed/denied process
image combinations and English/Korean `System.Byte[]` bodies. Its probe file
path contained spaces. All 15 runbook PowerShell blocks parsed successfully.
The offline harness's first ACL preparation failed before native execution;
the runbook's SID-based `icacls` method corrected that harness setup. The
two owned offline roots were removed. No DB, HTTP or Ollama was used for
preflight. Sections 5–9 have no remaining inline native Python source;
actual pinned-helper/stdin transport subsequently passed in the E2E.

A new Run ID and fresh PowerShell A state were used. Sections 1–11 completed
with an allowlisted temporary implementation copy, synthetic configuration
and mapping, and an independently owned PostgreSQL 17 tmpfs container.
Destination gates ran before every DB helper/connection: copied module
root, synthetic settings path, pinned container ID/label/image/mount,
loopback port 57838, synthetic database/role and actual connection identity.
Migrations 001–014 and exact catalog checks applied only to that empty DB.
Its full 21-table baseline remained private in A. Existing personal DB,
named volume and settings/mapping were not inspected or used.

| Fifth isolated E2E acceptance | Actual result |
| --- | --- |
| Native and real process/model gates | Passed before requests, including both server restarts; installed `gemma4:12b-it-qat` on dedicated `127.0.0.1:11435` |
| Registration | Exactly one POST, HTTP 201; ready/pending Task and definition only; Execution/model/file/mapping zero |
| First restart | Same Task inspection GET HTTP 200; exact definition/state and complete DB snapshot unchanged |
| Explicit execution | Exactly one POST, HTTP 200; grounded `supported`; same Task, exactly one Execution |
| Committed terminal state and Evidence | Completed/passed Task, succeeded/verified Execution, exact execution binding; one read and one answer Evidence; SHA-256/UTF-8/BOM and exact quote/Unicode positions verified |
| Second restart | Same historical result GET HTTP 200; same execution and `execution_observation` result; complete DB snapshot unchanged |
| No reexecution during stored-result read | Application counters remained model=1, safe_read=2, mapping=2; no new file/mapping/model call |
| Normal cleanup | Read-only exact nine-row ownership/delta proof, then one SERIALIZABLE delete transaction with exact RETURNING counts and FK order |
| Baseline restoration | All 21 original empty-table counts/private fingerprints matched before cleanup commit, after commit and final snapshot; no running Task/Execution |
| Resource removal | Owned NOAH/11435 processes stopped; exact tmpfs container and owned files/empty root removed; no fifth-run residue |
| Existing environment | Ordinary 11434 listener/process matched preflight; no request/service control; Git paths unchanged before documentation; no original DB helper after source removal |

Business HTTP totals were exactly two POSTs and two GETs: 201, 200, 200,
200 in planned order. One dedicated tags GET checked the environment and
one answer-model call performed the execution. No POST was repeated; no
response loss, commit uncertainty, unexpected outcome or cleanup failure
occurred. The four earlier stopped attempts remain separately recorded
above and in `57`; their results are not combined into this successful run.

This is isolated happy-path actual-model evidence, not personal-environment
deployment or manual race/fault injection. Concurrency, revocation, rollback,
process interruption and unknown acknowledgement guarantees remain the
existing deterministic automated evidence. Bounded listing and other answer
outcomes were not added to the manual run. The automatic suite was not rerun:
its recorded results remain focused 32 passed and full 243 passed, 10 opt-in
skipped, 0 failed. No production code, migration or approved functional
contract was changed by this native correction/E2E.

**Current acceptance:** M18 implementation, deterministic validation and
isolated actual Ollama HTTP E2E have passed; exact synthetic cleanup and
owned resource removal are complete. Final closeout review found Critical 0
and Major 0. The previously reviewed Minor in `55` was closed by distinguishing
its original baseline/plan from current validation status; no functional
contract changed. Final commit/push state and commit ID must be verified from
Git rather than inferred from this validation record. Personal DB migrations 013/014 and deployment
remain unperformed; no private baseline/fingerprint or universal environment
immutability is claimed. No secret, raw fingerprint, private data or dump
is recorded here.
