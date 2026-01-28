#!/usr/bin/env python3
"""Build a minimal, deterministic HTML docs site.

No JS frameworks, no timestamps, stable ordering, and LF newlines.

Outputs (default paths can be overridden via CLI args):
- docs/html/index.html
- docs/html/articles/index.html
- docs/html/articles/article_09.html, article_10.html, article_11.html

This is intentionally lightweight and only supports the formatting patterns
used in docs/articles/eudr_article_summaries.md.
"""

from __future__ import annotations

import argparse
import html
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote


@dataclass(frozen=True)
class ArticleSummary:
    article_id: str  # two-digit, e.g. "09"
    heading: str
    bullets: tuple[str, ...]


@dataclass(frozen=True)
class Dependency:
    id: str
    title: str
    url: str
    expected_content_type: str
    server_path: str
    used_by: tuple[str, ...]
    purpose: str | None = None


_REQUIRED_ARTICLES: tuple[str, ...] = ("09", "10", "11")


def _repo_root_from_this_file() -> Path:
    # tools/site/build_docs_site.py -> repo root is ../../..
    return Path(__file__).resolve().parents[2]


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    with path.open("w", encoding="utf-8", newline="\n") as f:
        f.write(content)


def _read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _html_page(*, title: str, nav_html: str, body_html: str) -> str:
    # Deterministic: no timestamps, stable ordering, fixed structure.
    return "\n".join(
        [
            "<!doctype html>",
            '<html lang="en">',
            "  <head>",
            "    <meta charset=\"utf-8\" />",
            "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />",
            f"    <title>{html.escape(title)}</title>",
            "    <style>",
            "      :root { --fg:#111; --bg:#fff; --muted:#666; --card:#f6f7f9; --link:#0b5fff; }",
            (
                "      body { font-family: ui-sans-serif, system-ui, -apple-system, "
                "Segoe UI, Roboto, Helvetica, Arial, sans-serif;"
            ),
            "             color: var(--fg); background: var(--bg); margin: 0; }",
            (
                "      header { border-bottom: 1px solid #e7e7e7; background: #fff; "
                "position: sticky; "
                "top: 0; }"
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
                "border-radius: 12px; "
                "padding: 14px 14px; }"
            ),
            "      ul { padding-left: 18px; }",
            "      code { background: #f1f1f1; padding: 1px 4px; border-radius: 6px; }",
            "      .grid { display: grid; grid-template-columns: 1fr; gap: 12px; }",
            "      @media (min-width: 760px) { .grid { grid-template-columns: 1fr 1fr; } }",
            "    </style>",
            "  </head>",
            "  <body>",
            "    <header>",
            "      <div class=\"wrap\">",
            "        <nav>",
            nav_html,
            "        </nav>",
            "      </div>",
            "    </header>",
            "    <main>",
            "      <div class=\"wrap\">",
            body_html,
            "      </div>",
            "    </main>",
            "  </body>",
            "</html>",
        ]
    )


def _nav(*, current: str, rel_prefix: str) -> str:
    # rel_prefix is the relative path from the current page to docs/html/.
    def link(label: str, href: str, key: str) -> str:
        cls = "active" if current == key else ""
        class_attr = f' class="{cls}"' if cls else ""
        return f'<a href="{href}"{class_attr}>{html.escape(label)}</a>'

    home = link("Home", f"{rel_prefix}index.html", "home")
    articles = link("Articles", f"{rel_prefix}articles/index.html", "articles")
    dependencies = link(
        "Dependencies",
        f"{rel_prefix}dependencies/index.html",
        "dependencies",
    )
    regulation = link("Regulation", f"{rel_prefix}../regulation/links.html", "regulation")
    spine = link("Spine", f"{rel_prefix}../regulation/policy_to_evidence_spine.md", "spine")
    aoi = link("AOI Reports", f"{rel_prefix}aoi_reports/index.html", "aoi")
    dao_stakeholders = link(
        "DAO (Stakeholders)",
        f"{rel_prefix}dao_stakeholders/index.html",
        "dao_stakeholders",
    )
    dao_dev = link(
        "DAO (Developers)",
        f"{rel_prefix}dao_dev/index.html",
        "dao_dev",
    )

    nav_items = [
        home,
        articles,
        dependencies,
        regulation,
        spine,
        aoi,
        dao_stakeholders,
        dao_dev,
    ]
    return "\n".join(
        ["          " + s for s in nav_items]
    )


def _render_dao_stakeholders_index() -> str:
    return "\n".join(
        [
            "<h1>DAO (Stakeholders)</h1>",
            (
                '<p class="muted">A stakeholder-facing view for proposing and reviewing changes '
                "to the audit documentation bundle and its inspection contracts."
                "</p>"
            ),
            '<div class="card">',
            "  <h2>Purpose</h2>",
            "  <ul>",
            "    <li>Provide a stable place for non-developers to propose changes.</li>",
            "    <li>Make Q/A and review possible from a portable, offline bundle.</li>",
            "    <li>Keep evidence and acceptance criteria explicit and auditable.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>How to use the bundle for Q/A</h2>",
            "  <ul>",
            "    <li>Download the bundle (or ZIP) and open <code>index.html</code>.</li>",
            (
                "    <li>Use your browser find/search to locate obligations, controls, and "
                "evidence.</li>"
            ),
            "    <li>When asking questions, reference concrete bundle paths (relative links).</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>Proposals</h2>",
            "  <ul>",
            "    <li><a href=\"proposals/index.html\">Browse proposals</a></li>",
            "    <li><a href=\"new_proposal.html\">Create a new proposal</a></li>",
            "    <li><a href=\"how_to_participate.html\">How to participate</a></li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>Agent prompt</h2>",
            (
                "  <p><a href=\"../../agent_prompts/dao_stakeholders_prompt.md\">Open "
                "stakeholders agent prompt</a></p>"
            ),
            "</div>",
            _render_related_views_card(current_view="dao_stakeholders"),
        ]
    )


