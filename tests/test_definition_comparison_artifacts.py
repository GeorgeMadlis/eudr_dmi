from __future__ import annotations

import json
from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file
from eudr_dmi.evidence.stable_json import write_json


def _write_json(path: Path, payload: dict) -> None:
    write_json(path, payload, make_parents=True)


def test_definition_comparison_artifacts_schema_valid_and_deterministic(tmp_path: Path) -> None:
    from jsonschema import validate

    from scripts.task3 import definition_comparison_control

    regulation_snapshot = tmp_path / "reg_snapshot"
    regulation_snapshot.mkdir(parents=True)

    dependency_run = tmp_path / "deps" / "hansen_gfc_definitions" / "2026-01-25"
    dependency_run.mkdir(parents=True)

    artifact = dependency_run / "artifact.bin"
    artifact.write_bytes(b"fixture-bytes\n")

    meta = {
        "schema_version": "1.0.0",
        "source_id": "hansen_gfc_definitions",
        "url": "file:///unused",
        "content_type_expected": "application/octet-stream",
        "fetch_status": "ok",
        "http_status": None,
        "artifact_sha256": sha256_file(artifact),
        "notes": "fixture",
    }
    _write_json(dependency_run / "metadata.json", meta)

    # Minimal manifest file; its contents are hashed for provenance.
    (dependency_run / "manifest.sha256").write_text(
        sha256_file(artifact) + "  artifact.bin\n",
        encoding="utf-8",
        newline="\n",
    )

    out1 = tmp_path / "out1"
    out2 = tmp_path / "out2"

    rc1 = definition_comparison_control.main(
        [
            "--regulation-snapshot",
            str(regulation_snapshot),
            "--dependency-run",
            str(dependency_run),
            "--out",
            str(out1),
        ]
    )
    assert rc1 == 0

    rc2 = definition_comparison_control.main(
        [
            "--regulation-snapshot",
            str(regulation_snapshot),
            "--dependency-run",
            str(dependency_run),
            "--out",
            str(out2),
        ]
    )
    assert rc2 == 0

    prov1 = (out1 / "provenance" / "dependencies.json").read_text(encoding="utf-8")
    prov2 = (out2 / "provenance" / "dependencies.json").read_text(encoding="utf-8")
    assert prov1 == prov2

    comp1_path = out1 / "method" / "definition_comparison.json"
    comp2_path = out2 / "method" / "definition_comparison.json"

    comp1 = comp1_path.read_text(encoding="utf-8")
    comp2 = comp2_path.read_text(encoding="utf-8")
    assert comp1 == comp2

    # Schema validation.
    repo_root = Path(__file__).resolve().parents[1]
    schema = json.loads(
        (repo_root / "schemas" / "definition_comparison.schema.json").read_text(encoding="utf-8")
    )
    validate(instance=json.loads(comp1), schema=schema)

    # Provenance hashes.
    prov = json.loads(prov1)
    assert "hansen_gfc_definitions" in prov
    entry = prov["hansen_gfc_definitions"]
    assert entry["run_path"] == str(dependency_run)
    assert entry["artifact_sha256"] == meta["artifact_sha256"]
    assert entry["manifest_sha256"] == sha256_file(dependency_run / "manifest.sha256")
