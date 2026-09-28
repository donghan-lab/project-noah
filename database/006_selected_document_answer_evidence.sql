-- M9: one answer execution with exactly two application-validated observations.
-- Inserts are append-only and commit with Task/Execution terminal success.
-- M7/M8 single-document evidence tables retain their existing meanings.
CREATE TABLE IF NOT EXISTS noah.selected_document_answer_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.execution_records(id),
    project_id uuid NOT NULL REFERENCES noah.projects(id),
    outcome text NOT NULL CHECK (outcome IN
        ('supported', 'partial', 'insufficient', 'conflicting', 'out_of_scope')),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noah.selected_document_source_evidence (
    execution_id uuid NOT NULL REFERENCES noah.selected_document_answer_evidence(execution_id),
    source_id text NOT NULL CHECK (source_id IN ('D1', 'D2')),
    source_ordinal smallint NOT NULL CHECK (source_ordinal IN (1, 2)),
    root_id text NOT NULL CHECK (length(root_id) BETWEEN 1 AND 64),
    document_name text NOT NULL CHECK (length(document_name) BETWEEN 1 AND 255),
    observed_at timestamptz NOT NULL,
    byte_length integer NOT NULL CHECK (byte_length BETWEEN 0 AND 65536),
    content_sha256 char(64) NOT NULL CHECK (length(content_sha256) = 64),
    content_encoding text NOT NULL CHECK (content_encoding = 'utf-8'),
    bom_present boolean NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id, source_id),
    UNIQUE (execution_id, source_ordinal),
    UNIQUE (execution_id, document_name),
    CHECK ((source_id = 'D1' AND source_ordinal = 1)
        OR (source_id = 'D2' AND source_ordinal = 2))
);

CREATE TABLE IF NOT EXISTS noah.selected_document_quote_evidence (
    execution_id uuid NOT NULL,
    quote_ordinal smallint NOT NULL CHECK (quote_ordinal BETWEEN 1 AND 3),
    source_id text NOT NULL,
    quote text NOT NULL CHECK (length(quote) BETWEEN 1 AND 240),
    start_index integer NOT NULL CHECK (start_index >= 0),
    end_index integer NOT NULL CHECK (end_index > start_index),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id, quote_ordinal),
    FOREIGN KEY (execution_id, source_id)
        REFERENCES noah.selected_document_source_evidence(execution_id, source_id),
    UNIQUE (execution_id, source_id, quote)
);
