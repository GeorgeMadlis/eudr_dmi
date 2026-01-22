# Migration Runbook — Adopt from geospatial_dmi

Purpose: copy selected subsystems from `/Users/server/projects/geospatial_dmi` into this repository in a repeatable, idempotent way, and record an integrity manifest of the adopted files.

## Boundaries / safety constraints

- Do not copy secrets.
- Do not copy runtime data plane: `/Users/server/data/dmi`.
- Do not copy `audit/` or `outputs/` directories.

Consider this process a *copy + own* adoption step. Record provenance in ADOPTION_LOG.md.

## 1) Copy selected folders (idempotent)

From this repo root:

```sh
bash scripts/migrate_from_geospatial_dmi/01_copy_selected.sh
```

What it does:
- Uses `rsync -a --delete` to mirror the selected source subsets into this repo.
- Excludes: `.git/`, `audit/`, `outputs/`, `.venv/`, `__pycache__/`, `*.pyc`, `.env*`, `keys.yml`.
- Fails if `.env*` or `keys.yml` are found under copied targets.

## 2) Write integrity manifest (sha256)

From this repo root:

```sh
python scripts/migrate_from_geospatial_dmi/02_write_manifest.py
```

Output:
- Writes: `adopted/geospatial_dmi_snapshot/latest_manifest.sha256`
- Format: `<sha256>  <relative_path>`
- Ordering: stable (sorted by relative path)

## 3) Review changes

```sh
git status
```

Optional (spot-check secrets were not copied):

```sh
find data_db mcp_servers prompts llm infra config -name '.env' -o -name '.env.*' -o -name 'keys.yml'
```

## 4) Commit the adoption snapshot

```sh
git add -A
git commit -m "Adopt selected subsystems from geospatial_dmi (snapshot + manifest)"
```

## 5) Update provenance log (required)

Update `ADOPTION_LOG.md` with:
- source commit SHA (exact)
- adoption/copy date
- source paths copied
- any divergence notes
