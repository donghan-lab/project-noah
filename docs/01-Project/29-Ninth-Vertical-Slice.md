# M9 proposed two-document grounded answering contract

> Status: pre-implementation contract, 2026-09-29. No M9 API, migration,
> execution, or validation result exists yet. The implemented baseline is
> M1–M8 at `c0c97ffd6322884e4ae3fa18ff8e8c9105b0cde5`. This contract
> extends the bounded [M8 answer](27-Eighth-Vertical-Slice.md) and the
> [M7 safe read](25-Seventh-Vertical-Slice.md) within the existing
> [Runtime state boundary](../02-Architecture/Runtime/State.md). Blueprint 10
> and Accepted DDR-001–006 remain authoritative.

## Scope and proposed API

The proposed capability is `project.documents.answer.selected` at
`POST /projects/<project_id>/documents/answer-selected`. These names are
**proposals**, to be fixed before implementation; the existing M8 route and
capability keep their single-document meanings. The request contains exactly
two distinct, explicitly selected direct-child `.md` names in one project and
one bounded question:

```json
{
  "document_names": ["alpha.md", "beta.md"],
  "question": "What do these documents say about the test color?"
}
```

NOAH preserves the input order: `D1` denotes the first name, `D2` the second.
Reject arrays of any other length, non-string names, duplicate exact names,
case-only aliases on case-insensitive filesystems, and an invalid question
before execution reservation. If two distinct names identify the same file,
reject that pair rather than present one observation as two independent
sources. Apply the existing M7 exact
basename validation to **each** name, including its `.md`, direct-child,
reserved-name, hidden-name, separator, drive/UNC, and link restrictions. Both
names resolve only under the same operator-controlled project mapping. The
client supplies no OS path; the model neither selects nor discovers files.
Question limits initially inherit M8's 300 Unicode characters and 512 UTF-8
bytes, subject to the combined Context verification below.

One authorized request reserves **one M9 Task and one Execution**. NOAH calls
the M7 internal safe reader twice; it does not call M7 or M8 HTTP endpoints
and does not create their separate Tasks. Each file retains M7's 65,536
original-byte limit, strict UTF-8 and optional leading BOM behavior. M9 does
not read a third file, search, chunk, summarize freely, write a file or
Memory, or perform RAG, embeddings, vector search, Knowledge ingestion, Tool
chaining, shell execution, external connector calls, or multi-agent planning.

## Trust and source identity

NOAH's security, permission, and execution rules are enforced boundaries.
The authenticated user chooses two exact documents and a question within
those boundaries. Both document bodies are **untrusted data**. Text in D1
cannot instruct NOAH to read D2 differently; text in either source cannot
select a third document, run a Tool, override policy, access credentials, or
turn a model suggestion into authority. The model receives no Tool list or
Tool-call channel. NOAH sends only the bounded question, logical identifiers,
and verified decoded text in explicitly marked data fields, with separate
system-level instructions and output contract. No absolute root path, API
token, DB password, unrelated Memory, or other project document is added to
the Context. User-authored documents could themselves contain sensitive
text; the existing local-only model boundary and authorized disclosure policy
still apply.

Before Context construction, NOAH binds `D1` and `D2` to their ordered
document observations. The binding is per Execution, not a persistent
document identity. Each observation records its own logical `root_id`, exact
`document_name`, original byte length, SHA-256 of **original bytes** (including
any BOM), `observed_at`, UTF-8 encoding, and BOM flag. Decoded text supplied
to the model is exactly the M7-verified text after optional leading BOM
removal, without newline or Unicode normalization. Sequential reads are **not
one atomic filesystem snapshot**: different `observed_at` values and hashes
must be preserved. A later file change cannot rewrite what was observed.

## Combined Context budget

