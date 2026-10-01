# M11 Controlled Read-Only Capability Routing — validation record

> Date: 2026-10-01 (Asia/Seoul).
> Baseline: `d410debd1c7251376a63895895e2df93099916cd` on `main`.
> Status: implementation, automated validation, and user manual HTTP E2E complete;
> M11 was subsequently committed on `main` at
> `b3f7200f1226414f13b6202ca2bfc3ef6d1c1205`.
> The tests and manual observations below predate that commit; this record
> does not claim that they were rerun afterward.

## Implemented boundary

`POST /requests/route` authenticates before routing-model exposure, accepts
one bounded question and an optional caller-supplied project UUID, and accepts
only the strict model choice `memory.query`,
`project.documents.answer.auto`, or `no_action`. The model cannot supply
arguments or execution authority. A provided project is checked for read
membership before the model call. NOAH invokes at most one existing internal
function, never another HTTP endpoint or a second capability on failure.

M3 `query_memory()` keeps its request-scoped response and no durable
Task/Execution. On successful M3 delegation, M11 rechecks the token and each
quoted Memory ID against the existing visibility predicate immediately before
disclosing the result. M10 `answer_auto_documents()` keeps its own single
Task/Execution, permission checks, and candidate/source/quote Evidence. The
router creates no Task, Execution, Evidence table, or common durable route
decision record. `no_action` is a completed routing decision with no delegated
work; delegated failure and uncertain outcome remain unchanged inside the
response's `result` body. M5 Recovery Triage remains `memory.save`-only.

The implementation added `noah/capability_route.py` and one explicit
`noah/__main__.py` POST branch. The latter uses duplicate-key rejection for
the M11 JSON request without changing the older endpoints' parsing contract.
No migration or new dependency was added.

## Data protection before automated tests

Docker Compose reported the existing `postgres:17` container running; no
Compose down, volume deletion, reset, or schema initialization was used for
M11. A read-only snapshot of all **17** `noah` tables was taken before test
data creation. Its baseline included users 1, API tokens 1, memories 2,
Tasks 2, Execution Records 3, and M4 write-key mappings 1. Projects,
memberships, and M6–M10 Evidence rows were 0, as were `running` Tasks and
Executions. Row fingerprints were computed in memory without displaying
tokens, passwords, or Memory content.

M11 tests created only named synthetic users, a synthetic project and
membership, synthetic Memory rows, and temporary `.md` files. Cleanup uses
the synthetic actor/project IDs and removes only their M10 Evidence,
Execution, Task, Memory, membership, token, user, and temporary files.

## Automated results

| Run | Result | Scope |
| --- | --- | --- |
| M11 dedicated default, final | **17 tests: 16 passed, 1 opt-in skipped; 0 failures/errors** | Authentication-before-model, strict request/model shape, extra arguments, minimum model Context, project access, Memory isolation, `no_action`, permission revocation, distinct model failures, actual M3/M10 internal delegation, Task/Execution/Evidence counts, malformed/duplicate HTTP JSON. |
| M11 dedicated with `NOAH_TEST_OLLAMA_M11=1`, before one additional deterministic Context test | **16 passed; 0 skipped/failures/errors** | The contract tests plus one actual Ollama test containing three separate public synthetic choices: Korean saved-Memory question → `memory.query`; Korean project-document question → `project.documents.answer.auto`; English write request → `no_action`. The existing `gemma4:12b-it-qat` settings and dedicated `127.0.0.1:11435` loopback listener were used. No runtime code changed after this run. |
| M1–M11 full regression, final | **133 tests: 125 passed, 8 opt-in skipped; 0 failures/errors** | All prior M1–M10 tests plus the final M11 tests. The skipped tests require separately enabled local Ollama flags; the M11 actual-model test was executed in the dedicated run above. |

The actual Ollama test asserts **routing selection quality** only. Separate
deterministic Compose tests exercise actual PostgreSQL Memory visibility,
M10 directory enumeration and safe-read, and M10's own durable result with
one Task, one Execution, and one parent Evidence row. Those automatic runs
alone did not establish a user-run HTTP E2E; the separate completed manual
run is recorded below.

