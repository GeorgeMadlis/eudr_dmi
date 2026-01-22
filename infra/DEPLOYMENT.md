# DMI Infrastructure Deployment Guide

**Authoritative source of truth for DMI infrastructure services (MinIO + PostgreSQL)**

This document follows Golden Solution Authoring principles: authoritative, testable, continuously monitored.

---

## 1. Canonical Configuration

### Project Identity
- **Compose project name:** `infra` (MUST NOT change)
- **Compose file:** `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`
- **Environment file:** `/Users/server/projects/geospatial_dmi/infra/.env`

### Container Names
- `dmi_minio` - MinIO S3-compatible object storage
- `dmi_postgres` - PostgreSQL 16.11 with PostGIS 3.6
- `dmi_init` - One-shot initialization container

### Data Storage (Bind Mounts)
- `/Users/server/data/dmi/minio/` - MinIO bucket data (mounted at `/data` in container)
- `/Users/server/data/dmi/postgres/` - PostgreSQL database files (mounted at `/var/lib/postgresql/data` in container)

**CRITICAL:** These directories contain production data. Backup regularly using host filesystem tools.

### Service Endpoints
- **MinIO API:** http://localhost:9000
- **MinIO Console:** http://localhost:9001
- **PostgreSQL:** localhost:5432

---

## 2. Startup Sequence

### Prerequisites
1. Colima VM must be running:
   ```bash
   colima status
   # If not running:
   colima start
   ```

2. Docker context set to Colima:
   ```bash
   docker context show
   # Should output: colima
   ```

### Standard Startup

**Always start from the infra directory:**

```bash
cd /Users/server/projects/geospatial_dmi/infra
docker compose up -d
```

**Why this matters:**
- The `.env` file contains `COMPOSE_PROJECT_NAME=infra`
- The `docker-compose.yml` has `name: infra` at the top
- Starting from any other directory risks creating duplicate volumes

### Verifying Startup

```bash
# Check all services are healthy
docker compose ps

# Expected output:
# dmi_minio     Up (healthy)
# dmi_postgres  Up (healthy)
# dmi_init      Exited (0)
```

---

## 3. Reusing Existing Infrastructure

### Detection: Is the infra stack already running?

```bash
docker compose -p infra ps
```

If you see `dmi_minio` and `dmi_postgres` in Up state, the stack exists.

### Verification: Confirm bind mounts are populated

```bash
# Check MinIO buckets (all required buckets for EUDR pipeline)
docker exec dmi_minio mc alias set local http://localhost:9000 $MINIO_ROOT_USER "$MINIO_ROOT_PASSWORD"
docker exec dmi_minio mc ls local/

# Should show:
# - eudr-geofiles-in-checked/
# - eudr-geofiles-in-test/
# - eudr-reports/
# - hansen-gfc-2024-v1-12-treecover2000/
# - hansen-gfc-2024-v1-12-loss/
# - hansen-url-textfiles/
```

```bash
# Check Hansen URL manifest files
docker exec dmi_minio mc ls local/hansen-url-textfiles/
# Should show: treecover2000.txt, yearloss_2024.txt
```

```bash
# Check PostgreSQL databases
docker exec dmi_postgres psql -U dmi_postgres_admin -l

# Should show: geospatial_dmi, hansen (with PostGIS extension)
```

### What NOT to Do

❌ **Never run from wrong directory without setting project:**
```bash
cd /Users/server/projects/geospatial_dmi  # WRONG - parent directory
docker compose up -d  # May recreate containers with incorrect bind mount paths
```

❌ **Never destroy data directories:**
```bash
rm -rf /Users/server/data/dmi  # DESTROYS ALL DATA
docker compose down -v  # Not destructive with bind mounts, but risky pattern
```

✅ **Safe restart:**
```bash
cd /Users/server/projects/geospatial_dmi/infra
docker compose restart
```

---

## 4. Credential Management

### Production Credentials Location
- **Server storage:** `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt` (chmod 600)
- **Active config:** `/Users/server/projects/geospatial_dmi/infra/.env`
- **Application config:** `/Users/server/projects/geospatial_dmi/src/task3_eudr_minio/configurations/keys.yml`

### Users

**MinIO:**
- `dmi_minio_root` - Administrative account (console access, user management)
- `dmi_eudr_app` - Application account (readwrite policy on eudr bucket)

