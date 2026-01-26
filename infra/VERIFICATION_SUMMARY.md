# Infrastructure Canonicalization Summary

**Date:** 2026-01-15  
**Objective:** Prevent "fresh" MinIO deployments from creating duplicate containers/volumes  
**Solution:** Canonicalize all workflows to reuse existing `infra` stack

---

## A) Diagnosis Results

### Root Cause
Running `docker compose up -d` from a **different directory** (e.g., repo root) could cause Docker Compose to:
- Default project name to the parent directory name (`geospatial_dmi`)
- Create containers with different project labels
- Result: Confusion about which containers are canonical (now mitigated by bind mounts)

### Evidence (Pre-Fix)
```bash
$ docker compose ls
NAME    STATUS          CONFIG FILES
infra   running(2)      /Users/server/projects/geospatial_dmi/infra/docker-compose.yml

$ docker inspect dmi_minio | jq -r '.[0].Config.Labels["com.docker.compose.project"]'
infra

$ docker volume ls | egrep 'minio|pg'
infra_minio_data
infra_pg_data
```

**Analysis:** Only ONE stack exists and it's already correctly named `infra`. The problem is **not yet manifest** but the risk is real: any operator running compose from the wrong directory would create duplicates.

---

## B) Permanent Fix Implementation

### Changes Made

#### 1. Migrated to bind mounts (completed 2026-01-15)
**Data now resides on host filesystem:**
- MinIO: `/Users/server/data/dmi/minio/`
- PostgreSQL: `/Users/server/data/dmi/postgres/`
- Exports: `/Users/server/data/dmi/exports/`
- Backups: `/Users/server/data/dmi/backups/`

**Migration was non-destructive:**
- Original Docker volumes (`infra_minio_data`, `infra_pg_data`) preserved
- Data copied from volumes to bind mounts
- All buckets and databases migrated successfully

#### 2. Added COMPOSE_PROJECT_NAME to .env
**File:** `/Users/server/projects/geospatial_dmi/infra/.env`

**Change:**
```bash
# --- Compose Project Name (CANONICAL) ---
# This MUST be "infra" to ensure consistent project naming across all operations
COMPOSE_PROJECT_NAME=infra
```

**Effect:** Forces all `docker compose` commands to use project name `infra` regardless of working directory

#### 2. Added explicit name to docker-compose.yml
**File:** `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`

**Change:**
```yaml
# Explicit project name prevents accidental volume duplication
name: infra

services:
  minio:
    ...
```

**Effect:** Docker Compose 2.x uses explicit `name:` directive as canonical project name

#### 4. Bind mount configuration
The compose file now uses explicit host paths:
- `- /Users/server/data/dmi/minio:/data` (MinIO)
- `- /Users/server/data/dmi/postgres:/var/lib/postgresql/data` (PostgreSQL)

Docker volume declarations removed from docker-compose.yml.

---

## C) Documentation Updates

### Created Files

1. **`/Users/server/projects/geospatial_dmi/infra/DEPLOYMENT.md`**
   - Authoritative infrastructure documentation
   - Canonical startup sequence
   - Reusability guidelines
   - Troubleshooting procedures
   - Golden Solution Authoring principles
   - Executive Roadmap alignment

2. **`/Users/server/projects/geospatial_dmi/infra/CHANGELOG.md`**
   - Evidence-based change log
   - Traces all infrastructure modifications
   - Includes before/after verification commands

3. **`/Users/server/projects/geospatial_dmi/infra/verify_infra.sh`**
   - Automated verification script
   - 10 comprehensive checks
   - Color-coded pass/fail output
   - Usage: `cd /Users/server/projects/geospatial_dmi/infra && ./verify_infra.sh`

### Updated Files

1. **`/Users/server/projects/geospatial_dmi/README.md`**
   - Added Infrastructure section at top
   - Links to DEPLOYMENT.md
   - Quick infrastructure check commands

