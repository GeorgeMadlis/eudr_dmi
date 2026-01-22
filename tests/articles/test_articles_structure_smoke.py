from pathlib import Path


def test_expected_project_structure_exists() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    expected_paths = [
        repo_root / "README.md",
        repo_root / "docs" / "INDEX.md",
        repo_root / "docs" / "architecture" / "evidence_contract.md",
        repo_root / "docs" / "operations" / "inspection_checklist.md",
        repo_root / "docs" / "articles" / "art_09" / "README.md",
        repo_root / "docs" / "articles" / "art_10" / "README.md",
        repo_root / "docs" / "articles" / "art_11" / "README.md",
        repo_root / "src" / "eudr_dmi" / "__init__.py",
        repo_root / "src" / "eudr_dmi" / "articles" / "__init__.py",
        repo_root / "src" / "eudr_dmi" / "articles" / "art_09" / "__init__.py",
        repo_root / "src" / "eudr_dmi" / "articles" / "art_10" / "__init__.py",
        repo_root / "src" / "eudr_dmi" / "articles" / "art_11" / "__init__.py",
        repo_root / "tests" / "articles" / "test_articles_structure_smoke.py",
    ]

    missing = [str(p.relative_to(repo_root)) for p in expected_paths if not p.exists()]
    assert not missing, f"Missing expected paths: {missing}"