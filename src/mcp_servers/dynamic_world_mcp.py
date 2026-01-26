#!/usr/bin/env python
"""
dynamic_world_mcp.py

Task 2 MCP Server implementation for Google Dynamic World V1.

Provides tools to discover and access near real-time land cover data
from Sentinel-2 imagery via Google Earth Engine and COG downloads.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb
from datetime import datetime, timedelta


class DynamicWorldServer:
    """
    MCP Server implementation for Google Dynamic World.
    
    Provides tools to list versions and retrieve time series land cover data
    for specific regions.
    """
    
    def __init__(
        self, 
        config_path: Optional[Path] = None,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "google_dynamic_world"
    ):
        self.config = self._load_config(config_path) if config_path else {}
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # Dynamic World configuration
        self.gee_asset = "GOOGLE/DYNAMICWORLD/V1"
        self.cog_base_url = self.config.get(
            "cog_base_url",
            "https://storage.googleapis.com/earthengine-highvolume/projects/sat-io/open-datasets/GOOGLE_DYNAMIC_WORLD"
        )
        self.api_endpoint = self.config.get(
            "api_endpoint",
            "https://www.dynamicworld.app/"
        )
        
        # Land cover classes
        self.classes = [
            {"id": 0, "name": "water", "color": "#419BDF"},
            {"id": 1, "name": "trees", "color": "#397D49"},
            {"id": 2, "name": "grass", "color": "#88B053"},
            {"id": 3, "name": "flooded_vegetation", "color": "#7A87C6"},
            {"id": 4, "name": "crops", "color": "#E49635"},
            {"id": 5, "name": "shrub_and_scrub", "color": "#DFC35A"},
            {"id": 6, "name": "built", "color": "#C4281B"},
            {"id": 7, "name": "bare", "color": "#A59B8F"},
            {"id": 8, "name": "snow_and_ice", "color": "#B39FE1"}
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
                "Google Dynamic World V1"
            ),
            "provider": self.catalogue_metadata.get(
                "provider_name_raw",
                "Google / World Resources Institute"
            ),
            "primary_url": self.catalogue_metadata.get(
                "primary_url",
                "https://dynamicworld.app/"
            ),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": "global",
            "temporal_coverage": "2015-present (near real-time)",
            "resolution": "10m",
            "update_frequency": "2-5 day latency"
        }
    
    def list_dynamic_world_versions(self) -> Dict[str, Any]:
        """
        List available Dynamic World versions and products.
        
        Returns:
            Dictionary with version and product information
        """
        current_date = datetime.now().strftime("%Y-%m-%d")
        latest_available = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        
        return {
            "platform": "Google Dynamic World",
            "version": "V1",
            "resolution": "10m",
            "temporal_coverage": {
                "start_date": "2015-06-23",
                "latest_available": latest_available,
                "current_date": current_date,
                "update_frequency": "near real-time (2-5 day latency)"
            },
            "products": [
                {
                    "id": "label",
                    "name": "Discrete Classification",
                    "description": "Most likely class per pixel",
                    "bands": 1,
                    "values": "0-8 (9 classes)"
                },
                {
                    "id": "probability",
                    "name": "Class Probabilities",
                    "description": "Probability for each of 9 classes",
                    "bands": 9,
                    "values": "0-100 (%)"
                }
            ],
            "classes": self.classes,
            "access_methods": ["Google Earth Engine", "Cloud Optimized GeoTIFF"],
            "gee_asset": self.gee_asset,
            "cog_base_url": self.cog_base_url,
            "catalogue_metadata": self.get_dataset_info(),
            "license": "CC-BY-4.0",
            "citation": "Brown, C.F., et al. (2022). Dynamic World, Near real-time global 10m land use land cover mapping. Scientific Data 9, 251"
        }
    
    def get_dynamic_world_timeseries(
        self,
        bbox: Dict[str, float],
        start_date: str,
        end_date: str,
        product: str = "label"
    ) -> Dict[str, Any]:
        """
        Get Dynamic World time series for a specific bounding box and date range.
        
        Args:
            bbox: Bounding box with keys: min_lon, min_lat, max_lon, max_lat
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            product: Product type ("label" or "probability")
            
        Returns:
            Dictionary with access information for time series data
        """
        if product not in ["label", "probability"]:
            return {
                "error": f"Invalid product: {product}. Use 'label' or 'probability'"
            }
        
        # Calculate expected number of images (roughly every 2-5 days)
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        days = (end - start).days
        expected_images = days // 3  # Approximate
        
        # GEE Code snippet
        gee_code = f"""
// Load Dynamic World collection
var dw = ee.ImageCollection('{self.gee_asset}')
  .filterBounds(ee.Geometry.Rectangle([
    {bbox['min_lon']}, {bbox['min_lat']},
    {bbox['max_lon']}, {bbox['max_lat']}
  ]))
  .filterDate('{start_date}', '{end_date}');

// Get {'label' if product == 'label' else 'probability bands'}
var {product} = dw.select('{product if product == 'label' else 'water'}*');

print('Total images:', {product}.size());
Map.addLayer({product}.first(), {{}}, 'First Image');
"""
        
        return {
            "bbox": bbox,
            "start_date": start_date,
            "end_date": end_date,
            "product": product,
            "estimated_images": expected_images,
            "resolution": "10m",
            "access_methods": {
                "google_earth_engine": {
                    "asset": self.gee_asset,
                    "code_snippet": gee_code,
                    "description": "Use Google Earth Engine Code Editor or Python API",
                    "requires": "GEE account (free registration)"
                },
                "cog_download": {
                    "base_url": self.cog_base_url,
                    "pattern": f"{{tile}}/{{year}}/{{month}}/{{day}}/dw_{{product}}_{{tile}}_{{date}}.tif",
                    "description": "Cloud Optimized GeoTIFFs organized by Sentinel-2 tiles",
                    "note": "Requires determining Sentinel-2 tile IDs covering the bbox"
                }
            },
            "classes": self.classes if product == "label" else None,
            "catalogue_metadata": self.get_dataset_info(),
            "visualization": {
                "label": {
                    "min": 0,
                    "max": 8,
                    "palette": [c["color"] for c in self.classes]
                },
                "probability": {
                    "min": 0,
                    "max": 100,
                    "palette": ["white", "blue"]
                }
            }
        }


# Singleton instance for registry
def get_dynamic_world_server() -> DynamicWorldServer:
    """Factory function for MCP server registry."""
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_Dynamic_World.json"
    return DynamicWorldServer(config_path=config_path)