**PostgreSQL:**
- `dmi_postgres_admin` - Superuser (schema changes, extensions, backups)
- `dmi_eudr_app` - Application user (read/write on geospatial_dmi and hansen databases)
- `dmi_readonly` - Read-only monitoring account

### Credential Rotation
Recommended every 90 days. Process:
1. Generate new credentials: `python generate_credentials.py`
2. Update `.env`, `keys.yml`, `.env.task3_local`
3. Recreate MinIO users: `mc admin user add ...`
4. Recreate PostgreSQL users: `docker exec dmi_postgres psql ...`
5. Test all services: `python test_production_credentials.py`

---

## 5. Operational Roadmap (Golden Solution Principles)

### Continuous Monitoring

**Health Checks (automated):**
- MinIO: `/minio/health/ready` endpoint (Docker healthcheck)
- PostgreSQL: `pg_isready` command (Docker healthcheck)

**Periodic Verification (manual, weekly):**
```bash
# MinIO bucket verification
mc ls local/eudr/  # Confirm recent EUDR reports
mc ls local/hansen/  # Confirm Hansen tiles

# PostgreSQL database verification
psql -U dmi_eudr_app -d hansen -c "SELECT COUNT(*) FROM global;"  # Should show tile count
psql -U dmi_eudr_app -d geospatial_dmi -c "\dt"  # List application tables
```

### Reusability

All commands in this document are:
- **Idempotent:** Safe to run multiple times
- **Absolute paths:** No ambiguity about working directory
- **Explicit project naming:** Always uses `-p infra` or COMPOSE_PROJECT_NAME
- **Testable:** Exit codes and output parseable by scripts

### Evidence/Logging

**Change Log Format:**
```
Date: 2026-01-15
Change: Migrated from Docker named volumes to bind mounts at /Users/server/data/dmi/
Reason: Align with Executive Roadmap data location standards; improve operational visibility
Evidence: docker inspect shows bind mounts; data accessible at /Users/server/data/dmi/{minio,postgres}
```

Keep change log in: `/Users/server/projects/geospatial_dmi/infra/CHANGELOG.md`

### Makefile Targets (Optional Enhancement)

```makefile
.PHONY: infra-up infra-down infra-verify infra-logs

infra-up:
	cd /Users/server/projects/geospatial_dmi/infra && docker compose up -d

infra-verify:
	docker compose -p infra ps
	docker exec dmi_minio mc ls local/
	docker exec dmi_postgres psql -U dmi_postgres_admin -l

infra-logs:
	docker compose -p infra logs -f

infra-restart:
	cd /Users/server/projects/geospatial_dmi/infra && docker compose restart
```

---

## 6. Troubleshooting

### Issue: "Fresh" MinIO with no eudr bucket

**Symptom:** After running compose up, MinIO console shows no buckets.

**Diagnosis:**
```bash
docker ps --format "{{.Names}}\t{{.Labels}}" | grep compose.project
# Check if project name is NOT "infra"

docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data") | .Source'
# Check if bind mount is NOT "/Users/server/data/dmi/minio"
```

**Fix:**
1. Stop the wrong stack: `docker compose down` (from wherever you started it)
2. Verify data location: Check if `/Users/server/data/dmi/minio` exists and has data
3. Start correctly: `cd /Users/server/projects/geospatial_dmi/infra && docker compose up -d`

### Issue: PostgreSQL PostGIS extension missing

**Symptom:** `ERROR: type "geometry" does not exist`

