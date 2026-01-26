from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


DEFAULT_RELATIVE_PATHS: tuple[str, ...] = (
    "data_db",
    "mcp_servers",
    "prompts",
    "llm",
    "infra",
    "config",
)

DEFAULT_OPTIONAL_TOP_LEVEL_FILES: tuple[str, ...] = (
    "demo_mcp_maaamet.py",
    "eudr_compliance_check_estonia.py",
    "demo_mcp_servers.py",
)


@dataclass(frozen=True, slots=True)
class ManifestOptions:
    repo_root: Path
    include_paths: tuple[str, ...] = DEFAULT_RELATIVE_PATHS
    optional_files: tuple[str, ...] = DEFAULT_OPTIONAL_TOP_LEVEL_FILES
    output_relpath: str = "adopted/geospatial_dmi_snapshot/latest_manifest.sha256"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_files_under(base: Path) -> list[Path]:
    if not base.exists():
        return []
    if base.is_file():
        return [base]

    files: list[Path] = []
    for p in base.rglob("*"):
        if p.is_file():
            files.append(p)
    return files


def write_latest_manifest(options: ManifestOptions) -> Path:
    repo_root = options.repo_root.resolve()

    included_files: list[Path] = []

    for rel in options.include_paths:
        included_files.extend(_iter_files_under(repo_root / rel))

    for fname in options.optional_files:
        p = repo_root / fname
        if p.exists() and p.is_file():
            included_files.append(p)

    # Stable ordering by repo-relative POSIX path.
    rel_to_abs: dict[str, Path] = {}
    for p in included_files:
        rel = p.resolve().relative_to(repo_root).as_posix()
        rel_to_abs[rel] = p.resolve()

    relpaths = sorted(rel_to_abs.items(), key=lambda kv: kv[0])

    out_path = repo_root / options.output_relpath
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    for rel_path, abs_path in relpaths:
        digest = _sha256_file(abs_path)
        lines.append(f"{digest}  {rel_path}\n")

    out_path.write_text("".join(lines), encoding="utf-8", newline="\n")
    return out_path


__all__ = [
    "DEFAULT_RELATIVE_PATHS",
    "DEFAULT_OPTIONAL_TOP_LEVEL_FILES",
    "ManifestOptions",
    "write_latest_manifest",
]
