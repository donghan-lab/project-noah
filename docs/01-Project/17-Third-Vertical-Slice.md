# Third vertical slice: read-only local LLM Memory Query

This slice adds `POST /memories/query` to the existing local HTTP API. It
interprets a natural-language question and returns only quotations verified
against memories that the authenticated user may read. It does not change the
database schema, saved memories, Task State, or the existing Write/Read routes.

## Local Ollama setup on Windows

The machine's existing Ollama service listens on port 11434 for network
connections and may be used by other projects. Leave it running. Start a
**separate** Ollama server in a new PowerShell window with a process-only
loopback setting:

```powershell
$env:OLLAMA_HOST = '127.0.0.1:11435'
& "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe" serve
```

The model `gemma4:12b-it-qat` must already be installed. NOAH uses the fixed
address `127.0.0.1:11435` and checks the Windows TCP listeners before every
model request. If that port is absent or bound to a network-facing address,
NOAH fails closed without sending the question or a memory excerpt. Model
requests use CPU only (`num_gpu=0`) to avoid displacing the existing GPU model;
response times will depend on available CPU and RAM. The separate Ollama
window must remain open while this feature is in use.

`gemma4:12b-it-qat` is the model validated for this slice, not NOAH's final
model choice. The current model name and CPU option are defined in
`noah/ollama.py` (`MODEL` and `num_gpu`). Changing either requires a code
review and a new synthetic/Compose validation run. A broader CPU/GPU and
model-quality comparison remains follow-up work.

In another PowerShell window, start the existing NOAH server:

```powershell
.venv\Scripts\python -m noah serve
```

To check the dedicated listener, `netstat -ano -p tcp | Select-String ':11435'`
should show `127.0.0.1:11435` in `LISTENING` state and no `0.0.0.0:11435`
or `[::]:11435` listener. The existing port 11434 is not changed.

## Request and response

Use the existing bearer token. The request accepts exactly one `question`
string of 1 to 500 characters:

```powershell
$body = @{ question = '내 개인 메모에서 오리온 정원 급수 계획을 찾아줘' } | ConvertTo-Json
Invoke-RestMethod -Uri 'http://127.0.0.1:8080/memories/query' -Method Post `
    -Headers @{ Authorization = "Bearer $env:NOAH_API_TOKEN" } `
    -ContentType 'application/json' -Body $body
```

`POST` carries the question in the body; this route performs no Memory, Task,
or execution-record write. Successful responses include `outcome`, `answer`,
`evidence` (verified `memory_id` and verbatim quote pairs), `scope`,
`search_terms`, `examined`, and `truncated`. `outcome` is `grounded`,
`no_match`, or `insufficient_evidence`. When `truncated` is true, more matching
memories may exist outside the five-memory window.

Failures use the existing structured `failure` object. Invalid or unsupported
requests return 400 or 422; missing/invalid authentication returns 401;
PostgreSQL and local Ollama unavailability return 503; model timeout returns
504; malformed model output or unverifiable evidence returns 502. An unsafe
Ollama listener returns 503 with `OLLAMA_NOT_LOCAL`.

## Data and trust flow

1. NOAH authenticates the bearer token against the existing PostgreSQL token
   hash before any model call. The token and database password never enter
   model messages.
2. Ollama proposes only `memory_read` or `unsupported`, a scope, and search
   words in a strict JSON object. NOAH validates the schema and requires the
   words to come from the user's question.
3. NOAH reauthenticates and performs a parameterized, literal word search in
   `noah.memories`. It shares the existing Memory Read visibility predicate:
   personal ownership or project membership. All words must occur in a
   memory, case-insensitively. Results are ordered by `created_at DESC, id
   DESC`, with five returned rows and one extra row to detect truncation.
4. At most 400 characters around a matched word from each authorized result
   are projected to Ollama as untrusted data. Ollama can select at most three
   verbatim quotes with memory IDs. NOAH rejects any ID or quote that does not
   match the projected results. NOAH assembles the final answer from those
   quotes, without accepting a free-form factual claim from the model.

The model receives no SQL tool, API token, database credential, or write
capability. Instructions embedded in a memory body are treated as data. Empty
lexical results and relevant results without a supported quotation have
different outcomes. This first search does not use vectors, synonyms,
cross-request pagination, or a full Knowledge/Context system. Reads continue
to create no Task or execution record, matching `GET /memories`; failures
remain structured and database failures use the existing local fallback log.

Validation details: [Third Slice Validation Record](18-Third-Slice-Validation.md).
