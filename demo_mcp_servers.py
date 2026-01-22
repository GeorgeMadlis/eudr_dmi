#!/usr/bin/env python
"""
Demo: List all features available from Hansen GFC, ERA5, GBIF, Maa-amet, and OWID
for the bounding box defined by estonia_testland1.geojson
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add mcp_servers to path
sys.path.insert(0, str(Path(__file__).parent / "mcp_servers"))

from hansen_gfc_example import HansenGFCServer
from era5_cds_mcp import ERA5CDSServer
from gbif_mcp import GBIFServer
from maaamet_mcp import MaaametServer
from owid_mcp import OWIDServer
from copernicus_landcover_mcp import CopernicusLandcoverServer
from dynamic_world_mcp import DynamicWorldServer
from geobon_ebv_mcp import GeobonEBVServer
from wdpa_mcp import WDPAServer


def load_geojson_bbox(geojson_path: Path) -> dict:
    """
    Extract bounding box from a GeoJSON file.
    
    Returns:
        dict with keys: min_lon, min_lat, max_lon, max_lat
    """
    with open(geojson_path) as f:
        data = json.load(f)
    
    # Extract coordinates from the polygon
    coords = data["features"][0]["geometry"]["coordinates"][0]
    
    lons = [pt[0] for pt in coords]
    lats = [pt[1] for pt in coords]
    
    return {
        "min_lon": min(lons),
        "min_lat": min(lats),
        "max_lon": max(lons),
        "max_lat": max(lats),
    }


def demo_hansen_gfc(bbox: dict) -> dict:
    """Query Hansen GFC server for available features in the bounding box."""
    print("\n" + "="*80)
    print("HANSEN GLOBAL FOREST CHANGE")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_Hansen_GFC.json"
    
    server = HansenGFCServer(config_path)
    
    # Get all layers
    layers_info = server.list_layers()
    print(f"\nDataset: {layers_info['dataset']}")
    print(f"Available layers: {layers_info['total_layers']}")
    
    results = {
        "dataset": layers_info["dataset"],
        "total_layers": layers_info["total_layers"],
        "layers": [],
        "tiles_per_layer": {}
    }
    
    for layer in layers_info["layers"]:
        print(f"\n  Layer: {layer['name']} ({layer['layer_id']})")
        print(f"    Description: {layer['description']}")
        print(f"    Temporal Coverage: {layer['temporal_coverage']}")
        
        results["layers"].append({
            "id": layer["layer_id"],
            "name": layer["name"],
            "description": layer["description"],
            "temporal_coverage": layer["temporal_coverage"],
        })
        
        # Get tiles for this layer in the bounding box
        tiles = server.list_tiles(layer=layer["layer_id"], **bbox)
        print(f"    Tiles covering bbox: {tiles['tile_count']}")
        
        results["tiles_per_layer"][layer["layer_id"]] = {
            "count": tiles["tile_count"],
            "tile_ids": [t["tile_id"] for t in tiles["tiles"]],
        }
        
        if tiles["tile_count"] > 0:
            print(f"    Tile IDs: {', '.join([t['tile_id'] for t in tiles['tiles']])}")
    
    return results


def demo_era5_cds(bbox: dict) -> dict:
    """Query ERA5 CDS server for available features."""
    print("\n" + "="*80)
    print("ERA5 CLIMATE DATA STORE")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_ERA5.json"
    
    server = ERA5CDSServer(config_path)
    
    # Get all variables
    vars_info = server.list_variables()
    print(f"\nDataset: {vars_info['dataset']}")
    print(f"Available variables: {vars_info['total_variables']}")
    
    results = {
        "dataset": vars_info["dataset"],
        "total_variables": vars_info["total_variables"],
        "variables": [],
    }
    
    for var in vars_info["variables"]:
        print(f"\n  Variable: {var['name']} ({var['id']})")
        print(f"    Units: {var['units']}")
        
        results["variables"].append({
            "id": var["id"],
            "name": var["name"],
            "units": var["units"],
        })
    
    # Show example request for the bounding box
    print("\nExample: Build CDS API request for 2m temperature (January 2024)")
    request = server.build_cds_request(
        variable="2m_temperature",
        year=2024,
        month=1,
        bbox={
            "north": bbox["max_lat"],
            "south": bbox["min_lat"],
            "east": bbox["max_lon"],
            "west": bbox["min_lon"],
        }
    )
    
    results["example_request"] = {
        "variable": "2m_temperature",
        "dataset_name": request["dataset_name"],
        "spatial_subset": request["request"]["area"],
    }
    
    print(f"  Dataset: {request['dataset_name']}")
    print(f"  Spatial subset: {request['request']['area']}")
    
    return results


def demo_gbif(bbox: dict) -> dict:
    """Query GBIF server for available features."""
    print("\n" + "="*80)
    print("GBIF - GLOBAL BIODIVERSITY INFORMATION FACILITY")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_GBIF.json"
    
    server = GBIFServer(config_path)
    
    # Get platform info
    info = server.get_dataset_info()
    print(f"\nPlatform: {info['platform']}")
    print(f"API Base URL: {info['api_base_url']}")
    print(f"\nCapabilities:")
    for cap in info["capabilities"]:
        print(f"  - {cap}")
    
    results = {
        "platform": info["platform"],
        "capabilities": info["capabilities"],
        "kingdoms": [],
        "example_search": None,
    }
    
    # List taxonomic kingdoms
    kingdoms = server.list_kingdoms()
    print(f"\nTaxonomic Kingdoms: {kingdoms['total_kingdoms']}")
    for kingdom in kingdoms["kingdoms"]:
        print(f"  - {kingdom['name']}: {kingdom['description']}")
        results["kingdoms"].append({
            "name": kingdom["name"],
            "description": kingdom["description"],
        })
    
    # Build example occurrence search for the bbox
    print("\nExample: Build occurrence search for the bounding box")
    search = server.build_occurrence_search(
        bbox=bbox,
        limit=100
    )
    
    results["example_search"] = {
        "endpoint": search["endpoint"],
        "parameters": search["parameters"],
        "url": search["url"][:100] + "..." if len(search["url"]) > 100 else search["url"],
    }
    
    print(f"  Endpoint: {search['endpoint']}")
    print(f"  Parameters: {search['parameters']}")
    print(f"  URL: {search['url'][:80]}...")
    
    return results


def demo_copernicus_landcover(bbox: dict) -> dict:
    """Query Copernicus Land Cover server for available layers."""
    print("\n" + "="*80)
    print("COPERNICUS GLOBAL LAND COVER")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_COPERNICUS_LANDCOVER.json"
    
    server = CopernicusLandcoverServer(config_path)
    
    # Get available layers
    layers = server.list_landcover_layers()
    print(f"\nPlatform: {layers['platform']}")
    print(f"Resolution: {layers['resolution']}")
    print(f"Temporal Coverage: {layers['temporal_coverage']['start_year']}-{layers['temporal_coverage']['end_year']}")
    print(f"Available Years: {len(layers['temporal_coverage']['years'])} ({min(layers['temporal_coverage']['years'])}-{max(layers['temporal_coverage']['years'])})")
    
    results = {
        "platform": layers["platform"],
        "resolution": layers["resolution"],
        "temporal_coverage": f"{layers['temporal_coverage']['start_year']}-{layers['temporal_coverage']['end_year']}",
        "available_years": layers["temporal_coverage"]["years"],
        "products": layers["products"],
    }
    
    print(f"\nProducts ({len(layers['products'])}):")
    for product in layers["products"][:3]:  # Show first 3
        print(f"  - {product['id']}: {product['name']}")
    
    # Get tile info for a sample year
    sample_year = 2020
    tile_info = server.get_landcover_tile(
        bbox=bbox,
        year=sample_year,
        product_id="discrete"
    )
    
    print(f"\nSample Tile Request (Year {sample_year}, Estonia bbox):")
    print(f"  Access Methods: {', '.join(tile_info['access_methods'].keys())}")
    results["sample_tile"] = {
        "year": sample_year,
        "bbox": bbox,
        "access_methods": list(tile_info["access_methods"].keys()),
    }
    
    return results


def demo_dynamic_world(bbox: dict) -> dict:
    """Query Dynamic World server for near real-time land cover."""
    print("\n" + "="*80)
    print("GOOGLE DYNAMIC WORLD")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_DYNAMIC_WORLD.json"
    
    server = DynamicWorldServer(config_path)
    
    # Get available versions
    versions = server.list_dynamic_world_versions()
    print(f"\nPlatform: {versions['platform']}")
    print(f"Resolution: {versions['resolution']}")
    print(f"Temporal Coverage: {versions['temporal_coverage']['start_date']} to {versions['temporal_coverage']['latest_available']}")
    print(f"Update Frequency: {versions['temporal_coverage']['update_frequency']}")
    
    results = {
        "platform": versions["platform"],
        "resolution": versions["resolution"],
        "temporal_coverage": f"{versions['temporal_coverage']['start_date']} to present",
        "update_frequency": versions["temporal_coverage"]["update_frequency"],
        "land_cover_classes": versions["classes"],
    }
    
    print(f"\nLand Cover Classes ({len(versions['classes'])}):")
    for lc_class in versions["classes"][:5]:  # Show first 5
        print(f"  - {lc_class['id']}: {lc_class['name']}")
    
    # Get timeseries info
    timeseries = server.get_dynamic_world_timeseries(
        bbox=bbox,
        start_date="2023-01-01",
        end_date="2023-12-31"
    )
    
    print(f"\nTimeseries Request (2023, Estonia bbox):")
    print(f"  Expected Images: {timeseries['estimated_images']}")
    print(f"  Access Methods: {', '.join(timeseries['access_methods'].keys())}")
    results["sample_timeseries"] = {
        "year": 2023,
        "bbox": bbox,
        "expected_images": timeseries["estimated_images"],
    }
    
    return results


def demo_geobon_ebv(bbox: dict) -> dict:
    """Query GEOBON EBV server for biodiversity variables."""
    print("\n" + "="*80)
    print("GEOBON ESSENTIAL BIODIVERSITY VARIABLES")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_GEOBON_EBV.json"
    
    server = GeobonEBVServer(config_path)
    
    # Get available EBV layers
    layers = server.list_ebv_layers()
    print(f"\nPlatform: {layers['platform']}")
    print(f"Spatial Coverage: Global")
    print(f"EBV Classes: {len(layers['ebv_classes'])}")
    
    results = {
        "platform": layers["platform"],
        "spatial_coverage": "global",
        "ebv_classes": [],
    }
    
    print(f"\nEBV Classes:")
    for ebv_class in layers["ebv_classes"]:
        print(f"  - {ebv_class['id']}: {ebv_class['name']}")
        results["ebv_classes"].append({
            "id": ebv_class["id"],
            "name": ebv_class["name"],
        })
    
    # Get summary for a sample EBV - use first example dataset
    first_example = layers["example_datasets"][0]
    summary = server.get_ebv_summary(
        bbox=bbox,
        ebv_id=first_example["id"],
        time="2015/2020"
    )
    
    print(f"\nSample EBV Summary ({first_example['name']}, 2015-2020, Estonia bbox):")
    print(f"  Access Methods: {', '.join(summary['access_methods'].keys())}")
    results["sample_summary"] = {
        "ebv_id": first_example["id"],
        "time_period": "2015-2020",
        "bbox": bbox,
    }
    
    return results


def demo_wdpa(bbox: dict) -> dict:
    """Query WDPA Protected Areas server."""
    print("\n" + "="*80)
    print("WORLD DATABASE ON PROTECTED AREAS (WDPA)")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_WDPA_PROTECTED_AREAS.json"
    
    server = WDPAServer(config_path)
    
    # Get protected areas in bbox (convert dict to separate params)
    bbox_dict = {
        "min_lon": bbox["min_lon"],
        "min_lat": bbox["min_lat"],
        "max_lon": bbox["max_lon"],
        "max_lat": bbox["max_lat"]
    }
    
    areas = server.list_protected_areas(
        bbox=bbox_dict,
        category_filter=None,
        marine=False
    )
    
    print(f"\nDataset: WDPA")
    print(f"Spatial Coverage: Global")
    print(f"Search Results for Estonia bbox:")
    
    results = {
        "dataset": "WDPA",
        "spatial_coverage": "global",
        "iucn_categories": areas["iucn_categories"],
        "access_methods": list(areas["access_methods"].keys()),
    }
    
    print(f"\nIUCN Categories:")
    for category in areas["iucn_categories"]:
        print(f"  - {category['code']}: {category['name']}")
    
    print(f"\nAccess Methods:")
    for method, details in areas["access_methods"].items():
        print(f"  - {method}: {details.get('description', 'N/A')}")
    
    # Get detail for a sample area (first IUCN category)
    sample_wdpa_id = "12345"  # Placeholder
    detail = server.get_protected_area_detail(sample_wdpa_id)
    
    print(f"\nSample Protected Area Detail (WDPA ID {sample_wdpa_id}):")
    print(f"  Access Methods: {', '.join(detail['access_methods'].keys())}")
    results["sample_detail"] = {
        "wdpa_id": sample_wdpa_id,
        "access_methods": list(detail["access_methods"].keys()),
    }
    
    return results


def demo_maaamet(bbox: dict) -> dict:
    """Query Maa-amet Estonian Geoportal for available features."""
    print("\n" + "="*80)
    print("MAA-AMET ESTONIAN GEOPORTAL")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_Maa-amet_Geoportaal.json"
    
    server = MaaametServer(config_path)
    
    # Get available services
    services = server.list_services()
    print(f"\nPlatform: {services['platform']}")
    print(f"Country: {services['country']}")
    print(f"Spatial scope: {services['spatial_scope']}")
    print(f"Available services: {services['total_services']}")
    
    # Get service types
    service_types = list(set([s['type'] for s in services['services']]))
    print(f"Service types: {', '.join(service_types)}")
    
    results = {
        "platform": services["platform"],
        "country": services["country"],
        "spatial_scope": services["spatial_scope"],
        "total_services": services["total_services"],
        "service_types": service_types,
        "services": [],
        "example_wms_request": None,
    }
    
    print("\nService List:")
    for svc in services["services"]:
        print(f"  - {svc['id']}: {svc['name']} ({svc['type']})")
        results["services"].append({
            "id": svc["id"],
            "name": svc["name"],
            "type": svc["type"],
        })
    
    # Build example WMS request for orthophotos
    print("\nExample: Build WMS GetMap request for orthophotos")
    wms_request = server.build_wms_request(
        layer="ortofoto",
        bbox=bbox,
        crs="EPSG:4326",
        width=800,
        height=600
    )
    
    results["example_wms_request"] = {
        "layer": wms_request["layer"],
        "bbox": wms_request["bbox"],
        "crs": wms_request["crs"],
        "url": wms_request["url"][:100] + "..." if len(wms_request["url"]) > 100 else wms_request["url"],
    }
    
    print(f"  Layer: {wms_request['layer']}")
    print(f"  CRS: {wms_request['crs']}")
    print(f"  Size: {wms_request['dimensions']['width']}x{wms_request['dimensions']['height']}")
    print(f"  URL: {wms_request['url'][:80]}...")
    
    return results


def demo_owid() -> dict:
    """Query Our World in Data for available indicators."""
    print("\n" + "="*80)
    print("OUR WORLD IN DATA")
    print("="*80)
    
    base_dir = Path(__file__).parent
    config_path = base_dir / "config" / "mcp_configs" / "mcp_Our_World_in_Data.json"
    
    server = OWIDServer(config_path)
    
    # Get sample indicators
    indicators = server.list_sample_indicators()
    print(f"\nPlatform: {indicators['platform']}")
    print(f"Spatial scope: Global (country-level)")
    print(f"Sample indicators: {indicators['total_sample_indicators']}")
    print(f"Categories: {', '.join(indicators['categories'])}")
    
    results = {
        "platform": indicators["platform"],
        "total_sample_indicators": indicators["total_sample_indicators"],
        "categories": indicators["categories"],
        "indicators": [],
        "example_download": None,
    }
    
    print("\nSample Indicators:")
    for ind in indicators["indicators"][:5]:
        print(f"  - {ind['name']} ({ind['category']}): {ind['description'][:50]}...")
        results["indicators"].append({
            "name": ind["name"],
            "category": ind["category"],
            "slug": ind["slug"],
        })
    
    # Build example download URL
    print("\nExample: Build download URL for CO2 emissions")
    download = server.build_indicator_download_url("co2-emissions", format="csv", full_data=True)
    
    results["example_download"] = {
        "indicator": download["indicator_slug"],
        "format": download["format"],
        "url": download["download_url"][:100] + "..." if len(download["download_url"]) > 100 else download["download_url"],
    }
    
    print(f"  Indicator: {download['indicator_slug']}")
    print(f"  Format: {download['format']}")
    print(f"  URL: {download['download_url'][:80]}...")
    
    return results


def main():
    """Run the demo and save results to log file."""
    
    # Setup logging
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logs_dir = Path(__file__).parent / "logs"
    logs_dir.mkdir(exist_ok=True)
    log_file = logs_dir / f"demo_mcp_servers_{timestamp}.log"
    
    # Redirect stdout to both console and file
    class TeeOutput:
        def __init__(self, *files):
            self.files = files
        
        def write(self, data):
            for f in self.files:
                f.write(data)
                f.flush()
        
        def flush(self):
            for f in self.files:
                f.flush()
    
    log_handle = open(log_file, 'w')
    original_stdout = sys.stdout
    sys.stdout = TeeOutput(sys.stdout, log_handle)
    
    try:
        print("MCP Servers Demo: Hansen GFC, ERA5, GBIF, Maa-amet, OWID, Copernicus, Dynamic World, GEOBON, WDPA")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)
        
        # Load bounding box from GeoJSON
        geojson_path = Path(__file__).parent / "data_examples" / "estonia_testland1.geojson"
        bbox = load_geojson_bbox(geojson_path)
        
        print("\nBounding Box from estonia_testland1.geojson:")
        print(f"  Min Lon: {bbox['min_lon']:.6f}")
        print(f"  Min Lat: {bbox['min_lat']:.6f}")
        print(f"  Max Lon: {bbox['max_lon']:.6f}")
        print(f"  Max Lat: {bbox['max_lat']:.6f}")
        
        # Query each MCP server
        hansen_results = demo_hansen_gfc(bbox)
        era5_results = demo_era5_cds(bbox)
        gbif_results = demo_gbif(bbox)
        maaamet_results = demo_maaamet(bbox)
        owid_results = demo_owid()
        copernicus_results = demo_copernicus_landcover(bbox)
        dynamic_world_results = demo_dynamic_world(bbox)
        geobon_results = demo_geobon_ebv(bbox)
        wdpa_results = demo_wdpa(bbox)
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print(f"\nHansen GFC (Global):")
        print(f"  - {hansen_results['total_layers']} layers available")
        print(f"  - Total tiles covering bbox: {sum(t['count'] for t in hansen_results['tiles_per_layer'].values())}")
        
        print(f"\nERA5 CDS (Global):")
        print(f"  - {era5_results['total_variables']} climate variables available")
        print(f"  - Spatial subsetting supported")
        
        print(f"\nGBIF (Global):")
        print(f"  - {len(gbif_results['kingdoms'])} taxonomic kingdoms")
        print(f"  - Occurrence search available for bbox")
        
        print(f"\nMaa-amet (National - Estonia):")
        print(f"  - {maaamet_results['total_services']} OGC services available")
        print(f"  - Service types: {', '.join(maaamet_results['service_types'])}")
        
        print(f"\nOur World in Data (Global - Country Level):")
        print(f"  - {owid_results['total_sample_indicators']} sample indicators shown")
        print(f"  - Categories: {', '.join(owid_results['categories'][:5])}...")
        print(f"  - Data: CSV time series + JSON metadata")
        
        print(f"\nCopernicus Land Cover (Global):")
        print(f"  - {len(copernicus_results['available_years'])} years of data ({min(copernicus_results['available_years'])}-{max(copernicus_results['available_years'])})")
        print(f"  - Resolution: {copernicus_results['resolution']}")
        print(f"  - Products: {len(copernicus_results['products'])}")
        
        print(f"\nDynamic World (Global):")
        print(f"  - Resolution: {dynamic_world_results['resolution']}")
        print(f"  - Update Frequency: {dynamic_world_results['update_frequency']}")
        print(f"  - Land Cover Classes: {len(dynamic_world_results['land_cover_classes'])}")
        
        print(f"\nGEOBON EBV (Global):")
        print(f"  - EBV Classes: {len(geobon_results['ebv_classes'])}")
        
        print(f"\nWDPA Protected Areas (Global):")
        print(f"  - IUCN Categories: {len(wdpa_results['iucn_categories'])}")
        print(f"  - Access Methods: {len(wdpa_results['access_methods'])}")
        
        print("\n" + "="*80)
        print(f"Demo complete! Results saved to: {log_file}")
        print("="*80)
        
    finally:
        sys.stdout = original_stdout
        log_handle.close()
        print(f"\nLog file created: {log_file}")


if __name__ == "__main__":
    main()
