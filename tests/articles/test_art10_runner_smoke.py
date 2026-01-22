from __future__ import annotations

import pytest

from eudr_dmi.articles.art_10 import runner as art10_runner


def test_art10_compute_bundle_id_is_deterministic(tmp_path) -> None:
    aoi = tmp_path / "aoi.geojson"
    aoi.write_text("{\"type\":\"Polygon\",\"coordinates\":[[[0,0],[1,0],[1,1],[0,1],[0,0]]]}\n")

    bid1 = art10_runner.compute_bundle_id(aoi, "2026-01-01", "2026-01-31")
    bid2 = art10_runner.compute_bundle_id(aoi, "2026-01-01", "2026-01-31")

    assert bid1 == bid2
    assert bid1.startswith("art10_")


def test_art10_parser_help_exits_cleanly() -> None:
    with pytest.raises(SystemExit) as excinfo:
        art10_runner.main(["--help"])
    assert excinfo.value.code == 0
