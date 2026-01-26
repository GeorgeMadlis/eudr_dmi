from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eudr_dmi.evidence.stable_json import read_json, write_json


def _read_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    write_json(path, data)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCES = REPO_ROOT / "docs" / "dependencies" / "sources.json"

# Canonical watcher output folder (date-subfolder) for triggers.
TRIGGERS_BASE = Path("/Users/server/audit/eudr_dmi/digital_twin_triggers/dependencies")

TRIGGER_NOTES = (
    "Dependency definition changed; downstream methods that rely on semantics must rerun "
    "definition_comparison control."
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/watch_dependency_definitions.py",
        description=(
            "Dependency-definition watcher: compares current vs previous artifact_sha256 and emits "
            "a canonical digital twin trigger if changed. Exit codes: 0=no change, 2=change, "
            "1=error/insufficient history."
        ),
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Run date YYYY-MM-DD (default: today in UTC)",
    )
    parser.add_argument(
        "--id",
        default=None,
        help="Optional source id (recommended if multiple sources exist)",
    )
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES), help="Sources registry JSON")
    return parser


def _utc_today_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _is_date_dir_name(name: str) -> bool:
    return len(name) == 10 and name[4] == "-" and name[7] == "-"


def _latest_prior_run_date(base: Path, run_date: str) -> str | None:
    if not base.exists() or not base.is_dir():
        return None
    dates: list[str] = []
    for child in base.iterdir():
        if not child.is_dir():
            continue
        if not _is_date_dir_name(child.name):
            continue
        if child.name >= run_date:
            continue
        if not (child / "metadata.json").exists():
            continue
        dates.append(child.name)
    return max(dates) if dates else None


def _iter_sources(*, registry: dict[str, Any], only_id: str | None) -> list[dict[str, Any]]:
    sources = [s for s in (registry.get("sources") or []) if isinstance(s, dict)]
    if only_id is None:
        return sources
    filtered = [s for s in sources if str(s.get("id")) == only_id]
    if not filtered:
        raise ValueError(f"No source with id={only_id!r} found in registry")
    return filtered


def _trigger_payload(
    *,
    source_id: str,
    previous_run: str,
    current_run: str,
    previous_artifact_sha256: str,
    current_artifact_sha256: str,
) -> dict[str, Any]:
    return {
        "trigger_type": "DEPENDENCY_DEFINITION_CHANGED",
        "source_id": source_id,
        "previous_run": previous_run,
        "current_run": current_run,
        "previous_artifact_sha256": previous_artifact_sha256,
        "current_artifact_sha256": current_artifact_sha256,
        "requires_rerun": True,
        "notes": TRIGGER_NOTES,
    }


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))

    from tools.dependencies.acquire_and_hash import (  # noqa: PLC0415
        _validate_sources_registry_minimal,
    )

    run_date = str(args.date).strip() if args.date else _utc_today_date()
    sources_path = Path(str(args.sources))
    if not sources_path.exists():
        print(f"ERROR: sources file not found: {sources_path}", file=sys.stderr)
        return 1

    registry = _read_json(sources_path)
    _validate_sources_registry_minimal(registry)
    sources = _iter_sources(registry=registry, only_id=args.id)

    changed: list[tuple[str, dict[str, Any]]] = []
    errors: list[str] = []

    for src in sources:
        source_id = str(src.get("id") or "").strip()
        base = Path(str(src.get("server_local_path") or "").strip())

        cur_dir = base / run_date
        cur_meta_path = cur_dir / "metadata.json"
        if not cur_meta_path.exists():
            errors.append(f"missing_current_metadata:{source_id}:{cur_meta_path}")
            continue

        cur_meta = _read_json(cur_meta_path)
        cur_sha = cur_meta.get("artifact_sha256")
        if not isinstance(cur_sha, str) or len(cur_sha) != 64:
            errors.append(f"invalid_current_artifact_sha256:{source_id}")
            continue

        prev_date = _latest_prior_run_date(base, run_date)
        if prev_date is None:
            errors.append(f"no_previous_run:{source_id}")
            continue

        prev_meta_path = (base / prev_date) / "metadata.json"
        if not prev_meta_path.exists():
            errors.append(f"missing_previous_metadata:{source_id}:{prev_meta_path}")
            continue

        prev_meta = _read_json(prev_meta_path)
        prev_sha = prev_meta.get("artifact_sha256")
        if not isinstance(prev_sha, str) or len(prev_sha) != 64:
            errors.append(f"invalid_previous_artifact_sha256:{source_id}")
            continue

        if prev_sha != cur_sha:
            changed.append(
                (
                    source_id,
                    _trigger_payload(
                        source_id=source_id,
                        previous_run=prev_date,
                        current_run=run_date,
                        previous_artifact_sha256=prev_sha,
                        current_artifact_sha256=cur_sha,
                    ),
                )
            )

    if errors:
        for e in errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    if not changed:
        return 0

    # Spec requires a single canonical trigger file; require --id if multiple sources changed.
    if len(changed) != 1:
        print(
            "ERROR: multiple sources changed; run with --id to emit a single canonical trigger",
            file=sys.stderr,
        )
        return 1

    source_id, payload = changed[0]
    out_dir = TRIGGERS_BASE / run_date
    out_dir.mkdir(parents=True, exist_ok=True)
    trigger_path = out_dir / "digital_twin_trigger.json"
    _write_json(trigger_path, payload)
    print(f"trigger_written={trigger_path} source_id={source_id}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
