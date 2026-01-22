from __future__ import annotations

import importlib.util
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[1]
WATCHER_PATH = REPO_ROOT / "scripts" / "watch_eurlex_eudr_32023R1115.py"
FETCH_PATH = REPO_ROOT / "scripts" / "fetch_eurlex_eudr_32023R1115.py"


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

_scripts_pkg = types.ModuleType("scripts")
_scripts_pkg.__path__ = [str(REPO_ROOT / "scripts")]
sys.modules.setdefault("scripts", _scripts_pkg)

_FETCH = _load_module("scripts.fetch_eurlex_eudr_32023R1115", FETCH_PATH)
_WATCHER = _load_module("scripts.watch_eurlex_eudr_32023R1115", WATCHER_PATH)


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


class TestWatcherExitCodes(unittest.TestCase):
    def test_exit_0_when_no_change(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

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
                        body=b"<html><p>EUDR digital twin entry stable</p></html>",
                        headers={"content-type": "text/html"},
                    )
                if "TXT/PDF" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"%PDF-1.4\n%mock\n",
                        headers={"content-type": "application/pdf"},
                    )
                if "legal-content/EN/TXT/" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>CELEX:32023R1115</html>",
                        headers={"content-type": "text/html"},
                    )
                if "eli/reg/2023/1115/oj/eng" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>ok</html>",
                        headers={"content-type": "text/html"},
                    )
                return _FakeResponse(status=404, body=b"", headers={})

            # Establish previous run.
            with patch.object(_FETCH, "urlopen", new=fake_urlopen):
                _FETCH.run_mirror(
                    out_base=out_base,
                    run_date="2026-01-20",
                    repo_root=REPO_ROOT,
                )

            with patch.object(_FETCH, "urlopen", new=fake_urlopen):
                rc = _WATCHER.main(["--out", str(out_base), "--date", "2026-01-21"])
            self.assertEqual(rc, 0)

    def test_exit_2_when_change_detected(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

            def fake_urlopen_prev(req, timeout=20):  # noqa: ARG001
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
                        body=b"<html><p>entry v1</p></html>",
                        headers={"content-type": "text/html"},
                    )
                if "TXT/PDF" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"%PDF-1.4\n%mock\n",
                        headers={"content-type": "application/pdf"},
                    )
                if "legal-content/EN/TXT/" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>CELEX:32023R1115</html>",
                        headers={"content-type": "text/html"},
                    )
                if "eli/reg/2023/1115/oj/eng" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>ok</html>",
                        headers={"content-type": "text/html"},
                    )
                return _FakeResponse(status=404, body=b"", headers={})

            def fake_urlopen_cur(req, timeout=20):  # noqa: ARG001
                url = req.full_url
                if "legal-content/EN/LSU/" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html><p>entry v2</p></html>",
                        headers={"content-type": "text/html"},
                    )
                return fake_urlopen_prev(req, timeout=timeout)

            with patch.object(_FETCH, "urlopen", new=fake_urlopen_prev):
                _FETCH.run_mirror(
                    out_base=out_base,
                    run_date="2026-01-20",
                    repo_root=REPO_ROOT,
                )

            with patch.object(_FETCH, "urlopen", new=fake_urlopen_cur):
                rc = _WATCHER.main(["--out", str(out_base), "--date", "2026-01-21"])
            self.assertEqual(rc, 2)

    def test_exit_3_when_partial_uncertain(self):
        with tempfile.TemporaryDirectory() as td:
            out_base = Path(td)

            def fake_urlopen_unreachable(req, timeout=20):  # noqa: ARG001
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
                        body=b"%PDF-1.4\n%mock\n",
                        headers={"content-type": "application/pdf"},
                    )
                if "legal-content/EN/TXT/" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>CELEX:32023R1115</html>",
                        headers={"content-type": "text/html"},
                    )
                if "eli/reg/2023/1115/oj/eng" in url:
                    return _FakeResponse(
                        status=200,
                        body=b"<html>ok</html>",
                        headers={"content-type": "text/html"},
                    )
                return _FakeResponse(status=404, body=b"", headers={})

            with patch.object(_FETCH, "urlopen", new=fake_urlopen_unreachable):
                _FETCH.run_mirror(
                    out_base=out_base,
                    run_date="2026-01-20",
                    repo_root=REPO_ROOT,
                )

            with patch.object(_FETCH, "urlopen", new=fake_urlopen_unreachable):
                rc = _WATCHER.main(["--out", str(out_base), "--date", "2026-01-21"])
            self.assertEqual(rc, 3)


if __name__ == "__main__":
    unittest.main()
