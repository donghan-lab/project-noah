# Second Vertical Slice Validation Record

Date: 2026-09-27 (Asia/Seoul)

## Environment and preserved data

The existing `noah-postgres` Docker Compose service was running from
`postgres:17`. The application connected through the unchanged local
`compose/.env`; PostgreSQL reported major version 17. Before testing, the
`noah` schema held one real user, one active API token, one personal memory,
one completed Task and one succeeded execution record. No project existed.

The new tests provisioned their own three users and one project and saved
test-specific memories. Cleanup targeted only those test identities, their
project and their records. After both test runs, the seven `noah` tables had
the same row counts as before: one user, one token, no project or membership,
one Task, one memory and one execution. The real user's personal memory was
still present with the same ID and scope. Its content and credentials are not
included in this record. No container, named volume or existing user data was
removed or initialized.

## Executed tests

| Command | Result | Coverage |
| --- | --- | --- |
| `.venv\Scripts\python.exe -m unittest discover -s tests -p test_memory_read.py -v` | 7 passed, 0 failures, 0 errors, 0 skips | Authorized list, empty list, private memory exclusion, project read-only membership, unauthenticated rejection, stable ordering and cursor pagination, invalid parameters, HTTP route and single-memory policy consistency |
| `.venv\Scripts\python.exe -m unittest discover -s tests -p test_first_slice.py -k FirstSliceIntegrationTests -v` | 4 passed, 0 failures, 0 errors, 0 skips | Existing write, readback, durable Task and execution, authorization and invalid input, real PostgreSQL write rollback, HTTP server instance recreation |

All 11 tests used the existing Docker Compose PostgreSQL 17 database. One
first-slice test deliberately caused a foreign-key violation there to check
rollback and failed execution records. The separate simulated
database-unavailable fallback test was not rerun. Its previous results remain
in the [First Slice Validation Record](14-First-Slice-Validation.md).

The new test suite checked that project membership with `can_write = false`
allows listing and individual reading, while a non-member sees no project
items. Removing that test membership immediately hid the project memories
from both list and individual GET; the test membership was restored afterward.
It also checked that a user's private memory is absent from another user's
list and returns 404 when requested by ID. Six test memories were given the
same timestamp to verify UUID tie breaking across pages. The HTTP test
called the actual `GET /memories` route and checked its 401 response without a
token.

`git diff --check` passed. The test runs did not create a local
`.noah/failures.jsonl` file. A direct command targeting the old test file
initially failed to import `noah` because it was launched as a script;
re-running it through `unittest discover` passed all four selected tests.

## User manual verification

After the automated runs, the user started NOAH locally and called
`GET /memories?scope=user&limit=20` with their own token. They reported that
the personal memory saved in the first slice appeared in the response. A
separate read-only PostgreSQL check confirmed that the same memory ID, its
personal scope, completed Task, passed verification and succeeded execution
were still present. The private memory content and token are omitted here.

The user also observed a `KeyboardInterrupt` traceback after pressing
`Ctrl+C` to stop the local server. This concerns shutdown presentation, not
the memory-read result, and is tracked as a future UX improvement.

## Architecture check and limits

The list reads only the Memory domain and preserves its user/project scope and
the existing authentication principal. It does not write to Knowledge,
Artifact, Identity Core or Task State. Permission enforcement remains in the
service and SQL query, independent of any Agent or model. Structured 400, 401
and 503 failures follow the first-slice response pattern. This is a limited
implementation of the Blueprint and Accepted DDR boundaries, not completion
of all their acceptance criteria.

The cursor is a position, not a cross-request snapshot. If records or project
memberships change while paging, later pages reflect the current database
state. Read requests do not create Task or execution records, matching the
existing individual GET behavior. Full-process restart and remote deployment
were not part of this validation.
