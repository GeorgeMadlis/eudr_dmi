# EUDR DMI GIL — Inspection-Oriented Documentation

## Purpose
This repository maintains the inspection-oriented documentation and evidence bundle conventions for EUDR-facing outputs. This project consumes `geospatial_dmi` as the upstream platform for data/services; it defines what evidence must exist, how it is verified, and how changes are controlled.

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
- This project consumes `geospatial_dmi`.
- No platform architecture duplication: do not copy, restate, or re-document `geospatial_dmi` architecture in this repository; only reference canonical entrypoints (TODO: add links/paths once confirmed).
