-- M8: one bounded answer evidence record per verified document observation.
-- Both rows share one M8 execution_id and commit with its terminal states.
CREATE TABLE IF NOT EXISTS noah.document_answer_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.document_read_evidence(execution_id),
    outcome text NOT NULL CHECK (outcome IN
        ('supported', 'partial', 'insufficient', 'conflicting', 'out_of_scope')),
    quotes jsonb NOT NULL CHECK (jsonb_typeof(quotes) = 'array'
        AND jsonb_array_length(quotes) <= 3),
    created_at timestamptz NOT NULL DEFAULT now()
);
