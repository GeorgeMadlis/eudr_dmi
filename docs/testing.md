# Testing EUDR Method Modules

## Method dependency check

To verify that all required geospatial dependencies are installed:

    python scripts/check_method_deps.py

## Run method tests with skip reasons

To run all method-level tests and show skip reasons:

    pytest -q -rs tests/test_methods_*

## Expected skips

- tests/test_methods_deforestation_area.py::test_estimate_deforestation_area_raises_clear_error_when_rasterio_missing
  - Reason: validates missing-dependency error path; skipped when rasterio is present.

## Sample output

```
..s....                                                                            [100%]
================================ short test summary info =================================
SKIPPED [1] tests/test_methods_deforestation_area.py:72: rasterio installed; skip missing-
dependency error test (intentional)                                                       6 passed, 1 skipped in 0.01s
```

## Evidence bundle validation (local)

If you have an evidence bundle directory (e.g. produced by an article runner scaffold), you can validate integrity and required files with:

    python scripts/validate_evidence_bundle.py <bundle_root>

## Task 3 MinIO report pipeline tests

Unit tests only:

    pytest -q tests/test_task3_minio_report_writer_unit.py

Integration test (requires local MinIO + env vars; opt-in):

    EUDR_RUN_MINIO_TESTS=1 pytest -q tests/test_task3_minio_report_writer_integration.py
