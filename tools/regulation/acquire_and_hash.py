from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_JSON = REPO_ROOT / "docs" / "regulation" / "sources.json"
REGISTRY_MD = REPO_ROOT / "docs" / "regulation" / "sources.md"

SERVER_AUDIT_ROOT = Path("/Users/server/audit/eudr_dmi")
SERVER_REG_EUDR_DIR = SERVER_AUDIT_ROOT / "regulation" / "eudr_2023_1115"
SERVER_REG_GUIDANCE_DIR = SERVER_AUDIT_ROOT / "regulation" / "guidance"


def _load_registry() -> dict:
    data = json.loads(REGISTRY_JSON.read_text(encoding="utf-8"))
    if "sources" not in data or not isinstance(data["sources"], list):
        raise ValueError("Invalid registry schema: expected top-level 'sources' array")
    return data


def _write_registry(data: dict) -> None:
    REGISTRY_JSON.write_text(
        json.dumps(data, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _ensure_server_dirs() -> None:
    SERVER_REG_EUDR_DIR.mkdir(parents=True, exist_ok=True)
    SERVER_REG_GUIDANCE_DIR.mkdir(parents=True, exist_ok=True)


def _curl_fetch(url: str, out_path: Path, cookie_jar: Path | None) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        header_path = Path(td) / "headers.txt"
        tmp_out = Path(td) / (out_path.name + ".download")

        cmd = [
            "curl",
            "-L",
            "--fail",
            "--show-error",
            "-S",
            "-A",
            "Mozilla/5.0",
            "--dump-header",
            str(header_path),
            "-o",
            str(tmp_out),
            "-w",
            "%{http_code}",
            url,
        ]
        if cookie_jar is not None:
            cmd.insert(1, "-b")
            cmd.insert(2, str(cookie_jar))

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"curl failed for {url}: {result.stderr.strip()}")

        http_code = (result.stdout or "").strip()
        size = tmp_out.stat().st_size if tmp_out.exists() else 0
        headers = header_path.read_text(encoding="utf-8", errors="replace")

        if size == 0:
            raise RuntimeError(f"Refusing 0-byte download for {url} (http={http_code}).")

        # WAF challenge often returns 202 with x-amzn-waf-action: challenge.
        if http_code == "202" and "x-amzn-waf-action:" in headers.lower():
            raise RuntimeError(
                f"WAF challenge detected for {url} (http=202). "
                "Use interactive browser access and/or operator-provided cookies; "
                "no bypass attempted."
            )

        tmp_out.replace(out_path)


def _update_markdown_table(md_text: str, sha_by_local_path: dict[str, str]) -> str:
    lines = md_text.splitlines()
    out: list[str] = []

    in_table = False
    for line in lines:
        if line.strip() == "| Source | URL | Local Path (server) | SHA256 | Notes |":
            in_table = True
            out.append(line)
            continue

        if in_table:
            if not line.strip().startswith("|") or line.strip() == "":
                in_table = False
                out.append(line)
                continue

            # Header separator row
            if line.strip().startswith("|---"):
                out.append(line)
                continue

            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                out.append(line)
                continue

            # parts: ["", Source, URL, Local Path, SHA256, Notes, ""]
            local_path_cell = parts[3]
            normalized_local_path = local_path_cell.strip("`")
            sha = sha_by_local_path.get(normalized_local_path)
            if sha:
                parts[4] = sha
            # Rebuild
            rebuilt = "| " + " | ".join(parts[1:-1]) + " |"
            out.append(rebuilt)
            continue

        out.append(line)

    return "\n".join(out) + ("\n" if md_text.endswith("\n") else "")


def _write_sha256sums_eudr_dir(sha_by_path: dict[Path, str]) -> Path:
    entries: list[tuple[str, str]] = []
    for p, digest in sha_by_path.items():
        try:
            relative = p.relative_to(SERVER_REG_EUDR_DIR)
        except ValueError:
            continue
        entries.append((str(relative), digest))

    entries.sort(key=lambda t: t[0])

    sums_path = SERVER_REG_EUDR_DIR / "SHA256SUMS.txt"
    with sums_path.open("w", encoding="utf-8", newline="\n") as f:
        for rel, digest in entries:
            f.write(f"{digest}  {rel}\n")

    return sums_path


def verify_and_update_registry(*, fetch: bool, cookie_jar: Path | None) -> int:
    _ensure_server_dirs()

    data = _load_registry()
    sources = data["sources"]

    sha_by_path: dict[Path, str] = {}
    sha_by_local_path_str: dict[str, str] = {}

    failures: list[str] = []
    status_lines: list[str] = []

    for source in sources:
        url = str(source.get("url"))
        local_path = Path(str(source.get("server_local_path")))

        if fetch:
            try:
                _curl_fetch(url, local_path, cookie_jar)
                status_lines.append(f"FETCHED: {source.get('id')} -> {local_path}")
            except Exception as e:
                failures.append(f"FETCH FAILED: {source.get('id')}: {e}")

        if local_path.exists() and local_path.is_file() and local_path.stat().st_size > 0:
            digest = sha256_file(local_path)
            source["sha256"] = digest
            sha_by_path[local_path] = digest
            sha_by_local_path_str[str(local_path)] = digest
            status_lines.append(f"OK: {source.get('id')} sha256={digest[:12]}…")
        else:
            source["sha256"] = source.get("sha256") if source.get("sha256") else None
            status_lines.append(f"MISSING/EMPTY: {source.get('id')} -> {local_path}")

    if failures:
        for line in failures:
            print(line)

    # Always write JSON deterministically (only sha256 fields change).
    _write_registry(data)

    # Update Markdown table SHA256 column.
    md_text = REGISTRY_MD.read_text(encoding="utf-8")
    updated_md = _update_markdown_table(md_text, sha_by_local_path_str)
    REGISTRY_MD.write_text(updated_md, encoding="utf-8", newline="\n")

    # Write SHA256SUMS for the EUDR directory if we have any hashes.
    if sha_by_path:
        sums_path = _write_sha256sums_eudr_dir(sha_by_path)
        print(f"WROTE: {sums_path}")

    for line in status_lines:
        print(line)

    return 1 if failures else 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python tools/regulation/acquire_and_hash.py",
        description=(
            "WAF-safe regulation acquisition verifier. "
            "Default is verify-only; fetch is optional and cookie-jar is operator-supplied."
        ),
    )

    mode = parser.add_mutually_exclusive_group(required=False)
    mode.add_argument("--verify", action="store_true", help="Verify + hash local server files")
    mode.add_argument("--fetch", action="store_true", help="Attempt fetch via curl (no bypass)")

    parser.add_argument(
        "--cookie-jar",
        type=str,
        default=None,
        help=(
            "Optional curl cookie jar path (operator-managed), e.g. "
            "/Users/server/secrets/eudr_dmi/eurlex_cookies.txt"
        ),
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    fetch = bool(args.fetch)

    cookie_jar = Path(args.cookie_jar) if args.cookie_jar else None
    if cookie_jar is not None:
        if not cookie_jar.exists():
            return 2
        # Do not attempt to enforce permissions, but warn if obviously too open.
        try:
            mode = os.stat(cookie_jar).st_mode & 0o777
            if mode != 0o600:
                print(
                    f"WARNING: cookie jar permissions are {oct(mode)}; expected 0o600.",
                    file=sys.stderr,
                )
        except Exception:
            pass

    # Default mode is verify-only.
    if not args.verify and not args.fetch:
        args.verify = True

    return verify_and_update_registry(fetch=fetch, cookie_jar=cookie_jar)


if __name__ == "__main__":
    raise SystemExit(main())
