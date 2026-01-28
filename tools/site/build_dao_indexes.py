#!/usr/bin/env python3
"""Build deterministic DAO proposal indexes.

Inputs (default relative to repo root):
- proposals/ (directories named SCP-*)
- optional audit/proposals/ (directories named SCP-*) for decision/status hints

Outputs (overwritten deterministically):
- docs/dao/machine/dao_stakeholders/proposals_index.yaml
- docs/dao/machine/dao_dev/proposals_index.yaml

Determinism contract:
- No timestamps
- Stable ordering (lexicographic by scp_id)
- LF newlines

Notes
- This tool intentionally uses a very small YAML subset parser because the repo
  does not depend on a YAML library.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProposalEntry:
    scp_id: str
    title: str
    proposer_org: str
    change_type: str
    status: str | None


_SCP_DIR_RE = re.compile(r"^SCP-[0-9]{4}-[0-9]{3}-.+$")


def _repo_root_from_this_file() -> Path:
    # tools/site/build_dao_indexes.py -> repo root is ../../..
    return Path(__file__).resolve().parents[2]


def _read_text_lf(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _write_text_lf(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8", newline="\n")


def _yaml_get_scalar(yaml_text: str, key: str) -> str | None:
    # Supports top-level `key: value` where value is quoted or bare.
    # Also supports `key: |` followed by indented block; returns first non-empty line.
    pat = re.compile(rf"^(?P<indent> *){re.escape(key)}:\s*(?P<rest>.*)$")
    lines = yaml_text.split("\n")
    for i, line in enumerate(lines):
        m = pat.match(line)
        if not m:
            continue
        rest = m.group("rest").strip()
        if rest == "|":
            # Block scalar: consume subsequent indented lines.
            indent = len(m.group("indent"))
            block: list[str] = []
            for j in range(i + 1, len(lines)):
                l2 = lines[j]
                if not l2.strip():
                    continue
                # At least 2 spaces more indent than key line is typical; accept > indent.
                if len(l2) - len(l2.lstrip(" ")) <= indent:
                    break
                block.append(l2.strip())
            for b in block:
                if b:
                    return b
            return ""

        if rest.startswith("\"") and rest.endswith("\"") and len(rest) >= 2:
            return rest[1:-1]
        if rest.startswith("'") and rest.endswith("'") and len(rest) >= 2:
            return rest[1:-1]
        # Strip inline comments for bare scalars.
        bare = rest.split("#", 1)[0].strip()
        return bare
    return None


def _yaml_get_nested_scalar(yaml_text: str, parent_key: str, child_key: str) -> str | None:
    # Supports a subset like:
    # parent_key:
    #   child_key: value
    lines = yaml_text.split("\n")
    parent_pat = re.compile(rf"^(?P<indent> *){re.escape(parent_key)}:\s*$")
    for i, line in enumerate(lines):
        pm = parent_pat.match(line)
        if not pm:
            continue
        parent_indent = len(pm.group("indent"))
        child_pat = re.compile(
            rf"^(?P<indent> +){re.escape(child_key)}:\s*(?P<rest>.*)$"
        )
        for j in range(i + 1, len(lines)):
            l2 = lines[j]
            if not l2.strip():
                continue
            indent2 = len(l2) - len(l2.lstrip(" "))
            if indent2 <= parent_indent:
                break
            cm = child_pat.match(l2)
            if not cm:
                continue
            rest = cm.group("rest").strip()
            if rest.startswith("\"") and rest.endswith("\"") and len(rest) >= 2:
                return rest[1:-1]
            if rest.startswith("'") and rest.endswith("'") and len(rest) >= 2:
                return rest[1:-1]
            return rest.split("#", 1)[0].strip()
    return None


def _read_status_from_audit_dir(audit_scp_dir: Path) -> str | None:
    # Priority order (most explicit first).
    candidates = [
        audit_scp_dir / "decision.json",
        audit_scp_dir / "status.json",
        audit_scp_dir / "decision.yaml",
        audit_scp_dir / "decision.yml",
        audit_scp_dir / "status.yaml",
        audit_scp_dir / "status.yml",
        audit_scp_dir / "status.txt",
        audit_scp_dir / "decision_status.txt",
    ]

    for p in candidates:
        if not p.is_file():
            continue
        if p.suffix == ".json":
            try:
                obj = json.loads(_read_text_lf(p))
            except (OSError, json.JSONDecodeError):
                continue
            for k in ("status", "decision", "decision_status"):
                v = obj.get(k)
                if isinstance(v, str) and v.strip():
                    return v.strip()
            continue

        if p.suffix in {".yaml", ".yml"}:
            txt = _read_text_lf(p)
            v = _yaml_get_scalar(txt, "status")
            if v and v.strip():
                return v.strip()
            v = _yaml_get_scalar(txt, "decision")
            if v and v.strip():
                return v.strip()
            continue

        # .txt
        try:
            txt = _read_text_lf(p)
        except OSError:
            continue
        for line in txt.split("\n"):
            s = line.strip()
            if s:
                return s

    return None


def _parse_proposal_entry(*, scp_dir: Path, audit_proposals_root: Path | None) -> ProposalEntry:
    proposal_yaml_path = scp_dir / "proposal.yaml"
    yaml_text = _read_text_lf(proposal_yaml_path) if proposal_yaml_path.is_file() else ""

    scp_id = scp_dir.name

    title = _yaml_get_scalar(yaml_text, "title")
    if not title:
        # Fall back to the first line of `claim: |` if present.
        title = _yaml_get_scalar(yaml_text, "claim") or ""

    proposer_org = _yaml_get_nested_scalar(yaml_text, "proposer", "organization")
    if proposer_org is None:
        proposer_org = _yaml_get_nested_scalar(yaml_text, "proposer", "org")
    proposer_org = proposer_org or ""

    change_type = _yaml_get_nested_scalar(yaml_text, "scope", "change_type")
    if change_type is None:
        change_type = _yaml_get_scalar(yaml_text, "change_type")
    change_type = change_type or ""

    status: str | None = None
    if audit_proposals_root is not None:
        audit_scp_dir = audit_proposals_root / scp_id
        if audit_scp_dir.is_dir():
            status = _read_status_from_audit_dir(audit_scp_dir)

    return ProposalEntry(
        scp_id=scp_id,
        title=title,
        proposer_org=proposer_org,
        change_type=change_type,
        status=status,
    )


def _yaml_quote(s: str) -> str:
    # Deterministic quoting.
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _render_index_yaml(*, proposals: list[ProposalEntry], html_base: str) -> str:
    lines: list[str] = []
    lines.append('schema_version: "1.0"')
    lines.append('generated_by: "tools/site/build_dao_indexes.py"')
    if not proposals:
        lines.append("proposals: []")
        return "\n".join(lines) + "\n"

    lines.append("proposals:")
    for p in proposals:
        lines.append(f"  - scp_id: {_yaml_quote(p.scp_id)}")
        lines.append(f"    title: {_yaml_quote(p.title)}")
        lines.append("    proposer:")
        lines.append(f"      org: {_yaml_quote(p.proposer_org)}")
        lines.append("    scope:")
        lines.append(f"      change_type: {_yaml_quote(p.change_type)}")
        if p.status is not None:
            lines.append(f"    status: {_yaml_quote(p.status)}")
        html_path = f"{html_base}/{p.scp_id}/proposal.html"
        lines.append(f"    html_path: {_yaml_quote(html_path)}")
    return "\n".join(lines) + "\n"


def build_indexes(
    *,
    proposals_root: Path,
    audit_proposals_root: Path | None,
    out_stakeholders: Path,
    out_dev: Path,
) -> None:
    if not proposals_root.exists() or not proposals_root.is_dir():
        scp_dirs = []
    else:
        scp_dirs = [
            p
            for p in proposals_root.iterdir()
            if p.is_dir() and _SCP_DIR_RE.match(p.name) and (p / "proposal.yaml").is_file()
        ]

    entries = [
        _parse_proposal_entry(scp_dir=d, audit_proposals_root=audit_proposals_root)
        for d in scp_dirs
    ]
    entries.sort(key=lambda e: e.scp_id)

    # Classification rule:
    # - If audit/proposals/<SCP>/ exists, treat as developer DAO (implementation artifacts).
    # - Otherwise treat as stakeholder DAO.
    dev: list[ProposalEntry] = []
    stakeholders: list[ProposalEntry] = []
    for e in entries:
        if audit_proposals_root is not None and (audit_proposals_root / e.scp_id).is_dir():
            dev.append(e)
        else:
            stakeholders.append(e)

    stakeholders_yaml = _render_index_yaml(
        proposals=stakeholders,
        html_base="site/dao_stakeholders/proposals",
    )
    dev_yaml = _render_index_yaml(
        proposals=dev,
        html_base="site/dao_dev/proposals",
    )

    _write_text_lf(out_stakeholders, stakeholders_yaml)
    _write_text_lf(out_dev, dev_yaml)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build deterministic DAO proposal indexes")
    parser.add_argument(
        "--proposals-root",
        default="proposals",
        help="Root folder containing SCP-* proposal directories (default: proposals)",
    )
    parser.add_argument(
        "--audit-proposals-root",
        default="audit/proposals",
        help=(
            "Optional root folder with audit decision/status hints (default: audit/proposals). "
            "If missing, dev index will be empty."
        ),
    )
    parser.add_argument(
        "--out-stakeholders",
        default="docs/dao/machine/dao_stakeholders/proposals_index.yaml",
        help="Output YAML path for stakeholders DAO proposals index",
    )
    parser.add_argument(
        "--out-dev",
        default="docs/dao/machine/dao_dev/proposals_index.yaml",
        help="Output YAML path for developers DAO proposals index",
    )

    args = parser.parse_args(argv)

    repo_root = _repo_root_from_this_file()
    proposals_root = (repo_root / args.proposals_root).resolve()
    audit_root = (repo_root / args.audit_proposals_root).resolve()
    audit_proposals_root = audit_root if audit_root.is_dir() else None

    out_stakeholders = (repo_root / args.out_stakeholders).resolve()
    out_dev = (repo_root / args.out_dev).resolve()

    build_indexes(
        proposals_root=proposals_root,
        audit_proposals_root=audit_proposals_root,
        out_stakeholders=out_stakeholders,
        out_dev=out_dev,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