The synthetic permission checks include an outsider denied before any model
call, a membership revoked during routing before M10 delegation, a token
revoked before M3 disclosure, and a project Memory membership revoked before
its quote could be returned. Failures preserve their original M3/M10 HTTP
status and body; a synthetic M10 `TOOL_OUTCOME_UNKNOWN` is not converted into
success or retried. A real M10 delegation created no M6–M9 nested execution or
Evidence as a result of the router. The new HTTP handler was also exercised
with malformed and duplicate-key JSON and a valid `no_action` request; the
valid request returned HTTP 200 without creating a Task or Execution.

## Post-test baseline and remaining limits

A second read-only snapshot matched the initial **count and SHA-256 row
fingerprint for every `noah` table**. Users 1, tokens 1, memories 2, Tasks 2,
Executions 3, and M4 mappings 1 remain; synthetic project, membership, and
M6–M10 Evidence counts returned to 0. `running` Task and Execution counts
are both 0. `config/project_documents.local.json` is absent and no M11
temporary document root remains. The existing PostgreSQL container and named
volume were preserved.

M11 has no durable route-decision audit, and M3 still has no durable
Task/Execution. The actual model may make a semantically wrong but schema-valid
choice; the allowlist and delegated permissions restrict what it can execute.
M3's literal word search and M10's filename-only document selection retain
their prior completeness limits. The local model cannot retract Context
already sent before a later permission revocation; NOAH withholds a result
whose current access check fails. No automatic fallback or retry was added.

## Separate user manual HTTP E2E and cleanup

The user completed the [M11 manual procedure](36-Eleventh-Slice-Manual-Validation.md)
against the live local server and dedicated model with public synthetic
Memory, project, and `.md` files. This is **separate from** the automated
results above:

| Routed request | User-observed result | Durable delta |
| --- | --- | --- |
| Memory Query | `memory.query`; grounded synthetic quote matched its Memory ID and source text. | 0 new Task/Execution/Evidence rows. |
| Project Document Auto Answer | `project.documents.answer.auto`; two selected sources, `outcome=partial`, two exact source-aware quotes. Read-only verification matched Unicode positions and content hashes. | Exactly one M10 Task/Execution pair plus its candidate/source/quote Evidence; no M6–M9 legacy Evidence attached. |
| No Action | `routing.outcome=no_action`; no delegated capability ran. | 0 new Task/Execution/Evidence rows. |

`partial` was retained as the actual M10 outcome. The verified source quotes
and provenance establish a successful **grounded two-source execution** under
the current M9/M10 contract; they do not prove complete semantic coverage of
the question. The document-route DB check also confirmed the parent Evidence,
two source observations, two quote rows, and one Task/Execution pair. After
the run, targeted cleanup removed only the synthetic fixture and execution
rows. The pre-run and final DB counts and private row fingerprints matched
exactly; the local mapping, files, and root were removed, and the PostgreSQL
named volume remained. Existing user/token/Memory/M1–M10 records were
preserved.

Two manual-procedure issues were resolved without changing runtime behavior.
The original `docker inspect --format` Go template failed in Windows
PowerShell 5.1 with `function "volume" not defined`; the operator checked the
named volume through `docker inspect | ConvertFrom-Json` and `.Mounts` filtered
by `Type=volume`, and the guide now uses that approach. A chat-delivered copy
of the read-only Python Evidence verifier replaced the guide's ASCII Unicode
escapes with Korean literals, causing a false `Animal quote missing fact` in
the PowerShell 5.1 stdin path. The operator reran **only that read-only
verifier** with the original escapes and passed against the already obtained
response and DB rows. The HTTP request was **not resent**. No new test or
runtime result is inferred from that verifier rerun.

M11 remains uncommitted. Manual success does not authorize private content
transmission or remove the routing-quality and durable route-audit limits
described above.
