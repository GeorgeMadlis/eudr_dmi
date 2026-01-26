#!/usr/bin/env bash
set -euo pipefail

# Idempotent migration copier: geospatial_dmi -> eudr_dmi
# - Copies selected folders using rsync (with --delete)
# - Explicitly excludes common secret/runtime/output folders
# - Safe to rerun: destination mirrors the selected source subsets

SRC="/Users/server/projects/geospatial_dmi"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="$(cd "${SCRIPT_DIR}/../.." && pwd)"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "FAIL: missing required command: $1" >&2
    exit 1
  }
}

require_cmd rsync
require_cmd find

if [[ ! -d "${SRC}" ]]; then
  echo "FAIL: SRC does not exist: ${SRC}" >&2
  exit 1
fi

EXCLUDES=(
  "--exclude=.git/"
  "--exclude=audit/"
  "--exclude=outputs/"
  "--exclude=.venv/"
  "--exclude=__pycache__/"
  "--exclude=*.pyc"
  "--exclude=.env"
  "--exclude=.env.*"
  "--exclude=keys.yml"
)

sync_dir() {
  local rel="$1"
  local src_path="${SRC}/${rel}"
  local dest_path="${DEST}/${rel}"

  if [[ ! -d "${src_path}" ]]; then
    echo "SKIP: ${rel} (missing in source)"
    return 0
  fi

  mkdir -p "${dest_path}"

  echo "SYNC: ${rel}"
  rsync -a --delete "${EXCLUDES[@]}" "${src_path}/" "${dest_path}/"
}

sync_file_if_exists() {
  local filename="$1"
  local src_file="${SRC}/${filename}"
  local dest_file="${DEST}/${filename}"

  if [[ ! -f "${src_file}" ]]; then
    echo "SKIP: ${filename} (missing in source)"
    return 0
  fi

  echo "COPY: ${filename}"
  rsync -a "${EXCLUDES[@]}" "${src_file}" "${dest_file}"
}

# Copy selected folders into repo root
sync_dir "data_db"
sync_dir "mcp_servers"
sync_dir "prompts"
sync_dir "llm"
sync_dir "infra"
sync_dir "config"

# Copy selected top-level demo scripts (if present)
sync_file_if_exists "demo_mcp_maaamet.py"
sync_file_if_exists "eudr_compliance_check_estonia.py"
sync_file_if_exists "demo_mcp_servers.py"

# Post-copy safety checks (ensure no secrets were copied)
# Note: these checks operate only on the copied targets.
TARGETS=(
  "${DEST}/data_db"
  "${DEST}/mcp_servers"
  "${DEST}/prompts"
  "${DEST}/llm"
  "${DEST}/infra"
  "${DEST}/config"
)

for t in "${TARGETS[@]}"; do
  if [[ -d "${t}" ]]; then
    if find "${t}" \( -name ".env" -o -name ".env.*" -o -name "keys.yml" \) -print | grep -q .; then
      echo "FAIL: secret-like files found under ${t} (.env* or keys.yml). Remove from source or add exclusions." >&2
      exit 2
    fi
  fi
done

echo "PASS: copy completed (no secret-like files detected)."
