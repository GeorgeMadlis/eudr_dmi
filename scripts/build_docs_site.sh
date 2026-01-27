#!/usr/bin/env bash
set -euo pipefail

python tools/site/build_docs_site.py

required_files=(
  "docs/html/index.html"
  "docs/html/articles/index.html"
  "docs/html/articles/article_09.html"
  "docs/html/articles/article_10.html"
  "docs/html/articles/article_11.html"
  "docs/html/dependencies/index.html"
  "docs/html/aoi_reports/index.html"
)

for f in "${required_files[@]}"; do
  if [[ ! -f "$f" ]]; then
    echo "Missing expected output: $f" >&2
    exit 1
  fi
done

echo "Docs site build OK"
