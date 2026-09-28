# M9 two-document grounded answering — validation

> 2026-09-29, Windows and the existing Docker Compose PostgreSQL 17. This
> records automatic synthetic tests and a separate user manual API check.
> Starting commit:
> `8843c6fcd251cb51e07e32c6e3243a049d0158ce`. The M9 work is not yet
> committed or pushed. No actual personal document was sent to a model.

## Implemented path checked

`POST /projects/<project_id>/documents/answer-selected` authenticates the
token and project membership, validates two ordered direct-child `.md`
basenames and one question, resolves the operator mapping, and reserves one
M9 Task/Execution. Before each read it rechecks access. The M7 internal
no-follow reader returns original bytes and file identity from the same
handle; NOAH verifies each observation through M7's independent read,
strict UTF-8/BOM, size and original-byte SHA-256 checks. D1 and D2 identities
must differ. After combined Context and permission checks, the dedicated
loopback Ollama receives both texts as untrusted data with no Tool channel.
NOAH accepts only bounded `{outcome,evidence:[{source_id,quote}]}` and checks
each quote against the claimed source. It calculates first `[start,end)`
Unicode positions and assembles the response. One final PostgreSQL transaction
inserts parent, two source, and zero-to-three quote Evidence rows and marks
the Task `completed/passed` and Execution `succeeded` with `verified_at`.
Permission is checked again before response disclosure.

The chosen file identity is `(volume serial, file index high, file index
low)` on Windows, or `(device, inode)` on POSIX. Exact/case-folded duplicate
names are rejected before reservation. A real hard-link alias was rejected
after no-follow opens. Missing or malformed file identity fails closed.
M7/M8 single-document Evidence tables and external APIs were not repurposed.

## Model and Context limit

The dedicated `127.0.0.1:11435` Ollama listener was observed as loopback
only. Its current `gemma4:12b-it-qat` configuration uses `num_ctx=4096`,
`num_gpu=0`, and a 512-token M9 output allowance. This is a validated
current configuration, not a permanent model choice. No settings of the
separate `11434` service were changed.

| Synthetic sources | Combined decoded UTF-8 bytes | Observed time | Result |
| --- | ---: | ---: | --- |
| Korean + Korean | 1,809 | 14.8 s | HTTP 200; `partial`; verified D1 and D2 quotes |
| English + English | 1,817 | 14.0 s | HTTP 200; `partial`; verified D1 and D2 quotes |
| Korean + English | 1,830 | 14.7 s | HTTP 200; `partial`; verified D1 and D2 quotes |
| English + English at exact boundary | 2,048 | 13.7 s | Full messages 3,153 bytes; `partial`; two verified source quotes |

The first three rows came from the opt-in M9 integration test in the final
suite; the exact-boundary row came from a separate synthetic model probe.
The model's `partial` label is reported as returned. NOAH verifies source
coverage and literal quotations; the label does not certify semantic
adequacy. The first M9 limit is **2,048 decoded UTF-8 bytes for both bodies
combined**, plus **3,456 UTF-8 bytes for system/user message contents**.
Oversized input fails before model transmission, without truncation or
one-document fallback. These measurements do not guarantee every possible
document or future model will answer within the adapter's timeout.

## Test results

- M9-specific suite: **14 tests passed** when the dedicated real Ollama
  test was enabled. The other 13 use synthetic/stub model responses and the
  existing PostgreSQL; the model test uses synthetic documents only.
- M1–M9 full discovery: **93 tests, 91 passed, 2 skipped, 0 failures/errors**.
  The two skipped tests are the M3 and M6 real-Ollama opt-ins, which use
  separate environment flags. Each was run separately afterward and **both
  passed**. Thus every discovered test was executed successfully, although
  not in one all-opt-ins invocation.
- Existing M1–M8 code paths, including Memory Write/Read/Query,
  idempotency, read-only Recovery Triage, M6 listing, M7 safe read, and M8
  single-document answer, passed their regression checks. M8's real model
  opt-in also ran in the 93-test suite.

