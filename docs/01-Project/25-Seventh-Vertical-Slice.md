# M7 restricted project document read

> Status: implemented on 2026-09-28 against this pre-implementation safety
> contract. The architecture baseline remains the Blueprint, Accepted DDR-001–006,
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
other pre-reservation rejections must not create a Task or Execution Record. After
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

## Implementation verification requirements

Use a synthetic user, project, membership, and temporary root, preserving
existing users, memories, and volumes. Check exact-name selection, permission
revocation immediately before open and before response, empty/missing and
oversized files, UTF-8 with/without BOM, invalid UTF-8/NUL, symlink/reparse
and non-regular entries, root absence/access failure, and bounded-read
consistency. Verify that content and evidence hash match, that no absolute
path or document body enters logs, and that Task/Execution/evidence states
remain consistent across success, definite failure, timeout, and DB errors.
Run M1–M6 regressions. Executed test results and data-preservation checks are
recorded separately in the [M7 validation report](26-Seventh-Slice-Validation.md).

## Implemented API and evidence

The API accepts only an exact filename in JSON at
`POST /projects/<project_id>/documents/read`:

```powershell
$body = @{ document_name = 'guide.md' } | ConvertTo-Json
$headers = @{ Authorization = "Bearer $env:NOAH_API_TOKEN" }
Invoke-RestMethod -Uri "http://127.0.0.1:8080/projects/$env:NOAH_PROJECT_ID/documents/read" `
    -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' -Body $body
```

On Windows PowerShell 5.1, inspect a rejected request through
`ErrorDetails.Message`; `GetResponseStream()` may be empty:

```powershell
try {
    $badBody = @{ document_name = '../guide.md' } | ConvertTo-Json
    Invoke-RestMethod -Uri "http://127.0.0.1:8080/projects/$env:NOAH_PROJECT_ID/documents/read" `
        -Method Post -Headers $headers -ContentType 'application/json; charset=utf-8' `
        -Body $badBody -ErrorAction Stop
    throw 'Expected INVALID_DOCUMENT_IDENTIFIER'
} catch [System.Net.WebException] {
    $failure = $_.ErrorDetails.Message | ConvertFrom-Json
    if ([int]$_.Exception.Response.StatusCode -ne 400 -or $failure.failure.code -ne 'INVALID_DOCUMENT_IDENTIFIER') { throw }
    $failure.failure.code
}
```

Use an existing project with read membership and an operator-approved
`config/project_documents.local.json` mapping as described in [M6 setup](23-Sixth-Vertical-Slice.md).
The response contains the decoded text, byte count, original-byte SHA-256,
Task and Execution IDs, and a logical evidence reference; it contains no OS
path. The capability is `project.documents.read`. The additive
`noah.document_read_evidence` table stores one observation per execution with
project/root/name, time, length, hash, UTF-8/BOM metadata, but no body or path.
Files over the byte limit fail; no `truncated` result is used.

On Windows, the fixed Tool adapter opens the basename with Win32 `CreateFileW`
and `FILE_FLAG_OPEN_REPARSE_POINT`, then checks the opened handle's attributes
before reading. A reparse target is rejected; the opened handle supplies the
bounded bytes and metadata. NOAH independently opens and compares the bytes
before finalizing evidence. The stated same-user filesystem race remains
outside this Slice's guarantee. A broader Tool or security change must be
reviewed against the existing DDRs first.
