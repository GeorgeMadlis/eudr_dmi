#!/usr/bin/env python
"""
FAO MCP server (Task 2 – MCP-Based Access And Monitoring)

Provides tools to access FAO datasets:
- FAOSTAT: Tabular statistics via SDMX
- FAO Hand-in-Hand: Geospatial layers via GeoNetwork/CSW
"""

from __future__ import annotations

import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fao_clients import (
    FaoGeoClient,
    FaostatClient,
    make_fao_geo_client_from_catalogue_row,
    make_faostat_client_from_catalogue_row,
)


def get_fao_catalogue_rows() -> Dict[str, pd.Series]:
    """Load FAO-related rows from catalogue CSV.
    
    Returns a mapping from dataset_family to representative row.
    If no FAO families exist, returns defaults using standard FAO URLs.
    """
    csv_path = Path(__file__).parent.parent / "data_db" / "dataset_catalogue_with_families.csv"
    
    if not csv_path.exists():
        return {}
    
    df = pd.read_csv(csv_path)
    
    fao_families = ["FAO FAOSTAT", "FAO Hand-in-Hand Geospatial", "FAO"]
    mask = df["dataset_family"].isin(fao_families)
    fao_rows = df[mask]
    
    result: Dict[str, pd.Series] = {}
    
    for family in fao_families:
        family_rows = fao_rows[fao_rows["dataset_family"] == family]
        if not family_rows.empty:
            result[family] = family_rows.iloc[0]
    
    if not result:
        result["FAO FAOSTAT"] = pd.Series({
            "api_url": FaostatClient.DEFAULT_BASE_URL,
            "access_type": "open",
            "requires_registration": False,
        })
        result["FAO Hand-in-Hand Geospatial"] = pd.Series({
            "metadata_url": FaoGeoClient.DEFAULT_CSW_URL,
            "access_type": "open",
            "requires_registration": False,
        })
    
    return result


