-- M6 additive evidence for a single read-only document-list observation.
-- NOAH inserts once per execution; no application update/delete path exists.
CREATE TABLE IF NOT EXISTS noah.document_tool_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.execution_records(id),
    project_id uuid NOT NULL REFERENCES noah.projects(id),
    root_id text NOT NULL CHECK (length(root_id) BETWEEN 1 AND 64),
    observed_at timestamptz NOT NULL,
    filenames jsonb NOT NULL CHECK (jsonb_typeof(filenames) = 'array'),
    result_count integer NOT NULL CHECK (result_count >= 0),
    truncated boolean NOT NULL,
    result_sha256 char(64) NOT NULL CHECK (length(result_sha256) = 64),
    created_at timestamptz NOT NULL DEFAULT now()
);
