## EUDR MinIO pipeline smoke test (SERVER / Docker / Colima)

**Date created:** 2026-01-15
**Last updated:** 2026-01-15 (canonicalized infra project name)
**Supersedes:** MacBook-Pro local MinIO prompt
**Scope:** Task 3 (EUDR) – MinIO + Hansen + Maa-amet integration
**Host:** Mac mini (headless), Colima, Docker Compose
**Compose project:** `infra` (canonical, must not change)

---

### Goal

Run the integrated EUDR analysis pipeline against:

* an **AOI GeoJSON stored in MinIO**
* **Hansen GFC tiles (treecover2000 + loss)** stored in MinIO
* **Maa-amet cadastral parcels**, selecting **10 parcels** where forest area ≥ **3 ha**

This prompt verifies the **entire Task 3 data plane**, not just code correctness.

---

### IMPORTANT SAFETY CONSTRAINTS

* **DO NOT** print or paste secrets from:

  * `src/task3_eudr_minio/configurations/keys.yml`
  * `.env.task3_local`
* It is allowed to **read secrets locally** to configure clients.
* Bucket names, object keys, table names **may be printed**.

---

### Canonical server setup (authoritative)

**Infrastructure Stack (MUST reuse existing):**

* **Compose project name:** `infra` (enforced in .env and docker-compose.yml)
* **Compose directory:** `/Users/server/projects/geospatial_dmi/infra/`
* **Data storage:**
  * Bind mounts at `/Users/server/data/dmi/minio/` (MinIO data)
  * Bind mounts at `/Users/server/data/dmi/postgres/` (PostgreSQL data)
* **Containers:**
  * `dmi_minio` (MinIO server)
  * `dmi_postgres` (PostgreSQL 16.11 with PostGIS 3.6)
  * `dmi_init` (one-shot initialization)

**MinIO**

* API: `http://localhost:9000`
* Console: `http://localhost:9001`
* Runtime: **Docker Compose via Colima**
* Data persistence: **Bind mount at `/Users/server/data/dmi/minio/`**
* Data is directly accessible on host filesystem

**PostgreSQL**

* Host: `localhost:5432`
* DB: `geospatial_dmi`, `hansen`
* Purpose:

  * Hansen tile index
  * Supporting metadata queries

**Environment**

* Repo root: `/Users/server/projects/geospatial_dmi`
* Python: `.venv` (already created)
* Active env file: `.env.task3_local`

**Startup Sequence:**

```bash
# ALWAYS start from infra directory to reuse existing volumes
colima start  # If VM not running
cd /Users/server/projects/geospatial_dmi/infra
docker compose up -d
```

**Reference:** See [/Users/server/projects/geospatial_dmi/infra/DEPLOYMENT.md](../../infra/DEPLOYMENT.md) for complete infrastructure documentation.

---

### Required MinIO buckets (full 10-parcel run)

These must exist before running analysis:

* `eudr-geofiles-in-checked`
* `eudr-geofiles-in-test`
* `eudr-reports`
* `hansen-gfc-2024-v1-12-treecover2000`
* `hansen-gfc-2024-v1-12-loss`
* `hansen-url-textfiles`

  * must contain:

    * `treecover2000.txt`
    * `yearloss_2024.txt`

If any are missing, the pipeline **must stop**.

---

### Test input

* **AOI object in MinIO**
  `eudr-geofiles-in-checked/estonia_testland1.geojson`

* **Local fallback source**
  `data_examples/estonia_testland1.geojson`

---

## Runbook (execute strictly in order)

---

### 1) Confirm Docker-managed infrastructure is running

```bash
cd /Users/server/projects/geospatial_dmi/infra
docker compose ps
```

Expected output:

* `dmi_minio` - Up (healthy)
* `dmi_postgres` - Up (healthy)
* `dmi_init` - Exited (0)

**Verify project name is `infra`:**

```bash
docker inspect dmi_minio | jq -r '.[0].Config.Labels["com.docker.compose.project"]'
# Must output: infra
```

**Verify bind mounts are canonical:**

