# M17 Bounded Session Follow-Up with Verified Document Provenance

> Status: **pre-implementation contract; not implemented or validated**.
> Baseline: `main@abd69ef5912109451255d3b4fe9fffeff1ff0fe0`.
> This contract is limited to a Session-scoped, single-source project-document
> follow-up. The Constitution, Blueprints, Accepted DDR-001–006, and existing
> M7/M8/M10/M12/M16 execution contracts remain authoritative.

## Goal and observable slice

An authenticated user receives a verified, one-document M10 answer in an
active Session. After a NOAH process restart, the same user asks a natural
follow-up about **that document**, without supplying a router ID or document
name. NOAH finds exactly one eligible earlier source in the same Session,
checks present authority and document bytes, and returns a new answer assembled
only from freshly verified quotes. This is bounded **source continuity**, not
general conversation memory or proof that the first answer was semantically
complete or delivered to the client.

The first M17 request uses one earlier M10 source, one current question, one
current file observation, and one current answer execution. A prior `partial`
answer may identify an eligible verified source; its incompleteness is not
converted to `supported`. Questions that require the earlier model's prose,
another source, or facts absent from the current document remain unsupported
under the existing M8 grounding outcomes.

## Existing facts and ownership

M16 `noah.sessions` stores owner and active/closed lifecycle only. Its
`routing_audit.session_id` association and bounded inspection expose router
references, not Conversation, answer text, Context, or capability authority.
M12 `routing_audit` is operational metadata. Its `observed` row may correlate
an M10 request, Task, and Execution, but `dispatch_prepared` is not evidence
that the delegate ran. The M10 Execution and its candidate/source/quote
Evidence are the previous answer's durable execution truth. In particular,
M10 persists logical `project_id`, `root_id`, document name, original byte
length/SHA-256, outcome, and source-qualified exact quotes; it does not
persist the previous question, complete document, or model-written answer.

M17 must not treat Session, audit order, a previous answer, or old project
membership as current information authority. Task progress remains in
`noah.tasks`; each execution remains in `noah.execution_records`. Context is
a bounded, reconstructable projection and never a canonical store. The
authenticated `noah.users` principal is not DDR-005's NOAH Identity Core.

## API decision and request contract

**Extend the existing `POST /requests/route` with one exact request shape:**

```json
{"question":"그 문서의 테스트 색상은?","project_id":"<canonical project UUID>","document_follow_up":true}
```

Require exactly one canonical `Noah-Session-Id` header, an existing Bearer
token, and no query parameters. The caller supplies the project ID; NOAH
never obtains it from a model proposal. The `document_follow_up` field must
be JSON boolean `true`, not an object or a string. Reject extra JSON fields,
duplicate keys, `memory_save`/`memory_suppress` mixtures, model-supplied
arguments, document names, source IDs, prior router IDs, OS paths, and an
`Idempotency-Key` for this shape. Apply the existing M8 question limits:
nonempty, at most 300 Unicode characters and 512 UTF-8 bytes. The public
Session ID is a lifecycle reference, not a capability permission.

This shape is **opt-in and request-specific**. Requests without it retain
M11/M13/M15 routing candidates, prompts, argument rules, results, and M16
optional-Session behavior. Direct M8 and M10 APIs remain unchanged. A
dedicated `POST /sessions/<id>/...` endpoint was considered, but M16 currently
associates only routed requests and M12's audit semantics belong to the
router. Extending the existing router keeps one established reservation and
correlation boundary without creating a second Session interaction ledger.
No generic dispatcher or Context Manager follows from this choice.

The new shape has a strict, separate routing-model schema:

```json
{"route":"project.documents.answer.followup | no_action"}
```

