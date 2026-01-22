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


@dataclass(frozen=True, slots=True)
class MaaAmetCrossCheckInputs:
    aoi_geojson: dict
    maa_amet_layer_ref: str
    expected_forest_area_m2: float | None
    observed_forest_area_m2: float | None
    tolerance_ratio: float = 0.05
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class MaaAmetCrossCheckResult:
    status: str  # "PASS" | "FAIL" | "INCONCLUSIVE"
    delta_m2: float | None
    delta_ratio: float | None
    tolerance_ratio: float
    method_version: str
    inputs_fingerprint: str
    messages: list[str]


def fingerprint_maa_amet_inputs(inputs: MaaAmetCrossCheckInputs) -> str:
    """Deterministic sha256 fingerprint of non-binary inputs.

    Note: this intentionally does not hash external datasets or file contents.
    """

    payload: dict[str, Any] = {
        "aoi_geojson": inputs.aoi_geojson,
        "maa_amet_layer_ref": inputs.maa_amet_layer_ref,
        "expected_forest_area_m2": inputs.expected_forest_area_m2,
        "observed_forest_area_m2": inputs.observed_forest_area_m2,
        "tolerance_ratio": inputs.tolerance_ratio,
        "notes": inputs.notes,
        "method_version": METHOD_VERSION,
    }
    return _fingerprint_payload(payload)


def crosscheck_maa_amet(inputs: MaaAmetCrossCheckInputs) -> MaaAmetCrossCheckResult:
    """Cross-check a forest area figure against Maa-amet-derived observation.

    Deterministic: no timestamps, no randomness.
    """

    messages: list[str] = []
    fingerprint = fingerprint_maa_amet_inputs(inputs)

    if inputs.expected_forest_area_m2 is None or inputs.observed_forest_area_m2 is None:
        if inputs.expected_forest_area_m2 is None:
            messages.append("Missing expected_forest_area_m2.")
        if inputs.observed_forest_area_m2 is None:
            messages.append("Missing observed_forest_area_m2.")
        return MaaAmetCrossCheckResult(
            status="INCONCLUSIVE",
            delta_m2=None,
            delta_ratio=None,
            tolerance_ratio=inputs.tolerance_ratio,
            method_version=METHOD_VERSION,
            inputs_fingerprint=fingerprint,
            messages=messages,
        )

    expected = float(inputs.expected_forest_area_m2)
    observed = float(inputs.observed_forest_area_m2)

    delta_m2 = abs(expected - observed)
    tiny = 1e-12
    denom = max(abs(expected), tiny)
    delta_ratio = delta_m2 / denom

    status = "PASS" if delta_ratio <= inputs.tolerance_ratio else "FAIL"
    messages.append(
        " ".join(
            [
                f"delta_ratio={delta_ratio:.12g}",
                f"tolerance_ratio={inputs.tolerance_ratio:.12g}",
                f"status={status}",
            ]
        )
    )

    return MaaAmetCrossCheckResult(
        status=status,
        delta_m2=delta_m2,
        delta_ratio=delta_ratio,
        tolerance_ratio=inputs.tolerance_ratio,
        method_version=METHOD_VERSION,
        inputs_fingerprint=fingerprint,
        messages=messages,
    )
