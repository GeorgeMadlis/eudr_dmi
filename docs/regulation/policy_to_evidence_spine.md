# Policy-to-Evidence Spine

## Purpose
This document provides the master mapping from obligations (e.g., regulatory articles) to control objectives and the concrete evidence artifacts that support inspection.

## Boundary
This repo does not describe upstream platform internals (including `geospatial_dmi`). The “Produced By” column references agents/workflows and canonical entrypoints only.

## Master Spine Table

| Obligation/Article | Control Objective | Evidence Artifact | Acceptance Criteria | Produced By (agent/workflow) | Evidence Path | Notes |
|---|---|---|---|---|---|---|
| TODO_ARTICLE_REF_001 | TODO_OBJECTIVE_STATEMENT | `summary.json` | Outcome present; status ∈ {PASS, FAIL, UNDETERMINED}; reasons present for UNDETERMINED. | TODO_AGENT_OR_WORKFLOW_NAME | `outputs/summary.json` | TODO_UPDATE_NOTES |
| TODO_ARTICLE_REF_002 | TODO_OBJECTIVE_STATEMENT | `manifest.json` + `hashes.sha256` | Manifest parses; all referenced files exist; all SHA-256 hashes match; no extra files outside allowlist (if applicable). | TODO_AGENT_OR_WORKFLOW_NAME | `manifest.json`, `hashes.sha256` | TODO_UPDATE_NOTES |
| TODO_ARTICLE_REF_003 | TODO_OBJECTIVE_STATEMENT | Provenance fields for each dependency | Provenance fields present and non-empty per dependency register; timestamps within expected currency window. | TODO_AGENT_OR_WORKFLOW_NAME | `provenance/provenance.json` | TODO_UPDATE_NOTES |
| TODO_ARTICLE_REF_004 | TODO_OBJECTIVE_STATEMENT | Decision log excerpt (if invoked) | If uncertainty/conflict policy triggered, decision is recorded and referenced by summary. | TODO_AGENT_OR_WORKFLOW_NAME | `method/decisions_applied.json` | TODO_UPDATE_NOTES |
| TODO_ARTICLE_REF_DEFINITIONS | Definition consistency / interpretability constraint (scaffold) | `definition_comparison.json` + `dependencies.json` | Artifacts present; parseable JSON; deterministic ordering; `outcome` defaults to `UNKNOWN` until extraction implemented; provenance hashes recorded for dependency run. | `scripts/task3/definition_comparison_control.py` | `method/definition_comparison.json`, `provenance/dependencies.json` | Scaffold for later NLP extraction and mismatch logic. |

### Update Notes (How to Maintain the Spine)
- Each new obligation/control MUST add a row and MUST reference a concrete artifact and acceptance criteria.
- Each evidence artifact MUST be defined in [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md).
- TODO: Add canonical references/links to any upstream entrypoints used (without describing upstream architecture).

## Inspector Checklist
- Each control objective has at least one artifact with objective acceptance criteria.
- Evidence paths are relative to the bundle root and resolve to real files.
- “Produced By” identifies the responsible workflow/agent version (recorded in manifest).
