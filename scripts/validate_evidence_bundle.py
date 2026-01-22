from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from eudr_dmi.evidence.hash_utils import sha256_file


@dataclass(frozen=True, slots=True)
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


def _parse_manifest_lines(text: str) -> list[tuple[str, str]]:
    entries: list[tuple[str, str]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            raise ValueError(f"Invalid manifest line: {raw_line!r}")
        digest = parts[0]
        rel_path = parts[-1]
        entries.append((digest, rel_path))
    return entries


def validate_bundle(bundle_dir: str | Path) -> ValidationResult:
    bundle_path = Path(bundle_dir)
    errors: list[str] = []
    warnings: list[str] = []

    if not bundle_path.exists():
        return ValidationResult(False, [f"Bundle path does not exist: {bundle_path}"], [])
    if not bundle_path.is_dir():
        return ValidationResult(False, [f"Bundle path is not a directory: {bundle_path}"], [])

    manifest_path = bundle_path / "manifest.sha256"
    if not manifest_path.exists():
        errors.append("Missing required file: manifest.sha256")
        return ValidationResult(False, errors, warnings)

    # Required deterministic metadata file (Art 09 uses bundle_metadata.json).
    metadata_candidates = ["bundle_metadata.json", "deterministic_metadata.json"]
    if not any((bundle_path / name).exists() for name in metadata_candidates):
        errors.append(
            "Missing deterministic metadata JSON (expected one of: "
            + ", ".join(metadata_candidates)
            + ")"
        )

    execution_log_path = bundle_path / "execution_log.json"
    if not execution_log_path.exists():
        warnings.append("Missing recommended file: execution_log.json")

    try:
        manifest_text = manifest_path.read_text(encoding="utf-8", errors="strict")
        entries = _parse_manifest_lines(manifest_text)
    except Exception as exc:
        errors.append(f"Failed to parse manifest.sha256: {exc.__class__.__name__}: {exc}")
        return ValidationResult(False, errors, warnings)

    if not entries:
        errors.append("manifest.sha256 contains no entries")
        return ValidationResult(False, errors, warnings)

    for expected_digest, rel_path in entries:
        # The manifest is expected to list bundle-local paths.
        # We allow subpaths, but prevent escaping the bundle directory.
        rel = Path(rel_path)
        if rel.is_absolute():
            errors.append(f"Manifest entry must be relative, got absolute path: {rel_path}")
            continue

        file_path = (bundle_path / rel).resolve()
        try:
            file_path.relative_to(bundle_path.resolve())
        except Exception:
            errors.append(f"Manifest entry escapes bundle dir: {rel_path}")
            continue

        if not file_path.exists() or not file_path.is_file():
            errors.append(f"Missing file listed in manifest: {rel_path}")
            continue

        actual_digest = sha256_file(file_path)
        if actual_digest != expected_digest:
            errors.append(
                f"SHA256 mismatch for {rel_path}: expected={expected_digest} actual={actual_digest}"
            )

    return ValidationResult(ok=not errors, errors=errors, warnings=warnings)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/validate_evidence_bundle.py",
        description="Validate evidence bundle integrity (required files + manifest.sha256 hashes).",
    )
    parser.add_argument("bundle_dir", type=str, help="Path to evidence bundle directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    result = validate_bundle(args.bundle_dir)

    if result.warnings:
        for w in result.warnings:
            print(f"WARN: {w}")

    if result.ok:
        print("PASS: evidence bundle is valid")
        return 0

    print("FAIL: evidence bundle is invalid")
    for e in result.errors:
        print(f"- {e}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
