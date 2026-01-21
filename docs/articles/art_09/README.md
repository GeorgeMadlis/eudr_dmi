# Article 09 — Inspection Notes (Placeholder)

## Purpose and boundary
This document defines the inspection-oriented evidence expectations for obligations mapped to Article 09 (placeholder reference). It specifies what an inspector should verify and where the corresponding evidence should be found in the evidence bundle.

Boundary:
- This project consumes `geospatial_dmi` as the upstream platform for data/services.
- This document does not describe, restate, or duplicate `geospatial_dmi` architecture.
- Evidence requirements here are project-level conventions and MUST be traceable to the spine.

## Out of scope
- Any implementation details inside `geospatial_dmi`.
- Reproducing upstream dataset/service catalogue details.
- Legal advice or non-testable interpretations.

## In-scope / Out-of-scope

| In-scope | Out-of-scope |
|---|---|
| Article 09 obligations mapped in the spine (TODO: add exact references). | Any implementation details inside `geospatial_dmi`. |
| Evidence artifacts and acceptance criteria used for inspection. | Reproducing upstream dataset/service catalogue details. |
| Determinism and verification rules applicable to Article 09 artifacts. | Legal advice or non-testable interpretations. |

## Evidence Outputs (File Names + Semantics)
These artifacts are expected to exist inside a compliant evidence bundle (see [docs/20_evidence_bundle_spec.md](../../20_evidence_bundle_spec.md)).

| Artifact | Semantics | Acceptance criteria |
|---|---|---|
| `outputs/articles/art_09.json` (TODO: finalize path/name) | Article 09 control-level results, including statuses and evidence references. | File is present; parseable JSON; references only in-bundle paths; control ids map to the spine. |
| `outputs/summary.json` | Run-level outcome summary including PASS/FAIL/UNDETERMINED and reasons. | `status` valid; includes references to Article 09 controls when applicable. |
| `manifest.json` + `hashes.sha256` | Integrity and completeness proof for all artifacts. | Hashes recompute and match; manifest lists Article 09 artifacts. |
| `provenance/provenance.json` | Provenance records for dependencies used by Article 09 checks. | Required provenance fields present for each dependency used by this Article. |

## How to run (TODO)
Commands are intentionally placeholders until the generator interface is finalized.

1. Preflight
   - `TODO_COMMAND_PREPARE_ENV`
   - `TODO_COMMAND_VALIDATE_INPUTS`
2. Generate Article 09 evidence
   - `TODO_COMMAND_GENERATE_ART_09_EVIDENCE`
3. Write/refresh manifest and hashes
   - `TODO_COMMAND_WRITE_MANIFEST`
   - `TODO_COMMAND_WRITE_HASHES`

## How to Inspect Evidence (Step-by-step)
1. Locate the evidence bundle root: `TODO_RELATIVE_PATH_TO_EVIDENCE_BUNDLES/<bundle_id>/`.
2. Verify bundle integrity:
   - Recompute SHA-256 for each file referenced by `hashes.sha256` (see [docs/30_runbook.md](../../30_runbook.md)).
   - Confirm `manifest.json` lists `outputs/articles/art_09.json` (or the finalized equivalent).
3. Inspect Article 09 results:
   - Open `outputs/articles/art_09.json`.
   - Confirm each control result references an obligation/control id present in the spine.
4. Trace evidence references:
   - For each control marked FAIL or UNDETERMINED, open the referenced artifacts and confirm the reason is supported.
5. Confirm summary consistency:
   - Check `outputs/summary.json` includes or links to Article 09 outcomes where applicable.

TODO: Replace the placeholder artifact name/path once the evidence contract is finalized.