**Fix:**
```bash
docker exec -it dmi_postgres bash
apt-get update && apt-get install -y postgresql-16-postgis-3
exit

# Then in each database:
psql -U dmi_postgres_admin -d geospatial_dmi -c "CREATE EXTENSION IF NOT EXISTS postgis;"
psql -U dmi_postgres_admin -d hansen -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

### Issue: Colima VM not running

**Symptom:** `Cannot connect to the Docker daemon`

**Fix:**
```bash
colima start
# Wait ~30 seconds for VM to initialize
docker context use colima
```

---

## 7. Server Folder Conventions

DMI follows Mac mini standard patterns:

- **Infrastructure configs:** `/Users/server/projects/geospatial_dmi/infra/`
- **Credentials (secrets):** `/Users/server/secrets/` (chmod 600)
- **Project data root (required):** `/Users/server/data/dmi/` (bind mounts are canonical)
- **Other project data examples:**
  - Numerai cron: `/Users/server/data/numerai` (sftp://macmini.local/Users/server/data/numerai)

**Current data strategy:** Bind mounts under `/Users/server/data/dmi/` are canonical. Data is stored on the host filesystem for operational visibility and alignment with the Executive Roadmap:
- MinIO data: `/Users/server/data/dmi/minio/`
- PostgreSQL data: `/Users/server/data/dmi/postgres/`
- Exports/backups: `/Users/server/data/dmi/exports/` and `/Users/server/data/dmi/backups/`
- Operational artifacts: `/Users/server/data/dmi/ops-logs/`

**Directory baseline (required):**
```
/Users/server/data/dmi/
```

---

## 8. Acceptance Tests

Run these commands to verify full stack health:

```bash
# 1. Compose project identity
docker compose -p infra ps | grep -q "dmi_minio.*Up" && echo "✓ MinIO running"
docker compose -p infra ps | grep -q "dmi_postgres.*Up" && echo "✓ Postgres running"

# 2. Bind mount paths
docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data" and .Type=="bind") | .Source' | grep -q "/Users/server/data/dmi/minio" && echo "✓ MinIO bind mount correct"
docker inspect dmi_postgres | jq -r '.[0].Mounts[] | select(.Destination=="/var/lib/postgresql/data" and .Type=="bind") | .Source' | grep -q "/Users/server/data/dmi/postgres" && echo "✓ Postgres bind mount correct"

# 3. Project label
docker inspect dmi_minio | jq -r '.[0].Config.Labels["com.docker.compose.project"]' | grep -q "infra" && echo "✓ Project label = infra"

# 4. MinIO connectivity
curl -f http://localhost:9000/minio/health/ready && echo "✓ MinIO health check passed"

# 5. MinIO buckets exist
docker exec dmi_minio mc alias set local http://localhost:9000 dmi_minio_root "$MINIO_ROOT_PASSWORD" >/dev/null 2>&1
docker exec dmi_minio mc ls local/eudr-geofiles-in-checked/ >/dev/null 2>&1 && echo "✓ eudr-geofiles-in-checked exists"
docker exec dmi_minio mc ls local/eudr-geofiles-in-test/ >/dev/null 2>&1 && echo "✓ eudr-geofiles-in-test exists"
docker exec dmi_minio mc ls local/eudr-reports/ >/dev/null 2>&1 && echo "✓ eudr-reports exists"
docker exec dmi_minio mc ls local/hansen-gfc-2024-v1-12-treecover2000/ >/dev/null 2>&1 && echo "✓ hansen treecover2000 bucket exists"
docker exec dmi_minio mc ls local/hansen-gfc-2024-v1-12-loss/ >/dev/null 2>&1 && echo "✓ hansen loss bucket exists"
docker exec dmi_minio mc ls local/hansen-url-textfiles/ >/dev/null 2>&1 && echo "✓ hansen-url-textfiles exists"

# 6. PostgreSQL connectivity
docker exec dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi -c "SELECT 1;" >/dev/null 2>&1 && echo "✓ Postgres app user connected"

# 7. PostGIS extension
docker exec dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi -c "SELECT PostGIS_version();" >/dev/null 2>&1 && echo "✓ PostGIS available"

# 8. Canonical data root exists
test -d /Users/server/data/dmi && echo "✓ /Users/server/data/dmi exists"
```

Expected output: All checks show ✓

---

## 9. References

- **Executive Roadmap:** See attached PDFs for reusability, continuous monitoring, evidence-based operations
- **Golden Solution Authoring:** Authoritative documentation, testable workflows, single source of truth
- **EUDR smoke test:** [/Users/server/projects/geospatial_dmi/prompts/eudr/EUDR_MinIO_pipeline_smoke_test_SERVER.md](../prompts/eudr/EUDR_MinIO_pipeline_smoke_test_SERVER.md)
- **Main README:** [/Users/server/projects/geospatial_dmi/README.md](../README.md)

---

**Document version:** 1.0  
**Last updated:** 2026-01-15  
**Maintainer:** DMI Infrastructure Team
