from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/watch_eurlex_eudr_32023R1115.py",
        description=(
            "Daily watcher wrapper for the deterministic EUR-Lex mirror (CELEX:32023R1115). "
            "Exit codes: 0=no change, 2=change/update needed, 3=partial/blocked/uncertain."
        ),
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output base directory (run folder will be <out>/<YYYY-MM-DD>/)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Run date YYYY-MM-DD (default: date.today().isoformat())",
    )
    return parser


def _decide_exit_code(metadata: dict[str, Any]) -> int:
    status = metadata.get("status")
    needs_update = bool(metadata.get("needs_update"))

    run_dir = None
    if isinstance(metadata.get("run"), dict) and "run_dir" in metadata["run"]:
        run_dir = Path(metadata["run"]["run_dir"])

    trigger: dict[str, Any] | None = None
    if run_dir is not None:
        trigger_path = run_dir / "digital_twin_trigger.json"
        if trigger_path.exists():
            trigger = _read_json(trigger_path)

    reasons: list[str] = []
    if trigger is not None:
        reasons = [r for r in (trigger.get("reason") or []) if isinstance(r, str)]

    strong_reasons = {
        "no_previous_run",
        "lsu_hash_changed",
        "summary_last_update_changed",
        "pdf_sha256_changed",
        "html_sha256_changed",
        "eli_oj_sha256_changed",
    }

    uncertain_reasons = {
        "lsu_unreachable",
    }

    def _has_uncertainty(rs: list[str]) -> bool:
        if any(r in uncertain_reasons for r in rs):
            return True
        if any("unexpected" in r for r in rs):
            return True
        if any(r.endswith("_unexpected_signature") for r in rs):
            return True
        if any(r.endswith("_unexpected_content_type") for r in rs):
            return True
        return False

    def _has_strong_change(rs: list[str]) -> bool:
        return any(r in strong_reasons for r in rs)

    if status != "complete":
        if needs_update and _has_strong_change(reasons) and not _has_uncertainty(reasons):
            return 2
        return 3

    if needs_update:
        return 2

    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from scripts.fetch_eurlex_eudr_32023R1115 import resolve_run_date, run_mirror  # noqa: PLC0415

    run_date = resolve_run_date(args.date)
    out_base = Path(args.out)

    run_dir = run_mirror(out_base=out_base, run_date=run_date, repo_root=repo_root)
    metadata_path = run_dir / "metadata.json"
    metadata = _read_json(metadata_path)

    metadata.setdefault("run", {})
    if isinstance(metadata["run"], dict):
        metadata["run"]["run_dir"] = str(run_dir)

    exit_code = _decide_exit_code(metadata)

    reasons: list[str] = []
    trigger_path = run_dir / "digital_twin_trigger.json"
    if trigger_path.exists():
        trigger = _read_json(trigger_path)
        reasons = trigger.get("reason") or []

    print(f"run_dir={run_dir}")
    print(f"status={metadata.get('status')} needs_update={metadata.get('needs_update')}")
    if reasons:
        print("reason=" + ",".join(reasons))

    return int(exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