def _render_dao_stakeholders_how_to_participate() -> str:
    return "\n".join(
        [
            "<h1>How to Participate (Stakeholders)</h1>",
            '<p class="muted">A minimal, deterministic process for proposing improvements.</p>',
            '<div class="card">',
            "  <h2>Steps</h2>",
            "  <ol>",
            (
                "    <li>Read the relevant pages in the bundle and note the exact paths you "
                "reference.</li>"
            ),
            "    <li>Create a proposal using the provided template.</li>",
            "    <li>State the acceptance criteria (what would prove the change is correct).</li>",
            "    <li>Submit the proposal as a pull request (or send it to the operator).</li>",
            "  </ol>",
            "</div>",
            '<div class="card">',
            "  <h2>Links</h2>",
            "  <ul>",
            "    <li><a href=\"new_proposal.html\">Create a new proposal</a></li>",
            "    <li><a href=\"proposals/index.html\">Browse proposals</a></li>",
            "    <li><a href=\"index.html\">Back to DAO (Stakeholders)</a></li>",
            "  </ul>",
            "</div>",
        ]
    )


def _read_repo_text(rel_path: str) -> str:
    path = _repo_root_from_this_file() / rel_path
    # Deterministic normalization: always embed with LF newlines.
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n").rstrip(
        "\n"
    )


def _render_related_views_card(*, current_view: str) -> str:
    # These links must remain valid inside docs/site_bundle/...
    # From site/<dao_view>/... to bundle root: ../../
    task_done_means = "../../views/task_view.md#task-to-artifact-map"
    agent_roles = "../../views/agentic_view.md#agent-roles"
    deterministic_run = "../../views/agentic_view.md#deterministic-run-contract-for-all-agents"
    invariants = "../../views/agentic_view.md#required-inspection-invariants"
    twin_triggers = "../../views/digital_twin_view.md#trigger-and-rerun-rules-high-level"

    other_dao_label, other_dao_href = (
        ("DAO (Developers)", "../dao_dev/index.html")
        if current_view == "dao_stakeholders"
        else ("DAO (Stakeholders)", "../dao_stakeholders/index.html")
    )

    return "\n".join(
        [
            '<div class="card">',
            "  <h2>Related Views</h2>",
            "  <ul>",
            f"    <li><a href=\"{other_dao_href}\">{html.escape(other_dao_label)}</a></li>",
            (
                f"    <li><a href=\"{task_done_means}\">Task view</a> — what “done” "
                "means</li>"
            ),
            (
                f"    <li><a href=\"{agent_roles}\">Agentic view</a> — roles, "
                f"<a href=\"{deterministic_run}\">deterministic run contract</a>, "
                f"<a href=\"{invariants}\">inspection invariants</a></li>"
            ),
            (
                f"    <li><a href=\"{twin_triggers}\">Digital twin view</a> — change "
                "triggers and rerun rules</li>"
            ),
            "  </ul>",
            "</div>",
        ]
    )


