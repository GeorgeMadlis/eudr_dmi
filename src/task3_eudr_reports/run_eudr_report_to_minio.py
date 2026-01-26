from __future__ import annotations

import argparse
import html as html_lib
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eudr_dmi.articles.art_09.runner import _git_commit
from eudr_dmi.methods.deforestation_area import (
    DeforestationAreaInputs,
    METHOD_VERSION as DEFORESTATION_AREA_METHOD_VERSION,
    estimate_deforestation_area,
    fingerprint_deforestation_area_inputs,
)
from eudr_dmi.methods.maa_amet_crosscheck import (
    METHOD_VERSION as MAA_AMET_METHOD_VERSION,
    MaaAmetCrossCheckInputs,
    crosscheck_maa_amet,
)

from task3_eudr_reports.minio_report_writer import write_report


def _utc_run_id_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%d_%H%M%S")


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _env_optional(name: str) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return None
    return value


def _env_float(name: str) -> float | None:
    raw = _env_optional(name)
    if raw is None:
        return None
    return float(raw)


def _render_html_report(report: dict[str, Any]) -> str:
    run_id = html_lib.escape(str(report.get("run_id")))
    created_at = html_lib.escape(str(report.get("created_at_utc")))

    summary = report.get("summary") or {}
    results = report.get("results") or {}

    def row(k: str, v: Any) -> str:
        return (
            "<tr>"
            f"<td><code>{html_lib.escape(k)}</code></td>"
            f"<td>{html_lib.escape(str(v))}</td>"
            "</tr>"
        )

    metrics: list[tuple[str, Any]] = []
    metrics.append(("deforestation.status", (results.get("deforestation") or {}).get("status")))
    metrics.append(("maa_amet.status", (results.get("maa_amet") or {}).get("status")))

    metrics_rows = "\n".join(row(k, v) for k, v in metrics)

    assumptions = (
        "<ul>"
        "<li>This is a minimal scaffold report intended for iteration.</li>"
        "<li>Deforestation area estimation requires a loss raster path; if not provided, the result is UNDETERMINED.</li>"
        "<li>Maa-amet cross-check is currently a deterministic primitive and does not fetch Maa-amet data.</li>"
        "</ul>"
    )

    return (
        "<!doctype html>"
        "<html><head><meta charset='utf-8'><title>EUDR Report</title>"
        "<style>body{font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 960px; margin: 2rem auto; padding: 0 1rem;}"
        "table{border-collapse:collapse;width:100%;}td,th{border:1px solid #ddd;padding:8px;}th{background:#f6f6f6;text-align:left;}"
        "code{background:#f2f2f2;padding:2px 4px;border-radius:4px;}</style>"
        "</head><body>"
        f"<h1>EUDR Report</h1>"
        f"<p><b>run_id</b>: <code>{run_id}</code><br><b>created_at_utc</b>: <code>{created_at}</code></p>"
        "<h2>Summary</h2>"
        f"<pre>{html_lib.escape(json.dumps(summary, indent=2, sort_keys=True))}</pre>"
        "<h2>Key metrics</h2>"
        "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>"
        f"{metrics_rows}"
        "</tbody></table>"
        "<h2>Assumptions / limitations</h2>"
        f"{assumptions}"
        "</body></html>"
    )


