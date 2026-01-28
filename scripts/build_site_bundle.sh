#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

BUNDLE_ROOT="docs/site_bundle"
SITE_BUILD_ROOT="docs/site"   # where build_docs_site.py writes its pages
AUDIT_AOI_ROOT="/Users/server/audit/eudr_dmi/reports/aoi_runs"

# Controls
MAX_RUNS="${MAX_RUNS:-25}"                 # copy latest N runs (deterministic sort)
INCLUDE_AUDIT_JSON="${INCLUDE_AUDIT_JSON:-1}"  # include *.json sidecars
CLEAN="${CLEAN:-1}"

if [[ "$CLEAN" == "1" ]]; then
  rm -rf "$BUNDLE_ROOT"
  rm -rf "$SITE_BUILD_ROOT"
fi
mkdir -p "$BUNDLE_ROOT"

echo "[1/6] Build docs site (generated HTML)"
python tools/site/build_docs_site.py --out-root "$SITE_BUILD_ROOT" --portable --aoi-max-runs "$MAX_RUNS"

echo "[2/6] Copy generated site pages into bundle"
mkdir -p "$BUNDLE_ROOT/site"
rsync -a --delete "$SITE_BUILD_ROOT/" "$BUNDLE_ROOT/site/"

# Entry point stub required by contract.
cat > "$BUNDLE_ROOT/index.html" <<'HTML'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta http-equiv="refresh" content="0; url=site/index.html" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Audit Documentation Bundle</title>
    <style>
      body { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; padding: 24px; }
      a { color: #0b5fff; }
      code { background:#f1f1f1; padding:1px 4px; border-radius:6px; }
    </style>
  </head>
  <body>
    <h1>Audit Documentation Bundle</h1>
    <p>Redirecting to <a href="site/index.html">site/index.html</a>…</p>
    <p class="muted">If redirects are blocked, open <code>site/index.html</code>.</p>
  </body>
</html>
HTML

echo "[3/6] Copy regulation operator launcher + sources into bundle (portable paths)"
mkdir -p "$BUNDLE_ROOT/regulation"
cp -f "docs/regulation/links.html" "$BUNDLE_ROOT/regulation/links.html"

if [[ -f "docs/regulation/sources.md" ]]; then
  cp -f "docs/regulation/sources.md" "$BUNDLE_ROOT/regulation/sources.md"
fi
if [[ -f "docs/regulation/policy_to_evidence_spine.md" ]]; then
  cp -f "docs/regulation/policy_to_evidence_spine.md" "$BUNDLE_ROOT/regulation/policy_to_evidence_spine.md"
fi

echo "[3.3/6] Copy view docs into bundle (task/agentic/digital twin)"

REQUIRED_VIEW_DOCS=(
  "docs/views/task_view.md"
  "docs/views/agentic_view.md"
  "docs/views/digital_twin_view.md"
)

MISSING_VIEW_DOCS=()
for f in "${REQUIRED_VIEW_DOCS[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING_VIEW_DOCS+=("$f")
  fi
done

if (( ${#MISSING_VIEW_DOCS[@]} > 0 )); then
  echo "ERROR: required view docs missing:" >&2
  for f in "${MISSING_VIEW_DOCS[@]}"; do
    echo "  - $f" >&2
  done
  exit 1
fi

mkdir -p "$BUNDLE_ROOT/views"
for src in "${REQUIRED_VIEW_DOCS[@]}"; do
  cp -f "$src" "$BUNDLE_ROOT/views/$(basename "$src")"
done

echo "[3.4/6] Generate DAO proposal indexes (deterministic)"
python tools/site/build_dao_indexes.py

echo "[3.5/6] Copy DAO machine view descriptors into bundle (required for agent upload)"

REQUIRED_DAO_FILES=(
  "docs/dao/machine/dao_stakeholders/view.yaml"
  "docs/dao/machine/dao_stakeholders/proposals_index.yaml"
  "docs/dao/machine/dao_dev/view.yaml"
  "docs/dao/machine/dao_dev/proposals_index.yaml"
)

MISSING_DAO_FILES=()
for f in "${REQUIRED_DAO_FILES[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING_DAO_FILES+=("$f")
  fi
done

if (( ${#MISSING_DAO_FILES[@]} > 0 )); then
  echo "ERROR: required DAO machine files missing:" >&2
  for f in "${MISSING_DAO_FILES[@]}"; do
    echo "  - $f" >&2
  done
  echo "Bundle must be complete for agent upload." >&2
  exit 1
fi

mkdir -p "$BUNDLE_ROOT/machine"

# Copy while preserving folder structure under docs/dao/machine/...
for src in "${REQUIRED_DAO_FILES[@]}"; do
  rel="${src#docs/dao/machine/}"
  dest="$BUNDLE_ROOT/machine/$rel"
  mkdir -p "$(dirname "$dest")"
  cp -f "$src" "$dest"
done

echo "[3.6/6] Copy DAO agent prompts into bundle (required for agent upload)"

REQUIRED_AGENT_PROMPTS=(
  "docs/dao/agent_prompts/dao_stakeholders_prompt.md"
  "docs/dao/agent_prompts/dao_dev_prompt.md"
)

MISSING_AGENT_PROMPTS=()
for f in "${REQUIRED_AGENT_PROMPTS[@]}"; do
  if [[ ! -f "$f" ]]; then
    MISSING_AGENT_PROMPTS+=("$f")
  fi
done

if (( ${#MISSING_AGENT_PROMPTS[@]} > 0 )); then
  echo "ERROR: required agent prompt files missing:" >&2
  for f in "${MISSING_AGENT_PROMPTS[@]}"; do
    echo "  - $f" >&2
  done
  echo "Bundle must be complete for agent upload." >&2
  exit 1
fi

mkdir -p "$BUNDLE_ROOT/agent_prompts"
for src in "${REQUIRED_AGENT_PROMPTS[@]}"; do
  cp -f "$src" "$BUNDLE_ROOT/agent_prompts/$(basename "$src")"
done

echo "[4/6] Copy AOI report runs into bundle (portable, shareable)"
mkdir -p "$BUNDLE_ROOT/site/aoi_reports/runs"

if [[ -d "$AUDIT_AOI_ROOT" ]]; then
  RUN_LIST="$(find "$AUDIT_AOI_ROOT" -maxdepth 1 -type f -name "*.html" | sort -r | head -n "$MAX_RUNS")"

  while IFS= read -r f; do
    [[ -z "$f" ]] && continue
    base="$(basename "$f")"          # e.g. <run_id>.html
    run_id="${base%.html}"
    run_dir="$BUNDLE_ROOT/site/aoi_reports/runs/$run_id"
    mkdir -p "$run_dir"
    cp -f "$f" "$run_dir/report.html"

    if [[ "$INCLUDE_AUDIT_JSON" == "1" ]]; then
      if [[ -f "$AUDIT_AOI_ROOT/$run_id.json" ]]; then
        cp -f "$AUDIT_AOI_ROOT/$run_id.json" "$run_dir/summary.json"
      fi
    fi
  done <<< "$RUN_LIST"
else
  echo "WARN: AUDIT_AOI_ROOT not found: $AUDIT_AOI_ROOT" >&2
fi

echo "[5/6] Link integrity check (relative links must resolve inside bundle)"
python tools/site/check_site_links.py --root "$BUNDLE_ROOT" --out "$BUNDLE_ROOT/link_check.json"

echo "[6/6] Write manifest (sha256) for audit-grade sharing"
python tools/site/write_manifest.py --root "$BUNDLE_ROOT" --out "$BUNDLE_ROOT/manifest.sha256"

echo "OK: Bundle ready at $BUNDLE_ROOT"
echo "Open: $BUNDLE_ROOT/index.html"
