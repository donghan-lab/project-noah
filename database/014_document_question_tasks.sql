-- M18: independent intake and one explicit claim. Existing rows are unchanged.
ALTER TABLE noah.tasks
    DROP CONSTRAINT IF EXISTS tasks_status_check,
    ADD CONSTRAINT tasks_status_check
        CHECK (status IN ('ready', 'running', 'completed', 'failed'));

CREATE TABLE IF NOT EXISTS noah.document_question_tasks (
    task_id uuid PRIMARY KEY REFERENCES noah.tasks(id) ON DELETE NO ACTION,
    registration_request_id uuid NOT NULL UNIQUE,
    project_id uuid NOT NULL REFERENCES noah.projects(id) ON DELETE NO ACTION,
    document_name text NOT NULL CHECK (length(document_name) BETWEEN 1 AND 255),
    question text NOT NULL CHECK (length(question) BETWEEN 1 AND 300
        AND octet_length(question) <= 512),
    execution_id uuid UNIQUE REFERENCES noah.execution_records(id) ON DELETE NO ACTION
);

CREATE INDEX IF NOT EXISTS tasks_actor_created_id_idx
    ON noah.tasks (actor_user_id, created_at DESC, id DESC);
