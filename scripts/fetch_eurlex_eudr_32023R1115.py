from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from eudr_dmi.evidence.hash_utils import sha256_file, write_manifest_sha256

CELEX = "32023R1115"
CANONICAL_NAME = "eudr_2023_1115"

URL_SUMMARY = (
    "https://eur-lex.europa.eu/EN/legal-content/summary/"
    "fighting-deforestation-and-forest-degradation.html"
)
URL_LSU_ENTRY = "https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32023R1115"
URL_PDF = "https://eur-lex.europa.eu/legal-content/EN/TXT/PDF/?uri=CELEX:32023R1115"
URL_HTML = "https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32023R1115"
URL_ELI_OJ = "https://eur-lex.europa.eu/eli/reg/2023/1115/oj/eng"

USER_AGENT = "eudr_dmi-eurlex-mirror/0.1 (macOS; audit-safe; contact: operator)"
DEFAULT_TIMEOUT_SECONDS = 20


LAST_UPDATE_RE = re.compile(
    r"\blast\s+update\b[^0-9]{0,40}(?P<date>\d{1,2}\.\d{1,2}\.\d{4})",
    flags=re.IGNORECASE,
)

LSU_UPDATED_ON_RE = re.compile(
    r"\b(updated\s+on|last\s+update)\b[^0-9]{0,40}(?P<date>\d{1,2}\.\d{1,2}\.\d{4})",
    flags=re.IGNORECASE,
)

DATE_DIR_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class FetchResult:
    name: str
    url: str
    http_status: int | None
    content_type: str | None
    content_length: int | None
    etag: str | None
    last_modified: str | None
    stored_path: Path | None
    sha256: str | None
    error: str | None


def resolve_run_date(arg_date: str | None) -> str:
    if arg_date:
        return arg_date  # must already be YYYY-MM-DD
    return date.today().isoformat()


def _git_sha(repo_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_root),
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


def extract_summary_last_update(html_text: str) -> str | None:
    match = LAST_UPDATE_RE.search(html_text)
    if not match:
        return None
    return match.group("date")


def extract_lsu_updated_on(html_text: str) -> str | None:
    match = LSU_UPDATED_ON_RE.search(html_text)
    if not match:
        return None
    return match.group("date")


def _iter_date_run_dirs(out_base: Path) -> list[str]:
    if not out_base.exists():
        return []
    dates: list[str] = []
    for child in out_base.iterdir():
        if child.is_dir() and DATE_DIR_RE.match(child.name):
            dates.append(child.name)
    return sorted(dates)


def _latest_prior_run_date(out_base: Path, run_date: str) -> str | None:
    dates = _iter_date_run_dirs(out_base)
    priors = [d for d in dates if d < run_date]
    if not priors:
        return None
    return priors[-1]


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _headers_fingerprint(result: FetchResult) -> dict[str, Any]:
    return {
        "etag": result.etag,
        "last_modified": result.last_modified,
        "content_length": result.content_length,
        "content_type": result.content_type,
        "http_status": result.http_status,
        "error": result.error,
    }


def _best_fallback_fingerprint(results: list[FetchResult]) -> dict[str, Any]:
    by_name = {r.name: r for r in results}
    pdf = by_name.get("pdf")
    html = by_name.get("html")
    eli = by_name.get("eli_oj")

    return {
        "pdf": None
        if pdf is None or pdf.error is not None or pdf.sha256 is None
        else {"sha256": pdf.sha256, **_headers_fingerprint(pdf)},
        "html": None
        if html is None or html.error is not None or html.sha256 is None
        else {"sha256": html.sha256, **_headers_fingerprint(html)},
        "eli_oj": None if eli is None else {"sha256": eli.sha256, **_headers_fingerprint(eli)},
    }


def _entrypoint_status(
    *,
    entrypoint_url: str,
    lsu_result: FetchResult,
    run_dir: Path,
    results: list[FetchResult],
) -> dict[str, Any]:
    reachable = lsu_result.error is None and lsu_result.http_status == 200

    evidence: dict[str, Any] = {}
    if reachable:
        stored = run_dir / "lsu_entry.html"
        lsu_sha256 = sha256_file(stored) if stored.exists() else None
        lsu_updated_on: str | None = None
        if stored.exists():
            lsu_updated_on = extract_lsu_updated_on(
                stored.read_text(encoding="utf-8", errors="replace")
            )
        evidence = {
            "lsu_entry_sha256": lsu_sha256,
            "lsu_updated_on": lsu_updated_on,
        }
    else:
        evidence = {
            "fallback": _best_fallback_fingerprint(results),
        }

    return {
        "entrypoint_url": entrypoint_url,
        "attempted": True,
        "http_status": lsu_result.http_status,
        "reachable": reachable,
        "error": lsu_result.error,
        "evidence": evidence,
    }