def _dao_new_proposal_block(*, view_id: str) -> str:
    if view_id == "dao_stakeholders":
        proposal_tmpl = _read_repo_text("docs/dao/templates/stakeholders/proposal.yaml")
        evidence_tmpl = _read_repo_text("docs/dao/templates/stakeholders/evidence_refs.yaml")
        audit_readme_block = ""
        tree = "\n".join(
            [
                "proposals/",
                "  SCP-YYYY-NNN-<slug>/",
                "    proposal.yaml",
                "    evidence_refs.yaml",
            ]
        )
        checklist_4 = "submit as an SCP package (outside of this repo)"
        focus = (
            "Focus: list the affected obligations/controls and state the expected impact "
            "on PASS/FAIL/UNDETERMINED."
        )
        qa = [
            "<li><strong>Q:</strong> What is the <code>scp_id</code>? <strong>A:</strong> "
            "Pick <code>SCP-YYYY-NNN-slug</code>.</li>",
            "<li><strong>Q:</strong> Who is the proposer? <strong>A:</strong> Fill "
            "<code>proposer</code>.</li>",
            "<li><strong>Q:</strong> Which obligations/controls are affected? "
            "<strong>A:</strong> Fill <code>affected_controls</code>.</li>",
            "<li><strong>Q:</strong> What is your claim? <strong>A:</strong> Fill "
            "<code>claim</code> with a single testable sentence.</li>",
            "<li><strong>Q:</strong> How does this change PASS/FAIL/UNDETERMINED? "
            "<strong>A:</strong> Fill <code>expected_impact</code>.</li>",
            "<li><strong>Q:</strong> What evidence supports this? <strong>A:</strong> Add "
            "items to <code>evidence_refs.yaml</code> using bundle paths when possible.</li>",
        ]
    else:
        proposal_tmpl = _read_repo_text("docs/dao/templates/dev/proposal.yaml")
        evidence_tmpl = _read_repo_text("docs/dao/templates/dev/evidence_refs.yaml")
        audit_readme = "\n".join(
            [
                "# Reproducible artifacts (SCP)",
                "",
                "SCP: SCP-YYYY-NNN-<slug>",
                "",
                "## Goal",
                "- Explain what change is being validated.",
                "",
                "## How to reproduce",
                "1) Run the relevant tests (ruff/pytest).",
                "2) Build the portable bundle.",
                "3) Verify link_check.json is PASS and manifest.sha256 updated.",
                "",
                "## Included artifacts",
                "- Diffs / patches (if applicable)",
                "- Logs / exports / screenshots (if applicable)",
                "- Notes that tie artifacts back to proposal.yaml claims",
            ]
        )
        audit_readme_block = "\n".join(
            [
                '<div class="card">',
                "  <h3>audit/proposals/&lt;SCP&gt;/README.md (developers)</h3>",
                f"  <pre><code>{html.escape(audit_readme)}</code></pre>",
                "</div>",
            ]
        )
        tree = "\n".join(
            [
                "proposals/",
                "  SCP-YYYY-NNN-<slug>/",
                "    proposal.yaml",
                "    evidence_refs.yaml",
                "audit/",
                "  proposals/",
                "    SCP-YYYY-NNN-<slug>/",
                "      README.md",
                "      (repro steps, diffs, logs, exports, etc)",
            ]
        )
        checklist_4 = "open a PR"
        focus = (
            "Focus: define gates, attach reproducible artifacts under "
            "<code>audit/proposals/&lt;SCP&gt;/...</code>, and reference adoption log/spine "
            "changes when needed."
        )
        qa = [
            "<li><strong>Q:</strong> What is the <code>scp_id</code>? <strong>A:</strong> "
            "Pick <code>SCP-YYYY-NNN-slug</code>.</li>",
            "<li><strong>Q:</strong> Who is the proposer? <strong>A:</strong> Fill "
            "<code>proposer</code>.</li>",
            "<li><strong>Q:</strong> Which obligations/controls are affected? "
            "<strong>A:</strong> Fill <code>affected_controls</code>.</li>",
            "<li><strong>Q:</strong> What is your claim? <strong>A:</strong> Fill "
            "<code>claim</code> with a single testable sentence.</li>",
            "<li><strong>Q:</strong> What gates prove the change is safe? "
            "<strong>A:</strong> Fill <code>gates</code> with the exact commands and the "
            "expected outcomes.</li>",
            "<li><strong>Q:</strong> How can someone reproduce the result? "
            "<strong>A:</strong> Put instructions and artifacts under "
            "<code>audit/proposals/&lt;SCP&gt;/</code> and reference them in "
            "<code>evidence_refs.yaml</code>.</li>",
            "<li><strong>Q:</strong> Does this require adoption log/spine changes? "
            "<strong>A:</strong> If yes, list the touched paths in "
            "<code>spine_or_adoption_log_changes</code>.</li>",
        ]

    checklist = "\n".join(
        [
            "<h2>Checklist</h2>",
            '<p class="muted">This is intentionally manual: copy templates, answer the Q/A, '
            "and submit for review.</p>",
            '<div class="card">',
            f"  <p class=\"muted\">{focus}</p>",
            "  <ol>",
            "    <li>Create folder <code>proposals/SCP-YYYY-NNN-slug/</code></li>",
            "    <li>Copy the appropriate template files (<code>proposal.yaml</code> and "
            "<code>evidence_refs.yaml</code>)</li>",
            (
                "    <li>Fill required fields: <code>scp_id</code>, <code>proposer</code>, "
                "<code>affected_controls</code>, <code>claim</code></li>"
            ),
            f"    <li>{checklist_4}</li>",
            "  </ol>",
            "</div>",
        ]
    )

    qa_block = "\n".join(
        [
            "<h2>Q/A Session (your inputs)</h2>",
            '<div class="card">',
            "  <ul>",
            *["    " + s for s in qa],
            "  </ul>",
            "</div>",
        ]
    )

    package_block = "\n".join(
        [
            "<h2>Copy/Paste Package (output)</h2>",
            (
                '<p class="muted">Use this as your starting point. The source-of-truth '
                "repo templates live under <code>docs/dao/templates/</code>.</p>"
            ),
            '<div class="card">',
            "  <h3>Folder tree</h3>",
            f"  <pre><code>{html.escape(tree)}</code></pre>",
            "</div>",
            '<div class="card">',
            "  <h3>proposal.yaml</h3>",
            f"  <pre><code>{html.escape(proposal_tmpl)}</code></pre>",
            "</div>",
            '<div class="card">',
            "  <h3>evidence_refs.yaml</h3>",
            f"  <pre><code>{html.escape(evidence_tmpl)}</code></pre>",
            "</div>",
            audit_readme_block,
        ]
    )

    return "\n".join([checklist, qa_block, package_block])


def _render_dao_stakeholders_new_proposal() -> str:
    return "\n".join(
        [
            "<h1>New Proposal (Stakeholders)</h1>",
            (
                '<p class="muted">Create a proposal directory under '
                '<code>proposals/</code> and submit it for review.</p>'
            ),
            _dao_new_proposal_block(view_id="dao_stakeholders"),
            _render_related_views_card(current_view="dao_stakeholders"),
            '<div class="card">',
            "  <h2>Links</h2>",
            "  <ul>",
            "    <li><a href=\"proposals/index.html\">Browse proposals</a></li>",
            "    <li><a href=\"index.html\">Back to DAO (Stakeholders)</a></li>",
            "  </ul>",
            "</div>",
        ]
    )


