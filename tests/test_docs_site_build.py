from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_docs_site_build_smoke(tmp_path: Path) -> None:
    docs_root = tmp_path / "docs"

    # Inputs
    (docs_root / "articles").mkdir(parents=True, exist_ok=True)
    (docs_root / "regulation").mkdir(parents=True, exist_ok=True)
    (docs_root / "dependencies").mkdir(parents=True, exist_ok=True)

    (docs_root / "articles" / "eudr_article_summaries.md").write_text(
        """# EUDR Article Summaries

## Article 9 — Information requirements
- Bullet A

## Article 10 — Risk assessment
- Bullet B

## Article 11 — Risk mitigation
- Bullet C
""",
        encoding="utf-8",
    )

    (docs_root / "regulation" / "sources.md").write_text(
        "# Regulation Sources Registry\n\n- Placeholder\n",
        encoding="utf-8",
    )

    (docs_root / "regulation" / "links.html").write_text(
        "<!doctype html><html><head><title>Links</title></head><body>Links</body></html>\n",
        encoding="utf-8",
    )

    (docs_root / "regulation" / "policy_to_evidence_spine.md").write_text(
        "# Policy-to-Evidence Spine\n\n- Placeholder\n",
        encoding="utf-8",
    )

    (docs_root / "dependencies" / "dependencies.json").write_text(
        """{
  "version": "1.0.0",
  "dependencies": [
    {
      "id": "hansen_gfc_definitions",
      "title": "Hansen definitions",
      "url": "https://example.invalid/hansen",
      "expected_content_type": "text/html",
      "server_path": "/Users/server/audit/eudr_dmi/dependencies/hansen_gfc_definitions",
      "used_by": ["src/mcp_servers/hansen_gfc_example.py"]
    }
  ]
}
""",
        encoding="utf-8",
    )

    out_root = docs_root / "html"

    repo_root = Path(__file__).resolve().parents[1]
    builder = repo_root / "tools" / "site" / "build_docs_site.py"

    subprocess.check_call(
        [
            sys.executable,
            str(builder),
            "--docs-root",
            str(docs_root),
            "--out-root",
            str(out_root),
        ]
    )

    assert (out_root / "index.html").exists()
    assert (out_root / "articles" / "index.html").exists()
    assert (out_root / "articles" / "article_09.html").exists()
    assert (out_root / "articles" / "article_10.html").exists()
    assert (out_root / "articles" / "article_11.html").exists()
    assert (out_root / "dependencies" / "index.html").exists()
    assert (out_root / "aoi_reports" / "index.html").exists()
