from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from eudr_dmi.evidence.hash_utils import sha256_file, write_manifest_sha256
from eudr_dmi.evidence.stable_json import read_json, write_json

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SOURCES = REPO_ROOT / "docs" / "dependencies" / "sources.json"

DEFAULT_OUT_ROOT = Path("/Users/server/audit/eudr_dmi/dependencies")

ALLOWED_HEADERS = ("content-type", "etag", "last-modified")

RUN_METADATA_SCHEMA_VERSION = "1.0.0"


def _utc_today_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    data = read_json(path)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


def _write_json(path: Path, data: dict[str, Any]) -> None:
    write_json(path, data)


def _validate_sources_registry_minimal(data: dict[str, Any]) -> None:
    # Keep runtime dependencies minimal (do not require jsonschema). We only
    # perform a strict-enough validation to protect the tool from bad input.
    if not isinstance(data, dict):
        raise ValueError("sources registry must be a JSON object")
    if data.get("generated_at") is not None:
        raise ValueError("sources registry generated_at must be null for determinism")
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources registry must contain a 'sources' array")
    for i, src in enumerate(sources):
        if not isinstance(src, dict):
            raise ValueError(f"sources[{i}] must be an object")
        required_keys = (
            "id",
            "title",
            "url",
            "source_class",
            "content_type_expected",
            "server_local_path",
        )
        for k in required_keys:
            v = src.get(k)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"sources[{i}].{k} must be a non-empty string")
        if src.get("source_class") != "DATA":
            raise ValueError(f"sources[{i}].source_class must be 'DATA'")


def _iter_sources(*, registry: dict[str, Any], only_id: str | None) -> list[dict[str, Any]]:
    sources = list(registry.get("sources") or [])
    if only_id is None:
        return sources
    filtered = [s for s in sources if isinstance(s, dict) and str(s.get("id")) == only_id]
    if not filtered:
        raise ValueError(f"No source with id={only_id!r} found in registry")
    return filtered


def _run_dir_for_source(
    *,
    source_id: str,
    server_local_path: str,
    run_date: str,
    out_root: Path | None,
) -> Path:
    if out_root is None:
        base = Path(server_local_path)
    else:
        base = Path(out_root) / source_id
    return base / run_date


def _fetch_bytes_and_headers(url: str) -> tuple[bytes, int | None, dict[str, str]]:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        src_path = Path(parsed.path)
        if not src_path.exists() or not src_path.is_file():
            raise FileNotFoundError(f"file URL does not exist: {src_path}")
        return src_path.read_bytes(), None, {}

    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"Unsupported URL scheme: {parsed.scheme!r}")

    req = Request(url, headers={"User-Agent": "eudr_dmi-dependencies-acquire/1.0"})
    with urlopen(req, timeout=30) as resp:
        body = resp.read()
        status = int(getattr(resp, "status", 0) or 0)
        headers: dict[str, str] = {}
        for k in ALLOWED_HEADERS:
            v = resp.headers.get(k)
            if v is not None and str(v).strip() != "":
                headers[k] = str(v).strip()

        if not body:
            raise RuntimeError(f"Refusing 0-byte download for {url} (http_status={status}).")

        return body, status, headers


def _write_headers_txt(path: Path, headers: dict[str, str]) -> None:
    if not headers:
        return
    lines = [f"{k}: {headers[k]}" for k in sorted(headers.keys())]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


@dataclass(frozen=True, slots=True)
class RunPaths:
    run_dir: Path

    @property
    def artifact_path(self) -> Path:
        return self.run_dir / "artifact.bin"

    @property
    def headers_path(self) -> Path:
        return self.run_dir / "headers.txt"

    @property
    def metadata_path(self) -> Path:
        return self.run_dir / "metadata.json"

    @property
    def manifest_path(self) -> Path:
        return self.run_dir / "manifest.sha256"


