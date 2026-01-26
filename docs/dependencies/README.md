# Dependency Definitions

This section covers dependency-definition sourcing and the deterministic dependency-definition mirroring workflow.

## Registry files

- [docs/dependencies/sources.json](sources.json)
  - Canonical registry of dependency definition sources.
  - Determinism requirement: `generated_at` is always `null`.
- [docs/dependencies/sources.md](sources.md)
  - Human-readable table view of the same registry.

## Tools and scripts

- Fetch/verify tool: [tools/dependencies/acquire_and_hash.py](../../tools/dependencies/acquire_and_hash.py)
  - Writes per-source per-date run folders with:
    - `artifact.bin`
    - `headers.txt` (optional; allowlisted headers only)
    - `metadata.json` (deterministic; no timestamps)
    - `manifest.sha256` (deterministic ordering)
- Fetch wrapper (operator entrypoint): [scripts/fetch_dependency_definitions.py](../../scripts/fetch_dependency_definitions.py)
  - Runs fetch for each source in the registry and also writes `run_summary.json` in each run folder.
- Watcher: [scripts/watch_dependency_definitions.py](../../scripts/watch_dependency_definitions.py)
  - Compares `artifact_sha256` for the latest run vs the previous run and emits a digital twin trigger on change.

## Scoped quality gate

The repository may have legacy full-repo lint debt (e.g., `ruff check .` can fail due to unrelated areas).
However, the dependency-definition mirroring and the Task3 definition-comparison surface area must remain ruff-clean.

Before submitting PRs that touch dependency mirroring or definition comparison, run:

python tools/ci/quality_scoped.py

Determinism is enforced via a shared stable JSON helper ([src/eudr_dmi/evidence/stable_json.py](../../src/eudr_dmi/evidence/stable_json.py));
the scoped gate exists to protect these conventions from regression.

## Canonical audit locations

Dependency definition snapshots are written under each source’s `server_local_path` as:

- `<server_local_path>/<YYYY-MM-DD>/`

Typical server defaults (see the registry):

- `/Users/server/audit/eudr_dmi/dependencies/<source_id>/<YYYY-MM-DD>/`

Watcher triggers are written to the canonical folder:

- `/Users/server/audit/eudr_dmi/digital_twin_triggers/dependencies/<YYYY-MM-DD>/digital_twin_trigger.json`

## Operator commands

Fetch all dependency definitions for a given date:

python scripts/fetch_dependency_definitions.py --date 2026-01-25

Verify (no network):

python tools/dependencies/acquire_and_hash.py --verify --date 2026-01-25

Watch for changes:

python scripts/watch_dependency_definitions.py --date 2026-01-25

### Verify single source

If multiple sources exist in the registry, verify is commonly performed per-source:

- `python tools/dependencies/acquire_and_hash.py --verify --id <source_id> --date <YYYY-MM-DD>`

## Watcher exit codes

- `0`: no change detected
- `2`: change detected (trigger written)
- `1`: error / insufficient history

## Integration into Task3 evidence generation

The dependency-definition snapshot is consumed by the Task3 “Definition consistency / interpretability constraint” scaffold:

- Control runner: [scripts/task3/definition_comparison_control.py](../../scripts/task3/definition_comparison_control.py)
- Evidence artifacts written under an evidence bundle root:
  - `provenance/dependencies.json`
  - `method/definition_comparison.json`

These artifacts are referenced in the spine mapping:

- [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)
