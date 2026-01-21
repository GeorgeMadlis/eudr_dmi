from pathlib import Path


def test_required_scaffold_files_exist() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    required = [
        repo_root / "pyproject.toml",
        repo_root / ".github" / "workflows" / "ci.yml",
        repo_root / "tools" / "ci" / "check_pr_gates.py",
        repo_root / ".github" / "pull_request_template.md",
    ]

    missing = [str(p.relative_to(repo_root)) for p in required if not p.exists()]
    assert not missing, f"Missing required scaffold files: {missing}"
