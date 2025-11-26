CREATE SCHEMA IF NOT EXISTS houston_311 AUTHORIZATION postgres;

CREATE TABLE houston_311.incidents (
    case_365_number TEXT,
    case_number TEXT,
    incident_address TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    status TEXT,
    created_date_local TEXT,
    closed_date TEXT,
    title TEXT,
    incident_case_type TEXT,
    sla_time TEXT,
    resolve_by_time TEXT,
    service_area TEXT,
    council_district TEXT,
    key_map TEXT,
    department TEXT,
    division TEXT,
    ava_case_type TEXT,
    state_code TEXT,
    state_code_name TEXT,
    sla_start_time TEXT,
    x DOUBLE PRECISION,
    y DOUBLE PRECISION,
    incident_street TEXT,
    incident_city TEXT,
    incident_state TEXT,
    zip_code TEXT,
    taxid TEXT,
    created_date_utc TEXT,
    customer_super_neighborhood TEXT,
    management_district TEXT,
    garbage_route TEXT,
    garbage_day TEXT,
    swm_quadrant TEXT,
    recycling_route TEXT,
    recycling_day TEXT,
    recycling_quadrant TEXT,
    recycling_areas TEXT,
    heavy_trash_day TEXT,
    heavy_trash_quadrant TEXT,
    queue TEXT,
    etj TEXT,
    sla_name TEXT,
    channel TEXT,
    extract_date TEXT,
    latest_case_notes TEXT,
    sample_case_conflicts_notes TEXT,
    description TEXT,
    resolution_notes TEXT,
    PRIMARY KEY (case_number)
);

-- Create read-only user for application queries
-- This user can only SELECT from the incidents table, preventing any destructive operations
-- IMPORTANT: Change this password before deploying to production!
-- Use a strong password (20+ characters) and update .env file to match
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readonly_311') THEN
        -- TODO: Change this password! This is for development only.
        -- Production: Generate with: openssl rand -base64 32
        CREATE USER readonly_311 WITH PASSWORD 'dev_readonly_password_CHANGE_IN_PRODUCTION';
    END IF;
END
$$;

-- Grant minimal permissions needed for the application
GRANT CONNECT ON DATABASE houston_311_db TO readonly_311;
GRANT USAGE ON SCHEMA houston_311 TO readonly_311;
GRANT SELECT ON houston_311.incidents TO readonly_311;

-- Revoke any other permissions to ensure read-only access
REVOKE CREATE ON SCHEMA houston_311 FROM readonly_311;
REVOKE ALL ON SCHEMA public FROM readonly_311;