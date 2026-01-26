from __future__ import annotations

import pytest

from eudr_dmi.articles.art_11 import runner as art11_runner


def test_art11_compute_bundle_id_is_deterministic(tmp_path) -> None:
    aoi = tmp_path / "aoi.geojson"
    aoi.write_text("{\"type\":\"Polygon\",\"coordinates\":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}\n")

    bid1 = art11_runner.compute_bundle_id(aoi, "2026-01-01", "2026-01-31")
    bid2 = art11_runner.compute_bundle_id(aoi, "2026-01-01", "2026-01-31")

    assert bid1 == bid2
    assert bid1.startswith("art11_")


def test_art11_parser_help_exits_cleanly() -> None:
    with pytest.raises(SystemExit) as excinfo:
        art11_runner.main(["--help"])
    assert excinfo.value.code == 0
