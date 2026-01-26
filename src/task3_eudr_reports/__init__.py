"""Task 3: EUDR report pipelines.

This package contains small, operator-oriented pipelines that write EUDR-facing reports
to shared infrastructure (e.g., MinIO) without embedding secrets in this repo.
"""

__all__: list[str] = [
    "minio_report_writer",
    "run_eudr_report_to_minio",
]
