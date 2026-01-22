# Evidence Contract (Project-Level)

## Purpose
This contract defines the minimum obligations for any generator or workflow that produces evidence bundles for this project, and the minimum expectations for inspection. It is project-level and does not describe the consumed platform `geospatial_dmi`.

## Boundaries
- This project is informed by `geospatial_dmi` and may adopt selected components/patterns from it (with explicit provenance), while continuing to reference canonical entrypoints where appropriate (TODO: reference links/paths).
- Do not copy, restate, or re-document `geospatial_dmi` architecture here.

## Contract Parties

| Party | Responsibility |
|---|---|
| Evidence Producer (agent/workflow) | Produces deterministic evidence bundles with required artifacts, provenance, and integrity metadata. |
| Inspector/Auditor | Verifies integrity, completeness, provenance, and traceability to control objectives using acceptance criteria. |

## Required Bundle Invariants
These are non-negotiable inspection requirements.

| Invariant | Requirement | Where to check | Acceptance criteria |
|---|---|---|---|
| Completeness | All required files exist per bundle spec. | [docs/20_evidence_bundle_spec.md](../20_evidence_bundle_spec.md) | Required artifacts present; no missing required directories/files. |
| Integrity | Hashes and manifest provide independent verification. | `hashes.sha256`, `manifest.json` | Recomputed SHA-256 matches; manifest lists each artifact. |
| Traceability | Control results reference obligations/control objectives in the spine. | `outputs/*`, spine | Each control id maps to spine rows; each has evidence references. |
| Provenance | Each used dependency has required provenance fields. | `provenance/provenance.json` | Fields present and non-empty, unless explicitly allowed nulls are documented. |
| Determinism | Re-runs with identical inputs + pinned dependencies are equivalent. | Runbook verification | Outputs are byte-identical under documented determinism rules. |

## Article Evidence Conventions (Placeholders)
- Article-specific outputs MUST be defined and versioned.
- Placeholder convention (to be finalized):
  - `outputs/articles/art_09.json`
  - `outputs/articles/art_10.json`
  - `outputs/articles/art_11.json`

TODO: Once finalized, update:
- [docs/20_evidence_bundle_spec.md](../20_evidence_bundle_spec.md) to include article-specific artifacts.
- [docs/10_policy_to_evidence_spine.md](../10_policy_to_evidence_spine.md) to map obligations → these artifacts with acceptance criteria.

## Deterministic Serialization Rules
- JSON output MUST be UTF-8 encoded.
- Object key ordering MUST be stable (define canonicalization approach; TODO).
- Arrays MUST be deterministically ordered and documented (sort keys; TODO).
- Numeric formatting MUST be consistent (precision/rounding; TODO).
