from __future__ import annotations

from tests.fixtures import ESTONIA_AOI_SMALL_GEOJSON


def test_estonia_aoi_small_geojson_is_valid_and_small() -> None:
    aoi = ESTONIA_AOI_SMALL_GEOJSON

    assert aoi.get("type") == "Polygon"
    coords = aoi.get("coordinates")
    assert isinstance(coords, list) and len(coords) == 1

    ring = coords[0]
    assert isinstance(ring, list)
    assert len(ring) >= 4

    first = ring[0]
    last = ring[-1]
    assert first == last, "Ring must be closed (first == last)."

    lons = [pt[0] for pt in ring]
    lats = [pt[1] for pt in ring]

    lon_span = max(lons) - min(lons)
    lat_span = max(lats) - min(lats)

    assert lon_span <= 0.2
    assert lat_span <= 0.2