2. **`/Users/server/projects/geospatial_dmi/prompts/eudr/EUDR_MinIO_pipeline_smoke_test_SERVER.md`**
   - Updated canonical setup section
   - Added compose project name requirements
   - Added volume verification steps
   - References DEPLOYMENT.md

---

## D) Verification Results

### All Checks Passed ✓

```bash
$ cd /Users/server/projects/geospatial_dmi/infra && ./verify_infra.sh

=== DMI Infrastructure Verification ===

✓ Project name is 'infra'
✓ MinIO running and healthy
✓ PostgreSQL running and healthy
✓ MinIO bind mount: /Users/server/data/dmi/minio
✓ PostgreSQL bind mount: /Users/server/data/dmi/postgres
✓ MinIO project label: infra
✓ PostgreSQL project label: infra
✓ MinIO /ready endpoint responds
✓ Bucket: eudr-geofiles-in-checked
✓ Bucket: eudr-geofiles-in-test
✓ Bucket: eudr-reports
✓ Bucket: hansen-gfc-2024-v1-12-treecover2000
✓ Bucket: hansen-gfc-2024-v1-12-loss
✓ Bucket: hansen-url-textfiles
✓ treecover2000.txt exists
✓ yearloss_2024.txt exists
✓ PostgreSQL app user connection successful
✓ PostGIS extension available
✓ COMPOSE_PROJECT_NAME=infra set in .env
✓ name: infra set in docker-compose.yml
✓ /Users/server/data/dmi exists

=== All Checks Passed ===
```

### Manual Verification Commands

1. **Project identity:**
   ```bash
   docker compose -p infra ps
   # Shows: dmi_minio (Up), dmi_postgres (Up)
   ```

2. **Bind mount assignments:**
   ```bash
   docker inspect dmi_minio dmi_postgres | jq -r '.[] | {name: .Name, project: .Config.Labels["com.docker.compose.project"], bind_mount: (.Mounts[] | select(.Type=="bind") | .Source)}'
   # Output:
   # {"name": "/dmi_minio", "project": "infra", "bind_mount": "/Users/server/data/dmi/minio"}
   # {"name": "/dmi_postgres", "project": "infra", "bind_mount": "/Users/server/data/dmi/postgres"}
   ```

3. **MinIO bucket verification:**
   ```bash
   docker exec dmi_minio mc ls local/
   # Shows all 6 required buckets:
   # eudr-geofiles-in-checked/
   # eudr-geofiles-in-test/
   # eudr-reports/
   # hansen-gfc-2024-v1-12-treecover2000/
   # hansen-gfc-2024-v1-12-loss/
   # hansen-url-textfiles/
   ```

4. **Hansen URL manifest files:**
   ```bash
   docker exec dmi_minio mc ls local/hansen-url-textfiles/
   # Output: treecover2000.txt (366 B), yearloss_2024.txt (351 B)
   ```

5. **PostgreSQL connectivity:**
   ```bash
   docker exec dmi_postgres psql -U dmi_eudr_app -d geospatial_dmi -c "SELECT PostGIS_version();"
   # Output: 3.6 USE_GEOS=1 USE_PROJ=1 USE_STATS=1
   ```

---

## E) Golden Solution Authoring & Executive Roadmap Alignment

### Principles Implemented

1. **Single Source of Truth**
   - One canonical compose directory: `/Users/server/projects/geospatial_dmi/infra/`
   - One canonical project name: `infra`
   - One authoritative document: `DEPLOYMENT.md`

2. **Reusability**
   - All commands idempotent
   - Absolute paths eliminate ambiguity
   - Explicit project naming prevents accidents

3. **Continuous Monitoring**
   - Automated verification script
   - Docker healthchecks (`/minio/health/ready`, `pg_isready`)
   - Periodic manual checks documented

4. **Evidence-Based Operations**
   - CHANGELOG.md tracks all changes with evidence
   - Verification commands prove current state
   - Before/after comparisons documented

5. **Testability**
   - `verify_infra.sh` provides acceptance tests
   - Each check has clear pass/fail criteria
   - Exit codes enable automation

### Folder Convention Compliance

