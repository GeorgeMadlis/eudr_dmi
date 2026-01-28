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
- See the runbook: [docs/operations/runbooks.md](docs/operations/runbooks.md)
- Commands are intentionally placeholders until finalized:
  - `TODO_COMMAND_TO_BUILD_OR_PREPARE`
  - `TODO_COMMAND_TO_GENERATE_EVIDENCE_BUNDLE`
  - `TODO_COMMAND_TO_VERIFY_MANIFEST_AND_HASHES`

## Portable Docs Site Bundle (HTML + Zip)

This repo can produce a portable, shareable HTML documentation bundle under `docs/site_bundle/` and a deterministic zip at `docs/site_bundle.zip`.

Create/recreate the bundle folder and zip:

```sh
source .venv/bin/activate && bash scripts/export_site_bundle.sh
```

Outputs:
- `docs/site_bundle/` (portable folder bundle)
- `docs/site_bundle.zip` (deterministic zip)
- `docs/site_bundle.zip.sha256` (sha256 for the zip)

Notes:
- The bundle build expects the repo-local `proposals/` folder to exist (it may be empty).
- DAO agent upload requires machine descriptors under `docs/dao/machine/.../view.yaml`.

## Running method-level tests (geospatial dependencies)
Some method tests exercise geospatial functionality (e.g., raster masking) and require explicit
Python packages.

Install method dependencies:

```sh
python -m pip install -r requirements-methods.txt
```

Platform note:
- `rasterio` may require system GDAL/native libraries on some platforms.

Validate your environment:

```sh
python scripts/check_method_deps.py
```

Run method tests and show skip reasons:

```sh
pytest -q -rs tests/test_methods_*
```

## Testing

See [docs/testing.md](docs/testing.md) for full testing instructions, expected skips, and sample output.

Run the full test suite:

```sh
pytest -q
```

## Demos

Show CLI help:

```sh
python scripts/demos/demo_mcp_maaamet.py --help
python scripts/demos/eudr_compliance_check_estonia.py --help
```

## Shared Infra (MinIO/Postgres)

MinIO + Postgres are treated as shared infrastructure owned by `geospatial_dmi` under `/Users/server/projects/geospatial_dmi/infra/`.

Runbook (copy/paste commands):
- [docs/runbooks/task3_minio_shared_infra.md](docs/runbooks/task3_minio_shared_infra.md)

Task 3 report pipeline:
- [docs/runbooks/task3_report_to_minio.md](docs/runbooks/task3_report_to_minio.md)

Verify from this repo:

```sh
bash scripts/infra/verify_shared_infra.sh
```

## Adoption from geospatial_dmi

This repo is preparing to fully own previously-working EUDR pipelines that currently live in `geospatial_dmi`, using an explicit adopt-and-evolve process.

- Plan: [docs/architecture/adoption_plan_geospatial_dmi_to_eudr_dmi.md](docs/architecture/adoption_plan_geospatial_dmi_to_eudr_dmi.md)
- Provenance log: [ADOPTION_LOG.md](ADOPTION_LOG.md)

## Inspection Map
- Start here: [docs/README.md](docs/README.md)
- Full index: [docs/INDEX.md](docs/INDEX.md)

## Non-goals
- This project is informed by `geospatial_dmi`, adopts selected components with explicit provenance, and allows divergence as required under EUDR pressure.
- `geospatial_dmi` remains a general framework; `eudr_dmi` owns EUDR-specific logic and evidence semantics.
- No upstream architecture duplication: do not copy, restate, or re-document `geospatial_dmi` architecture in this repository; only reference canonical entrypoints (TODO: add links/paths once confirmed).
