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
    METHOD_VERSION as DEFORESTATION_AREA_METHOD_VERSION,
)
from eudr_dmi.methods.deforestation_area import (
    DeforestationAreaInputs,
    estimate_deforestation_area,
    fingerprint_deforestation_area_inputs,
    m2_to_ha,
)
from eudr_dmi.methods.maa_amet_crosscheck import (
    METHOD_VERSION as MAA_AMET_METHOD_VERSION,
)
from eudr_dmi.methods.maa_amet_crosscheck import (
    MaaAmetCrossCheckInputs,
    crosscheck_maa_amet,
)
from task3_eudr_reports.minio_report_writer import write_report

_HANSEN_DATASET_VERSION = "GFC-2024-v1.12"
_HANSEN_AUDIT_TILE_DIR = Path(
    f"/Users/server/audit/eudr_dmi/dependencies/hansen_gfc_tiles/{_HANSEN_DATASET_VERSION}"
)


def _extract_bbox(aoi_geojson: dict[str, Any]) -> dict[str, float]:
    def iter_coords(geom: dict[str, Any]) -> list[tuple[float, float]]:
        coords = geom.get("coordinates")
        gtype = geom.get("type")
        if coords is None or gtype is None:
            return []

        points: list[tuple[float, float]] = []
        if gtype == "Point":
            return [tuple(coords)]
        if gtype in {"MultiPoint", "LineString"}:
            return [tuple(c) for c in coords]
        if gtype in {"Polygon", "MultiLineString"}:
            for part in coords:
                points.extend([tuple(c) for c in part])
            return points
        if gtype == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    points.extend([tuple(c) for c in ring])
            return points
        return []

    geoms: list[dict[str, Any]] = []
    if aoi_geojson.get("type") == "FeatureCollection":
        for feature in aoi_geojson.get("features", []):
            if isinstance(feature, dict) and isinstance(feature.get("geometry"), dict):
                geoms.append(feature["geometry"])
    elif aoi_geojson.get("type") == "Feature":
        geom = aoi_geojson.get("geometry")
        if isinstance(geom, dict):
            geoms.append(geom)
    else:
        geoms.append(aoi_geojson)

    coords: list[tuple[float, float]] = []
    for g in geoms:
        coords.extend(iter_coords(g))

    if not coords:
        raise ValueError("AOI GeoJSON did not contain any coordinates")

    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return {
        "min_lon": float(min(lons)),
        "min_lat": float(min(lats)),
        "max_lon": float(max(lons)),
        "max_lat": float(max(lats)),
    }


def _load_hansen_server() -> Any:
    from mcp_servers.hansen_gfc_example import HansenGFCServer

    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "mcp_configs" / "mcp_Hansen_GFC.json"
    return HansenGFCServer(config_path)


def _ensure_hansen_tile(*, server: Any, layer: str, tile_id: str) -> dict[str, Any]:
    out_dir = _HANSEN_AUDIT_TILE_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    expected_path = out_dir / f"{layer}_{tile_id}.tif"

    url = None
    try:
        url = server.base_url + server.tile_pattern.format(layer=layer, tile_id=tile_id)
    except Exception:
        url = None

    if expected_path.exists():
        return {
            "status": "OK",
            "layer": layer,
            "tile_id": tile_id,
            "file_path": str(expected_path),
            "url": url,
            "note": "cache_hit",
        }

    allow_download = os.getenv("EUDR_DOWNLOAD_HANSEN_TILES") == "1"
    if not allow_download:
        return {
            "status": "MISSING",
            "layer": layer,
            "tile_id": tile_id,
            "expected_path": str(expected_path),
            "url": url,
            "note": "Set EUDR_DOWNLOAD_HANSEN_TILES=1 to allow downloading tiles automatically.",
        }

    result = server.download_tile(tile_id=tile_id, layer=layer, output_dir=out_dir)
    if result.get("status") == "success":
        return {
            "status": "OK",
            "layer": layer,
            "tile_id": tile_id,
            "file_path": result.get("file_path"),
            "url": result.get("url") or url,
            "note": "downloaded",
        }

    return {
        "status": "ERROR",
        "layer": layer,
        "tile_id": tile_id,
        "expected_path": str(expected_path),
        "error": result.get("error") or "unknown",
        "url": result.get("url") or url,
        "raw": result,
    }


