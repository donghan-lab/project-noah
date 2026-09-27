# Third Vertical Slice Validation Record

Date: 2026-09-27 (Asia/Seoul)

## Security preparation and model selection

The existing machine/process `OLLAMA_HOST` setting was `0.0.0.0`; the
pre-existing Ollama 0.34.4 service listened on `0.0.0.0:11434`. Windows
firewall profile/rule inspection returned access denied, including when
retried outside the filesystem sandbox, so its allow rules were **not**
verified. Nearby projects `jarvis` and `noah` reference the local 11434
service. The `이브` project documents an Ollama connection to another PC,
including remote-host and firewall configuration. Whether any remote client
currently uses this machine's service could not be established. No global
environment variable, firewall rule, or existing Ollama service was changed.

For NOAH, a second Ollama service was started at `127.0.0.1:11435`. Windows
`netstat` showed only a loopback `LISTENING` address on that port while the
original 11434 listener remained unchanged. NOAH checks this condition before
each model call. Inference uses `num_gpu=0`; the dedicated service reported
zero model VRAM use, while the existing GPU model remained loaded. This
provides local-only access for NOAH without interrupting the other service.
The existing network-facing 11434 listener remains a separate security
review item if its remote access is no longer needed.

All six registered models were compared with **synthetic** Korean personal
read, English project read, and English delete requests. The first Korean
trial was discarded because the benchmark shell corrupted its input encoding;
the table uses the corrected Unicode trial. The schema was a strict JSON
object with `intent`, `scope`, and `query`; runs used `think=false`,
`temperature=0`, `num_ctx=2048`, `num_predict=96`, and CPU-only inference.

| Model | Valid JSON schema | Correct intent/scope | Korean / English / delete seconds |
| --- | ---: | ---: | --- |
| `llama3.2:latest` | 3/3 | 2/3 | 2.19 / 1.55 / 1.30 |
| `gemma3:4b` | 3/3 | 1/3 | 2.31 / 1.89 / 1.70 |
| `qwen2.5:14b` | 3/3 | 2/3 | 16.39 / 4.84 / 3.58 |
| `gemma4:12b-it-qat` | 3/3 | 3/3 | 7.50 / 6.61 / 4.30 |
| `gemma4:26b-a4b-it-qat` | 3/3 | 3/3 | 34.70 / 3.47 / 2.97 |
| `qwen2.5:32b` | 3/3 | 3/3 | 36.81 / 9.84 / 7.64 |

There were 0 API/schema failures in the 18 valid trials and 4 semantic
misclassifications. Three trials per model are a small functional comparison,
not a statistical failure-rate estimate. Times include mixed cold/warm loads
and do not predict every future request. `gemma4:12b-it-qat` was selected for
its 3/3 result and smaller CPU/RAM footprint than the two other 3/3 models.
It is the validated baseline for this slice, not NOAH's permanent final model.
The production prompts and token/context limits differ slightly from this
selection benchmark. A controlled GPU-use and model-performance comparison
remains separate follow-up work.

The chosen model also processed three synthetic evidence-selection prompts:
Korean, English, and a memory containing an instruction-injection sentence.
All three outputs had IDs and exact quotes matching their supplied synthetic
memories; the injection sentence was not selected as an instruction or
answer. Observed response times were 30.09, 12.84, and 12.25 seconds. The
application independently checks quote and ID membership; these three
examples do not prove that a model will always ignore malicious text.
**No actual personal memory was sent to any model during this validation.**

## Docker Compose PostgreSQL 17 integration

The existing `noah-postgres` container ran PostgreSQL 17.10. The database
schema was unchanged. Before testing, the seven `noah` tables had one user,
one active token, no projects or memberships, one Task, one personal memory,
and one execution record. Tests created only three dedicated synthetic users,
a synthetic project, and synthetic memories. Their cleanup targeted those
identities and records.

