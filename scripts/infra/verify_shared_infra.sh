#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

pass() {
  echo "PASS: $*"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

require_cmd docker
require_cmd curl

# Compose is typically `docker compose` (plugin). We rely on it being available.
docker compose version >/dev/null 2>&1 || fail "docker compose is not available (install Docker Desktop / compose plugin)"

# 1) Validate compose project label for MinIO container
# Requirement: compose project label for dmi_minio is infra
# We locate a running container matching name 'dmi_minio'.
container_id="$(docker ps --filter "name=dmi_minio" --format '{{.ID}}' | head -n 1)"
if [[ -z "${container_id}" ]]; then
  fail "No running container found matching name 'dmi_minio' (is the shared stack up?)"
fi

project_label="$(docker inspect -f '{{ index .Config.Labels "com.docker.compose.project" }}' "$container_id" 2>/dev/null || true)"
if [[ "${project_label}" != "infra" ]]; then
  fail "dmi_minio compose project label must be 'infra' (got '${project_label:-<empty>}')"
fi
pass "dmi_minio compose project label is infra"

# 2) MinIO readiness endpoint
curl -fsS http://localhost:9000/minio/health/ready >/dev/null || fail "MinIO health endpoint not ready: http://localhost:9000/minio/health/ready"
pass "MinIO health endpoint is ready"

# 3) Expected bind-mount roots
minio_dir="/Users/server/data/dmi/minio"
pg_dir="/Users/server/data/dmi/postgres"

[[ -d "$minio_dir" ]] || fail "Missing expected MinIO bind mount directory: $minio_dir"
[[ -d "$pg_dir" ]] || fail "Missing expected Postgres bind mount directory: $pg_dir"
pass "Bind mount directories exist"

pass "Shared infra verification succeeded"
