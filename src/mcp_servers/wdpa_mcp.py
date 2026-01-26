#!/usr/bin/env python
"""
wdpa_mcp.py

Task 2 MCP Server implementation for World Database on Protected Areas (WDPA).

Provides tools to discover and access protected area boundaries, management
categories, and conservation status from UNEP-WCMC and IUCN.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class WDPAServer:
    """
    MCP Server implementation for World Database on Protected Areas.
    
    Provides tools to list protected areas within a bounding box and
    retrieve detailed information about specific protected areas.
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "wdpa_protected_areas"
    ):
        self.config = self._load_config(config_path) if config_path else {}
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # WDPA configuration
        self.portal_url = "https://www.protectedplanet.net/"
        self.api_endpoint = self.config.get(
            "api_endpoint",
            "https://api.protectedplanet.net/"
        )
        self.download_url = "https://www.protectedplanet.net/en/thematic-areas/wdpa"
        
        # IUCN Management Categories
        self.iucn_categories = [
            {
                "code": "Ia",
                "name": "Strict Nature Reserve",
                "description": "Strictly protected for biodiversity and geological/geomorphological features"
            },
            {
                "code": "Ib",
                "name": "Wilderness Area",
                "description": "Large unmodified or slightly modified areas, retaining natural character"
            },
            {
                "code": "II",
                "name": "National Park",
                "description": "Large natural or near-natural areas set aside to protect ecological processes"
            },
            {
                "code": "III",
                "name": "Natural Monument or Feature",
                "description": "Areas containing specific natural features of outstanding value"
            },
            {
                "code": "IV",
                "name": "Habitat/Species Management Area",
                "description": "Areas requiring active conservation interventions"
            },
            {
                "code": "V",
                "name": "Protected Landscape/Seascape",
                "description": "Areas where interaction of people and nature has produced distinctive character"
            },
            {
                "code": "VI",
                "name": "Protected Area with Sustainable Use",
                "description": "Areas conserving ecosystems with sustainable natural resource management"
            },
            {
                "code": "Not Reported",
                "name": "Not Reported",
                "description": "Category not assigned or reported"
            }
        ]
        
        # Governance types
        self.governance_types = [
            {"code": "A", "name": "Governance by government"},
            {"code": "B", "name": "Shared governance"},
            {"code": "C", "name": "Private governance"},
            {"code": "D", "name": "Governance by indigenous peoples and local communities"}
        ]
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load MCP configuration from JSON file."""
        if not config_path or not config_path.exists():
            return {}
        with config_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    
    def _load_catalogue_metadata(
        self, 
        duckdb_path: Optional[Path],
        dataset_id: str
    ) -> Dict[str, Any]:
        """Load dataset metadata from Task 1 catalogue database."""
        if duckdb_path is False:
            return {}
            
        if duckdb_path is None:
            duckdb_path = Path(__file__).parent.parent / "data_db" / "geodata_catalogue.duckdb"
        
        if not duckdb_path.exists():
            return {}
        
        try:
            con = duckdb.connect(str(duckdb_path), read_only=True)
            result = con.execute(
                "SELECT * FROM dataset WHERE dataset_id = ?",
                [dataset_id]
            ).fetchone()
            
            if result:
                columns = [desc[0] for desc in con.description]
                metadata = dict(zip(columns, result))
                con.close()
                return metadata
            else:
                con.close()
                return {}
        except Exception:
            return {}
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get dataset information from Task 1 catalogue."""
        return {
            "dataset_id": self.dataset_id,
            "dataset_name": self.catalogue_metadata.get(
                "dataset_name",
                "World Database on Protected Areas (WDPA)"
            ),
            "provider": self.catalogue_metadata.get(
                "provider_name_raw",
                "UNEP-WCMC / IUCN"
            ),
            "primary_url": self.catalogue_metadata.get(
                "primary_url",
                self.portal_url
            ),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": "global",
            "temporal_coverage": "current (monthly updates)",
            "update_frequency": "monthly"
        }
    
    def list_protected_areas(
        self,
        bbox: Dict[str, float],
        category_filter: Optional[str] = None,
        marine: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        List protected areas within a bounding box.
        
        Args:
            bbox: Bounding box with keys: min_lon, min_lat, max_lon, max_lat
            category_filter: Optional IUCN category filter (Ia, Ib, II, III, IV, V, VI)
            marine: Optional filter for marine (True), terrestrial (False), or both (None)
            
        Returns:
            Dictionary with protected area search information
        """
        # Build API query
        api_query = {
            "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        }
        if category_filter:
            api_query["iucn_category"] = category_filter
        if marine is not None:
            api_query["marine"] = str(marine).lower()
        
        # Build API URL
        params_str = "&".join([f"{k}={v}" for k, v in api_query.items()])
        api_url = f"{self.api_endpoint}v3/protected_areas/search?{params_str}"
        
        # Build download URL for bbox
        download_params = f"?bbox={bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        download_url = f"{self.download_url}{download_params}"
        
        return {
            "search_params": {
                "bbox": bbox,
                "category_filter": category_filter,
                "marine": marine
            },
            "access_methods": {
                "api_search": {
                    "url": api_url,
                    "method": "GET",
                    "format": "JSON",
                    "description": "Search protected areas via API",
                    "requires_auth": "API key (free registration)",
                    "pagination": "Results may be paginated for large queries"
                },
                "portal_search": {
                    "url": f"{self.portal_url}search",
                    "description": "Interactive map-based search",
                    "requires_auth": False
                },
                "bulk_download": {
                    "url": download_url,
                    "description": "Download WDPA data for region",
                    "formats": ["Shapefile", "GeoPackage", "GeoJSON", "KML", "CSV"],
                    "requires_auth": False,
                    "note": "Monthly updates available"
                }
            },
            "iucn_categories": self.iucn_categories,
            "governance_types": self.governance_types,
            "catalogue_metadata": self.get_dataset_info(),
            "notes": (
                "API requires free registration at api.protectedplanet.net/documentation. "
                "Bulk downloads available without registration but require attribution. "
                "Data updated monthly with latest protected area designations."
            )
        }
    
    def get_protected_area_detail(
        self,
        wdpa_id: int
    ) -> Dict[str, Any]:
        """
        Get detailed information about a specific protected area.
        
        Args:
            wdpa_id: WDPA unique identifier
            
        Returns:
            Dictionary with protected area details and access information
        """
        # Build API URL
        api_url = f"{self.api_endpoint}v3/protected_areas/{wdpa_id}"
        
        # Build portal URL
        portal_url = f"{self.portal_url}en/{wdpa_id}"
        
        return {
            "wdpa_id": wdpa_id,
            "access_methods": {
                "api_detail": {
                    "url": api_url,
                    "method": "GET",
                    "format": "JSON",
                    "description": "Retrieve detailed metadata via API",
                    "requires_auth": "API key (free registration)",
                    "includes": [
                        "Name and designation",
                        "IUCN category and governance type",
                        "Designation date and legal status",
                        "Area (terrestrial and marine)",
                        "Boundaries (GeoJSON geometry)",
                        "Management authority",
                        "Related designations (UNESCO, Ramsar, etc.)"
                    ]
                },
                "portal_detail": {
                    "url": portal_url,
                    "description": "Interactive detail page with maps and reports",
                    "requires_auth": False,
                    "includes": [
                        "Interactive map",
                        "Downloadable fact sheet",
                        "Related protected areas",
                        "Connectivity analysis",
                        "Biodiversity data (if available)"
                    ]
                }
            },
            "data_fields": {
                "core": ["name", "original_name", "designation", "designation_eng", "designation_type"],
                "classification": ["iucn_cat", "gov_type", "own_type", "mang_auth", "mang_plan"],
                "spatial": ["gis_area", "gis_m_area", "rep_m_area", "rep_area", "geometry"],
                "temporal": ["status_yr", "verif"],
                "identifiers": ["wdpaid", "wdpa_pid", "parent_iso3", "iso3"]
            },
            "iucn_categories": self.iucn_categories,
            "governance_types": self.governance_types,
            "catalogue_metadata": self.get_dataset_info(),
            "attribution": "UNEP-WCMC and IUCN (year), Protected Planet: World Database on Protected Areas",
            "notes": (
                "WDPA data is compiled from official sources. Boundaries are indicative and "
                "may not reflect legal or actual boundaries. For authoritative boundaries, "
                "contact the management authority."
            )
        }


# Singleton instance for registry
def get_wdpa_server() -> WDPAServer:
    """Factory function for MCP server registry."""
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_WDPA_PROTECTED_AREAS.json"
    return WDPAServer(config_path=config_path)
