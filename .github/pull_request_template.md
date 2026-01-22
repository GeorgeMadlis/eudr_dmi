# PR Title Prefix (choose one)
Use one of the following prefixes in the PR title:
- [Art 09]
- [Art 10]
- [Art 11]
- [Governance]

---

## 1) Purpose and boundary
**Purpose (what changes and why):**
- TODO

**Boundary statement (required):**
- This project is informed by `geospatial_dmi` and may adopt selected components from it into `eudr_dmi` with explicit provenance (see ADR-0001).
- This PR MUST NOT copy, restate, or re-document `geospatial_dmi` architecture or code.

## 2) Evidence artifacts added/changed (exact paths)
List all evidence artifacts (exact relative paths) that are added or changed, including docs and schemas.

- TODO_PATH_1
- TODO_PATH_2

If this PR changes the evidence bundle structure or hashing rules, list:
- impacted bundle paths
- impacted manifest fields
- impacted determinism rules

## 3) How to reproduce (commands; TODO allowed)
Provide the exact commands to generate the declared evidence artifacts.

```sh
# Example
# TODO_COMMAND_TO_PREPARE_ENV
# TODO_COMMAND_TO_GENERATE_EVIDENCE
# TODO_COMMAND_TO_VERIFY_MANIFEST_AND_HASHES
```

## 4) How to inspect (steps)
Provide an inspector-friendly sequence of checks.

1. Locate bundle root: `<root>/<YYYY-MM-DD>/<bundle_id>/`
	- Default `<root>`: `audit/evidence/`
	- Override: `EUDR_DMI_EVIDENCE_ROOT=/Users/server/audit/eudr_dmi/evidence`
2. Verify integrity:
	- Validate `hashes.sha256` against on-disk files
	- Confirm `manifest.json` completeness
3. Verify traceability:
	- Confirm control ids map to the policy-to-evidence spine
4. Verify provenance:
	- Confirm required provenance fields for each dependency
5. Apply acceptance criteria:
	- For each control outcome, confirm referenced evidence supports the status

## 5) Risks/assumptions
List any assumptions introduced or relied upon, plus risks and mitigations.

- Assumptions: TODO
- Risks: TODO
- Mitigations/controls: TODO

---

## Checklist (audit PR gates)
- [ ] Article doc updated under `docs/articles/art_XX/` (if applicable)
- [ ] Evidence governance updated under `docs/evidence_governance/` (if applicable)
- [ ] Policy-to-evidence spine impact noted (if applicable)
- [ ] Executable code produces declared evidence artifacts (paths match section 2)
- [ ] Tests updated/added and passing
- [ ] Determinism: no timestamps in specs/proposals (logs may contain time)
- [ ] No duplication of `geospatial_dmi` architecture or code
- [ ] New dependencies recorded in the dependency register (if applicable)
