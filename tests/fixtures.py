from __future__ import annotations

import copy

# A small (0.1° x 0.1°) AOI rectangle centered near Estonia's center (WGS84 lon/lat).
# lon span: 24.95..25.05 (0.10)
# lat span: 58.55..58.65 (0.10)
ESTONIA_AOI_SMALL_GEOJSON: dict = {
    "type": "Polygon",
    "coordinates": [
        [
            [24.95, 58.55],
            [25.05, 58.55],
            [25.05, 58.65],
            [24.95, 58.65],
            [24.95, 58.55],
        ]
    ],
}


def estonia_aoi_small_geojson() -> dict:
    """Return a deep copy of the shared Estonia AOI GeoJSON.

    Tests should treat fixtures as immutable; a deep copy prevents accidental mutation.
    """

    return copy.deepcopy(ESTONIA_AOI_SMALL_GEOJSON)
