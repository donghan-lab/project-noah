# M17 Automated Validation — Bounded Session Document Follow-Up

> Status: **implementation-stage deterministic validation passed**; initial run
> 2026-10-10 and post-review concurrency-test rerun 2026-10-11.
> Contract: `52-Seventeenth-Vertical-Slice.md`, based on
> `main@abd69ef5912109451255d3b4fe9fffeff1ff0fe0`.
> Isolated actual Ollama HTTP E2E: first attempt stopped at M10 routing;
> a separate second run on 2026-10-11 verified M10 and M17 HTTP/Evidence behavior.
> Second-run environmental cleanup remains incomplete. No private-DB E2E was run.

## Implemented and checked

The request-specific `document_follow_up: true` branch extends
`POST /requests/route` without changing the existing read, save, and suppress
request shapes. Routing proposes only `project.documents.answer.followup` or
`no_action`; the M17 delegate resolves one prior M10 source from a complete
READ COMMITTED statement snapshot after the Session row lock. That snapshot
is a DB visibility boundary, not a guarantee of human conversation order.
The delegate freshly checks the logical root, document name, original bytes,
prior quotes, permission, and bounded M8 answer quotes. It owns one new
Task/Execution pair. The new M17 Evidence row and terminal states share a
single final transaction; M12 audit remains separate operational metadata.

Migration `013_document_followup_evidence.sql` minimally extends three
`routing_audit` route constraints and adds one non-cascading lineage/Evidence
table. It was applied **only to a disposable PostgreSQL 17 test database**
through the existing initialization path. It was not applied to the existing
personal development database or named volume.

## Deterministic results

| Validation | Result |
| --- | --- |
| M17 focused tests | 24 passed, 0 failed |
| M1–M17 full suite | 221 total: 211 passed, 10 opt-in skipped, 0 failed |
| Existing M1–M16 suite within full run | 197 total: 187 passed, 10 opt-in skipped, 0 failed |

Focused tests cover a real synthetic M10 Evidence producer followed by M17,
one verified previous source, a prior `partial` result, other-project
exclusion, same-project ambiguity, nonterminal audit rejection, source byte
changes, corrupt prior quote and malformed safe-read identity rejection,
permission revocation, `no_action`,
missing Session/invalid Idempotency-Key/unreadable-project preflight,
quote-free prior exclusion, invalid routing proposals, pre-delegate audit
failure, Session close before
and after current audit reservation, a new M10 record committed while M17
waits for the Session lock, and an audit update after a rejected snapshot.
The final concurrency regression also holds the M17 Session lock after the
candidate statement snapshot, confirms through PostgreSQL blocking PIDs that
a new M10 Audit reservation cannot commit while that lock is held, then
releases M17 and verifies that the later M10 record does not retroactively
change the accepted M17 prior source. The result remains a DB snapshot
guarantee, not a human conversation-order guarantee.
They also cover a bounded candidate-query timeout, uncertain Task reservation
commit acknowledgement, definite final Evidence rollback, uncertain final
commit acknowledgement, terminal audit uncertainty, and withholding a
committed answer when permission disappears during the final document read.
A file change during answer-model work prevents success Evidence.

The tests used a separate source copy and a PostgreSQL 17 container with
tmpfs storage and synthetic credentials. The existing database connection
settings were not used. After the suite, all 20 tables in that disposable
database contained zero rows, with zero running Tasks and Executions. The
temporary container and source copy were removed. No personal data or
existing named volume was changed.

## Remaining validation

A **separate second isolated run** used a new Run ID and the source-explicit M10 question in the manual runbook. Its one Session creation POST returned HTTP 201. One Session-scoped M10 POST returned HTTP 200 with `project.documents.answer.auto`, `outcome=supported`, one source and one exact animal quote. After restarting only the owned NOAH server, one natural M17 follow-up POST in the same Session returned HTTP 200 with `project.documents.answer.followup`, `outcome=supported`, and one exact color quote. Read-only DB proof verified two recorded Session Audits, one Task/Execution for each answer, exact M10 and M17 Evidence lineage, current file SHA-256 and Unicode quote positions, and the expected 20-table delta. The isolated synthetic DB rows were deleted in one exact-ownership transaction; an empty 20-table baseline was confirmed before the copied source files were removed. The owned tmpfs container and dedicated Ollama 11435 were stopped; ordinary Ollama 11434 remained unchanged. No POST was repeated.

The second run's empty temporary source root remained after one failed removal attempt; its cleanup is incomplete and no removal was retried. A subsequent read-only diagnostic invoked the snapshot helper after switching to the source repository. Its Python entry point loaded the source repository's DB settings and called `connect()`; whether authentication succeeded or any SQL query reached the personal DB is unconfirmed because no connection/statement log was available. No private DB write was requested, and no private-DB E2E or Migration 013 application was performed. There is no concrete evidence of private-data mutation or external disclosure, but this run cannot claim zero private-DB access or complete environmental cleanup. The previous attempt's empty-root report remains separate and was not used as a cleanup target here.

The first isolated operator HTTP attempt used a temporary source copy, a separate
PostgreSQL 17 tmpfs container with an empty 20-table baseline and Migration
013, a synthetic user/project/document, and the installed
`gemma4:12b-it-qat` model on the dedicated loopback port 11435. Session
creation was sent once and returned HTTP 201. The first Session-scoped M10
request was sent once and returned HTTP 200 with routing outcome `no_action`.
Its single observed Audit had no delegate Task, Execution, or M17 Evidence.
The expected M10 document answer was not obtained, so the server restart and
M17 follow-up were not attempted. No request was repeated to seek a different
model selection. This is an actual-model selection result, not an M17
provenance or answer validation result.

After the stop, exact synthetic ownership and the six-row delta were checked.
The six synthetic rows were removed in one transaction, and the isolated
20-table empty baseline was restored before the owned tmpfs container was
removed. The owned NOAH 8080 and Ollama 11435 services were stopped; the
existing 11434 listener was unchanged. The synthetic mapping, document and
source-copy files were removed. An empty temporary source directory remained
after its removal attempt; no secret or fixture file remained in it. The
personal development DB and named volume were neither connected to nor
inspected in this run.

Actual M17 route selection, grounded answer, M10-to-M17 lineage, and server restart
were verified in the second isolated HTTP run. Existing automated tests may use
temporary local HTTP fixtures.
The additive migration must be reviewed before any later application
to the development database. A synthetic Session/M10/M17 HTTP run, server
restart, exact provenance readback, and baseline-preserving cleanup in the
existing personal DB remain separate acceptance steps. Concurrent requests are resolved by the stated
DB snapshot, not by a durable Conversation/Turn order.
