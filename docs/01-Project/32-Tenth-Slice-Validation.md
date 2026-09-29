# M10 Controlled Document Selection — validation record

> 2026-09-29. Automated verification on the existing Docker Compose
> PostgreSQL 17 and the dedicated loopback Ollama instance. The first
> user-operated two-source manual API attempt did **not** pass its selection
> goal. A second, separately prepared attempt completed the two-source
> grounded contract with `partial`; both runs were cleaned up exactly. No personal document was used for
> model probes or tests. No Git commit or push is part of this record.

## Implemented boundary

`POST /projects/<project_id>/documents/answer-auto` accepts exactly
`{"question":"..."}` and records capability `project.documents.answer.auto`.
After token and membership checks, it reserves one Task and Execution. It
uses M6's bounded directory worker plus independent rescan, filters observed
names through M7's exact `.md` basename policy, then allows the selection
model to propose zero, one, or two **exact** candidate names. The model sees
only the question and logical filenames at this stage. Neither model has a
Tool-call channel. A selected file is opened with the M7 no-follow safe-read
and independent verification, then its untrusted content enters the M8 or
M9 answer Context. NOAH verifies exact quotes and computes Unicode
`[start,end)` positions. The candidate and later source observations have
different times and do not form one filesystem snapshot.

For an empty complete list, no model call is made. A valid model `none`
also yields `no_document_selected`, `grounded=false`, no source/quote rows,
and a completed/passed Task with succeeded Execution. This does not assert
that no answer exists in the project. One/two sources reuse M8/M9 internal
grounding validators without invoking their HTTP routes or writing their
Evidence. After a read, an `insufficient` answer remains distinct from
zero selection. Authorization is rechecked before enumeration, selection
model exposure, each file open, answer model exposure, final commit, and
response disclosure.

## Selection limits and actual local-model probes

The baseline model is the currently configured `gemma4:12b-it-qat` on
`127.0.0.1:11435`, `num_ctx=4096`, temperature zero. The following size and
structured-output probes used the **initial selection prompt**, before the
manual no-selection result and prompt clarification. Only synthetic names
and synthetic questions were sent. The real model returned strict JSON that
passed NOAH's validator in these earlier probes:

| Synthetic case | Names | Name-array UTF-8 bytes | System + user bytes | Result | Time |
| --- | ---: | ---: | ---: | --- | ---: |
| English | 20 | 365 | 999 | valid `selected` | 16.9 s |
| Korean, ASCII-escaped probe source to preserve UTF-8 | 20 | 441 | 1,009 | valid `none` | 7.1 s |
| Mixed English/Korean, correctly encoded | 20 | 341 | 912 | valid `none` | 24.5 s |
| Long synthetic basename near filesystem name limit | 20 | 481 | 1,109 | valid `selected` | 8.2 s |
| Synthetic high-byte candidate array | 20 | 1,064 | 1,632 | valid `selected` | 9.4 s |

An initial Korean probe passed through Windows PowerShell stdin with damaged
text; it was discarded and repeated using ASCII `\u` escapes. The chosen
runtime limits are conservative: **20 candidates**, **1,024 UTF-8 bytes**
for their compact JSON array, **2,048 UTF-8 bytes** for the complete system
and user selection-message bodies, and **384 output tokens**. The 1,064-byte
probe above demonstrates model behavior near the chosen name budget; M10
intentionally rejects that array before a model call. The message budget
leaves room within `num_ctx=4096` for the schema and output allowance.
NOAH rejects truncation, over-count, over-byte names, or over-byte messages
without sending a partial candidate list. These bounds constrain Context,
not selection quality or a guarantee about future model versions.

## Database and automated tests

Migration `007_auto_document_answer_evidence.sql` adds three M10-only tables:
`auto_document_answer_evidence` (complete candidate observation, canonical
SHA-256, valid raw proposal, approved order and outcome),
`auto_document_source_evidence` (D1/D2 independent byte observation), and
`auto_document_quote_evidence` (source-qualified exact quote and NOAH-computed
position). The parent has one `execution_id`; source and quote children
reference it. Candidate/source/quote Evidence and terminal Task/Execution
states commit in one final transaction. The earlier running reservation is
separate. Whole document bodies, machine paths, model prompts, tokens, and
DB credentials are not stored in this Evidence. Invalid proposals record
only a safe failure code in the Execution, not their raw text.

