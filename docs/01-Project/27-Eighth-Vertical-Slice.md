# M8 grounded single-document question answering

> Status: M8 contract and implementation record, 2026-09-29. The implemented
> baseline is M1–M8; executed checks are recorded separately in
> [M8 Validation](28-Eighth-Slice-Validation.md). M1–M7 remain the baseline,
> especially [M3 quoted Memory Query](17-Third-Vertical-Slice.md),
> [M6 document listing](23-Sixth-Vertical-Slice.md),
> [M7 verified document read](25-Seventh-Vertical-Slice.md), and
> [Runtime/State](../02-Architecture/Runtime/State.md). Blueprint 10 and
> Accepted DDR-001–006 remain the architecture baseline.

## Goal and exclusions

For one authenticated question, NOAH selects one exact, direct-child `.md`
document in an operator-registered project root. NOAH uses the M7 bounded,
no-follow read and independent byte verification, then sends the verified text
to the dedicated local model as **untrusted data**. The model may propose at
most three exact quotations. NOAH checks them against that same decoded text,
calculates their positions, and constructs the final response itself.

M8 does not produce free-form document summaries or trust a model-written
answer as a fact. It does not search other documents, perform RAG, embeddings,
vector search or Knowledge ingestion, invoke another Tool, edit files, save
Memory, run a Shell, call an external connector, or add multi-agent or
autonomous planning. M7's public read API and M1–M6 behavior remain intact.

## Non-negotiable trust and permission boundary

NOAH's security policy, authentication, authorization, and verified execution
contract are enforced constraints that a user question cannot waive. The
authenticated user chooses a question and an exact document basename only
within those constraints. Retrieved document text is task data, never an
instruction source or a grant of permission. Verified file bytes establish
what NOAH observed, not the truth or authority of the document's claims.

The document may contain instructions to ignore earlier directions, read
another file, run a Tool, reveal an API token, DB credential, or system prompt,
or fabricate an answer. None is executed or promoted into NOAH policy. The
model receives no Tool list, Tool-call channel, OS path, API token, or DB
credential. The only task data supplied to it are the user's question, a
logical document identifier, and the verified bounded document text. NOAH
supplies the separate system-level task and structured-output contract.
NOAH does not add its own credentials to Context. If an approved document
itself contains sensitive text, the local model would see that text; M8 does
not claim to recognize every secret embedded in user-authored documents.

Authenticate and check current project read membership before resolving or
opening the document. Recheck immediately before the M7-style file open,
immediately before sending text to the model, and immediately before
disclosing the response. If permission is revoked after a reservation but
before the read or model call, record a definite failure when storage is
available and do not perform the next action. If permission is revoked before
the response, withhold the answer, quotations, and document content. Text
already sent to the local model during an earlier authorized interval cannot
be recalled after a later revocation; this is a timing limit, not continued
permission to disclose a result.

Before transmitting document content, retain the dedicated Ollama
loopback-only check from M3/M6. Model and listener selection remain the
currently validated local configuration unless implementation-stage synthetic
verification supports a reviewed change. No change to the other local Ollama
service is part of M8.

## Context construction and size

Use the exact validated M7 decoded content. Accept strict UTF-8 with M7's
optional leading BOM treatment; preserve all remaining Unicode characters and
line endings. Do not normalize CRLF to LF, change spaces, or silently shorten
the document. Represent the document as an explicitly marked data field in a
message separate from NOAH's instructions, with its logical identifier. The
source observation is linked to the M8 Execution in PostgreSQL, not supplied
as model authority. A role label or instruction embedded within
that field is still untrusted text. Do not include unrelated Memory, project
files, conversation history, credentials, or the absolute document root.

M7 permits up to **65,536 original file bytes**. This is not the M8 model
Context budget. M8 uses **2,048 UTF-8 bytes of the decoded document text
after M7's optional BOM removal**, not 2,048 characters or a permanent
model-independent guarantee. This cap was selected after synthetic Korean and
English checks with the current local model at `num_ctx=4096`. A changed model
or context configuration requires renewed validation. An over-cap document produces an explicit
`CONTEXT_TOO_LARGE`-family failure without calling the model. Do not silently
truncate, chunk, or answer for a fragment as though it were the whole file.
The request contains one nonempty question bounded to 300 Unicode characters
and 512 UTF-8 bytes.

