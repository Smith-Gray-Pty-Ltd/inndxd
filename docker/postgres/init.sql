CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

ALTER TABLE IF EXISTS projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS briefs ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_items ENABLE ROW LEVEL SECURITY;

CREATE POLICY IF NOT EXISTS tenant_isolation_projects ON projects
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY IF NOT EXISTS tenant_isolation_briefs ON briefs
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));

CREATE POLICY IF NOT EXISTS tenant_isolation_data_items ON data_items
    USING (tenant_id::text = current_setting('app.current_tenant_id', true));