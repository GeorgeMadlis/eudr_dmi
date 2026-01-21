import hashlib
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
    def _write_prev_run(
        self,
        *,
        out_base: Path,
        run_date: str,
        entrypoint_status: dict,
        metadata: dict,
    ):
        prev_dir = out_base / run_date
        prev_dir.mkdir(parents=True, exist_ok=True)
        (prev_dir / "entrypoint_status.json").write_text(
            json.dumps(entrypoint_status, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        (prev_dir / "metadata.json").write_text(
            json.dumps(metadata, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def _sha256_hex(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

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

    def test_needs_update_lsu_reachable_changed(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

            prev_lsu_body = b"<html><p>EUDR digital twin entry v1</p></html>"
            cur_lsu_body = b"<html><p>EUDR digital twin entry v2</p></html>"

            self._write_prev_run(
                out_base=out_base,
                run_date="2026-01-20",
                entrypoint_status={
                    "attempted": True,
                    "entrypoint_url": "https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32023R1115",
                    "error": None,
                    "http_status": 200,
                    "reachable": True,
                    "evidence": {
                        "lsu_entry_sha256": self._sha256_hex(prev_lsu_body),
                        "lsu_updated_on": None,
                    },
                },
                metadata={
                    "celex": "32023R1115",
                    "canonical_name": "eudr_2023_1115",
                    "extracted_fields": {"summary_last_update": "22.5.2025"},
                },
            )

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
                        body=cur_lsu_body,
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
                run_dir = run_mirror(
                    out_base=out_base,
                    run_date="2026-01-21",
                    repo_root=Path(__file__).resolve().parents[1],
                )
                metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
                self.assertTrue(metadata["needs_update"])
                trigger = json.loads(
                    (run_dir / "digital_twin_trigger.json").read_text(encoding="utf-8")
                )
                self.assertEqual(trigger["previous_run"], "2026-01-20")
                self.assertEqual(trigger["current_run"], "2026-01-21")
                self.assertIn("lsu_sha256_changed", trigger["reason"])

    def test_needs_update_lsu_unreachable_but_pdf_changed(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

            prev_pdf_body = b"%PDF-1.4\n%mock-v1\n"
            cur_pdf_body = b"%PDF-1.4\n%mock-v2\n"

            self._write_prev_run(
                out_base=out_base,
                run_date="2026-01-20",
                entrypoint_status={
                    "attempted": True,
                    "entrypoint_url": "https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32023R1115",
                    "error": "waf_challenge",
                    "http_status": 202,
                    "reachable": False,
                    "evidence": {
                        "fallback": {
                            "pdf": {
                                "sha256": self._sha256_hex(prev_pdf_body),
                                "etag": None,
                                "last_modified": None,
                                "content_length": len(prev_pdf_body),
                                "content_type": "application/pdf",
                                "http_status": 200,
                                "error": None,
                            },
                            "html": None,
                            "eli_oj": None,
                        }
                    },
                },
                metadata={
                    "celex": "32023R1115",
                    "canonical_name": "eudr_2023_1115",
                    "extracted_fields": {"summary_last_update": "22.5.2025"},
                },
            )

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
                        status=202,
                        body=b"",
                        headers={"x-amzn-waf-action": "challenge"},
                    )
                if "TXT/PDF" in url:
                    return _FakeResponse(
                        status=200,
                        body=cur_pdf_body,
                        headers={"content-type": "application/pdf"},
                    )
                return _FakeResponse(status=404, body=b"", headers={})

            with patch.object(_SCRIPT, "urlopen", new=fake_urlopen):
                run_dir = run_mirror(
                    out_base=out_base,
                    run_date="2026-01-21",
                    repo_root=Path(__file__).resolve().parents[1],
                )
                metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
                self.assertTrue(metadata["needs_update"])
                trigger = json.loads(
                    (run_dir / "digital_twin_trigger.json").read_text(encoding="utf-8")
                )
                self.assertIn("lsu_unreachable_but_pdf_sha256_changed", trigger["reason"])

    def test_needs_update_false_when_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

            lsu_body = b"<html><p>EUDR digital twin entry stable</p></html>"
            lsu_sha = self._sha256_hex(lsu_body)

            self._write_prev_run(
                out_base=out_base,
                run_date="2026-01-20",
                entrypoint_status={
                    "attempted": True,
                    "entrypoint_url": "https://eur-lex.europa.eu/legal-content/EN/LSU/?uri=CELEX:32023R1115",
                    "error": None,
                    "http_status": 200,
                    "reachable": True,
                    "evidence": {"lsu_entry_sha256": lsu_sha, "lsu_updated_on": None},
                },
                metadata={
                    "celex": "32023R1115",
                    "canonical_name": "eudr_2023_1115",
                    "extracted_fields": {"summary_last_update": "22.5.2025"},
                },
            )

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
                        body=lsu_body,
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
                run_dir = run_mirror(
                    out_base=out_base,
                    run_date="2026-01-21",
                    repo_root=Path(__file__).resolve().parents[1],
                )
                metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
                self.assertFalse(metadata["needs_update"])
                self.assertFalse((run_dir / "digital_twin_trigger.json").exists())


if __name__ == "__main__":
    unittest.main()
