from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, date, datetime
from pathlib import Path

from eudr_dmi.articles.art_09.runner import (
    _git_commit,
    _load_sha256sums,
    _repo_root,
    _regulation_files,
    _safe_sha256_if_exists,
    resolve_audit_root,
    resolve_evidence_root,
    resolve_regulation_root,
)
from eudr_dmi.evidence.hash_utils import sha256_file, write_manifest_sha256


def compute_bundle_id(aoi_file: str | Path, from_date: str, to_date: str) -> str:
    aoi_path = Path(aoi_file)
    digest = hashlib.sha256(aoi_path.read_bytes()).hexdigest()[:12]
    return f"art10_{digest}_{from_date}_{to_date}"


def build_bundle(
    *,
    aoi_file: str | Path,
    commodity: str,
    from_date: str,
    to_date: str,
    now: datetime | None = None,
) -> Path:
    repo_root = _repo_root()
    evidence_root = resolve_evidence_root(repo_root)
    audit_root = resolve_audit_root(repo_root)
    regulation_root = resolve_regulation_root(audit_root)

    run_date = date.today().isoformat()
    bundle_id = compute_bundle_id(aoi_file, from_date, to_date)
    bundle_dir = evidence_root / run_date / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=False)

    aoi_path = Path(aoi_file).resolve()
    aoi_sha = sha256_file(aoi_path)

    sums_path = regulation_root / "SHA256SUMS.txt"
    sums_map = _load_sha256sums(sums_path)

    regulation_sources: list[dict[str, object]] = []
    for p in _regulation_files(regulation_root):
        regulation_sources.append(
            {
                "local_path": str(p.resolve()),
                "sha256": sums_map.get(p.name) or _safe_sha256_if_exists(p),
                "sha256sums_path": str(sums_path.resolve()),
            }
        )

    deterministic_metadata = {
        "schema_version": "0.1",
        "article": "10",
        "inputs": {
            "commodity": commodity,
            "from_date": from_date,
            "to_date": to_date,
            "aoi_file_path": str(aoi_path),
            "aoi_file_sha256": aoi_sha,
        },
        "evidence_root_resolved": str(evidence_root),
        "regulation_sources": regulation_sources,
    }

    info_collection = {
        "schema_version": "0.1",
        "article": "10",
        "status": "SCAFFOLD_ONLY",
        "inputs": {
            "commodity": commodity,
            "from_date": from_date,
            "to_date": to_date,
            "aoi_file_sha256": aoi_sha,
        },
        "todo": {
            "geospatial_dmi_integration": "TODO",
            "control_mapping": "TODO",
        },
    }

    bundle_metadata_path = bundle_dir / "bundle_metadata.json"
    bundle_metadata_path.write_text(
        json.dumps(deterministic_metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    art10_info_path = bundle_dir / "art10_info_collection.json"
    art10_info_path.write_text(
        json.dumps(info_collection, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if now is None:
        now = datetime.now(UTC)

    execution_log = {
        "schema_version": "0.1",
        "article": "10",
        "event": "runner_scaffold_executed",
        "timestamp_utc": now.isoformat(),
        "bundle_dir": str(bundle_dir),
        "git_commit": _git_commit(),
    }

    execution_log_path = bundle_dir / "execution_log.json"
    execution_log_path.write_text(
        json.dumps(execution_log, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    write_manifest_sha256(bundle_dir, exclude={"manifest.sha256", "execution_log.json"})

    return bundle_dir


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m eudr_dmi.articles.art_10.runner",
        description=(
            "Article 10 runner scaffold: creates a deterministic evidence bundle skeleton. "
            "Integration to upstream entrypoints is TODO."
        ),
    )
    parser.add_argument("--aoi-file", required=True, help="Path to AOI geometry file")
    parser.add_argument("--commodity", required=True, help="Commodity identifier")
    parser.add_argument("--from-date", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to-date", required=True, help="End date (YYYY-MM-DD)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    bundle_dir = build_bundle(
        aoi_file=args.aoi_file,
        commodity=args.commodity,
        from_date=args.from_date,
        to_date=args.to_date,
    )

    print(str(bundle_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
