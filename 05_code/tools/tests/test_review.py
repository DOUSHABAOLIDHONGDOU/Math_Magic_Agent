"""Tests for Phase 3b: data-driven scheme comparison."""

from __future__ import annotations


def _write_metrics(project, question, scheme, rows):
    tables_dir = project / "06_results" / question / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    path = tables_dir / f"scheme_{scheme}_metrics.csv"
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row[h]) for h in headers))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def test_load_metrics_for_question(minimal_state, isolated_project):
    from mm._review import load_metrics_for_question

    _write_metrics(isolated_project, "Q1", "A", [{"rmse": 1.5, "r2": 0.80}])
    _write_metrics(isolated_project, "Q1", "B", [{"rmse": 0.9, "r2": 0.92}])
    data = load_metrics_for_question("Q1")
    assert "A" in data and "B" in data
    assert data["B"]["rmse"] == "0.9"


def test_score_schemes_picks_winner_per_metric(minimal_state, isolated_project):
    from mm._review import load_metrics_for_question, score_schemes

    _write_metrics(isolated_project, "Q1", "A", [{"rmse": 1.5, "r2": 0.80}])
    _write_metrics(isolated_project, "Q1", "B", [{"rmse": 0.9, "r2": 0.92}])
    metrics = load_metrics_for_question("Q1")
    scored = score_schemes(metrics)
    # B should win both metrics: lower rmse and higher r2.
    assert scored["B"]["wins"] == 2
    assert scored["A"]["wins"] == 0


def test_render_scheme_comparison_marks_best(minimal_state, isolated_project):
    from mm._review import render_scheme_comparison
    from mm._state import load_state

    _write_metrics(isolated_project, "Q1", "A", [{"rmse": 1.5}])
    _write_metrics(isolated_project, "Q1", "B", [{"rmse": 0.9}])
    state = load_state()
    text = render_scheme_comparison(state, "Q1")
    assert "★" in text
    assert "推荐" in text


def test_render_scheme_comparison_empty_when_no_csv(minimal_state, isolated_project):
    from mm._review import render_scheme_comparison
    from mm._state import load_state

    state = load_state()
    text = render_scheme_comparison(state, "Q1")
    assert "未发现结构化指标表" in text
