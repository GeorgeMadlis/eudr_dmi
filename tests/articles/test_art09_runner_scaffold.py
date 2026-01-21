from __future__ import annotations

import re

from eudr_dmi.articles.art_09 import runner

ISO_DATETIME_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


def test_runner_creates_expected_files_and_manifest(tmp_path, monkeypatch):
    monkeypatch.setenv("EUDR_DMI_EVIDENCE_ROOT", str(tmp_path))

    aoi_path = tmp_path / "aoi.geojson"
    aoi_path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    bundle_dir = runner.build_bundle(
        aoi_file=aoi_path,
        commodity="coffee",
        from_date="2026-01-01",
        to_date="2026-01-15",
    )

    assert bundle_dir.exists()

    expected = {
        "bundle_metadata.json",
        "art09_info_collection.json",
        "execution_log.json",
        "manifest.sha256",
    }
    assert expected.issubset({p.name for p in bundle_dir.iterdir() if p.is_file()})

    manifest_text = (bundle_dir / "manifest.sha256").read_text(encoding="utf-8")
    assert "bundle_metadata.json" in manifest_text
    assert "art09_info_collection.json" in manifest_text

    # execution_log.json is intentionally excluded (may contain timestamps)
    assert "execution_log.json" not in manifest_text


def test_bundle_id_is_deterministic(tmp_path, monkeypatch):
    monkeypatch.setenv("EUDR_DMI_EVIDENCE_ROOT", str(tmp_path))

    aoi_path = tmp_path / "aoi.geojson"
    aoi_path.write_bytes(b"dummy-geojson-bytes")

    bundle_id_1 = runner.compute_bundle_id(aoi_path, "2026-01-01", "2026-01-15")
    bundle_id_2 = runner.compute_bundle_id(aoi_path, "2026-01-01", "2026-01-15")
    assert bundle_id_1 == bundle_id_2


def test_deterministic_files_do_not_contain_timestamps(tmp_path, monkeypatch):
    monkeypatch.setenv("EUDR_DMI_EVIDENCE_ROOT", str(tmp_path))

    aoi_path = tmp_path / "aoi.geojson"
    aoi_path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    bundle_dir = runner.build_bundle(
        aoi_file=aoi_path,
        commodity="cocoa",
        from_date="2026-01-01",
        to_date="2026-01-15",
    )

    deterministic_files = [
        bundle_dir / "bundle_metadata.json",
        bundle_dir / "art09_info_collection.json",
    ]

    for p in deterministic_files:
        text = p.read_text(encoding="utf-8")
        assert ISO_DATETIME_RE.search(text) is None


def test_manifest_has_stable_sorted_entries(tmp_path, monkeypatch):
    monkeypatch.setenv("EUDR_DMI_EVIDENCE_ROOT", str(tmp_path))

    aoi_path = tmp_path / "aoi.geojson"
    aoi_path.write_text('{"type":"FeatureCollection","features":[]}', encoding="utf-8")

    bundle_dir = runner.build_bundle(
        aoi_file=aoi_path,
        commodity="rubber",
        from_date="2026-01-01",
        to_date="2026-01-15",
    )

    lines = (bundle_dir / "manifest.sha256").read_text(encoding="utf-8").splitlines()
    names = [line.split()[-1] for line in lines if line.strip()]
    assert names == sorted(names)
