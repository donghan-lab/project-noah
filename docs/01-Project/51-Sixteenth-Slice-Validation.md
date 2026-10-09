# M16 Minimal Durable Session / Interaction Continuity — validation

> Date: 2026-10-09 (Asia/Seoul). Contract baseline: `main@b8ef7bd5333cd2641e65a687be3b9163f5ab1a93`.
> Status: implementation, deterministic automated validation, operator manual HTTP E2E, and synthetic cleanup are complete. Independent closeout review passed with Critical 0 and Major 0. Confirm the implementation commit and GitHub `main` status from Git history. The approved [M16 contract](49-Sixteenth-Vertical-Slice.md) remains the frozen requirement, not a record of completed work.

## Implemented and verified boundary

The M16 implementation changes seven files: [`012_session_continuity.sql`](../../database/012_session_continuity.sql), [`noah/session.py`](../../noah/session.py), [`noah/__main__.py`](../../noah/__main__.py), [`noah/capability_route.py`](../../noah/capability_route.py), [`noah/routing_audit.py`](../../noah/routing_audit.py), [`noah/db.py`](../../noah/db.py), and [`tests/test_session_continuity.py`](../../tests/test_session_continuity.py). The separate [operator runbook and result](50-Sixteenth-Slice-Manual-Validation.md) was the eighth M16 file at the manual-run checkpoint; this closeout also adds this validation record and updates `NOAH_DEV_STATUS.md`, for ten changed files. The checkpoint difference was a Minor documentation timing matter, not an implementation discrepancy.

Migration 012 adds `noah.sessions` with server UUID, owner, creation time, and nullable close time; it also adds nullable `routing_audit.session_id` and a bounded-inspection index. Catalog inspection in the actual PostgreSQL 17 database confirmed `sessions.owner_user_id → users.id` and `routing_audit.session_id → sessions.id`, both with `ON DELETE NO ACTION`, the expected columns, and the index. The migration preserves older unscoped audit rows and existing data. Cleanup removes synthetic rows, not migration 012 or the named volume.

Authenticated owner create, bounded read, and close use the Session's own active/closed lifecycle without creating Task, Execution, Capability Evidence, or Routing Audit rows. Foreign and absent Session IDs share a non-enumerating denial. An optional `Noah-Session-Id` header associates an existing routed request; it is not a capability permission or model input. A scoped route revalidates the original token and Session owner, locks the Session, and reserves the M12 audit row with its Session FK in one short transaction. A closed Session stops a new association before model or delegate work. M12 audit stage/result meanings and delegated capability ownership remain unchanged.

## Deterministic automated validation previously run

These are results reported from the completed implementation validation; **no automated test was rerun for this documentation closeout**.

| Run | Reported result | Contract coverage |
| --- | --- | --- |
| M16 focused | **17/17 passed; 0 failed** | Authentication, request/header shape, owner/non-enumerating access, lifecycle and repeated close, bounded keyset inspection and cursor isolation, two scoped routes, old unscoped route behavior, model-input separation, no duplicate Task/Execution, and fresh-process readback. |
| M11–M15 related | **72 passed, 4 opt-in skipped, 0 failed** | Existing routing/audit/write/suppression branches and their correlation boundaries. |
| Full M1–M16 | **197 total: 187 passed, 10 opt-in skipped, 0 failed** | M16 plus M1–M15 regression. |

Focused deterministic cases also exercise both close-versus-reservation orderings, token revocation and owner change before reservation, definite and commit-acknowledgement-uncertain Session create/close, and uncertain audit reservation. They check that the model/delegate is not run after a denied or unconfirmed reservation and that an earlier association survives a later close. These fault/race checks are automated evidence; they were **not** injected into the operator HTTP run. An uncertain transition remains unknown rather than a confirmed failure or an automatic retry.

## Operator manual HTTP E2E actually run

On 2026-10-09, the operator completed Sections 1–12 of the [manual runbook](50-Sixteenth-Slice-Manual-Validation.md) using a **new** synthetic user and token, Compose PostgreSQL 17, the working-tree NOAH server, and the configured local model on a dedicated loopback-only Ollama `11435`. Before fixture creation, the run verified migration 012, its two FK relationships and index, all 19 table counts/private row fingerprints, zero synthetic Session/Audit rows, zero running Task/Execution, and named-volume identity. PowerShell 5.1 verified that English and Korean questions became strict UTF-8 JSON in a single `System.Byte[]` before the routed POSTs.

The successful run sent exactly **five POSTs**, each once: Session create returned 201; two Session-scoped routes returned 200 with `no_action` and `routing.audit_status=recorded`; Session close returned 200; and a new association with the closed Session returned 409 `SESSION_CLOSED`. The two router IDs were distinct and linked to the same owned Session. The scoped `no_action` requests added exactly two routing audit rows and no delegate, Task, Execution, or Capability Evidence. The closed-Session probe added no audit or execution record.

NOAH was stopped and restarted between the routed requests and inspection. The same active Session and both router references were returned in two bounded `limit=1` GET pages without a DB delta. Close persisted `closed_at` and left the prior audit rows unchanged. The actual model selected `no_action` for these two synthetic questions; this is an observed selection, not a general model-quality guarantee.

The earlier stopped attempts are separate from this passed run. The first stopped before mutation on a false-negative, schema-qualified FK definition string check. The second stopped after one Session-create 201 and one routed 400 `INVALID_REQUEST` caused by PowerShell 5.1 `byte[]` pipeline enumeration; separately authorized partial cleanup restored its baseline. The corrected catalog check and byte-array return were used for the fresh successful run. No POST was resent to turn either stopped attempt into a success.

## Synthetic cleanup and existing-data preservation

After stopping NOAH, read-only ownership checks identified only this run's two routing audits, one closed Session, one token, and one user. Section 11 deleted exactly those five synthetic rows in one transaction. The post-cleanup snapshot matched the new pre-fixture baseline across **all 19 tables**, including original row counts and private fingerprints; running Task/Execution remained zero. Existing users, tokens, Memories, Task/Execution, M4 mapping, and their private contents were preserved. Migration 012 and the PostgreSQL named volume remained. Mapping state and Git working-tree paths stayed unchanged. NOAH 8080 and only the dedicated Ollama 11435 started by this run were stopped; ordinary Ollama 11434 was unchanged.

## Limits and closeout state

The live run did not inject close/reservation concurrency, token revocation, definite or uncertain DB commit failure, audit acknowledgement loss, or a lost HTTP response. Those boundaries have deterministic automated coverage as described above. Bounded inspection is keyset pagination, not a cross-request database snapshot. Session metadata does not become model Context or a source of delegated Task/Execution truth. M16 does not add Session deletion, automatic retry, or recovery.

**Validation verdict:** the implemented M16 lifecycle, durable routed association, process-restart continuity, close denial, and exact synthetic cleanup passed the reported automated and operator checks. Final independent closeout review found Critical 0 and Major 0. Git inclusion and GitHub `main` synchronization are determined by the actual commit and remote Git history.
