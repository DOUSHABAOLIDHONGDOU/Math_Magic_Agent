"""Tests for Phase 2: rich Claude prompt with inlined context."""

from __future__ import annotations

import pytest


SCHEME_TEXT = """# Q1 Scheme B

## 基本信息

- 问题：Q1
- 方案：B
- 定位：竞赛均衡型

## 建模思路

用 Kalman filter 估计目标变量；建模均匀采样。

## 数学模型

| 符号 | 含义 | 单位 |
|---|---|---|
| x_t | 状态向量 | — |

核心公式：x_{t+1} = F x_t + B u_t

## 算法流程

1. 初始化
2. 预测
3. 更新

## 数据需求

| 数据 | 用途 | 是否已有 | 风险 |
|---|---|---|---|
| 传感器读数 | 观测 | 是 | 噪声大 |

## 预期输出

- metrics CSV
- 时序图

## 敏感性分析设计

| 参数 | 扰动 | 指标 | 影响 |
|---|---|---|---|

## 误差分析设计

- 模型误差
- 测量误差

## 优点

- 工程实现成熟

## 风险

- 状态空间假设较强

## Claude Code 实现提示

- 使用 numpy / scipy
- 固定 seed=42
"""

DATA_DICT_TEXT = """# Data Dictionary

- 数据目录：`01_problem/source/data`
- 扫描时间：2026-06-10T00:00:00

## 字段字典

| 文件 | 工作表 | 字段 | 类型 | 单位 | 含义 | 数据质量 |
|---|---|---|---|---|---|---|
| `01_problem/source/a.csv` | - | x | float64 | mm | 厚度 | sample_non_null=100 |
| `01_problem/source/a.csv` | - | y | float64 | mm | 误差 | sample_non_null=100 |
"""


def test_render_claude_prompt_inlines_scheme(minimal_state, isolated_project, scheme_template):
    from mm._workorder import create_workorder, render_claude_prompt

    (isolated_project / "03_methods" / "Q1").mkdir(parents=True, exist_ok=True)
    (isolated_project / "03_methods" / "Q1" / "scheme_B.md").write_text(SCHEME_TEXT, encoding="utf-8")
    (isolated_project / "01_problem" / "data_dictionary.md").write_text(DATA_DICT_TEXT, encoding="utf-8")
    workorder = create_workorder("Q1", "B")
    prompt = render_claude_prompt("Q1", "B", workorder)
    assert "数学模型" in prompt
    assert "x_{t+1} = F x_t + B u_t" in prompt
    assert "数据字典摘要" in prompt
    assert "厚度" in prompt  # data dict row inlined
    assert "执行边界" in prompt
    assert "完成报告必须包含" in prompt


def test_render_claude_prompt_errors_when_scheme_missing(minimal_state, isolated_project, scheme_template):
    from mm._workorder import render_claude_prompt

    with pytest.raises(SystemExit) as exc:
        render_claude_prompt("Q1", "B", isolated_project / "04_claude_workorders" / "fake.md")
    assert "scheme file not found" in str(exc.value)


def test_render_claude_prompt_warns_on_unfilled_dict(minimal_state, isolated_project, scheme_template):
    from mm._workorder import create_workorder, render_claude_prompt

    (isolated_project / "03_methods" / "Q1").mkdir(parents=True, exist_ok=True)
    (isolated_project / "03_methods" / "Q1" / "scheme_B.md").write_text(SCHEME_TEXT, encoding="utf-8")
    # Don't write data_dictionary.md; the warning path should trigger.
    workorder = create_workorder("Q1", "B")
    prompt = render_claude_prompt("Q1", "B", workorder)
    assert "数据字典还是占位模板" in prompt or "scan-data" in prompt


def test_estimate_prompt_tokens_is_positive(isolated_project):
    from mm._workorder import estimate_prompt_tokens

    assert estimate_prompt_tokens("hello world") > 0
    assert estimate_prompt_tokens("") == 1


def test_extract_scheme_sections_returns_requested_only(isolated_project, scheme_template):
    from mm._workorder import extract_scheme_sections

    path = isolated_project / "scheme.md"
    path.write_text(SCHEME_TEXT, encoding="utf-8")
    result = extract_scheme_sections(path, ["数学模型", "算法流程"])
    assert "## 数学模型" in result
    assert "## 算法流程" in result
    assert "## 误差分析设计" not in result
