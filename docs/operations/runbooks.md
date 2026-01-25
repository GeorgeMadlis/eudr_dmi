# Runbook

## Evidence Root Policy
- Default evidence root (repo-local): `audit/evidence/`
- Override (server evidence root): `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
- Bundle layout: `<root>/<YYYY-MM-DD>/<bundle_id>/`

Notes:
- `<root>` resolves to `$EUDR_DMI_EVIDENCE_ROOT` if set; otherwise `audit/evidence/`.
- `<bundle_root>` refers to a single bundle directory: `<root>/<YYYY-MM-DD>/<bundle_id>/`.

## Preflight Checklist

| Item | What to check | Where to find it | Acceptance criteria |
|---|---|---|---|
| Operator inputs available | Geometry, date window, commodity context, operator ref. | Operator ticket / request record (TODO) | All required inputs complete and recorded. |
| Upstream access | Ability to reach required upstream entrypoints (datasets/services; may include adopted components from `geospatial_dmi`). | [docs/architecture/dependency_register.md](../architecture/dependency_register.md) | Access confirmed; credentials and network prerequisites satisfied. |
| Regulation snapshot current | Regulation mirror has a recent run folder; LSU/watch is not stale. | [docs/regulation/sources.md](../regulation/sources.md) | Latest run folder exists; `manifest.sha256` verifies; `needs_update` is understood/handled. |
| Dependency pinning | Dataset/service versions pinned as required. | `TODO_CONFIG_FILE_OR_ENV_VARS` | Versions/IDs recorded; reruns are feasible. |
| Workspace cleanliness | Evidence root writable; no conflicting bundle id. | `audit/evidence/` (or `$EUDR_DMI_EVIDENCE_ROOT`) | Evidence root exists and is writable; selected `<bundle_root>` is new/empty. |

## Execution Steps (Placeholders)
1. Prepare environment
   - `TODO_COMMAND_TO_CREATE_ENV`
   - `TODO_COMMAND_TO_INSTALL_DEPENDENCIES`
2. Provide inputs
   - Choose a `<bundle_root>` at `<root>/<YYYY-MM-DD>/<bundle_id>/`
   - Place geometry at `<bundle_root>/inputs/geometry.<ext>`
   - Create `<bundle_root>/inputs/parameters.json`
3. Generate evidence bundle
   - `TODO_COMMAND_TO_GENERATE_BUNDLE`
4. Generate/update manifest and hashes
   - `TODO_COMMAND_TO_WRITE_MANIFEST`
   - `TODO_COMMAND_TO_WRITE_HASHES`

## Expected Outputs

| Output | Location | Acceptance criteria |
|---|---|---|
| Evidence bundle directory | `<root>/<YYYY-MM-DD>/<bundle_id>/` | Bundle contains all required files per [20_evidence_bundle_spec.md](20_evidence_bundle_spec.md). |
| Summary outcome | `<bundle_root>/outputs/summary.json` | `status` present and valid; evidence references resolve. |
| Provenance record | `<bundle_root>/provenance/provenance.json` | Contains required provenance fields for each dependency used. |
| Manifest + hashes | `<bundle_root>/manifest.json`, `<bundle_root>/hashes.sha256` | Parseable manifest; all hashes match on recomputation. |
| Run log | `<bundle_root>/logs/run.log` | Contains run start/end, operator ref, and any warnings/errors. |

## Verification Steps

### Hash / Manifest Checks
- Recompute hashes:
  - `TODO_COMMAND_TO_RECOMPUTE_SHA256`
- Validate manifest:
  - `TODO_COMMAND_TO_VALIDATE_MANIFEST`

Acceptance criteria:
- All hashes match `hashes.sha256` and the manifest.
- All manifest artifact paths exist and are within the bundle root.

### Rerun Equivalence (Determinism)
- Rerun using identical inputs and pinned dependencies:
  - `TODO_COMMAND_TO_RERUN_WITH_PINNED_DEPS`

Acceptance criteria:
- Outputs are byte-identical under the determinism rules in [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md).
- Any permitted differences (e.g., timestamps) are explicitly documented and excluded from equivalence checks.

## Troubleshooting

| Symptom | Likely cause | What to check | Remediation |
|---|---|---|---|
| Missing dependency provenance | Upstream call failed or provenance mapping incomplete. | `logs/run.log`; `provenance/provenance.json` | Fix upstream access or provenance extraction; rerun; record decision if unavoidable. |
| Hash mismatch | File modified post-generation or non-deterministic output. | Compare file timestamps; rerun equivalence. | Regenerate bundle; enforce determinism rules; lock formatting and ordering. |
| UNDETERMINED outcome | Conflicts across sources or missing upstream coverage. | `outputs/summary.json` reasons; method decision artifacts. | Apply uncertainty/conflict policy; record applied decisions; rerun if data becomes available. |
| Runtime failure | Environment/config error. | `logs/run.log`; `TODO_CONFIG` | Repair environment, update runbook, and record change if procedure changed. |
