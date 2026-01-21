# Evidence Bundle Specification

## Purpose
Defines the canonical evidence bundle layout, required files, field-level schemas, hashing rules, determinism expectations, and auditor verification steps.

## Evidence Root Policy
Evidence bundles are stored under a single evidence root, with one date folder per run date and one bundle folder per bundle id:

- Default evidence root (repo-local): `audit/evidence/`
- Override (server evidence root): `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
- Bundle layout: `<root>/<YYYY-MM-DD>/<bundle_id>/`

Notes:
- `<root>` resolves to `$EUDR_DMI_EVIDENCE_ROOT` if set; otherwise `audit/evidence/`.
- In this document, `<bundle_root>` refers to the concrete bundle directory: `<root>/<YYYY-MM-DD>/<bundle_id>/`.

## Canonical Bundle Directory Layout

```
<root>/<YYYY-MM-DD>/<bundle_id>/
  manifest.json
  hashes.sha256
  inputs/
    geometry.<ext>
    parameters.json
  outputs/
    summary.json
  provenance/
    provenance.json
  logs/
    run.log
  method/
    decisions_applied.json
    method_version.json
  attachments/
    (optional supporting artifacts)
```

Notes:
- `<ext>` MUST be a stable, documented format (TODO: choose/confirm e.g., `geojson`).
- Optional files MAY be present under `attachments/` if referenced by the manifest.

## Required Files (Minimal Schemas)
The following describes required fields (not full JSON Schema). All JSON files MUST be UTF-8 encoded and deterministic (see determinism rules).

### `manifest.json`

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `bundle_id` | string | yes | Deterministic identifier or recorded UUID (TODO: decide policy; must be consistent with hashing rules). |
| `created_utc` | string | yes | ISO-8601 timestamp in UTC. For determinism, either fixed to run start or excluded from equivalence checks (see rules). |
| `producer` | object | yes | Contains workflow/agent name + version; MUST not be empty. |
| `inputs` | object | yes | References `inputs/geometry.*` and `inputs/parameters.json` with hashes. |
| `artifacts` | array | yes | List of artifact entries: `path`, `sha256`, `size_bytes`, `content_type`, `role`. |
| `dependencies` | array | yes | Each dependency item includes `catalogue_id` and provenance summary (see dependency register). |
| `outcome` | object | yes | Summary outcome: status + reasons; must align with `outputs/summary.json`. |

Artifact entry fields (for each item in `artifacts`):
- `path` (string; relative; no `..` segments)
- `sha256` (string; lowercase hex)
- `size_bytes` (integer)
- `content_type` (string; e.g., `application/json`)
- `role` (string; e.g., `input`, `output`, `provenance`, `log`, `method`, `attachment`)

### `hashes.sha256`
A text file containing one line per artifact in deterministic order:
- Format: `<sha256>  <relative_path>`
- Hash algorithm: SHA-256
- Line endings: LF (`\n`)

### `inputs/parameters.json`

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `date_start` | string | yes | ISO-8601 (TODO: define inclusive/exclusive). |
| `date_end` | string | yes | ISO-8601 (TODO: define inclusive/exclusive). |
| `commodity` | string | yes | Must match declared taxonomy (TODO). |
| `operator_ref` | string | yes | Ticket or reference id. |
| `run_purpose` | string | yes | Short description. |

### `outputs/summary.json`

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `status` | string | yes | One of `PASS`, `FAIL`, `UNDETERMINED`. |
| `controls` | array | yes | Each item references the spine row/control objective id (TODO: define identifier). |
| `reasons` | array | conditional | Required if `status=UNDETERMINED` or `status=FAIL` with explanatory reasons. |
| `evidence_refs` | array | yes | List of artifact paths supporting the decision. |

### `provenance/provenance.json`

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `dependencies` | array | yes | One entry per dependency used (subset of register). |
| `retrieved_utc` | string | yes | ISO-8601 UTC timestamp for retrieval window end (TODO). |

Dependency provenance entry fields:
- `catalogue_id` (string)
- `dataset_or_service` (string)
- `version` (string or null; TODO)
- `source_timestamp_utc` (string or null)
- `retrieval_method` (string; canonical entrypoint identifier; TODO)
- `integrity` (object; optional: checksum/signature if available)

### `method/method_version.json`

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `method_id` | string | yes | Stable identifier for the method variant. |
| `method_version` | string | yes | Semantic version or git reference (TODO). |
| `spine_version` | string | yes | Version of the spine used for this run (see change control). |

### `method/decisions_applied.json` (if applicable)

| Field | Type | Required | Notes |
|---|---:|---:|---|
| `decisions` | array | yes | Records invoked uncertainty/conflict decisions with references to [50_method_notes_and_decisions.md](50_method_notes_and_decisions.md). |

## Manifest + Hashing Rules
- Hash algorithm: SHA-256.
- All required artifacts MUST be listed in `manifest.json` and in `hashes.sha256`.
- The manifest MUST include the hash of itself only if a stable rule is defined (TODO: either exclude `manifest.json` from `hashes.sha256` or hash a canonicalized representation).
- Paths MUST be relative to `<bundle_root>` and MUST NOT contain `..`.
- The authoritative list of files is the manifest; auditors verify on-disk files match the manifest and hashes.

## Determinism Rules
The bundle generator MUST ensure the following do not vary across reruns with identical inputs and dependency versions:
- File ordering in JSON arrays (define stable sort keys).
- Floating-point rounding and numeric formatting (define precision; TODO).
- Line endings and text encoding (UTF-8; LF).
- Randomness (seeded or disabled).
- Time fields: either fixed policy (e.g., run start) or explicitly excluded from equivalence checks (documented in verification).
- Paths and filenames: stable and normalized.

## Auditor Verification Checklist

| Check | What to do | Acceptance criteria |
|---|---|---|
| Bundle completeness | Confirm required directories/files exist. | Layout matches canonical tree; required files present. |
| Manifest validity | Parse `manifest.json` and confirm required fields. | All required fields present; no empty producer/dependency identifiers. |
| Hash verification | Recompute SHA-256 for each artifact listed and compare with `hashes.sha256` and `manifest.json`. | All hashes match; no missing artifacts; no unexpected artifacts outside manifest (unless explicitly allowed). |
| Provenance review | Compare provenance entries against dependency register. | Required provenance fields present; currency within expected bounds or documented exception. |
| Outcome traceability | For each reported control outcome, locate linked evidence references. | Each control has supporting artifact paths; status consistent with acceptance criteria in the spine. |
| Rerun equivalence | Re-run with identical inputs and pinned dependencies (TODO). | Artifacts identical under determinism rules; any allowed differences explicitly documented. |
