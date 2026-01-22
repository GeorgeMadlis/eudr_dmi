# Task 3 Runbook — Report to MinIO (Shared Infra)

## Purpose
Generate a minimal EUDR report from an AOI GeoJSON and upload it to the shared MinIO stack under deterministic object keys.

This runbook is operator-oriented and uses copy/paste commands.

## Prerequisites
- Shared infra is running (MinIO + Postgres) and owned by `geospatial_dmi`.
  - See: [docs/runbooks/task3_minio_shared_infra.md](task3_minio_shared_infra.md)
- Credentials are stored outside this repo:
  - `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt`
- This repo must not commit secrets.

## 1) Start and verify shared infra

```sh
cd /Users/server/projects/geospatial_dmi/infra && docker compose up -d
curl -f http://localhost:9000/minio/health/ready
cd /Users/server/projects/geospatial_dmi/infra && docker compose -p infra ps
```

Optional verifier (from this repo):

```sh
cd /Users/server/projects/eudr_dmi
bash scripts/infra/verify_shared_infra.sh
```

## 2) Export MinIO environment variables (no hardcoded secrets)

Populate these values from:
- `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt`

```sh
export MINIO_ENDPOINT="localhost:9000"
export MINIO_ACCESS_KEY="<from CREDENTIALS_SUMMARY.txt>"
export MINIO_SECRET_KEY="<from CREDENTIALS_SUMMARY.txt>"
export MINIO_SECURE="false"
export EUDR_REPORTS_BUCKET="eudr-reports"
```

## 3) Choose an AOI GeoJSON

If you already have an example AOI:
- `data_examples/estonia_testland1.geojson`

Otherwise use the small Estonia AOI in this repo:
- `data_examples/estonia_small_aoi.geojson`

## 4) Run the report pipeline (deterministic run id)

From `eudr_dmi` repo root:

```sh
python -m task3_eudr_reports.run_eudr_report_to_minio \
  --aoi-geojson data_examples/estonia_small_aoi.geojson \
  --run-id demo_run_001 \
  --out-local /tmp/eudr_dmi_reports
```

Notes:
- With `--run-id demo_run_001`, object keys are stable:
  - `demo_run_001/demo_run_001.json`
  - `demo_run_001/demo_run_001.html`
- Without `--run-id`, the default is `YYYYMMDD_HHMMSS` in UTC.

## 5) Optional: enable deforestation area estimation

The deforestation area method requires a loss raster path.
If you have one available, set:

```sh
export EUDR_LOSS_RASTER_PATH="/absolute/path/to/loss.tif"
# Optional override if your raster CRS requires explicit area:
export EUDR_PIXEL_AREA_M2="9.0"
```

If not set, the report will record the deforestation section as UNDETERMINED (scaffold behavior).
