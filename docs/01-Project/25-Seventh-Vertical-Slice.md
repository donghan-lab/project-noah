# M7 proposed slice: verified single project document read

> Status: pre-implementation scope and safety contract, 2026-09-28. No M7
> code, database migration, API, or validation result exists yet. The current
> architecture baseline remains the Blueprint, Accepted DDR-001–006,
> [Runtime/State](../02-Architecture/Runtime/State.md), and the
> [M6 document-listing contract](23-Sixth-Vertical-Slice.md).

## Goal and boundary

An authenticated project reader selects **one** directly contained, regular
`.md` document in an operator-registered document root. NOAH returns its
bounded text and verifiable source metadata. This is a read-only observation
of a file at a particular time; it is not a promise that the file remains
unchanged. The first M7 does **not** summarize the text with an LLM or send
the text to a model. A later Slice may separately define model context,
prompt-injection defenses, and grounded summary verification.

The first M7 does not add recursive discovery, Knowledge ingestion, a generic
Artifact Store or Harness, shell execution, or file creation, modification,
and deletion. It does not change M1–M6 behavior or add database state values.

## Target, permission, and path contract

- The authenticated request supplies `project_id` and one exact
  `document_name` **basename**. An M6 listing can help choose the name, but
  eligibility and permission must be checked afresh; a prior listing grants
  no lasting access. The API and any model cannot provide or alter an OS path.
- Reject an empty name, `.`, `..`, a dot-prefixed/hidden name, any `/` or `\`
  separator, a drive or UNC path, a colon, control characters, Windows
  reserved device names or ambiguous trailing dots/spaces, and a name that
  does not end in `.md`. Match the exact direct-child name; do not interpret
  it as a relative path, wildcard, or case-insensitive search.
- Resolve the root only from the local operator allowlist for `project_id`.
  Authenticate and check project read membership before reading; recheck
  immediately before the Tool opens the target and before releasing the text
  in a successful response. Loss of membership withholds the text.
- Reject missing/inaccessible roots and symlink, junction, or reparse-point
  roots, ancestors, and target entries. The target must be a regular direct
  child, never a directory or linked file. Do not follow links, recurse, or
  fall back to a different root. If the platform cannot enforce this for the
  target open, fail closed and review the boundary before implementation.
- As in M6, this contract protects against user, model, and remote input
  escaping the registered root. It does not claim to defeat a malicious
  process with the same Windows user privileges swapping filesystem entries
  between checks and use. That threat needs a stronger OS/handle boundary
  before NOAH can claim resistance to it.

## Bounded content and verification

- Initial maximum: **65,536 raw bytes** per file. Check the size before
  reading and read no more than 65,537 bytes to detect an over-limit or
  changing file. Reject an oversized file instead of truncating its text;
  `content_sha256` must describe the entire returned observation.
- Accept strict UTF-8 text, with or without a leading UTF-8 BOM. No encoding
  guessing, lossy replacement, or automatic normalization of line endings.
  Reject invalid UTF-8, NUL-containing/binary content, and files that change
  or cannot be consistently observed during the bounded read. Keep a BOM
  indicator so the original bytes can be distinguished from decoded text.
- Treat document text as **untrusted data**. Instructions inside it have no
  authority over NOAH, permissions, Tool selection, or the response contract.
  The first M7 returns the observed text as data, with no model interpretation.
- Verify the returned content against the same bounded byte observation used
  for evidence. At minimum, retain `execution_id`, `project_id`, logical
  `root_id`, exact `document_name`, observation time, raw byte count,
  `content_sha256` of the original bytes (including a BOM when present), and
  decoding/BOM metadata. Link this evidence append-only to the Execution
  Record. Do not put full text or the machine's absolute path in evidence or
  logs. The API may return the text and corresponding logical source, hash,
  and observation time; the hash proves consistency with that observation,
  not the truth of statements in the document.
- The successful response must contain only text decoded from the bytes whose
  length and SHA-256 were verified. Evidence, Task `completed/passed`, and
  Execution `succeeded` with verification time commit together before NOAH
  returns a successful response. Existing document changes after observation
  require a new read and new evidence, not mutation of prior evidence.

## Failure and uncertain outcome contract

Authentication, project membership, malformed target, absent mapping, and
other pre-Tool rejections must not create a Task or Execution Record. After
preflight, recheck permission and durably reserve `running/pending` Task and
`running` Execution before starting the read worker, following the M6 Tool
boundary in [Runtime/State](../02-Architecture/Runtime/State.md).

Distinguish invalid target, inaccessible project, missing mapping, missing
or inaccessible root, missing or non-regular document, oversized document,
invalid/binary text, definite Tool/verification failure, timeout, and DB
failure. A definite post-reservation failure permits a paired
`failed/failed` Task and `failed` Execution with a safe failure code if the
database is available. API errors and logs must omit absolute paths, API
tokens, database credentials, and document bodies.

**Unknown Outcome != Failed.** A timeout without proof that the worker has
stopped, lost DB connectivity or commit acknowledgement, or a lost HTTP
response cannot justify a guessed terminal state. Do not silently rerun an
uncertain attempt. Although reading does not modify the source file, a new
attempt can observe different bytes and create distinct durable records. M4
Idempotency-Key mapping applies only to `memory.save`; M5 Recovery Triage
currently inspects only `memory.save` and neither diagnoses nor recovers M6
or M7 Tool executions.

## Minimum implementation verification for a future M7 task

Use a synthetic user, project, membership, and temporary root, preserving
existing users, memories, and volumes. Check exact-name selection, permission
revocation immediately before open and before response, empty/missing and
oversized files, UTF-8 with/without BOM, invalid UTF-8/NUL, symlink/reparse
and non-regular entries, root absence/access failure, and bounded-read
consistency. Verify that content and evidence hash match, that no absolute
path or document body enters logs, and that Task/Execution/evidence states
remain consistent across success, definite failure, timeout, and DB errors.
Run M1–M6 regressions. This section specifies future tests; none have been
run for M7 in this documentation checkpoint.

## Details to fix during implementation review

Choose the exact HTTP route, request/response field names, failure codes,
and additive evidence schema. Establish how the Windows file handle is
opened without following a reparse target and how a concurrent replacement
is detected within the stated threat boundary. These choices must preserve
the permissions, byte limit, strict decoding, evidence, and unknown-outcome
rules above. A new DDR is unnecessary for this narrow read if those rules
fit the accepted boundaries; a broader Tool or security change must be
reviewed against the existing DDRs first.
