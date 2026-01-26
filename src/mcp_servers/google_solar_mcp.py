#!/usr/bin/env python
"""MCP server implementation for Google Solar API."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional
import json
import os
import urllib.parse

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import duckdb

from auth_metadata import (
    describe_auth_options,
    get_missing_credentials,
    has_required_credentials,
    load_registration_metadata,
)


class GoogleSolarServer:
    """High-level MCP server exposing Google Solar API utilities."""

    def __init__(
        self,
        config_path: Path,
        duckdb_path: Optional[Path] = None,
        dataset_id: str = "google_solar_api",
        dataset_family: str = "Google_Solar",
    ) -> None:
        self.config = self._load_config(config_path)
        self.dataset_id = dataset_id
        self.dataset_family = dataset_family
        self.catalogue_metadata = self._load_catalogue_metadata(duckdb_path, dataset_id)
        self.registration_metadata = load_registration_metadata(dataset_family)
        self.base_url = self.config.get("api", {}).get("base_url", "https://solar.googleapis.com/v1")
        self.project_id_env = self.registration_metadata.get("project_id_env_var", "GOOGLE_CLOUD_PROJECT")
        self.available_layers = [
            {"layer": "DSM", "description": "Digital surface model"},
            {"layer": "RGB", "description": "RGB imagery"},
            {"layer": "MASK", "description": "Masked (valid pixels)"},
            {"layer": "ANNUAL_FLUX", "description": "Annual solar flux"},
            {"layer": "MONTHLY_FLUX", "description": "Monthly solar flux stack"},
        ]

    # ------------------------------------------------------------------
    # Common helpers
    # ------------------------------------------------------------------
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        if not config_path.exists():
            raise FileNotFoundError(f"Google Solar MCP config not found: {config_path}")
        with config_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def _load_catalogue_metadata(
        self,
        duckdb_path: Optional[Path],
        dataset_id: str,
    ) -> Dict[str, Any]:
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
                [dataset_id],
            ).fetchone()
            if not result:
                con.close()
                return {}
            columns = [desc[0] for desc in con.description]
            metadata = dict(zip(columns, result))
            con.close()
            return metadata
        except Exception as exc:  # pragma: no cover - defensive logging only
            print(f"Warning: Could not load catalogue metadata: {exc}")
            return {}

    def get_catalogue_info(self) -> Dict[str, Any]:
        return {
            "dataset_id": self.catalogue_metadata.get("dataset_id"),
            "dataset_name": self.catalogue_metadata.get("dataset_name"),
            "provider": self.catalogue_metadata.get("provider_name_raw"),
            "primary_url": self.catalogue_metadata.get("primary_url"),
            "description": self.catalogue_metadata.get("description_short"),
            "spatial_scope": self.catalogue_metadata.get("spatial_scope"),
            "update_frequency": self.catalogue_metadata.get("update_frequency"),
        }

    def _build_auth_guidance(self) -> Dict[str, Any]:
        return {
            "registration_required": self.registration_metadata.get("registration_required", False),
            "project_id_required": self.registration_metadata.get("project_id_required", False),
            "project_id_env_var": self.project_id_env,
            "project_id_present": bool(os.environ.get(self.project_id_env)),
            "has_credentials": has_required_credentials(self.registration_metadata),
            "missing_env_vars": get_missing_credentials(self.registration_metadata),
            "options": describe_auth_options(self.registration_metadata),
            "notes": self.registration_metadata.get("notes"),
        }

    def _validate_location(self, latitude: float, longitude: float) -> Optional[str]:
        if not (-90.0 <= latitude <= 90.0):
            return "Latitude must be between -90 and 90 degrees"
        if not (-180.0 <= longitude <= 180.0):
            return "Longitude must be between -180 and 180 degrees"
        return None

    def _build_get_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        query = urllib.parse.urlencode(params, doseq=True)
        url = f"{endpoint}?{query}"
        api_key_template = f"{url}&key=${{GOOGLE_MAPS_API_KEY}}"
        return {
            "method": "GET",
            "endpoint": endpoint,
            "query_params": params,
            "request_url_template": api_key_template,
            "curl_examples": self._build_curl_examples(api_key_template, method="GET"),
            "auth": self._build_auth_guidance(),
        }

    def _build_curl_examples(self, url_with_key_template: str, method: str = "GET", body: Optional[Dict[str, Any]] = None) -> Dict[str, str]:
        body_fragment = ""
        if body is not None:
            json_payload = json.dumps(body)
            body_fragment = f" -H 'Content-Type: application/json' -d '{json_payload}'"
        api_key_cmd = f"curl -X {method} '{url_with_key_template}'{body_fragment}"
        oauth_url = (
            url_with_key_template
            .replace("&key=${GOOGLE_MAPS_API_KEY}", "")
            .replace("?key=${GOOGLE_MAPS_API_KEY}", "")
        )
        oauth_cmd = (
            f"curl -X {method} '{oauth_url}'"
            " -H 'Authorization: Bearer ${GOOGLE_OAUTH_ACCESS_TOKEN}'"
            f"{body_fragment}"
        )
        service_account_hint = "gcloud auth print-access-token --scopes=https://www.googleapis.com/auth/maps-platform.solar"
        return {
            "api_key": api_key_cmd,
            "oauth2": oauth_cmd,
            "service_account": f"{oauth_cmd}  # obtain token via `{service_account_hint}`",
        }

    # ------------------------------------------------------------------
    # Public MCP tools
    # ------------------------------------------------------------------
    def get_building_insights(
        self,
        latitude: float,
        longitude: float,
        required_quality: str = "HIGH",
    ) -> Dict[str, Any]:
        error = self._validate_location(latitude, longitude)
        if error:
            return {"error": error}

        endpoint = f"{self.base_url}/buildingInsights:findClosest"
        params = {
            "location.latitude": f"{latitude:.7f}",
            "location.longitude": f"{longitude:.7f}",
            "requiredQuality": required_quality.upper(),
        }

        response = self._build_get_request(endpoint, params)
        response.update(
            {
                "operation": "buildingInsights:findClosest",
                "description": "Retrieve rooftop solar potential for the closest building to the provided coordinates.",
                "catalogue_metadata": self.get_catalogue_info(),
            }
        )
        return response

    def get_data_layers(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 250,
        view: str = "FULL_LAYERS",
        include_roof_segments: bool = True,
    ) -> Dict[str, Any]:
        error = self._validate_location(latitude, longitude)
        if error:
            return {"error": error}

        endpoint = f"{self.base_url}/dataLayers:search"
        payload = {
            "location": {"latitude": latitude, "longitude": longitude},
            "radiusMeters": max(50, radius_meters),
            "view": view,
            "includeRoofSegmentSummaries": include_roof_segments,
        }
        url = endpoint
        response = {
            "method": "POST",
            "endpoint": endpoint,
            "json_body": payload,
            "curl_examples": self._build_curl_examples(f"{url}?key=${{GOOGLE_MAPS_API_KEY}}", method="POST", body=payload),
            "auth": self._build_auth_guidance(),
            "description": "Search for available Solar API data layers (DSM, RGB, flux) around a point.",
            "catalogue_metadata": self.get_catalogue_info(),
        }
        return response

    def get_geotiff(
        self,
        latitude: float,
        longitude: float,
        radius_meters: int = 250,
        layer_type: str = "DSM",
        pixel_size_meters: int = 0,
    ) -> Dict[str, Any]:
        error = self._validate_location(latitude, longitude)
        if error:
            return {"error": error}

        endpoint = f"{self.base_url}/geoTiff:get"
        params = {
            "location.latitude": f"{latitude:.7f}",
            "location.longitude": f"{longitude:.7f}",
            "radiusMeters": max(50, radius_meters),
            "layerType": layer_type.upper(),
        }
        if pixel_size_meters > 0:
            params["desiredResolutionMeters"] = pixel_size_meters

        response = self._build_get_request(endpoint, params)
        response.update(
            {
                "operation": "geoTiff:get",
                "description": "Download GeoTIFF assets (DSM, RGB, flux, masks) for the requested area.",
                "catalogue_metadata": self.get_catalogue_info(),
            }
        )
        return response

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            "dataset_family": self.dataset_family,
            "api_base_url": self.base_url,
            "supports_api_key": True,
            "supports_service_account": True,
            "supports_oauth2": True,
            "available_layers": self.available_layers,
            "spatial_scope": "Global coverage wherever high-resolution imagery is available",
            "geographic_coverage_notes": "City-scale rooftop coverage in the United States and select international metros.",
            "data_formats": ["JSON", "GeoTIFF"],
            "temporal_resolution": "On-demand (source imagery refreshed periodically)",
            "catalogue_metadata": self.get_catalogue_info(),
            "auth": self._build_auth_guidance(),
        }


def main() -> None:
    print("=" * 80)
    print("TASK 2 EXAMPLE: Google Solar MCP Server")
    print("=" * 80)
    config_path = Path(__file__).parent.parent / "config" / "mcp_configs" / "mcp_Google_Solar.json"
    if not config_path.exists():
        print(f"ERROR: Config file not found: {config_path}")
        return

    server = GoogleSolarServer(config_path)

    print("\nExample 1: Building insights for Googleplex")
    insights = server.get_building_insights(latitude=37.4221, longitude=-122.0841)
    print(json.dumps(insights, indent=2))

    print("\nExample 2: Data layers search")
    layers = server.get_data_layers(latitude=37.4221, longitude=-122.0841, radius_meters=120)
    print(json.dumps(layers, indent=2))

    print("\nExample 3: GeoTIFF request")
    geotiff = server.get_geotiff(latitude=37.4221, longitude=-122.0841, layer_type="ANNUAL_FLUX")
    print(json.dumps(geotiff, indent=2))

    print("\nExample 4: Capability summary")
    print(json.dumps(server.get_capabilities(), indent=2))


if __name__ == "__main__":
    main()