## Model output and quote verification

The model output is a strict JSON object with exactly these fields:

```json
{
  "outcome": "supported",
  "evidence": [{ "quote": "exact excerpt from the document" }]
}
```

`outcome` is exactly one of `supported`, `partial`, `insufficient`,
`conflicting`, or `out_of_scope`. `evidence` is an array of **0–3** items;
each item has exactly one `quote` string of **1–240 Unicode characters**
(code points), containing at least one non-whitespace character. No model
field for `answer`, Tool requests, paths, line numbers, or offsets is
accepted. Reject extra fields, duplicate quote strings, invalid types,
empty/oversized quotes, and quotes absent from the verified decoded text.
`supported` and `partial` require at least one quote; `insufficient` and
`out_of_scope` require none. `conflicting` requires at least two distinct
verified quotes. These checks validate structure and provenance, not whether
the quotes are relevant or truly contradictory.

NOAH locates each exact quote in the **same decoded text actually supplied to
the model** and calculates `[start, end)` as Unicode code-point indices in
that text; no newline or Unicode normalization occurs. If an identical quote
appears in several places, NOAH selects the lowest starting index and reports
that occurrence consistently. It rejects repeated quote entries in one
output. The model never supplies a location. Both the quote and NOAH-computed
position are returned as evidence with the M7 observation reference.

NOAH constructs the user-facing answer from verified quotes and fixed
qualifying text. A free-form model answer is neither accepted nor forwarded.
For `partial`, disclose only the quoted portion and state that the rest is
unverified. For `conflicting`, show both quoted passages and defer a final
conclusion; this outcome reports a possible conflict flagged by the model,
not a proven logical contradiction. For `insufficient`, say that no verifiable
quote was obtained, not that the document contains no answer. For
`out_of_scope`, state the single-document scope and do not fetch another
source. `supported` presents the verified excerpts without adding facts from
model general knowledge.

`grounded` in the final response means only that the selected document was a
verified M7-style observation, every selected quote occurs exactly in its
decoded text, and NOAH calculated each cited position. It does **not** prove
real-world truth, complete semantic relevance to the question, absence of an
answer elsewhere in the document, or exhaustiveness of the selected quotes.
An `insufficient` outcome means no verified quote was obtained. A successful
processing outcome with no quotes must not be labeled `grounded: true`.

## Execution and evidence boundary

After authentication, membership, request validation, and operator-root
preflight, durably reserve one `running/pending` Task and one `running` M8
Execution before the read worker starts. M8 reuses the M7 **reader and
verification behavior**, not the public M7 endpoint; the latter would create
a separate completed M7 request. Recheck permission at each point above.
The sequence is verified document observation, Context size check, local model
call, strict output validation, exact quote and position verification, and
final permission check. Only after these checks may NOAH atomically commit the
document observation evidence, M8 answer evidence, Task `completed/passed`,
and Execution `succeeded` with verification time. Authorization must be
checked again immediately before emitting the HTTP response. If membership
was revoked after the commit, withhold the excerpts even though a verified
execution is durable; if the final check cannot reach PostgreSQL, withhold
them and report the uncertainty. This atomic boundary must also work for
verified non-answer outcomes: `passed` then means NOAH obeyed
the bounded response contract, not that it proved no answer exists.

The minimum append-only M8 answer evidence is linked by `execution_id` to the
M8 Execution and its document observation. It carries `project_id`, logical
`root_id`, exact `document_name`, document original-byte SHA-256 and
`observed_at`, the validated `outcome`, and each verified exact quote with
NOAH-computed `[start, end)` indices. It must not store the complete document,
absolute OS path, API token, DB credential, or model prompt. A source hash
identifies the observed bytes; it cannot reconstruct them after the source
changes unless those bytes are retained elsewhere.

The implementation uses the first evidence-link design:

| Option | Benefit | Cost / condition |
| --- | --- | --- |
| Reuse `noah.document_read_evidence` for the M8 Execution, plus one small M8 answer-evidence row referencing its `execution_id` | One authoritative observation shape and direct reuse of M7 metadata; both rows can commit with the M8 terminal state | Confirm that the existing table and readers permit a `project.documents.answer` Execution, and define the shared observation semantics explicitly |
| Add the minimum observation fields to an M8-specific append-only evidence row | M8 evidence is self-contained and does not broaden the M7 table's use | Duplicates M7 metadata and verification rules; migration and audit queries must keep them aligned |

