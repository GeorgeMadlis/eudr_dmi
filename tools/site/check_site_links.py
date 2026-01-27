#!/usr/bin/env python3
"""Portable link checker for a static site bundle.

Inputs:
- --root: site root folder (e.g. docs/site_bundle)
- --out: output JSON report path

Scans **/*.html and extracts href/src links.

Rules:
- Ignore: http://, https://, mailto:, tel:, and #fragment-only links.
- Disallow (FAIL): links starting with / or file://.
- For other relative links: resolve against the current page directory and assert
    the target exists within the root.

Output JSON:
    {"status":"PASS|FAIL","broken":[...],"disallowed":[...],"scanned_files":N}
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

_IGNORE_PREFIXES = ("http://", "https://", "mailto:", "tel:")


@dataclass(frozen=True)
class LinkRef:
    source_file: str
    attr: str
    url: str


class _LinkExtractor(HTMLParser):
    def __init__(self, *, source_file_rel: str) -> None:
        super().__init__(convert_charrefs=True)
        self._source_file_rel = source_file_rel
        self.links: list[LinkRef] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        for k, v in attrs:
            if v is None:
                continue
            if k in {"href", "src"}:
                self.links.append(LinkRef(self._source_file_rel, k, v))


def _is_ignored(url: str) -> bool:
    u = url.strip()
    if not u:
        return True
    if u.startswith("#"):
        return True
    u_lower = u.lower()
    return any(u_lower.startswith(p) for p in _IGNORE_PREFIXES)


def _is_disallowed(url: str) -> bool:
    u = url.strip()
    if not u:
        return False
    if u.startswith("/"):
        return True
    if u.lower().startswith("file://"):
        return True
    return False


def _strip_fragment_and_query(url: str) -> str:
    # Keep it simple and deterministic.
    u = url
    if "#" in u:
        u = u.split("#", 1)[0]
    if "?" in u:
        u = u.split("?", 1)[0]
    return u


def _walk_html(root: Path) -> list[Path]:
    return sorted([p for p in root.rglob("*.html") if p.is_file()])


def check_links(*, root: Path) -> dict[str, Any]:
    root = root.resolve()

    broken: list[dict[str, Any]] = []
    disallowed: list[dict[str, Any]] = []

    html_files = _walk_html(root)
    for html_path in html_files:
        rel = html_path.relative_to(root).as_posix()
        text = html_path.read_text(encoding="utf-8", errors="replace")
        parser = _LinkExtractor(source_file_rel=rel)
        parser.feed(text)

        for link in parser.links:
            url = link.url.strip()
            if not url:
                continue

            if _is_ignored(url):
                continue

            if _is_disallowed(url):
                disallowed.append({"source": link.source_file, "attr": link.attr, "url": url})
                continue

            target = _strip_fragment_and_query(url)
            if not target:
                continue

            # Resolve relative to the current HTML file.
            candidate = (html_path.parent / target).resolve()

            # Must remain within root.
            try:
                candidate.relative_to(root)
            except ValueError:
                broken.append(
                    {
                        "source": link.source_file,
                        "attr": link.attr,
                        "url": url,
                        "resolved": candidate.as_posix(),
                    }
                )
                continue

            if not candidate.exists():
                broken.append(
                    {
                        "source": link.source_file,
                        "attr": link.attr,
                        "url": url,
                        "resolved": candidate.relative_to(root).as_posix(),
                    }
                )

    broken.sort(key=lambda d: (d["source"], d["attr"], d["url"]))
    disallowed.sort(key=lambda d: (d["source"], d["attr"], d["url"]))

    status = "PASS" if (not broken and not disallowed) else "FAIL"
    return {
        "status": status,
        "broken": broken,
        "disallowed": disallowed,
        "scanned_files": len(html_files),
    }


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Check relative links inside a site root")
    ap.add_argument("--root", type=Path, required=True, help="Site root folder")
    ap.add_argument("--out", type=Path, required=True, help="Output JSON file")
    args = ap.parse_args(argv)

    report = check_links(root=args.root)
    _write_text(args.out, json.dumps(report, indent=2, sort_keys=True) + "\n")

    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
