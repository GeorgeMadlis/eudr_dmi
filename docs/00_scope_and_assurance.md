# Scope and Assurance

## Scope

| In-scope | Out-of-scope |
|---|---|
| Definition of evidence bundle contents and verification rules for EUDR-facing outputs. | Implementation details and architecture of the `geospatial_dmi` platform. |
| Control-to-evidence mapping (obligation → objective → artifact → acceptance criteria). | Reproducing the full upstream data catalogue or service specs of `geospatial_dmi`. |
| Operator inputs, runbook steps, and reproducibility checks (manifest + hashes). | Legal interpretation of EUDR obligations beyond documenting traceable checks. |
| Registers for dependencies, decisions, risks, and change control. | Product UI/UX, pipeline orchestration internals, or infrastructure design. |

## Definitions Used in This Project

| Term | Definition |
|---|---|
| Evidence bundle | A deterministic directory of artifacts produced for a specific run and inputs, with a manifest and cryptographic hashes enabling independent verification. |
| Operator | The person or automated actor executing the runbook and providing required inputs. |
| Control objective | A testable statement that supports an obligation and can be verified from evidence artifacts. |
| Acceptance criteria | Observable, testable conditions an auditor can apply to an artifact to determine whether the control objective is met. |
| PASS / FAIL / UNDETERMINED | Standardized outcome semantics (see below). |
| Consumed platform | The upstream system `geospatial_dmi` used to obtain data/services; canonical entrypoints are referenced but not duplicated here. |

## Inputs Required from Operator
The operator must provide and record the following inputs as part of each run:

| Input | Description | Format / Constraints | Where recorded |
|---|---|---|---|
| Geometry | Area of Interest (AOI) for assessment. | `TODO_GEOMETRY_FORMAT` (e.g., GeoJSON polygon); must be valid and non-self-intersecting. | Evidence bundle: `inputs/geometry.*` and `manifest.json` fields. |
| Dates | Relevant temporal window for evaluation. | `TODO_DATE_POLICY` (e.g., start/end in ISO-8601, timezone handling). | Evidence bundle: `inputs/parameters.json` and `manifest.json`. |
| Commodity context | Commodity and any relevant classification needed for checks. | `TODO_COMMODITY_TAXONOMY` | Evidence bundle: `inputs/parameters.json`. |
| Run identification | Operator identity, purpose, and ticket/reference. | `TODO_FORMAT` | Evidence bundle: `manifest.json` fields. |

## Output Semantics
Outcomes are expressed as one of: PASS, FAIL, UNDETERMINED.

| Outcome | Meaning | Criteria |
|---|---|---|
| PASS | All required checks executed and acceptance criteria met. | No missing required artifacts; all validation steps pass; no control objective indicates failure. |
| FAIL | A required check executed and indicates non-compliance, or required evidence is missing/invalid. | Any control objective acceptance criteria not met, or required artifacts absent/unverifiable. |
| UNDETERMINED | The run completed but cannot reach PASS/FAIL due to known limitations, missing upstream inputs, or conflicts unresolved by policy. | Explicitly recorded reason(s) and affected controls; artifacts exist to justify the status. |

### What to Check (Inspector View)
- Confirm the evidence bundle contains required inputs, outputs, and verification artifacts (manifest + hashes).
- Confirm the reported outcome is supported by artifacts mapped in the spine.
- Confirm any UNDETERMINED outcome includes explicit reasons and references to impacted controls.

### Where to Find It
- Outcome summary: `TODO_EVIDENCE_BUNDLE_RELATIVE_PATH/outputs/summary.json`
- Manifest and hashes: `TODO_EVIDENCE_BUNDLE_RELATIVE_PATH/manifest.json`, `TODO_EVIDENCE_BUNDLE_RELATIVE_PATH/hashes.sha256`
- Spine mapping: [10_policy_to_evidence_spine.md](10_policy_to_evidence_spine.md)

## Assumptions and Limitations
The following must be explicit and treated as audit-relevant constraints:

| Assumption / Limitation | Description | Impact on interpretation | How evidenced |
|---|---|---|---|
| Upstream platform reliance | Data/services are obtained from `geospatial_dmi` via canonical entrypoints. | Evidence validity depends on upstream provenance and availability. | Dependency register references, provenance fields in bundle (TODO). |
| Temporal alignment | The date window reflects the assessment period; timezones and cutoffs are consistently applied. | Incorrect date handling may change outcomes. | `inputs/parameters.json` + determinism rules in [20_evidence_bundle_spec.md](20_evidence_bundle_spec.md). |
| Geometry validity | AOI geometry must be valid and within acceptable size/complexity. | Invalid geometry can cause errors or incorrect results. | Stored geometry artifact + preflight checks in [30_runbook.md](30_runbook.md). |
| Conflict / uncertainty policy | Conflicting signals across sources are handled by a fixed policy. | May result in UNDETERMINED or conservative FAIL depending on policy. | Decision log + method policies in [50_method_notes_and_decisions.md](50_method_notes_and_decisions.md). |

TODO: Add any project-specific limitations once confirmed (e.g., coverage gaps, resolution thresholds, known lags).
