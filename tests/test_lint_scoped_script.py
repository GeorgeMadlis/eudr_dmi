from __future__ import annotations

from types import SimpleNamespace


def test_lint_scoped_invokes_ruff_with_expected_paths_in_order(monkeypatch) -> None:
    from tools.ci import lint_scoped

    captured: dict[str, object] = {}

    def _fake_run(cmd, cwd=None, check=False):  # noqa: ANN001
        captured["cmd"] = cmd
        captured["cwd"] = cwd
        captured["check"] = check
        return SimpleNamespace(returncode=7)

    monkeypatch.setattr(lint_scoped.subprocess, "run", _fake_run)

    rc = lint_scoped.main([])
    assert rc == 7

    repo_root = lint_scoped._repo_root()
    expected_paths = lint_scoped._resolve_scoped_paths(repo_root)

    assert captured["check"] is False
    assert captured["cwd"] == str(repo_root)
    assert captured["cmd"] == ["python", "-m", "ruff", "check", *expected_paths]


def test_lint_scoped_missing_path_exits_2(monkeypatch) -> None:
    from tools.ci import lint_scoped

    monkeypatch.setattr(
        lint_scoped,
        "PATH_GROUPS",
        lint_scoped.PATH_GROUPS
        + (
            lint_scoped._PathGroup(
                "missing",
                ("this/path/does/not/exist.py",),
            ),
        ),
    )

    def _should_not_run(*_args, **_kwargs):  # noqa: ANN001
        raise AssertionError("subprocess.run should not be called")

    monkeypatch.setattr(lint_scoped.subprocess, "run", _should_not_run)

    assert lint_scoped.main([]) == 2
