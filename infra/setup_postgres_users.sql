-- Create production PostgreSQL users and configure permissions
-- Run this as the default postgres superuser

-- Create superuser account for database administration
CREATE USER dmi_postgres_admin WITH SUPERUSER PASSWORD 'LABE+N11{zu+?WC[8wH2CGMYs$K6yA38Zd1+$RRo';

-- Create application user for EUDR pipeline
CREATE USER dmi_eudr_app WITH PASSWORD 'Q#=pY9}yb:)ycNM^h_s%iYH]x9CNArBx=7iGjpkD';
GRANT ALL PRIVILEGES ON DATABASE geospatial_dmi TO dmi_eudr_app;
ALTER DATABASE geospatial_dmi OWNER TO dmi_eudr_app;

-- Create read-only user for reporting/monitoring
CREATE USER dmi_readonly WITH PASSWORD 'j!2Vn%G%*s}>VtIGx|WRm!wjc}c6&8g!';
GRANT CONNECT ON DATABASE geospatial_dmi TO dmi_readonly;

-- Grant privileges in geospatial_dmi database (run after connecting to it)
-- \c geospatial_dmi
-- GRANT SELECT ON ALL TABLES IN SCHEMA public TO dmi_readonly;
-- GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO dmi_readonly;
-- ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dmi_readonly;

-- Create Hansen tile database and grant permissions
CREATE DATABASE hansen_gfc_2024_v1_12_loss_treecover2000 OWNER dmi_eudr_app;
GRANT ALL PRIVILEGES ON DATABASE hansen_gfc_2024_v1_12_loss_treecover2000 TO dmi_eudr_app;
