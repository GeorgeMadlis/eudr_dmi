# Adoption Policy (Adopt-and-Evolve Provenance)

## Purpose
This policy defines how this repository adopts external components (including from `geospatial_dmi`) while maintaining auditability, ownership clarity, and long-term maintainability.

This is an inspection and governance policy, not an upstream architecture description.

## Definitions
### Adoption
**Adoption** means:
- The component’s code (or a controlled excerpt) is **copied into this repository** under `src/` (or other repo-owned paths), and
- The component is **owned and maintained here** going forward, including tests, change control, and documentation.

Adoption is preferred over hidden coupling.

### Reference (non-adoption)
A **reference** means:
- This repo may point to an upstream capability via a **canonical entrypoint** (URL/CLI/API),
- Without importing upstream source code directly or depending on undocumented internal behavior.

## Required provenance metadata (for every adoption)
Every adopted component MUST have provenance recorded in the root adoption log.

Required fields:
- **Source repo** (URL or canonical identifier)
- **Source path** (path in the source repo)
- **Source commit SHA** (exact commit hash)
- **Adoption date** (ISO-8601, e.g., `2026-01-22`)
- **Rationale** (why we adopted instead of referencing)
- **Divergence notes** (how/why the adopted copy diverges; include compatibility expectations)

Canonical record location:
- [ADOPTION_LOG.md](../../ADOPTION_LOG.md)

## Prohibited practices
The following are explicitly prohibited for core EUDR methods and evidence semantics:
- **Hidden coupling**: relying on undocumented upstream behavior, internal data contracts, or internal modules.
- **Undocumented imports**: directly importing `geospatial_dmi` (or other upstream repos) in core EUDR method code without recording it as an explicit dependency and without a plan to internalize/adopt it.
- **Architecture duplication**: copying or restating upstream system architecture into this repo.

If direct imports from `geospatial_dmi` are introduced:
- They MUST be logged in [ADOPTION_LOG.md](../../ADOPTION_LOG.md) as a temporary coupling.
- A follow-up task MUST be created to internalize/adopt the required component(s) or replace the dependency with a stable, documented entrypoint.

## Review checklist (for PRs)
- Is the change an **adoption** (code copied into this repo) or a **reference** (entrypoint-only)?
- If adoption: does [ADOPTION_LOG.md](../../ADOPTION_LOG.md) include all required provenance metadata?
- If reference: are entrypoints stable and documented, and are we avoiding hidden coupling?
- Are any direct upstream imports introduced in core methods? If yes, is there an explicit plan to remove them?