def _pixel_area_m2_from_dataset(*, dataset: Any, override: float | None) -> tuple[float, str]:
    if override is not None:
        if override <= 0:
            raise ValueError("EUDR_PIXEL_AREA_M2 must be > 0 when set")
        return float(override), "override"

    if dataset.crs is None:
        raise ValueError("Raster CRS missing; provide EUDR_PIXEL_AREA_M2")
    if getattr(dataset.crs, "is_geographic", False):
        raise ValueError("Geographic CRS requires EUDR_PIXEL_AREA_M2")

    pixel_width = float(getattr(dataset.transform, "a", 0.0))
    pixel_height = float(getattr(dataset.transform, "e", 0.0))
    area = abs(pixel_width * pixel_height)
    if area <= 0:
        raise ValueError("Computed pixel area is not positive")
    return area, "from_raster_transform"


def _estimate_threshold_area(
    *,
    aoi_geojson: dict[str, Any],
    raster_path: str,
    threshold: float,
    pixel_area_m2_override: float | None,
) -> dict[str, Any]:
    import rasterio
    from rasterio.mask import mask

    geometries: list[dict[str, Any]] = []
    if aoi_geojson.get("type") == "FeatureCollection":
        for f in aoi_geojson.get("features", []):
            if isinstance(f, dict) and isinstance(f.get("geometry"), dict):
                geometries.append(f["geometry"])
    elif aoi_geojson.get("type") == "Feature":
        geom = aoi_geojson.get("geometry")
        if isinstance(geom, dict):
            geometries.append(geom)
    else:
        geometries.append(aoi_geojson)

    if not geometries:
        raise ValueError("AOI GeoJSON did not contain any geometries")

    # rasterio.mask accepts GeoJSON-like mappings; shapely mapping not required here.
    with rasterio.open(raster_path) as dataset:
        masked, _ = mask(dataset, geometries, crop=True, filled=False)
        band = masked[0]
        data = band.data
        mask_arr = band.mask

        valid = ~mask_arr
        excluded_pixels = int(mask_arr.sum())

        pixel_area_m2, pixel_area_source = _pixel_area_m2_from_dataset(
            dataset=dataset,
            override=pixel_area_m2_override,
        )

        counted = valid & (data >= threshold)
        counted_pixels = int(counted.sum())
        area_m2 = float(counted_pixels) * float(pixel_area_m2)

        return {
            "threshold": threshold,
            "counted_pixels": counted_pixels,
            "excluded_pixels": excluded_pixels,
            "pixel_area_m2": pixel_area_m2,
            "pixel_area_source": pixel_area_source,
            "area_m2": area_m2,
            "area_ha": m2_to_ha(area_m2),
        }


def _geometry_area_ha_wgs84(geometry: dict[str, Any]) -> float:
    from pyproj import Transformer
    from shapely.geometry import shape
    from shapely.ops import transform

    geom = shape(geometry)
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:3301", always_xy=True)
    projected = transform(transformer.transform, geom)
    return float(projected.area) / 10000.0