def _compute_needs_update(
    *,
    out_base: Path,
    run_date: str,
    entrypoint_status: dict[str, Any],
    extracted_fields: dict[str, Any],
) -> tuple[bool, list[str], str | None]:
    prev_date = _latest_prior_run_date(out_base, run_date)
    if prev_date is None:
        return True, ["no_previous_run"], None

    prev_dir = out_base / prev_date
    prev_entry = _read_json(prev_dir / "entrypoint_status.json")
    prev_meta = _read_json(prev_dir / "metadata.json")

    reasons: list[str] = []

    cur_reachable = bool(entrypoint_status.get("reachable"))
    prev_reachable = bool(prev_entry.get("reachable")) if isinstance(prev_entry, dict) else False

    if cur_reachable and isinstance(prev_entry, dict) and prev_reachable:
        cur_e = entrypoint_status.get("evidence") or {}
        prev_e = prev_entry.get("evidence") or {}
        if cur_e.get("lsu_entry_sha256") != prev_e.get("lsu_entry_sha256"):
            reasons.append("lsu_sha256_changed")
        if cur_e.get("lsu_updated_on") != prev_e.get("lsu_updated_on"):
            reasons.append("lsu_updated_on_changed")
    else:
        cur_fb = (entrypoint_status.get("evidence") or {}).get("fallback")
        prev_fb = (
            (prev_entry.get("evidence") or {}).get("fallback")
            if isinstance(prev_entry, dict)
            else None
        )

        def _get(dct: Any, *path: str) -> Any:
            cur: Any = dct
            for key in path:
                if not isinstance(cur, dict):
                    return None
                cur = cur.get(key)
            return cur

        if _get(cur_fb, "pdf", "sha256") != _get(prev_fb, "pdf", "sha256"):
            reasons.append("lsu_unreachable_but_pdf_sha256_changed")
        if _get(cur_fb, "html", "sha256") != _get(prev_fb, "html", "sha256"):
            reasons.append("lsu_unreachable_but_html_sha256_changed")
        if _get(cur_fb, "eli_oj", "sha256") != _get(prev_fb, "eli_oj", "sha256"):
            reasons.append("lsu_unreachable_but_eli_oj_sha256_changed")

        if _get(cur_fb, "pdf", "etag") != _get(prev_fb, "pdf", "etag"):
            reasons.append("lsu_unreachable_but_pdf_etag_changed")
        if _get(cur_fb, "pdf", "last_modified") != _get(prev_fb, "pdf", "last_modified"):
            reasons.append("lsu_unreachable_but_pdf_last_modified_changed")

    prev_summary_last_update = None
    if isinstance(prev_meta, dict):
        prev_summary_last_update = (prev_meta.get("extracted_fields") or {}).get(
            "summary_last_update"
        )
    if extracted_fields.get("summary_last_update") != prev_summary_last_update:
        reasons.append("summary_last_update_changed")

    content_gate_failures = extracted_fields.get("content_gate_failures")
    if isinstance(content_gate_failures, list):
        for item in content_gate_failures:
            if isinstance(item, str) and item:
                reasons.append(item)

    needs_update = len(reasons) > 0
    return needs_update, sorted(set(reasons)), prev_date


def _fetch(url: str) -> tuple[int | None, dict[str, str], bytes | None, str | None]:
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=DEFAULT_TIMEOUT_SECONDS) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            headers = {k.lower(): v for k, v in resp.headers.items()}
            body = resp.read()
            if status == 202 and headers.get("x-amzn-waf-action") == "challenge":
                return status, headers, None, "waf_challenge"
            if status != 200:
                return status, headers, None, f"http_{status}"
            if not body:
                return status, headers, None, "empty_body"
            return status, headers, body, None
    except HTTPError as e:
        headers = {k.lower(): v for k, v in e.headers.items()} if e.headers else {}
        return e.code, headers, None, f"http_error_{e.code}"
    except URLError as e:
        return None, {}, None, f"url_error_{e.reason}"
    except Exception as e:
        return None, {}, None, f"error_{type(e).__name__}: {e}"


