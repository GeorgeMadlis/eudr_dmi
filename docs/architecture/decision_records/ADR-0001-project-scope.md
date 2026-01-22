# ADR-0001: EUDR DMI GIL scope: adopt-and-evolve vs consume

Status: Accepted

## Context
The EUDR Digital Twin requires a maintained method and the ability to evolve alongside regulatory updates (including how regulation sources are mirrored, verified, and traced).

Historically, this repository’s documentation used wording that implied a “consume-only” relationship to an upstream platform (`geospatial_dmi`). That framing is too restrictive for an audit-driven program that must:
- adopt and specialize platform components where needed,
- maintain explicit provenance for adopted elements,
- allow controlled divergence to satisfy EUDR-specific obligations, and
- preserve a stronger audit trail for regulation + method evolution over time.

## Decision
We will refactor documentation in-place in this repository to reflect the project’s actual role:

- This project **adopts and evolves** selected components and patterns from `geospatial_dmi`, with explicit provenance recorded at the point of adoption.
- Adopted components will live in `eudr_dmi` with clear attribution (what was adopted, when, from where, and why).
- `geospatial_dmi` remains the general framework; `eudr_dmi` is the EUDR-specific specialization and may diverge when required by compliance, auditability, or operational needs.

## Consequences
- No “consume-only” constraint: this repo may adopt and modify components as needed.
- An explicit adoption/provenance log becomes part of change control.
- Divergence is allowed and expected under EUDR pressure; compatibility with `geospatial_dmi` is not assumed unless explicitly documented.
- Stronger audit traceability: EUDR-specific method and regulation evolution is captured within this repository’s governed documentation and evidence workflows.
