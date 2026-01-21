from __future__ import annotations

from pathlib import Path


def test_regulation_registry_files_exist():
    repo_root = Path(__file__).resolve().parents[1]

    required = [
        repo_root / "docs" / "regulation_sources.json",
        repo_root / "docs" / "regulation_links.html",
        repo_root / "docs" / "articles" / "eudr_article_summaries.md",
        repo_root / "tools" / "regulation" / "acquire_and_hash.py",
        repo_root / "docs" / "secrets_handling.md",
    ]

    missing = [str(p) for p in required if not p.exists()]
    assert not missing, f"Missing required files: {missing}"
