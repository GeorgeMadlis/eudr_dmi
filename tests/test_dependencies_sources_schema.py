from __future__ import annotations

import json
from pathlib import Path


def test_dependencies_sources_json_validates_against_schema() -> None:
    repo_root = Path(__file__).resolve().parents[1]

    registry_path = repo_root / "docs" / "dependencies" / "sources.json"
    schema_path = repo_root / "schemas" / "dependencies_sources.schema.json"

    instance = json.loads(registry_path.read_text(encoding="utf-8"))
    schema = json.loads(schema_path.read_text(encoding="utf-8"))

    # Keep dependency lightweight: jsonschema is a dev/test-only dependency.
    import jsonschema

    jsonschema.validate(instance=instance, schema=schema)