```bash
docker inspect dmi_minio | jq -r '.[0].Mounts[] | select(.Destination=="/data") | .Source'
# Must show: /Users/server/data/dmi/minio

docker inspect dmi_postgres | jq -r '.[0].Mounts[] | select(.Destination=="/var/lib/postgresql/data") | .Source'
# Must show: /Users/server/data/dmi/postgres
```

If services are not running → `docker compose up -d` from infra directory  
If project name is NOT `infra` → **STOP and consult DEPLOYMENT.md**

---

### 2) Activate venv and environment

```bash
cd /Users/server/projects/geospatial_dmi
source .venv/bin/activate
set -a
source .env.task3_local
set +a
```

---

### 3) Verify required buckets exist (safe)

```bash
python - <<'PY'
from minio import Minio
from src.task3_eudr_minio.eudr_utilities import utilities_config

meta = utilities_config.merge_configurations()
client = Minio(
    meta['minio_endpoint'],
    access_key=meta['minio_access_key'],
    secret_key=meta['minio_secret_key'],
    secure=False,
)

buckets = sorted(b.name for b in client.list_buckets())
print("Buckets:")
for b in buckets:
    print(" -", b)

needed = [
    meta['geofiles-in-checked'],
    meta['geofiles-in'],
    meta['reports_bucket'],
    meta['hansen_bucket_treecover2000'],
    meta['hansen_bucket_loss'],
    meta['hansen_urls_bucket'],
]

missing = [b for b in needed if b not in buckets]
print("\nMissing:")
print(" (none)" if not missing else "\n".join(" - "+m for m in missing))
PY
```

If Hansen buckets are missing → **STOP**.

---

### 4) Ensure AOI object exists (upload if needed)

```bash
python - <<'PY'
from pathlib import Path
from minio import Minio
from src.task3_eudr_minio.eudr_utilities import utilities_config

meta = utilities_config.merge_configurations()
client = Minio(meta['minio_endpoint'],
               meta['minio_access_key'],
               meta['minio_secret_key'],
               secure=False)

bucket = meta['geofiles-in-checked']
name = "estonia_testland1.geojson"

found = any(o.object_name == name for o in client.list_objects(bucket, recursive=True))
print("found?", found)

if not found:
    local = Path("data_examples/estonia_testland1.geojson")
    client.fput_object(bucket, name, str(local))
    print("uploaded", name)
PY
```

---

### 5) Verify Postgres + Hansen tile index DB

```bash
pg_isready -h localhost -p 5432
```

Optional deep check:

```bash
python - <<'PY'
import psycopg2
from src.task3_eudr_minio.eudr_utilities import utilities_config

meta = utilities_config.merge_configurations()
conn = psycopg2.connect(
    dbname=meta['database_name_hansen'],
    user=meta['postgresql_user'],
    password=meta['postgresql_pw'],
    host='localhost'
)
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM global")
print("global rows:", cur.fetchone()[0])
conn.close()
PY
```

---

### 6) Export missing Hansen tiles for AOI

```bash
python src/task3_eudr_minio/geojson_tiles_monitor.py estonia_testland1.geojson
```

Expected:

* tiles exported into:

  * `hansen-gfc-2024-v1-12-loss/...`
  * `hansen-gfc-2024-v1-12-treecover2000/...`

---

### 7) Run integrated EUDR analysis (10 parcels)

```bash
python src/task3_eudr_minio/eudr_maaamet_integrated_analysis.py \
  --geometry-path estonia_testland1.geojson \
  --min-target-parcels 10 \
  --max-parcels 2000
```

Expected:

* Parcels analyzed: **10**
* Hansen raster analysis executed
* No `NoSuchBucket` errors

---

### Outputs

Written to MinIO bucket `eudr-reports`:

* `integrated_eudr_<timestamp>.json`
* `integrated_eudr_<timestamp>.html`
* `integrated_eudr_<timestamp>_map.html`

---

### Debugging checklist

* `NoSuchBucket` → missing bucket or wrong MinIO endpoint
* `No treecover2000 tiles found` → Step 6 not executed
* `Connection refused` → Docker services not running
* Hansen DB errors → Postgres container down or wrong DB name

---

## End of prompt
