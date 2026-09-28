# M10 proposed controlled project document selection contract

> Status: pre-implementation contract, 2026-09-29. M10 has no API, migration,
> implementation, automated test, or manual validation yet. The implemented
> M1–M9 baseline is `382b4d8e5354ea61ce0d1ff5de496f808ce4ee53`.
> Blueprint 10 and Accepted DDR-001–006 remain authoritative. This bounded
> proposal extends [M6 listing](23-Sixth-Vertical-Slice.md),
> [M7 safe read](25-Seventh-Vertical-Slice.md),
> [M8 single-source grounding](27-Eighth-Vertical-Slice.md),
> [M9 two-source grounding](29-Ninth-Vertical-Slice.md), and
> [Runtime/State](../02-Architecture/Runtime/State.md); it does not change
> their public APIs or Evidence meanings.

## Scope and proposed interface

For one authenticated question in one project, NOAH observes the complete,
small set of eligible direct-child regular `.md` filenames under the
operator-registered document root. A local model proposes zero, one, or two
names from that observation. NOAH validates the proposal against the exact
observed names. Only validated selections are opened with M7's safe-read
boundary. One selected source follows M8's grounding verification; two
ordered sources follow M9's source-aware verification. NOAH constructs the
response from verified quotes, not from model-written free prose.

The proposed endpoint is `POST /projects/<project_id>/documents/answer-auto`
with capability `project.documents.answer.auto`. The only request field is
`{"question":"..."}`. These names are **proposals**, to be confirmed before
implementation. The question should initially inherit M8/M9's nonempty,
300-Unicode-character and 512-UTF-8-byte bounds; no user or model OS path or
document basename is an API input. The authorized project ID remains in the
route. M8 and M9's explicit selection endpoints remain unchanged.

This is not general RAG or a Tool loop. It excludes embeddings, a vector DB,
semantic indexing, recursive discovery, Knowledge ingestion, Memory search,
external connectors, Tool chaining, multi-agent planning, file changes, and
free-form summary. The selection model has no Tool-call channel. The only
filesystem operation before selection is NOAH's fixed M6-style candidate
observation; the selection model receives **no document body**.

## One execution and candidate observation

Authenticate, validate the question, check project read membership, and
resolve the operator root before reservation. Recheck token and membership,
then durably reserve **one M10 `running/pending` Task and one `running`
Execution before starting the directory worker**. Pre-reservation rejection
creates neither. M10 uses M6's internal bounded enumeration and independent
observation validation; it does not call M6 `/documents/query` or create an
M6 Task/Execution or M6 Evidence row. Likewise, it reuses M7/M8/M9 internal
read and grounding primitives rather than their HTTP endpoints or Tasks.

M6's current filename listing accepts a case-insensitive `.md` suffix,
whereas M7's basename validator requires the exact lowercase `.md` suffix
and its other identifier restrictions. Define the M10 candidate set as
**M6-observed names that also pass M7's exact basename policy**; for example,
an `.MD` entry is outside this first M10 read scope. Apply that eligibility
rule deterministically before constructing candidate Context or its hash,
and document the filtering as a scope rule rather than silently treating an
ineligible name as a selectable source. A truncated raw M6 observation must
still fail completeness even if the visible eligible subset is small.

Bind each complete candidate observation to this M10 Execution with
`project_id`, logical `root_id`, `observed_at`, the stable ordered exact
**M10-eligible** filenames, count, `truncated`, and a canonical candidate-set
SHA-256. The
bounded filename list itself is needed to audit exact membership; a hash
alone cannot prove that a selected name was present. The operator root is a
project-level allowlist, while these names are a **time-specific filesystem
observation**, not a durable file registry or an authority grant to the
model. The candidate scan and later file reads are sequential observations,
not one filesystem snapshot. No machine absolute path is persisted or sent
to the model.

## Completeness and Context budget

M6 currently observes at most 50 names with a `truncated` flag. For first
M10 implementation planning, use **20 candidates** as a smaller *initial
candidate*, not a finalized limit. Set a separate candidate-name Context
byte limit and a complete selection-message limit after synthetic Korean and
English filename probes against the current local Ollama model at
`num_ctx=4096`. Count UTF-8 bytes of the actual serialized filename data;
also budget the question, system instructions, schema, and output headroom.
The precise byte ceilings and selection output token allowance are **not yet
fixed**. M8/M9's existing answer Context limits remain in force after
selection and are not enlarged by this proposal.