def _build_metadata(
    *,
    source_id: str,
    url: str,
    content_type_expected: str,
    notes: str,
    fetch_status: str,
    http_status: int | None,
    artifact_sha256: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": RUN_METADATA_SCHEMA_VERSION,
        "source_id": source_id,
        "url": url,
        "content_type_expected": content_type_expected,
        "fetch_status": fetch_status,
        "http_status": http_status,
        "artifact_sha256": artifact_sha256,
        "notes": notes,
    }


def write_run_manifest(run_dir: Path) -> Path:
    # Deterministic ordering by relative path.
    # Excludes manifest.sha256 (by implementation) and run_summary.json
    # (written by scripts wrapper).
    manifest_path = write_manifest_sha256(run_dir)
    # Filter out run_summary.json to keep verify stable and avoid self-referential hashes.
    lines = manifest_path.read_text(encoding="utf-8").splitlines()
    kept: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if "  " not in line:
            kept.append(raw)
            continue
        _digest, rel = line.split("  ", 1)
        if rel == "run_summary.json":
            continue
        kept.append(raw)
    manifest_path.write_text("\n".join(kept) + "\n" if kept else "", encoding="utf-8", newline="\n")
    return manifest_path


def verify_run_folder(run_dir: Path) -> None:
    paths = RunPaths(run_dir)

    if not run_dir.exists() or not run_dir.is_dir():
        raise FileNotFoundError(f"run folder not found: {run_dir}")

    for required in (paths.artifact_path, paths.metadata_path, paths.manifest_path):
        if not required.exists() or not required.is_file():
            raise FileNotFoundError(f"missing required file: {required}")

    metadata = _read_json(paths.metadata_path)
    artifact_sha = sha256_file(paths.artifact_path)
    if metadata.get("artifact_sha256") != artifact_sha:
        raise ValueError("metadata.json artifact_sha256 does not match artifact.bin")

    # Verify manifest content matches current hashes.
    expected_entries: dict[str, str] = {}
    for child in run_dir.rglob("*"):
        if not child.is_file():
            continue
        rel = child.relative_to(run_dir).as_posix()
        if rel in {"manifest.sha256", "run_summary.json"}:
            continue
        expected_entries[rel] = sha256_file(child)

    manifest_text = paths.manifest_path.read_text(encoding="utf-8")
    manifest_entries: dict[str, str] = {}
    for raw in manifest_text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if "  " not in line:
            raise ValueError("manifest.sha256 contains a malformed line")
        digest, rel = line.split("  ", 1)
        manifest_entries[rel] = digest

    # Must match exactly (same file set and digests).
    if manifest_entries != expected_entries:
        raise ValueError("manifest.sha256 does not match current folder contents")

    # Must be sorted by relative path (determinism gate).
    rels = list(manifest_entries.keys())
    if rels != sorted(rels):
        raise ValueError("manifest.sha256 is not sorted by relative path")


