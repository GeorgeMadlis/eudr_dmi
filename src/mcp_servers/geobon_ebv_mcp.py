#!/usr/bin/env python
"""
geobon_ebv_mcp.py

Task 2 MCP Server implementation for GEOBON Essential Biodiversity Variables.

Provides tools to discover and access EBV data cubes covering genetic composition,
species populations, community composition, ecosystem functioning, and structure.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class GeobonEBVServer:
    """
    MCP Server implementation for GEOBON Essential Biodiversity Variables.
    
    Provides tools to list EBV layers and retrieve summary statistics
    for specific regions.
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "geobon_ebv_portal"
    ):
        self.config = self._load_config(config_path) if config_path else {}
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # GEOBON EBV configuration
        self.portal_url = "https://portal.geobon.org/"
        self.api_endpoint = self.config.get(
            "api_endpoint",
            "https://portal.geobon.org/api/v1"
        )
        self.wms_endpoint = self.config.get(
            "wms_endpoint",
            "https://portal.geobon.org/geoserver/wms"
        )
        self.wcs_endpoint = self.config.get(
            "wcs_endpoint",
            "https://portal.geobon.org/geoserver/wcs"
        )
        
        # EBV Classes
        self.ebv_classes = [
            {
                "id": "genetic_composition",
                "name": "Genetic Composition",
                "description": "Genetic diversity within and among populations",
                "examples": ["Genetic diversity", "Effective population size", "Inbreeding"]
            },
            {
                "id": "species_populations",
                "name": "Species Populations",
                "description": "Species distribution, abundance, and traits",
                "examples": ["Species distributions", "Population abundance", "Population structure by age/size"]
            },
            {
                "id": "species_traits",
                "name": "Species Traits",
                "description": "Phenotypic traits relevant to ecosystem functioning",
                "examples": ["Phenology", "Body mass", "Dispersal capacity"]
            },
            {
                "id": "community_composition",
                "name": "Community Composition",
                "description": "Diversity and composition of communities",
                "examples": ["Taxonomic/phylogenetic diversity", "Community abundance", "Trait diversity"]
            },
            {
                "id": "ecosystem_functioning",
                "name": "Ecosystem Functioning",
                "description": "Rates of ecosystem processes",
                "examples": ["Primary productivity", "Nutrient retention", "Disturbance regimes"]
            },
            {
                "id": "ecosystem_structure",
                "name": "Ecosystem Structure",
                "description": "Physical habitat structure",
                "examples": ["Habitat structure", "Ecosystem composition", "Ecosystem extent/fragmentation"]
            }
        ]
        
        # Example EBV datasets
        self.example_datasets = [
            {
                "id": "cSAR_lai",
                "name": "Leaf Area Index (LAI)",
                "ebv_class": "ecosystem_structure",
                "provider": "c-scale AR",
                "resolution": "500m",
                "temporal": "2001-2020 (monthly)",
                "description": "Global leaf area index from MODIS"
            },
            {
                "id": "geobon_tundra_greenness",
                "name": "Arctic Tundra Greenness",
                "ebv_class": "ecosystem_functioning",
                "provider": "GEO BON",
                "resolution": "1km",
                "temporal": "2000-2021 (annual max NDVI)",
                "description": "Vegetation greenness trends in Arctic tundra"
            },
            {
                "id": "globbiomass_agb",
                "name": "Above Ground Biomass",
                "ebv_class": "ecosystem_structure",
                "provider": "GlobBiomass",
                "resolution": "100m",
                "temporal": "2010, 2017, 2018",
                "description": "Forest above-ground biomass estimates"
            }
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
                "GEOBON Essential Biodiversity Variables"
            ),
            "provider": self.catalogue_metadata.get(
                "provider_name_raw",
                "Group on Earth Observations Biodiversity Observation Network (GEO BON)"
            ),
            "primary_url": self.catalogue_metadata.get(
                "primary_url",
                self.portal_url
            ),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": "global",
            "temporal_coverage": "varies by EBV (1980s-present for many)"
        }
    
    def list_ebv_layers(self) -> Dict[str, Any]:
        """
        List all available EBV classes and example datasets.
        
        Returns:
            Dictionary with EBV class and dataset information
        """
        return {
            "platform": "GEOBON EBV Portal",
            "ebv_classes": self.ebv_classes,
            "total_classes": len(self.ebv_classes),
            "example_datasets": self.example_datasets,
            "total_example_datasets": len(self.example_datasets),
            "access_methods": ["WMS", "WCS", "NetCDF Download", "API"],
            "endpoints": {
                "portal": self.portal_url,
                "api": self.api_endpoint,
                "wms": self.wms_endpoint,
                "wcs": self.wcs_endpoint
            },
            "catalogue_metadata": self.get_dataset_info(),
            "data_format": "NetCDF-CF with EBV-specific metadata",
            "standards": {
                "format": "NetCDF Climate and Forecast (CF) Conventions",
                "metadata": "EBV Data Cube standard",
                "dimensions": "typically [time, latitude, longitude] or [time, entity, metric]"
            },
            "notes": (
                "EBV data cubes follow standardized format for interoperability. "
                "Each cube contains multiple temporal snapshots of biodiversity metrics. "
                "Access via portal search, API queries, or OGC web services."
            )
        }
    
    def get_ebv_summary(
        self,
        bbox: Dict[str, float],
        ebv_id: str,
        time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get EBV data summary for a specific bounding box.
        
        Args:
            bbox: Bounding box with keys: min_lon, min_lat, max_lon, max_lat
            ebv_id: EBV dataset ID (e.g., "cSAR_lai", "geobon_tundra_greenness")
            time: Optional time parameter (ISO 8601 format)
            
        Returns:
            Dictionary with EBV access information and summary
        """
        # Find dataset
        dataset = next((d for d in self.example_datasets if d["id"] == ebv_id), None)
        if not dataset:
            return {
                "error": f"EBV dataset {ebv_id} not found. Available: {[d['id'] for d in self.example_datasets]}"
            }
        
        # Build WMS GetMap URL
        bbox_str = f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        time_param = f"&time={time}" if time else ""
        wms_url = (
            f"{self.wms_endpoint}?"
            f"service=WMS&version=1.3.0&request=GetMap"
            f"&layers={ebv_id}"
            f"&bbox={bbox_str}"
            f"&crs=EPSG:4326&width=1024&height=1024"
            f"&format=image/png{time_param}"
        )
        
        # Build WCS GetCoverage URL for data download
        wcs_url = (
            f"{self.wcs_endpoint}?"
            f"service=WCS&version=2.0.1&request=GetCoverage"
            f"&coverageId={ebv_id}"
            f"&subset=Lat({bbox['min_lat']},{bbox['max_lat']})"
            f"&subset=Long({bbox['min_lon']},{bbox['max_lon']})"
            f"{('&subset=time(' + time + ')') if time else ''}"
            f"&format=application/netcdf"
        )
        
        # Build API query
        api_query_url = (
            f"{self.api_endpoint}/ebv-cubes/{ebv_id}?"
            f"bbox={bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
            f"{'&time=' + time if time else ''}"
        )
        
        return {
            "ebv_id": ebv_id,
            "dataset": dataset,
            "bbox": bbox,
            "time": time,
            "access_methods": {
                "wms_preview": {
                    "url": wms_url,
                    "method": "GET",
                    "format": "image/png",
                    "description": "Quick visualization via WMS"
                },
                "wcs_download": {
                    "url": wcs_url,
                    "method": "GET",
                    "format": "NetCDF",
                    "description": "Download data subset via WCS"
                },
                "api_query": {
                    "url": api_query_url,
                    "method": "GET",
                    "format": "JSON",
                    "description": "Query EBV metadata and access links via API"
                },
                "portal_search": {
                    "url": f"{self.portal_url}search?q={ebv_id}",
                    "description": "Interactive search and download via web portal"
                }
            },
            "catalogue_metadata": self.get_dataset_info(),
            "notes": (
                "EBV data cubes may be large. For analysis, consider using WCS to subset "
                "spatially and temporally. Portal provides interactive visualization and download."
            )
        }


# Singleton instance for registry
def get_geobon_ebv_server() -> GeobonEBVServer:
    """Factory function for MCP server registry."""
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_GEOBON_EBV.json"
    return GeobonEBVServer(config_path=config_path)