`noah.document_read_evidence` records the M8 execution's M7-style observation.
`noah.document_answer_evidence` references the same `execution_id` and stores
the outcome and verified quote/position array. Its project, logical root,
document identifier, source SHA-256, and observation time are obtained through
that required source row. Both evidence rows and terminal Task/Execution states
commit together. The body is not copied into either record.

## Failure and unknown-outcome rules

- Authentication, unreadable project, malformed filename/question, or missing
  operator mapping rejected before reservation create no M8 Task/Execution.
- A definite read, Context construction, model availability, malformed model
  output, quote mismatch, or permission failure after reservation records
  paired `failed/failed` Task and `failed` Execution with a safe failure code
  when PostgreSQL is available. Distinguish document-read failure,
  `CONTEXT_TOO_LARGE`, model unavailable, model timeout, invalid structured
  output, evidence mismatch, and DB failure in the API contract. Do not return
  a purported grounded answer on these paths.
- A model timeout is a confirmed failure only if NOAH can establish that the
  attempt cannot still finalize. An unconfirmed worker/model outcome, DB
  connection or commit-acknowledgement loss, and HTTP response loss do not
  justify a guessed terminal state. Preserve what is durably known, report
  outcome uncertainty, and do not silently retry. **Unknown Outcome != Failed.**
- An `insufficient`, `partial`, `conflicting`, or `out_of_scope` structured
  result is a bounded response outcome, not by itself an execution failure.
  Its verification status refers only to the checks in this contract.
- M4 Idempotency-Key mapping remains `memory.save`-only. Each M8 read is a new
  observation. M5 Recovery Triage remains `memory.save`-only; it neither
  inspects nor automatically recovers an M8 Execution. No new DB Task,
  Execution, or verification status is introduced by this contract.

Errors, logs, and evidence must omit document bodies, absolute paths, API
tokens, DB passwords, and system prompt text. A successful authorized API
response may contain only the chosen short verified quotations, not the full
document body.

## Implementation decisions and verification

The selected capability is `project.documents.answer` at
`POST /projects/<project_id>/documents/answer`, with JSON `document_name` and
`question`. The M7 65,536-byte safe-read limit remains independent of M8's
2,048 UTF-8 byte model-document cap. A question is limited to 300 Unicode
characters and 512 UTF-8 bytes; the combined system/user messages are limited
to 3,456 UTF-8 bytes without truncation. Korean and English synthetic inputs
near 1.8–1.9 KiB were checked with the current dedicated local model and
`num_ctx=4096`; the model configuration remains changeable, not permanent.
The synchronous model adapter's timeout ends NOAH's model attempt before any
answer commit. A worker whose termination cannot be proven and uncertain DB
commits remain unknown outcomes. The M7 file/path/UTF-8 contract is unchanged.

After an operator has registered a readable project root and the M8 schema is
initialized, Windows PowerShell can send a request using existing user and
project credentials stored locally in environment variables:

```powershell
$body = @{ document_name = "guide.md"; question = "문서에 나온 나무는?" } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8080/projects/$env:NOAH_PROJECT_ID/documents/answer" -Headers @{ Authorization = "Bearer $env:NOAH_API_TOKEN" } -ContentType "application/json; charset=utf-8" -Body $body
```

The successful response includes `outcome`, NOAH-assembled `answer`, verified
quote/evidence positions, source byte length/hash, and Task/Execution IDs.
It does not return the entire document or the machine's absolute root path.

Use separate synthetic user, project, membership, and document root on Docker
Compose PostgreSQL 17. Test every outcome, duplicate and fabricated quotes,
Unicode positions and unchanged CRLF, duplicate source occurrences, BOM,
Context boundary, permission revocation before open/model/release, model and
DB failures, and Task/Execution/evidence atomicity. Include documents that
instruct NOAH to ignore policy, read another file, invoke a Tool, reveal
secrets or system instructions, or invent citations. Assert zero additional
Tool calls, zero NOAH credential/context leakage, and no unverified citation
in the response. Run M1–M7 regressions and clean only test-owned records and
files; preserve existing users, memories, Tasks, Executions, and Docker
volumes. Executed results are in [M8 Validation](28-Eighth-Slice-Validation.md).
