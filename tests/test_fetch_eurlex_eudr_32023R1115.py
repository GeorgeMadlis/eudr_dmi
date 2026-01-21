from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "fetch_eurlex_eudr_32023R1115.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("fetch_eurlex_eudr_32023R1115", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_SCRIPT = _load_script_module()
extract_summary_last_update = _SCRIPT.extract_summary_last_update
run_mirror = _SCRIPT.run_mirror


class _FakeResponse:
    def __init__(self, *, status: int, body: bytes, headers: dict[str, str] | None = None):
        self.status = status
        self._body = body
        self.headers = headers or {}

    def read(self) -> bytes:
        return self._body

    def getcode(self) -> int:
        return self.status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class TestEurlexMirror(unittest.TestCase):
    def test_extract_last_update_from_fixture(self):
        fixture = Path(__file__).resolve().parent / "fixtures" / "summary_example.html"
        html = fixture.read_text(encoding="utf-8")
        self.assertEqual(extract_summary_last_update(html), "22.5.2025")

    def test_manifest_sorted_and_format(self):
        with self.subTest("writes stable manifest.sha256"):
            # We patch urlopen so no live network is used.
            def fake_urlopen(req, timeout=20):  # noqa: ARG001
                url = req.full_url
                if "summary" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html><p>Last update 22.5.2025</p></html>",
                        headers={"content-type": "text/html"},
                    )
                if "legal-content/EN/LSU/" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html><p>EUDR digital twin entry</p></html>",
                        headers={"content-type": "text/html"},
                    )
                if "TXT/PDF" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"%PDF-1.4\n%mock\n",
                        headers={"content-type": "application/pdf"},
                    )
                # Force failures for optional endpoints
                return _FakeResponse(
                    status=202, body=b"", headers={"x-amzn-waf-action": "challenge"}
                )

            with patch.object(_SCRIPT, "urlopen", new=fake_urlopen):
                with tempfile.TemporaryDirectory() as td:
                    out_base = Path(td)
                    run_dir = run_mirror(
                        out_base=out_base,
                        run_date="2026-01-21",
                        repo_root=Path(__file__).resolve().parents[1],
                    )

                    manifest_path = run_dir / "manifest.sha256"
                    self.assertTrue(manifest_path.exists())

                    lines = manifest_path.read_text(encoding="utf-8").splitlines()
                    self.assertTrue(lines)

                    rel_paths = [line.split()[-1] for line in lines]
                    self.assertEqual(rel_paths, sorted(rel_paths))

                    for line in lines:
                        digest, rel = line.split()[:2]
                        self.assertEqual(len(digest), 64)
                        self.assertNotIn("/", rel)

    def test_metadata_minimal_schema(self):
        def fake_urlopen(req, timeout=20):  # noqa: ARG001
            url = req.full_url
            if "summary" in url:
                return _FakeResponse(
                    status=200,
                    body=b"<html><p>Last update 22.5.2025</p></html>",
                    headers={"content-type": "text/html"},
                )
            if "legal-content/EN/LSU/" in url:
                return _FakeResponse(
                    status=200,
                    body=b"<html><p>EUDR digital twin entry</p></html>",
                    headers={"content-type": "text/html"},
                )
            if "TXT/PDF" in url:
                return _FakeResponse(
                    status=200,
                    body=b"%PDF-1.4\n%mock\n",
                    headers={"content-type": "application/pdf"},
                )
            return _FakeResponse(status=404, body=b"", headers={})

        with patch.object(_SCRIPT, "urlopen", new=fake_urlopen):
            with tempfile.TemporaryDirectory() as td:
                out_base = Path(td)
                run_dir = run_mirror(
                    out_base=out_base,
                    run_date="2026-01-21",
                    repo_root=Path(__file__).resolve().parents[1],
                )
                metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))

                self.assertEqual(metadata["celex"], "32023R1115")
                self.assertEqual(metadata["canonical_name"], "eudr_2023_1115")
                self.assertIn(metadata["status"], {"complete", "partial"})

                self.assertIn("sources", metadata)
                self.assertIsInstance(metadata["sources"], list)
                self.assertTrue(metadata["sources"])

                self.assertIn("extracted_fields", metadata)
                self.assertEqual(metadata["extracted_fields"]["summary_last_update"], "22.5.2025")

                self.assertIn("run", metadata)
                self.assertEqual(metadata["run"]["run_date"], "2026-01-21")
                self.assertIn("started_at_utc", metadata["run"])
                self.assertIn("finished_at_utc", metadata["run"])
                self.assertIn("git_sha", metadata["run"])


if __name__ == "__main__":
    unittest.main()
