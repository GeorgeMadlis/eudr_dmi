from __future__ import annotations

import hashlib
from pathlib import Path


def sha256_file(path: str | Path) -> str:
    file_path = Path(path)
    digest = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_manifest_sha256(bundle_dir: str | Path, exclude: set[str] | None = None) -> Path:
    bundle_path = Path(bundle_dir)
    exclude_set = {"manifest.sha256"} if exclude is None else set(exclude)

    entries: list[tuple[str, str]] = []
    for child in bundle_path.rglob("*"):
        if not child.is_file():
            continue

        rel_name = child.relative_to(bundle_path).as_posix()
        if rel_name in exclude_set or child.name in exclude_set:
            continue

        entries.append((rel_name, sha256_file(child)))

    entries.sort(key=lambda t: t[0])

    manifest_path = bundle_path / "manifest.sha256"
    with manifest_path.open("w", encoding="utf-8", newline="\n") as f:
        for rel_name, digest in entries:
            f.write(f"{digest}  {rel_name}\n")

    return manifest_path
