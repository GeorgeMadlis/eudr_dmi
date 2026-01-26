# EUDR Digital Twin Model (Audit View)

## Purpose
Define how this repository frames the “EUDR Digital Twin” for inspection: what gets mirrored, what gets produced, where it is stored, and how change is detected and propagated downstream.

This is an inspection/audit model, not a system architecture spec.

## Core idea
The Digital Twin is treated as:
- **Authoritative inputs** (regulation snapshots + upstream datasets/services) captured as evidence-grade artifacts.
- **Method + decision policies** that transform inputs into **EUDR-facing outcomes**.
- **Evidence bundles** that let an inspector recompute integrity and trace outcomes to sources.

## Regulation as a mirrored dependency
For Regulation (EU) 2023/1115:
- The EUR-Lex LSU page for CELEX:32023R1115 is treated as the **digital twin entrypoint**.
- A deterministic mirror run writes a dated run folder under the server audit root:
  - `/Users/server/audit/eudr_dmi/regulation/eudr_2023_1115/<YYYY-MM-DD>/`
- Each run folder contains artifacts plus:
  - `metadata.json` (per-source status, headers, hashes, and `needs_update`)
  - `manifest.sha256` (sorted, deterministic)
  - `entrypoint_status.json` (entrypoint reachability + evidence)
  - `digital_twin_trigger.json` (only when `needs_update=true`)

See: [docs/regulation/sources.md](../regulation/sources.md) and [docs/regulation/mirror_manual_checklist.md](../regulation/mirror_manual_checklist.md).

## Change detection and downstream triggering
Downstream jobs should treat `digital_twin_trigger.json` as the primary “do work” hook.

Design constraints:
- Some EUR-Lex endpoints are protected by WAF/login challenges. This project does not attempt to bypass challenges.
- When LSU is blocked, the mirror still produces a deterministic **entrypoint watch** output with fallback fingerprints (derived from the most stable available endpoints and/or headers).
- Invalid artifacts (e.g., non-PDF bodies at the PDF endpoint) are rejected so WAF/challenge pages are not treated as authoritative.

## Evidence bundles (control evaluation outputs)
Evidence bundles (separate from regulation mirror run folders) are the inspection unit for Article/control evaluation.

A bundle:
- Records operator inputs.
- Records the method version and any invoked decision policies.
- Records provenance for each dependency (including regulation mirror run folder references).
- Includes a manifest + hashes so an inspector can verify integrity.

See: [docs/architecture/evidence_contract.md](evidence_contract.md) and [docs/architecture/evidence_bundle_spec.md](evidence_bundle_spec.md).

## What this repo does not do
- Provide legal advice or interpretations beyond traceable, testable inspection checks.
- Duplicate or restate upstream system architecture (e.g., `geospatial_dmi`); only canonical entrypoints and adopted components with provenance are referenced (ADR-0001).
