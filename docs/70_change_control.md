# Change Control

## Versioning Policy (Docs + Evidence Schema)

| Item | Versioning rule | Where recorded | Acceptance criteria |
|---|---|---|---|
| Documentation set | Semantic version (MAJOR.MINOR.PATCH) or git tag (TODO: decide). | `TODO_RELEASE_NOTES_LOCATION` | Version is discoverable and referenced by evidence bundles. |
| Evidence bundle schema | Semantic version; increment according to change category. | `method/method_version.json` and `manifest.json` | Bundle declares schema version; validators use the correct version. |
| Spine mapping | Versioned alongside schema. | `method/method_version.json` (`spine_version`) | Bundle references exact spine version used. |

## Change Categories

| Category | Examples | Required approvals | Version impact |
|---|---|---|---|
| Doc-only | Clarifications, typos, formatting. | TODO_APPROVER_ROLE | PATCH for docs only (no schema impact). |
| Method change | New decision policy, new evaluation rule affecting outcomes. | TODO_APPROVER_ROLE(S) | MINOR or MAJOR depending on impact; update method version. |
| Evidence schema change | Add/remove required fields/files; change hashing rules. | TODO_APPROVER_ROLE(S) | MINOR for backward-compatible additions; MAJOR for breaking changes. |

## Required Updates When Changes Occur
- Update the spine: [10_policy_to_evidence_spine.md](10_policy_to_evidence_spine.md)
  - Add/modify rows for impacted obligations, objectives, artifacts, and acceptance criteria.
- Update method notes: [50_method_notes_and_decisions.md](50_method_notes_and_decisions.md)
  - Add a decision log entry for method or policy changes.
- Update evidence spec: [20_evidence_bundle_spec.md](20_evidence_bundle_spec.md)
  - If artifacts or verification rules change.
- Update risk register: [60_risk_register.md](60_risk_register.md)
  - If new risk/control emerges or residual risk changes.

## Backward Compatibility Rules for Evidence Bundles
- Backward-compatible changes MUST NOT invalidate previously produced bundles.
- Validators MUST support at least the last `TODO_N` minor versions (TODO: decide).
- If a breaking change is required:
  - increment MAJOR version,
  - document migration guidance,
  - preserve the ability to verify historical bundles using the schema version declared in each bundle.

## Release Checklist (Audit Continuity)

| Step | What to do | Acceptance criteria |
|---|---|---|
| Update version | Bump doc/schema/method versions as applicable. | Versions updated and referenced consistently. |
| Update spine | Verify obligations → evidence mapping is current. | Spine table updated; acceptance criteria testable. |
| Update spec | Ensure bundle spec matches generated artifacts. | Spec reflects reality; no undocumented artifacts. |
| Update decision log | Record method/policy decisions. | Decision entries complete (rationale, impacted evidence). |
| Run verification | Generate a bundle and perform hash/manifest checks. | All verification steps pass; rerun equivalence documented. |
| Preserve continuity | Ensure prior bundles remain verifiable. | Historical validators/configs retained; compatibility statement updated. |

TODO: Define the release artifact location and link it here.
