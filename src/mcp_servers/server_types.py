# geodmi_mcp/server_types.py

from __future__ import annotations
from enum import Enum
from typing import List
from .models import DatasetRecord


class MCPServerType(str, Enum):
    BIODIVERSITY = "biodiversity_occurrences"
    EO_CLIMATE = "eo_climate"
    NATIONAL_ADMIN = "national_cadastral_admin"
    SOCIO_ECONOMIC = "socio_economic"
    COPERNICUS_LANDCOVER = "copernicus_landcover"
    DYNAMIC_WORLD = "dynamic_world"
    GEOBON_EBV = "geobon_ebv"
    WDPA_PROTECTED_AREAS = "wdpa_protected_areas"


def infer_server_type(record: DatasetRecord) -> MCPServerType:
    """
    Simple heuristic. You can refine using Task-1 'family' / 'provider'.
    """
    if record.thematic_type == "biodiversity":
        return MCPServerType.BIODIVERSITY
    if record.thematic_type in {"climate", "land_cover", "forest", "ocean"}:
        return MCPServerType.EO_CLIMATE
    if record.thematic_type in {"administrative", "hydrology"}:
        return MCPServerType.NATIONAL_ADMIN
    if record.thematic_type == "socio_economic":
        return MCPServerType.SOCIO_ECONOMIC
    # Default: fall back to provider-based logic, or EO:
    return MCPServerType.EO_CLIMATE


def group_by_server_type(records: List[DatasetRecord]) -> dict[MCPServerType, List[DatasetRecord]]:
    result: dict[MCPServerType, List[DatasetRecord]] = {t: [] for t in MCPServerType}
    for r in records:
        result[infer_server_type(r)].append(r)
    return result
