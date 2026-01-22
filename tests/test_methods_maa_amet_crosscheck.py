from __future__ import annotations

from eudr_dmi.methods.maa_amet_crosscheck import (
    MaaAmetCrossCheckInputs,
    crosscheck_maa_amet,
    fingerprint_maa_amet_inputs,
)

from tests.fixtures import ESTONIA_AOI_SMALL_GEOJSON, estonia_aoi_small_geojson


def test_inconclusive_when_missing_values() -> None:
    inputs = MaaAmetCrossCheckInputs(
        aoi_geojson=estonia_aoi_small_geojson(),
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=None,
        observed_forest_area_m2=100.0,
    )
    result = crosscheck_maa_amet(inputs)
    assert result.status == "INCONCLUSIVE"
    assert result.delta_m2 is None
    assert result.delta_ratio is None
    assert any("Missing expected_forest_area_m2" in m for m in result.messages)


def test_pass_within_tolerance() -> None:
    inputs = MaaAmetCrossCheckInputs(
        aoi_geojson=estonia_aoi_small_geojson(),
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=100.0,
        observed_forest_area_m2=104.0,
        tolerance_ratio=0.05,
    )
    result = crosscheck_maa_amet(inputs)
    assert result.status == "PASS"
    assert result.delta_m2 == 4.0
    assert result.delta_ratio is not None
    assert result.delta_ratio <= inputs.tolerance_ratio


def test_fail_outside_tolerance() -> None:
    inputs = MaaAmetCrossCheckInputs(
        aoi_geojson=estonia_aoi_small_geojson(),
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=100.0,
        observed_forest_area_m2=120.0,
        tolerance_ratio=0.05,
    )
    result = crosscheck_maa_amet(inputs)
    assert result.status == "FAIL"
    assert result.delta_m2 == 20.0
    assert result.delta_ratio is not None
    assert result.delta_ratio > inputs.tolerance_ratio


def test_inputs_fingerprint_is_deterministic() -> None:
    coords = ESTONIA_AOI_SMALL_GEOJSON["coordinates"]
    aoi_1 = {"coordinates": coords, "type": "Polygon"}
    aoi_2 = {"type": "Polygon", "coordinates": coords}

    inputs_1 = MaaAmetCrossCheckInputs(
        aoi_geojson=aoi_1,
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=100.0,
        observed_forest_area_m2=104.0,
        tolerance_ratio=0.05,
        notes=None,
    )
    inputs_2 = MaaAmetCrossCheckInputs(
        aoi_geojson=aoi_2,
        maa_amet_layer_ref="maa-amet/forest/v1",
        expected_forest_area_m2=100.0,
        observed_forest_area_m2=104.0,
        tolerance_ratio=0.05,
        notes=None,
    )

    assert fingerprint_maa_amet_inputs(inputs_1) == fingerprint_maa_amet_inputs(inputs_2)
