# Documentation Index

## Read in This Order
1. [00_scope_and_assurance.md](00_scope_and_assurance.md)
2. [10_policy_to_evidence_spine.md](10_policy_to_evidence_spine.md)
3. [20_evidence_bundle_spec.md](20_evidence_bundle_spec.md)
4. [30_runbook.md](30_runbook.md)
5. [40_data_dependency_register.md](40_data_dependency_register.md)
6. [50_method_notes_and_decisions.md](50_method_notes_and_decisions.md)
7. [60_risk_register.md](60_risk_register.md)
8. [70_change_control.md](70_change_control.md)
9. [regulation_sources.md](regulation_sources.md)
10. [regulation_sources.json](regulation_sources.json)
11. [regulation_links.html](regulation_links.html)
12. [articles/eudr_article_summaries.md](articles/eudr_article_summaries.md)
13. [secrets_handling.md](secrets_handling.md)

## Document Map

| Document | Purpose | When to use |
|---|---|---|
| [00_scope_and_assurance.md](00_scope_and_assurance.md) | Defines scope, definitions, input requirements, output semantics, assumptions/limitations. | At onboarding, during audit scoping, and when interpreting outcomes. |
| [10_policy_to_evidence_spine.md](10_policy_to_evidence_spine.md) | Maps obligations to control objectives and concrete evidence artifacts. | For audit walkthroughs and control testing. |
| [20_evidence_bundle_spec.md](20_evidence_bundle_spec.md) | Defines bundle structure, required files, manifest/hashing, and determinism rules. | To validate bundles and to implement/verify generators. |
| [30_runbook.md](30_runbook.md) | Operator execution and verification steps with troubleshooting. | For routine runs, incident response, and reproducibility checks. |
| [40_data_dependency_register.md](40_data_dependency_register.md) | Lists only the external datasets/services from `geospatial_dmi` this project uses. | For provenance review, currency checks, and dependency risk review. |
| [50_method_notes_and_decisions.md](50_method_notes_and_decisions.md) | Records decisions and policies for uncertainty/conflicts across sources. | When outcomes are challenged or method changes are proposed. |
| [60_risk_register.md](60_risk_register.md) | Identifies risks, controls, and how controls are evidenced. | For risk review, audit planning, and release gating. |
| [70_change_control.md](70_change_control.md) | Versioning and release rules for docs and evidence schemas. | Before releases and whenever controls/evidence/schema change. |
| [regulation_sources.md](regulation_sources.md) | Human-readable registry of authoritative EUR-Lex artefacts and SHA-256 fingerprints. | When validating legal source snapshots for audit.
| [regulation_sources.json](regulation_sources.json) | Machine-readable registry of regulation sources (paths + hashes). | Used by tooling to verify/update hashes.
| [regulation_links.html](regulation_links.html) | Operator launcher for interactive EUR-Lex access (WAF/login-safe). | When browser access is needed to obtain snapshots.
| [articles/eudr_article_summaries.md](articles/eudr_article_summaries.md) | Short, non-verbatim summaries of Articles 9–11. | For orientation; not authoritative.
| [secrets_handling.md](secrets_handling.md) | Operator guidance for cookie jar storage outside the repo. | Before using fetch mode or handling secrets.