The example denotes exactly one of those two literal enum values; the actual
JSON contains only `route`. The model receives the current question and a
boolean that an explicit follow-up request shape is present. It receives no
Session/router/execution/project ID, filename, previous answer or quote,
document body, credential, or path during routing. Presence of the marker is
not itself an instruction to answer: unrelated, unsupported, or ambiguous
questions should select `no_action`. NOAH validates the exact proposal and
never accepts generated arguments. This follows M13/M15's shape-specific
proposal pattern; model selection grants no permission or source authority.

## Prior-source determination

Only NOAH resolves history. For this first Slice, the eligible set is
intentionally narrower than a general conversational reference algorithm:

1. From one complete DB statement snapshot taken **after** the Session lock
   described below, inspect every committed audit row associated with this
   actor and Session except the current router row. Membership in this set
   depends on visibility in that snapshot, not `created_at`, `router_id`,
   server arrival time, or the M16 inspection display order. A nonterminal
   row with an unknown route might be M10, so its project cannot yet be
   classified; an in-progress or uncertain M10 attempt likewise makes the
   context unconfirmed. Do not infer that an incomplete attempt failed.
2. Scope verified M10 sources and ambiguity to the **caller-supplied,
   currently authorized `project_id`**. `routing_audit` has no project ID:
   classify an observed M10 result through its validated
   Execution/parent Evidence project binding. A conclusively different
   project's result is excluded even if it has one or two sources; do not
   reauthorize that other project merely to classify it. A definitely
   failed/no-source result supplies no source. If an otherwise relevant
   audit cannot be safely classified as same-project, other-project, or
   definite no-source, fail closed with a generic error. Never expose the
   other project's name, ID, former membership, activity count, or content.
3. Count qualifying **verified single-source M10 result occurrences** for
   the requested project, not distinct filenames. Require exactly one. A
   same-project observed two-source M10 result makes the reference ambiguous,
   even alongside one qualifying single-source result. Two qualifying
   results are ambiguous even if they name the same file: NOAH cannot
   silently choose a previous Execution. Prior completed `no_action`,
   Memory, save, and suppression routes do not supply document context.
   No arbitrary newest-row choice, model choice, pagination prefix, or
   silent filtering is allowed. A DB timeout or incomplete scan is failure,
   not evidence of zero or one source.
4. The qualifying result must be a committed `observed`, HTTP 200,
   `delegate_returned` M10 audit with a verified `request_id`, Task ID, and
   Execution ID. Its actor and Session must equal the current actor and
   Session; its M10 Execution must have capability
   `project.documents.answer.auto`, status `succeeded`, `verified_at`, and a
   matching completed/passed Task. The observed M10 project must equal the
   caller's currently authorized `project_id`.
5. Its M10 parent Evidence must show `selection_outcome=selected`,
   `selected_count=1`, exactly one approved selected name, and answer outcome
   `supported` or `partial`. Exactly one D1 source observation must match
   that name, and at least one (at most three) D1 quote Evidence row must be
   structurally valid. This derives the historical `grounded=true` minimum;
   it does **not** prove answer relevance or real-world truth. A two-source
   result, `no_document_selected`, quote-free result, failed execution, or
   uncertain result cannot be used.

Cross-check the audit IDs, actor, Session, M10 request/Task/Execution,
project, parent/source/quote rows, source order, and outcome; do not trust an
audit UUID merely because it exists. Invalid cross-record provenance is a
verification failure, not a fallback to another row. Define a finite SQL
statement timeout; a query unable to establish the complete candidate set
fails closed. A count/`LIMIT 2` optimization is acceptable only if it proves
zero, exactly one, or more than one **over the complete qualifying set** and
does not hide unconfirmed or inconsistent attempts.