- **Infrastructure:** `/Users/server/projects/geospatial_dmi/infra/`
- **Credentials:** `/Users/server/secrets/` (chmod 600)
- **Data (canonical):** `/Users/server/data/dmi/`
  - MinIO data: `/Users/server/data/dmi/minio/`
  - PostgreSQL data: `/Users/server/data/dmi/postgres/`
  - Exports: `/Users/server/data/dmi/exports/`
  - Backups: `/Users/server/data/dmi/backups/`
- **Other project examples:** `/Users/server/data/numerai` (numerai_cron project)
- **Current approach:** Bind mounts at `/Users/server/data/dmi/` (aligned with Executive Roadmap)

---

## F) Files Modified/Created Summary

### Modified Files
1. `/Users/server/projects/geospatial_dmi/infra/.env`
   - Added `COMPOSE_PROJECT_NAME=infra`

2. `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`
   - Added `name: infra` directive

3. `/Users/server/projects/geospatial_dmi/README.md`
   - Added Infrastructure section

4. `/Users/server/projects/geospatial_dmi/prompts/eudr/EUDR_MinIO_pipeline_smoke_test_SERVER.md`
   - Updated canonical setup section
   - Added project name verification steps

### Created Files
1. `/Users/server/projects/geospatial_dmi/infra/DEPLOYMENT.md`
   - Authoritative infrastructure documentation (291 lines)

2. `/Users/server/projects/geospatial_dmi/infra/CHANGELOG.md`
   - Evidence-based change tracking

3. `/Users/server/projects/geospatial_dmi/infra/verify_infra.sh`
   - Automated acceptance testing script (executable)

4. `/Users/server/projects/geospatial_dmi/infra/VERIFICATION_SUMMARY.md` (this file)
   - Complete verification and implementation summary

---

## G) Operational Guidance

### Safe Startup (Always Use This)
```bash
colima start  # If VM not running
cd /Users/server/projects/geospatial_dmi/infra
docker compose up -d
```

### Verification After Startup
```bash
cd /Users/server/projects/geospatial_dmi/infra
./verify_infra.sh
```

### What to NEVER Do
```bash
# ❌ Starting from wrong directory without .env
cd /Users/server/projects/geospatial_dmi  # WRONG
docker compose up -d  # May create new containers with wrong bind mounts

# ❌ Deleting data directories
rm -rf /Users/server/data/dmi  # DESTROYS ALL DATA

# ❌ Running compose without knowing project name
docker compose up -d  # from arbitrary directory
```

### Safe Operations
```bash
# ✅ Restart services
cd /Users/server/projects/geospatial_dmi/infra
docker compose restart

# ✅ View logs
docker compose -p infra logs -f

# ✅ Check status
docker compose -p infra ps

# ✅ Verify configuration
docker compose config --format json | jq -r '.name'  # Should output: infra
```

---

## H) Success Criteria (All Met ✓)

- [x] Compose project name is `infra` (enforced in .env and docker-compose.yml)
- [x] Data stored at `/Users/server/data/dmi/minio/` and `/Users/server/data/dmi/postgres/` (bind mounts)
- [x] Container labels show `com.docker.compose.project=infra`
- [x] All 6 required MinIO buckets exist:
  - eudr-geofiles-in-checked
  - eudr-geofiles-in-test
  - eudr-reports
  - hansen-gfc-2024-v1-12-treecover2000
  - hansen-gfc-2024-v1-12-loss
  - hansen-url-textfiles
- [x] Hansen URL manifest files uploaded (treecover2000.txt, yearloss_2024.txt)
- [x] PostgreSQL connectivity works with app user
- [x] PostGIS extension available
- [x] All instruction files reference canonical setup
- [x] DEPLOYMENT.md created with Golden Solution principles
- [x] CHANGELOG.md tracks changes with evidence
- [x] Automated verification script passes all checks (including all buckets)
- [x] Documentation updated for consistency

---

**Status:** ✅ COMPLETE  
**Next Actions:** None required. Infrastructure is canonicalized and verified.  
**Maintainer:** DMI Infrastructure Team