| Executed command | Result | Coverage |
| --- | --- | --- |
| `$env:NOAH_RUN_OLLAMA_TESTS='1'; .venv\Scripts\python.exe -m unittest discover -s tests -v` | 24 passed, 0 failures, 0 errors, 0 skips | First Slice Write/rollback, Second Slice Read/pagination, Third Slice authentication, authorization, evidence and model failures; actual Compose PostgreSQL 17 |
| `$env:NOAH_RUN_OLLAMA_TESTS='1'; .venv\Scripts\python.exe -m unittest discover -s tests -p test_memory_query.py -v` after strengthening the real-model HTTP case | 12 passed, 0 failures, 0 errors, 0 skips | `POST /memories/query` through the HTTP server with real loopback Ollama and synthetic English/Korean PostgreSQL memories; listener guard, private/project access, truncation, invalid evidence, failure codes |
| Same full discovery command, rerun on 2026-09-28 before final review | 24 passed, 0 failures, 0 errors, 0 skips (97.363 seconds) | Current M3 code plus M1/M2 regressions on Compose PostgreSQL 17 and dedicated local Ollama |

The new tests confirmed that an unauthenticated request calls no model;
another user's private memory never enters model input; a project member with
`can_write=false` can read the project note; an outsider cannot; forged IDs
and changed quotes fail verification; a five-result limit reports truncation;
and database failure, unavailable model, timeout, unsafe listener, and bad
model output remain distinct. Existing Write/Read tests passed, including a
real PostgreSQL write rollback. The true Ollama HTTP test used only synthetic
English and Korean personal memories and received grounded quotations with
the correct memory IDs.

After testing, the seven table counts returned to exactly the same values as
before. The single original personal memory remained, and there were zero
remaining Third Slice synthetic users. The Compose container ID remained
`9e490c9235b843149dda9620e6cf9b0178a4c06aa0a1eea756b2e58988c85218`
and the named volume remained `noah_noah-postgres-data`. Neither was stopped,
deleted, or initialized. `compose/.env` and the local failure log under
`.noah/` are ignored by Git; their contents are not included here.

## User manual verification (2026-09-28)

The user independently confirmed that the dedicated Ollama listener was
loopback-only, the selected model was registered, and the new API rejected an
unauthenticated request. They then asked a natural-language question about an
existing personal memory using their own token. They reported
`status=succeeded`, `outcome=grounded`, `scope=all`, `examined=1`, and
`truncated=false`, with a matching `memory_id` and verbatim quote in
`evidence`. The model's `all` scope did not bypass NOAH's user/project read
filter. The private memory text, its ID, and credentials are omitted here.

A separate read-only database check on 2026-09-28 found the original one
user, one token, one Task, one memory, and one execution record, with no
project or remaining synthetic test user. The user-reported HTTP response was
not independently replayed with their private token.

## Architecture and limits

The model suggests a constrained read intention and selects evidence; NOAH
authenticates, queries PostgreSQL with parameters and existing scope policy,
and validates evidence. This follows the Agent/Harness separation of DDR-002,
the Memory/Knowledge separation of DDR-003, Identity's independence from the
model in DDR-005, and the scope, evidence, failure, and context-projection
parts of DDR-006. It does not use Memory as Task State (DDR-001) or implement
an Artifact store (DDR-004). The Blueprint documents remain the architecture
baseline; this slice implements only a small part of their contracts.
The existing `docs/02-Architecture/Runtime/State.md` Blueprint file is empty;
DDR-001 remains the explicit accepted Task State/Runtime boundary used here.

Lexical AND search can miss synonyms, inflections, or memories outside the
five-result answer window. The quote check proves textual provenance from an
authorized result, not the real-world truth of the quoted statement or its
semantic relevance. The response therefore labels it as content recorded in
a memory. NOAH returns an explicit limited-window flag when more matching
rows exist. The query route creates no durable Task/execution row, consistent
with the existing read routes. Local Ollama startup remains a separate manual
step, and CPU-only inference may take tens of seconds. Remote deployment,
vector retrieval, Knowledge queries, and free-form answer synthesis remain
outside this slice.
