from __future__ import annotations

import json
from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file
from eudr_dmi.evidence.stable_json import write_json


def test_fetch_dependency_definitions_smoke(monkeypatch, tmp_path: Path) -> None:
    # Monkeypatch underlying fetch to avoid network and provide deterministic bytes.
    from scripts import fetch_dependency_definitions
    from tools.dependencies import acquire_and_hash

    def _fake_fetch_bytes_and_headers(url: str):  # noqa: ANN001
        return (
            b"fixed-bytes\n",
            200,
            {
                "content-type": "application/octet-stream",
                "etag": "deadbeef",
            },
        )

    monkeypatch.setattr(acquire_and_hash, "_fetch_bytes_and_headers", _fake_fetch_bytes_and_headers)

    server_base = tmp_path / "server" / "example_source"
    run_date = "2026-01-25"

    sources_path = tmp_path / "sources.json"
    write_json(
        sources_path,
        {
            "version": "1.0.0",
            "generated_at": None,
            "sources": [
                {
                    "id": "example",
                    "title": "Example",
                    "url": "https://example.invalid/fake",
                    "source_class": "DATA",
                    "content_type_expected": "application/octet-stream",
                    "server_local_path": str(server_base),
                    "notes": "fixture",
                }
            ],
        },
    )

    rc = fetch_dependency_definitions.main(
        [
            "--sources",
            str(sources_path),
            "--id",
            "example",
            "--date",
            run_date,
        ]
    )
    assert rc == 0

    run_dir = server_base / run_date

    artifact_path = run_dir / "artifact.bin"
    metadata_path = run_dir / "metadata.json"
    manifest_path = run_dir / "manifest.sha256"
    summary_path = run_dir / "run_summary.json"

    assert artifact_path.exists()
    assert metadata_path.exists()
    assert manifest_path.exists()
    assert summary_path.exists()

    # Metadata should be schema-valid.
    from jsonschema import validate

    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "schemas" / "dependency_run_metadata.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    validate(instance=metadata, schema=schema)

    # Summary should include hashes, with no timestamps.
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    assert summary["status"] == "ok"
    assert summary["source_id"] == "example"
    assert summary["artifact_sha256"] == metadata.get("artifact_sha256")
    assert summary["manifest_sha256"] == sha256_file(manifest_path)
    assert "generated_at" not in summary
