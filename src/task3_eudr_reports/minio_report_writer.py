from __future__ import annotations

import json
import os
import io
from dataclasses import dataclass
from typing import Any


def _env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _env_bool(name: str, default: bool = False) -> bool:
    raw = _env(name)
    if raw is None:
        return default
    raw_norm = raw.strip().lower()
    if raw_norm in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if raw_norm in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


@dataclass(frozen=True, slots=True)
class MinioConfig:
    endpoint: str
    access_key: str
    secret_key: str
    secure: bool
    bucket: str


def load_minio_config_from_env() -> MinioConfig:
    endpoint = _env("MINIO_ENDPOINT")
    access_key = _env("MINIO_ACCESS_KEY")
    secret_key = _env("MINIO_SECRET_KEY")
    secure = _env_bool("MINIO_SECURE", default=False)
    bucket = _env("EUDR_REPORTS_BUCKET", default="eudr-reports")

    missing: list[str] = []
    if not endpoint:
        missing.append("MINIO_ENDPOINT")
    if not access_key:
        missing.append("MINIO_ACCESS_KEY")
    if not secret_key:
        missing.append("MINIO_SECRET_KEY")

    if missing:
        raise RuntimeError(
            "Missing required MinIO environment variables: " + ", ".join(missing)
        )

    return MinioConfig(
        endpoint=str(endpoint),
        access_key=str(access_key),
        secret_key=str(secret_key),
        secure=bool(secure),
        bucket=str(bucket),
    )


def _get_minio_client(config: MinioConfig):
    try:
        from minio import Minio  # type: ignore[import-not-found]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "minio library is required. Install with: pip install minio"
        ) from exc

    return Minio(
        endpoint=config.endpoint,
        access_key=config.access_key,
        secret_key=config.secret_key,
        secure=config.secure,
    )


def object_keys_for_run(run_id: str) -> dict[str, str]:
    """Deterministic object key naming for a run id."""

    run_id = str(run_id)
    return {
        "json": f"{run_id}/{run_id}.json",
        "html": f"{run_id}/{run_id}.html",
        "map_html": f"{run_id}/{run_id}_map.html",
    }


def _to_deterministic_json_bytes(report_dict: dict[str, Any]) -> bytes:
    # Ensure stable serialization for evidence-grade writes.
    return (
        json.dumps(report_dict, indent=2, sort_keys=True, ensure_ascii=False) + "\n"
    ).encode("utf-8")


def write_report(
    run_id: str,
    report_dict: dict[str, Any],
    html: str,
    map_html: str | None = None,
) -> dict[str, str]:
    """Write a report bundle to MinIO under deterministic keys.

    Uploads:
      - {run_id}/{run_id}.json
      - {run_id}/{run_id}.html
      - optional {run_id}/{run_id}_map.html

    Returns:
      dict of uploaded object keys (for logging/evidence).

    Secrets are read from environment variables only.
    """

    config = load_minio_config_from_env()
    client = _get_minio_client(config)

    keys = object_keys_for_run(run_id)

    # Ensure bucket exists (idempotent). If permissions disallow, fail loudly.
    if not client.bucket_exists(config.bucket):
        client.make_bucket(config.bucket)

    uploaded: dict[str, str] = {}

    json_bytes = _to_deterministic_json_bytes(report_dict)
    client.put_object(
        config.bucket,
        keys["json"],
        data=io.BytesIO(json_bytes),
        length=len(json_bytes),
        content_type="application/json",
    )
    uploaded["json"] = keys["json"]

    html_bytes = (html or "").encode("utf-8")
    client.put_object(
        config.bucket,
        keys["html"],
        data=io.BytesIO(html_bytes),
        length=len(html_bytes),
        content_type="text/html; charset=utf-8",
    )
    uploaded["html"] = keys["html"]

    if map_html is not None:
        map_bytes = map_html.encode("utf-8")
        client.put_object(
            config.bucket,
            keys["map_html"],
            data=io.BytesIO(map_bytes),
            length=len(map_bytes),
            content_type="text/html; charset=utf-8",
        )
        uploaded["map_html"] = keys["map_html"]

    return uploaded
