#!/usr/bin/env bash
set -euo pipefail

# Run a local AOI report and write HTML/JSON to the server audit root.
#
# Usage:
#   AOI_PATH=path/to/aoi.geojson RUN_ID=20260126_120000 bash scripts/run_aoi_report_local.sh
#   bash scripts/run_aoi_report_local.sh path/to/aoi.geojson [RUN_ID]

AOI_PATH="${AOI_PATH:-${1:-}}"
RUN_ID="${RUN_ID:-${2:-}}"

if [[ -z "$AOI_PATH" ]]; then
  echo "AOI_PATH is required (env var or first arg)." >&2
  exit 2
fi

OUT_LOCAL="/Users/server/audit/eudr_dmi/reports/aoi_runs"
CREDS_FILE="${EUDR_MINIO_CREDENTIALS_FILE:-/Users/server/secrets/eudr_dmi/CREDENTIALS_SUMMARY.txt}"
SKIP_MINIO="${SKIP_MINIO:-0}"

args=(
  -m task3_eudr_reports.run_eudr_report_to_minio
  --aoi-geojson "$AOI_PATH"
  --out-local "$OUT_LOCAL"
)

if [[ "$SKIP_MINIO" == "1" ]]; then
  args+=(--skip-minio)
else
  if [[ -f "$CREDS_FILE" ]]; then
    args+=(--minio-credentials-file "$CREDS_FILE")
  fi
fi

if [[ -n "$RUN_ID" ]]; then
  args+=(--run-id "$RUN_ID")
fi

python "${args[@]}"
