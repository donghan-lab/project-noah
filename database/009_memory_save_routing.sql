-- M13: add only the explicit memory.save route to M12's bounded audit values.
-- Existing rows remain valid; no Task, Execution, Evidence, or write-key schema changes.
ALTER TABLE noah.routing_audit
    DROP CONSTRAINT IF EXISTS routing_audit_validated_route_check,
    ADD CONSTRAINT routing_audit_validated_route_check CHECK (validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save', 'no_action')),
    DROP CONSTRAINT IF EXISTS routing_audit_delegate_capability_check,
    ADD CONSTRAINT routing_audit_delegate_capability_check CHECK (delegate_capability IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save')),
    DROP CONSTRAINT IF EXISTS routing_audit_check1,
    ADD CONSTRAINT routing_audit_check1 CHECK (NOT dispatch_prepared OR validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save'));
