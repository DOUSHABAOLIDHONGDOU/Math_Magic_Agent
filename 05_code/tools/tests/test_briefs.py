"""Tests for the brief renderers and scheme summary helpers."""

from __future__ import annotations


def _seed_scheme(project, question, scheme, position="测试定位"):
    target = project / "03_methods" / question
    target.mkdir(parents=True, exist_ok=True)
    (target / f"scheme_{scheme}.md").write_text(
        f"""# {question} Scheme {scheme}

## 基本信息

- 问题：{question}
- 方案：{scheme}
- 定位：{position}

## 建模思路

这是一个测试方案，用于驱动单元测试。可执行的建模思路应被首句捕获作为 idea_one_line。

## 预期输出

- 表格 A
- 图 B

## 优点

- 解释性优秀

## 风险

- 数据量不足
""",
        encoding="utf-8",
    )


def test_scheme_summary_extracts_sections(minimal_state, isolated_project):
    from mm._briefs import scheme_summary

    _seed_scheme(isolated_project, "Q1", "B", "竞赛均衡型")
    summary = scheme_summary("Q1", "B")
    assert summary["position"] == "竞赛均衡型"
    assert "测试方案" in summary["idea"]
    assert "解释性优秀" in summary["pros"]
    assert summary["idea_one_line"].startswith("这是一个测试方案")


def test_render_approval_brief_lists_all_schemes(minimal_state, isolated_project):
    from mm._briefs import render_approval_brief
    from mm._state import load_state

    for scheme in ("A", "B", "C"):
        _seed_scheme(isolated_project, "Q1", scheme)
    state = load_state()
    text = render_approval_brief(state, "Q1")
    for scheme in ("A", "B", "C"):
        assert f"方案 {scheme}" in text
    assert "用户回复模板" in text


def test_render_scheme_generation_prompt_includes_eda_when_present(minimal_state, isolated_project):
    from mm._briefs import render_scheme_generation_prompt

    eda_dir = isolated_project / "06_results" / "Q1" / "eda"
    eda_dir.mkdir(parents=True, exist_ok=True)
    (eda_dir / "eda_summary.md").write_text("# EDA\n\n- 字段 X 缺失率 5%\n", encoding="utf-8")
    prompt = render_scheme_generation_prompt("Q1")
    assert "EDA 摘要" in prompt
    assert "字段 X 缺失率" in prompt


def test_render_scheme_generation_prompt_includes_rag_when_present(minimal_state, isolated_project):
    from mm._briefs import render_scheme_generation_prompt

    rag_dir = isolated_project / "02_references" / "rag_context"
    rag_dir.mkdir(parents=True, exist_ok=True)
    (rag_dir / "Q1_top_passages.md").write_text("# RAG\n\n## #1 score 7\n\n> 优秀论文片段示例\n", encoding="utf-8")
    prompt = render_scheme_generation_prompt("Q1")
    assert "BM25" in prompt
    assert "优秀论文片段示例" in prompt
