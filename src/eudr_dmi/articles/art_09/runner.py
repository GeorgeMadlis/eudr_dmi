from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from datetime import UTC, date, datetime
from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file, write_manifest_sha256

SERVER_AUDIT_ROOT = Path("/Users/server/audit/eudr_dmi")
REGULATION_ROOT = SERVER_AUDIT_ROOT / "regulation" / "eudr_2023_1115"
REGULATION_FILES = [
    REGULATION_ROOT / "eudr_2023_1115_oj_eng.html",
    REGULATION_ROOT / "eudr_2023_1115_consolidated_2024-12-26_en.html",
    REGULATION_ROOT / "eudr_2023_1115_celex_32023R1115_en.pdf",
]


def _repo_root() -> Path:
    # Expected path in editable installs: <repo>/src/eudr_dmi/articles/art_09/runner.py
    here = Path(__file__).resolve()
    try:
        candidate = here.parents[5]
        if (candidate / "pyproject.toml").exists():
            return candidate
    except IndexError:
        pass
    return Path.cwd()


def _git_commit() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def compute_bundle_id(aoi_file: str | Path, from_date: str, to_date: str) -> str:
    aoi_path = Path(aoi_file)
    digest = hashlib.sha256(aoi_path.read_bytes()).hexdigest()[:12]
    return f"art09_{digest}_{from_date}_{to_date}"


def resolve_evidence_root(repo_root: Path) -> Path:
    configured = os.getenv("EUDR_DMI_EVIDENCE_ROOT") or "audit/evidence"
    configured_path = Path(configured)
    if configured_path.is_absolute():
        return configured_path
    return (repo_root / configured_path).resolve()


def _safe_sha256_if_exists(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    return sha256_file(path)


def _load_sha256sums(sums_path: Path) -> dict[str, str]:
    if not sums_path.exists():
        return {}
    mapping: dict[str, str] = {}
    for line in sums_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest = parts[0]
        filename = parts[-1]
        mapping[filename] = digest
    return mapping


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

    run_date = date.today().isoformat()
    bundle_id = compute_bundle_id(aoi_file, from_date, to_date)
    bundle_dir = evidence_root / run_date / bundle_id
    bundle_dir.mkdir(parents=True, exist_ok=False)

    aoi_path = Path(aoi_file)
    aoi_sha = sha256_file(aoi_path)

    sums_path = REGULATION_ROOT / "SHA256SUMS.txt"
    sums_map = _load_sha256sums(sums_path)

    regulation_sources: list[dict[str, object]] = []
    for p in REGULATION_FILES:
        regulation_sources.append(
            {
                "local_path": str(p),
                "sha256": sums_map.get(p.name) or _safe_sha256_if_exists(p),
                "sha256sums_path": str(sums_path),
            }
        )

    deterministic_metadata = {
        "schema_version": "0.1",
        "article": "9",
        "inputs": {
            "commodity": commodity,
            "from_date": from_date,
            "to_date": to_date,
            "aoi_file_path": str(aoi_file),
            "aoi_file_sha256": aoi_sha,
        },
        "evidence_root_resolved": str(evidence_root),
        "git_commit": _git_commit(),
        "regulation_sources": regulation_sources,
    }

    info_collection = {
        "schema_version": "0.1",
        "article": "9",
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

    art09_info_path = bundle_dir / "art09_info_collection.json"
    art09_info_path.write_text(
        json.dumps(info_collection, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    if now is None:
        now = datetime.now(UTC)

    execution_log = {
        "schema_version": "0.1",
        "article": "9",
        "event": "runner_scaffold_executed",
        "timestamp_utc": now.isoformat(),
        "bundle_dir": str(bundle_dir),
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
        prog="python -m eudr_dmi.articles.art_09.runner",
        description=(
            "Article 09 runner scaffold: creates a deterministic evidence bundle skeleton. "
            "Integration to geospatial_dmi entrypoints is TODO."
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
