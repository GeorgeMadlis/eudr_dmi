from __future__ import annotations

import os

import pytest


def _env(name: str) -> str | None:
    v = os.getenv(name)
    return v if v not in (None, "") else None


@pytest.mark.skipif(
    _env("EUDR_RUN_MINIO_TESTS") != "1",
    reason="Set EUDR_RUN_MINIO_TESTS=1 to run MinIO integration test.",
)
def test_minio_upload_smoke_and_cleanup() -> None:
    # Delay imports so unit test runs without minio installed.
    try:
        from minio import Minio  # type: ignore[import-not-found]
    except Exception as exc:
        pytest.skip(f"minio library not installed: {exc}")

    endpoint = _env("MINIO_ENDPOINT")
    access = _env("MINIO_ACCESS_KEY")
    secret = _env("MINIO_SECRET_KEY")
    bucket = _env("EUDR_REPORTS_BUCKET") or "eudr-reports"

    if not endpoint or not access or not secret:
        pytest.skip("MINIO_ENDPOINT/MINIO_ACCESS_KEY/MINIO_SECRET_KEY must be set")

    secure_raw = (_env("MINIO_SECURE") or "false").strip().lower()
    secure = secure_raw in {"1", "true", "yes", "y", "on"}

    client = Minio(endpoint, access_key=access, secret_key=secret, secure=secure)

    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)

    run_id = "ci_smoke_test"
    report_dict = {"run_id": run_id, "created_at_utc": "2026-01-22T00:00:00Z"}
    html = "<html><body>ci_smoke_test</body></html>"

    from task3_eudr_reports.minio_report_writer import object_keys_for_run, write_report

    uploaded = write_report(run_id=run_id, report_dict=report_dict, html=html, map_html=None)

    keys = object_keys_for_run(run_id)

    # Verify objects exist
    client.stat_object(bucket, keys["json"])
    client.stat_object(bucket, keys["html"])

    # Cleanup if supported
    try:
        client.remove_object(bucket, keys["json"])
        client.remove_object(bucket, keys["html"])
    except Exception:
        # If deletion isn't available (permissions), leave objects under ci_smoke_test/ prefix.
        pass

    assert uploaded["json"] == keys["json"]
    assert uploaded["html"] == keys["html"]