def _render_dao_stakeholders_proposals_index() -> str:
    return "\n".join(
        [
            "<h1>Proposals (Stakeholders)</h1>",
            '<p class="muted">This index is a placeholder until proposals are rendered.</p>',
            '<div class="card">',
            "  <h2>Proposals</h2>",
            "  <ul>",
            '    <li class="muted">(no proposals found)</li>',
            "  </ul>",
            "  <p><a href=\"../new_proposal.html\">Create a new proposal</a></p>",
            "</div>",
            '<div class="card">',
            "  <p><a href=\"../index.html\">Back to DAO (Stakeholders)</a></p>",
            "</div>",
        ]
    )


def _render_dao_dev_index() -> str:
    return "\n".join(
        [
            "<h1>DAO (Developers)</h1>",
            (
                '<p class="muted">A developer-facing view for implementing proposals with '
                "determinism, portability, and audit integrity gates.</p>"
            ),
            '<div class="card">',
            "  <h2>Purpose</h2>",
            "  <ul>",
            "    <li>Define the implementation contract for proposals.</li>",
            (
                "    <li>Keep outputs deterministic (no timestamps, stable ordering, LF "
                "newlines).</li>"
            ),
            "    <li>Preserve link integrity inside the site bundle.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>How to use the bundle for Q/A</h2>",
            "  <ul>",
            (
                "    <li>Rebuild the bundle locally and open <code>index.html</code> to review "
                "UX.</li>"
            ),
            (
                "    <li>Run the portability link checker and review "
                "<code>link_check.json</code>.</li>"
            ),
            "    <li>Verify the manifest and/or zip sha256 match after sharing.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>Proposals</h2>",
            "  <ul>",
            "    <li><a href=\"proposals/index.html\">Browse proposals</a></li>",
            "    <li><a href=\"new_proposal.html\">Create a new proposal</a></li>",
            "    <li><a href=\"gates.html\">Gates</a></li>",
            "    <li><a href=\"contribution_contract.html\">Contribution contract</a></li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>Agent prompt</h2>",
            (
                "  <p><a href=\"../../agent_prompts/dao_dev_prompt.md\">Open developers "
                "agent prompt</a></p>"
            ),
            "</div>",
            _render_related_views_card(current_view="dao_dev"),
        ]
    )


def _render_dao_dev_gates() -> str:
    return "\n".join(
        [
            "<h1>Gates (Developers)</h1>",
            '<p class="muted">Minimum checks before a proposal can be accepted.</p>',
            '<div class="card">',
            "  <h2>Required</h2>",
            "  <ul>",
            "    <li><code>python -m ruff check</code> passes.</li>",
            "    <li><code>pytest</code> passes.</li>",
            (
                "    <li>Portable link check passes (no <code>/</code> or <code>file://</code> "
                "links).</li>"
            ),
            "    <li>Manifest written deterministically for the bundle.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <p><a href=\"index.html\">Back to DAO (Developers)</a></p>",
            "</div>",
        ]
    )


def _render_dao_dev_contribution_contract() -> str:
    return "\n".join(
        [
            "<h1>Contribution Contract (Developers)</h1>",
            '<p class="muted">Rules for implementing changes without breaking portability.</p>',
            '<div class="card">',
            "  <h2>Determinism</h2>",
            "  <ul>",
            "    <li>No timestamps in generated HTML or JSON.</li>",
            "    <li>Stable ordering for lists and directory walks (lexicographic sorting).</li>",
            "    <li>Write text files with LF newlines.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <h2>Portability</h2>",
            "  <ul>",
            "    <li>Use relative links that resolve inside the bundle root.</li>",
            "    <li>Do not emit <code>file://</code> links or absolute <code>/</code> links.</li>",
            "  </ul>",
            "</div>",
            '<div class="card">',
            "  <p><a href=\"index.html\">Back to DAO (Developers)</a></p>",
            "</div>",
        ]
    )


def _render_dao_dev_new_proposal() -> str:
    return "\n".join(
        [
            "<h1>New Proposal (Developers)</h1>",
            (
                '<p class="muted">Developer-authored proposals should include the exact gates '
                "and test impact.</p>"
            ),
            _dao_new_proposal_block(view_id="dao_dev"),
            _render_related_views_card(current_view="dao_dev"),
            '<div class="card">',
            "  <h2>Links</h2>",
            "  <ul>",
            "    <li><a href=\"proposals/index.html\">Browse proposals</a></li>",
            "    <li><a href=\"index.html\">Back to DAO (Developers)</a></li>",
            "  </ul>",
            "</div>",
        ]
    )


def _render_dao_dev_proposals_index() -> str:
    return "\n".join(
        [
            "<h1>Proposals (Developers)</h1>",
            '<p class="muted">This index is a placeholder until proposals are rendered.</p>',
            '<div class="card">',
            "  <h2>Proposals</h2>",
            "  <ul>",
            '    <li class="muted">(no proposals found)</li>',
            "  </ul>",
            "  <p><a href=\"../new_proposal.html\">Create a new proposal</a></p>",
            "</div>",
            '<div class="card">',
            "  <p><a href=\"../index.html\">Back to DAO (Developers)</a></p>",
            "</div>",
        ]
    )


