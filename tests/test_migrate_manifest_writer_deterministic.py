from __future__ import annotations

from pathlib import Path

from scripts.migrate_from_geospatial_dmi import write_manifest


def test_manifest_writer_is_deterministic(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()

    # Create directories and files in a deliberately non-sorted creation order.
    (repo / "prompts").mkdir()
    (repo / "data_db").mkdir()
    (repo / "mcp_servers").mkdir()

    (repo / "prompts" / "b.txt").write_text("bbb\n", encoding="utf-8")
    (repo / "prompts" / "a.txt").write_text("aaa\n", encoding="utf-8")
    (repo / "data_db" / "schema.sql").write_text("create table t(x int);\n", encoding="utf-8")
    (repo / "mcp_servers" / "server.py").write_text("print('hi')\n", encoding="utf-8")

    out1 = write_manifest.write_latest_manifest(
        write_manifest.ManifestOptions(
            repo_root=repo,
            include_paths=("data_db", "mcp_servers", "prompts"),
            optional_files=(),
            output_relpath="adopted/geospatial_dmi_snapshot/latest_manifest.sha256",
        )
    )
    content1 = out1.read_text(encoding="utf-8")

    out2 = write_manifest.write_latest_manifest(
        write_manifest.ManifestOptions(
            repo_root=repo,
            include_paths=("data_db", "mcp_servers", "prompts"),
            optional_files=(),
            output_relpath="adopted/geospatial_dmi_snapshot/latest_manifest.sha256",
        )
    )
    content2 = out2.read_text(encoding="utf-8")

    assert content1 == content2

    # Ensure paths are sorted.
    lines = [ln for ln in content1.splitlines() if ln.strip()]
    rels = [ln.split()[-1] for ln in lines]
    assert rels == sorted(rels)
