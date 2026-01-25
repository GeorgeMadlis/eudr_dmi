from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PYTEST_REQUIRED_ALLOWLIST: list[str] = [
    "tests/test_definition_comparison_artifacts.py",
    "tests/test_dependencies_acquire_and_hash_determinism.py",
    "tests/test_fetch_dependency_definitions_smoke.py",
    "tests/test_watch_dependency_definitions_exit_codes.py",
]

PYTEST_OPTIONAL_ALLOWLIST: list[str] = [
    "tests/test_dependencies_sources_schema.py",
]


def _repo_root() -> Path:
    # tools/ci/quality_scoped.py -> tools/ci -> tools -> repo root
    return Path(__file__).resolve().parents[2]


def _resolve_pytest_paths(repo_root: Path) -> list[str]:
    missing: list[str] = []
    resolved: list[str] = []

    for rel in PYTEST_REQUIRED_ALLOWLIST:
        if not (repo_root / rel).exists():
            missing.append(rel)
        else:
            resolved.append(rel)

    for rel in PYTEST_OPTIONAL_ALLOWLIST:
        if (repo_root / rel).exists():
            resolved.append(rel)

    if missing:
        missing_str = ", ".join(missing)
        raise FileNotFoundError(f"Missing required pytest allowlist paths: {missing_str}")

    return resolved


def main(argv: list[str] | None = None) -> int:
    _ = argv  # no args; hardcoded allowlists
    repo_root = _repo_root()

    # Step 1: scoped pytest
    print("Scoped quality: pytest (dependency mirroring)")
    try:
        pytest_paths = _resolve_pytest_paths(repo_root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    pytest_cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "--maxfail=1",
        *pytest_paths,
    ]
    print("Command:")
    print("  " + " ".join(pytest_cmd))

    pytest_completed = subprocess.run(pytest_cmd, cwd=str(repo_root), check=False)
    if pytest_completed.returncode != 0:
        return int(pytest_completed.returncode)

    # Step 2: scoped ruff lint
    print("Scoped quality: ruff (dependency mirroring)")
    lint_cmd = [sys.executable, "tools/ci/lint_scoped.py"]
    print("Command:")
    print("  " + " ".join(lint_cmd))

    lint_completed = subprocess.run(lint_cmd, cwd=str(repo_root), check=False)
    return int(lint_completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