def _build_report(
    *,
    run_id: str,
    aoi_path: Path,
    max_parcels: int | None,
) -> dict[str, Any]:
    now = datetime.now(UTC)
    aoi_geojson = _read_json(aoi_path)

    params: dict[str, Any] = {
        "max_parcels": max_parcels,
        "env": {
            # No secrets here; just non-sensitive optional knobs.
            "EUDR_LOSS_RASTER_PATH": _env_optional("EUDR_LOSS_RASTER_PATH"),
            "EUDR_PIXEL_AREA_M2": _env_optional("EUDR_PIXEL_AREA_M2"),
        },
    }

    results: dict[str, Any] = {}

    # Deforestation area estimation (if raster path is provided).
    loss_raster_path = _env_optional("EUDR_LOSS_RASTER_PATH")
    pixel_area_m2 = _env_float("EUDR_PIXEL_AREA_M2")

    if not loss_raster_path:
        defo_status = "UNDETERMINED"
        defo_payload: dict[str, Any] = {
            "status": defo_status,
            "reason": "EUDR_LOSS_RASTER_PATH not set; deforestation area estimation not executed.",
        }
    else:
        try:
            defo_inputs = DeforestationAreaInputs(
                aoi_geojson=aoi_geojson,
                loss_raster_path=loss_raster_path,
                pixel_area_m2=pixel_area_m2,
            )
            defo_result = estimate_deforestation_area(defo_inputs)
            defo_payload = {
                "status": "OK",
                "result": asdict(defo_result),
            }
        except Exception as exc:
            # Keep deterministic-ish structure; message is still useful for operators.
            defo_payload = {
                "status": "ERROR",
                "error_type": exc.__class__.__name__,
                "error": str(exc),
                "inputs_fingerprint": fingerprint_deforestation_area_inputs(
                    DeforestationAreaInputs(
                        aoi_geojson=aoi_geojson,
                        loss_raster_path=loss_raster_path,
                        pixel_area_m2=pixel_area_m2,
                    )
                )
                if loss_raster_path
                else None,
            }

    results["deforestation"] = defo_payload

    # Maa-amet cross-check primitive (no fetching; deterministic compare).
    notes = f"max_parcels={max_parcels}" if max_parcels is not None else None
    maa_inputs = MaaAmetCrossCheckInputs(
        aoi_geojson=aoi_geojson,
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=None,
        observed_forest_area_m2=None,
        notes=notes,
    )
    maa_result = crosscheck_maa_amet(maa_inputs)
    results["maa_amet"] = asdict(maa_result)

    summary = {
        "status": "SCAFFOLD_ONLY",
        "notes": [
            "This report is a minimal deterministic scaffold; compliance logic will be iterated.",
        ],
    }

    provenance = {
        "git_commit": _git_commit(),
        "method_versions": {
            "deforestation_area": DEFORESTATION_AREA_METHOD_VERSION,
            "maa_amet_crosscheck": MAA_AMET_METHOD_VERSION,
        },
    }

    report: dict[str, Any] = {
        "run_id": run_id,
        "created_at_utc": now.isoformat(),
        "aoi_path": str(aoi_path),
        "summary": summary,
        "results": results,
        "parameters": params,
        "provenance": provenance,
        "eudr_requirements_coverage": {
            "status": "PLACEHOLDER",
            "notes": ["TODO: Map report sections to EUDR requirements coverage."],
        },
    }

    return report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m task3_eudr_reports.run_eudr_report_to_minio",
        description="Generate a minimal EUDR report and upload it to MinIO under deterministic keys.",
    )
    parser.add_argument("--aoi-geojson", required=True, help="Path to AOI GeoJSON")
    parser.add_argument(
        "--run-id",
        required=False,
        default=None,
        help="Deterministic run id (default: UTC timestamp YYYYMMDD_HHMMSS)",
    )
    parser.add_argument(
        "--max-parcels",
        required=False,
        default=None,
        type=int,
        help="Optional max parcels (recorded; passed as note to Maa-amet cross-check)",
    )
    parser.add_argument(
        "--out-local",
        required=False,
        default=None,
        help="Optional directory: also write JSON/HTML locally for debug/audit.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    run_id = args.run_id or _utc_run_id_now()
    aoi_path = Path(args.aoi_geojson).resolve()

    report = _build_report(run_id=run_id, aoi_path=aoi_path, max_parcels=args.max_parcels)
    html = _render_html_report(report)

    if args.out_local:
        out_dir = Path(args.out_local).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{run_id}.json").write_text(
            json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (out_dir / f"{run_id}.html").write_text(html, encoding="utf-8", newline="\n")

    uploaded = write_report(run_id=run_id, report_dict=report, html=html, map_html=None)

    # Structured final output for operators/logging.
    print(json.dumps({"run_id": run_id, "uploaded": uploaded}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
