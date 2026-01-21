# Regulation Mirror — Manual Verification Checklist

Use this checklist for each run folder:

## 1) PDF is a real PDF
From the run folder, confirm the PDF is recognized by the OS:

```sh
file regulation.pdf
```

Expected: output includes `PDF document`.

## 2) Manifest integrity
From the run folder:

```sh
shasum -a 256 -c manifest.sha256
```

Expected: command exits successfully (all files `OK`).

## 3) Update signal consistency
Inspect `metadata.json`:

- `needs_update` matches your expectations for whether the digital twin should be re-synced.
- If `status` is `partial`, treat results as potentially uncertain and review `entrypoint_status.json`.

## 4) Trigger file presence
- If `needs_update=true`, `digital_twin_trigger.json` should exist.
- If `needs_update=false`, `digital_twin_trigger.json` should not exist.
