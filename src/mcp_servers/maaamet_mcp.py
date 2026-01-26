#!/usr/bin/env python
"""
maaamet_mcp.py

Task 2 MCP Server implementation for Maa-amet (Estonian Land Board) Geoportal.

Provides tools to discover and access Estonian national geospatial data through
OGC WMS/WFS/WCS services.

Note: This is a NATIONAL-scale dataset (Estonia only), unlike the global datasets
(Hansen GFC, ERA5, GBIF).
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import duckdb
import requests


class MaaametServer:
    """
    MCP Server implementation for Maa-amet Estonian Geoportal.
    
    Provides tools to discover available OGC services (WMS/WFS/WCS) and layers
    for Estonian national geospatial data.
    """
    
    def __init__(
        self, 
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "maaamet_geoportaal"
    ):
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        
        # Maa-amet Geoportal configuration
        self.base_url = self.config.get("base_url", "https://geoportaal.maaamet.ee")
        default_wms = self.config.get("wms_endpoint", f"{self.base_url}/geoserver/ows")
        self.wms_endpoint = default_wms
        # Maa-amet exposes public WFS services on the gsavalik domain; allow overrides via config.
        self.wfs_endpoint = self.config.get("wfs_endpoint", "https://gsavalik.envir.ee/geoserver/wfs")
        
        # Key Estonian layers/services (subset)
        self.services = [
            {
                "id": "ortofoto",
                "name": "Orthophotos",
                "type": "WMS",
                "description": "High-resolution aerial imagery of Estonia",
                "coverage": "Estonia",
                "resolution": "0.4m - 1m",
                "temporal": "Various years, updated regularly"
            },
            {
                "id": "aluskaart",
                "name": "Base Map",
                "type": "WMS",
                "description": "Estonian topographic base map",
                "coverage": "Estonia",
                "scale": "1:10,000 - 1:250,000"
            },
            {
                "id": "halduspiirid",
                "name": "Administrative Boundaries",
                "type": "WFS",
                "description": "Estonian administrative units (counties, municipalities)",
                "coverage": "Estonia",
                "features": "Counties, municipalities, settlements"
            },
            {
                "id": "katastrikaart",
                "name": "Cadastral Map",
                "type": "WMS/WFS",
                "description": "Land parcel cadastral data",
                "coverage": "Estonia",
                "features": "Land parcels, buildings, addresses"
            },
            {
                "id": "maaamet_pohivesi",
                "name": "Groundwater",
                "type": "WMS",
                "description": "Groundwater monitoring and hydrogeological data",
                "coverage": "Estonia"
            },
            {
                "id": "geoloogia",
                "name": "Geology",
                "type": "WMS",
                "description": "Geological maps and data",
                "coverage": "Estonia",
                "scale": "1:50,000 - 1:400,000"
            },
        ]
        
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load MCP configuration from JSON file."""
        if not config_path.exists():
            # Return minimal config if file doesn't exist
            return {
                "server_id": "maaamet_mcp",
                "family": "Maaamet_Estonia",
                "server_type": "ogc_services"
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
                [dataset_id, "Maaamet_Estonia"]
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
            "dataset_name": self.catalogue_metadata.get("dataset_name", "Maa-amet Geoportaal"),
            "provider": self.catalogue_metadata.get("provider_name_raw", "Maa-amet (Estonian Land Board)"),
            "primary_url": self.catalogue_metadata.get("primary_url", self.base_url),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": self.catalogue_metadata.get("spatial_scope", "national (Estonia)"),
        }
    
    def list_services(self) -> Dict[str, Any]:
        """
        List available OGC services and layers.
        
        Returns:
            Dictionary with service information
        """
        return {
            "platform": "Maa-amet Geoportaal",
            "country": "Estonia",
            "spatial_scope": "national",
            "total_services": len(self.services),
            "services": self.services,
            "endpoints": {
                "WMS": self.wms_endpoint,
                "WFS": self.wfs_endpoint,
            },
            "catalogue_metadata": self.get_catalogue_info(),
            "notes": (
                "Estonia-specific national geospatial data. "
                "OGC-compliant services (WMS/WFS/WCS). "
                "Open access with terms of use."
            ),
        }
    
    def get_service_capabilities(self, service_type: str = "WMS") -> Dict[str, Any]:
        """
        Build GetCapabilities request for OGC service.
        
        Args:
            service_type: Service type (WMS, WFS, WCS)
            
        Returns:
            Dictionary with capabilities request information
        """
        service_type = service_type.upper()
        
        if service_type == "WMS":
            endpoint = self.wms_endpoint
        elif service_type == "WFS":
            endpoint = self.wfs_endpoint
        else:
            return {"error": f"Unsupported service type: {service_type}. Use WMS or WFS."}
        
        capabilities_url = f"{endpoint}?service={service_type}&request=GetCapabilities"
        
        return {
            "service_type": service_type,
            "endpoint": endpoint,
            "capabilities_url": capabilities_url,
            "usage": (
                f"Use this URL to retrieve full {service_type} capabilities XML. "
                f"Parse to discover all available layers, CRS, formats, etc."
            ),
            "catalogue_metadata": self.get_catalogue_info(),
        }
    
    def build_wms_request(
        self,
        layer: str,
        bbox: Dict[str, float],
        width: int = 1024,
        height: int = 1024,
        crs: str = "EPSG:3301",
        format: str = "image/png"
    ) -> Dict[str, Any]:
        """
        Build WMS GetMap request.
        
        Args:
            layer: Layer name (e.g., "ortofoto", "aluskaart")
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            width: Image width in pixels
            height: Image height in pixels
            crs: Coordinate reference system (default: EPSG:3301 - Estonian national grid)
            format: Image format
            
        Returns:
            Dictionary with WMS request parameters and URL
        """
        bbox_str = f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']}"
        
        params = {
            "service": "WMS",
            "version": "1.3.0",
            "request": "GetMap",
            "layers": layer,
            "bbox": bbox_str,
            "width": str(width),
            "height": str(height),
            "crs": crs,
            "format": format,
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.wms_endpoint}?{query_string}"
        
        return {
            "service": "WMS",
            "endpoint": self.wms_endpoint,
            "layer": layer,
            "bbox": bbox,
            "dimensions": {"width": width, "height": height},
            "crs": crs,
            "format": format,
            "url": url,
            "notes": (
                f"Estonian national grid (EPSG:3301) recommended for Maa-amet data. "
                f"WGS84 (EPSG:4326) also supported but may require reprojection."
            ),
        }
    
    def get_coverage_info(self) -> Dict[str, Any]:
        """
        Get spatial coverage information.
        
        Returns:
            Dictionary with Estonia bbox and coverage details
        """
        return {
            "country": "Estonia",
            "spatial_scope": "national",
            "bbox_wgs84": {
                "min_lon": 21.5,
                "min_lat": 57.5,
                "max_lon": 28.5,
                "max_lat": 59.8,
            },
            "bbox_est_grid": {
                "description": "Estonian national coordinate system EPSG:3301 (Lambert Est)",
                "min_x": 370000,
                "min_y": 6370000,
                "max_x": 740000,
                "max_y": 6630000,
            },
            "recommended_crs": "EPSG:3301",
            "supported_crs": ["EPSG:3301", "EPSG:4326", "EPSG:3857"],
            "catalogue_metadata": self.get_catalogue_info(),
        }

    def fetch_wfs_features(
        self,
        layer: str,
        bbox: Dict[str, float],
        srs: str = "EPSG:4326",
        output_format: str = "application/json",
        max_features: int = 0,
    ) -> Dict[str, Any]:
        """Fetch features from the Maa-amet WFS endpoint for a bounding box.

        Args:
            layer: Qualified layer name (e.g., "kataster:ky_kehtiv").
            bbox: Dict with min_lon, min_lat, max_lon, max_lat coordinates.
            srs: Coordinate reference system for the WFS query (default EPSG:4326).
            output_format: Desired WFS output format (default GeoJSON).
            max_features: Optional limit on the number of features kept locally (0 = keep all).

        Returns:
            Parsed JSON response enriched with query metadata.
        """
        if not self.wfs_endpoint:
            raise ValueError("WFS endpoint is not configured for Maa-amet server")

        params = {
            "service": "WFS",
            "version": "2.0.0",
            "request": "GetFeature",
            "typenames": layer,
            "srsName": srs,
            "bbox": f"{bbox['min_lon']},{bbox['min_lat']},{bbox['max_lon']},{bbox['max_lat']},{srs}",
            "outputFormat": output_format,
        }

        response = requests.get(self.wfs_endpoint, params=params, timeout=120)
        response.raise_for_status()
        data = response.json()
        features = data.get("features", [])
        metadata: Dict[str, Any] = {
            "endpoint": self.wfs_endpoint,
            "params": params,
            "fetched_feature_count": len(features),
        }

        if max_features and len(features) > max_features:
            metadata["note"] = f"Truncated to first {max_features} features for reproducibility"
            data["features"] = features[:max_features]
            metadata["saved_feature_count"] = len(data["features"])

        data["_query_metadata"] = metadata
        return data