_AOI_REPORTS_AUDIT_DIR = Path("/Users/server/audit/eudr_dmi/reports/aoi_runs")
_AOI_REPORTS_MAX_RUNS_DEFAULT = 25


def _file_url(path: Path) -> str:
    # Convert an absolute POSIX path to a file:// URL.
    # Example: /Users/server/audit/... -> file:///Users/server/audit/...
    p = path.resolve().as_posix()
    return "file:///" + quote(p.lstrip("/"), safe="/")


def _list_aoi_report_html(audit_dir: Path) -> list[Path]:
    try:
        if not audit_dir.exists():
            return []
        paths = [p for p in audit_dir.glob("*.html") if p.is_file()]
    except OSError:
        return []

    return sorted(paths, key=lambda p: p.name, reverse=True)


def _render_aoi_reports_index(*, audit_dir: Path, portable: bool, max_runs: int) -> str:
    if portable:
        # Bundle-friendly: no file:// links. Emit stable relative links into the bundle
        # layout under: site/aoi_reports/runs/<run_id>/report.html
        reports = _list_aoi_report_html(audit_dir)
        if max_runs > 0:
            reports = reports[:max_runs]

        items: list[str] = []
        if reports:
            for p in reports:
                run_id = p.stem
                report_href = f"runs/{run_id}/report.html"
                item = f'<li><a href="{html.escape(report_href)}">{html.escape(run_id)}</a>'

                # Optional JSON sidecar (will be copied by the bundler if present).
                if (audit_dir / f"{run_id}.json").is_file():
                    summary_href = f"runs/{run_id}/summary.json"
                    item += (
                        f' <span class="muted">(</span><a href="{html.escape(summary_href)}">'
                        'summary.json</a><span class="muted">)</span>'
                    )
                item += "</li>"
                items.append(item)
        else:
            items.append('<li class="muted">(no AOI HTML reports found)</li>')

        return "\n".join(
            [
                "<h1>AOI Reports</h1>",
                (
                    '<p class="muted">Portable mode: links point into the bundle under '
                    '<code>runs/&lt;run_id&gt;/report.html</code>.</p>'
                ),
                "<div class=\"card\">",
                "  <h2>Runs (newest first)</h2>",
                "  <ul>",
                "\n".join(items),
                "  </ul>",
                "</div>",
            ]
        )

    reports = _list_aoi_report_html(audit_dir)

    if reports:
        items = []
        for p in reports:
            run_id = p.stem
            href = _file_url(p)
            items.append(
                "\n".join(
                    [
                        "<li>",
                        f"  <a href=\"{html.escape(href)}\">{html.escape(run_id)}</a>",
                        f"  <span class=\"muted\">{html.escape(str(p))}</span>",
                        "</li>",
                    ]
                )
            )
        items_html = "\n".join(items)
    else:
        items_html = '<li class="muted">(no AOI HTML reports found)</li>'

    return "\n".join(
        [
            "<h1>AOI Reports</h1>",
            (
                "<p class=\"muted\">Links point to the server audit root via <code>file://</code> "
                "URLs.</p>"
            ),
            "<div class=\"card\">",
            "  <h2>Audit directory</h2>",
            f"  <p><code>{html.escape(str(audit_dir))}</code></p>",
            "</div>",
            "<div class=\"card\">",
            "  <h2>Runs (newest first)</h2>",
            "  <ul>",
            items_html,
            "  </ul>",
            "</div>",
        ]
    )


def _parse_article_summaries(md_text: str) -> dict[str, ArticleSummary]:
    # Expected patterns:
    #   ## Article 9 — Title
    #   - bullet
    article_re = re.compile(r"^##\s+Article\s+(\d{1,2})\b\s*(.*)$")

    current_id: str | None = None
    current_heading: str | None = None
    current_bullets: list[str] = []

    summaries: dict[str, ArticleSummary] = {}

    def flush() -> None:
        nonlocal current_id, current_heading, current_bullets
        if current_id is None or current_heading is None:
            return
        bullets = tuple([b for b in current_bullets if b.strip()])
        summaries[current_id] = ArticleSummary(
            article_id=current_id,
            heading=current_heading,
            bullets=bullets,
        )
        current_id = None
        current_heading = None
        current_bullets = []

    for raw_line in md_text.splitlines():
        line = raw_line.rstrip("\r\n")
        match = article_re.match(line)
        if match:
            flush()
            article_num = int(match.group(1))
            current_id = f"{article_num:02d}"
            current_heading = line.replace("## ", "", 1).strip()
            continue

        if current_id is None:
            continue

        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            current_bullets.append(stripped[2:].strip())

    flush()
    return summaries


