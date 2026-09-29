-- M10 evidence is append-only and finalizes with its one Task/Execution.
-- Candidate and source observations occur at different times, not one snapshot.
CREATE TABLE IF NOT EXISTS noah.auto_document_answer_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.execution_records(id),
    project_id uuid NOT NULL REFERENCES noah.projects(id),
    root_id text NOT NULL CHECK (length(root_id) BETWEEN 1 AND 64),
    candidates_observed_at timestamptz NOT NULL,
    candidate_names jsonb NOT NULL CHECK (jsonb_typeof(candidate_names) = 'array'
        AND jsonb_array_length(candidate_names) BETWEEN 0 AND 20),
    candidate_count smallint NOT NULL CHECK (candidate_count BETWEEN 0 AND 20
        AND candidate_count = jsonb_array_length(candidate_names)),
    truncated boolean NOT NULL CHECK (truncated = false),
    candidate_sha256 char(64) NOT NULL CHECK (length(candidate_sha256) = 64),
    selection_model_called boolean NOT NULL,
    selection_outcome text NOT NULL CHECK (selection_outcome IN ('selected', 'none')),
    raw_candidate_names jsonb NOT NULL CHECK (jsonb_typeof(raw_candidate_names) = 'array'),
    selected_names jsonb NOT NULL CHECK (jsonb_typeof(selected_names) = 'array'),
    selected_count smallint NOT NULL CHECK (selected_count BETWEEN 0 AND 2
        AND selected_count = jsonb_array_length(selected_names)),
    answer_outcome text CHECK (answer_outcome IN
        ('supported', 'partial', 'insufficient', 'conflicting', 'out_of_scope')),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((selection_outcome = 'none' AND selected_count = 0 AND answer_outcome IS NULL)
        OR (selection_outcome = 'selected' AND selected_count BETWEEN 1 AND 2
            AND answer_outcome IS NOT NULL)),
    CHECK (selection_model_called OR (candidate_count = 0 AND selection_outcome = 'none'
        AND jsonb_array_length(raw_candidate_names) = 0)),
    CHECK (jsonb_array_length(raw_candidate_names) = selected_count)
);

CREATE TABLE IF NOT EXISTS noah.auto_document_source_evidence (
    execution_id uuid NOT NULL REFERENCES noah.auto_document_answer_evidence(execution_id),
    source_id text NOT NULL CHECK (source_id IN ('D1', 'D2')),
    source_ordinal smallint NOT NULL CHECK (source_ordinal IN (1, 2)),
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

CREATE TABLE IF NOT EXISTS noah.auto_document_quote_evidence (
    execution_id uuid NOT NULL,
    quote_ordinal smallint NOT NULL CHECK (quote_ordinal BETWEEN 1 AND 3),
    source_id text NOT NULL,
    quote text NOT NULL CHECK (length(quote) BETWEEN 1 AND 240),
    start_index integer NOT NULL CHECK (start_index >= 0),
    end_index integer NOT NULL CHECK (end_index > start_index),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (execution_id, quote_ordinal),
    FOREIGN KEY (execution_id, source_id)
        REFERENCES noah.auto_document_source_evidence(execution_id, source_id),
    UNIQUE (execution_id, source_id, quote)
);
