CREATE TABLE event_processing_attempts (
    id         UUID        PRIMARY KEY,
    tenant_id  UUID        NOT NULL REFERENCES tenants(id),
    event_id  UUID         NOT NULL REFERENCES events(id),
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status     TEXT        NOT NULL CHECK (status IN ('started', 'succeeded', 'failed')),
    error_message TEXT,
    duration_ms INT
);

ALTER TABLE event_processing_attempts ENABLE ROW LEVEL SECURITY;
ALTER TABLE event_processing_attempts FORCE ROW LEVEL SECURITY;

CREATE POLICY tenant_isolation ON event_processing_attempts
    USING (tenant_id = current_setting('app.current_tenant')::UUID)
    WITH CHECK (tenant_id = current_setting('app.current_tenant')::UUID);
