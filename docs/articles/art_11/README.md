# Article 11 — Inspection Notes (Placeholder)

## Purpose and boundary
This document defines the inspection-oriented evidence expectations for obligations mapped to Article 11 (placeholder reference). It focuses on what to check, where to find it in the evidence bundle, and acceptance criteria.

Boundary:
- This project is informed by `geospatial_dmi` and may adopt selected components from it into `eudr_dmi` with explicit provenance.
- This document does not describe, restate, or duplicate `geospatial_dmi` architecture.
- Article 11 evidence requirements MUST be traceable to the policy-to-evidence spine.

## Out of scope
- `geospatial_dmi` architecture and internal implementation details.
- Copying upstream MCP/server logic or platform code.
- Speculative claims without verifiable artifacts.

## In-scope / Out-of-scope

| In-scope | Out-of-scope |
|---|---|
| Article 11 obligations mapped in the spine (TODO: add exact references). | `geospatial_dmi` architecture and internal implementation details. |
| Article 11-specific evidence artifacts, acceptance criteria, and inspection procedure. | Copying upstream MCP/server logic or platform code. |
| Deterministic artifact generation and validation rules. | Speculative claims without verifiable artifacts. |

## Evidence Outputs (File Names + Semantics)
Expected artifacts inside the evidence bundle (see [docs/20_evidence_bundle_spec.md](../../20_evidence_bundle_spec.md)).

| Artifact | Semantics | Acceptance criteria |
|---|---|---|
| `outputs/articles/art_11.json` (TODO: finalize path/name) | Article 11 control-level results with evidence references. | Present; parseable; stable ordering; evidence references resolve. |
| `outputs/summary.json` | Run-level outcome summary. | Includes reasons and evidence refs for FAIL/UNDETERMINED controls. |
| `manifest.json` + `hashes.sha256` | Integrity and completeness. | Hashes match; no missing/extra artifacts outside manifest policy. |
| `provenance/provenance.json` | Dependency provenance for Article 11 checks. | Provenance fields complete; aligns to the dependency register. |

## How to run (TODO)
Commands are intentionally placeholders until the generator interface is finalized.

1. Preflight
   - `TODO_COMMAND_PREPARE_ENV`
   - `TODO_COMMAND_VALIDATE_INPUTS`
2. Generate Article 11 evidence
   - `TODO_COMMAND_GENERATE_ART_11_EVIDENCE`
3. Write/refresh manifest and hashes
   - `TODO_COMMAND_WRITE_MANIFEST`
   - `TODO_COMMAND_WRITE_HASHES`

## How to Inspect Evidence (Step-by-step)
1. Locate the evidence bundle root: `TODO_RELATIVE_PATH_TO_EVIDENCE_BUNDLES/<bundle_id>/`.
2. Verify integrity:
   - Confirm `manifest.json` and `hashes.sha256` validate.
3. Inspect Article 11 results:
   - Open `outputs/articles/art_11.json`.
   - For each control, confirm the evidence references are present and hashed.
4. Validate provenance alignment:
   - Cross-check `provenance/provenance.json` against [docs/40_data_dependency_register.md](../../40_data_dependency_register.md).
5. Check summary alignment:
   - Confirm the overall `outputs/summary.json` status is consistent with Article 11 control outcomes.

TODO: Replace the placeholder artifact name/path once the evidence contract is finalized.
