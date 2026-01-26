# Glossary

| Term | Meaning (in this repo) |
|---|---|
| Digital Twin | A deterministic, evidence-backed representation of the regulatory and data state used to justify EUDR-facing decisions. This repo focuses on the inspection artifacts and contracts that make that representation auditable. |
| Digital Twin entrypoint | The canonical “change signal” URL we watch to detect updates that should trigger downstream re-evaluation (for EUDR 2023/1115, the EUR-Lex LSU page for CELEX:32023R1115). |
| Evidence bundle | A deterministic directory of artifacts produced for a specific run + inputs, with a manifest and cryptographic hashes enabling independent verification. |
| Run folder | A dated folder containing a deterministic snapshot of a sourcing/mirroring run (e.g., regulation mirror output under the server audit root). |
| Control objective | A testable statement supporting an obligation; it is verified from concrete evidence artifacts. |
| Acceptance criteria | Observable conditions an inspector can apply to an artifact to determine whether a control objective is met. |
| PASS / FAIL / UNDETERMINED | Standardized outcome semantics for inspection outputs; see the overview for criteria. |
| Upstream dependency | Any external dataset/service/platform/library used to produce outputs (e.g., selected components/patterns adopted from `geospatial_dmi` per ADR-0001). |
| Determinism | Re-running with identical inputs and pinned dependencies produces byte-identical artifacts, except for explicitly allowed fields (e.g., timestamps in logs) under documented rules. |
