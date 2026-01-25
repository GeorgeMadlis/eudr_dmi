#!/bin/sh
set -euo pipefail

echo "quality-deps: scoped pytest"
python tools/ci/quality_scoped.py

echo "lint-deps: scoped ruff"
python tools/ci/lint_scoped.py