def _write_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(content)
    tmp.replace(path)


def _result_from_fetch(
    *,
    name: str,
    url: str,
    out_path: Path,
    expected_content_type: str | None,
) -> FetchResult:
    status, headers, body, error = _fetch(url)

    content_type = headers.get("content-type")
    etag = headers.get("etag")
    last_modified = headers.get("last-modified")

    if body is None:
        return FetchResult(
            name=name,
            url=url,
            http_status=status,
            content_type=content_type,
            content_length=None,
            etag=etag,
            last_modified=last_modified,
            stored_path=None,
            sha256=None,
            error=error,
        )

    if name == "pdf":
        if not body.startswith(b"%PDF-"):
            if out_path.exists():
                try:
                    out_path.unlink()
                except Exception:
                    pass
            return FetchResult(
                name=name,
                url=url,
                http_status=status,
                content_type=content_type,
                content_length=len(body),
                etag=etag,
                last_modified=last_modified,
                stored_path=None,
                sha256=None,
                error="unexpected_signature",
            )

    if name == "html":
        marker = f"CELEX:{CELEX}".encode()
        if marker not in body:
            if out_path.exists():
                try:
                    out_path.unlink()
                except Exception:
                    pass
            return FetchResult(
                name=name,
                url=url,
                http_status=status,
                content_type=content_type,
                content_length=len(body),
                etag=etag,
                last_modified=last_modified,
                stored_path=None,
                sha256=None,
                error="unexpected_content_type",
            )

    _write_bytes(out_path, body)
    digest = sha256_file(out_path)

    return FetchResult(
        name=name,
        url=url,
        http_status=status,
        content_type=content_type or expected_content_type,
        content_length=len(body),
        etag=etag,
        last_modified=last_modified,
        stored_path=out_path,
        sha256=digest,
        error=None,
    )


def _stable_fingerprint(metadata: dict[str, Any]) -> str:
    stable = dict(metadata)
    stable.pop("run", None)
    encoded = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return hashlib.sha256(encoded).hexdigest()


