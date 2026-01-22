#!/usr/bin/env python3
"""Demo: Fetch Maa-amet cadastral parcels for the Estonia test area.

This script replicates the manual example used during development:
1. Reads the bounding polygon from ``data_examples/estonia_testland1.geojson``.
2. Builds a WGS84 bounding box and calls :class:`MaaametServer`'s WFS helper,
    which is now configurable via MCP config metadata (endpoint, layer, etc.).
3. Saves the resulting GeoJSON feature collection (including the query metadata)
    to ``data_examples/maaamet_cadastral_plots_estonia_testland1.json``.

Usage (defaults to the paths above):
    python demo_mcp_maaamet.py \
        --geojson data_examples/estonia_testland1.geojson \
          --output data_examples/maaamet_cadastral_plots_estonia_testland1.json \
          --max-features 50 \
          --config config/mcp_configs/mcp_Maaamet_Estonia.json

Pass ``--max-features 0`` if you need the full response (expect a multi-MB file).

The script is intentionally self-contained so it can be referenced by future
agents/subtasks without needing the MCP runtime.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple


# Constants describing the Maa-amet cadastral service we call.
LAYER_NAME = "kataster:ky_kehtiv"

REPO_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_INPUT = REPO_ROOT / "data_examples" / "estonia_testland1.geojson"
DEFAULT_OUTPUT = (
    REPO_ROOT / "data_examples" / "maaamet_cadastral_plots_estonia_testland1.json"
)
DEFAULT_CONFIG = REPO_ROOT / "config" / "mcp_configs" / "mcp_Maaamet_Estonia.json"
DEFAULT_DUCKDB = REPO_ROOT / "data_db" / "geodata_catalogue.duckdb"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Download Maa-amet cadastral plots intersecting a bounding box.")
    parser.add_argument("--geojson", type=Path, default=DEFAULT_INPUT,
                        help="Input GeoJSON polygon defining the AOI (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Where to write the resulting feature collection (default: %(default)s)")
    parser.add_argument("--layer", default=LAYER_NAME,
                        help="Qualified WFS layer name to query (default: %(default)s)")
    parser.add_argument("--max-features", type=int, default=50,
                        help="Limit the number of features saved (0 = unlimited, default: %(default)s)")
    parser.add_argument("--srs", default="EPSG:4326",
                        help="Coordinate reference system used for the bbox filter (default: %(default)s)")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG,
                        help="Path to the Maa-amet MCP config JSON (default: %(default)s)")
    parser.add_argument("--duckdb", type=Path, default=DEFAULT_DUCKDB,
                        help="Optional DuckDB catalogue for metadata enrichment (default: %(default)s)")
    return parser.parse_args(argv)


def iter_coordinates(geometry: Dict[str, Any]) -> Iterable[Tuple[float, float]]:
    """Yield all coordinate tuples contained within a GeoJSON geometry."""
    gtype = geometry["type"]
    coords = geometry["coordinates"]

    if gtype == "Point":
        yield tuple(coords)
    elif gtype in {"MultiPoint", "LineString"}:
        for coord in coords:
            yield tuple(coord)
    elif gtype in {"Polygon", "MultiLineString"}:
        for part in coords:
            for coord in part:
                yield tuple(coord)
    elif gtype == "MultiPolygon":
        for poly in coords:
            for ring in poly:
                for coord in ring:
                    yield tuple(coord)
    else:
        raise ValueError(f"Unsupported geometry type: {gtype}")


def compute_bbox(feature_collection: Dict[str, Any]) -> Dict[str, float]:
    """Compute the min/max lon/lat for a GeoJSON feature collection."""
    coords: List[Tuple[float, float]] = []
    for feature in feature_collection.get("features", []):
        geometry = feature.get("geometry")
        if geometry:
            coords.extend(iter_coordinates(geometry))

    if not coords:
        raise RuntimeError("No coordinates found in input GeoJSON")

    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return {
        "min_lon": min(lons),
        "min_lat": min(lats),
        "max_lon": max(lons),
        "max_lat": max(lats),
    }


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Delay MCP server imports so `--help` works without optional deps (e.g., duckdb).
    from mcp_servers.maaamet_mcp import MaaametServer

    if not args.geojson.exists():
        raise FileNotFoundError(f"GeoJSON input not found: {args.geojson}")

    with args.geojson.open("r", encoding="utf-8") as src:
        feature_collection = json.load(src)

    bbox = compute_bbox(feature_collection)
    print(f"Computed bbox: {bbox}")

    server = MaaametServer(config_path=args.config, duckdb_path=args.duckdb)
    result = server.fetch_wfs_features(
        layer=args.layer,
        bbox=bbox,
        srs=args.srs,
        max_features=args.max_features,
    )
    fetched = result['_query_metadata']['fetched_feature_count']
    metadata = result.get("_query_metadata", {})
    saved = metadata.get("saved_feature_count", len(result.get("features", [])))
    if metadata.get("note"):
        print(f"Fetched {fetched} parcels (saved first {saved}) from {args.layer}")
    else:
        print(f"Fetched {fetched} cadastral parcels from {args.layer}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as dst:
        json.dump(result, dst, ensure_ascii=False, indent=2)
    print(f"Saved output to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