The decisive candidate check and M17 Task/Execution reservation share one
short, explicitly `READ COMMITTED` transaction. Revalidate the token, then
acquire the Session owner row `FOR UPDATE` in a **separate SQL statement**;
wait for any M16 reservation/close holding that lock. Confirm the Session
still belongs to this actor and the current M17 audit reservation and
`dispatch_prepared` update already committed under that Session. Do **not**
require `closed_at IS NULL` again.
Only after the lock has been acquired, start a new, complete candidate SQL
statement and take its `READ COMMITTED` snapshot. That statement's snapshot
start is the prior-source selection point. While M17 holds the Session lock,
no new M16-compliant scoped audit reservation can commit. An M10 reservation
that committed while M17 waited is therefore included in the **new**
candidate snapshot; it is never missed by reusing the waiting lock
statement's older snapshot. Read and classify every relevant committed row
from that one snapshot, including the M10 Execution/Evidence bindings needed
to classify observed results. Existing M12 audit updates do not take the Session
lock, but a terminal `observed` row is immutable; a row not terminal in this
snapshot is rejected as unconfirmed if it could be a same-project M10,
even if it becomes terminal during or after the scan. Do not mix a later
audit update into this decision or convert an in-progress row to a definite
failure. Validate the selected immutable M10 execution/Evidence and current
project authority, then reserve one M17 Task/Execution before committing
this transaction. Its confirmed commit makes that snapshot-based selection
the execution's accepted provenance. Release the Session lock before file
or model work. An M10 reservation after the selection point, or an earlier
in-progress request that completes after a rejected selection, does not
retroactively change an already confirmed M17 decision. No preliminary
unlocked lookup is authoritative. Use a finite lock/statement timeout;
on timeout, incomplete scan, deadlock, or reservation commit uncertainty,
fail closed without another source choice or automatic transaction retry.
Only a confirmed rollback proves zero new Task/Execution rows; if the
reservation commit or rollback result is uncertain, use
`TOOL_OUTCOME_UNKNOWN` and do not assert that those rows are absent.
The lock order is token check, Session row, then candidate read and M17
Task/Execution insert; do not lock audit rows ahead of the Session row.
M16 reservations/close acquire the Session row, whereas M12 stage updates
write their audit row in separate transactions without acquiring that Session
row. This order avoids a new Session-to-audit-row lock cycle; bounded waits
and deadlock-as-failure remain required. No extra ordering counter or Session
conversation state is needed for this snapshot-scoped guarantee.

An M10 audit proves an observed delegate result, not that the first HTTP
response reached the user. M17 claims continuity from a verified source, not
from confirmed human receipt or a stored conversation turn.

## Present authorization, file identity, and Context

Authenticate and validate the request before an audit/model call. Require
present project read membership before routing-model exposure. M16 atomically
rechecks the original credential and active Session owner while reserving
the current audit row. A close committed **before that reservation** rejects
the new association with `SESSION_CLOSED` and prevents model/delegate work.
After a confirmed reservation, route validation and, for a selected route,
confirmed `dispatch_prepared` precede the **one** internal M17 delegate call.
Prior-source resolution is the delegate's first bounded operation, before
it creates a Task or accesses a file; a source-resolution failure returns a
safe delegate failure with null Task/Execution IDs. An unconfirmed
`dispatch_prepared` prevents the delegate and any M17 Task. The route and
delegate continue even if close commits before M17 Task reservation: this is an
already associated in-flight request, not a new Session association. The
later Session lock verifies owner and correlation and serializes the
candidate snapshot; it does not impose a second active-state gate. Do not
expose the prior source name to the routing model. Recheck the credential,
project membership, and unique prior reference at M17 Task reservation.
Session close itself is not token or project-permission revocation and does
not retroactively cancel the Task/Execution. Recheck token and project
permission before current document content reaches the answer model, at
terminal Evidence commit, and immediately before public disclosure. If
permission disappears after a successful commit, withhold the answer without
rewriting the committed Task/Execution truth. Context already delivered to a
local model cannot be withdrawn retroactively.