def _maa_amet_query(
    *,
    aoi_geojson: dict[str, Any],
    max_features: int | None,
) -> dict[str, Any]:
    from mcp_servers.maaamet_mcp import MaaametServer

    repo_root = Path(__file__).resolve().parents[2]
    config_path = repo_root / "config" / "mcp_configs" / "mcp_Maa-amet_Geoportaal.json"

    bbox = _extract_bbox(aoi_geojson)
    layer = os.getenv("EUDR_MAA_AMET_WFS_LAYER") or "kataster:ky_kehtiv"
    srs = os.getenv("EUDR_MAA_AMET_WFS_SRS") or "EPSG:4326"
    limit = max_features if max_features is not None else 50

    server = MaaametServer(config_path=config_path, duckdb_path=False)
    data = server.fetch_wfs_features(layer=layer, bbox=bbox, srs=srs, max_features=limit)

    parcels: list[dict[str, Any]] = []
    total_area_ha = 0.0
    for feature in data.get("features", []):
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties") or {}
        geom = feature.get("geometry") or {}

        parcel_id = None
        for key in [
            "tunnus",
            "katastritunnus",
            "KY_TUNNUS",
            "id",
            "ID",
        ]:
            if isinstance(props, dict) and props.get(key):
                parcel_id = str(props.get(key))
                break

        if parcel_id is None:
            parcel_id = "(missing)"

        area_ha = None
        area_source = "unknown"

        if isinstance(props, dict):
            for key in [
                "forest_area_ha",
                "metsamaa_ha",
                "mets_ha",
                "pindala_ha",
                "area_ha",
            ]:
                if props.get(key) is not None:
                    try:
                        area_ha = float(props.get(key))
                        area_source = f"property:{key}"
                        break
                    except Exception:
                        pass

        if area_ha is None and isinstance(geom, dict) and geom.get("type"):
            area_ha = _geometry_area_ha_wgs84(geom)
            area_source = "geometry_area_epsg3301"

        if area_ha is not None:
            total_area_ha += float(area_ha)

        parcels.append(
            {
                "parcel_id": parcel_id,
                "forest_area_ha": area_ha,
                "forest_area_source": area_source,
            }
        )

    return {
        "status": "OK",
        "layer": layer,
        "srs": srs,
        "bbox": bbox,
        "query_metadata": data.get("_query_metadata", {}),
        "parcel_count": len(parcels),
        "parcels": parcels,
        "aggregated_forest_area_ha": total_area_ha,
        "aggregated_forest_area_m2": total_area_ha * 10000.0,
        "notes": [
            (
                "If the Maa-amet layer does not expose a forest-area attribute, this report uses "
                "geometry area as a proxy."
            ),
            "Override layer via EUDR_MAA_AMET_WFS_LAYER if needed.",
        ],
    }


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
        "<li>Hansen GFC tile selection is deterministic from AOI bbox (10° tiles).</li>"
        "<li>Maa-amet parcels are fetched via the public WFS endpoint; the layer can be overridden "
        "via environment.</li>"
        "</ul>"
    )

    style = "".join(
        [
            "body{font-family:system-ui, -apple-system, Segoe UI, Roboto, sans-serif; ",
            "max-width: 960px; margin: 2rem auto; padding: 0 1rem;}",
            "table{border-collapse:collapse;width:100%;}",
            "td,th{border:1px solid #ddd;padding:8px;}",
            "th{background:#f6f6f6;text-align:left;}",
            "code{background:#f2f2f2;padding:2px 4px;border-radius:4px;}",
        ]
    )

    run_meta_html = "".join(
        [
            "<p><b>run_id</b>: <code>",
            run_id,
            "</code><br><b>created_at_utc</b>: <code>",
            created_at,
            "</code></p>",
        ]
    )

    summary_html = html_lib.escape(json.dumps(summary, indent=2, sort_keys=True))
    results_html = html_lib.escape(json.dumps(results, indent=2, sort_keys=True))

    return "".join(
        [
            "<!doctype html>",
            "<html><head><meta charset='utf-8'><title>EUDR Report</title>",
            "<style>",
            style,
            "</style>",
            "</head><body>",
            "<h1>EUDR Report</h1>",
            run_meta_html,
            "<h2>Summary</h2>",
            "<pre>",
            summary_html,
            "</pre>",
            "<h2>Results</h2>",
            "<pre>",
            results_html,
            "</pre>",
            "<h2>Key metrics</h2>",
            "<table><thead><tr><th>Metric</th><th>Value</th></tr></thead><tbody>",
            metrics_rows,
            "</tbody></table>",
            "<h2>Assumptions / limitations</h2>",
            assumptions,
            "</body></html>",
        ]
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
    pixel_area_m2 = _env_float("EUDR_PIXEL_AREA_M2")
    loss_raster_path = _env_optional("EUDR_LOSS_RASTER_PATH")

    hansen_meta: dict[str, Any] = {"status": "UNDETERMINED"}
    if not loss_raster_path:
        try:
            bbox = _extract_bbox(aoi_geojson)
            hansen = _load_hansen_server()
            tiles = hansen.list_tiles(layer="loss", **bbox)
            tile_ids = [t.get("tile_id") for t in tiles.get("tiles", []) if isinstance(t, dict)]
            tile_ids = [t for t in tile_ids if isinstance(t, str)]

            hansen_meta = {
                "status": "OK" if tile_ids else "UNDETERMINED",
                "dataset": _HANSEN_DATASET_VERSION,
                "bbox": bbox,
                "loss_tiles": tile_ids,
                "audit_tile_dir": str(_HANSEN_AUDIT_TILE_DIR),
            }

            if tile_ids:
                if len(tile_ids) != 1:
                    hansen_meta["note"] = (
                        "AOI spans multiple Hansen tiles; using the first tile only."
                    )
                selected = tile_ids[0]
                loss_tile = _ensure_hansen_tile(server=hansen, layer="loss", tile_id=selected)
                hansen_meta["loss_tile"] = loss_tile
                if loss_tile.get("status") == "OK":
                    loss_raster_path = str(loss_tile.get("file_path"))

                # Also compute Hansen tree cover (2000) area for a crude forest-area proxy.
                tc_tile = _ensure_hansen_tile(
                    server=hansen,
                    layer="treecover2000",
                    tile_id=selected,
                )
                hansen_meta["treecover2000_tile"] = tc_tile
        except Exception as exc:
            hansen_meta = {
                "status": "ERROR",
                "error_type": exc.__class__.__name__,
                "error": str(exc),
            }

    results["hansen"] = hansen_meta

    if not loss_raster_path:
        results["deforestation"] = {
            "status": "UNDETERMINED",
            "reason": (
                "No loss raster path resolved (EUDR_LOSS_RASTER_PATH unset and "
                "Hansen selection failed)."
            ),
        }
        hansen_loss_area_m2 = None
    else:
        try:
            defo_inputs = DeforestationAreaInputs(
                aoi_geojson=aoi_geojson,
                loss_raster_path=loss_raster_path,
                pixel_area_m2=pixel_area_m2,
            )
            defo_result = estimate_deforestation_area(defo_inputs)
            results["deforestation"] = {
                "status": "OK",
                "loss_raster_path": loss_raster_path,
                "raster_version": _HANSEN_DATASET_VERSION if "hansen" in results else None,
                "pixel_area_m2_override": pixel_area_m2,
                "result": asdict(defo_result),
            }
            hansen_loss_area_m2 = defo_result.loss_area_m2
        except Exception as exc:
            results["deforestation"] = {
                "status": "ERROR",
                "error_type": exc.__class__.__name__,
                "error": str(exc),
                "loss_raster_path": loss_raster_path,
                "pixel_area_m2_override": pixel_area_m2,
                "inputs_fingerprint": fingerprint_deforestation_area_inputs(
                    DeforestationAreaInputs(
                        aoi_geojson=aoi_geojson,
                        loss_raster_path=loss_raster_path,
                        pixel_area_m2=pixel_area_m2,
                    )
                ),
            }
            hansen_loss_area_m2 = None

    # Maa-amet cross-check (real WFS query + deterministic comparison payload).
    maa_payload: dict[str, Any]
    maa_obs_m2: float | None = None
    try:
        maa_payload = _maa_amet_query(aoi_geojson=aoi_geojson, max_features=max_parcels)
        maa_obs_m2 = maa_payload.get("aggregated_forest_area_m2")
    except Exception as exc:
        maa_payload = {
            "status": "ERROR",
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }

    # Hansen-derived forest area proxy (treecover2000 >= 30%).
    hansen_expected_m2: float | None = None
    try:
        hansen_tc_tile = (results.get("hansen") or {}).get("treecover2000_tile") or {}
        tc_path = hansen_tc_tile.get("file_path")
        if isinstance(tc_path, str) and tc_path:
            tc_stats = _estimate_threshold_area(
                aoi_geojson=aoi_geojson,
                raster_path=tc_path,
                threshold=30.0,
                pixel_area_m2_override=pixel_area_m2,
            )
            results["hansen"]["treecover2000_forest_area_threshold30"] = tc_stats
            forest_2000_m2 = float(tc_stats["area_m2"])
            loss_m2 = float(hansen_loss_area_m2) if hansen_loss_area_m2 is not None else 0.0
            hansen_expected_m2 = max(forest_2000_m2 - loss_m2, 0.0)
            results["hansen"]["derived_forest_area_m2"] = hansen_expected_m2
            results["hansen"]["derived_forest_area_ha"] = m2_to_ha(hansen_expected_m2)
            results["hansen"]["derived_forest_area_note"] = (
                "Derived as treecover2000>=30% area minus loss area (binary loss 2001-2024)."
            )
    except Exception as exc:
        results.setdefault("hansen", {})
        results["hansen"]["forest_area_derivation_error"] = {
            "error_type": exc.__class__.__name__,
            "error": str(exc),
        }

    maa_notes = f"max_parcels={max_parcels}" if max_parcels is not None else None
    cross_inputs = MaaAmetCrossCheckInputs(
        aoi_geojson=aoi_geojson,
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=hansen_expected_m2,
        observed_forest_area_m2=float(maa_obs_m2) if maa_obs_m2 is not None else None,
        notes=maa_notes,
    )
    cross_result = crosscheck_maa_amet(cross_inputs)
    discrepancy_pct = None
    if cross_result.delta_ratio is not None:
        discrepancy_pct = float(cross_result.delta_ratio) * 100.0

    rule_status = "UNDETERMINED"
    if cross_result.status == "PASS":
        rule_status = "PASS"

    results["maa_amet"] = {
        "query": maa_payload,
        "comparison": {
            "status": rule_status,
            "expected_forest_area_m2": hansen_expected_m2,
            "expected_forest_area_ha": m2_to_ha(hansen_expected_m2) if hansen_expected_m2 else None,
            "observed_forest_area_m2": maa_obs_m2,
            "observed_forest_area_ha": (float(maa_obs_m2) / 10000.0) if maa_obs_m2 else None,
            "discrepancy_pct": discrepancy_pct,
            "tolerance_ratio": cross_inputs.tolerance_ratio,
            "deterministic_rule": (
                "PASS if discrepancy_pct <= tolerance_ratio*100 else UNDETERMINED"
            ),
            "raw_crosscheck": asdict(cross_result),
        },
    }

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
        description=(
            "Generate a minimal EUDR report and upload it to MinIO under deterministic keys."
        ),
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
    parser.add_argument(
        "--skip-minio",
        action="store_true",
        help="Do not upload to MinIO (useful for local/offline runs).",
    )
    parser.add_argument(
        "--minio-credentials-file",
        required=False,
        default=None,
        help=(
            "Optional path to a local credentials summary file that contains MINIO_* values. "
            "Only used to populate missing environment variables."
        ),
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

    uploaded: dict[str, str] | None = None
    if not args.skip_minio:
        if args.minio_credentials_file:
            os.environ.setdefault("EUDR_MINIO_CREDENTIALS_FILE", args.minio_credentials_file)
        uploaded = write_report(run_id=run_id, report_dict=report, html=html, map_html=None)

    # Structured final output for operators/logging.
    print(json.dumps({"run_id": run_id, "uploaded": uploaded}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
