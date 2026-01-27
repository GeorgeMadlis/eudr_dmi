#!/usr/bin/env bash
set -euo pipefail

# Backwards-compatible wrapper: the canonical script is build_site_bundle.sh.
# Kept to match operator docs / commands.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

bash scripts/build_site_bundle.sh

echo "[post] Create deterministic zip for sharing"
python tools/site/write_bundle_zip.py \
	--root docs/site_bundle \
	--out docs/site_bundle.zip \
	--sha256-out docs/site_bundle.zip.sha256

echo "OK: Zip ready at docs/site_bundle.zip"
