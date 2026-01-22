from __future__ import annotations

import sys
from pathlib import Path


def _repo_root_from_this_file() -> Path:
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    # No CLI args yet; keep deterministic and operator-friendly.
    _ = argv
    repo_root = _repo_root_from_this_file()

    # When executed as a file (python scripts/.../02_write_manifest.py), the repo root
    # is not on sys.path. Add it so we can import the package implementation.
    sys.path.insert(0, str(repo_root))
    from scripts.migrate_from_geospatial_dmi.write_manifest import (
        ManifestOptions,
        write_latest_manifest,
    )

    out = write_latest_manifest(ManifestOptions(repo_root=repo_root))
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