M8's 2,048 UTF-8 byte document cap is **not** a per-document M9 allowance.
For implementation planning, use a candidate cap of **2,048 UTF-8 bytes for
the two decoded document bodies combined**, plus a separately checked cap
for the complete model messages. This is a candidate, not an approved M9
limit or evidence that the current model handles two-source prompts well.
The complete budget must include system instructions, question, D1/D2 labels
and metadata, both bodies, structured-output instructions and an output
allowance under the current model's `num_ctx=4096` setting. Before fixing a
number, test synthetic Korean/Korean, English/English, and mixed-language
documents near the proposed boundary with the actual local Ollama model;
measure structured-output validity, latency, failures, and available output
headroom. Lower the cap if needed. A model or `num_ctx` change requires
renewed validation. Exceeding either finalized cap must produce explicit
`CONTEXT_TOO_LARGE`-family failure **before** model transmission. Never
truncate, silently omit one source, or describe a fragment as both full
documents.

## Model proposal and NOAH verification

The model may propose only this strict JSON shape:

```json
{
  "outcome": "supported",
  "evidence": [
    { "source_id": "D1", "quote": "exact excerpt from alpha.md" },
    { "source_id": "D2", "quote": "exact excerpt from beta.md" }
  ]
}
```

`outcome` is one of M8's `supported`, `partial`, `insufficient`,
`conflicting`, or `out_of_scope`. Evidence has **0–3** entries. Each entry
has exactly `source_id` and `quote`; the source ID must be `D1` or `D2`, and
the quote must be a nonblank exact excerpt of at most **240 Unicode code
points** from that source's verified decoded text. No model-written answer,
path, file name, line number, character offset, or Tool request is accepted.
Reject extra fields, invalid types, fabricated source IDs, a quote present
only in the *other* source, and repeated `(source_id, quote)` pairs. The same
quote text may appear once for D1 and once for D2; these are separate
source-qualified observations. NOAH calculates the first matching Unicode
code-point interval `[start, end)` within **the claimed source**, with no
normalization, and attaches that source's observed hash. The model never
supplies the interval. NOAH constructs a bounded response from verified
quotes and fixed qualifying text; it does not forward free-form model prose.

For this first two-source contract, `supported` requires at least one
verified quote from **each** source; this is source coverage, not proof that
the two quotes semantically agree or fully answer the question. `partial`
requires at least one verified quote and is appropriate when only one source
supplies an excerpt or the model reports only partial support from both.
`conflicting` requires at least one distinct, verified quote from **each**
source and presents both with a possible-conflict qualifier, without choosing
a winner. `insufficient` and `out_of_scope` require no quotes; the former
means no verifiable quote was obtained, **not** that neither document contains
an answer. The latter means the bounded two-document task is inadequate and
does not authorize another read. The model's outcome remains a proposal;
NOAH enforces these structural and source-coverage rules, but cannot prove
semantic agreement, conflict, relevance, truth, or exhaustiveness. The
response must show which source supplied each excerpt, including when only
D1 or only D2 has evidence.

`grounded: true` means only that every returned quote has an exact match and
NOAH-computed position in its identified, verified source observation. A
successful processing result with no quotes has `grounded: false`. Neither
grounded nor `supported` asserts real-world correctness or complete answer
coverage. The response includes logical source references, hashes, and
Evidence/Task/Execution references, but no complete document body or OS path.

## Permission, failure, and atomicity

Authenticate and check current project read membership at request entry.
Validate both names and the question and confirm the operator mapping before
Task/Execution reservation. Recheck token and membership before reservation,
immediately before **each** file open, immediately before transmitting either
body to the model, before final commit, and immediately before response
disclosure. One project's membership governs both files, but it can change
between D1 and D2 or during the model call. Revocation stops the next action;
it cannot retract Context already sent during an authorized interval. If
access disappears after a successful commit, withhold excerpts and answer.
No file access occurs after a denied preflight or denied pre-open check.

Both observations and the model proposal are required for an M9 answer. If
D1 or D2 has a definite read/verification failure, do not send only the
other document as a purported complete M9 Context. Distinguish first/second
input rejection (pre-Task), first/second read failure (post-reservation),
combined Context overrun, malformed model output, invalid source ID,
quote/source mismatch, permission revocation, confirmed model failure or
timeout, DB failure, and outcome uncertainty. A definite post-reservation
failure records paired failed Task/Execution when storage is available; no
successful answer or evidence is committed. If a timeout does not prove the
worker/model attempt has ended, or connection/commit acknowledgement/HTTP
response is lost, retain only provable durable state. **Unknown Outcome !=
Failed**; do not infer a terminal transition or silently rerun. M4 keyed
idempotency applies to `memory.save`, not this read. M5 Recovery Triage still
inspects `memory.save` only and does not recover M9.

