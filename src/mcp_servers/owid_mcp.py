#!/usr/bin/env python
"""
owid_mcp.py

Task 2 MCP Server implementation for Our World in Data (OWID).

Provides tools to discover and access global socio-economic and environmental
indicators through the OWID Grapher API.

Note: OWID is a GLOBAL-scale dataset providing country-level time-series data
across hundreds of indicators (health, environment, economy, demographics, etc.).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb


class OWIDServer:
    """
    MCP Server implementation for Our World in Data.
    
    Provides tools to discover available indicators and charts, search topics,
    and build download URLs for CSV data and JSON metadata.
    """
    
    def __init__(
        self, 
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "ourworldindata_our_world_in_data"
    ):
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # OWID configuration
        self.base_url = "https://ourworldindata.org"
        self.api_base_url = "https://api.ourworldindata.org/v1/indicators"
        self.grapher_base = f"{self.base_url}/grapher"
        
        # Sample indicators (subset of popular ones)
        self.sample_indicators = [
            {
                "id": "co2-emissions",
                "slug": "co2-emissions",
                "name": "CO₂ emissions",
                "category": "Environment",
                "description": "Annual CO₂ emissions from fossil fuels and land use change",
                "grapher_url": f"{self.grapher_base}/co2-emissions",
            },
            {
                "id": "life-expectancy",
                "slug": "life-expectancy",
                "name": "Life expectancy",
                "category": "Health",
                "description": "Period life expectancy at birth",
                "grapher_url": f"{self.grapher_base}/life-expectancy",
            },
            {
                "id": "gdp-per-capita-maddison",
                "slug": "gdp-per-capita-maddison",
                "name": "GDP per capita",
                "category": "Economy",
                "description": "Gross domestic product per capita (Maddison Project)",
                "grapher_url": f"{self.grapher_base}/gdp-per-capita-maddison",
            },
            {
                "id": "child-mortality",
                "slug": "child-mortality",
                "name": "Child mortality",
                "category": "Health",
                "description": "Share of children who die before their fifth birthday",
                "grapher_url": f"{self.grapher_base}/child-mortality",
            },
            {
                "id": "forest-area",
                "slug": "forest-area",
                "name": "Forest area",
                "category": "Environment",
                "description": "Forest area as a share of total land area",
                "grapher_url": f"{self.grapher_base}/forest-area",
            },
            {
                "id": "population",
                "slug": "population",
                "name": "Population",
                "category": "Demographics",
                "description": "Total population by country",
                "grapher_url": f"{self.grapher_base}/population",
            },
            {
                "id": "renewable-energy-consumption",
                "slug": "renewable-energy-consumption",
                "name": "Renewable energy consumption",
                "category": "Energy",
                "description": "Renewable energy consumption as share of total energy",
                "grapher_url": f"{self.grapher_base}/renewable-energy-consumption",
            },
            {
                "id": "literacy-rate-adults",
                "slug": "literacy-rate-adults",
                "name": "Literacy rate",
                "category": "Education",
                "description": "Literacy rate among adults (15+)",
                "grapher_url": f"{self.grapher_base}/literacy-rate-adults",
            },
        ]
        
        self.categories = [
            "Health",
            "Environment",
            "Economy",
            "Demographics",
            "Energy",
            "Education",
            "Poverty",
            "Agriculture",
            "Technology",
        ]
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load MCP configuration from JSON file."""
        if not config_path.exists():
            # Return minimal config if file doesn't exist
            return {
                "server_id": "owid_mcp",
                "family": "OurWorldInData",
                "server_type": "api"
            }
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
            
            # Try to find by dataset_id, fallback to family search
            result = con.execute(
                "SELECT * FROM dataset WHERE dataset_id = ? OR dataset_family_name = ?",
                [dataset_id, "OurWorldInData"]
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
            "dataset_name": self.catalogue_metadata.get("dataset_name", "Our World in Data"),
            "provider": self.catalogue_metadata.get("provider_name_raw", "Our World in Data"),
            "primary_url": self.catalogue_metadata.get("primary_url", self.base_url),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": self.catalogue_metadata.get("spatial_scope", "global (country-level)"),
        }
    
    def list_sample_indicators(self) -> Dict[str, Any]:
        """
        List sample indicators available in OWID.
        
        Returns:
            Dictionary with sample indicator information
        """
        return {
            "platform": "Our World in Data",
            "total_sample_indicators": len(self.sample_indicators),
            "categories": self.categories,
            "indicators": self.sample_indicators,
            "api_base_url": self.api_base_url,
            "grapher_base_url": self.grapher_base,
            "catalogue_metadata": self.get_catalogue_info(),
            "notes": (
                "OWID provides 13,794+ charts and datasets covering global socio-economic "
                "and environmental indicators. This sample shows popular indicators. "
                "Visit https://ourworldindata.org/search to explore all data."
            ),
        }
    
    def search_indicators_by_category(self, category: str) -> Dict[str, Any]:
        """
        Search indicators by category.
        
        Args:
            category: Category name (e.g., "Health", "Environment", "Economy")
            
        Returns:
            Dictionary with matching indicators
        """
        if category not in self.categories:
            return {
                "error": f"Category '{category}' not found",
                "available_categories": self.categories,
            }
        
        matching = [ind for ind in self.sample_indicators if ind["category"] == category]
        
        return {
            "category": category,
            "total_indicators": len(matching),
            "indicators": matching,
            "search_url": f"{self.base_url}/search?q={category}",
        }
    
    def build_indicator_download_url(
        self,
        indicator_slug: str,
        format: str = "csv",
        full_data: bool = True
    ) -> Dict[str, Any]:
        """
        Build download URL for an indicator.
        
        Args:
            indicator_slug: Indicator slug (e.g., "co2-emissions", "life-expectancy")
            format: Download format ("csv", "json", "zip")
            full_data: If True, download all data; if False, download only visible data
            
        Returns:
            Dictionary with download URL and metadata
        """
        grapher_url = f"{self.grapher_base}/{indicator_slug}"
        
        if format == "csv":
            csv_type = "full" if full_data else "filtered"
            download_url = f"{grapher_url}.{csv_type}.csv"
        elif format == "json":
            download_url = f"{grapher_url}.metadata.json"
        elif format == "zip":
            csv_type = "full" if full_data else "filtered"
            download_url = f"{grapher_url}.{csv_type}.zip"
        else:
            return {"error": f"Unsupported format: {format}. Use 'csv', 'json', or 'zip'."}
        
        return {
            "indicator_slug": indicator_slug,
            "format": format,
            "full_data": full_data,
            "download_url": download_url,
            "grapher_url": grapher_url,
            "notes": (
                "CSV format: country-year time series data. "
                "JSON format: metadata including sources, descriptions, units. "
                "ZIP format: includes both CSV and JSON."
            ),
        }
    
    def get_data_explorers(self) -> Dict[str, Any]:
        """
        Get list of OWID Data Explorers.
        
        Returns:
            Dictionary with explorer information
        """
        explorers = [
            {
                "name": "Poverty Data Explorer",
                "url": f"{self.base_url}/explorers/poverty-explorer",
                "description": "Explore poverty data across countries and time",
            },
            {
                "name": "Population & Demography Data Explorer",
                "url": f"{self.base_url}/explorers/population-and-demography",
                "description": "Explore population growth, age structure, fertility, mortality",
            },
            {
                "name": "Global Health Data Explorer",
                "url": f"{self.base_url}/explorers/global-health",
                "description": "Explore disease burden, mortality causes, health systems",
            },
            {
                "name": "Energy Data Explorer",
                "url": f"{self.base_url}/explorers/energy",
                "description": "Explore energy production, consumption, and sources",
            },
            {
                "name": "CO2 Data Explorer",
                "url": f"{self.base_url}/explorers/co2",
                "description": "Explore CO2 emissions by country, sector, and time",
            },
        ]
        
        return {
            "platform": "Our World in Data",
            "total_explorers": len(explorers),
            "explorers": explorers,
            "catalogue_metadata": self.get_catalogue_info(),
        }
    
    def get_coverage_info(self) -> Dict[str, Any]:
        """
        Get spatial and temporal coverage information.
        
        Returns:
            Dictionary with coverage details
        """
        return {
            "platform": "Our World in Data",
            "spatial_scope": "global",
            "spatial_resolution": "country-level",
            "entity_types": ["countries", "regions", "continents", "world"],
            "temporal_scope": "varies by indicator",
            "temporal_coverage_notes": (
                "Some indicators cover 1800s-present (e.g., GDP, population), "
                "others cover recent decades (e.g., CO2 emissions 1750+, child mortality 1800+)"
            ),
            "data_format": "CSV (time series), JSON (metadata)",
            "update_frequency": "varies by indicator (daily to annual updates)",
            "total_charts": "13,794+",
            "catalogue_metadata": self.get_catalogue_info(),
        }


