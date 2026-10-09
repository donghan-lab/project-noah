-- M16: a user-owned lifecycle reference, not Task/Execution or Context state.
CREATE TABLE IF NOT EXISTS noah.sessions (
    id uuid PRIMARY KEY,
    owner_user_id uuid NOT NULL REFERENCES noah.users(id) ON DELETE NO ACTION,
    created_at timestamptz NOT NULL DEFAULT now(),
    closed_at timestamptz,
    CHECK (closed_at IS NULL OR closed_at >= created_at)
);

-- Existing audits remain unscoped. Session association is the reservation row.
ALTER TABLE noah.routing_audit
    ADD COLUMN IF NOT EXISTS session_id uuid REFERENCES noah.sessions(id) ON DELETE NO ACTION;

CREATE INDEX IF NOT EXISTS routing_audit_session_created_idx
    ON noah.routing_audit (session_id, created_at DESC, router_id DESC)
    WHERE session_id IS NOT NULL;
