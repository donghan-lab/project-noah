# M12 Durable Read-Only Routing Audit — validation record

> Date: 2026-10-01 (Asia/Seoul). Implementation baseline:
> `00de2bd7a96bfd82312919b511f48500712086d9` on `main`.
> Status: local implementation, automated Compose PostgreSQL 17 validation,
> and separate operator-run manual HTTP E2E completed; GitHub commit/push pending.

## Implemented boundary

`POST /requests/route` retains M11's authentication, input, known-credential,
and caller-supplied project membership prechecks. After they pass, one
server-generated `router_id` reserves an operational row in
`noah.routing_audit` before the routing model call. Its independent short
transactions advance `reserved → route_validated → dispatch_prepared →
observed`; definite model failure, `no_action`, and argument rejection have
the direct terminal transitions defined in the [M12 contract](37-Twelfth-Vertical-Slice.md).
`dispatch_prepared` records intention only, not proof of invocation.

The M3 branch calls `query_memory()` once and links its response-scoped
`request_id`, with no Task/Execution. The M10 branch calls
`answer_auto_documents()` once; M10 alone owns its Task/Execution and
candidate/source/quote Evidence. The audit retains M10 correlation IDs only
after matching the returned request, Task, actor, and capability against its
Execution row. `no_action` writes one terminal audit row and no delegate,
Task, Execution, or Capability Evidence. Neither branch uses a nested HTTP
route or a parent Task. M11's final Memory disclosure check still runs before
public content is returned.

`routing.audit_status=recorded` means the terminal audit update committed.
`unconfirmed` means it could not be confirmed, **not** that a delegate failed.
A definite or uncertain reservation/pre-delegate write failure stops without
model/delegate work. A failed `no_action` final update returns the agreed
503 audit error, while an already observed delegate result keeps its original
HTTP status/body if only the audit finalization fails. No retry, fallback,
automatic recovery, or Task status inference was added.

## Database and data protection

The additive `008_routing_audit.sql` creates one constrained operational table
and actor/time index; `noah init` registers it after migrations 001–007. The
table does not persist questions, prompts, raw model output, token or token
hash, DB credential, Memory/document content or quotes, generated answer,
absolute path, or local mapping. It has no new FK to M3 request IDs or M10
Task/Execution/project rows. There is no public audit-browsing API.

Before applying the additive migration, a read-only snapshot covered all 17
existing `noah` tables. Its counts were: user 1, token 1, Memory 2, Task 2,
Execution 3, M4 mapping 1, project and membership 0, and M6–M10 Evidence 0.
SHA-256 fingerprints were computed from sorted row JSON **without printing
private values**. The only SQL in migrations 001–008 creates missing schema,
tables, or indexes; it contains no data deletion or updates. After automated
tests and synthetic cleanup, every original table had the same count and
fingerprint. The new `routing_audit` table had 0 remaining synthetic rows,
and running Task/Execution counts were both 0. The existing `postgres:17`
Compose service was running with one named local volume; no volume or
container reset was performed. The Git-excluded local project mapping was
absent before and after tests; temporary synthetic document roots were
removed by test fixtures.

## Automated results

| Run | Result | Verified behavior |
| --- | --- | --- |
| M12 dedicated Compose test | **13 passed; 0 skipped/failures/errors** | Preflight no-row boundary; distinct router IDs; M3/M10 ID linkage and one delegate call; `no_action` metadata only; model failure classes; argument rejection; definite and uncertain audit writes at reservation, pre-dispatch, and finalization; final Memory denial; swapped M10 ID suppression; sensitive data absent from stored row. |
| Full M1–M12 Compose regression | **146 total: 138 passed, 8 opt-in skipped; 0 failures/errors** | Existing M1–M11 functionality and M12 tests. M11 historical no-Task/Execution assertions remain; fixture cleanup removes only its own new audit rows. |

The fault cases inject definite failure or lost commit acknowledgement at the
audit helper boundary. They test fail-closed dispatch and response semantics,
not an actual network outage. The implementation turn did **not** run a new
actual Ollama opt-in selection test or a user manual HTTP E2E. The separate
operator run below subsequently exercised the dedicated local Ollama and all
three HTTP routes. Prior M11 actual-model/manual results remain historical and
are not relabeled M12 validation.

## Separate operator-run manual HTTP E2E

The operator reported exactly one `POST /requests/route` request for each
Memory, Document, and No Action path, with no API retry. The Memory request
selected `memory.query`, returned a grounded synthetic quote and
`routing.audit_status=recorded`, and correlated its M3 response `request_id`
with the M12 routing audit. Its durable delta was one audit row and zero
Task/Execution/Evidence rows.

The Document request selected `project.documents.answer.auto` and two
synthetic sources. Its observed outcome was **`partial`**, not `supported`.
Read-only DB verification linked the M12 router to exactly one M10
Task/Execution pair and checked source-aware Evidence. The No Action request
produced one routing audit row, with no delegate invocation or
Task/Execution/Evidence addition. All three router IDs were distinct; the
synthetic user had one M10 Task/Execution pair in total. The verifiers used
captured responses and read-only DB checks only.

After NOAH stopped, ownership, path, hash, and volume checks passed. One
cleanup transaction removed only the synthetic M12/M10 rows. Original table
counts and private-row fingerprints matched the pre-run baseline exactly;
the synthetic mapping, two Markdown files, and root were removed. The named
PostgreSQL volume remained. Only the dedicated `127.0.0.1:11435` Ollama
started for the procedure was stopped last; the ordinary `11434` service and
PostgreSQL were not changed. The working-tree state was identical before and
after the manual run. See the [operator procedure and result record](39-Twelfth-Slice-Manual-Validation.md).

## Remaining boundaries

Audit rows have no automatic retention/deletion policy. A missing terminal
observation or old `dispatch_prepared` row cannot establish whether a delegate
ran or succeeded. M5 Recovery Triage remains `memory.save`-only. A client
whose HTTP response was lost may lack the server-generated `router_id`, and
M12 offers no client idempotency identity. Grounded quotes and M10's
`partial` outcome retain their existing provenance meaning; routing audit
does not prove semantic completeness.
