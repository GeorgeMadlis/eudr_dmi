# Article 10 — Inspection Notes (Placeholder)

## Purpose and boundary
This document defines the inspection-oriented evidence expectations for obligations mapped to Article 10 (placeholder reference). It specifies what evidence must exist for inspection and how to apply acceptance criteria.

Boundary:
- This project is informed by `geospatial_dmi` and may adopt selected components from it into `eudr_dmi` with explicit provenance.
- This document does not describe, restate, or duplicate `geospatial_dmi` architecture.
- Evidence requirements here MUST be consistent with the bundle spec and the policy-to-evidence spine.

## Out of scope
- Any implementation details inside `geospatial_dmi`.
- Duplicating upstream service specifications or dataset descriptions.
- Non-testable narrative claims.

## In-scope / Out-of-scope

| In-scope | Out-of-scope |
|---|---|
| Article 10 obligations mapped in the spine (TODO: add exact references). | Any implementation details inside `geospatial_dmi`. |
| Article 10-specific evidence artifacts and acceptance criteria. | Duplicating upstream service specifications or dataset descriptions. |
| Deterministic evidence generation and verification steps. | Non-testable narrative claims. |

## Evidence Outputs (File Names + Semantics)
Expected artifacts inside the evidence bundle (see [docs/20_evidence_bundle_spec.md](../../20_evidence_bundle_spec.md)).

| Artifact | Semantics | Acceptance criteria |
|---|---|---|
| `outputs/articles/art_10.json` (TODO: finalize path/name) | Article 10 control-level results with evidence references. | Present; parseable; stable ordering; references in-bundle paths; maps to spine controls. |
| `outputs/summary.json` | Run-level outcome summary. | Reflects Article 10 control statuses and reasons where relevant. |
| `manifest.json` + `hashes.sha256` | Integrity and completeness. | Hashes match; Article 10 artifacts are included. |
| `provenance/provenance.json` | Dependency provenance for Article 10 checks. | Required provenance fields complete and within expected currency constraints (or documented exception). |

## How to run (TODO)
Commands are intentionally placeholders until the generator interface is finalized.

1. Preflight
   - `TODO_COMMAND_PREPARE_ENV`
   - `TODO_COMMAND_VALIDATE_INPUTS`
2. Generate Article 10 evidence
   - `TODO_COMMAND_GENERATE_ART_10_EVIDENCE`
3. Write/refresh manifest and hashes
   - `TODO_COMMAND_WRITE_MANIFEST`
   - `TODO_COMMAND_WRITE_HASHES`

## How to Inspect Evidence (Step-by-step)
1. Locate the evidence bundle root: `<root>/<YYYY-MM-DD>/<bundle_id>/`.
   - Default `<root>`: `audit/evidence/`
   - Override: `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
2. Verify integrity:
   - Recompute SHA-256 and confirm manifest completeness.
3. Inspect Article 10 results:
   - Open `outputs/articles/art_10.json`.
   - Confirm control ids link to spine rows and acceptance criteria are testable.
4. Validate provenance:
   - Confirm dependencies used are listed in the dependency register and provenance fields are populated.
5. Confirm overall consistency:
   - Check `outputs/summary.json` is consistent with Article 10 control outcomes.

TODO: Replace the placeholder artifact name/path once the evidence contract is finalized.
