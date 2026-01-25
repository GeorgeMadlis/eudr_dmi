from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class _PathGroup:
    """A required allowlist entry.

    Some entries have multiple acceptable repo-relative candidates to support
    file moves ("or wherever it currently lives"). At least one candidate must
    exist.
    """

    label: str
    candidates: tuple[str, ...]


# Hardcoded allowlist of repo-relative paths.
#
# MUST include exactly these conceptual entries (and may include additional
# adjacent paths if they exist):
# - scripts/fetch_dependency_definitions.py
# - scripts/watch_dependency_definitions.py
# - tools/dependencies/acquire_and_hash.py
# - definition_comparison_control.py (current location)
# - stable_json.py (current location)
# - tests/... (the dependency mirroring + control tests)
PATH_GROUPS: tuple[_PathGroup, ...] = (
    _PathGroup("fetch wrapper", ("scripts/fetch_dependency_definitions.py",)),
    _PathGroup("watcher", ("scripts/watch_dependency_definitions.py",)),
    _PathGroup("acquire tool", ("tools/dependencies/acquire_and_hash.py",)),
    _PathGroup(
        "definition comparison control",
        (
            "src/controls/definition_comparison_control.py",
            "scripts/task3/definition_comparison_control.py",
        ),
    ),
    _PathGroup(
        "stable json helper",
        (
            "src/utils/stable_json.py",
            "src/eudr_dmi/evidence/stable_json.py",
        ),
    ),
    _PathGroup("test: definition comparison", ("tests/test_definition_comparison_artifacts.py",)),
    _PathGroup(
        "test: acquire determinism",
        ("tests/test_dependencies_acquire_and_hash_determinism.py",),
    ),
    _PathGroup(
        "test: fetch wrapper smoke",
        ("tests/test_fetch_dependency_definitions_smoke.py",),
    ),
    _PathGroup(
        "test: watcher exit codes",
        ("tests/test_watch_dependency_definitions_exit_codes.py",),
    ),
)


def _repo_root() -> Path:
    # tools/ci/lint_scoped.py -> tools/ci -> tools -> repo root
    return Path(__file__).resolve().parents[2]


def _resolve_scoped_paths(repo_root: Path) -> list[str]:
    resolved: list[str] = []

    for group in PATH_GROUPS:
        found: str | None = None
        for rel in group.candidates:
            if (repo_root / rel).exists():
                found = rel
                break

        if found is None:
            candidates = ", ".join(group.candidates)
            raise FileNotFoundError(
                f"Missing allowlisted path for {group.label}. Tried: {candidates}"
            )

        resolved.append(found)

    return resolved


def main(argv: list[str] | None = None) -> int:
    _ = argv  # no args; hardcoded allowlist
    repo_root = _repo_root()

    print("Scoped ruff lint (dependency mirroring)")

    try:
        paths = _resolve_scoped_paths(repo_root)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    cmd = ["python", "-m", "ruff", "check", *paths]
    print("Command:")
    print("  " + " ".join(cmd))

    completed = subprocess.run(cmd, cwd=str(repo_root), check=False)
    return int(completed.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
