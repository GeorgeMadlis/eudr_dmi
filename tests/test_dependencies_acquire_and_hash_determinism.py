from __future__ import annotations

import json
from pathlib import Path

from eudr_dmi.evidence.stable_json import write_json


def _write_sources_registry(
    path: Path,
    *,
    source_id: str,
    url: str,
    server_local_path: str,
) -> None:
    registry = {
        "version": "1.0.0",
        "generated_at": None,
        "sources": [
            {
                "id": source_id,
                "title": "Example",
                "url": url,
                "source_class": "DATA",
                "content_type_expected": "application/octet-stream",
                "server_local_path": server_local_path,
                "notes": "fixture",
            }
        ],
    }
    write_json(path, registry)


def test_dependencies_acquire_and_hash_fetch_is_deterministic(tmp_path: Path) -> None:
    from jsonschema import validate

    from tools.dependencies.acquire_and_hash import main

    # Source file served via file:// for deterministic tests.
    src = tmp_path / "src.bin"
    src.write_bytes(b"hello\n")

    sources = tmp_path / "sources.json"
    _write_sources_registry(
        sources,
        source_id="example",
        url=f"file://{src}",
        server_local_path=str(tmp_path / "unused"),
    )

    out_root = tmp_path / "out"
    run_date = "2026-01-25"

    rc1 = main(
        [
            "--sources",
            str(sources),
            "--id",
            "example",
            "--date",
            run_date,
            "--out-root",
            str(out_root),
        ]
    )
    assert rc1 == 0

    run_dir = out_root / "example" / run_date
    metadata_path = run_dir / "metadata.json"
    manifest_path = run_dir / "manifest.sha256"

    assert (run_dir / "artifact.bin").exists()
    assert metadata_path.exists()
    assert manifest_path.exists()

    meta1 = metadata_path.read_text(encoding="utf-8")
    manifest1 = manifest_path.read_text(encoding="utf-8")

    # Re-run to same folder: outputs should remain byte-identical.
    rc2 = main(
        [
            "--sources",
            str(sources),
            "--id",
            "example",
            "--date",
            run_date,
            "--out-root",
            str(out_root),
        ]
    )
    assert rc2 == 0
    assert meta1 == metadata_path.read_text(encoding="utf-8")
    assert manifest1 == manifest_path.read_text(encoding="utf-8")

    # Manifest ordering must be stable and sorted.
    lines = [ln for ln in manifest1.splitlines() if ln.strip()]
    rels = [ln.split("  ", 1)[1] for ln in lines]
    assert rels == sorted(rels)

    # Metadata validates against schema.
    repo_root = Path(__file__).resolve().parents[1]
    schema_path = repo_root / "schemas" / "dependency_run_metadata.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    instance = json.loads(meta1)
    validate(instance=instance, schema=schema)


def test_dependencies_acquire_and_hash_verify_detects_mismatch(tmp_path: Path) -> None:
    from tools.dependencies.acquire_and_hash import main

    src = tmp_path / "src.bin"
    src.write_bytes(b"hello\n")

    sources = tmp_path / "sources.json"
    _write_sources_registry(
        sources,
        source_id="example",
        url=f"file://{src}",
        server_local_path=str(tmp_path / "unused"),
    )

    out_root = tmp_path / "out"
    run_date = "2026-01-25"

    rc_fetch = main(
        [
            "--sources",
            str(sources),
            "--id",
            "example",
            "--date",
            run_date,
            "--out-root",
            str(out_root),
        ]
    )
    assert rc_fetch == 0

    run_dir = out_root / "example" / run_date
    artifact = run_dir / "artifact.bin"
    artifact.write_bytes(b"tampered\n")

    rc_verify = main(
        [
            "--sources",
            str(sources),
            "--id",
            "example",
            "--date",
            run_date,
            "--out-root",
            str(out_root),
            "--verify",
        ]
    )
    assert rc_verify != 0
