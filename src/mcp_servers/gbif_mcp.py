#!/usr/bin/env python
"""
gbif_mcp.py

Task 2 MCP Server implementation for GBIF (Global Biodiversity Information Facility).

Provides tools to search species occurrence data through the GBIF API.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class GBIFServer:
    """
    MCP Server implementation for GBIF species occurrence data.
    
    Provides tools to search species observations, discover datasets,
    and access biodiversity information.
    """
    
    def __init__(
        self, 
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "gbif_gbif"
    ):
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # GBIF API configuration
        self.base_url = self.config.get("gbif", {}).get("base_url", "https://api.gbif.org/v1")
        
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
        }
    
    def build_occurrence_search(
        self,
        scientific_name: Optional[str] = None,
        country: Optional[str] = None,
        bbox: Optional[Dict[str, float]] = None,
        year: Optional[int] = None,
        limit: int = 300
    ) -> Dict[str, Any]:
        """
        Build a GBIF occurrence search query.
        
        Args:
            scientific_name: Species scientific name (e.g., "Lynx lynx")
            country: ISO 2-letter country code (e.g., "EE" for Estonia)
            bbox: Bounding box {"min_lon": ..., "min_lat": ..., "max_lon": ..., "max_lat": ...}
            year: Year of observation
            limit: Maximum number of results (default 300)
            
        Returns:
            Dictionary with API query parameters and URL
        """
        params = {
            "limit": min(limit, 300),  # GBIF max is 300 per request
        }
        
        if scientific_name:
            params["scientificName"] = scientific_name
        
        if country:
            params["country"] = country.upper()
        
        if bbox:
            # GBIF uses decimalLatitude/decimalLongitude range queries
            params["decimalLatitude"] = f"{bbox['min_lat']},{bbox['max_lat']}"
            params["decimalLongitude"] = f"{bbox['min_lon']},{bbox['max_lon']}"
        
        if year:
            params["year"] = year
        
        # Build URL
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.base_url}/occurrence/search?{query_string}"
        
        return {
            "endpoint": "occurrence/search",
            "parameters": params,
            "url": url,
            "catalogue_metadata": self.get_catalogue_info(),
            "notes": "Use requests.get(url).json() to retrieve occurrence data. Results include coordinates, date, species info.",
        }
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """
        Get information about the GBIF platform.
        
        Returns:
            Dictionary with GBIF platform information
        """
        return {
            "platform": "GBIF - Global Biodiversity Information Facility",
            "dataset_id": self.dataset_id,
            "api_base_url": self.base_url,
            "api_documentation": "https://www.gbif.org/developer/summary",
            "catalogue_metadata": self.get_catalogue_info(),
            "capabilities": [
                "Search species occurrence records",
                "Filter by taxon, location, time",
                "Access to >2 billion occurrence records",
                "Download occurrence datasets",
                "Access species checklists and datasets",
            ],
            "common_queries": {
                "species_in_country": "occurrence/search?scientificName={species}&country={ISO_code}",
                "species_in_bbox": "occurrence/search?scientificName={species}&decimalLatitude={min},{max}&decimalLongitude={min},{max}",
                "all_in_area": "occurrence/search?decimalLatitude={min},{max}&decimalLongitude={min},{max}",
            },
        }
    
    def list_kingdoms(self) -> Dict[str, Any]:
        """
        List taxonomic kingdoms available in GBIF.
        
        Returns:
            Dictionary with kingdom information
        """
        kingdoms = [
            {"name": "Animalia", "description": "Animals"},
            {"name": "Plantae", "description": "Plants"},
            {"name": "Fungi", "description": "Fungi"},
            {"name": "Chromista", "description": "Chromists"},
            {"name": "Bacteria", "description": "Bacteria"},
            {"name": "Archaea", "description": "Archaea"},
            {"name": "Protozoa", "description": "Protozoa"},
            {"name": "Viruses", "description": "Viruses"},
        ]
        
        return {
            "total_kingdoms": len(kingdoms),
            "kingdoms": kingdoms,
            "notes": "Use kingdom filter in searches: occurrence/search?kingdom={kingdom_name}",
        }


def main():
    """Example usage of GBIF MCP Server."""
    print("=" * 80)
    print("TASK 2 EXAMPLE: GBIF MCP Server")
    print("=" * 80)
    print()
    
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_GBIF.json"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return
    
    server = GBIFServer(config_path)
    
    # Example 1: Get dataset info
    print("Example 1: GBIF Platform Information")
    print("-" * 80)
    info = server.get_dataset_info()
    print(f"Platform: {info['platform']}")
    print(f"API Base URL: {info['api_base_url']}")
    print("\nCapabilities:")
    for cap in info["capabilities"]:
        print(f"  • {cap}")
    print()
    
    # Example 2: Build query for European lynx in Estonia
    print("\nExample 2: Search for European Lynx (Lynx lynx) in Estonia")
    print("-" * 80)
    query = server.build_occurrence_search(
        scientific_name="Lynx lynx",
        country="EE",
        year=2023,
        limit=100
    )
    print(f"API URL: {query['url']}")
    print(f"\nParameters:")
    for k, v in query["parameters"].items():
        print(f"  {k}: {v}")
    print()
    
    # Example 3: Build query with bounding box
    print("\nExample 3: Search for all species in Estonia bbox")
    print("-" * 80)
    estonia_bbox = {
        "min_lon": 21.5,
        "min_lat": 57.5,
        "max_lon": 28.5,
        "max_lat": 59.8,
    }
    query = server.build_occurrence_search(
        bbox=estonia_bbox,
        year=2024,
        limit=300
    )
    print(f"API URL: {query['url']}")
    
    # Example 4: List kingdoms
    print("\n\nExample 4: List taxonomic kingdoms")
    print("-" * 80)
    kingdoms = server.list_kingdoms()
    print(f"Total kingdoms: {kingdoms['total_kingdoms']}")
    for kingdom in kingdoms["kingdoms"]:
        print(f"  • {kingdom['name']}: {kingdom['description']}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
