# Article 09 — Inspection Notes (Placeholder)

## Purpose and boundary
This document defines the inspection-oriented evidence expectations for obligations mapped to Article 09 (placeholder reference). It specifies what an inspector should verify and where the corresponding evidence should be found in the evidence bundle.

Boundary:
- This project is informed by `geospatial_dmi` and may adopt selected components from it into `eudr_dmi` with explicit provenance.
- This document does not describe, restate, or duplicate `geospatial_dmi` architecture.
- Evidence requirements here are project-level conventions and MUST be traceable to the spine.

## Out of scope
- Any implementation details inside `geospatial_dmi`.
- Reproducing upstream dataset/service catalogue details.
- Legal advice or non-testable interpretations.

## In-scope / Out-of-scope

| In-scope | Out-of-scope |
|---|---|
| Article 09 obligations mapped in the spine (TODO: add exact references). | Any implementation details inside `geospatial_dmi`. |
| Evidence artifacts and acceptance criteria used for inspection. | Reproducing upstream dataset/service catalogue details. |
| Determinism and verification rules applicable to Article 09 artifacts. | Legal advice or non-testable interpretations. |

## Evidence Outputs (File Names + Semantics)
These artifacts are expected to exist inside a compliant evidence bundle (see [docs/architecture/evidence_bundle_spec.md](../../architecture/evidence_bundle_spec.md)).

| Artifact | Semantics | Acceptance criteria |
|---|---|---|
| `art09_info_collection.json` (scaffold) | Article 09 placeholder output with input echo and TODO integration markers. | File is present; parseable JSON; references only in-bundle paths (when added); control ids map to the spine (TODO). |
| `outputs/summary.json` | Run-level outcome summary including PASS/FAIL/UNDETERMINED and reasons. | `status` valid; includes references to Article 09 controls when applicable. |
| `manifest.sha256` (scaffold) | Stable SHA-256 manifest for deterministic files only. | Manifest is present; entries are sorted; hashes recompute and match. |
| `provenance/provenance.json` | Provenance records for dependencies used by Article 09 checks. | Required provenance fields present for each dependency used by this Article. |

## How to run (scaffold)
This scaffold creates a minimal, deterministic evidence bundle skeleton. Integration to `geospatial_dmi` entrypoints is TODO, but the evidence contract (bundle layout + deterministic artifacts + hashing) is already enforced.

## Regulatory references
Authoritative text is stored as hashed EUR-Lex artefacts under the server audit root (not in this repo).

- Human registry: [docs/regulation/sources.md](../../regulation/sources.md)
- Machine registry: [docs/regulation/sources.json](../../regulation/sources.json)
- Browser launcher: [docs/regulation/links.html](../../regulation/links.html)
- Non-verbatim summaries: [docs/articles/eudr_article_summaries.md](../eudr_article_summaries.md)

Evidence root policy:
- Default repo-local: `audit/evidence/`
- Override (server): `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
- Layout: `<root>/<YYYY-MM-DD>/<bundle_id>/`

Example command:
```sh
python -m eudr_dmi.articles.art_09.runner \
  --aoi-file /path/to/aoi.geojson \
  --commodity coffee \
  --from-date 2026-01-01 \
  --to-date 2026-01-15
```

## How to Inspect Evidence (Step-by-step)
1. Locate the evidence bundle root: `<root>/<YYYY-MM-DD>/<bundle_id>/`.
   - Default `<root>`: `audit/evidence/`
   - Override: `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
2. Verify bundle integrity:
   - Recompute SHA-256 for each file referenced by `manifest.sha256`.
   - Confirm `manifest.sha256` lists `bundle_metadata.json` and `art09_info_collection.json`.
3. Inspect Article 09 results:
   - Open `art09_info_collection.json`.
   - Confirm inputs are echoed correctly and TODO integration markers are present.
4. Trace evidence references:
   - (TODO) Once control outcomes are implemented, open referenced artifacts and confirm reasons are supported.
5. Confirm summary consistency:
   - Check `outputs/summary.json` includes or links to Article 09 outcomes where applicable.

TODO: Add `outputs/articles/art_09.json` once controls + spine mapping are finalized.
