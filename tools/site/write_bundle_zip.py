#!/usr/bin/env python3
"""Create a deterministic ZIP archive of a folder.

- Walk all files under root
- Sort paths lexicographically
- Store paths as POSIX-style relative paths
- Force stable ZIP metadata (timestamp/permissions) for reproducible bytes

This is useful for sharing the bundle as a single file while keeping integrity
verification easy (pair with a sha256 file).
"""

from __future__ import annotations

import argparse
import hashlib
import stat
import zipfile
from pathlib import Path

_ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)  # earliest valid ZIP timestamp


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _iter_files(root: Path) -> list[str]:
    rel_paths: list[str] = []
    for p in root.rglob("*"):
        if p.is_file():
            rel_paths.append(p.relative_to(root).as_posix())
    rel_paths.sort()
    return rel_paths


def write_zip(*, root: Path, out: Path) -> None:
    root = root.resolve()
    out = out.resolve()

    out.parent.mkdir(parents=True, exist_ok=True)

    # Ensure we never accidentally include a pre-existing output zip inside root.
    if out.is_relative_to(root):
        raise ValueError("--out must not be inside --root")

    rel_paths = _iter_files(root)

    # Use deflate for smaller archives; fix compresslevel for reproducibility.
    with zipfile.ZipFile(
        out,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
        strict_timestamps=True,
    ) as zf:
        for rel in rel_paths:
            src = root / rel

            zi = zipfile.ZipInfo(filename=rel, date_time=_ZIP_EPOCH)
            zi.create_system = 3  # Unix

            # Normalize permissions: regular file 0644.
            zi.external_attr = (stat.S_IFREG | 0o644) << 16

            with src.open("rb") as f:
                data = f.read()
            zf.writestr(zi, data)


def write_sha256_sidecar(*, file_path: Path, out: Path) -> None:
    sha = _sha256_file(file_path)
    # Common sha256sum-style format: <sha256>  <filename>
    line = f"{sha}  {file_path.name}\n"
    out.write_text(line, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create deterministic ZIP archive of a folder")
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True, help="Path to write .zip")
    ap.add_argument(
        "--sha256-out",
        type=Path,
        default=None,
        help="Optional path to write a sha256 sidecar file for the zip",
    )
    args = ap.parse_args(argv)

    write_zip(root=args.root, out=args.out)

    if args.sha256_out is not None:
        args.sha256_out.parent.mkdir(parents=True, exist_ok=True)
        write_sha256_sidecar(file_path=args.out, out=args.sha256_out)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
