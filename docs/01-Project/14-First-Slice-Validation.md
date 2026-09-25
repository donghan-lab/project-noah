# First Vertical Slice Validation Record

Date: 2026-09-24 (Asia/Seoul)

## Test environment and ownership

The Docker Compose PostgreSQL service was unavailable when the first slice tests were run. A separate PostgreSQL 18 cluster was initialized at `.noah/pg-slice-validation`. The validation command checked that this path did not exist before initialization. The cluster was created solely for this task, using the existing Compose database name, user name and port as local test connection settings. It did not use or modify the Docker Compose container or its named volume. Its server process was stopped after testing. A later port check found `com.docker.backend` listening on the configured port; the temporary cluster has no `postmaster.pid`.

## Executed results

Command: `.venv\Scripts\python -m unittest discover -s tests -v`

Result: **5 tests passed; 0 failures; 0 errors; 0 skips** (1.861 seconds).

| Test | Result | Evidence checked |
| --- | --- | --- |
| `test_save_readback_and_durable_records` | Passed | PostgreSQL memory row, explicit provenance, completed Task, succeeded execution and verification timestamp |
| `test_project_permission_and_server_restart_persistence` | Passed | HTTP save, new server instance readback, unrelated user denied |
| `test_unauthorized_and_invalid_input_record_failures` | Passed | 401, 403 and 400 responses with failed execution records |
| `test_database_write_failure_rolls_back_memory_and_marks_task_failed` | Passed | No memory row after injected write failure; failed Task and execution records |
| `test_unavailable_database_returns_failure_without_leaking_request` | Passed | 503 response and credential-free local fallback failure record |

The test fixture cleanup removed only users, memberships, Tasks, executions and memories created by the tests in the isolated cluster. `git diff --check` passed. `docker compose --env-file compose/.env -f compose/docker-compose.yml config -q` passed, although Docker reported restricted access to the user's Docker client configuration. The Compose PostgreSQL 17 container was **not** used for these integration tests.

## Failure evidence retained from the local audit file

`.noah/failures.jsonl` was created during the intentionally simulated database-unavailable test. At inspection it contained exactly one JSON record:

- Time: 2026-09-24 03:08:12 Asia/Seoul
- Request ID: `8a57ed36-7c15-41fa-befa-abf896a33c29`
- Task ID: absent, because PostgreSQL was deliberately made unavailable before Task creation
- Status: `failed`
- Category: `Environment Failure`
- Code: `DATABASE_UNAVAILABLE`

The record has only `at`, `request_id`, `task_id`, `status`, `category` and `code` fields. It contains no request content, token or database password. This was a planned failure scenario and did not make the test suite fail.

## Temporary artifacts and cleanup decision

| Path | Purpose | Reason it may be removed after review |
| --- | --- | --- |
| `.noah/pg-slice-validation` | PostgreSQL 18 data directory created for isolated testing; contains `PG_VERSION`, `base`, `global`, `pg_wal` and configuration files | It was absent before this task's initialization, is separate from the Compose volume, and its server process has stopped. Test results are recorded above. |
| `.noah/pg-slice-validation.log` | Startup and shutdown log written by the temporary PostgreSQL server | At inspection it contained 11 lines and no `WARNING`, `ERROR`, `FATAL` or `PANIC` lines. The relevant outcome is recorded above. |
| `.noah/failures.jsonl` | Fallback audit file for a deliberately unavailable database | Its single failure event and safe metadata are preserved above. |

All three paths are ignored by Git through `.noah/`. The user approved removal of exactly these three temporary artifacts on 2026-09-25. They were removed after this record was checked. The Docker Compose container, named volume and project data were outside the cleanup scope.

## Docker Compose integration validation — 2026-09-25

Docker Desktop was restored by the user. Before testing, `docker compose ps` showed the existing `noah-postgres` container running from `postgres:17`, container ID `9e490c9235b8`. The named volume `noah_noah-postgres-data` existed with creation time `2026-07-13T08:22:12Z`. The application connected using the unchanged local `compose/.env`; PostgreSQL reported server version `170010`. The `noah` schema was absent before this run.

`python -m noah init` added only the first-slice `noah` schema and tables. It did not recreate the container or volume. The integration command `.venv\Scripts\python -m unittest discover -s tests -v` then completed with **5 passed, 0 failures, 0 errors, 0 skips** in 1.538 seconds. The five tests listed above all passed against the Compose PostgreSQL 17 database. The write-failure test was strengthened for this run: it caused a real foreign-key violation inside PostgreSQL, then verified that the memory insert rolled back while the Task and execution recorded failure.

The HTTP test saved a project memory, stopped its first application server, started a new server instance, read the memory again, and confirmed an unrelated user could not read it. Other tests verified successful personal memory save and independent database readback, unauthenticated and scope-denied writes, invalid content, and the credential-free 503 fallback. After the test fixture cleanup, each of `noah.users`, `noah.api_tokens`, `noah.projects`, `noah.project_memberships`, `noah.tasks`, `noah.memories` and `noah.execution_records` had zero rows. The schema remains available for first-slice use.

After testing, `docker compose ps` still showed the same running container ID. `docker volume inspect` showed the same named volume and creation time. No Compose down, volume removal, prune or reset command was run. Existing non-NOAH database objects were not targeted by the schema or test cleanup.

The deliberate database-unavailable test created a new `.noah/failures.jsonl` with one event on 2026-09-25 13:43:27 Asia/Seoul: request ID `e540121b-a753-40e3-9698-9835d000861e`, no Task ID, status `failed`, category `Environment Failure`, code `DATABASE_UNAVAILABLE`. This synthetic failure did not make the test suite fail. The event has the same six safe metadata fields described above; no content or credentials were recorded. Its evidence is preserved here before removal of the regenerated temporary file.
