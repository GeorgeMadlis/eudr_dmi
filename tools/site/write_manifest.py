#!/usr/bin/env python3
"""Write an audit-grade SHA-256 manifest for a folder.

Format:
    <sha256> <relative/path>

- Deterministic ordering (lexicographic by relative path)
- LF newlines
"""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_manifest(*, root: Path, out: Path) -> None:
    root = root.resolve()
    out = out.resolve()

    rel_paths: list[str] = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if p.resolve() == out:
            continue
        rel_paths.append(p.relative_to(root).as_posix())

    rel_paths.sort()

    lines: list[str] = []
    for rel in rel_paths:
        sha = _sha256_file(root / rel)
        lines.append(f"{sha} {rel}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Write SHA-256 manifest for a folder")
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args(argv)

    write_manifest(root=args.root, out=args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
