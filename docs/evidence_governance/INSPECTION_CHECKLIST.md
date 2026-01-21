# Inspection Checklist (Project-Level)

## Purpose
Provides a step-by-step checklist for inspecting an evidence bundle produced under this project’s conventions.

## Boundaries
- This project consumes `geospatial_dmi`.
- This checklist does not document `geospatial_dmi` architecture; it checks only project-owned evidence artifacts.

## Checklist

### 1) Identify the Bundle Under Review
- Bundle root: `<root>/<YYYY-MM-DD>/<bundle_id>/`
   - Default `<root>`: `audit/evidence/`
   - Override: `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
- Record: bundle id, operator ref, run date, and method version.

Acceptance criteria:
- Bundle root contains `manifest.json` and `hashes.sha256`.

### 2) Verify Integrity (Hashes)
1. Recompute SHA-256 for each artifact referenced by `hashes.sha256`.
2. Confirm each computed hash matches.

Acceptance criteria:
- All hashes match; no missing artifacts.

### 3) Verify Completeness (Manifest)
1. Parse `manifest.json`.
2. Confirm required fields exist (producer, inputs, dependencies, outcome, artifacts).
3. Confirm each artifact `path` exists and is within the bundle root.

Acceptance criteria:
- Manifest is parseable; required fields present; no invalid paths.

### 4) Verify Provenance
1. Open `provenance/provenance.json`.
2. For each dependency listed, confirm required provenance fields per [docs/40_data_dependency_register.md](../40_data_dependency_register.md).

Acceptance criteria:
- Required provenance fields present; currency expectations met or exceptions documented.

### 5) Verify Outcome Traceability
1. Open `outputs/summary.json`.
2. For each control referenced, locate the corresponding artifact(s) and confirm evidence references resolve.
3. Cross-check control objectives and acceptance criteria in [docs/10_policy_to_evidence_spine.md](../10_policy_to_evidence_spine.md).

Acceptance criteria:
- Each control outcome is supported by referenced evidence artifacts; FAIL/UNDETERMINED include reasons.

### 6) Article-Specific Verification (09/10/11)
1. If present, open:
   - `outputs/articles/art_09.json` (TODO: finalize)
   - `outputs/articles/art_10.json` (TODO: finalize)
   - `outputs/articles/art_11.json` (TODO: finalize)
2. Confirm control ids map to spine; evidence references resolve.

Acceptance criteria:
- Article artifacts (if applicable) are present, hashed, and traceable to the spine.

### 7) Reproducibility / Determinism (Optional but Recommended)
- Re-run with identical inputs and pinned dependencies (see [docs/30_runbook.md](../30_runbook.md)).

Acceptance criteria:
- Outputs are equivalent under determinism rules; any allowed differences are documented.
