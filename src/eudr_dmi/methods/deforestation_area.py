from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any

METHOD_VERSION = "0.1.0"


def _canonicalize_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _canonicalize_json(value[k]) for k in sorted(value)}
    if isinstance(value, list):
        return [_canonicalize_json(v) for v in value]
    return value


def _sha256_hexdigest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _fingerprint_payload(payload: dict[str, Any]) -> str:
    canonical = _canonicalize_json(payload)
    data = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )
    return _sha256_hexdigest(data)


def m2_to_ha(area_m2: float) -> float:
    return area_m2 / 10000.0


@dataclass(frozen=True, slots=True)
class DeforestationAreaInputs:
    aoi_geojson: dict
    loss_raster_path: str
    pixel_area_m2: float | None = None
    nodata: int | float | None = None
    loss_value: int | float = 1
    crs_epsg: int | None = None


@dataclass(frozen=True, slots=True)
class DeforestationAreaResult:
    loss_area_m2: float
    loss_area_ha: float
    counted_pixels: int
    excluded_pixels: int
    method_version: str
    inputs_fingerprint: str
    warnings: list[str]


def fingerprint_deforestation_area_inputs(inputs: DeforestationAreaInputs) -> str:
    """Deterministic sha256 fingerprint of non-binary inputs.

    Note: this intentionally does not hash raster file contents.
    """

    payload: dict[str, Any] = {
        "aoi_geojson": inputs.aoi_geojson,
        "loss_raster_path": inputs.loss_raster_path,
        "nodata": inputs.nodata,
        "loss_value": inputs.loss_value,
        "pixel_area_m2": inputs.pixel_area_m2,
        "crs_epsg": inputs.crs_epsg,
        "method_version": METHOD_VERSION,
    }
    return _fingerprint_payload(payload)


def _require_rasterio() -> Any:
    try:
        import rasterio  # type: ignore[import-not-found]

        return rasterio
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "rasterio is required for deforestation area estimation. "
            "Install with: pip install rasterio"
        ) from exc


def _extract_geometries(aoi_geojson: dict) -> list[dict]:
    # Accept Geometry / Feature / FeatureCollection
    if aoi_geojson.get("type") == "FeatureCollection":
        features = aoi_geojson.get("features") or []
        geometries = [f.get("geometry") for f in features if isinstance(f, dict)]
        return [g for g in geometries if isinstance(g, dict)]

    if aoi_geojson.get("type") == "Feature":
        geometry = aoi_geojson.get("geometry")
        return [geometry] if isinstance(geometry, dict) else []

    return [aoi_geojson]


def _compute_pixel_area_m2(
    *,
    raster_crs: Any | None,
    transform: Any,
    pixel_area_override: float | None,
    crs_epsg_hint: int | None,
    warnings: list[str],
) -> float:
    if pixel_area_override is not None:
        if pixel_area_override <= 0:
            raise ValueError("pixel_area_m2 must be > 0 when provided.")
        return float(pixel_area_override)

    # CRS hint only used if raster lacks CRS.
    crs = raster_crs
    if crs is None and crs_epsg_hint is not None:
        try:
            from rasterio.crs import CRS  # type: ignore[import-not-found]

            crs = CRS.from_epsg(int(crs_epsg_hint))
        except Exception:
            crs = None

    if crs is None:
        raise ValueError(
            "Cannot determine pixel area without a projected CRS. "
            "Provide pixel_area_m2 or ensure raster has a CRS."
        )

    if getattr(crs, "is_geographic", False):
        warnings.append(
            "Raster CRS is geographic; pixel area in m^2 is not derivable from transform alone."
        )
        raise ValueError("Geographic CRS requires pixel_area_m2 to be provided explicitly.")

    # For projected CRS, assume transform units are linear (typically meters).
    pixel_width = float(getattr(transform, "a", 0.0))
    pixel_height = float(getattr(transform, "e", 0.0))
    area = abs(pixel_width * pixel_height)
    if area <= 0:
        raise ValueError("Computed pixel area is not positive; check raster transform.")
    return area


def estimate_deforestation_area(inputs: DeforestationAreaInputs) -> DeforestationAreaResult:
    """Estimate deforestation area within AOI by counting loss pixels.

    Uses rasterio.mask to crop the loss raster to the AOI and counts pixels == loss_value,
    excluding nodata.

    Deterministic: no timestamps, no randomness.
    """

    rasterio = _require_rasterio()

    warnings: list[str] = []
    inputs_fingerprint = fingerprint_deforestation_area_inputs(inputs)

    geometries = _extract_geometries(inputs.aoi_geojson)
    if not geometries:
        raise ValueError("AOI GeoJSON did not contain any geometries.")

    # Optional: validate geometries if shapely is available.
    try:  # pragma: no cover
        from shapely.geometry import mapping, shape  # type: ignore[import-not-found]

        geometries = [mapping(shape(g)) for g in geometries]
    except Exception:
        pass

    with rasterio.open(inputs.loss_raster_path) as dataset:
        from rasterio.mask import mask  # type: ignore[import-not-found]

        masked, _ = mask(dataset, geometries, crop=True, filled=False)
        band = masked[0]

        data = band.data
        mask_arr = band.mask

        nodata_value = inputs.nodata if inputs.nodata is not None else dataset.nodata

        valid = ~mask_arr
        excluded_pixels = int(mask_arr.sum())

        if nodata_value is not None:
            nodata_mask = valid & (data == nodata_value)
            excluded_pixels += int(nodata_mask.sum())
            valid = valid & ~nodata_mask

        counted = valid & (data == inputs.loss_value)
        counted_pixels = int(counted.sum())

        pixel_area_m2 = _compute_pixel_area_m2(
            raster_crs=dataset.crs,
            transform=dataset.transform,
            pixel_area_override=inputs.pixel_area_m2,
            crs_epsg_hint=inputs.crs_epsg,
            warnings=warnings,
        )

    loss_area_m2 = float(counted_pixels) * float(pixel_area_m2)

    return DeforestationAreaResult(
        loss_area_m2=loss_area_m2,
        loss_area_ha=m2_to_ha(loss_area_m2),
        counted_pixels=counted_pixels,
        excluded_pixels=excluded_pixels,
        method_version=METHOD_VERSION,
        inputs_fingerprint=inputs_fingerprint,
        warnings=warnings,
    )
