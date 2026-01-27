#!/usr/bin/env python3
"""Render a bundle-friendly AOI reports index.

Reads bundled AOI runs under:
  <bundle_root>/aoi_reports/runs/<run_id>/report.html

Writes:
  <bundle_root>/site/aoi_reports/index.html

This is intentionally simple and deterministic.
"""

from __future__ import annotations

import argparse
import html
from pathlib import Path


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def _list_runs(runs_root: Path) -> list[str]:
    if not runs_root.exists():
        return []
    runs = []
    for p in runs_root.iterdir():
        if not p.is_dir():
            continue
        if (p / "report.html").is_file():
            runs.append(p.name)
    return sorted(runs, reverse=True)


def render_index(*, bundle_root: Path) -> None:
    bundle_root = bundle_root.resolve()
    runs_root = bundle_root / "aoi_reports" / "runs"
    out_path = bundle_root / "site" / "aoi_reports" / "index.html"

    run_ids = _list_runs(runs_root)

    items: list[str] = []
    if run_ids:
        for run_id in run_ids:
            run_dir = runs_root / run_id
            report_rel = Path("../../aoi_reports/runs") / run_id / "report.html"
            summary_rel = Path("../../aoi_reports/runs") / run_id / "summary.json"

            line = f'<li><a href="{html.escape(report_rel.as_posix())}">{html.escape(run_id)}</a>'
            if (run_dir / "summary.json").is_file():
                line += (
                    f' <span class="muted">(</span><a href="{html.escape(summary_rel.as_posix())}">'  # noqa: E501
                    'summary.json</a><span class="muted">)</span>'
                )
            line += "</li>"
            items.append(line)
    else:
        items.append('<li class="muted">(no bundled AOI runs found)</li>')

    body = "\n".join(
        [
            "<h1>AOI Reports</h1>",
            '<p class="muted">Bundled AOI report runs (newest first).</p>',
            '<div class="card">',
            "  <h2>Runs</h2>",
            "  <ul>",
            "\n".join(items),
            "  </ul>",
            "</div>",
        ]
    )

    page = "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "  <head>",
            "    <meta charset=\"utf-8\" />",
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
            "    <title>AOI Reports</title>",
            "    <style>",
            "      :root { --fg:#111; --bg:#fff; --muted:#666; --card:#f6f7f9; --link:#0b5fff; }",
            (
                "      body { font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, "
                "Roboto, Helvetica, Arial, sans-serif; color: var(--fg); background: var(--bg); "
                "margin: 0; }"
            ),
            (
                "      header { border-bottom: 1px solid #e7e7e7; background: #fff; position: "
                "sticky; top: 0; }"
            ),
            "      .wrap { max-width: 980px; margin: 0 auto; padding: 16px 20px; }",
            (
                "      nav a { margin-right: 14px; text-decoration: none; color: var(--link); "
                "font-weight: 600; }"
            ),
            "      nav a.active { color: var(--fg); }",
            "      main { padding: 18px 20px 40px; }",
            "      h1 { margin: 0 0 6px; font-size: 22px; }",
            "      h2 { margin-top: 24px; font-size: 18px; }",
            "      p { line-height: 1.5; }",
            "      .muted { color: var(--muted); }",
            (
                "      .card { background: var(--card); border: 1px solid #e8eaee; "
                "border-radius: 12px; padding: 14px 14px; }"
            ),
            "      ul { padding-left: 18px; }",
            "      code { background: #f1f1f1; padding: 1px 4px; border-radius: 6px; }",
            "    </style>",
            "  </head>",
            "  <body>",
            "    <header>",
            "      <div class=\"wrap\">",
            "        <nav>",
            '          <a href="../index.html">Home</a>',
            '          <a href="../articles/index.html">Articles</a>',
            '          <a href="../dependencies/index.html">Dependencies</a>',
            '          <a href="../../regulation/links.html">Regulation</a>',
            '          <a href="../../regulation/policy_to_evidence_spine.md">Spine</a>',
            '          <a href="index.html" class="active">AOI Reports</a>',
            "        </nav>",
            "      </div>",
            "    </header>",
            "    <main>",
            "      <div class=\"wrap\">",
            body,
            "      </div>",
            "    </main>",
            "  </body>",
            "</html>",
        ]
    )

    _write_text(out_path, page)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Render AOI runs index inside a site bundle")
    ap.add_argument("--bundle-root", type=Path, required=True)
    args = ap.parse_args(argv)

    render_index(bundle_root=args.bundle_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
