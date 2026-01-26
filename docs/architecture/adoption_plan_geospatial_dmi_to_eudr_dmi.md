# Adoption Plan: geospatial_dmi → eudr_dmi

Date: 2026-01-22

This document describes how `eudr_dmi` will *fully own* the previously-working EUDR pipelines that currently live in `geospatial_dmi`, by using an explicit adopt-and-evolve scaffold and clear ownership boundaries.

## Objectives

- Fully internalize EUDR-specific pipelines into `eudr_dmi` so operators can run end-to-end EUDR workflows from this repo.
- Preserve auditability: deterministic outputs, stable artifact naming, evidence bundle integrity, and explicit provenance.
- Avoid hidden coupling: `eudr_dmi` should not depend on runtime imports of `geospatial_dmi` for core EUDR functionality.

## Ownership boundaries (high-level)

- `eudr_dmi` owns:
  - EUDR domain logic, evidence semantics, and inspection-grade conventions.
  - EUDR pipeline runners/CLIs and any EUDR-specific adapters.
  - EUDR report generation and storage conventions.

- `geospatial_dmi` remains:
  - A general-purpose geospatial/DMI framework.
  - A reference implementation to adopt from (via copy + provenance logging), not a runtime dependency.

- Shared operator data root (remains shared):
  - `/Users/server/data/dmi`
  - This is treated as a host-level shared resource. This repo should reference it via explicit configuration (env vars / config files), but should not attempt to “own” that path.

## Adopt-and-evolve scaffolding in this repo

The following directories exist to make adoption explicit and reviewable:

- `adopted/geospatial_dmi_snapshot/`
  - Stores a *read-only snapshot* of copied source files (or tarball) used as the basis of adoption.
  - Snapshot contents should never be executed as production code.
  - Snapshot must be referenced from `ADOPTION_LOG.md` with commit SHA and copy date.

- `scripts/migrate_from_geospatial_dmi/`
  - Contains one-time or idempotent migration scripts that:
    - copy files from a pinned `geospatial_dmi` commit
    - rewrite imports/namespaces into `src/eudr_dmi/*`
    - produce a manifest of copied files + hashes

## What will be copied (direct adoption candidates)

The goal is to copy the minimal working set needed to fully run the EUDR pipelines from this repo.

Subsystems and artifacts expected to be copied from `geospatial_dmi`:

- `data_db/` (Task 1 catalogue + DuckDB)
  - DuckDB schema and migration scripts
  - dataset catalogue tables / views
  - any dataset indexing loaders and validation utilities

- `infra/`
  - Compose files, scripts, and configuration needed to run local/shared infra
  - NOTE: shared infra remains owned by `geospatial_dmi/infra` today; this adoption plan clarifies how we migrate ownership or treat it as shared.

- `llm/`
  - LLM orchestration components used by EUDR pipelines (if any)
  - evaluation harnesses or prompt runners that are EUDR-specific

- `mcp_servers/` (Task 2)
  - MCP server implementations and their configs
  - Any operator run scripts and minimal documentation to run them

- `prompts/`
  - prompt templates, policies, and governance structure
  - prompt versioning conventions and review checklists

- Selected `src/` scripts
  - pipeline entrypoints that currently execute end-to-end EUDR tasks
  - utilities that are EUDR-specific (not general geospatial utilities)

- Configuration
  - environment-variable conventions
  - minimal config files (YAML/JSON) if used

## What will be refactored/renamed into src/eudr_dmi/*

Adopted code should be refactored to align with this repo’s boundaries and naming.

- Anything EUDR-specific should live under `src/eudr_dmi/` (or a clearly-scoped package like `src/task3_eudr_reports/` when it is intentionally pipeline-scoped).
- Any namespace/imports referencing `geospatial_dmi` must be removed for owned code.
- CLI entrypoints should use deterministic run IDs and evidence-friendly outputs.

Examples of refactor expectations:

- `geospatial_dmi.<something>.catalogue` → `src/eudr_dmi/catalogue/*` or `data_db/*` + `src/eudr_dmi/data/*`
- `geospatial_dmi.<something>.eudr_task3_*` → `src/task3_eudr_reports/*` and/or `src/eudr_dmi/articles/*`
- MCP servers should become `mcp_servers/<server_name>/...` with run docs and minimal smoke tests.

## What remains shared

Some things are intentionally shared between repos/projects to avoid duplicated host-level state.

- Host data root: `/Users/server/data/dmi`
  - treated as shared operator storage
  - referenced via config/env vars
  - contents are not version-controlled here

- Shared infra ownership (near-term)
  - MinIO/Postgres are currently managed under `/Users/server/projects/geospatial_dmi/infra/` (compose project name: `infra`).
  - `eudr_dmi` runbooks should reference the shared infra as external/owned elsewhere until/unless ownership is explicitly transferred.

## Dataset updates (e.g., Hansen 2024 → 2025)

Dataset updates must be handled as *dataset families* with *versioned releases* to maintain audit continuity.

### Concept: dataset family + versioned release

- Dataset family: stable identifier (e.g., `hansen_gfc`)
- Release/version: time/version tag (e.g., `2024`, `2025`)

In the data lake / object store, use versioned bucket names or versioned prefixes so older runs remain reproducible:

- Preferred: versioned prefixes within a stable bucket
  - bucket: `dmi-data`
  - keys:
    - `datasets/hansen_gfc/2024/...`
    - `datasets/hansen_gfc/2025/...`

- Acceptable alternative: versioned buckets
  - `dmi-data-hansen-gfc-2024`
  - `dmi-data-hansen-gfc-2025`

### Catalogue updates

When a new release is introduced:

- Add a new row to the catalogue (DuckDB) for the dataset release with:
  - family, version, spatial/temporal coverage, checksums/ETags, source URL(s)
  - ingestion timestamp, operator, and validation status

- Do not overwrite old releases.

### Re-run triggers

A dataset release update should trigger controlled re-runs:

- Decide the impacted pipelines (Task 1/2/3, Articles 09/10/11)
- For each impacted pipeline, define:
  - which run IDs must be regenerated
  - which evidence bundles must be invalidated/superseded
  - how to preserve prior results (do not delete; supersede)

### Evidence continuity guidance

- Evidence bundles should explicitly reference dataset family + version.
- Reports should include:
  - dataset release identifiers
  - hashes/ETags (if available)
  - catalogue row IDs

## Execution and governance

- Every adoption action must be recorded in `ADOPTION_LOG.md` with:
  - source repo/path(s)
  - source commit SHA
  - copy date
  - new owned path(s)
  - notes on divergence and any follow-up tasks

- `adopted/geospatial_dmi_snapshot/` should contain:
  - either a tarball named by commit SHA, or
  - a folder structure with a manifest + hashes

## Near-term work breakdown (operator-focused)

1. Pin `geospatial_dmi` commit SHA for adoption.
2. Snapshot relevant paths into `adopted/geospatial_dmi_snapshot/`.
3. Run migration scripts under `scripts/migrate_from_geospatial_dmi/` to copy/refactor into owned locations.
4. Update `ADOPTION_LOG.md` entries (replace placeholders).
5. Add smoke tests for each adopted subsystem.
6. Update runbooks and validate end-to-end runs on shared infra + shared data root.