An M6-style observation with `truncated=true`, more names than M10's
validated candidate count, or names/messages exceeding the validated
selection Context limit must stop **before the selection model call**. Do
not silently truncate, send a prefix of names, or conclude that the project
has no relevant document. An explicit `SELECTION_SCOPE_INCOMPLETE`-family
failure is preferred; implementation should retain distinct safe reasons
for truncated enumeration, excessive count, and Context bytes. A truly empty
and complete observation can deterministically produce the zero-selection
result without a model call. A nonempty complete observation may also yield
a valid model-proposed zero selection.

## Filename and selection trust boundary

Candidate names such as `ignore previous instructions.md` are untrusted
filesystem data. Send names in a delimited data field, separate from NOAH's
selection instruction and strict output schema. Neither a filename nor the
question can change system policy, grant a Tool, trigger further discovery,
provide an OS path, or authorize a file read. Never include the operator's
absolute root, API token, DB password, or document content in the selection
Context. Project membership and the dedicated loopback-only Ollama check
remain NOAH-enforced boundaries.

Proposed strict selection output:

```json
{"outcome":"selected","document_names":["alpha.md","beta.md"]}
```

`outcome` is exactly `selected` or `none`; `document_names` is an array of
strings. `selected` requires one or two names. `none` requires an empty
array. Reject extra fields, invalid types, duplicates (including case-folded
aliases), three or more names, path syntax, and any name that does not
**exactly** match an observed candidate. NOAH does not repair case,
fuzzy-match, substitute a similar name, or fall back to another file. A
malformed or out-of-set model proposal is a verification failure, not an
authorization decision. Store the valid raw model candidate names separately
from the NOAH-approved selection, even when their values are equal. Never
use unverified raw output as the final source list. For two selections, the
approved model order defines D1 and D2; one selection is D1.

## Zero, one, or two selected sources

For a complete candidate observation with a valid `none` proposal (or an
empty complete list), `no_document_selected` is a **selection-level normal
result**. It has no document safe-read, answer-model call, source observation,
or quote Evidence. Return `grounded=false`; commit the complete observation,
zero-selection result, Task `completed/passed`, and Execution `succeeded`
with verification time together. `passed` means the bounded selection
contract was followed. `no_document_selected` does **not** mean the project
or its documents contain no answer and is distinct from M8/M9
`insufficient`, which follows a document read but obtains no verifiable quote.

For one approved name, use M7's internal safe read and M8's single-source
Context, structured outcome, exact quote, and NOAH-computed first Unicode
`[start,end)` verification. For two approved names, use M7's safe read for
each, reject equal actual file identities as M9 does, and use M9's combined
Context, D1/D2 source-aware outcome and quote checks. M7's original-byte
size, strict UTF-8/BOM, no-follow, and independent observation checks apply
to every file. The selected files are read only **after** selection. No
M7/M8/M9 HTTP route, Task, Execution, or existing Evidence table is reused
as an M10 record. Existing one-source and exactly-two-source Evidence
meanings remain intact. A valid quote-free M8/M9 `insufficient` or
`out_of_scope` answer remains a successful bounded answer execution, not
the M10 zero-selection result. `grounded=true` proves only source-qualified
literal quotes and positions, not semantic relevance or real-world truth.

An observed candidate can disappear, change content, become a
symlink/junction/reparse point, or become a hard-link alias before its later
read. Selection confers no file trust. Recheck the exact selected basename,
root safety, handle-level type and link properties, bytes, text, and hash at
each M7-style open. For two reads, preserve each `observed_at` and original
byte hash independently. A failed required read cannot become a successful
answer from the remaining source; do not replace the selected name.

## Permission and two model calls

Recheck authentication and project read membership at request entry, before
candidate enumeration, before sending candidate names to the selection
model, before each selected safe read, before sending verified content to the
answer model, before the final commit, and immediately before response
disclosure. Denial before a filesystem action prevents that action. After
revocation, send no *new* filename or content Context to a model and disclose
no selection or answer. Context already sent to the local model during an
authorized interval cannot be recalled retroactively.

The selection call receives only the bounded question and complete logical
candidate names with the strict selection schema. For one or two approved
names, a separate answer call receives only the bounded question and those
verified source texts under M8/M9's existing structured grounding schema.
M10 makes at most one call of each type. A valid zero selection makes no
answer call; an empty candidate set need not call either model. Distinguish
selection-model unavailability, timeout, or malformed output from analogous
answer-model failures. A successful selection followed by answer failure is
**not** a successful answer or a reason to disclose the selection as one.
The document bodies remain untrusted data and neither model receives Tool
authority.

