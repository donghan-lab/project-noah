# Second vertical slice: authorized memory list

The local HTTP API now supports `GET /memories` alongside the first slice's
`POST /memories` and `GET /memories/<id>`. It reads the existing `noah.memories`
table; no schema change or data migration is required.

## Request and response

Send the same bearer token used for the first slice:

```powershell
$page = Invoke-RestMethod -Uri 'http://127.0.0.1:8080/memories?scope=user&limit=20' `
    -Headers @{ Authorization = "Bearer $env:NOAH_API_TOKEN" }
$page.memories
```

`scope` is optional (`user` or `project`); omitting it lists both readable
scopes. `limit` defaults to 20 and accepts 1 through 100. Results are ordered
by `created_at DESC, id DESC`. Each item has the same fields as the existing
single-memory response: `id`, `scope`, `content`, `owner_user_id`, `project_id`
and `created_at`. An empty result returns HTTP 200 with `memories: []` and
`next_cursor: null`.

When `next_cursor` is present, pass it to the next request:

```powershell
$cursor = [uri]::EscapeDataString($page.next_cursor)
$next = Invoke-RestMethod -Uri "http://127.0.0.1:8080/memories?scope=user&limit=20&cursor=$cursor" `
    -Headers @{ Authorization = "Bearer $env:NOAH_API_TOKEN" }
```

The cursor is an opaque page position, not an authorization token. Keep the
same scope and limit while paging. Authorization is checked again on every
request, so a later membership change can alter which rows are visible.

## Access and failure behavior

- Personal memories are visible only to their `owner_user_id`.
- Project memories are visible to project members, including members with
  `can_write = false`. Project write permission is not required for reading.
- The list filters access in PostgreSQL before applying the page limit. It
  never returns another user's private memory to fill a page.
- Missing or invalid tokens return 401. Invalid query parameters or cursors
  return 400 with a structured failure. PostgreSQL unavailability returns 503.
- A single-memory request still returns 404 for an absent or inaccessible ID.
  Its access policy and response fields match the list endpoint.
- Reads do not create a Task or execution record, consistent with the existing
  single-memory GET. The explicit save operation retains its first-slice
  durable Task and execution behavior.

The ordering uses a timestamp and UUID tie breaker. Keyset pagination avoids
duplicates caused by new rows arriving at the front of the list. It does not
freeze a database snapshot across requests; permissions and older rows may
change between pages. Search, relevance ranking, vector retrieval and automatic
context projection remain outside this slice.

Validation details: [Second Slice Validation Record](16-Second-Slice-Validation.md).
