CREATE TABLE events (
    id         UUID        PRIMARY KEY,
    tenant_id  UUID        NOT NULL REFERENCES tenants(id),
    provider   TEXT        NOT NULL,
    event_type TEXT        NOT NULL,
    idempotency_key   TEXT NOT NULL,
    body_hash  TEXT        NOT NULL,
    raw_body   BYTEA       NOT NULL,
    payload    JSONB       NOT NULL,
    received_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    current_status TEXT NOT NULL DEFAULT 'received' CHECK (current_status IN ('received', 'processing', 'processed', 'failed')),
    last_attempted_at TIMESTAMPTZ,
    attempt_count INT      NOT NULL DEFAULT 0,
    UNIQUE (tenant_id, provider, idempotency_key)
);

CREATE INDEX events_tenant_status_received_idx ON events (tenant_id, current_status, received_at);

ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE events FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON events
    USING (tenant_id = current_setting('app.current_tenant')::UUID)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::UUID);