def _parse_dependencies(obj: object) -> list[Dependency]:
    if not isinstance(obj, dict):
        raise TypeError("dependencies.json must be a JSON object")

    deps_obj = obj.get("dependencies")
    if not isinstance(deps_obj, list):
        raise TypeError("dependencies.json must contain a 'dependencies' list")

    deps: list[Dependency] = []
    for item in deps_obj:
        if not isinstance(item, dict):
            raise TypeError("Each dependency must be an object")

        used_by = item.get("used_by")
        if not isinstance(used_by, list) or not all(isinstance(x, str) for x in used_by):
            raise TypeError("dependency.used_by must be a list of strings")

        dep_id = item.get("id")
        title = item.get("title")
        url = item.get("url")
        expected_content_type = item.get("expected_content_type")
        server_path = item.get("server_path")

        required_str_fields = [dep_id, title, url, expected_content_type, server_path]
        if not all(isinstance(x, str) and x for x in required_str_fields):
            raise TypeError(
                "dependency must include non-empty string fields: id, title, url, "
                "expected_content_type, server_path"
            )

        deps.append(
            Dependency(
                id=dep_id,
                title=title,
                url=url,
                expected_content_type=expected_content_type,
                server_path=server_path,
                used_by=tuple(used_by),
                purpose=str(item.get("purpose")) if item.get("purpose") is not None else None,
            )
        )

    deps.sort(key=lambda d: d.id)
    return deps


def _repo_link_from_docs_html(path_from_repo_root: str, *, page_depth: int) -> str:
    """Build a relative link from docs/html/<...> to a repo-root path.

    page_depth: number of path segments after docs/html.
      - docs/html/index.html => 1
      - docs/html/articles/index.html => 2
      - docs/html/dependencies/index.html => 2
    """

    # From docs/html/<...> up to repo root: ../ (to docs/html) per segment,
    # then ../ to docs, then ../ to repo root.
    prefix = "../" * page_depth + "../" + "../"
    return prefix + path_from_repo_root


def _render_dependency_card(dep: Dependency, *, portable: bool) -> str:
    used_by_links: list[str] = []
    for module_path in sorted(dep.used_by):
        if portable:
            used_by_links.append(f"<li><code>{html.escape(module_path)}</code></li>")
        else:
            href = _repo_link_from_docs_html(module_path, page_depth=2)
            used_by_links.append(
                f"<li><a href=\"{html.escape(href)}\">{html.escape(module_path)}</a></li>"
            )

    used_by_html = (
        "\n".join(used_by_links) if used_by_links else "<li class=\"muted\">(none)</li>"
    )

    purpose_html = ""
    if dep.purpose:
        purpose_html = f"<p class=\"muted\">{html.escape(dep.purpose)}</p>"

    definition_links_html = ""
    if ("definitions" in dep.id or "definitions" in (dep.purpose or "").lower()) and not portable:
        definition_links_html = "\n".join(
            [
                "<h3>Definition comparison context</h3>",
                "<ul>",
                (
                    "  <li><a href=\"../../regulation/policy_to_evidence_spine.md\">"
                    "Policy-to-evidence spine</a></li>"
                ),
                (
                    "  <li><a href=\"../../../scripts/task3/definition_comparison_control.py\">"
                    "Definition comparison control</a></li>"
                ),
                "</ul>",
            ]
        )

    return "\n".join(
        [
            '<div class="card">',
            f"  <h2>{html.escape(dep.title)}</h2>",
            purpose_html,
            "  <ul>",
            f"    <li><b>id</b>: <code>{html.escape(dep.id)}</code></li>",
            (
                f"    <li><b>URL</b>: <a href=\"{html.escape(dep.url)}\">"
                f"{html.escape(dep.url)}</a></li>"
            ),
            (
                f"    <li><b>Expected content type</b>: <code>"
                f"{html.escape(dep.expected_content_type)}</code></li>"
            ),
            f"    <li><b>Server audit path</b>: <code>{html.escape(dep.server_path)}</code></li>",
            "  </ul>",
            "  <h3>Used by</h3>",
            "  <ul>",
            used_by_html,
            "  </ul>",
            definition_links_html,
            "</div>",
        ]
    )


def _render_article_card(summary: ArticleSummary, *, href: str) -> str:
    bullets_html = "\n".join(
        [f"<li>{html.escape(b)}</li>" for b in summary.bullets]
    )
    return "\n".join(
        [
            '<div class="card">',
            f"  <h2><a href=\"{href}\">{html.escape(summary.heading)}</a></h2>",
            "  <ul>",
            f"{bullets_html}",
            "  </ul>",
            "</div>",
        ]
    )