def _load_existing_metadata(run_dir: Path) -> dict[str, Any] | None:
    path = run_dir / "metadata.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_fetch_log(run_dir: Path, results: list[FetchResult]) -> None:
    failures = [r for r in results if r.error]
    if not failures:
        return

    lines = ["fetch_status=partial"]
    for r in sorted(failures, key=lambda x: x.name):
        status = "none" if r.http_status is None else str(r.http_status)
        lines.append(f"{r.name} status={status} error={r.error} url={r.url}")

    (run_dir / "fetch.log").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def run_mirror(*, out_base: Path, run_date: str, repo_root: Path) -> Path:
    run_dir = out_base / run_date
    run_dir.mkdir(parents=True, exist_ok=True)

    started_at = datetime.now(UTC).isoformat()

    results: list[FetchResult] = []
    results.append(
        _result_from_fetch(
            name="summary",
            url=URL_SUMMARY,
            out_path=run_dir / "summary.html",
            expected_content_type="text/html",
        )
    )
    lsu_result = _result_from_fetch(
        name="lsu_entry",
        url=URL_LSU_ENTRY,
        out_path=run_dir / "lsu_entry.html",
        expected_content_type="text/html",
    )
    results.append(lsu_result)
    results.append(
        _result_from_fetch(
            name="pdf",
            url=URL_PDF,
            out_path=run_dir / "regulation.pdf",
            expected_content_type="application/pdf",
        )
    )

    html_result = _result_from_fetch(
        name="html",
        url=URL_HTML,
        out_path=run_dir / "regulation.html",
        expected_content_type="text/html",
    )
    if html_result.error is None:
        results.append(html_result)
    else:
        results.append(
            FetchResult(
                name=html_result.name,
                url=html_result.url,
                http_status=html_result.http_status,
                content_type=html_result.content_type,
                content_length=html_result.content_length,
                etag=html_result.etag,
                last_modified=html_result.last_modified,
                stored_path=None,
                sha256=None,
                error=html_result.error,
            )
        )

    eli_result = _result_from_fetch(
        name="eli_oj",
        url=URL_ELI_OJ,
        out_path=run_dir / "eli_oj.html",
        expected_content_type="text/html",
    )
    if eli_result.error is None:
        results.append(eli_result)
    else:
        results.append(
            FetchResult(
                name=eli_result.name,
                url=eli_result.url,
                http_status=eli_result.http_status,
                content_type=eli_result.content_type,
                content_length=eli_result.content_length,
                etag=eli_result.etag,
                last_modified=eli_result.last_modified,
                stored_path=None,
                sha256=None,
                error=eli_result.error,
            )
        )

    summary_last_update: str | None = None
    summary_path = run_dir / "summary.html"
    if summary_path.exists():
        summary_last_update = extract_summary_last_update(
            summary_path.read_text(encoding="utf-8", errors="replace")
        )

    content_gate_failures: list[str] = []
    for r in results:
        if r.name == "pdf" and r.error == "unexpected_signature":
            content_gate_failures.append("pdf_unexpected_signature")
        if r.name == "html" and r.error == "unexpected_content_type":
            content_gate_failures.append("html_unexpected_content_type")

    status = "complete" if all(r.error is None for r in results) else "partial"

    extracted_fields: dict[str, Any] = {
        "summary_last_update": summary_last_update,
        "content_gate_failures": sorted(content_gate_failures),
    }
    entrypoint_status = _entrypoint_status(
        entrypoint_url=URL_LSU_ENTRY,
        lsu_result=lsu_result,
        run_dir=run_dir,
        results=results,
    )
    _write_json(run_dir / "entrypoint_status.json", entrypoint_status)

    needs_update, reasons, prev_date = _compute_needs_update(
        out_base=out_base,
        run_date=run_date,
        entrypoint_status=entrypoint_status,
        extracted_fields=extracted_fields,
    )

    metadata: dict[str, Any] = {
        "celex": CELEX,
        "canonical_name": CANONICAL_NAME,
        "status": status,
        "needs_update": needs_update,
        "sources": [
            {
                "name": r.name,
                "url": r.url,
                "http_status": r.http_status,
                "content_type": r.content_type,
                "content_length": r.content_length,
                "etag": r.etag,
                "last_modified": r.last_modified,
                "sha256": r.sha256,
                "error": r.error,
            }
            for r in results
        ],
        "extracted_fields": extracted_fields,
    }

    if needs_update:
        trigger = {
            "reason": reasons,
            "previous_run": prev_date,
            "current_run": run_date,
        }
        _write_json(run_dir / "digital_twin_trigger.json", trigger)

    existing = _load_existing_metadata(run_dir)

    finished_at = datetime.now(UTC).isoformat()
    run_info = {
        "run_date": run_date,
        "started_at_utc": started_at,
        "finished_at_utc": finished_at,
        "git_sha": _git_sha(repo_root),
    }

    if existing is not None:
        try:
            existing_fp = _stable_fingerprint(existing)
            new_fp = _stable_fingerprint(metadata)
            if existing_fp == new_fp and "run" in existing:
                run_info["started_at_utc"] = existing["run"].get("started_at_utc", started_at)
                run_info["finished_at_utc"] = existing["run"].get("finished_at_utc", finished_at)
        except Exception:
            pass

    metadata["run"] = run_info

    _write_json(run_dir / "metadata.json", metadata)

    _write_fetch_log(run_dir, results)

    # Include metadata + stored files + optional fetch.log (if created); exclude manifest itself.
    write_manifest_sha256(run_dir, exclude={"manifest.sha256"})

    return run_dir


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/fetch_eurlex_eudr_32023R1115.py",
        description="Deterministic EUR-Lex mirror for CELEX:32023R1115 (EUDR).",
    )
    parser.add_argument(
        "--out",
        required=True,
        help="Output base directory (run folder will be <out>/<YYYY-MM-DD>/)",
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Run date YYYY-MM-DD (default: today local timezone)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    run_date = resolve_run_date(args.date)
    out_base = Path(args.out)

    run_dir = out_base / run_date
    assert DATE_DIR_RE.match(run_dir.name), f"run_dir name must be YYYY-MM-DD, got: {run_dir.name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    repo_root = Path(__file__).resolve().parents[1]
    run_dir = run_mirror(out_base=out_base, run_date=run_date, repo_root=repo_root)

    print(str(run_dir))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
