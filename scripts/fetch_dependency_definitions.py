from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eudr_dmi.evidence.hash_utils import sha256_file
from eudr_dmi.evidence.stable_json import read_json, write_json

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = REPO_ROOT / "docs" / "dependencies" / "sources.json"


def _ensure_repo_on_syspath() -> None:
    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))


def _utc_today_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    write_json(path, data)


def _iter_sources(*, registry: dict[str, Any], only_id: str | None) -> list[dict[str, Any]]:
    sources = list(registry.get("sources") or [])
    if only_id is None:
        return [s for s in sources if isinstance(s, dict)]
    filtered = [s for s in sources if isinstance(s, dict) and str(s.get("id")) == only_id]
    if not filtered:
        raise ValueError(f"No source with id={only_id!r} found in registry")
    return filtered


def _run_dir_for_source(*, source: dict[str, Any], run_date: str) -> Path:
    base = Path(str(source["server_local_path"]).strip())
    return base / run_date


def _write_run_summary(*, run_dir: Path, ok: bool, source_id: str) -> None:
    metadata_path = run_dir / "metadata.json"
    manifest_path = run_dir / "manifest.sha256"

    artifact_sha: str | None = None
    if metadata_path.exists():
        try:
            artifact_sha = str(_read_json(metadata_path).get("artifact_sha256") or "") or None
        except Exception:
            artifact_sha = None

    manifest_sha: str | None = None
    if manifest_path.exists():
        try:
            manifest_sha = sha256_file(manifest_path)
        except Exception:
            manifest_sha = None

    summary = {
        "status": "ok" if ok else "failed",
        "source_id": source_id,
        "artifact_sha256": artifact_sha,
        "manifest_sha256": manifest_sha,
    }
    _write_json(run_dir / "run_summary.json", summary)


def fetch_all_sources(
    *,
    sources_path: Path,
    run_date: str,
    only_id: str | None,
) -> tuple[list[Path], list[str]]:
    _ensure_repo_on_syspath()
    from tools.dependencies.acquire_and_hash import (  # noqa: PLC0415
        _validate_sources_registry_minimal,
        run_for_source,
    )

    registry = _read_json(sources_path)
    _validate_sources_registry_minimal(registry)
    sources = _iter_sources(registry=registry, only_id=only_id)

    run_dirs: list[Path] = []
    failures: list[str] = []

    for src in sources:
        source_id = str(src.get("id") or "").strip()
        run_dir = _run_dir_for_source(source=src, run_date=run_date)
        run_dirs.append(run_dir)

        ok = False
        try:
            ok, _msg = run_for_source(
                source=src,
                run_date=run_date,
                out_root=None,
                verify_only=False,
            )
        except Exception as exc:
            ok = False
            failures.append(
                "ERROR: id="
                f"{source_id} error_type={exc.__class__.__name__} error={exc}"
            )

        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            _write_run_summary(run_dir=run_dir, ok=ok, source_id=source_id)
        except Exception as exc:
            failures.append(
                "ERROR: id="
                f"{source_id} run_summary_write_failed={exc.__class__.__name__}:{exc}"
            )

        if not ok:
            failures.append(f"FAILED: id={source_id} run_dir={run_dir}")

    return run_dirs, failures


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python scripts/fetch_dependency_definitions.py",
        description=(
            "Thin orchestration wrapper around tools/dependencies/acquire_and_hash.py. "
            "For each dependency source, writes <server_local_path>/<YYYY-MM-DD>/ with "
            "artifact.bin + metadata.json + manifest.sha256. "
            "Also writes run_summary.json (status + hashes), with no timestamps."
        ),
    )
    p.add_argument(
        "--date",
        default=None,
        help="Run date YYYY-MM-DD (default: today in UTC)",
    )
    p.add_argument(
        "--id",
        default=None,
        help="Optional source id (if omitted, process all sources)",
    )
    p.add_argument("--sources", default=str(DEFAULT_SOURCES), help="Sources registry JSON")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    run_date = str(args.date).strip() if args.date else _utc_today_date()
    sources_path = Path(str(args.sources))

    if not sources_path.exists():
        print(f"ERROR: sources file not found: {sources_path}", file=sys.stderr)
        return 2

    run_dirs, failures = fetch_all_sources(
        sources_path=sources_path,
        run_date=run_date,
        only_id=args.id,
    )

    for rd in run_dirs:
        print(f"run_dir={rd}")

    for f in failures:
        print(f, file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