Use the current operator-registered root and M7 no-follow, bounded safe-read
plus independent observation verification. Require the **same logical
`root_id` and exact `document_name`**, and compare current original byte
length, BOM/encoding observation, and SHA-256 with the prior M10 source.
Recheck stored prior quotes against the freshly decoded text and their
NOAH-computed Unicode `[start,end)` positions. A different file, missing
file, root mapping mismatch, or changed bytes is an explicit failure before
answer-model exposure; never silently answer from replacement content.
Repeat the bounded safe-read and byte-identity check before terminal
Evidence commit, then again immediately before public disclosure. A change
detected at commit prevents success Evidence; a change detected after a
confirmed success commit withholds the response without rewriting durable
Task/Execution truth. These checks prove the file observations at their
respective times, not that the filesystem can never change afterward.
Because M10 Evidence does not store a prior filesystem file ID or absolute
path, this proves logical-name and byte-content equality, **not** identity
of the physical inode/file object across observations. Do not invent that
stronger guarantee or turn sequential reads into one filesystem snapshot.

Construct only a bounded, model-facing projection: the new user question,
logical document identifier, and **freshly verified** current document
body, with explicit data delimiters and untrusted-document labeling. The
system instruction may state that “that document” refers to this one
verified source; it does not insert the old model answer or raw audit row.
No general conversation transcript, previous question, secret, credential,
OS path, or additional Tool channel enters either model. The document and
old quotes are data, never instructions. Apply the existing M8 known-credential
rejection to each model-facing question, identifier, and document payload;
rejected input is not replaced with redacted or truncated content. Preserve
M8's limits of 2,048 UTF-8
bytes for decoded document content and 3,456 UTF-8 bytes for complete system
plus user answer-message bodies; keep the 300-character/512-byte question
limit. Count actual serialized bytes and reject with `CONTEXT_TOO_LARGE`
instead of truncating. A changed model or prompt must be validated against
these limits before implementation claims them. The answer model returns
only M8's `outcome` plus at most three exact quotes of at most 240 Unicode
characters. NOAH verifies each quote and computes its first `[start,end)`;
NOAH assembles the public answer. `grounded` means literal provenance, not
semantic completeness or real-world truth.

## One M17 execution and durable lineage

The routed follow-up uses capability `project.documents.answer.followup`.
M12 owns **one** current router audit; an eligible `no_action` owns only that
audit. On selected follow-up, the M17 delegate owns **one** new Task and one
new Execution. It reuses M7 safe-read and M8 Context/quote primitives, not
M7/M8/M10 HTTP APIs or their Task/Execution creators. Calling the full M8
answer function and later appending lineage would leave two independently
committed result boundaries, so that is not the M17 ownership model. No
parent Task, duplicate Evidence in M8/M10 tables, or second router is made.

An additive M17 Evidence table is justified to link the **new Execution**
to the exact earlier router and M10 Execution selected for this answer. One
row per successful M17 Execution contains only: current Execution ID and
router ID; previous router and M10 Execution IDs; logical project/root and
document name; previous/current original-byte SHA-256, current byte length,
encoding/BOM and `observed_at`; M8 outcome; and up to three validated exact
quote/Unicode-position records. Do not duplicate the candidate list, full
document, prior question/answer, model output, prompt, token/hash, password,
or OS/local-mapping path. Constrain cardinalities and value domains in SQL
and validate cross-row ownership, Session, status, and hashes in NOAH code.
Use non-cascading references for the current Execution and the referenced
audit/previous Execution records; a Session ID need not be duplicated in the
Evidence because both audit rows already carry it. These references protect
provenance but constrain future deletion order. M17 creates **no Session
delete/retention policy**; future user-controlled deletion must account for
these links rather than cascade silently. The new Evidence follows existing
Task/Execution Evidence retention behavior; M17 adds no TTL or automatic
purge. Only the current owner can receive
the resulting provenance through this authenticated request; no public
audit/Evidence browser is added.

