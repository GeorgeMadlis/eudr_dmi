from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


def _import_module_from_path(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(path))
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_demo_mcp_maaamet_help_works() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "demos" / "demo_mcp_maaamet.py"
    mod = _import_module_from_path("demo_mcp_maaamet", script)

    with pytest.raises(SystemExit) as excinfo:
        mod.main(["--help"])
    assert excinfo.value.code == 0


def test_eudr_compliance_check_estonia_help_works() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    script = repo_root / "scripts" / "demos" / "eudr_compliance_check_estonia.py"
    mod = _import_module_from_path("eudr_compliance_check_estonia", script)

    with pytest.raises(SystemExit) as excinfo:
        mod.main(["--help"])
    assert excinfo.value.code == 0
