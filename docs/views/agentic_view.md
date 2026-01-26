# Agentic View (EUDR DMI GIL)

## Agent roles
This view describes the intended agent/workflow split for producing inspection-grade artifacts.

- **Agent01 — Regulation mirror / watcher**
  - Owns deterministic acquisition/verification of regulation snapshots and their fingerprints.
  - Key docs: [docs/regulation/sources.md](../regulation/sources.md)
  - Tooling: [tools/regulation/acquire_and_hash.py](../../tools/regulation/acquire_and_hash.py)

- **Agent02 — Evidence builder (article/control evaluation)**
  - Owns running project-owned method primitives and writing evidence artifacts.
  - Method primitives layer (owned here):
    - [src/eudr_dmi/methods/deforestation_area.py](../../src/eudr_dmi/methods/deforestation_area.py)
    - [src/eudr_dmi/methods/maa_amet_crosscheck.py](../../src/eudr_dmi/methods/maa_amet_crosscheck.py)
  - Article scaffolds:
    - [src/eudr_dmi/articles/art_09/runner.py](../../src/eudr_dmi/articles/art_09/runner.py)

- **Agent03 — Inspector / verifier**
  - Owns verifying integrity/completeness/provenance against the contract and spine.
  - Key docs: [docs/operations/inspection_checklist.md](../operations/inspection_checklist.md), [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

## Deterministic run contract (for all agents)
### Bundle root
Evidence bundles must be written under the evidence root, by date and bundle id:
- `<evidence_root>/<YYYY-MM-DD>/<bundle_id>/`

Filesystem roots are environment-driven:
- `EUDR_DMI_AUDIT_ROOT`, `EUDR_DMI_REGULATION_ROOT`, `EUDR_DMI_EVIDENCE_ROOT`
- See [docs/operations/runbooks.md](../operations/runbooks.md)

### Required inspection invariants
- Completeness + integrity rules are defined in:
  - [docs/architecture/evidence_contract.md](../architecture/evidence_contract.md)
  - [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md)
- Traceability rules are defined in:
  - [docs/regulation/policy_to_evidence_spine.md](../regulation/policy_to_evidence_spine.md)

### What may contain timestamps
Determinism expectations are “byte-identical unless explicitly allowed”.
Allowed timestamp-bearing artifacts (example pattern):
- execution logs / run logs (must be excluded from equivalence checks or excluded from deterministic hashes)

See determinism rules in [docs/architecture/evidence_bundle_spec.md](../architecture/evidence_bundle_spec.md).

### Tests / sanity checks
- Method tests: `pytest -q -rs tests/test_methods_*` (see [docs/testing.md](../testing.md))
- Doc structure checks: [tests/articles/test_articles_structure_smoke.py](../../tests/articles/test_articles_structure_smoke.py)

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “agent-oriented navigation view”
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22`