Reserve the M17 `running/pending` Task and `running` Execution in the locked
candidate-check transaction after the unique source and current authority
have been checked, and before file/model work. Reservation acknowledgement must be confirmed
before dispatch. The **single final transaction** inserts M17 current
observation, prior/new lineage, and verified quotes as one Evidence row and
marks the same Task `completed/passed` and Execution `succeeded/verified`.
There is no success without all of them. A definite file/model/evidence
failure records the existing failed Task/Execution pattern when DB is
available; it does not write success Evidence. If final commit acknowledgement
is unknown, the Evidence and terminal states may or may not exist together:
return an unknown outcome with the current request/Task/Execution IDs and
do not guess failure or retry. M5 recovery remains `memory.save`-only.

The separate M12 terminal `observed` audit update follows the delegate
result. Its failure or unknown acknowledgement cannot reverse a confirmed
M17 result, rewrite Evidence, or cause another delegate call. Preserve the
delegate's response and mark `routing.audit_status=unconfirmed` if it can be
returned. Conversely, an `observed` audit by itself is not M17 Evidence or
Task truth. `dispatch_prepared` only establishes intent. **Unknown Outcome
!= Failed.**

Migration after 012 must add the single M17 Evidence relation and minimally
extend the existing `routing_audit` validated-route, delegate-capability,
and dispatch-prepared CHECK constraints to admit
`project.documents.answer.followup`. It must preserve all old route values,
rows, Session-less requests, and M10/M12/M16 meanings. Register it after
012 in `noah/db.py`. Do not add a Conversation store, generic Context
snapshot, new Task state, broad FK coupling, cascade deletion, or reset of
the PostgreSQL named volume.

## Response and failure contract

The selected successful route keeps the M11/M12 outer shape and HTTP 200:

```json
{
  "status":"succeeded",
  "router_id":"<current router UUID>",
  "routing":{"outcome":"selected","capability":"project.documents.answer.followup","stage":"delegated","audit_status":"recorded | unconfirmed"},
  "result":{
    "status":"succeeded","request_id":"<delegate UUID>",
    "task_id":"<one M17 Task UUID>","execution_id":"<one M17 Execution UUID>",
    "capability":"project.documents.answer.followup",
    "project_id":"<caller project UUID>",
    "outcome":"supported | partial | insufficient | conflicting | out_of_scope",
    "grounded":true,
    "answer":"<NOAH-assembled text>",
    "document":{"root_id":"<logical ID>","document_name":"<exact basename>",
      "byte_length":123,"content_sha256":"<original-byte hash>",
      "observed_at":"<ISO-8601 time>","evidence_execution_id":"<M17 Execution UUID>"},
    "context_source":{"prior_router_id":"<verified UUID>",
      "prior_execution_id":"<verified M10 UUID>"},
    "evidence":[{"quote":"<exact excerpt>","start":0,"end":1}]
  }
}
```

The enum strings separated by `|` above denote alternatives, not literal
response values. `grounded` is `false` with empty evidence for a valid
`insufficient` or `out_of_scope` result, just as in M8. A valid `partial`
does not assert full semantic coverage. `context_source` identifies the
verified prior execution without requiring the user to provide its router
ID. No absolute path, raw prompt, credential, or entire document is returned.
If final audit update is unconfirmed, the selected delegate result and HTTP
status remain unchanged. A route-model `no_action` retains M12's HTTP 200
shape, one audit, `result=null`, and zero M17 Task/Execution/Evidence.

