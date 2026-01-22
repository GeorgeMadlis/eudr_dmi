#!/usr/bin/env python
"""
hansen_gfc_example.py

Task 2 Example: Implementing MCP tools for Hansen Global Forest Change dataset.

This demonstrates how Task 2 (MCP servers) integrates with Task 1 (metadata catalogue):
1. Load dataset metadata from the Task 1 DuckDB database
2. Load the Hansen GFC MCP config
3. Implement the list_layers tool
4. Implement the list_tiles tool with actual tile calculation
5. Show metadata about available layers

This is a working implementation of Task 2 for one dataset family.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import duckdb


class HansenGFCServer:
    """
    MCP Server implementation for Hansen Global Forest Change dataset.
    
    Provides tools to discover available layers and tiles, following
    the Task 2 design for EO/climate MCP servers.
    
    Integrates with Task 1 metadata catalogue to retrieve dataset information.
    """
    
    def __init__(
        self, 
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "googleapis_global_forest_change"
    ):
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # Load from config
        self.layers = self.config.get("layers", [])
        self.base_url = self.config.get("storage", {}).get("base_url", "")
        self.tile_pattern = self.config.get("storage", {}).get("pattern", "")
        self.tile_size = self.config.get("tiling_scheme", {}).get("tile_size_degrees", 10)
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load MCP configuration from JSON file."""
        with config_path.open("r", encoding="utf-8") as f:
            config = json.load(f)
        # Fix NaN values that might have been written incorrectly
        if "source_catalogue_example" in config:
            for key, val in config["source_catalogue_example"].items():
                if val == "NaN" or (isinstance(val, float) and str(val) == "nan"):
                    config["source_catalogue_example"][key] = None
        return config
    
    def _load_catalogue_metadata(
        self, 
        duckdb_path: Optional[Path],
        dataset_id: str
    ) -> Dict[str, Any]:
        """
        Load dataset metadata from Task 1 catalogue database.
        
        Args:
            duckdb_path: Path to geodata_catalogue.duckdb, or False to skip loading
            dataset_id: Dataset ID to look up
            
        Returns:
            Dictionary with catalogue metadata or empty dict if not found
        """
        # If explicitly False, skip loading
        if duckdb_path is False:
            return {}
            
        if duckdb_path is None:
            # Default: geodata_catalogue.duckdb in data_db/ folder (project root)
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
                # Get column names
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
    
    # -------------------------------------------------------------------------
    # Tool 1: list_layers
    # -------------------------------------------------------------------------
    
    def get_catalogue_info(self) -> Dict[str, Any]:
        """
        Get dataset information from Task 1 catalogue.
        
        Returns:
            Dictionary with catalogue metadata
        """
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
            "access_type": self.catalogue_metadata.get("access_type"),
            "data_format": self.catalogue_metadata.get("data_format_primary"),
        }
    
    def list_layers(self) -> Dict[str, Any]:
        """
        List all available layers in the Hansen GFC dataset.
        
        Combines MCP config layers with Task 1 catalogue metadata.
        
        Returns:
            Dictionary with layer information including descriptions
        """
        layer_metadata = {
            "treecover2000": {
                "name": "Tree Cover 2000",
                "description": "Tree canopy cover for year 2000, defined as canopy closure for all vegetation taller than 5m in height",
                "unit": "percent",
                "data_type": "uint8",
                "range": [0, 100],
                "no_data": None,
                "temporal_coverage": "2000",
            },
            "loss": {
                "name": "Forest Loss",
                "description": "Forest loss during 2001-2024 period (binary mask: 1 = loss, 0 = no loss)",
                "unit": "binary",
                "data_type": "uint8",
                "range": [0, 1],
                "no_data": None,
                "temporal_coverage": "2001-2024",
            },
            "lossyear": {
                "name": "Year of Forest Loss",
                "description": "Year of forest loss (values 1-24 representing 2001-2024; 0 = no loss)",
                "unit": "year_index",
                "data_type": "uint8",
                "range": [0, 24],
                "no_data": 0,
                "temporal_coverage": "2001-2024",
                "notes": "Add 2000 to value to get actual year (e.g., 1 = 2001, 24 = 2024)",
            },
            "gain": {
                "name": "Forest Gain",
                "description": "Forest gain during 2000-2012 period (binary mask: 1 = gain, 0 = no gain)",
                "unit": "binary",
                "data_type": "uint8",
                "range": [0, 1],
                "no_data": None,
                "temporal_coverage": "2000-2012",
                "notes": "Gain is mapped only for 2000-2012 period",
            },
            "datamask": {
                "name": "Data Mask",
                "description": "Data mask indicating land/water/no-data (1 = mapped land, 2 = water, 0 = no data)",
                "unit": "categorical",
                "data_type": "uint8",
                "range": [0, 2],
                "no_data": 0,
                "temporal_coverage": "N/A",
            },
        }
        
        # Build response with available layers and catalogue metadata
        available_layers = []
        for layer in self.layers:
            if layer in layer_metadata:
                available_layers.append({
                    "layer_id": layer,
                    **layer_metadata[layer]
                })
        
        # Get dataset info from catalogue
        catalogue_info = self.get_catalogue_info()
        
        return {
            "dataset": catalogue_info.get("dataset_name") or "Hansen Global Forest Change 2000-2024 v1.12",
            "dataset_id": catalogue_info.get("dataset_id"),
            "provider": catalogue_info.get("provider"),
            "version": "v1.12",
            "total_layers": len(available_layers),
            "layers": available_layers,
            "tiling_scheme": {
                "crs": self.config.get("tiling_scheme", {}).get("crs"),
                "tile_size_degrees": self.tile_size,
                "tile_grid": self.config.get("tiling_scheme", {}).get("tile_grid"),
            },
            "base_url": self.base_url,
            "catalogue_metadata": {
                "description": catalogue_info.get("description"),
                "spatial_scope": catalogue_info.get("spatial_scope"),
                "temporal_coverage": f"{catalogue_info.get('temporal_coverage_start')}-{catalogue_info.get('temporal_coverage_end')}" if catalogue_info.get('temporal_coverage_start') else None,
                "update_frequency": catalogue_info.get("update_frequency"),
                "access_type": catalogue_info.get("access_type"),
            }
        }
    
    # -------------------------------------------------------------------------
    # Tool 2: list_tiles (with actual implementation)
    # -------------------------------------------------------------------------
    
    def _generate_tile_id(self, lon: int, lat: int) -> str:
        """
        Generate Hansen GFC tile ID from 10x10 degree tile coordinates.
        
        Format: {lat_band}{lon_band}
        - Latitude: 80N to 50S in 10° bands
        - Longitude: 180W to 170E in 10° bands
        
        Args:
            lon: Longitude of tile southwest corner (must be multiple of 10)
            lat: Latitude of tile southwest corner (must be multiple of 10)
            
        Returns:
            Tile ID string (e.g., "00N_000E", "10S_070W")
        """
        # Latitude band
        if lat >= 0:
            lat_str = f"{abs(lat):02d}N"
        else:
            lat_str = f"{abs(lat):02d}S"
        
        # Longitude band
        if lon >= 0:
            lon_str = f"{abs(lon):03d}E"
        else:
            lon_str = f"{abs(lon):03d}W"
        
        return f"{lat_str}_{lon_str}"
    
    def list_tiles(
        self,
        min_lon: float = -180,
        min_lat: float = -50,
        max_lon: float = 180,
        max_lat: float = 80,
        layer: str = "loss"
    ) -> Dict[str, Any]:
        """
        List available tiles for a given bounding box and layer.
        
        Args:
            min_lon: Minimum longitude (western edge)
            min_lat: Minimum latitude (southern edge)
            max_lon: Maximum longitude (eastern edge)
            max_lat: Maximum latitude (northern edge)
            layer: Layer name (must be one of the available layers)
            
        Returns:
            Dictionary with tile information and URLs
        """
        # Validate layer
        if layer not in self.layers:
            return {
                "error": f"Invalid layer '{layer}'. Must be one of: {', '.join(self.layers)}",
                "available_layers": self.layers,
            }
        
        # Validate bounds
        if not (-180 <= min_lon <= 180 and -180 <= max_lon <= 180):
            return {"error": "Longitude must be between -180 and 180"}
        if not (-90 <= min_lat <= 90 and -90 <= max_lat <= 90):
            return {"error": "Latitude must be between -90 and 90"}
        if min_lon >= max_lon or min_lat >= max_lat:
            return {"error": "Invalid bounding box: min must be < max"}
        
        # Hansen GFC coverage: 80N to 50S
        hansen_min_lat = -50
        hansen_max_lat = 80
        
        # Clip to Hansen coverage
        query_min_lat = max(min_lat, hansen_min_lat)
        query_max_lat = min(max_lat, hansen_max_lat)
        
        if query_min_lat >= query_max_lat:
            return {
                "warning": f"Query bbox outside Hansen coverage ({hansen_min_lat} to {hansen_max_lat})",
                "tiles": [],
                "tile_count": 0,
            }
        
        # Round to 10-degree tile boundaries
        # Floor for min, ceiling for max (to include partial tiles)
        tile_min_lon = (int(min_lon) // self.tile_size) * self.tile_size
        tile_max_lon = ((int(max_lon) + self.tile_size - 1) // self.tile_size) * self.tile_size
        tile_min_lat = (int(query_min_lat) // self.tile_size) * self.tile_size
        tile_max_lat = ((int(query_max_lat) + self.tile_size - 1) // self.tile_size) * self.tile_size
        
        # Generate tile list
        tiles = []
        for lat in range(tile_min_lat, tile_max_lat, self.tile_size):
            for lon in range(tile_min_lon, tile_max_lon, self.tile_size):
                # Skip if outside Hansen coverage
                if lat < hansen_min_lat or lat >= hansen_max_lat:
                    continue
                    
                tile_id = self._generate_tile_id(lon, lat)
                tile_url = self.base_url + self.tile_pattern.format(
                    layer=layer,
                    tile_id=tile_id
                )
                
                tiles.append({
                    "tile_id": tile_id,
                    "sw_lon": lon,
                    "sw_lat": lat,
                    "ne_lon": lon + self.tile_size,
                    "ne_lat": lat + self.tile_size,
                    "url": tile_url,
                })
        
        return {
            "layer": layer,
            "query_bbox": {
                "min_lon": min_lon,
                "min_lat": min_lat,
                "max_lon": max_lon,
                "max_lat": max_lat,
            },
            "hansen_coverage": {
                "min_lat": hansen_min_lat,
                "max_lat": hansen_max_lat,
            },
            "tile_count": len(tiles),
            "tiles": tiles,
        }
    
    # -------------------------------------------------------------------------
    # Tool 3: get_layer_metadata
    # -------------------------------------------------------------------------
    
    def get_layer_metadata(self, layer: str) -> Dict[str, Any]:
        """
        Get detailed metadata for a specific layer.
        
        Args:
            layer: Layer name
            
        Returns:
            Detailed layer metadata
        """
        layers_info = self.list_layers()
        
        for layer_info in layers_info.get("layers", []):
            if layer_info["layer_id"] == layer:
                return layer_info
        
        return {
            "error": f"Layer '{layer}' not found",
            "available_layers": [l["layer_id"] for l in layers_info.get("layers", [])],
        }
    
    # -------------------------------------------------------------------------
    # Tool 4: download_tile
    # -------------------------------------------------------------------------
    
    def download_tile(
        self,
        tile_id: str,
        layer: str,
        output_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Download a specific tile from Google Cloud Storage.
        
        Args:
            tile_id: Tile identifier (e.g., "40N_030E")
            layer: Layer name (e.g., "loss", "treecover2000")
            output_dir: Optional output directory (defaults to ./hansen_tiles/)
            
        Returns:
            Dictionary with download status and file path
        """
        import requests
        from pathlib import Path
        
        # Validate layer
        if layer not in self.layers:
            return {
                "error": f"Invalid layer '{layer}'. Must be one of: {', '.join(self.layers)}",
                "available_layers": self.layers,
            }
        
        # Set default output directory
        if output_dir is None:
            output_dir = Path("./hansen_tiles")
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Build URL
        tile_url = self.base_url + self.tile_pattern.format(
            layer=layer,
            tile_id=tile_id
        )
        
        # Output filename
        output_file = output_dir / f"{layer}_{tile_id}.tif"
        
        try:
            # Download the file
            response = requests.get(tile_url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Write to file
            with output_file.open("wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            file_size_mb = output_file.stat().st_size / (1024 * 1024)
            
            return {
                "status": "success",
                "tile_id": tile_id,
                "layer": layer,
                "url": tile_url,
                "file_path": str(output_file),
                "file_size_mb": round(file_size_mb, 2),
            }
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                return {
                    "status": "error",
                    "error": f"Tile not found: {tile_id}",
                    "message": "This tile may not exist in the Hansen GFC dataset (e.g., ocean areas)",
                    "url": tile_url,
                }
            else:
                return {
                    "status": "error",
                    "error": f"HTTP error {e.response.status_code}",
                    "url": tile_url,
                }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "url": tile_url,
            }


def main():
    """
    Example usage demonstrating Task 2 implementation.
    """
    print("=" * 80)
    print("TASK 2 EXAMPLE: Hansen GFC MCP Server")
    print("=" * 80)
    print()
    
    # Initialize server
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_Hansen_GFC.json"
    
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        print("Run regenerate_catalogue.py first to generate MCP configs.")
        return
    
    server = HansenGFCServer(config_path)
    
    # Example 1: List all available layers
    print("Example 1: List all available layers (with Task 1 catalogue integration)")
    print("-" * 80)
    layers = server.list_layers()
    print(f"Dataset: {layers['dataset']}")
    print(f"Dataset ID: {layers.get('dataset_id')}")
    print(f"Provider: {layers.get('provider')}")
    print(f"Version: {layers['version']}")
    print(f"Total layers: {layers['total_layers']}")
    print()
    
    # Show catalogue metadata
    if layers.get('catalogue_metadata'):
        print("Catalogue Metadata (from Task 1):")
        cat_meta = layers['catalogue_metadata']
        if cat_meta.get('description'):
            print(f"  Description: {cat_meta['description']}")
        if cat_meta.get('spatial_scope'):
            print(f"  Spatial Scope: {cat_meta['spatial_scope']}")
        if cat_meta.get('temporal_coverage'):
            print(f"  Temporal Coverage: {cat_meta['temporal_coverage']}")
        if cat_meta.get('update_frequency'):
            print(f"  Update Frequency: {cat_meta['update_frequency']}")
        if cat_meta.get('access_type'):
            print(f"  Access Type: {cat_meta['access_type']}")
        print()
    
    print("Available Layers:")
    for layer in layers["layers"]:
        print(f"  • {layer['name']} ({layer['layer_id']})")
        print(f"    Description: {layer['description']}")
        print(f"    Temporal Coverage: {layer['temporal_coverage']}")
        print(f"    Data Type: {layer['data_type']}, Range: {layer['range']}")
        if layer.get("notes"):
            print(f"    Notes: {layer['notes']}")
        print()
    
    # Example 2: Get metadata for a specific layer
    print("\nExample 2: Get metadata for 'lossyear' layer")
    print("-" * 80)
    lossyear_meta = server.get_layer_metadata("lossyear")
    print(json.dumps(lossyear_meta, indent=2))
    
    # Example 3: List tiles for Estonia region
    print("\n\nExample 3: List tiles for Estonia region (forest loss layer)")
    print("-" * 80)
    estonia_bbox = {
        "min_lon": 21.5,  # Estonia's western edge
        "min_lat": 57.5,  # Estonia's southern edge
        "max_lon": 28.5,  # Estonia's eastern edge
        "max_lat": 59.8,  # Estonia's northern edge
    }
    
    tiles = server.list_tiles(layer="loss", **estonia_bbox)
    print(f"Layer: {tiles['layer']}")
    print(f"Query bbox: {tiles['query_bbox']}")
    print(f"Tiles found: {tiles['tile_count']}")
    print()
    
    for tile in tiles["tiles"]:
        print(f"  Tile: {tile['tile_id']}")
        print(f"    Bounds: ({tile['sw_lon']}, {tile['sw_lat']}) to ({tile['ne_lon']}, {tile['ne_lat']})")
        print(f"    URL: {tile['url']}")
        print()
    
    # Example 4: List tiles for tropical region
    print("\nExample 4: List tiles for Amazon region (tree cover 2000)")
    print("-" * 80)
    amazon_bbox = {
        "min_lon": -75,
        "min_lat": -10,
        "max_lon": -45,
        "max_lat": 5,
    }
    
    tiles = server.list_tiles(layer="treecover2000", **amazon_bbox)
    print(f"Layer: {tiles['layer']}")
    print(f"Tiles found: {tiles['tile_count']}")
    print(f"First 5 tiles:")
    for tile in tiles["tiles"][:5]:
        print(f"  • {tile['tile_id']}: {tile['url']}")
    if tiles['tile_count'] > 5:
        print(f"  ... and {tiles['tile_count'] - 5} more tiles")
    print()
    
    print("=" * 80)
    print("Task 2 Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
