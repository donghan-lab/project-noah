-- M17: one verified, current single-document observation per successful follow-up.
-- Routing audit remains operational metadata; this row belongs to the M17 Execution.
ALTER TABLE noah.routing_audit
    DROP CONSTRAINT IF EXISTS routing_audit_validated_route_check,
    ADD CONSTRAINT routing_audit_validated_route_check CHECK (validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress', 'project.documents.answer.followup', 'no_action')),
    DROP CONSTRAINT IF EXISTS routing_audit_delegate_capability_check,
    ADD CONSTRAINT routing_audit_delegate_capability_check CHECK (delegate_capability IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress', 'project.documents.answer.followup')),
    DROP CONSTRAINT IF EXISTS routing_audit_check1,
    ADD CONSTRAINT routing_audit_check1 CHECK (NOT dispatch_prepared OR validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress', 'project.documents.answer.followup'));

CREATE TABLE IF NOT EXISTS noah.document_followup_evidence (
    execution_id uuid PRIMARY KEY REFERENCES noah.execution_records(id) ON DELETE NO ACTION,
    current_router_id uuid NOT NULL UNIQUE REFERENCES noah.routing_audit(router_id) ON DELETE NO ACTION,
    prior_router_id uuid NOT NULL REFERENCES noah.routing_audit(router_id) ON DELETE NO ACTION,
    prior_execution_id uuid NOT NULL REFERENCES noah.execution_records(id) ON DELETE NO ACTION,
    project_id uuid NOT NULL REFERENCES noah.projects(id) ON DELETE NO ACTION,
    root_id text NOT NULL CHECK (length(root_id) BETWEEN 1 AND 64),
    document_name text NOT NULL CHECK (length(document_name) BETWEEN 1 AND 255),
    prior_content_sha256 char(64) NOT NULL CHECK (prior_content_sha256 ~ '^[0-9a-f]{64}$'),
    content_sha256 char(64) NOT NULL CHECK (content_sha256 ~ '^[0-9a-f]{64}$'),
    byte_length integer NOT NULL CHECK (byte_length BETWEEN 0 AND 65536),
    content_encoding text NOT NULL CHECK (content_encoding = 'utf-8'),
    bom_present boolean NOT NULL,
    observed_at timestamptz NOT NULL,
    outcome text NOT NULL CHECK (outcome IN
        ('supported', 'partial', 'insufficient', 'conflicting', 'out_of_scope')),
    quotes jsonb NOT NULL CHECK (jsonb_typeof(quotes) = 'array'
        AND jsonb_array_length(quotes) BETWEEN 0 AND 3),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((outcome IN ('supported', 'partial') AND jsonb_array_length(quotes) BETWEEN 1 AND 3)
        OR (outcome = 'conflicting' AND jsonb_array_length(quotes) BETWEEN 2 AND 3)
        OR (outcome IN ('insufficient', 'out_of_scope') AND jsonb_array_length(quotes) = 0))
);
