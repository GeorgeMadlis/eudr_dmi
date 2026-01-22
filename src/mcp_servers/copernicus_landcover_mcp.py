#!/usr/bin/env python
"""
copernicus_landcover_mcp.py

Task 2 MCP Server implementation for Copernicus Global Land Cover 100m.

Provides tools to discover and access Copernicus land cover datasets through
WMS, STAC API, and direct download.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class CopernicusLandcoverServer:
    """
    MCP Server implementation for Copernicus Global Land Cover.
    
    Provides tools to list available land cover layers and retrieve tiles
    for specific regions and years.
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "copernicus_landcover_100m"
    ):
        self.config = self._load_config(config_path) if config_path else {}
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # Copernicus Land Cover configuration
        self.base_url = self.config.get(
            "base_url",
            "https://s3-eu-west-1.amazonaws.com/vito.landcover.global"
        )
        self.wms_endpoint = self.config.get(
            "wms_endpoint",
            "https://services.terrascope.be/wms/v2"
        )
        self.stac_endpoint = self.config.get(
            "stac_endpoint",
            "https://stac.terrascope.be/collections/COPERNICUS_LANDCOVER"
        )
        
        # Available years and products
        self.available_years = list(range(2015, 2025))  # 2015-2024
        self.products = [
            {
                "id": "discrete",
                "name": "Discrete Classification",
                "description": "Land cover discrete classification (22 classes)",
                "resolution": "100m",
                "classes": 22,
                "format": "GeoTIFF"
            },
            {
                "id": "forest",
                "name": "Forest Type",
                "description": "Fractional cover for forest types",
                "resolution": "100m",
                "layers": ["evergreen", "deciduous"],
                "format": "GeoTIFF"
            },
            {
                "id": "crops",
                "name": "Crops Cover",
                "description": "Fractional cover for crops",
                "resolution": "100m",
                "format": "GeoTIFF"
            },
            {
                "id": "urban",
                "name": "Urban/Built-up",
                "description": "Fractional cover for urban areas",
                "resolution": "100m",
                "format": "GeoTIFF"
            },
            {
                "id": "water",
                "name": "Water Bodies",
                "description": "Fractional cover for water bodies (seasonal and permanent)",
                "resolution": "100m",
                "layers": ["seasonal", "permanent"],
                "format": "GeoTIFF"
            },
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
                "Copernicus Global Land Cover 100m"
            ),
            "provider": self.catalogue_metadata.get(
                "provider_name_raw",
                "Copernicus Global Land Service"
            ),
            "primary_url": self.catalogue_metadata.get(
                "primary_url",
                "https://land.copernicus.eu/en/products/global-dynamic-land-cover"
            ),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": "global",
            "temporal_coverage": "2015-present (annual)",
            "resolution": "100m",
        }
    
    def list_landcover_layers(self) -> Dict[str, Any]:
        """
        List all available Copernicus land cover products and years.
        
        Returns:
            Dictionary with layer information
        """
        return {
            "platform": "Copernicus Global Land Cover",
            "resolution": "100m",
            "temporal_coverage": {
                "start_year": min(self.available_years),
                "end_year": max(self.available_years),
                "years": self.available_years,
                "frequency": "annual"
            },
            "products": self.products,
            "total_products": len(self.products),
            "access_methods": ["WMS", "STAC", "Direct Download"],
            "endpoints": {
                "wms": self.wms_endpoint,
                "stac": self.stac_endpoint,
                "download": self.base_url
            },
            "catalogue_metadata": self.get_dataset_info(),
            "classification_system": "LCCS (Land Cover Classification System)",
            "classes": {
                "count": 22,
                "categories": [
                    "Water", "Trees", "Shrubland", "Grassland", "Cropland",
                    "Built-up", "Bare/sparse vegetation", "Snow and ice",
                    "Permanent water bodies", "Herbaceous wetland", "Moss and lichen"
                ]
            }
        }
    
    def get_landcover_tile(
        self,
        bbox: Dict[str, float],
        year: int,
        product_id: str = "discrete",
        format: str = "GeoTIFF"
    ) -> Dict[str, Any]:
        """
        Get land cover data for a specific bounding box and year.
        
        Args:
            bbox: Bounding box with keys: min_lon, min_lat, max_lon, max_lat
            year: Year (2015-2024)
            product_id: Product type (discrete, forest, crops, urban, water)
            format: Output format (default: GeoTIFF)
            
        Returns:
            Dictionary with download information and WMS parameters
        """
        if year not in self.available_years:
            return {
                "error": f"Year {year} not available. Available years: {self.available_years}"
            }
        
        # Find product
        product = next((p for p in self.products if p["id"] == product_id), None)
        if not product:
            return {
                "error": f"Product {product_id} not found. Available: {[p['id'] for p in self.products]}"
            }
        
        # Build WMS GetMap URL
        bbox_str = f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        wms_url = (
            f"{self.wms_endpoint}?"
            f"service=WMS&version=1.3.0&request=GetMap"
            f"&layers=COPERNICUS_LANDCOVER_{year}_{product_id}"
            f"&bbox={bbox_str}"
            f"&crs=EPSG:4326&width=1024&height=1024"
            f"&format=image/png"
        )
        
        # Build STAC query
        stac_query = {
            "bbox": [bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat']],
            "datetime": f"{year}-01-01/{year}-12-31",
            "collections": ["COPERNICUS_LANDCOVER"],
            "query": {
                "product": {"eq": product_id}
            }
        }
        
        # Build direct download URL pattern
        tile_pattern = f"{self.base_url}/v3.0/{year}/E*N*/{{product}}/*_{year}0101_{product}_100m_*.tif"
        
        return {
            "year": year,
            "product": product,
            "bbox": bbox,
            "access_methods": {
                "wms_preview": {
                    "url": wms_url,
                    "method": "GET",
                    "format": "image/png",
                    "description": "Quick preview via WMS"
                },
                "stac_api": {
                    "endpoint": f"{self.stac_endpoint}/items",
                    "query": stac_query,
                    "method": "POST",
                    "description": "Query STAC catalog for assets"
                },
                "direct_download": {
                    "pattern": tile_pattern,
                    "description": "Direct download from S3 (requires tile calculation)",
                    "base_url": self.base_url
                }
            },
            "catalogue_metadata": self.get_dataset_info(),
            "notes": "For large areas, consider using STAC API to discover and download tiles. WMS is best for visualization."
        }


# Singleton instance for registry
def get_copernicus_landcover_server() -> CopernicusLandcoverServer:
    """Factory function for MCP server registry."""
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_COPERNICUS_LANDCOVER.json"
    return CopernicusLandcoverServer(config_path=config_path)
