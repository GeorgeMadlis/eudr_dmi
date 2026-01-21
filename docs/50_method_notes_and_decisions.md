# Method Notes and Decisions

## Decision Log
Records method and policy decisions that affect evidence production or interpretation.

| Decision ID | Topic | Decision | Rationale | Impacted Evidence | Version Introduced | Review Date |
|---|---|---|---|---|---|---|
| DEC-0001 | TODO_TOPIC | TODO_DECISION | TODO_RATIONALE | TODO_EVIDENCE_ARTIFACTS (e.g., `outputs/summary.json`) | TODO_VERSION | TODO_REVIEW_DATE |

## Uncertainty Handling Policy
This policy governs how the project reports uncertainty in outputs.

Policy (concrete, minimal):
- If required evidence artifacts are missing, invalid, or unverifiable, the outcome MUST be `FAIL` unless a documented exception allows `UNDETERMINED` (TODO: define exception conditions).
- If upstream sources conflict and the conflict cannot be resolved by a deterministic rule, the outcome MUST be `UNDETERMINED` and MUST include:
  - the conflicting sources,
  - the impacted control objectives,
  - the reason the conflict cannot be resolved, and
  - the decision reference(s) from this log.
- If uncertainty can be bounded by a documented conservative rule (TODO: define), the outcome MAY be `FAIL` with explicit reasoning.

## Conflict Resolution Policy Across Sources
When multiple sources provide overlapping signals:
1. Prefer the source with the strongest documented provenance and currency (as defined in the dependency register).
2. If both sources meet provenance/currency requirements, apply a deterministic tie-break rule (TODO: define, e.g., priority order by catalogue ID).
3. If tie-break cannot resolve, record as conflict and produce `UNDETERMINED` with evidence references.

## Inspector Checklist
- Any `UNDETERMINED` outcome references this policy and a decision entry.
- Any change in method logic is logged and mapped to impacted evidence and the spine.