| Boundary | Safe response | Durable effect |
| --- | --- | --- |
| Missing/bad token, malformed shape/header/project/question, missing Session header | Existing safe 400/401/404 codes; missing required header uses 400 `SESSION_ID_REQUIRED`. | No audit, model, delegate, Task, or Evidence. |
| Foreign/absent Session, Session closed before current audit reservation, or unreadable project | Existing `SESSION_NOT_FOUND` 404, `SESSION_CLOSED` 409, or `PROJECT_NOT_FOUND` 404 without existence details. | No new audit/model/delegate where rejected before reservation; later close alone does not cancel a reserved route. |
| Routing model unavailable/timeout/malformed, or invalid route | Existing M12 `ROUTING_OLLAMA_UNAVAILABLE` 503, `ROUTING_OLLAMA_TIMEOUT` 504, or `ROUTING_MODEL_OUTPUT_INVALID` 502. | One reserved/terminal audit as confirmable; no delegate/Task/Evidence. |
| No qualifying verified M10 result, including quote-free/zero-selected or unsupported-outcome results | 409 `FOLLOWUP_SOURCE_NOT_FOUND`. | Safe delegate failure after confirmed `dispatch_prepared`; terminal audit observes the failure without fabricated Task/Execution IDs. |
| Multiple qualifying same-project M10 results or an observed same-project two-source prior result | 409 `FOLLOWUP_SOURCE_AMBIGUOUS`. | No source chosen or M17 Task/Execution. |
| Earlier potentially relevant nonterminal/uncertain audit or unclassifiable project, incomplete candidate scan, or inconsistent M10 correlation/Evidence | 409 `FOLLOWUP_CONTEXT_UNCONFIRMED` for uncertain prior state/project; 503 `FOLLOWUP_CONTEXT_UNAVAILABLE` for incomplete DB query; 502 `FOLLOWUP_PROVENANCE_INVALID` for definite inconsistency. All messages are project-neutral. | No fallback, model-generated source, or M17 Task/Execution. |
| Current root/name/bytes differ, document missing, or Context exceeds limit | 409 `FOLLOWUP_SOURCE_CHANGED`, existing safe file failure, or 413 `CONTEXT_TOO_LARGE`. | If already reserved, one definite failed M17 Task/Execution; no success Evidence. |
| Permission/token lost before document/model or final disclosure | Existing non-enumerating 401/404 denial. | No private answer disclosure; retain any already committed Task/Execution truth. |
| M12 reservation/pre-delegate audit definite failure or acknowledgement unknown | Existing `ROUTING_AUDIT_UNAVAILABLE` / `ROUTING_AUDIT_OUTCOME_UNKNOWN` 503. | No M17 delegate/file/model answer call or Task/Execution. No retry. |
| M17 Task reservation or final commit acknowledgement unknown | 503 `TOOL_OUTCOME_UNKNOWN` with provisional IDs where allocated. | Outcome unconfirmed; no guessed failed state or automatic retry. |
| Only terminal M12 audit update fails after a confirmed M17 result | Keep the original delegate HTTP status/body and `routing.audit_status=unconfirmed`. | M17 Task/Execution/Evidence remain canonical. |

Use the repository's existing safe failure envelope: `status=failed`,
`request_id`, nullable `task_id`/`execution_id`, and bounded `failure` with
code/category/message/recoverable/retryable. The historical top-level
`status=failed` envelope for `TOOL_OUTCOME_UNKNOWN` is **not** a conclusion
that its Task or Execution failed; its code and stored records express the
unknown outcome. `retryable=false` for M17 unknowns. Routing failures carry
`routing.outcome=failed`, a stage and null `result`; after a confirmed audit
reservation they also carry `router_id` and `routing.audit_status` according
to M12. A delegated failure retains the selected capability and its own
safe result. A prior-source rejection returned by the M17 delegate after
confirmed `dispatch_prepared` is an observed delegate failure with a real
delegate request ID, `delegate_returned` observation class, and null
Task/Execution IDs; it never fabricates a Task correlation. Do not
synthesize a successful answer from an old quote.

## Tests, actual model, and operator E2E to perform after implementation

