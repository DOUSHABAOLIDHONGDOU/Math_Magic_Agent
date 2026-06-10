"""Pytest fixtures for the mm package tests.

These tests must not touch the real project state, so we monkey-patch the
``PROJECT_ROOT`` / ``STATE_PATH`` / ``LOCK_PATH`` constants to point at a
per-test ``tmp_path`` before any test runs.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add the parent directory (which contains the ``mm`` package) to sys.path.
TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))


@pytest.fixture
def isolated_project(tmp_path, monkeypatch):
    """Point PROJECT_ROOT / STATE_PATH / LOCK_PATH at a temp dir for the duration of one test."""
    from mm import _paths, _state, _util

    project_root = tmp_path
    state_path = project_root / "00_shared" / "workflow_state.json"
    lock_path = project_root / "00_shared" / ".workflow_state.lock"
    (project_root / "00_shared").mkdir(parents=True, exist_ok=True)
    (project_root / "01_problem").mkdir(parents=True, exist_ok=True)
    (project_root / "03_methods").mkdir(parents=True, exist_ok=True)
    (project_root / "04_claude_workorders" / "templates").mkdir(parents=True, exist_ok=True)
    (project_root / "06_results").mkdir(parents=True, exist_ok=True)
    (project_root / "07_paper" / "sections").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(_paths, "PROJECT_ROOT", project_root)
    monkeypatch.setattr(_paths, "STATE_PATH", state_path)
    monkeypatch.setattr(_paths, "LOCK_PATH", lock_path)
    # Helper modules cache PROJECT_ROOT at import time; patch their copies too.
    for mod_name in (
        "mm._state",
        "mm._util",
        "mm._archive",
        "mm._briefs",
        "mm._workorder",
        "mm._paper",
        "mm._review",
        "mm._dispatch",
        "mm._env",
        "mm._commands",
        "mm._eda",
        "mm._rag",
        "mm._figure_lint",
        "mm._project_state",
    ):
        if mod_name in sys.modules:
            module = sys.modules[mod_name]
            if hasattr(module, "PROJECT_ROOT"):
                monkeypatch.setattr(module, "PROJECT_ROOT", project_root)
            if hasattr(module, "STATE_PATH"):
                monkeypatch.setattr(module, "STATE_PATH", state_path)
            if hasattr(module, "LOCK_PATH"):
                monkeypatch.setattr(module, "LOCK_PATH", lock_path)
    yield project_root


@pytest.fixture
def minimal_state(isolated_project):
    """A fully initialised workflow state stored in the isolated project."""
    from mm._state import default_state, save_state

    state = default_state()
    state["problem"]["title"] = "Test Problem"
    state["problem"]["question_ids"] = ["Q1", "Q2"]
    state["language"]["approved"] = True
    state["language"]["decision_id"] = "D-001"
    save_state(state, snapshot=False)
    return state


@pytest.fixture
def scheme_template(isolated_project):
    """Drop a minimal method_scheme_template.md into the temp project so workorder
    creation can find it."""
    template = """# Method Scheme Template

## 基本信息

- 问题：QX
- 方案：X
- 定位：稳健解释型 / 竞赛均衡型 / 冲奖增强型
- 状态：待审批 / 已审批 / 已实现 / 已淘汰

## 建模思路

待 Codex 补充建模思路。

## 数学模型

| 符号 | 含义 | 单位 |
|---|---|---|

核心公式：待补充。

## 算法流程

1. 步骤一
2. 步骤二

## 数据需求

| 数据 | 用途 | 是否已有 | 风险 |
|---|---|---|---|

## 预期输出

- 输出 A
- 输出 B

## 敏感性分析设计

| 参数 | 扰动 | 指标 | 影响 |
|---|---|---|---|

## 误差分析设计

- 数据误差
- 模型误差

## 优点

- 解释性强

## 风险

- 数据量不足

## Claude Code 实现提示

- 用 numpy + scipy

## Codex 审批意见

- 待 Codex 填写

## 用户审批

- 是否批准运行：否
"""
    (isolated_project / "03_methods" / "method_scheme_template.md").write_text(template, encoding="utf-8")
    workorder_template = """# Claude Code Work Order

## 基本信息

- 工单 ID：
- 相关问题：QX
- 方案：X
- 创建方：Codex

## 权限边界

你只负责代码实现。

## 已批准建模路线

- 问题目标：
- 模型方法：
- 输入数据：
- 输出目标：
- 评价指标：
- 关键假设：
- 禁止修改的边界：

## 输入文件

- 待填写。

## 输出文件

- `06_results/QX/tables/scheme_X_metrics.csv`
- `06_results/QX/figures/scheme_X_raw.png`
- `06_results/QX/logs/scheme_X_run.md`
"""
    (isolated_project / "04_claude_workorders" / "templates" / "claude_workorder_template.md").write_text(
        workorder_template, encoding="utf-8"
    )
    return isolated_project