M9 checks covered both-source and one-source support, `partial`,
`insufficient`, `conflicting`, and `out_of_scope`; exact source-qualified
quotes and first occurrence positions; same text in both sources; 3/4 quote
and 240/241 Unicode-character boundaries; unknown source, wrong-source
quote, extra output fields and malformed output. Preflight denied missing
authorization, duplicate/case aliases and invalid D1/D2 names before Task
creation. The suite exercised a real hard link to the same file, missing D1
and D2, absent identity, both-body byte and full-message Context limits,
Korean/English synthetic content, model unavailable/timeout, and confirmed
unknown worker outcome. Revocation between source observations, before the
model, during its call, and before response prevented the next action or
withheld disclosure. Injected text asking for a third file, Tool execution,
source reassignment, secrets or system prompt remained document data: only
D1/D2 reads occurred, no extra Tool execution was invoked, no known token or
DB password reached Context or response, and forged provenance was rejected.

The final-transaction failure injection rolled back answer, source and quote
Evidence together and left the reserved Task `running` rather than claiming
success. This is an intentionally uncertain result, not an automatic failed
transition. M5 Recovery Triage still covers only `memory.save`.

## Existing data and Docker volume

Before and after the synthetic integration runs, the actual DB had the same
row counts: user **1**, active token **1**, memory **2**, Task **2**,
Execution **3**, and M4 key mapping **1**. Private fingerprints of all six
tables matched before and after; neither token nor memory text is included
here. Project, membership, M6–M9 Evidence, and `running` Task/Execution
counts were all **0** after cleanup. The three new M9 tables remain in the
schema but contain no synthetic rows. The existing `noah-postgres` container
remained running and the named volume `noah_noah-postgres-data` remained in
place (created 2026-07-13). No volume initialization or deletion occurred.

## Separate user manual API verification

The user ran the M9 API against a temporary synthetic project with read-only
membership and two public `.md` files. Exactly **one successful M9 request**
was sent to `POST /projects/<project_id>/documents/answer-selected`. It
returned HTTP **200**, `status=succeeded`,
`capability=project.documents.answer.selected`, and `grounded=true`. The
ordered observations were D1=`m9-source-one.md` and D2=`m9-source-two.md`.
The quote containing `NOAH의 테스트 동물은 수달이다.` was verified against D1; the
quote containing `NOAH의 테스트 색상은 파란색이다.` was verified against D2. Each
quote matched the claimed source exactly, and NOAH's Unicode `[start,end)`
positions were checked against that source's decoded text. This verifies
literal provenance, not the real-world truth of the synthetic statements.

The user checked one M9 Task and Execution, the answer parent Evidence, both
source observations, and the source-qualified quote Evidence. No extra
M7/M8 Execution or legacy Evidence was created for the M9 execution. Neither
the API response nor Evidence exposed a local absolute path, API token, DB
password, or complete document body. A separate duplicate-document-name
request returned HTTP **400** with `DUPLICATE_DOCUMENT_NAME` and null
`task_id`/`execution_id`; its before/after DB snapshots were identical.

Cleanup deleted only the temporary M9 answer/source/quote Evidence, its one
Execution and Task, and the synthetic membership and project. The private
baseline snapshot matched exactly afterward, including existing user,
token, memories, prior Tasks/Executions, and M4 mapping. The local mapping,
both synthetic files, and temporary document root were removed. The final
check reported `DB restored; local mapping and synthetic document root
removed`. The existing PostgreSQL data and named Docker volume were retained.

Two **manual procedure** defects were found; neither was an M9 runtime,
schema, permission, or provenance failure. On Windows PowerShell 5.1,
passing multiline Python as `& $Python -c $SnapshotCode` broke quoted SQL
and produced `SyntaxError`. Feeding the text on stdin, for example
`$SnapshotCode | & $Python -`, worked for snapshot, verification, and
cleanup blocks. The first cleanup example queried all three legacy Evidence
tables with `WHERE project_id=%s`, but
`noah.document_answer_evidence` has no `project_id` column. It stopped
**before any DELETE**; the DB, mapping, files, and root remained in their
post-success state. The corrected check uses `WHERE execution_id=%s`, which
matches the purpose of detecting legacy Evidence attached to this M9
Execution. Cleanup then passed and restored the baseline. These corrections
do not change the M9 application or database schema.

## Limits still in force

The two document reads are sequential observations, not one atomic
filesystem snapshot. Their timestamps and original-byte hashes describe
each observed source; later file changes do not change those records. The
current no-follow boundary does not claim to defeat a malicious process
running as the same Windows user and racing path changes. Source-qualified
`grounded` proves literal excerpt and computed position, not real-world
truth, question relevance, or exhaustive comparison. There is no automatic
retrieval, third source, free-form summary, Tool chain, Memory combination,
or M9 recovery.
