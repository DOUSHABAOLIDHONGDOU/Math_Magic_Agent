"""Tests for paper helpers — layout assertion, label parsing, latex constants."""

from __future__ import annotations

import pytest


def test_parse_label_expectations_simple(isolated_project):
    from mm._paper import parse_label_expectations

    parsed = parse_label_expectations(["fig:q1_surface=5", "tab:results=7"])
    assert parsed == {"fig:q1_surface": 5, "tab:results": 7}


def test_parse_label_expectations_rejects_bad_format(isolated_project):
    from mm._paper import parse_label_expectations

    with pytest.raises(SystemExit):
        parse_label_expectations(["nopage"])
    with pytest.raises(SystemExit):
        parse_label_expectations(["fig=abc"])


def test_parse_aux_label_pages(isolated_project, tmp_path):
    from mm._paper import parse_aux_label_pages

    aux = tmp_path / "main.aux"
    aux.write_text(
        r"""\newlabel{fig:q1_surface}{{1}{5}{Foo}{fig.1}{}}
\newlabel{tab:results}{{2}{7}{Bar}{table.1}{}}
""",
        encoding="utf-8",
    )
    pages = parse_aux_label_pages(aux)
    assert pages == {"fig:q1_surface": 5, "tab:results": 7}


def test_assert_layout_ok_exits_on_issues(isolated_project, capsys):
    from mm._paper import _assert_layout_ok

    with pytest.raises(SystemExit):
        _assert_layout_ok(["page 3: gap 30%"])
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


def test_assert_layout_ok_prints_ok_when_clean(isolated_project, capsys):
    from mm._paper import _assert_layout_ok

    _assert_layout_ok([])  # should not raise
    captured = capsys.readouterr()
    assert "ok" in captured.out


def test_run_layout_check_handles_missing_pdf(isolated_project):
    from mm._paper import run_layout_check

    fake_pdf = isolated_project / "missing.pdf"
    fake_aux = isolated_project / "missing.aux"
    with pytest.raises(SystemExit):
        run_layout_check(
            pdf_path=fake_pdf,
            aux_path=fake_aux,
            max_internal_gap_ratio=0.24,
            label_expectations=[],
        )