M10's initial dedicated synthetic Compose suite contained **20 tests**: 19
passed by default and one actual-Ollama opt-in test was skipped. That opt-in
test checked only the validity of structured output, so a valid `none` could
pass; it did not establish two-source selection quality. Coverage includes
empty/zero/one/two selection, exact-name
validation, case/duplicate/unknown/three-name rejection, 20/21 count and
byte boundaries, truncation, M7 `.MD` filtering, instruction-like filename,
model unavailable/timeout, preflight HTTP authentication, membership
revocation, deletion or replacement between selection and read, hard-link alias, actual
M6 directory worker, source
provenance, spoofed quote/source rejection, one Task/Execution, M10 Evidence
linkage, and absence of M6–M9 Evidence for that Execution. Windows link
creation required privileges unavailable in this run; M10's direct symlink
branch could not be exercised by this test, while prior M7 Windows junction
and synthetic reparse tests remain in the regression suite.

The initial **full M1–M10 regression** ran **113 tests: 108 passed, 5 opt-in tests
skipped, zero failures/errors**. This included existing M1–M9 Write, Read,
LLM Query, idempotency, recovery triage, document list/read, and one/two
source answer tests. The five skips are opt-in real-model cases.

### First user-operated manual attempt — not a two-source pass

The user submitted one Korean multipart question, `NOAH의 M10 테스트 동물과 테스트
색상을 각각 알려줘.`, with synthetic candidates `m10-test-animal.md` and
`m10-test-color.md`. The complete observation contained both names
(`candidate_count=2`, `truncated=false`) and the selection model was called.
It returned valid `none` with empty raw/approved names. The API returned
HTTP 200, `succeeded`, `no_document_selected`, `grounded=false`, with one
Task/Execution and no source or quote Evidence. This is a normal M10
zero-selection result, **not** an enumeration, permission, Runtime, DB, or
safe-read failure. It did not satisfy the planned two-source E2E goal. The
same request was not resent. Targeted cleanup removed only this attempt's
M10 parent Evidence, Task/Execution, synthetic membership/project, mapping,
two files, and temporary root. The DB matched its pre-attempt baseline.

Code review identified an actual-model selection coverage gap: the original
opt-in test used an English single-topic question with a strongly matching
English filename and asserted only schema validity. The selection instruction
also left multipart, cross-language filename relevance implicit. The prompt
now clarifies that names are limited topic clues, that each independent
question need is assessed against candidates, and that `none` applies only
when no candidate is reasonably relevant. Filename data remains untrusted;
the model still receives no document body, OS path, or Tool authority.

### Post-prompt automated regression — separate from manual E2E

The revised dedicated suite ran **21 tests: 19 passed and 2 actual-Ollama
opt-in cases skipped**, with no failures/errors. The two opt-in tests were
then run separately using the production `gemma4:12b-it-qat` client, schema,
`num_ctx=4096`, temperature zero, and output-token setting. Both passed:
the Korean multipart question selected exactly the two observed English topic
names `m10-test-animal.md` and `m10-test-color.md`, while an unrelated question and filenames returned valid
`none`. The actual-model assertions require the exact outcome, count, and
names; a valid `none` cannot pass the two-source case. The full M1–M10
regression then ran **114 tests: 108 passed, 6 opt-in tests skipped, zero
failures/errors**. These were the automatic results after the selection fix,
before the second user-operated run and the additional answer-stage test.

### Second user-operated manual attempt — two-source grounded success

