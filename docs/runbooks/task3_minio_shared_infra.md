# Task 3 Runbook — Shared Infra (MinIO + Postgres)

## Purpose
This runbook documents how to start/stop/verify the shared MinIO + Postgres stack used as shared infrastructure.

This infrastructure is **owned and operated** by the `geospatial_dmi` repository under:
- `/Users/server/projects/geospatial_dmi/infra/`

Important constraint:
- The docker compose project name **must remain** `infra`.

## Boundary (secrets)
Credentials are stored outside this repository:
- `/Users/server/secrets/geospatial_dmi/CREDENTIALS_SUMMARY.txt`

This repository (`eudr_dmi`) **must not commit secrets**. Do not copy credentials into repo files, issues, or logs.

## Start the shared stack (copy/paste)

```sh
cd /Users/server/projects/geospatial_dmi/infra && docker compose up -d
```

## Stop the shared stack (copy/paste)

```sh
cd /Users/server/projects/geospatial_dmi/infra && docker compose down
```

## Verify the shared stack (copy/paste)

### 1) Health check (MinIO readiness)

```sh
curl -f http://localhost:9000/minio/health/ready
```

### 2) Verify containers (compose project = infra)

```sh
cd /Users/server/projects/geospatial_dmi/infra && docker compose -p infra ps
```

### 3) Run the local verifier script from this repo

From `eudr_dmi` repo root:

```sh
bash scripts/infra/verify_shared_infra.sh
```

If you prefer it executable:

```sh
chmod +x scripts/infra/verify_shared_infra.sh
./scripts/infra/verify_shared_infra.sh
```

## Expected host bind mounts
The shared stack is expected to persist data under these host paths:
- `/Users/server/data/dmi/minio`
- `/Users/server/data/dmi/postgres`

These paths are verified by the script.

## Notes
- The stack is shared; do not change compose project naming (`infra`) or volumes/paths from within this repository.
- Use the authoritative compose files in `/Users/server/projects/geospatial_dmi/infra/`.
