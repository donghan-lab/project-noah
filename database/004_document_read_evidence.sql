-- M7: one immutable observation per restricted project document read.
-- The application inserts once; it has no evidence update/delete route.
CREATE TABLE IF NOT EXISTS noah.document_read_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.execution_records(id),
    project_id uuid NOT NULL REFERENCES noah.projects(id),
    root_id text NOT NULL CHECK (length(root_id) BETWEEN 1 AND 64),
    document_name text NOT NULL CHECK (length(document_name) BETWEEN 1 AND 255),
    observed_at timestamptz NOT NULL,
    byte_length integer NOT NULL CHECK (byte_length BETWEEN 0 AND 65536),
    content_sha256 char(64) NOT NULL CHECK (length(content_sha256) = 64),
    content_encoding text NOT NULL CHECK (content_encoding = 'utf-8'),
    bom_present boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
