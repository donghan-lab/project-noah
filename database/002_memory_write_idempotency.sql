-- Additive migration. Existing memories, tasks, and execution records remain unchanged.
-- The mapping is durable; canonical outcome remains in tasks/execution_records.
CREATE TABLE IF NOT EXISTS noah.memory_write_requests (
    actor_user_id uuid NOT NULL REFERENCES noah.users(id),
    key_digest char(64) NOT NULL CHECK (length(key_digest) = 64),
    request_fingerprint char(64) NOT NULL CHECK (length(request_fingerprint) = 64),
    execution_id uuid NOT NULL UNIQUE REFERENCES noah.execution_records(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (actor_user_id, key_digest)
);