class FAOServer:
    """MCP Server implementation for FAO datasets (FAOSTAT + HIH Geospatial)."""
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        dataset_id: str = "fao",
    ) -> None:
        self.dataset_id = dataset_id
        self.catalogue_rows = get_fao_catalogue_rows()
        
        faostat_row = self.catalogue_rows.get(
            "FAO FAOSTAT",
            pd.Series({"api_url": FaostatClient.DEFAULT_BASE_URL}),
        )
        hih_row = self.catalogue_rows.get(
            "FAO Hand-in-Hand Geospatial",
            pd.Series({"metadata_url": FaoGeoClient.DEFAULT_CSW_URL}),
        )
        
        self.faostat_client = make_faostat_client_from_catalogue_row(faostat_row)
        self.fao_geo_client = make_fao_geo_client_from_catalogue_row(hih_row)
        self.faostat_row = faostat_row
        self.hih_row = hih_row
    
    def list_faostat_dataflows(
        self,
        filter_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List available FAOSTAT dataflows."""
        df = self.faostat_client.list_dataflows()
        
        if filter_text:
            mask = (
                df["id"].str.contains(filter_text, case=False, na=False)
                | df["name"].str.contains(filter_text, case=False, na=False)
            )
            df = df[mask]
        
        dataflows = [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"],
            }
            for _, row in df.iterrows()
        ]
        
        return {
            "dataflows": dataflows,
            "total": len(dataflows),
            "filtered": filter_text is not None,
        }
    
    def describe_faostat_dataflow(self, dataflow_id: str) -> Dict[str, Any]:
        """Get detailed metadata for a FAOSTAT dataflow."""
        metadata = self.faostat_client.get_dataflow_metadata(dataflow_id)
        return {
            "dataflow_id": dataflow_id,
            "metadata": metadata,
        }
    
    def get_faostat_data(
        self,
        dataflow_id: str,
        key: str = "ALL",
        start_period: Optional[str] = None,
        end_period: Optional[str] = None,
        max_rows: Optional[int] = 100_000,
    ) -> Dict[str, Any]:
        """Fetch FAOSTAT data and save to file."""
        access_type = self.faostat_row.get("access_type", "open")
        requires_reg = self.faostat_row.get("requires_registration", False)
        
        if access_type != "open" or requires_reg:
            raise ValueError(
                f"FAOSTAT access requires registration or is restricted: "
                f"access_type={access_type}, requires_registration={requires_reg}"
            )
        
        df = self.faostat_client.get_data(
            dataflow_id,
            key=key,
            start_period=start_period,
            end_period=end_period,
        )
        
        notes = None
        if max_rows and len(df) > max_rows:
            notes = f"Truncated from {len(df)} to {max_rows} rows"
            df = df.head(max_rows)
        
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        out_dir = Path(__file__).parent.parent / "data_examples" / "fao" / "faostat"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{dataflow_id}_{timestamp}.csv"
        
        df.to_csv(out_path, index=False)
        
        query_url = f"{self.faostat_client.base_url}/{dataflow_id}/{key}"
        params = []
        if start_period:
            params.append(f"startPeriod={start_period}")
        if end_period:
            params.append(f"endPeriod={end_period}")
        if params:
            query_url += "?" + "&".join(params)
        
        return {
            "table_path": str(out_path),
            "n_rows": len(df),
            "dataflow_id": dataflow_id,
            "query_url": query_url,
            "notes": notes,
        }
    
    def search_hih_layers(
        self,
        query: str,
        max_records: int = 50,
    ) -> Dict[str, Any]:
        """Search FAO Hand-in-Hand geospatial layers."""
        records = self.fao_geo_client.csw_search(
            constraint=query,
            max_records=max_records,
        )
        
        layers = [
            {
                "record_id": rec["record_id"],
                "title": rec["title"],
                "abstract": rec["abstract"],
                "keywords": rec["keywords"],
                "bbox": rec["bbox"],
                "temporal_coverage": rec["temporal_coverage"],
            }
            for rec in records
        ]
        
        return {
            "layers": layers,
            "total": len(layers),
            "query": query,
        }
    
    def get_hih_layer_metadata(self, record_id: str) -> Dict[str, Any]:
        """Get detailed metadata for an HIH layer."""
        metadata = self.fao_geo_client.get_record_by_id(record_id)
        return {
            "record_id": record_id,
            "metadata": metadata,
        }
    
    def download_hih_layer(
        self,
        record_id: str,
        preferred_protocol: Literal["download", "WMS", "WFS"] = "download",
        bbox: Optional[tuple[float, float, float, float]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        crs: str = "EPSG:4326",
        output_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download an HIH layer using available protocols."""
        metadata = self.fao_geo_client.get_record_by_id(record_id)
        links = metadata.get("links", [])
        
        if not links:
            return {
                "files": [],
                "layer_type": "unknown",
                "chosen_protocol": "none",
                "notes": "No download links available for this record",
            }
        
        out_dir = Path(__file__).parent.parent / "data_examples" / "fao" / "hih" / record_id
        out_dir.mkdir(parents=True, exist_ok=True)
        
        chosen_link = None
        chosen_protocol = "unknown"
        
        for link in links:
            protocol = (link.get("protocol") or "").upper()
            if preferred_protocol == "WMS" and "WMS" in protocol:
                chosen_link = link
                chosen_protocol = "WMS"
                break
            elif preferred_protocol == "WFS" and "WFS" in protocol:
                chosen_link = link
                chosen_protocol = "WFS"
                break
            elif preferred_protocol == "download" and protocol in ("HTTP", "HTTPS", ""):
                chosen_link = link
                chosen_protocol = "download"
                break
        
        if not chosen_link:
            chosen_link = links[0]
            chosen_protocol = chosen_link.get("protocol", "download")
        
        files: List[str] = []
        layer_type = "unknown"
        
        try:
            if "WMS" in chosen_protocol.upper():
                if not bbox:
                    bbox = (-180.0, -90.0, 180.0, 90.0)
                if not width:
                    width = 1024
                if not height:
                    height = 1024
                
                out_path = out_dir / f"{record_id}_wms.tif"
                self.fao_geo_client.download_wms_raster(
                    base_wms_url=chosen_link["url"],
                    layer=record_id,
                    bbox=bbox,
                    width=width,
                    height=height,
                    crs=crs,
                    out_path=out_path,
                    format=output_format or "image/geotiff",
                )
                files.append(str(out_path))
                layer_type = "raster"
            
            elif "WFS" in chosen_protocol.upper():
                out_path = out_dir / f"{record_id}_wfs.geojson"
                self.fao_geo_client.download_wfs_vector(
                    base_wfs_url=chosen_link["url"],
                    type_name=record_id,
                    bbox=bbox,
                    out_path=out_path,
                    output_format=output_format or "application/json",
                )
                files.append(str(out_path))
                layer_type = "vector"
            
            else:
                url = chosen_link["url"]
                extension = Path(url).suffix or ".dat"
                out_path = out_dir / f"{record_id}{extension}"
                self.fao_geo_client.download_file(url, out_path)
                files.append(str(out_path))
                layer_type = "file"
        
        except Exception as e:
            return {
                "files": [],
                "layer_type": layer_type,
                "chosen_protocol": chosen_protocol,
                "notes": f"Download failed: {str(e)}",
            }
        
        return {
            "files": files,
            "layer_type": layer_type,
            "chosen_protocol": chosen_protocol,
            "notes": None,
        }
    
    def health_check(self, include_details: bool = False) -> Dict[str, Any]:
        """Check health of FAO services."""
        components: List[Dict[str, Any]] = []
        
        try:
            start = time.time()
            self.faostat_client.list_dataflows()
            latency = (time.time() - start) * 1000
            components.append({
                "name": "FAOSTAT",
                "status": "ok",
                "latency_ms": round(latency, 2),
                "last_error": None,
            })
        except Exception as e:
            components.append({
                "name": "FAOSTAT",
                "status": "down",
                "latency_ms": None,
                "last_error": str(e),
            })
        
        try:
            start = time.time()
            self.fao_geo_client.csw_get_capabilities()
            latency = (time.time() - start) * 1000
            components.append({
                "name": "FAO HIH GeoNetwork",
                "status": "ok",
                "latency_ms": round(latency, 2),
                "last_error": None,
            })
        except Exception as e:
            components.append({
                "name": "FAO HIH GeoNetwork",
                "status": "down",
                "latency_ms": None,
                "last_error": str(e),
            })
        
        statuses = [c["status"] for c in components]
        if all(s == "ok" for s in statuses):
            overall = "ok"
        elif any(s == "down" for s in statuses):
            overall = "down"
        else:
            overall = "degraded"
        
        return {
            "status": overall,
            "components": components if include_details else [],
            "timestamp": datetime.now().isoformat(),
        }
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get information about FAO datasets."""
        return {
            "platform": "FAO - Food and Agriculture Organization",
            "dataset_families": ["FAOSTAT", "Hand-in-Hand Geospatial"],
            "faostat": {
                "base_url": self.faostat_client.base_url,
                "description": "Global agricultural and food security statistics via SDMX",
                "data_type": "tabular",
            },
            "hih_geospatial": {
                "csw_url": self.fao_geo_client.csw_url,
                "description": "Geospatial layers and maps via GeoNetwork CSW",
                "data_type": "spatial",
            },
            "capabilities": [
                "List FAOSTAT dataflows",
                "Download FAOSTAT data as CSV",
                "Search geospatial layers",
                "Download layers via WMS/WFS",
                "Health monitoring",
            ],
        }


def main() -> None:
    """Example usage of FAO MCP Server."""
    print("=" * 80)
    print("TASK 2 EXAMPLE: FAO MCP Server")
    print("=" * 80)
    print()
    
    server = FAOServer()
    
    print("Example 1: FAO Platform Information")
    print("-" * 80)
    info = server.get_dataset_info()
    print(f"Platform: {info['platform']}")
    print(f"Dataset Families: {', '.join(info['dataset_families'])}")
    print("\nCapabilities:")
    for cap in info["capabilities"]:
        print(f"  • {cap}")
    
    print("\n\nExample 2: List FAOSTAT Dataflows (filtered)")
    print("-" * 80)
    result = server.list_faostat_dataflows(filter_text="population")
    print(f"Found {result['total']} dataflows matching 'population'")
    for df in result["dataflows"][:3]:
        print(f"\n  ID: {df['id']}")
        print(f"  Name: {df['name']}")
        if df["description"]:
            desc = df["description"][:80] + "..." if len(df["description"]) > 80 else df["description"]
            print(f"  Description: {desc}")
    
    print("\n\nExample 3: Health Check")
    print("-" * 80)
    health = server.health_check(include_details=True)
    print(f"Overall Status: {health['status']}")
    print("\nComponent Status:")
    for comp in health["components"]:
        status_icon = "✓" if comp["status"] == "ok" else "✗"
        print(f"  {status_icon} {comp['name']}: {comp['status']}")
        if comp["latency_ms"]:
            print(f"    Latency: {comp['latency_ms']}ms")
        if comp["last_error"]:
            print(f"    Error: {comp['last_error']}")
    
    print("\n\nExample 4: Search HIH Geospatial Layers")
    print("-" * 80)
    search_result = server.search_hih_layers(query="soil", max_records=5)
    print(f"Found {search_result['total']} layers matching 'soil'")
    for layer in search_result["layers"][:3]:
        print(f"\n  Title: {layer['title']}")
        print(f"  ID: {layer['record_id']}")
        if layer["abstract"]:
            abstract = layer["abstract"][:100] + "..." if len(layer["abstract"]) > 100 else layer["abstract"]
            print(f"  Abstract: {abstract}")
        if layer["keywords"]:
            print(f"  Keywords: {', '.join(layer['keywords'][:5])}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