def run_for_source(
    *,
    source: dict[str, Any],
    run_date: str,
    out_root: Path | None,
    verify_only: bool,
) -> tuple[bool, str]:
    source_id = str(source["id"]).strip()
    url = str(source["url"]).strip()
    content_type_expected = str(source["content_type_expected"]).strip()
    notes = str(source.get("notes") or "").strip()
    server_local_path = str(source["server_local_path"]).strip()

    run_dir = _run_dir_for_source(
        source_id=source_id,
        server_local_path=server_local_path,
        run_date=run_date,
        out_root=out_root,
    )
    paths = RunPaths(run_dir)

    if verify_only:
        verify_run_folder(run_dir)
        return True, f"VERIFY OK: {source_id} -> {run_dir}"

    run_dir.mkdir(parents=True, exist_ok=True)

    fetch_status = "failed"
    http_status: int | None = None
    artifact_sha: str | None = None
    headers: dict[str, str] = {}

    try:
        body, http_status, headers = _fetch_bytes_and_headers(url)
        paths.artifact_path.write_bytes(body)
        artifact_sha = sha256_file(paths.artifact_path)
        _write_headers_txt(paths.headers_path, headers)
        fetch_status = "ok"
    except Exception as exc:
        # Still write deterministic metadata on failure (no timestamps).
        fetch_status = "failed"
        http_status = http_status if isinstance(http_status, int) else None
        artifact_sha = sha256_file(paths.artifact_path) if paths.artifact_path.exists() else None
        metadata = _build_metadata(
            source_id=source_id,
            url=url,
            content_type_expected=content_type_expected,
            notes=notes,
            fetch_status=fetch_status,
            http_status=http_status,
            artifact_sha256=artifact_sha,
        )
        _write_json(paths.metadata_path, metadata)
        write_run_manifest(run_dir)
        return False, f"FETCH FAILED: {source_id} error_type={exc.__class__.__name__} error={exc}"

    metadata = _build_metadata(
        source_id=source_id,
        url=url,
        content_type_expected=content_type_expected,
        notes=notes,
        fetch_status=fetch_status,
        http_status=http_status,
        artifact_sha256=artifact_sha,
    )
    _write_json(paths.metadata_path, metadata)
    write_run_manifest(run_dir)

    http_status_str = "" if http_status is None else str(http_status)
    sha_prefix = "" if not artifact_sha else artifact_sha[:12] + "…"
    return True, f"FETCH OK: {source_id} http_status={http_status_str} sha256={sha_prefix}"


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python tools/dependencies/acquire_and_hash.py",
        description=(
            "Deterministic dependency-definition fetch/verify tool. "
            "Writes per-source run folders under <server_local_path>/<YYYY-MM-DD>/ with "
            "artifact.bin + metadata.json + manifest.sha256."
        ),
    )

    p.add_argument(
        "--sources",
        default=str(DEFAULT_SOURCES),
        help="Sources registry JSON (default: docs/dependencies/sources.json)",
    )
    p.add_argument(
        "--id",
        default=None,
        help="Optional source id (if omitted, process all sources)",
    )
    p.add_argument(
        "--date",
        default=None,
        help="Run date YYYY-MM-DD (default: today in UTC)",
    )
    p.add_argument(
        "--out-root",
        default=None,
        help=(
            "Optional output root. If set, per-source runs are written under "
            "<out_root>/<source_id>/<YYYY-MM-DD>/. "
            "If omitted, each source's server_local_path is used as the base."
        ),
    )

    mode = p.add_mutually_exclusive_group(required=False)
    mode.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing run folder (no fetch)",
    )
    mode.add_argument(
        "--fetch",
        action="store_true",
        help="Fetch + write deterministic run folder (default)",
    )

    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    sources_path = Path(args.sources)
    if not sources_path.exists():
        print(f"ERROR: sources file not found: {sources_path}", file=sys.stderr)
        return 2

    run_date = str(args.date).strip() if args.date else _utc_today_date()

    out_root: Path | None
    if args.out_root:
        out_root = Path(str(args.out_root))
    else:
        out_root = None

    verify_only = bool(args.verify)
    if not args.verify and not args.fetch:
        # Default mode is fetch.
        verify_only = False

    registry = _read_json(sources_path)
    _validate_sources_registry_minimal(registry)
    sources = _iter_sources(registry=registry, only_id=args.id)

    failures: list[str] = []
    status_lines: list[str] = []

    for src in sources:
        try:
            ok, msg = run_for_source(
                source=src,
                run_date=run_date,
                out_root=out_root,
                verify_only=verify_only,
            )
            status_lines.append(msg)
            if not ok:
                failures.append(msg)
        except Exception as exc:
            msg = f"ERROR: id={src.get('id')} error_type={exc.__class__.__name__} error={exc}"
            status_lines.append(msg)
            failures.append(msg)

    for line in status_lines:
        print(line)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
