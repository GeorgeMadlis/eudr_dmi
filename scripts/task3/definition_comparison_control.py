#!/usr/bin/env python

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from eudr_dmi.evidence.hash_utils import sha256_file
from eudr_dmi.evidence.stable_json import read_json, write_json

CONTROL_ID = "definition_consistency"
CONTROL_VERSION = "0.1.0"
DEPENDENCY_SOURCE_ID = "hansen_gfc_definitions"


def _read_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    write_json(path, data, make_parents=True)


def _safe_sha256(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_file(path)


def _load_dependency_run_fingerprints(dependency_run: Path) -> tuple[str | None, str | None]:
    meta_path = dependency_run / "metadata.json"
    manifest_path = dependency_run / "manifest.sha256"

    artifact_sha: str | None = None
    if meta_path.exists():
        meta = _read_json(meta_path)
        v = meta.get("artifact_sha256")
        if isinstance(v, str) and len(v) == 64:
            artifact_sha = v

    if artifact_sha is None:
        artifact_sha = _safe_sha256(dependency_run / "artifact.bin")

    manifest_sha = _safe_sha256(manifest_path)

    return artifact_sha, manifest_sha


def build_artifacts(
    *,
    regulation_snapshot: Path,
    dependency_run: Path,
    out_root: Path,
) -> None:
    artifact_sha, manifest_sha = _load_dependency_run_fingerprints(dependency_run)

    provenance = {
        DEPENDENCY_SOURCE_ID: {
            "run_path": str(dependency_run),
            "artifact_sha256": artifact_sha,
            "manifest_sha256": manifest_sha,
        }
    }

    comparison = {
        "control_id": CONTROL_ID,
        "control_version": CONTROL_VERSION,
        "inputs": {
            "regulation_snapshot_path": str(regulation_snapshot),
            "dependency_source_id": DEPENDENCY_SOURCE_ID,
            "dependency_run_path": str(dependency_run),
        },
        "extracted": {
            "eudr_definition_elements": [],
            "dependency_definition_elements": [],
        },
        "comparison": {
            "mismatches": [],
            "gaps": [],
            "impact_statement": "TBD",
            "outcome": "UNKNOWN",
        },
    }

    _write_json(out_root / "provenance" / "dependencies.json", provenance)
    _write_json(out_root / "method" / "definition_comparison.json", comparison)


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python scripts/task3/definition_comparison_control.py",
        description=(
            "Task3 control scaffold: Definition consistency / interpretability constraint. "
            "Writes deterministic artifacts comparing EUDR definition elements vs dependency "
            "definition elements."
        ),
    )
    p.add_argument(
        "--regulation-snapshot",
        required=True,
        type=Path,
        help="Path to mirrored EUDR artefact folder",
    )
    p.add_argument(
        "--dependency-run",
        required=True,
        type=Path,
        help="Path to dependency run folder (<...>/<source_id>/<YYYY-MM-DD>/)",
    )
    p.add_argument(
        "--out",
        required=True,
        type=Path,
        help="Evidence bundle root to write artifacts",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    regulation_snapshot = Path(args.regulation_snapshot)
    dependency_run = Path(args.dependency_run)
    out_root = Path(args.out)

    if not regulation_snapshot.exists():
        print(f"ERROR: regulation snapshot not found: {regulation_snapshot}", file=sys.stderr)
        return 2

    if not dependency_run.exists():
        print(f"ERROR: dependency run not found: {dependency_run}", file=sys.stderr)
        return 2

    # Ensure required dependency-run artifacts exist.
    if not (dependency_run / "metadata.json").exists():
        print(f"ERROR: dependency run missing metadata.json: {dependency_run}", file=sys.stderr)
        return 2
    if not (dependency_run / "manifest.sha256").exists():
        print(f"ERROR: dependency run missing manifest.sha256: {dependency_run}", file=sys.stderr)
        return 2

    build_artifacts(
        regulation_snapshot=regulation_snapshot,
        dependency_run=dependency_run,
        out_root=out_root,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