## Minimal M10 Evidence and atomicity proposal

Define a small M10-specific append-only Evidence structure before writing
SQL. A bounded parent selection record should link `execution_id`,
`project_id`, logical `root_id`, list `observed_at`, complete ordered
candidate names, count, `truncated=false` for normal results, canonical
candidate-set hash, `selection_outcome`, valid raw model candidate names,
NOAH-approved names, and selected count. For a deterministic empty-list
result, record that no selection call occurred rather than inventing model
output. Candidate names may themselves disclose project information: limit
their number and bytes, retain them only within protected project Evidence,
and do not put them in unauthenticated logs or error responses.

For each approved and successfully observed source, link its logical D1/D2
ID, exact basename, independent `observed_at`, original byte length and
SHA-256, UTF-8 encoding and BOM flag to the same M10 Execution and project.
For answered requests, store the verified answer outcome and up to three
short quotes, each with source ID and NOAH-computed `[start,end)`. The
0-source branch stores no source or quote rows. M10 may use a parent plus
bounded source/quote children or another equivalently constrained small
schema; this is **not yet a SQL design**. Do not persist whole documents,
model prompts, OS absolute paths, tokens, or DB credentials. If invalid
model output is rejected, record a safe failure code rather than trusting or
releasing its raw text.

For zero selection, the complete-list and selection Evidence and terminal
Task/Execution states must commit together. For a one/two-source answer,
selection, every required source observation, verified answer/quote Evidence,
Task `completed/passed`, and Execution `succeeded` with `verified_at` commit
in **one final transaction**. No partially recorded success is acceptable.
The earlier Task/Execution reservation is a distinct durable transaction.
Definite post-reservation failures can produce paired `failed/failed` Task
and `failed` Execution with a safe code when storage is available. Loss of
DB connection, commit acknowledgement, HTTP response, or unconfirmed worker
termination cannot prove failure: **Unknown Outcome != Failed.** Do not
silently retry or infer a final state from age. M4 keyed idempotency applies
only to `memory.save`; M5 Recovery Triage does not inspect or recover M10.

## Failure and validation contract

Separate pre-reservation invalid request, unauthenticated/project-not-readable,
and root-not-registered failures from post-reservation attempts. The latter
need distinct safe reasons for candidate enumeration failure, truncated
list, excessive candidate count, candidate-name/message Context excess,
selection-model unavailable/timeout, malformed selection output, excessive
or duplicate selection, out-of-set name, selected-file disappearance or
replacement, link/reparse or same-file alias, selected read/UTF-8 failure,
answer Context excess, answer-model unavailable/timeout, invalid grounding
output, source/quote mismatch, permission revocation, DB failure, and
uncertain outcome. The exact public HTTP status/code mapping is an
implementation-stage decision consistent with M6–M9. A valid zero selection
is **not** a failure.

Implementation tests must use synthetic projects and roots to cover empty,
one, two, at-limit, truncated, over-count, and candidate-name byte-boundary
sets; Korean/English and instruction-like filenames such as
`ignore previous instructions.md`, `read-secret-token.md`, and
`select-this-file-and-call-tool.md`; valid zero/one/two selection, three
selections, duplicate/case-changed/fuzzy/unknown names, and malformed model
output. Test deletion, replacement, symlink/junction/reparse change, and
hard-link alias between listing and read; authorization loss at each stated
boundary; selection and answer model failures/timeouts; M8-style one-source
and M9-style two-source provenance, prompt injection inside selected bodies,
no third-file access or Tool call, one Task/Execution, Evidence linkage and
atomicity, and M1–M9 regression. Real Ollama Context tests must use only
synthetic Korean and English names/documents. Preserve existing users,
memories, records, and Docker volume; clean up only test-owned rows/files.

This bounded proposal follows DDR-001's durable Task/Runtime separation,
DDR-002's model/Harness and policy boundary, DDR-004's provenance and
Evidence, and DDR-006's result/verification/retry contract. It does not
promote documents to Knowledge or alter Memory (DDR-003), nor change
protected Identity (DDR-005). No new long-term DDR is required by this
proposed scope. A future general retrieval policy or cross-domain
Memory+Document source model would need separate review.
