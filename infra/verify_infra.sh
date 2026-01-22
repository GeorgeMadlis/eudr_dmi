#!/bin/bash
# Infrastructure Verification Script
# Tests all components of the DMI infrastructure stack
# Run from: /Users/server/projects/geospatial_dmi/infra/

set -e

echo "=== DMI Infrastructure Verification ==="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# 1. Compose project identity
echo "1. Checking compose project identity..."
PROJECT_NAME=$(docker compose config --format json | jq -r '.name')
if [ "$PROJECT_NAME" = "infra" ]; then
    check_pass "Project name is 'infra'"
else
    check_fail "Project name is '$PROJECT_NAME' (expected 'infra')"
fi

# 2. Services running
echo "2. Checking services are running..."
if docker compose -p infra ps | grep -q "dmi_minio.*Up.*healthy"; then
    check_pass "MinIO running and healthy"
else
    check_fail "MinIO not running or not healthy"
fi

if docker compose -p infra ps | grep -q "dmi_postgres.*Up.*healthy"; then
    check_pass "PostgreSQL running and healthy"
else
    check_fail "PostgreSQL not running or not healthy"
fi

# 3. Bind mount assignments
echo "3. Checking bind mount assignments..."
MINIO_BIND=$(docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data" and .Type=="bind") | .Source')
if [ "$MINIO_BIND" = "/Users/server/data/dmi/minio" ]; then
    check_pass "MinIO bind mount: /Users/server/data/dmi/minio"
else
    check_fail "MinIO bind mount is '$MINIO_BIND' (expected '/Users/server/data/dmi/minio')"
fi

POSTGRES_BIND=$(docker inspect dmi_postgres | jq -r '.[0].Mounts[] | select(.Destination=="/var/lib/postgresql/data" and .Type=="bind") | .Source')
if [ "$POSTGRES_BIND" = "/Users/server/data/dmi/postgres" ]; then
    check_pass "PostgreSQL bind mount: /Users/server/data/dmi/postgres"
else
    check_fail "PostgreSQL bind mount is '$POSTGRES_BIND' (expected '/Users/server/data/dmi/postgres')"
fi

# 4. Project labels
echo "4. Checking container labels..."
MINIO_PROJECT=$(docker inspect dmi_minio | jq -r '.[0].Config.Labels["com.docker.compose.project"]')
if [ "$MINIO_PROJECT" = "infra" ]; then
    check_pass "MinIO project label: infra"
else
    check_fail "MinIO project label is '$MINIO_PROJECT' (expected 'infra')"
fi

POSTGRES_PROJECT=$(docker inspect dmi_postgres | jq -r '.[0].Config.Labels["com.docker.compose.project"]')
if [ "$POSTGRES_PROJECT" = "infra" ]; then
    check_pass "PostgreSQL project label: infra"
else
    check_fail "PostgreSQL project label is '$POSTGRES_PROJECT' (expected 'infra')"
fi

# 5. MinIO health
echo "5. Checking MinIO health endpoint..."
if curl -sf http://localhost:9000/minio/health/ready > /dev/null; then
    check_pass "MinIO /ready endpoint responds"
else
    check_fail "MinIO health check failed"
fi

# 6. MinIO buckets (using credentials from .env)
echo "6. Checking MinIO buckets..."
source .env
docker exec dmi_minio mc alias set local http://localhost:9000 "$MINIO_ROOT_USER" "$MINIO_ROOT_PASSWORD" > /dev/null 2>&1

REQUIRED_BUCKETS=(
    "eudr-geofiles-in-checked"
    "eudr-geofiles-in-test"
    "eudr-reports"
    "hansen-gfc-2024-v1-12-treecover2000"
    "hansen-gfc-2024-v1-12-loss"
    "hansen-url-textfiles"
)

MISSING_BUCKETS=()
for bucket in "${REQUIRED_BUCKETS[@]}"; do
    if docker exec dmi_minio mc ls local/$bucket/ > /dev/null 2>&1; then
        check_pass "Bucket: $bucket"
    else
        check_fail "Bucket missing: $bucket"
        MISSING_BUCKETS+=("$bucket")
    fi
done

# 6b. Check Hansen URL manifest files
echo "6b. Checking Hansen URL manifest files..."
if docker exec dmi_minio mc ls local/hansen-url-textfiles/treecover2000.txt > /dev/null 2>&1; then
    check_pass "treecover2000.txt exists"
else
    check_fail "treecover2000.txt missing in hansen-url-textfiles"
fi

if docker exec dmi_minio mc ls local/hansen-url-textfiles/yearloss_2024.txt > /dev/null 2>&1; then
    check_pass "yearloss_2024.txt exists"
else
    check_fail "yearloss_2024.txt missing in hansen-url-textfiles"
fi

# 7. PostgreSQL connectivity
echo "7. Checking PostgreSQL connectivity..."
if docker exec dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi -c "SELECT 1;" > /dev/null 2>&1; then
    check_pass "PostgreSQL app user connection successful"
else
    check_fail "PostgreSQL connection failed"
fi

# 8. PostGIS extension
echo "8. Checking PostGIS extension..."
if docker exec dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi -c "SELECT PostGIS_version();" > /dev/null 2>&1; then
    check_pass "PostGIS extension available"
else
    check_fail "PostGIS extension not available"
fi

# 9. COMPOSE_PROJECT_NAME in .env
echo "9. Checking .env configuration..."
if grep -q "^COMPOSE_PROJECT_NAME=infra" .env; then
    check_pass "COMPOSE_PROJECT_NAME=infra set in .env"
else
    check_fail "COMPOSE_PROJECT_NAME not set in .env"
fi

# 10. docker-compose.yml name directive
echo "10. Checking docker-compose.yml configuration..."
if grep -q "^name: infra" docker-compose.yml; then
    check_pass "name: infra set in docker-compose.yml"
else
    check_fail "name: infra not set in docker-compose.yml"
fi

# 11. Canonical data root directory
echo "11. Checking canonical data root..."
if [ -d "/Users/server/data/dmi" ]; then
    check_pass "/Users/server/data/dmi exists"
else
    check_fail "/Users/server/data/dmi does not exist"
fi

echo ""
echo "=== All Checks Passed ==="
echo ""
echo "Infrastructure Status Summary:"
echo "  Project:   infra"
echo "  Services:  dmi_minio (healthy), dmi_postgres (healthy)"
echo "  Data:      /Users/server/data/dmi/minio, /Users/server/data/dmi/postgres"
echo "  Endpoints: MinIO (localhost:9000), PostgreSQL (localhost:5432)"
echo ""
