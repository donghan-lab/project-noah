# M8 Grounded Single-Document Answer — Validation Record

> 2026-09-29, current uncommitted M8 worktree. Automated synthetic checks and
> the user's separate manual API verification are recorded below. No existing
> personal document was sent to Ollama during this validation.

## Implementation and execution contract

`POST /projects/<project_id>/documents/answer` accepts JSON with exactly
`document_name` and `question`, authenticated by the existing bearer token.
The document identifier is an M7-valid direct-child `.md` basename. The
capability is `project.documents.answer`. Authentication and project read
membership precede root/file access; membership is rechecked before file open,
before the model call, before final commit, and before answer release.

M8 reserves one Task and one Execution. It calls M7's internal no-follow,
bounded safe reader and independent byte verification, not the M7 HTTP API.
The original byte length and SHA-256 are stored in
`noah.document_read_evidence` under the M8 execution. A new
`noah.document_answer_evidence` row references the same execution and stores
the validated outcome and exact quotes with NOAH-computed Unicode character
`[start,end)` positions. The two Evidence rows, Task `completed/passed`, and
Execution `succeeded` commit in one transaction. No document body or absolute
OS path is stored in Evidence.

The model sees one verified document as untrusted data, one bounded question,
and a logical document name. It receives no Tool call interface, NOAH bearer
token, DB password, or actual root path. NOAH rejects an exact occurrence of
the current bearer token or configured DB password in the question or selected
document before the model call. This is a known-credential guard, not a claim
to detect every possible secret in user-authored text. The model may output
only `outcome` and up to three exact quote candidates. Each quote is at most
240 Unicode characters. NOAH verifies literal presence and computes the
first occurrence's position without newline normalization. It assembles the
response from verified excerpts; it never forwards a free-form model answer.

M7 permits 65,536 original file bytes. M8 separately limits the decoded
document sent to the model to **2,048 UTF-8 bytes**, the question to 300
Unicode characters / 512 UTF-8 bytes, and combined system/user messages to
3,456 UTF-8 bytes. Over-cap content is rejected, never truncated. The selected
model remains `gemma4:12b-it-qat` on dedicated loopback Ollama
`127.0.0.1:11435`; this is a validated current configuration, not a permanent
model choice.

## Synthetic local-model and PostgreSQL checks

Before any actual personal document was sent to a model, Korean and English
synthetic source text near 1.8–1.9 KiB was tried with the current model at
`num_ctx=4096`, `num_predict=384`, and CPU-only configuration. Refined probes
returned `supported` with one exact quote in both languages. The Korean
probe used 1,843 document bytes, 2,490 combined prompt bytes, 517 prompt
tokens, and about 10.7 seconds. The English probe used 1,914 document bytes,
2,545 combined prompt bytes, 411 prompt tokens, and about 9.3 seconds.
These are compatibility observations, not throughput guarantees.

Focused Compose PostgreSQL 17 tests cover the five outcomes (`supported`,
`partial`, `insufficient`, `conflicting`, `out_of_scope`); exact and fabricated
quotes; first Unicode position of a repeated quote; three/four-quote and
240/241-character boundaries; CRLF and BOM; exact 2,048/2,049-byte Context
boundary; authentication and project membership; revocation before open,
before model, and before response; prompt-injection text with no additional
Tool call; current credential exclusion; malformed model output, unavailable
model and timeout; actual M7 worker; HTTP route; atomic Task/Execution/Evidence
links; DB loss and partial final-transaction rollback. A real dedicated
Ollama integration test uses only a synthetic document and question.

The final full M1–M8 regression run used the existing Compose PostgreSQL 17,
enabled all three opt-in synthetic Ollama checks (M3, M6, M8), and passed
**79 tests with zero failures, errors, or skips** in 101.1 seconds. The M8
module contributed 16 tests. Earlier
runs: M8 focused suite had 15
tests, 14 passed and one opt-in Ollama test skipped; the first full run had 78
tests, all passed with two other opt-in Ollama checks skipped; an all-model
run then passed all 78. One additional final-transaction rollback test was
added after that run and is included in the final run.

## Data preservation and limits

Read-only post-test baseline: user 1, API token 1, personal memories 2,
Tasks 2, Execution Records 3, M4 mappings 1; projects, memberships, M6 Tool
Evidence, M7 Document Read Evidence, and M8 Answer Evidence each 0. Running
Tasks and Executions each 0. ID and token-hash fingerprints were recorded for
comparison without printing their values or any credential. The existing
`noah-postgres` container remained running on PostgreSQL 17 with the existing
`noah_noah-postgres-data` named volume. Synthetic test-owned users/projects,
rows, and temporary roots were removed by test cleanup.

## Separate user manual API verification

The user ran one successful M8 request against a temporary synthetic project
and public `.md` document through the actual NOAH server/API. HTTP 200 returned
`status=succeeded`, `capability=project.documents.answer`,
`outcome=supported`, and `grounded=true`. The exact Evidence quote was
`NOAH의 테스트 동물은 수달이다.`; it matched the document, and NOAH's Unicode
`[start,end)` position matched the source. The Task, Execution,
`document_read_evidence`, and `document_answer_evidence` references were
checked together. There was no additional `project.*` Execution or M6
`document_tool_evidence` row.

A separate `../document` request returned HTTP 400 with
`INVALID_DOCUMENT_IDENTIFIER` and null Task/Execution IDs. The DB snapshots
immediately before and after that rejection matched. The user then removed
only the M8 manual synthetic rows, local mapping, and temporary document root.
The final cleanup checks returned `MappingExists=False`, `RootExists=False`,
and `DbRestored=True` against the pre-verification row and private-fingerprint
snapshot. Existing user, token, memories, M1–M7 execution history, and Docker
volume were retained. These are user-reported manual observations, distinct
from the automated test run above.

The original Windows PowerShell 5.1 check
`($Result.evidence | Where-Object { ... }).Count` produced a false negative
when one Evidence object was returned. Direct inspection found
`EvidenceCount=1`, `ContainsOtter=True`, `ExactInDoc=True`, and
`PositionOK=True`; the API result was valid. For future PowerShell 5.1 manual
checks, force an array before counting:

```powershell
$matchingQuotes = @($Result.evidence | Where-Object { $_.quote -like '*수달*' })
if ($matchingQuotes.Count -lt 1) { throw 'Expected quote not found' }
```

M8 grounding proves a selected source observation and exact quote positions;
it does not prove real-world truth, full semantic relevance, or absence of
other answers. The model may classify a possible conflict; NOAH does not
prove the passages are logically contradictory. `insufficient` means no
verified quote was obtained. M5 Recovery Triage still inspects `memory.save`
only and does not recover M8. Same-user local filesystem race attacks remain
outside the M7/M8 path boundary. The manual check used only public synthetic
document text and does not establish behavior for a private user document.
