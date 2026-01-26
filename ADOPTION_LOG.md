# Adoption Log

This log records explicit adopt-and-evolve provenance for any components copied into this repository and owned here.

Policy: [docs/architecture/adoption_policy.md](docs/architecture/adoption_policy.md)

## Adopted components

| Component name | Source (repo/path) | Source commit | Adopted into (path) | Adoption date | Notes |
|---|---|---|---|---|---|
| EUDR methods adoption (deforestation area + Maa-amet cross-check) | `geospatial_dmi` / (see section below) | UNKNOWN | `src/eudr_dmi/methods/deforestation_area.py`, `src/eudr_dmi/methods/maa_amet_crosscheck.py` | 2026-01-22 | Copied-and-owned adoption; divergence allowed and expected under EUDR pressure; no upstream coupling; all changes must be logged here. |
| Task 1 catalogue + DuckDB (planned adoption scaffold) | `geospatial_dmi` / `data_db/` (exact paths TBD) | UNKNOWN | `data_db/` (+ owned code under `src/eudr_dmi/*` as needed) | TBD | Placeholder entry to be finalized when copying occurs; add source paths + snapshot manifest in `adopted/geospatial_dmi_snapshot/`. |
| Task 2 MCP servers (planned adoption scaffold) | `geospatial_dmi` / `mcp_servers/` (exact paths TBD) | UNKNOWN | `mcp_servers/` | TBD | Placeholder entry to be finalized when copying occurs; adopt servers + configs; remove any runtime coupling on `geospatial_dmi`. |
| Task 3 EUDR report→MinIO pipeline (planned adoption scaffold) | `geospatial_dmi` / (exact paths TBD) | UNKNOWN | `src/task3_eudr_reports/*` + runbook(s) | TBD | This repo already contains an owned Task 3 pipeline; if any prior working pipeline code is copied from `geospatial_dmi`, record exact source paths and commit here. |
| Prompts governance structure (planned adoption scaffold) | `geospatial_dmi` / `prompts/` (exact paths TBD) | UNKNOWN | `prompts/` | TBD | Placeholder entry to be finalized when copying occurs; prompts must be versioned and governed per this repo’s inspection model. |

## EUDR methods adoption (deforestation area + Maa-amet cross-check)

Required provenance fields:
- adopted_from_repo: `geospatial_dmi`
- source_paths:
	- `geospatial_dmi/.../deforestation_area.py` (placeholder)
	- `geospatial_dmi/.../maa_amet_crosscheck.py` (placeholder)
- source_commit_sha: `UNKNOWN`
- adoption_date: `2026-01-22` (Europe/Tallinn)
- new_owned_paths:
	- `src/eudr_dmi/methods/deforestation_area.py`
	- `src/eudr_dmi/methods/maa_amet_crosscheck.py`
- notes:
	- This is an explicit adoption (copied into `eudr_dmi` and owned here), not an import dependency.
	- Divergence is allowed and expected under EUDR pressure; `geospatial_dmi` remains a general framework; `eudr_dmi` owns EUDR-specific logic.
	- Hidden coupling is prohibited; do not introduce direct `geospatial_dmi` imports for core EUDR methods.
	- Any future upstream import (temporary coupling) must be logged with a follow-up task to internalize/adopt.

## Direct upstream imports (must be temporary)

No direct `geospatial_dmi` imports were found in the current codebase as of `2026-01-22`.

If a future change introduces direct imports for core EUDR methods, add a row above and create a follow-up task to internalize/adopt the required code.
