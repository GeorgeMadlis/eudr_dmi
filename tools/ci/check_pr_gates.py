from __future__ import annotations

import os
import sys
from pathlib import Path

REQUIRED_PATHS = [
    "README.md",
    "docs/INDEX.md",
    "docs/overview.md",
    "docs/glossary.md",
    "docs/architecture/decision_records/ADR-0001-project-scope.md",
    "docs/architecture/digital_twin_model.md",
    "docs/architecture/evidence_contract.md",
    "docs/architecture/evidence_bundle_spec.md",
    "docs/architecture/dependency_register.md",
    "docs/architecture/method_notes_and_decisions.md",
    "docs/architecture/risk_register.md",
    "docs/architecture/change_control.md",
    "docs/regulation/sources.md",
    "docs/regulation/sources.json",
    "docs/regulation/links.html",
    "docs/operations/runbooks.md",
    "docs/operations/secrets_handling.md",
    "docs/operations/inspection_checklist.md",
    ".github/pull_request_template.md",
    ".github/workflows/ci.yml",
]


def _normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def _fail(message: str, details: list[str] | None = None) -> int:
    print(f"FAIL: {message}")
    if details:
        for line in details:
            print(f"- {line}")
    return 1


def _pass(message: str) -> int:
    print(f"PASS: {message}")
    return 0


def _check_required_paths(repo_root: Path) -> list[str]:
    missing: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (repo_root / rel).exists():
            missing.append(rel)
    return missing


def main() -> int:
    repo_root = Path(__file__).resolve().parents[2]

    missing = _check_required_paths(repo_root)
    if missing:
        return _fail("Required canonical files are missing.", missing)

    changed_files = [_normalize_path(line) for line in sys.stdin.read().splitlines()]
    changed_files = [p for p in changed_files if p]

    # Non-PR runs: stdin empty => only existence checks.
    if not changed_files:
        if os.environ.get("GITHUB_EVENT_NAME") == "pull_request":
            return _fail(
                "PR gate checks failed.",
                ["Empty PR diff (no changed files) is not allowed."],
            )
        return _pass("Canonical files present (non-PR run).")

    failures: list[str] = []

    def any_changed(prefix: str) -> bool:
        prefix = _normalize_path(prefix).rstrip("/") + "/"
        return any(p.startswith(prefix) for p in changed_files)

    is_governance_only = all(p.startswith(".github/") for p in changed_files)
    if is_governance_only:
        print(
            "Governance-only change detected (.github/*). Skipping content-change requirement."
        )

    # Ensure PR touches at least one of these content roots.
    if (not is_governance_only) and not any(
        p.startswith(("docs/", "src/", "tests/", "tools/")) for p in changed_files
    ):
        failures.append(
            "PR must change at least one file under docs/ or src/ or tests/ or tools/."
        )

    article_rules = [
        ("src/eudr_dmi/articles/art_09/", "docs/articles/art_09/"),
        ("src/eudr_dmi/articles/art_10/", "docs/articles/art_10/"),
        ("src/eudr_dmi/articles/art_11/", "docs/articles/art_11/"),
    ]

    for src_prefix, docs_prefix in article_rules:
        if any_changed(src_prefix) and not any_changed(docs_prefix):
            failures.append(
                f"Changes under {src_prefix} require a corresponding change under {docs_prefix}."
            )

    if failures:
        return _fail("PR gate checks failed.", failures)

    return _pass("All PR gate checks passed.")


if __name__ == "__main__":
    raise SystemExit(main())
