# Documentation Index

## Read in This Order
1. [docs/README.md](README.md)
1. [docs/architecture/decision_records/ADR-0001-project-scope.md](architecture/decision_records/ADR-0001-project-scope.md)
2. [docs/overview.md](overview.md)
3. [docs/architecture/digital_twin_model.md](architecture/digital_twin_model.md)
4. [docs/architecture/adoption_policy.md](architecture/adoption_policy.md)
5. [docs/regulation/sources.md](regulation/sources.md)
6. [docs/regulation/policy_to_evidence_spine.md](regulation/policy_to_evidence_spine.md)
7. [docs/architecture/evidence_contract.md](architecture/evidence_contract.md)
8. [docs/architecture/evidence_bundle_spec.md](architecture/evidence_bundle_spec.md)
9. [docs/architecture/dependency_register.md](architecture/dependency_register.md)
10. [docs/architecture/method_notes_and_decisions.md](architecture/method_notes_and_decisions.md)
11. [docs/operations/runbooks.md](operations/runbooks.md)
12. [docs/operations/inspection_checklist.md](operations/inspection_checklist.md)
13. [docs/architecture/risk_register.md](architecture/risk_register.md)
14. [docs/architecture/change_control.md](architecture/change_control.md)
15. [docs/glossary.md](glossary.md)
16. [docs/articles/eudr_article_summaries.md](articles/eudr_article_summaries.md)

## Document Map

| Document | Purpose | When to use |
|---|---|---|
| [docs/overview.md](overview.md) | Scope, definitions, operator inputs, and standardized outcome semantics. | Onboarding and audit scoping. |
| [docs/architecture/digital_twin_model.md](architecture/digital_twin_model.md) | Inspection model for the EUDR Digital Twin (mirroring, change detection, and triggering). | When integrating downstream automation or explaining update triggers. |
| [docs/architecture/adoption_policy.md](architecture/adoption_policy.md) | Provenance requirements for adopting external components (adopt-and-evolve) and prohibited coupling patterns. | When copying in upstream code or reviewing dependencies. |
| [docs/regulation/sources.md](regulation/sources.md) | Deterministic EUR-Lex mirroring workflow and hashed source registry. | When validating regulation snapshots and change detection. |
| [docs/regulation/policy_to_evidence_spine.md](regulation/policy_to_evidence_spine.md) | Obligation → objective → artifact → acceptance criteria mapping. | During control testing and audit walkthroughs. |
| [docs/architecture/evidence_contract.md](architecture/evidence_contract.md) | Evidence contract: what artifacts exist and what they mean. | When implementing or reviewing evidence producers/consumers. |
| [docs/architecture/evidence_bundle_spec.md](architecture/evidence_bundle_spec.md) | Evidence bundle layout, required files, hashing and determinism rules. | When validating bundles or building generators/validators. |
| [docs/operations/runbooks.md](operations/runbooks.md) | Operator runbook: preflight, execution, verification, troubleshooting. | Routine runs and incident response. |
| [docs/operations/secrets_handling.md](operations/secrets_handling.md) | Cookie jar storage outside the repo and operational handling. | When interactive browser sessions/cookies are required for WAF-safe sourcing. |
| [docs/glossary.md](glossary.md) | Project terminology. | Quick reference. |