## Minimal append-only Evidence proposal

Keep existing M7/M8 evidence tables and their **one observation per
Execution** meaning unchanged. A proposed M9-specific structure is:

| Record | Minimal fields and relation |
| --- | --- |
| Answer parent | `execution_id` unique FK to M9 Execution; `project_id`; validated `outcome`; recorded time. |
| Source observation child | `(execution_id, source_id)` unique with `source_id` constrained to `D1`/`D2`; ordinal 1/2; logical `root_id`, exact `document_name`, original byte length and SHA-256, `observed_at`, encoding, BOM flag. Exactly two source rows are required for success. |
| Verified quote child | Parent Execution and source-child reference; ordinal 1–3; exact short quote; NOAH-computed Unicode `[start,end)`; source hash/reference. Zero rows only for `insufficient` or `out_of_scope`. |

The names and SQL constraints are implementation decisions. Preserve source
ordering and prevent mismatched project or source links. Persist both source
observations, quote evidence, Task `completed/passed`, and Execution
`succeeded`/verification time in **one final transaction**. Full document
bodies, model prompts, machine absolute paths, tokens, and credentials do not
belong in Evidence or logs. The source hashes attest observed bytes but
cannot reconstruct a changed source without separately retained bytes. No
general Artifact Store or generic provenance platform is implied.

## Runtime and test contract

The proposed transition is preflight (no Task on rejection), durable
`running/pending` Task and `running` Execution reservation, D1 observation,
D2 observation, combined Context construction, one bounded local model call,
source-aware quote verification, final permission check, and atomic Evidence
plus terminal success. A verified `insufficient` or `out_of_scope` is a
successful **contract execution**, not proof of an answer. A definite
post-reservation failure may transition to `failed/failed` Task and `failed`
Execution; uncertain work remains unresolved for later inspection. No new DB
Task, Execution, or verification state value is proposed.

Implementation tests must cover both-source support, only D1, only D2,
partial evidence from both, cross-source conflict, no verified quote, and
out-of-scope questions; duplicate names, invalid names in either position,
source ID fabrication, D1 quote falsely attributed to D2, shared quote text
in both documents, exact and repeated-quote positions, 3/4 quote and
240/241-character boundaries; first/second read failures, combined byte and
full-message limits, Korean/Korean, English/English, and mixed-language
synthetic inputs; injection text in either document seeking a third read,
Tool call, secret or prompt disclosure; membership revocation between reads,
before model, before commit, and before disclosure; model failure/timeout,
storage uncertainty, one Task/Execution, source/quote Evidence linkage and
atomicity. Assert zero extra Tool calls and zero unverified citation. Run
M1–M8 regressions against Docker Compose PostgreSQL 17 with isolated
synthetic users/projects/roots and preserve existing data and volume. Record
actual results in a separate M9 Validation document **after** execution;
none is claimed here.

## Decisions still required before implementation

1. Fix the endpoint/capability names, HTTP failure codes, the exact
   two-source response fields, and the same-file alias detection method
   without changing M8's route.
2. Measure the final combined body and full-message budgets, including model
   output headroom, with the actual local model and `num_ctx=4096`.
3. Choose minimal M9 table names and database constraints for exactly two
   ordered source observations and source-linked quotes. Preserve the M7/M8
   table meanings and existing rows.
4. Specify the observable behavior for a document change between sequential
   reads and final disclosure, without claiming an atomic two-file snapshot.

These are local implementation decisions within DDR-001, DDR-002, DDR-004,
and DDR-006. The Memory/Knowledge and Identity boundaries of DDR-003 and
DDR-005 remain unchanged. No new long-term DDR is required by this proposed
slice unless implementation reveals a conflict with those boundaries.