def build_site(*, docs_root: Path, out_root: Path, portable: bool, aoi_max_runs: int) -> None:
    articles_md_path = docs_root / "articles" / "eudr_article_summaries.md"
    sources_md_path = docs_root / "regulation" / "sources.md"
    links_html_path = docs_root / "regulation" / "links.html"
    spine_md_path = docs_root / "regulation" / "policy_to_evidence_spine.md"
    dependencies_json_path = docs_root / "dependencies" / "dependencies.json"

    for p in [
        articles_md_path,
        sources_md_path,
        links_html_path,
        spine_md_path,
        dependencies_json_path,
    ]:
        if not p.exists():
            raise FileNotFoundError(f"Required input missing: {p}")

    articles_md = articles_md_path.read_text(encoding="utf-8")
    summaries = _parse_article_summaries(articles_md)

    deps = _parse_dependencies(_read_json(dependencies_json_path))

    missing = [a for a in _REQUIRED_ARTICLES if a not in summaries]
    if missing:
        raise ValueError(
            "Missing required article summaries: " + ", ".join(missing)
        )

    # Stable ordering.
    ordered_ids = [a for a in _REQUIRED_ARTICLES]

    # Home page.
    home_body = "\n".join(
        [
            "<h1>Audit Documentation</h1>",
            '<p class="muted">Deterministic, static HTML generated from project docs.</p>',
            "<div class=\"grid\">",
            "  <div class=\"card\">",
            "    <h2>Articles 9/10/11</h2>",
            "    <ul>",
            (
                "      <li><a href=\"articles/article_09.html\">Article 9 — "
                "Information requirements"
                "</a></li>"
            ),
            "      <li><a href=\"articles/article_10.html\">Article 10 — Risk assessment</a></li>",
            "      <li><a href=\"articles/article_11.html\">Article 11 — Risk mitigation</a></li>",
            "    </ul>",
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>Regulation</h2>",
            "    <ul>",
            (
                "      <li><a href=\"../regulation/links.html\">EUR-Lex launcher</a> "
                "(operator browser entrypoint)</li>"
            ),
            "      <li><a href=\"../regulation/sources.md\">Regulation sources registry</a></li>",
            "    </ul>",
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>Spine</h2>",
            (
                "    <p><a href=\"../regulation/"
                "policy_to_evidence_spine.md\">Policy-to-evidence spine "
                "mapping</a></p>"
            ),
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>Dependencies</h2>",
            (
                "    <p><a href=\"dependencies/index.html\">"
                "Known data sources and how they are used</a></p>"
            ),
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>AOI Reports</h2>",
            "    <p><a href=\"aoi_reports/index.html\">Open AOI report runs</a></p>",
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>DAO (Stakeholders)</h2>",
            (
                "    <p><a href=\"dao_stakeholders/index.html\">Stakeholder proposals and "
                "participation</a></p>"
            ),
            "  </div>",
            "  <div class=\"card\">",
            "    <h2>DAO (Developers)</h2>",
            (
                "    <p><a href=\"dao_dev/index.html\">Developer gates and contribution "
                "contract</a></p>"
            ),
            "  </div>",
            "</div>",
        ]
    )
    _write_text(
        out_root / "index.html",
        _html_page(
            title="Audit Documentation",
            nav_html=_nav(current="home", rel_prefix=""),
            body_html=home_body,
        ),
    )

    # Dependencies index.
    dep_cards = "\n".join([_render_dependency_card(d, portable=portable) for d in deps])
    deps_body = "\n".join(
        [
            "<h1>Dependencies</h1>",
            (
                "<p class=\"muted\">Known data sources, their audit paths, "
                "and where they are used in this repo.</p>"
            ),
            "<div class=\"card\">",
            "  <h2>Regulation context</h2>",
            "  <ul>",
            "    <li><a href=\"../../regulation/links.html\">EUR-Lex launcher</a></li>",
            "    <li><a href=\"../../regulation/sources.md\">Regulation sources registry</a></li>",
            (
                "    <li><a href=\"../../regulation/policy_to_evidence_spine.md\">"
                "Policy-to-evidence spine</a></li>"
            ),
            "  </ul>",
            "</div>",
            dep_cards,
        ]
    )
    _write_text(
        out_root / "dependencies" / "index.html",
        _html_page(
            title="Dependencies",
            nav_html=_nav(current="dependencies", rel_prefix="../"),
            body_html=deps_body,
        ),
    )

    # Articles index.
    article_cards = []
    for article_id in ordered_ids:
        summary = summaries[article_id]
        article_cards.append(
            _render_article_card(
                summary,
                href=f"article_{article_id}.html",
            )
        )

    articles_index_body = "\n".join(
        [
            "<h1>Articles Index</h1>",
            (
                "<p class=\"muted\">Summaries are non-verbatim orientation notes for implementers "
                "and "
                "auditors.</p>"
            ),
            "<div class=\"card\">",
            "  <h2>Quick links</h2>",
            "  <ul>",
            "    <li><a href=\"../../regulation/links.html\">EUR-Lex launcher</a></li>",
            "    <li><a href=\"../../regulation/sources.md\">Regulation sources registry</a></li>",
            (
                "    <li><a href=\"../../regulation/"
                "policy_to_evidence_spine.md\">Policy-to-evidence spine"
                "</a></li>"
            ),
            "  </ul>",
            "</div>",
            "<div class=\"grid\">",
            "\n".join(article_cards),
            "</div>",
        ]
    )

    _write_text(
        out_root / "articles" / "index.html",
        _html_page(
            title="Articles Index",
            nav_html=_nav(current="articles", rel_prefix="../"),
            body_html=articles_index_body,
        ),
    )

    # Individual article pages.
    for article_id in ordered_ids:
        summary = summaries[article_id]
        bullets_html = "\n".join(
            [f"<li>{html.escape(b)}</li>" for b in summary.bullets]
        )
        article_body = "\n".join(
            [
                f"<h1>{html.escape(summary.heading)}</h1>",
                (
                    "<p class=\"muted\">Non-verbatim orientation notes. See regulation sources for "
                    "authoritative text.</p>"
                ),
                "<div class=\"card\">",
                "  <h2>Summary</h2>",
                "  <ul>",
                bullets_html,
                "  </ul>",
                "</div>",
                "<div class=\"card\">",
                "  <h2>Related links</h2>",
                "  <ul>",
                "    <li><a href=\"../../regulation/links.html\">EUR-Lex launcher</a></li>",
                (
                    "    <li><a href=\"../../regulation/sources.md\">Regulation sources "
                    "registry</a></li>"
                ),
                (
                    "    <li><a href=\"../../regulation/"
                    "policy_to_evidence_spine.md\">Policy-to-evidence spine"
                    "</a></li>"
                ),
                "    <li><a href=\"index.html\">Back to Articles Index</a></li>",
                "  </ul>",
                "</div>",
            ]
        )
        _write_text(
            out_root / "articles" / f"article_{article_id}.html",
            _html_page(
                title=summary.heading,
                nav_html=_nav(current="articles", rel_prefix="../"),
                body_html=article_body,
            ),
        )

    # AOI reports index.
    aoi_index_body = _render_aoi_reports_index(
        audit_dir=_AOI_REPORTS_AUDIT_DIR,
        portable=portable,
        max_runs=aoi_max_runs,
    )
    _write_text(
        out_root / "aoi_reports" / "index.html",
        _html_page(
            title="AOI Reports",
            nav_html=_nav(current="aoi", rel_prefix="../"),
            body_html=aoi_index_body,
        ),
    )

    # Backwards-compatible stub (old link).
    aoi_stub_body = "\n".join(
        [
            "<h1>AOI Reports</h1>",
            "<p class=\"muted\">This page has moved.</p>",
            "<div class=\"card\">",
            "  <p><a href=\"aoi_reports/index.html\">Open AOI report runs</a></p>",
            "</div>",
        ]
    )
    _write_text(
        out_root / "aoi_reports.html",
        _html_page(
            title="AOI Reports",
            nav_html=_nav(current="aoi", rel_prefix=""),
            body_html=aoi_stub_body,
        ),
    )

    # DAO (Stakeholders)
    _write_text(
        out_root / "dao_stakeholders" / "index.html",
        _html_page(
            title="DAO (Stakeholders)",
            nav_html=_nav(current="dao_stakeholders", rel_prefix="../"),
            body_html=_render_dao_stakeholders_index(),
        ),
    )
    _write_text(
        out_root / "dao_stakeholders" / "how_to_participate.html",
        _html_page(
            title="How to Participate (Stakeholders)",
            nav_html=_nav(current="dao_stakeholders", rel_prefix="../"),
            body_html=_render_dao_stakeholders_how_to_participate(),
        ),
    )
    _write_text(
        out_root / "dao_stakeholders" / "new_proposal.html",
        _html_page(
            title="New Proposal (Stakeholders)",
            nav_html=_nav(current="dao_stakeholders", rel_prefix="../"),
            body_html=_render_dao_stakeholders_new_proposal(),
        ),
    )
    _write_text(
        out_root / "dao_stakeholders" / "proposals" / "index.html",
        _html_page(
            title="Proposals (Stakeholders)",
            nav_html=_nav(current="dao_stakeholders", rel_prefix="../../"),
            body_html=_render_dao_stakeholders_proposals_index(),
        ),
    )

    # DAO (Developers)
    _write_text(
        out_root / "dao_dev" / "index.html",
        _html_page(
            title="DAO (Developers)",
            nav_html=_nav(current="dao_dev", rel_prefix="../"),
            body_html=_render_dao_dev_index(),
        ),
    )
    _write_text(
        out_root / "dao_dev" / "gates.html",
        _html_page(
            title="Gates (Developers)",
            nav_html=_nav(current="dao_dev", rel_prefix="../"),
            body_html=_render_dao_dev_gates(),
        ),
    )
    _write_text(
        out_root / "dao_dev" / "contribution_contract.html",
        _html_page(
            title="Contribution Contract (Developers)",
            nav_html=_nav(current="dao_dev", rel_prefix="../"),
            body_html=_render_dao_dev_contribution_contract(),
        ),
    )
    _write_text(
        out_root / "dao_dev" / "new_proposal.html",
        _html_page(
            title="New Proposal (Developers)",
            nav_html=_nav(current="dao_dev", rel_prefix="../"),
            body_html=_render_dao_dev_new_proposal(),
        ),
    )
    _write_text(
        out_root / "dao_dev" / "proposals" / "index.html",
        _html_page(
            title="Proposals (Developers)",
            nav_html=_nav(current="dao_dev", rel_prefix="../../"),
            body_html=_render_dao_dev_proposals_index(),
        ),
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build deterministic docs HTML site")
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repo root (defaults to inferred from this script)",
    )
    parser.add_argument(
        "--docs-root",
        type=Path,
        default=None,
        help="Docs root (defaults to <repo-root>/docs)",
    )
    parser.add_argument(
        "--out-root",
        type=Path,
        default=None,
        help="Output root (defaults to <docs-root>/html)",
    )
    parser.add_argument(
        "--portable",
        action="store_true",
        help=(
            "Emit a site intended for bundling/sharing: avoid links that point outside the site "
            "root (e.g., repo source links), and avoid file:// audit-root links."
        ),
    )
    parser.add_argument(
        "--aoi-max-runs",
        type=int,
        default=_AOI_REPORTS_MAX_RUNS_DEFAULT,
        help="Limit AOI runs listed on the AOI Reports index (default: 25).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)

    repo_root = args.repo_root
    if repo_root is None:
        repo_root = _repo_root_from_this_file()

    docs_root = args.docs_root
    if docs_root is None:
        docs_root = repo_root / "docs"

    out_root = args.out_root
    if out_root is None:
        out_root = docs_root / "html"

    build_site(
        docs_root=docs_root,
        out_root=out_root,
        portable=bool(args.portable),
        aoi_max_runs=int(args.aoi_max_runs),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
