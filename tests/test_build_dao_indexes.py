from __future__ import annotations

import re
from pathlib import Path

from tools.site.build_dao_indexes import build_indexes


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def test_build_dao_indexes_stable_ordering_and_no_timestamps(tmp_path: Path) -> None:
    proposals_root = tmp_path / "proposals"
    audit_root = tmp_path / "audit" / "proposals"

    # Intentionally create out of order.
    p2 = proposals_root / "SCP-2026-002-beta"
    p1 = proposals_root / "SCP-2026-001-alpha"
    _write(
        p2 / "proposal.yaml",
        "\n".join(
            [
                'scp_id: "SCP-2026-002-beta"',
                'title: "Second"',
                "proposer:",
                '  organization: "OrgB"',
                "scope:",
                '  change_type: "DOCS"',
                "claim: |",
                "  Add docs.",
                "",
            ]
        ),
    )
    _write(
        p1 / "proposal.yaml",
        "\n".join(
            [
                'scp_id: "SCP-2026-001-alpha"',
                'title: "First"',
                "proposer:",
                '  organization: "OrgA"',
                "scope:",
                '  change_type: "BUNDLE"',
                "claim: |",
                "  Add bundle.",
                "",
            ]
        ),
    )

    # Mark only SCP-2026-002-beta as a dev proposal by creating an audit dir.
    (audit_root / "SCP-2026-002-beta").mkdir(parents=True, exist_ok=True)
    _write(audit_root / "SCP-2026-002-beta" / "status.txt", "ACCEPTED\n")

    out_stakeholders = tmp_path / "out" / "stakeholders.yaml"
    out_dev = tmp_path / "out" / "dev.yaml"

    build_indexes(
        proposals_root=proposals_root,
        audit_proposals_root=audit_root,
        out_stakeholders=out_stakeholders,
        out_dev=out_dev,
    )

    stakeholders_txt = out_stakeholders.read_text(encoding="utf-8")
    dev_txt = out_dev.read_text(encoding="utf-8")

    # Stable ordering: alpha before beta, but beta is dev-index only.
    assert stakeholders_txt.find("SCP-2026-001-alpha") != -1
    assert stakeholders_txt.find("SCP-2026-002-beta") == -1

    assert dev_txt.find("SCP-2026-002-beta") != -1

    # Status is included only when available.
    assert "status: \"ACCEPTED\"" in dev_txt

    # No timestamps: forbid common generated-at patterns.
    assert "generated_at" not in stakeholders_txt
    assert "generated_at" not in dev_txt
    assert re.search(r"\\d{4}-\\d{2}-\\d{2}T", stakeholders_txt) is None
    assert re.search(r"\\d{4}-\\d{2}-\\d{2}T", dev_txt) is None
