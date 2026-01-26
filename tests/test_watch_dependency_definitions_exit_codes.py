from __future__ import annotations

import json
from pathlib import Path

from eudr_dmi.evidence.stable_json import write_json


def _write_metadata(path: Path, artifact_sha256: str) -> None:
    # Minimal metadata compatible with the dependency-run schema.
    payload = {
        "schema_version": "1.0.0",
        "source_id": "example",
        "url": "file:///unused",
        "content_type_expected": "application/octet-stream",
        "fetch_status": "ok",
        "http_status": None,
        "artifact_sha256": artifact_sha256,
        "notes": "fixture",
    }
    write_json(path, payload)


def _write_sources(path: Path, server_local_path: Path) -> None:
    payload = {
        "version": "1.0.0",
        "generated_at": None,
        "sources": [
            {
                "id": "example",
                "title": "Example",
                "url": "file:///unused",
                "source_class": "DATA",
                "content_type_expected": "application/octet-stream",
                "server_local_path": str(server_local_path),
                "notes": "fixture",
            }
        ],
    }
    write_json(path, payload)


def test_watch_dependency_definitions_change_detected_emits_trigger(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from scripts import watch_dependency_definitions

    server_base = tmp_path / "server" / "example"
    prev_date = "2026-01-24"
    cur_date = "2026-01-25"

    (server_base / prev_date).mkdir(parents=True)
    (server_base / cur_date).mkdir(parents=True)
    _write_metadata(server_base / prev_date / "metadata.json", "a" * 64)
    _write_metadata(server_base / cur_date / "metadata.json", "b" * 64)

    sources = tmp_path / "sources.json"
    _write_sources(sources, server_base)

    triggers_root = tmp_path / "triggers" / "dependencies"
    monkeypatch.setattr(watch_dependency_definitions, "TRIGGERS_BASE", triggers_root)

    rc = watch_dependency_definitions.main(
        ["--sources", str(sources), "--id", "example", "--date", cur_date]
    )
    assert rc == 2

    trigger_path = triggers_root / cur_date / "digital_twin_trigger.json"
    assert trigger_path.exists()
    trigger = json.loads(trigger_path.read_text(encoding="utf-8"))
    assert trigger["trigger_type"] == "DEPENDENCY_DEFINITION_CHANGED"
    assert trigger["source_id"] == "example"
    assert trigger["previous_run"] == prev_date
    assert trigger["current_run"] == cur_date
    assert trigger["previous_artifact_sha256"] == "a" * 64
    assert trigger["current_artifact_sha256"] == "b" * 64
    assert trigger["requires_rerun"] is True
    assert "notes" in trigger


def test_watch_dependency_definitions_no_change_exit_0(monkeypatch, tmp_path: Path) -> None:
    from scripts import watch_dependency_definitions

    server_base = tmp_path / "server" / "example"
    prev_date = "2026-01-24"
    cur_date = "2026-01-25"

    (server_base / prev_date).mkdir(parents=True)
    (server_base / cur_date).mkdir(parents=True)
    _write_metadata(server_base / prev_date / "metadata.json", "a" * 64)
    _write_metadata(server_base / cur_date / "metadata.json", "a" * 64)

    sources = tmp_path / "sources.json"
    _write_sources(sources, server_base)

    triggers_root = tmp_path / "triggers" / "dependencies"
    monkeypatch.setattr(watch_dependency_definitions, "TRIGGERS_BASE", triggers_root)

    rc = watch_dependency_definitions.main(
        ["--sources", str(sources), "--id", "example", "--date", cur_date]
    )
    assert rc == 0

    assert not (triggers_root / cur_date / "digital_twin_trigger.json").exists()


def test_watch_dependency_definitions_missing_previous_run_exit_1(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from scripts import watch_dependency_definitions

    server_base = tmp_path / "server" / "example"
    cur_date = "2026-01-25"
    (server_base / cur_date).mkdir(parents=True)
    _write_metadata(server_base / cur_date / "metadata.json", "a" * 64)

    sources = tmp_path / "sources.json"
    _write_sources(sources, server_base)

    triggers_root = tmp_path / "triggers" / "dependencies"
    monkeypatch.setattr(watch_dependency_definitions, "TRIGGERS_BASE", triggers_root)

    rc = watch_dependency_definitions.main(
        ["--sources", str(sources), "--id", "example", "--date", cur_date]
    )
    assert rc == 1

    assert not (triggers_root / cur_date / "digital_twin_trigger.json").exists()
