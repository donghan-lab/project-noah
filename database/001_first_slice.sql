CREATE SCHEMA IF NOT EXISTS noah;

CREATE TABLE IF NOT EXISTS noah.users (
    id uuid PRIMARY KEY,
    label text NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noah.api_tokens (
    token_hash text PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES noah.users(id),
    revoked_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noah.projects (
    id uuid PRIMARY KEY,
    label text NOT NULL CHECK (length(label) BETWEEN 1 AND 100),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noah.project_memberships (
    project_id uuid NOT NULL REFERENCES noah.projects(id),
    user_id uuid NOT NULL REFERENCES noah.users(id),
    can_write boolean NOT NULL DEFAULT false,
    PRIMARY KEY (project_id, user_id)
);

CREATE TABLE IF NOT EXISTS noah.tasks (
    id uuid PRIMARY KEY,
    actor_user_id uuid NOT NULL REFERENCES noah.users(id),
    goal text NOT NULL,
    status text NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    verification_status text NOT NULL CHECK (verification_status IN ('pending', 'passed', 'failed')),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS noah.memories (
    id uuid PRIMARY KEY,
    owner_user_id uuid REFERENCES noah.users(id),
    project_id uuid REFERENCES noah.projects(id),
    scope text NOT NULL CHECK (scope IN ('user', 'project')),
    content text NOT NULL CHECK (length(content) BETWEEN 1 AND 10000),
    provenance text NOT NULL DEFAULT 'explicit_user_request',
    created_by uuid NOT NULL REFERENCES noah.users(id),
    created_at timestamptz NOT NULL DEFAULT now(),
    CHECK ((scope = 'user' AND owner_user_id IS NOT NULL AND project_id IS NULL)
        OR (scope = 'project' AND project_id IS NOT NULL AND owner_user_id IS NULL))
);

CREATE TABLE IF NOT EXISTS noah.execution_records (
    id uuid PRIMARY KEY,
    request_id uuid NOT NULL,
    task_id uuid REFERENCES noah.tasks(id),
    actor_user_id uuid REFERENCES noah.users(id),
    capability text NOT NULL DEFAULT 'memory.save',
    status text NOT NULL CHECK (status IN ('running', 'succeeded', 'failed')),
    failure_category text,
    failure_code text,
    memory_id uuid REFERENCES noah.memories(id),
    verified_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS memories_user_scope_idx ON noah.memories (owner_user_id, created_at);
CREATE INDEX IF NOT EXISTS memories_project_scope_idx ON noah.memories (project_id, created_at);
CREATE INDEX IF NOT EXISTS execution_records_task_idx ON noah.execution_records (task_id);
