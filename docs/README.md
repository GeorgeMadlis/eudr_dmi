# Documentation (Canonical Entry Point)

## Purpose
This repository maintains inspection-oriented documentation and conventions for producing and verifying EUDR-facing evidence bundles (EUDR DMI GIL).

Authoritative scope statement:
- [docs/architecture/decision_records/ADR-0001-project-scope.md](architecture/decision_records/ADR-0001-project-scope.md)

## Relationship to `geospatial_dmi`
This project is informed by `geospatial_dmi` and may adopt selected documentation patterns and components with explicit provenance.

Boundaries:
- Do not copy, restate, or re-document upstream system architecture here.
- Prefer stable entrypoint references and project-owned inspection contracts.

## Three stable navigation “views”
- Task-oriented: [docs/views/task_view.md](views/task_view.md)
- Agent-oriented: [docs/views/agentic_view.md](views/agentic_view.md)
- Digital-twin-oriented: [docs/views/digital_twin_view.md](views/digital_twin_view.md)

## Deep links into the docs tree
- Architecture contracts: [docs/architecture/README.md](architecture/README.md)
- Regulation sourcing + spine: [docs/regulation/README.md](regulation/README.md)
- Operations (runbooks/checklists): [docs/operations/README.md](operations/README.md)
- Articles (inspection notes): [docs/articles/eudr_article_summaries.md](articles/eudr_article_summaries.md)

## Provenance & ownership
Adopted from `geospatial_dmi` documentation patterns; owned here; divergence expected.

Provenance record (placeholder):
- adopted_from_repo: `geospatial_dmi`
- adopted_pattern: “multiple navigation views” (task/agent/digital twin)
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22`
