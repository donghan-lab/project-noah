# M6 read-only Tool Execution validation

> 2026-09-28, existing Docker Compose PostgreSQL 17.10 and dedicated local
> Ollama. M6 tests used synthetic users, a synthetic DB project/membership,
> and temporary document roots. No actual user project was created.

## Automated results

- Initial M6 run: **16 dedicated tests**; default run **15 passed, 1 opt-in
  model test skipped**. The opt-in M6 model test then passed, and the initial
  full suite had **48 passed**.
- After the Windows PowerShell 5.1 compatibility changes: **18 M6 tests
  passed** and the full M1–M6 suite had **50 passed, 0 failed/errors/skipped**
  with both real local Ollama opt-ins enabled. The two new tests cover UTF-8
  BOM acceptance and malformed JSON/mapping rejection; the existing no-BOM
  mapping test remains in place.
- The HTTP route was exercised against a local server with an injected
  synthetic model and real PostgreSQL records. The M6 real model test used
  the service directly. No personal memory body or actual project file body
  was supplied to the model.

| Scenario | Result |
| --- | --- |
| Authentication and non-member rejection before model/Tool | Passed |
| Project member without write permission can read; malformed project ID rejected | Passed |
| Membership revoked before Tool; Tool never called | Passed |
| Membership revoked during Tool; listing withheld | Passed |
| Empty list, stable sorting, 50-entry limit and `truncated` | Passed |
| `.md` only, direct children only, dot-hidden and Windows hidden attribute exclusion | Passed |
| Symlink/reparse metadata exclusion | Passed (see limit below) |
| Unsupported/malformed model result, model unavailable/timeout | Passed |
| Unregistered/missing root, access denial, generic Tool failure | Passed |
| Fabricated filename rejected by independent observation | Passed |
| Confirmed Tool timeout vs unconfirmed termination | Passed |
| Completed Task, succeeded Execution, linked append-only evidence/hash | Passed |
| DB unavailable before model; safe error without credential details | Passed |
| DB lost after Tool observation; no durable-success claim or fabricated evidence | Passed |
| Local mapping without BOM and with UTF-8 BOM; malformed JSON and invalid mapping rejected | Passed |

The Windows account used for tests could not create a real symlink; that
specific filesystem fixture was unavailable. The test still exercised
reparse-point exclusion with synthetic Windows metadata and checked the
enumerator's no-follow path. A real junction fixture and a same-user race
test remain outside this slice's verified guarantee.

## User manual verification (separate from automated tests)

The user used one temporary synthetic project, read-only membership, and a
temporary document root with three public `.md` files and one `.txt` file.
The first Windows PowerShell 5.1 request for the natural Korean question
`이 프로젝트의 문서 목록을 보여줘` used `Content-Type: application/json` without a
charset. The Korean body was damaged during transmission and the model
returned `UNSUPPORTED_INTENT`; no Task, Execution, or Tool Evidence was
created. Adding `charset=utf-8` allowed the same Korean question to pass the
intent stage. A local mapping written with PowerShell 5.1
`Set-Content -Encoding utf8` contained a UTF-8 BOM and the original loader
returned `PROJECT_ROOT_CONFIG_INVALID`. Rewriting that mapping without a BOM
allowed the same question to execute `project.documents.list` successfully.

The API returned only `alpha.md`, `beta.md`, and `gamma.md`. `ignore.txt`, file
bodies, and the machine's absolute document-root path were absent from the
response. The user verified the response, linked completed Task, succeeded
Execution, Tool Evidence filenames/count/truncation, and result hash against
the database observation. The user then removed only the temporary project,
membership, Task, Execution, Tool Evidence, mapping, and document root. The
user's before/after check confirmed restoration of the existing row IDs and
counts. A separate read-only check after cleanup found **1 user, 1 token,
2 memories, 2 Tasks, 3 Executions, 1 M4 mapping, 0 projects, 0 memberships,
0 M6 Tool Evidence, and 0 running Tasks/Executions**; the local mapping file
was absent. The original root path was no longer available after mapping
cleanup, so that separate check could only confirm no matching temporary
directory remained under the expected temporary location.

The M6 operator guide now specifies `application/json; charset=utf-8` and a
BOM-free PowerShell 5.1 mapping example. The loader now accepts either UTF-8
form while keeping the existing JSON, mapping, and path validation. The
automated real-model M6 test calls the service directly; the successful
PowerShell-to-HTTP Korean request above is a user manual result, not an
automated test claim.

## Existing-data preservation

The `003_document_tool_evidence.sql` migration added only the evidence table.
Synthetic Task, Execution, project, membership, user, token, and evidence rows
were removed after tests. The existing Compose container and named volume
were not stopped, deleted, or initialized. A final read-only DB count showed
**1 user, 1 token, 0 projects, 0 memberships, 2 memories, 2 Tasks, 3 Execution
Records, 1 M4 key mapping, and 0 M6 evidence rows**. Running Task and
Execution counts were both **0**. These match the pre-M6 user-data state;
the user’s personal memories remain present.

## Scope and uncertainty

No API root path is accepted, no file body is read, and evidence/API output
uses a logical root identifier rather than a machine path. The `result_sha256`
is a digest of the recorded listing metadata, not a cryptographic proof that
the filesystem can never change. A DB acknowledgement loss may leave the
final record outcome unknown; M6 does not auto-retry or change such a Task.
M5 Recovery Triage remains `memory.save`-only.
