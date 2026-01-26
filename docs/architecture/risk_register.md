# Risk Register

## Risk Table

| Risk ID | Description | Likelihood | Impact | Control/Mitigation | How Control is Evidenced | Residual Risk |
|---|---|---|---|---|---|---|
| R-001 | Data drift in upstream datasets/services changes outcomes over time. | TODO_LOW_MED_HIGH | TODO_LOW_MED_HIGH | Pin dependency versions where possible; record provenance and currency; rerun equivalence checks. | `provenance/provenance.json`; manifest dependency list; rerun logs (TODO). | TODO_RESIDUAL |
| R-002 | Regulatory change alters obligations or required evidence. | TODO_LOW_MED_HIGH | TODO_LOW_MED_HIGH | Change control process; update spine and evidence spec; versioning and release checklist. | [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md); [docs/architecture/change_control.md](change_control.md) | TODO_RESIDUAL |
| R-003 | Non-deterministic outputs prevent reproducible inspection. | TODO_LOW_MED_HIGH | TODO_LOW_MED_HIGH | Determinism rules; canonical serialization; hash verification and rerun equivalence. | `hashes.sha256`; verification steps in [docs/operations/runbooks.md](../operations/runbooks.md) | TODO_RESIDUAL |
| R-004 | Missing or incomplete provenance undermines traceability. | TODO_LOW_MED_HIGH | TODO_LOW_MED_HIGH | Dependency register; required provenance fields; preflight validation. | [docs/architecture/dependency_register.md](dependency_register.md); `provenance/provenance.json` | TODO_RESIDUAL |
| R-005 | Operator input errors (geometry/dates/commodity) cause incorrect outcomes. | TODO_LOW_MED_HIGH | TODO_LOW_MED_HIGH | Preflight validation; strict input recording; review checklist. | `inputs/parameters.json`; `inputs/geometry.*`; run log | TODO_RESIDUAL |

## Inspector Notes
- Each mitigation MUST be tied to an observable artifact (hashes, manifest, provenance, logs, or documented decisions).
- Residual risk rationale MUST be recorded when risks are accepted (TODO: define acceptance workflow).
