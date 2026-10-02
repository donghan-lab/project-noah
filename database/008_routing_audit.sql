-- M12 operational routing correlation; this is not Task/Execution/Evidence.
CREATE TABLE IF NOT EXISTS noah.routing_audit (
    router_id uuid PRIMARY KEY,
    actor_user_id uuid NOT NULL,
    stage text NOT NULL CHECK (stage IN
        ('reserved', 'route_validated', 'dispatch_prepared', 'observed')),
    validated_route text CHECK (validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'no_action')),
    dispatch_prepared boolean NOT NULL DEFAULT false,
    delegate_result_observed boolean NOT NULL DEFAULT false,
    delegate_capability text CHECK (delegate_capability IN
        ('memory.query', 'project.documents.answer.auto')),
    delegate_request_id uuid,
    delegate_task_id uuid,
    delegate_execution_id uuid,
    observation_class text CHECK (observation_class IN
        ('no_action', 'routing_failed', 'argument_rejected', 'delegate_returned',
         'delegate_uncertain', 'disclosure_denied', 'correlation_unverified')),
    http_status smallint CHECK (http_status BETWEEN 100 AND 599),
    outcome_code text CHECK (length(outcome_code) BETWEEN 1 AND 80
        AND outcome_code ~ '^[A-Za-z0-9_.-]+$'),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    observed_at timestamptz,
    CHECK (stage = 'reserved' OR stage = 'observed' OR validated_route IS NOT NULL),
    CHECK (NOT dispatch_prepared OR validated_route IN
        ('memory.query', 'project.documents.answer.auto')),
    CHECK (stage NOT IN ('reserved', 'route_validated') OR NOT dispatch_prepared),
    CHECK (stage <> 'dispatch_prepared' OR dispatch_prepared),
    CHECK (NOT delegate_result_observed OR dispatch_prepared),
    CHECK ((delegate_capability IS NULL AND NOT dispatch_prepared)
        OR (delegate_capability = validated_route AND dispatch_prepared)),
    CHECK (stage <> 'observed' OR
        (observation_class IS NOT NULL AND http_status IS NOT NULL
         AND outcome_code IS NOT NULL AND observed_at IS NOT NULL)),
    CHECK (stage = 'observed' OR
        (observation_class IS NULL AND http_status IS NULL
         AND outcome_code IS NULL AND observed_at IS NULL)),
    CHECK (delegate_execution_id IS NULL OR delegate_task_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS routing_audit_actor_created_idx
    ON noah.routing_audit (actor_user_id, created_at DESC);
