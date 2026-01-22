#!/usr/bin/env python
"""
era5_cds_mcp.py

Task 2 MCP Server implementation for ERA5 Climate Data Store (CDS).

Provides tools to query ERA5 reanalysis data through the CDS API.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class ERA5CDSServer:
    """
    MCP Server implementation for ERA5 Climate Data Store.
    
    Provides tools to discover available variables and request ERA5 data
    through the Copernicus Climate Data Store API.
    """
    
    def __init__(
        self, 
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "ecmwf_era5"
    ):
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # ERA5 configuration
        self.base_url = "https://cds.climate.copernicus.eu/api/v2"
        self.dataset_name = "reanalysis-era5-single-levels"
        
        # Common ERA5 variables (subset)
        self.variables = [
            {"id": "2m_temperature", "name": "2m Temperature", "units": "K"},
            {"id": "total_precipitation", "name": "Total Precipitation", "units": "m"},
            {"id": "surface_pressure", "name": "Surface Pressure", "units": "Pa"},
            {"id": "10m_u_component_of_wind", "name": "10m U Wind Component", "units": "m/s"},
            {"id": "10m_v_component_of_wind", "name": "10m V Wind Component", "units": "m/s"},
            {"id": "mean_sea_level_pressure", "name": "Mean Sea Level Pressure", "units": "Pa"},
            {"id": "soil_temperature_level_1", "name": "Soil Temperature Level 1", "units": "K"},
            {"id": "snow_depth", "name": "Snow Depth", "units": "m"},
        ]
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load MCP configuration from JSON file."""
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    
    def _load_catalogue_metadata(
        self, 
        duckdb_path: Optional[Path],
        dataset_id: str
    ) -> Dict[str, Any]:
        """Load dataset metadata from Task 1 catalogue database."""
        # If explicitly False, skip loading
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
        except Exception as e:
            print(f"Warning: Could not load catalogue metadata: {e}")
            return {}
    
    def get_catalogue_info(self) -> Dict[str, Any]:
        """Get dataset information from Task 1 catalogue."""
        return {
            "dataset_id": self.catalogue_metadata.get("dataset_id"),
            "dataset_name": self.catalogue_metadata.get("dataset_name"),
            "provider": self.catalogue_metadata.get("provider_name_raw"),
            "primary_url": self.catalogue_metadata.get("primary_url"),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": self.catalogue_metadata.get("spatial_scope"),
            "temporal_coverage_start": self.catalogue_metadata.get("temporal_coverage_start"),
            "temporal_coverage_end": self.catalogue_metadata.get("temporal_coverage_end"),
            "update_frequency": self.catalogue_metadata.get("update_frequency"),
        }
    
    def list_variables(self) -> Dict[str, Any]:
        """
        List available ERA5 variables.
        
        Returns:
            Dictionary with variable information
        """
        return {
            "dataset": "ERA5 Reanalysis",
            "dataset_id": self.dataset_id,
            "cds_dataset_name": self.dataset_name,
            "total_variables": len(self.variables),
            "variables": self.variables,
            "catalogue_metadata": self.get_catalogue_info(),
            "notes": "This is a subset of available ERA5 variables. Full list at https://cds.climate.copernicus.eu/",
        }
    
    def build_cds_request(
        self,
        variable: str,
        year: int,
        month: int,
        bbox: Optional[Dict[str, float]] = None,
        time_steps: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Build a CDS API request for ERA5 data.
        
        Args:
            variable: Variable ID (e.g., "2m_temperature")
            year: Year (e.g., 2020)
            month: Month (1-12)
            bbox: Optional bounding box {"north": 60, "south": 50, "east": 30, "west": 20}
            time_steps: Optional list of hours (e.g., ["00:00", "12:00"])
            
        Returns:
            Dictionary with CDS API request parameters
        """
        # Validate variable
        valid_vars = [v["id"] for v in self.variables]
        if variable not in valid_vars:
            return {
                "error": f"Invalid variable '{variable}'",
                "available_variables": valid_vars,
            }
        
        # Build request
        request = {
            "product_type": "reanalysis",
            "format": "netcdf",
            "variable": [variable],
            "year": [str(year)],
            "month": [f"{month:02d}"],
            "day": [f"{d:02d}" for d in range(1, 32)],  # All days in month
            "time": time_steps or ["00:00", "06:00", "12:00", "18:00"],
        }
        
        # Add spatial subset if provided
        if bbox:
            request["area"] = [
                bbox.get("north", 90),
                bbox.get("west", -180),
                bbox.get("south", -90),
                bbox.get("east", 180),
            ]
        
        return {
            "dataset_name": self.dataset_name,
            "request": request,
            "api_endpoint": f"{self.base_url}/resources/{self.dataset_name}",
            "notes": "Use this request with cdsapi Python client: c.retrieve(dataset_name, request, output_file)",
        }


def main():
    """Example usage of ERA5 CDS MCP Server."""
    print("=" * 80)
    print("TASK 2 EXAMPLE: ERA5 CDS MCP Server")
    print("=" * 80)
    print()
    
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_ERA5.json"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return
    
    server = ERA5CDSServer(config_path)
    
    # Example 1: List variables
    print("Example 1: List available ERA5 variables")
    print("-" * 80)
    vars_info = server.list_variables()
    print(f"Dataset: {vars_info['dataset']}")
    print(f"Total variables: {vars_info['total_variables']}")
    print("\nAvailable Variables:")
    for var in vars_info["variables"][:5]:
        print(f"  • {var['name']} ({var['id']}) - {var['units']}")
    print(f"  ... and {vars_info['total_variables'] - 5} more variables")
    print()
    
    # Example 2: Build CDS request
    print("\nExample 2: Build CDS API request for temperature data over Estonia")
    print("-" * 80)
    request = server.build_cds_request(
        variable="2m_temperature",
        year=2023,
        month=7,
        bbox={"north": 59.8, "south": 57.5, "east": 28.5, "west": 21.5},
        time_steps=["00:00", "12:00"]
    )
    print(json.dumps(request, indent=2))
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