def main():
    """Example usage of OWID MCP Server."""
    print("=" * 80)
    print("TASK 2 EXAMPLE: Our World in Data MCP Server")
    print("=" * 80)
    print()
    
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_Our_World_in_Data.json"
    
    server = OWIDServer(config_path)
    
    # Example 1: List sample indicators
    print("Example 1: List sample indicators")
    print("-" * 80)
    indicators = server.list_sample_indicators()
    print(f"Platform: {indicators['platform']}")
    print(f"Sample indicators: {indicators['total_sample_indicators']}")
    print(f"Categories: {', '.join(indicators['categories'])}")
    print("\nSample Indicators:")
    for ind in indicators["indicators"][:5]:
        print(f"\n  {ind['name']} ({ind['category']})")
        print(f"    Slug: {ind['slug']}")
        print(f"    Description: {ind['description']}")
        print(f"    URL: {ind['grapher_url']}")
    
    # Example 2: Search by category
    print("\n\nExample 2: Search indicators by category")
    print("-" * 80)
    health_indicators = server.search_indicators_by_category("Health")
    print(f"Category: {health_indicators['category']}")
    print(f"Indicators found: {health_indicators['total_indicators']}")
    for ind in health_indicators["indicators"]:
        print(f"  - {ind['name']}: {ind['description']}")
    
    # Example 3: Build download URL
    print("\n\nExample 3: Build download URL for CO2 emissions")
    print("-" * 80)
    download = server.build_indicator_download_url("co2-emissions", format="csv", full_data=True)
    print(f"Indicator: {download['indicator_slug']}")
    print(f"Format: {download['format']}")
    print(f"Full data: {download['full_data']}")
    print(f"Download URL: {download['download_url']}")
    print(f"Grapher URL: {download['grapher_url']}")
    
    # Example 4: Data explorers
    print("\n\nExample 4: List Data Explorers")
    print("-" * 80)
    explorers = server.get_data_explorers()
    print(f"Total explorers: {explorers['total_explorers']}")
    for exp in explorers["explorers"]:
        print(f"\n  {exp['name']}")
        print(f"    URL: {exp['url']}")
        print(f"    {exp['description']}")
    
    # Example 5: Coverage info
    print("\n\nExample 5: Get coverage information")
    print("-" * 80)
    coverage = server.get_coverage_info()
    print(f"Platform: {coverage['platform']}")
    print(f"Spatial scope: {coverage['spatial_scope']}")
    print(f"Spatial resolution: {coverage['spatial_resolution']}")
    print(f"Total charts: {coverage['total_charts']}")
    print(f"Temporal coverage: {coverage['temporal_coverage_notes']}")
    
    print("\n" + "=" * 80)
    print("Task 2 Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
