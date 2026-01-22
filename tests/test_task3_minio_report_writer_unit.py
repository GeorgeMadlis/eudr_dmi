from __future__ import annotations

from task3_eudr_reports.minio_report_writer import object_keys_for_run


def test_object_keys_for_run_are_deterministic() -> None:
    keys = object_keys_for_run("run123")
    assert keys["json"] == "run123/run123.json"
    assert keys["html"] == "run123/run123.html"
    assert keys["map_html"] == "run123/run123_map.html"


def test_object_keys_do_not_change_between_calls() -> None:
    k1 = object_keys_for_run("abc")
    k2 = object_keys_for_run("abc")
    assert k1 == k2