After the selection fix, the user prepared a fresh synthetic project and
sent the Korean multipart question **once**, without retrying it. The API
returned HTTP 200, `status=succeeded`, capability
`project.documents.answer.auto`, candidate count 2 with `truncated=false`,
and exactly two selected names: `m10-test-animal.md` and
`m10-test-color.md`. D1 and D2 each had one exact quote, respectively
`NOAH의 M10 테스트 동물은 수달이다.` and
`NOAH의 M10 테스트 색상은 파란색이다.`. Both Unicode `[start,end)` intervals
and source content SHA-256 values matched the actual synthetic file bytes.
The response reported `grounded=true` and **`outcome=partial`**; this
outcome is preserved exactly as returned.

Read-only DB verification found the M10 Task `completed/passed`, its one
Execution `succeeded/verified`, the complete candidate observation, two
source rows, and two quote rows correctly linked. No M6/M7/M8/M9 legacy
Evidence was attached to this M10 Execution. The expected snapshot delta
matched, and neither response nor Evidence exposed whole document bodies,
absolute paths, API token, or DB password. After the server stopped, the
user removed only this run's quote/source/parent Evidence, Execution, Task,
membership, project, local mapping, two synthetic files, and root. The DB
returned to its pre-run baseline, including private row fingerprints. The
same request was not resent.

Contract review confirmed that [M9's two-source outcome rules](29-Ninth-Vertical-Slice.md)
permit `partial` even with verified quotes from **both** sources when the
model reports incomplete support. NOAH verifies source-qualified literal
quotes and positions, not complete semantic coverage of the question. The
manual guide's former `supported`-only check was therefore stricter than the
runtime contract; it is corrected to accept `supported` or `partial` with
both source quotes and explicit human review of their relevance. The first
run's filename-selection `none` issue and this second run's `partial` answer
label are separate. The latter is **not** a Runtime failure.

### Final contract regression after the manual review

M10 now has a deterministic two-source case in which the model stub returns
`partial` with exact D1/D2 quotes. An additional opt-in test invokes the
actual local Ollama model through both M10 selection and answer stages with
the synthetic animal/color documents and the same Korean multipart question.
It requires both exact selected names, `supported` **or** `partial`, both
source IDs, question-related quotes from the correct documents, exact
Unicode positions, and original-byte SHA-256. Neither test changes the
answer prompt, schema, or Runtime code. The final execution counts are
**23 M10 dedicated tests** ran by default: **20 passed, 3 opt-in actual-Ollama
tests skipped**, zero failures/errors. The new actual-Ollama answer test then
passed separately, as did both existing actual-Ollama selection tests. The
final **M1–M10 regression ran 116 tests: 109 passed, 7 opt-in tests skipped,
zero failures/errors**. The first run of the new answer test exposed a
Windows-only test-fixture hash assumption (`write_text` newline conversion),
not a Runtime failure. The fixture now writes exact UTF-8 bytes; the test
and full regression passed after that correction. No new user-operated HTTP
request was sent during this document/test-only follow-up.

After the suite ended, read-only counts were users 1, API tokens 1,
memories 2, Tasks 2, Execution Records 3, M4 mappings 1, project 0,
membership 0, M6–M10 Evidence 0, and running Task/Execution 0. Tests used
temporary roots and synthetic accounts, then removed only their owned data.
The existing Docker volume was not deleted or reset. The local project
mapping was not created by these tests. The later tests likewise use only
synthetic accounts and temporary roots.

## Failure and remaining limits

Preflight rejection creates no Task or Execution. Definite post-reservation
failures record paired failed states when DB storage is available. A lost
DB/commit acknowledgement or unconfirmed worker termination yields an
uncertain outcome; **Unknown Outcome != Failed**. M5 Recovery Triage still
handles only `memory.save`, not M10. Existing M4 keyed idempotency does not
extend to read-only M10.

Candidate filenames can be sensitive project metadata, so they are retained
only in project-linked Evidence and are never emitted in unauthenticated
errors. The filename selector can miss a relevant document; a zero selection
is not a completeness proof. `grounded=true` verifies literal excerpts and
positions against observed bytes, not semantic relevance or real-world
truth. Local same-user malicious filesystem replacement races remain outside
the M6/M7 threat guarantee. The dedicated local model may take tens of
seconds on CPU. The user-operated two-source grounding check is complete;
`partial` does not certify complete semantic coverage of both requested facts.