Deterministic tests must cover exact/extra/duplicate-field request parsing,
header count, authentication, Session owner/closed state, project membership,
no-model/no-audit preflight, no_action, invalid model output, and exactly one
delegate on selection. Prove the complete prior candidate decision for zero,
one, two, same-project two-source, different-project single/two-source,
no-selection, quote-free, `supported`, `partial`, failed, nonterminal,
uncertain, corrupted/swapped IDs, cross-user/Session/project, and DB timeout
cases. A revoked other project's observed M10 source must neither count nor
expose project details; an unclassifiable in-flight M10 must fail closed.
Test both M16 close/reservation orders: close first rejects without model or
delegate, while confirmed reservation first allows the in-flight selected
route to complete even if close commits before M17 Task reservation. Test
`no_action` in that latter order too; close is not permission revocation.
Inject a concurrent M10 reservation that holds the Session lock as M17 waits:
its committed audit row must appear in the subsequent candidate snapshot.
Inject an earlier M10 audit update before and after that snapshot: a
committed observed result is classified, while an incomplete snapshot row
is rejected even if it completes moments later. Prove no newer reservation
can commit until the candidate-check transaction releases the Session lock,
and that deadlock/timeout or incomplete scan yields no Task/Execution and no
retry. Separately race membership/token revocation and document changes
between prior lookup, Task reservation, safe-read, model, commit, and
disclosure; verify no silent source substitution. Check old-vs-current SHA,
root/name, exact prior/current
quotes and Unicode positions, 2,048/3,456-byte boundaries, untrusted
instructions, no extra Tool call, and no credential/path exposure.

Fault tests must verify audit reservation, route validation, dispatch,
M17 Task reservation, final Evidence/terminal commit, and terminal audit
definite/acknowledgement-unknown behavior; one Task/Execution only; no
partial successful Evidence; no automatic retry/fallback; and no M5 recovery
claim. Test old Session-less M11 routes, M13 save, M15 suppression, M16
inspection/close, M8 direct answer, M10 auto answer, and full M1–M17
regression. Actual local Ollama opt-in checks should distinguish a Korean or
English natural document follow-up from an unrelated `no_action` question,
then verify the answer stage separately. Each planned model case is called
once; selection quality is not inferred from schema validity alone.

For a minimal operator HTTP E2E, snapshot every existing PostgreSQL table's
counts and private row fingerprints and record the named-volume identity.
Use only a synthetic user/token, one synthetic project/read membership, a
Git-excluded operator mapping, and one small synthetic `.md` containing two
public test facts. Create one Session; make exactly one M10 routed question
that selects this document and yields a verified quote. Stop and restart
NOAH. Send one planned follow-up shape on the same active Session and
project, without a router ID or document name; verify one prior/new lineage,
one M17 Task/Execution, source byte identity, exact new quote/position,
current permission, and the separate M12 audit correlation. An unexpected
model choice or unknown response stops the run: never resend to obtain a
preferred result. No live fault injection is required. Stop only services
started for this run; verify exact synthetic ownership and file hashes,
remove only test-owned rows/files in a reviewed transaction/order, retain
the additive migration and named volume, and compare all original counts
and private fingerprints to the baseline. No personal Memory or document
enters the model.

## Explicit exclusions and acceptance gate

M17 does not implement general multi-turn chat, durable Conversation/message
text, full answer replay, automatic Memory/Knowledge extraction, generalized
Context selection or caching, multiple-document combination, persistent
cross-Session Task orchestration, approval/workflow engines, autonomous
planning, external tools/MCP, a generic Agent or capability registry, or
automatic recovery/retry. There is no new Session deletion or retention
policy, but the new provenance references must be included when such a
policy is designed later.

Implementation acceptance requires deterministic and full regression tests,
a separately reported actual-model check, one synthetic restart/manual E2E,
exact cleanup and private baseline restoration, and a final independent
contract/code/Evidence review. **None of these M17 validations has yet been
run.** No Blueprint or Accepted DDR change is required by this bounded
contract; a discovered conflict in ownership, atomicity, or privacy must be
reported before implementation rather than hidden by a generic framework.
