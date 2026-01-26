# Infrastructure Change Log

This log tracks all infrastructure changes following Golden Solution principles: evidence-based, traceable, testable.

---

## 2026-01-15: Canonicalized Compose Project Name

**Change:**
- Added `COMPOSE_PROJECT_NAME=infra` to `/Users/server/projects/geospatial_dmi/infra/.env`
- Added `name: infra` to top of `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`
- Created authoritative `DEPLOYMENT.md` documentation
- Created all required MinIO buckets for EUDR pipeline
- Uploaded Hansen URL manifest files to MinIO

**Reason:**
- Prevent accidental container duplication when starting compose from different directories
- Enforce single canonical project name: `infra`
- Ensure all workflows use bind mounts at `/Users/server/data/dmi/`
- Provide complete EUDR pipeline infrastructure
- Align with Executive Roadmap: data at `/Users/server/data/<project>/`

**Evidence (before fix):**
- Risk: Running `docker compose up -d` from repo root could create confusing project names
- Only one compose file exists: `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`
- Existing stack named `infra` but relied on implicit directory-based naming
- Only `eudr` bucket existed; EUDR pipeline requires 6 buckets
- Data stored in Docker named volumes instead of canonical bind mounts

**Evidence (after fix):**
```bash
$ docker compose ls
NAME    STATUS          CONFIG FILES
infra   running(2)      /Users/server/projects/geospatial_dmi/infra/docker-compose.yml

$ docker inspect dmi_minio | jq -r '.[0].Config.Labels["com.docker.compose.project"]'
infra

$ docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data") | .Source'
/Users/server/data/dmi/minio

$ docker exec dmi_minio mc ls local/
eudr-geofiles-in-checked/
eudr-geofiles-in-test/
eudr-reports/
hansen-gfc-2024-v1-12-loss/
hansen-gfc-2024-v1-12-treecover2000/
hansen-url-textfiles/

$ docker exec dmi_minio mc ls local/hansen-url-textfiles/
treecover2000.txt (366 B)
yearloss_2024.txt (351 B)
```

**Testing:**
- All containers restarted successfully after migration to bind mounts
- Future `docker compose up -d` from infra directory uses canonical bind mounts
- Future `docker compose up -d` from any directory (with .env) uses canonical bind mounts
- Complete infrastructure verification passes all checks (./verify_infra.sh)

**Related Files:**
- `/Users/server/projects/geospatial_dmi/infra/.env` (COMPOSE_PROJECT_NAME=infra)
- `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml` (uses bind mounts, name: infra)
- `/Users/server/projects/geospatial_dmi/infra/DEPLOYMENT.md` (updated for bind mounts)
- `/Users/server/projects/geospatial_dmi/infra/verify_infra.sh` (checks bind mounts and all buckets)
- `/Users/server/projects/geospatial_dmi/treecover2000.txt` (uploaded to MinIO)
- `/Users/server/projects/geospatial_dmi/yearloss_2024.txt` (uploaded to MinIO)

---

## 2026-01-15: Migrated to Host Bind Mounts (Non-Destructive)

**Change:**
- Created canonical host data root: `/Users/server/data/dmi/`
- Migrated MinIO and PostgreSQL data to host bind mounts (non-destructive copy)
- Updated docker-compose.yml to use bind mounts for `/data` and `/var/lib/postgresql/data`
- Updated verification and acceptance tests to validate bind mount paths

**Reason:**
- Align with Executive Roadmap and Golden Solution Authoring requirements
- Ensure operational visibility of data under `/Users/server/data/`

**Evidence:**
```bash
$ docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data" and .Type=="bind") | .Source'
/Users/server/data/dmi/minio

$ docker inspect dmi_postgres | jq -r '.[0].Mounts[] | select(.Destination=="/var/lib/postgresql/data" and .Type=="bind") | .Source'
/Users/server/data/dmi/postgres
```

**Notes:**
- Docker named volumes were preserved (not deleted)
- Migration performed as a copy operation to avoid data loss

---

## 2026-01-15: Production Credentials Deployment

**Change:**
- Generated strong random passwords for all users
- Deployed production credentials in `.env`, `keys.yml`, `.env.task3_local`
- Created MinIO application user: `dmi_eudr_app` with readwrite policy
- Created PostgreSQL users: `dmi_postgres_admin` (superuser), `dmi_eudr_app` (app user), `dmi_readonly` (monitoring)

**Evidence:**
- Credentials stored securely: `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt` (chmod 600)
- All services tested successfully: `python test_production_credentials.py` passed
- MinIO health: http://localhost:9000/minio/health/ready returns 200
- PostgreSQL connectivity: `psql -U dmi_eudr_app -d geospatial_dmi` connects

**Related Files:**
- `/Users/server/projects/geospatial_dmi/infra/.env`
- `/Users/server/projects/geospatial_dmi/src/task3_eudr_minio/configurations/keys.yml`
- `/Users/server/projects/geospatial_dmi/.env.task3_local`
- `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt`

---

## 2026-01-15: Infrastructure Hardening

**Change:**
- Added restart policies: `restart: unless-stopped` for minio/postgres, `restart: "no"` for init
- Changed MinIO healthcheck from `/minio/health/live` to `/minio/health/ready`
- Pinned image versions:
  - `minio/minio:RELEASE.2025-09-07T16-13-09Z`
  - `postgres:16.11`
  - `minio/mc:RELEASE.2025-08-13T08-35-41Z`

**Reason:**
- Automatic service recovery after host reboot or container crashes
- Better orchestration signals (ready vs live)
- Prevent unexpected breakage from upstream image changes

**Evidence:**
- Services survive `colima restart`
- Docker Compose health checks use `/ready` endpoint
- Image versions locked in docker-compose.yml

**Related Files:**
- `/Users/server/projects/geospatial_dmi/infra/docker-compose.yml`

---

## Previous Changes

- **2026-01-15:** Initial infrastructure setup (Colima, MinIO, PostgreSQL)
- **2026-01-15:** EUDR pipeline configuration and smoke test
- **2026-01-15:** Hansen tile infrastructure (URL manifests, PostgreSQL tile index, PostGIS)
- **2026-01-15:** Successful EUDR analysis (10 parcels, reports generated)

---

**Change log format:**
```
Date: YYYY-MM-DD
Change: What changed
Reason: Why it changed
Evidence: Proof it works (commands, outputs, test results)
Related Files: Paths to modified files
```
