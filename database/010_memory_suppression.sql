-- M14: preserve Memory rows while excluding suppressed rows from ordinary retrieval.
ALTER TABLE noah.memories
    ADD COLUMN IF NOT EXISTS suppressed_at timestamptz DEFAULT NULL;
