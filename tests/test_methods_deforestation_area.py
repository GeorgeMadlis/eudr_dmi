from __future__ import annotations

import importlib.util

import pytest

from eudr_dmi.methods.deforestation_area import (
    DeforestationAreaInputs,
    fingerprint_deforestation_area_inputs,
    m2_to_ha,
)

from tests.fixtures import estonia_aoi_small_geojson


def test_inputs_fingerprint_is_stable_and_deterministic() -> None:
    poly_1 = estonia_aoi_small_geojson()
    poly_2 = estonia_aoi_small_geojson()
    aoi_1 = {
        "type": "Feature",
        "geometry": {
            "type": "Polygon",
            "coordinates": poly_1["coordinates"],
        },
        "properties": {},
    }
    aoi_2 = {
        "properties": {},
        "geometry": {
            "coordinates": poly_2["coordinates"],
            "type": "Polygon",
        },
        "type": "Feature",
    }

    inputs_1 = DeforestationAreaInputs(
        aoi_geojson=aoi_1,
        loss_raster_path="/tmp/loss.tif",
        pixel_area_m2=9.0,
        nodata=0,
        loss_value=1,
        crs_epsg=3857,
    )
    inputs_2 = DeforestationAreaInputs(
        aoi_geojson=aoi_2,
        loss_raster_path="/tmp/loss.tif",
        pixel_area_m2=9.0,
        nodata=0,
        loss_value=1,
        crs_epsg=3857,
    )

    assert fingerprint_deforestation_area_inputs(inputs_1) == fingerprint_deforestation_area_inputs(
        inputs_2
    )


def test_m2_to_ha_conversion_is_correct() -> None:
    assert m2_to_ha(0.0) == 0.0
    assert m2_to_ha(10_000.0) == 1.0
    assert m2_to_ha(25_000.0) == 2.5


def test_estimate_deforestation_area_raises_clear_error_when_rasterio_missing() -> None:

    """
    This test only applies when rasterio is absent; when rasterio is installed, we skip to avoid asserting an impossible failure mode.
    It is intentionally skipped if rasterio is installed. It only runs when rasterio is missing, to verify that a clear error is raised.
    No fixture data is required; the raster path is a dummy value.
    """
    if importlib.util.find_spec("rasterio") is not None:
        pytest.skip("rasterio installed; skip missing-dependency error test (intentional)")

    from eudr_dmi.methods.deforestation_area import estimate_deforestation_area

    inputs = DeforestationAreaInputs(
        aoi_geojson=estonia_aoi_small_geojson(),
        loss_raster_path="/tmp/does_not_matter.tif",
        pixel_area_m2=1.0,
    )

    with pytest.raises(RuntimeError) as excinfo:
        estimate_deforestation_area(inputs)

    assert "rasterio is required" in str(excinfo.value)
