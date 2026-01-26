from __future__ import annotations

import importlib

REQUIRED = [
    "rasterio",
    "shapely",
    "pyproj",
    "numpy",
]


def _check(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
        print(f"PASS: {module_name}")
        return True
    except Exception as exc:
        print(f"FAIL: {module_name} ({exc.__class__.__name__}: {exc})")
        return False


def main() -> int:
    ok = True
    for name in REQUIRED:
        ok = _check(name) and ok

    if not ok:
        print("\nOne or more method dependencies are missing.")
        print("Install with: pip install -r requirements-methods.txt")
        return 1

    print("\nAll method dependencies present.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