def main():
    """Example usage of Maa-amet MCP Server."""
    print("=" * 80)
    print("TASK 2 EXAMPLE: Maa-amet (Estonian Land Board) MCP Server")
    print("=" * 80)
    print()
    
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_Maaamet_Estonia.json"
    
    server = MaaametServer(config_path)
    
    # Example 1: List services
    print("Example 1: List available OGC services")
    print("-" * 80)
    services = server.list_services()
    print(f"Platform: {services['platform']}")
    print(f"Country: {services['country']}")
    print(f"Spatial Scope: {services['spatial_scope']}")
    print(f"Total services: {services['total_services']}")
    print("\nAvailable Services:")
    for svc in services["services"]:
        print(f"\n  {svc['name']} ({svc['type']})")
        print(f"    ID: {svc['id']}")
        print(f"    Description: {svc['description']}")
        print(f"    Coverage: {svc['coverage']}")
    
    # Example 2: Get WMS capabilities
    print("\n\nExample 2: Build WMS GetCapabilities request")
    print("-" * 80)
    caps = server.get_service_capabilities("WMS")
    print(f"Service: {caps['service_type']}")
    print(f"Endpoint: {caps['endpoint']}")
    print(f"Capabilities URL: {caps['capabilities_url']}")
    
    # Example 3: Build WMS request for Estonia test area
    print("\n\nExample 3: Build WMS GetMap request for orthophotos")
    print("-" * 80)
    
    # Estonia test area from geojson (converted to EPSG:3301 approximately)
    estonia_bbox = {
        "min_lon": 550000,
        "min_lat": 6510000,
        "max_lon": 570000,
        "max_lat": 6530000,
    }
    
    wms_req = server.build_wms_request(
        layer="ortofoto",
        bbox=estonia_bbox,
        width=1024,
        height=1024,
        crs="EPSG:3301"
    )
    
    print(f"Layer: {wms_req['layer']}")
    print(f"CRS: {wms_req['crs']}")
    print(f"Format: {wms_req['format']}")
    print(f"URL: {wms_req['url'][:100]}...")
    
    # Example 4: Coverage info
    print("\n\nExample 4: Get coverage information")
    print("-" * 80)
    coverage = server.get_coverage_info()
    print(f"Country: {coverage['country']}")
    print(f"Recommended CRS: {coverage['recommended_crs']}")
    print(f"Bbox (WGS84): {coverage['bbox_wgs84']}")
    print(f"Bbox (Estonian Grid): {coverage['bbox_est_grid']}")
    
    print("\n" + "=" * 80)
    print("Task 2 Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
