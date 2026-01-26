from __future__ import annotations

from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file

from scripts.validate_evidence_bundle import validate_bundle


def _write_manifest(bundle_dir: Path, rel_paths: list[str]) -> None:
    lines: list[str] = []
    for rel in rel_paths:
        digest = sha256_file(bundle_dir / rel)
        lines.append(f"{digest}  {rel}\n")

    (bundle_dir / "manifest.sha256").write_text("".join(lines), encoding="utf-8", newline="\n")


def test_validate_bundle_passes_with_matching_hashes(tmp_path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    (bundle / "bundle_metadata.json").write_text("{\"schema_version\":\"0.1\"}\n", encoding="utf-8")
    (bundle / "art09_info_collection.json").write_text("{\"status\":\"SCAFFOLD_ONLY\"}\n", encoding="utf-8")
    (bundle / "execution_log.json").write_text("{\"timestamp_utc\":\"2026-01-22T00:00:00Z\"}\n")

    _write_manifest(bundle, ["bundle_metadata.json", "art09_info_collection.json"])

    result = validate_bundle(bundle)
    assert result.ok
    assert result.errors == []


def test_validate_bundle_fails_on_hash_mismatch(tmp_path) -> None:
    bundle = tmp_path / "bundle"
    bundle.mkdir()

    (bundle / "bundle_metadata.json").write_text("{\"schema_version\":\"0.1\"}\n", encoding="utf-8")
    (bundle / "artifact.json").write_text("{\"x\":1}\n", encoding="utf-8")
    (bundle / "execution_log.json").write_text("{\"timestamp_utc\":\"2026-01-22T00:00:00Z\"}\n")

    _write_manifest(bundle, ["bundle_metadata.json", "artifact.json"])

    # Mutate after manifest is written.
    (bundle / "artifact.json").write_text("{\"x\":2}\n", encoding="utf-8")

    result = validate_bundle(bundle)
    assert not result.ok
    assert any("SHA256 mismatch for artifact.json" in e for e in result.errors)
