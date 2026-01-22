# EUDR DMI GIL — Inspection-Oriented Documentation

## Purpose
This repository maintains the inspection-oriented documentation and evidence bundle conventions for EUDR-facing outputs. This project is informed by `geospatial_dmi` and adopts selected components/patterns from it (with explicit provenance), while specializing and evolving them for EUDR Digital Twin needs.

Authoritative scope statement: [docs/architecture/decision_records/ADR-0001-project-scope.md](docs/architecture/decision_records/ADR-0001-project-scope.md)

## What This Repo Produces
- Evidence bundle specification and verification rules (manifest + hashing + determinism expectations)
- Control-to-evidence “spine” mapping obligations to concrete artifacts
- Runbook for operators to execute and verify bundle generation
- Registers: data dependencies, method decisions, and risks
- Change control policy for audit continuity

## Where Evidence Bundles Are Stored
- Default evidence root (repo-local): `audit/evidence/`
- Override (server evidence root): `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
- Bundle layout: `<root>/<YYYY-MM-DD>/<bundle_id>/`

Notes:
- `<root>` resolves to `$EUDR_DMI_EVIDENCE_ROOT` if set; otherwise `audit/evidence/`.

## How to Run
- See the runbook: [docs/30_runbook.md](docs/30_runbook.md)
- Commands are intentionally placeholders until finalized:
  - `TODO_COMMAND_TO_BUILD_OR_PREPARE`
  - `TODO_COMMAND_TO_GENERATE_EVIDENCE_BUNDLE`
  - `TODO_COMMAND_TO_VERIFY_MANIFEST_AND_HASHES`

## Inspection Map
- Start here: [docs/INDEX.md](docs/INDEX.md)

## Non-goals
- This project does not treat `geospatial_dmi` as a read-only upstream to be “consumed”.
- No platform architecture duplication: do not copy, restate, or re-document `geospatial_dmi` architecture in this repository; only reference canonical entrypoints (TODO: add links/paths once confirmed).
