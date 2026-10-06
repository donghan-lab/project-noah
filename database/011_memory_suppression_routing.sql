-- M15: admit only the explicit memory.suppress route to the existing bounded audit.
-- No target column, Task/Execution ownership, or existing row meaning changes.
ALTER TABLE noah.routing_audit
    DROP CONSTRAINT IF EXISTS routing_audit_validated_route_check,
    ADD CONSTRAINT routing_audit_validated_route_check CHECK (validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress', 'no_action')),
    DROP CONSTRAINT IF EXISTS routing_audit_delegate_capability_check,
    ADD CONSTRAINT routing_audit_delegate_capability_check CHECK (delegate_capability IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress')),
    DROP CONSTRAINT IF EXISTS routing_audit_check1,
    ADD CONSTRAINT routing_audit_check1 CHECK (NOT dispatch_prepared OR validated_route IN
        ('memory.query', 'project.documents.answer.auto', 'memory.save',
         'memory.suppress'));
