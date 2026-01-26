# Data Dependency Register

## Purpose
Lists only the `geospatial_dmi` catalogue datasets/services actually used by this project for EUDR evidence. This document does not reproduce the upstream catalogue.

## Register

| geospatial_dmi Catalogue ID | Dataset/Service Name | Purpose in EUDR | Required Provenance Fields | Expected Currency | Known Constraints | Evidence Link |
|---|---|---|---|---|---|---|
| TODO_CATALOGUE_ID_001 | TODO_DATASET_NAME | TODO_PURPOSE (e.g., deforestation signal / land cover / boundary reference) | `catalogue_id`, `dataset_or_service`, `version`, `source_timestamp_utc`, `retrieval_method` | TODO_CURRENCY_EXPECTATION (e.g., monthly) | TODO_CONSTRAINTS (coverage, latency, licensing limits) | `provenance/provenance.json#TODO_POINTER` |
| TODO_CATALOGUE_ID_002 | TODO_SERVICE_NAME | TODO_PURPOSE | TODO_FIELDS | TODO_CURRENCY | TODO_CONSTRAINTS | `provenance/provenance.json#TODO_POINTER` |

## Inspector Notes
- Each register row MUST correspond to at least one provenance entry in the evidence bundle.
- If a dependency is optional, this MUST be stated and tied to a control objective (spine).
- Canonical `geospatial_dmi` entrypoints for these dependencies: TODO_LINKS_OR_PATHS (do not duplicate architecture).
