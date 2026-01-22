#!/bin/bash
# Create additional PostgreSQL users

export PGPASSWORD='Q#=pY9}yb:)ycNM^h_s%iYH]x9CNArBx=7iGjpkD'

# Create read-only user
docker exec -i dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi <<'EOF'
CREATE USER dmi_readonly WITH PASSWORD 'j!2Vn%G%*s}>VtIGx|WRm!wjc}c6&8g!';
GRANT CONNECT ON DATABASE geospatial_dmi TO dmi_readonly;
GRANT USAGE ON SCHEMA public TO dmi_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO dmi_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO dmi_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO dmi_readonly;
EOF

# Create Hansen database
docker exec -i dmi_postgres psql -U dmi_eudr_app -d postgres <<'EOF'
CREATE DATABASE hansen_gfc_2024_v1_12_loss_treecover2000 OWNER dmi_eudr_app;
EOF

# Install PostGIS in databases
docker exec -i dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi <<'EOF'
CREATE EXTENSION IF NOT EXISTS postgis;
EOF

docker exec -i dmi_postgres psql -U dmi_eudr_app -d hansen_gfc_2024_v1_12_loss_treecover2000 <<'EOF'
CREATE EXTENSION IF NOT EXISTS postgis;
EOF

echo "PostgreSQL users and databases configured successfully"
