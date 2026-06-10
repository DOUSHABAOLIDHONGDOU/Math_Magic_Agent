"""Scheme / approval / model-confirmation brief renderers."""

from __future__ import annotations

import csv
import re
from pathlib import Path

from ._paths import PROJECT_ROOT, SCHEMES
from ._state import previous_question
from ._util import extract_section


def scheme_position(scheme: str) -> str:
    return {"A": "稳健解释型", "B": "竞赛均衡型", "C": "冲奖增强型"}[scheme]


def render_scheme_generation_prompt(question: str) -> str:
    from ._state import load_state

    state = load_state()
    prev = previous_question(state, question)
    previous_context = (
        f"""
前置问题依赖：

- `{question}` 必须读取 `{prev}` 的已确认模型、Codex 审查和结果文件。
- 重点读取 `03_methods/{prev}/approved.md`、`06_results/{prev}/` 和相关完成报告。
- 若 `{question}` 已存在历史预分析方案，只能作为草稿参考，必须根据 `{prev}` 的最终结果重审或重写。
"""
        if prev
        else "前置问题依赖：无，本问是当前题目的第一问。"
    )

    eda_block = ""
    eda_summary_path = PROJECT_ROOT / "06_results" / question / "eda" / "eda_summary.md"
    if eda_summary_path.exists():
        try:
            eda_text = eda_summary_path.read_text(encoding="utf-8")
        except OSError:
            eda_text = ""
        if eda_text:
            eda_block = "\n\n## 自动 EDA 摘要（auto-eda 已生成）\n\n" + eda_text.strip() + "\n"

    rag_block = ""
    rag_brief_path = PROJECT_ROOT / "02_references" / "rag_context" / f"{question}_top_passages.md"
    if rag_brief_path.exists():
        try:
            rag_text = rag_brief_path.read_text(encoding="utf-8")
        except OSError:
            rag_text = ""
        if rag_text:
            rag_block = "\n\n## 参考优秀论文片段（BM25 检索）\n\n" + rag_text.strip() + "\n"

    return f"""# Codex Scheme Generation Prompt: {question}

你是数学建模多 Agent 系统中的 Codex Agent。请读取：

- `00_shared/WORKFLOW_PROTOCOL.md`
- `00_shared/PROJECT_STATE.md`
- `01_problem/problem_statement.md`
- `01_problem/data_dictionary.md`
- `02_references/paper_style_guide.md`
- `02_references/scoring_rubric.md`
- `03_methods/method_scheme_template.md`

{previous_context}

任务：为 `{question}` 生成 A/B/C 三套可执行方案，并分别写入：

- `03_methods/{question}/scheme_A.md`
- `03_methods/{question}/scheme_B.md`
- `03_methods/{question}/scheme_C.md`

硬性要求：

1. A/B/C 必须有实质差异，不得只是换算法名。
2. 每套方案都要包含数学模型、数据需求、预期图表、敏感性分析、误差分析、实现风险和 Claude Code 实现提示。
3. 推荐 Python，但最终语言以用户审批为准。
4. 不得直接确认最终模型，必须等待用户审批。
5. 如题目信息不足，将边界问题写入 `00_shared/QUESTION_BOUNDARIES.md`。
{eda_block}{rag_block}"""


def render_approval_brief(state: dict, question: str) -> str:
    prev = previous_question(state, question)
    dependency_note = (
        f"- 前置依赖：需等待 `{prev}` 模型确认后再生成或修订本问方案。"
        if prev
        else "- 前置依赖：无，本问是当前题目的第一问。"
    )
    rows = []
    details = []
    for scheme in SCHEMES:
        summary = scheme_summary(question, scheme)
        rows.append(
            f"| {scheme} | {summary['position']} | {summary['idea_one_line']} | {summary['pros_one_line']} | {summary['risks_one_line']} |"
        )
        details.extend(
            [
                f"### 方案 {scheme}：{summary['position']}",
                "",
                "**建模思路**",
                "",
                summary["idea"],
                "",
                "**预期输出**",
                "",
                summary["outputs"],
                "",
                "**优点**",
                "",
                summary["pros"],
                "",
                "**风险**",
                "",
                summary["risks"],
                "",
            ]
        )
    return "\n".join(
        [
            f"# {question} 三方案审批简报",
            "",
            "## 当前审批对象",
            "",
            f"- 当前只审批 `{question}`，后续问题暂不进入 Claude Code 执行。",
            dependency_note,
            "- 用户可以选择 A/B/C 中一个方案执行，也可以明确多选；未选方案会保留为备选但不生成 Claude Code 工单。",
            "- 用户确认后，Codex 会生成一段可直接发给 Claude Code 的执行提示词。",
            "",
            "## 三套方案一览",
            "",
            "| 方案 | 定位 | 核心思路 | 主要价值 | 主要风险 |",
            "|---|---|---|---|---|",
            *rows,
            "",
            "## 方案详情",
            "",
            *details,
            "## Codex 初步建议",
            "",
            "- 若用户没有额外偏好，优先考虑 B 方案作为主力竞赛方案。",
            "- A 方案适合作为解释性基准；C 方案适合作为风险、阈值或鲁棒性补强。",
            "- 最终以用户审批为准，Codex 不在此阶段替用户锁定最终模型。",
            "",
            "## 用户回复模板",
            "",
            "```text",
            f"选择 {question} 方案 B。理由：主力方案，先交给 Claude Code 执行。",
            "```",
            "",
            "或：",
            "",
            "```text",
            f"选择 {question} 方案 A,C。理由：先跑解释基准和风险补强。",
            "```",
            "",
        ]
    )


def render_model_confirmation_brief(state: dict, question: str, scheme: str) -> str:
    qstate = state["questions"][question]
    scheme_state = qstate["schemes"][scheme]
    review_path = scheme_state.get("review") or f"06_results/{question}/logs/scheme_{scheme}_codex_review.md"
    completion_path = scheme_state.get("completion_report") or f"04_claude_workorders/completions/{question}_scheme_{scheme}_completion.md"
    metric_lines = [
        f"- Codex 复审结论：`{scheme_state.get('review_result', '待审查')}`",
        f"- 完成报告：`{completion_path}`",
        f"- Codex 审查：`{review_path}`",
    ]
    metric_lines.extend(model_confirmation_metric_lines(question, scheme))
    paper_constraints = model_confirmation_paper_constraints(question, scheme)
    return "\n".join(
        [
            f"# {question} 模型确认审批简报",
            "",
            "## 当前审批对象",
            "",
            f"- 当前只审批 `{question}` 的最终模型是否确认。",
            f"- 候选模型：方案 `{scheme}`。",
            "- 模型确认后，后续问题才允许正式推进；但图表审批和论文入文仍需单独审批。",
            "",
            "## 复审摘要",
            "",
            *metric_lines,
            "",
            "## 审批选项",
            "",
            "| 选项 | 结论 | 适用情况 | 后续动作 |",
            "|---|---|---|---|",
            f"| 1 | 标准批准 `{question}-{scheme}` | 你接受当前模型和结果，可直接作为本问最终模型 | Codex 记录模型确认，进入中文最终图生成与图表审批 |",
            f"| 2 | 带论文约束批准 `{question}-{scheme}`（推荐） | 你接受模型，但要求论文中明确关键假设、误差来源和适用边界 | Codex 记录模型确认，并把注意事项写入 `approved.md` 和后续论文小节 |",
            "| 3 | 不批准，返修或重跑备选方案 | 你不接受当前模型，认为还需修正、补强或尝试其他方案 | Codex 生成返修要求或重新给出备选方案审批 |",
            "",
            "## 选项 2 的论文约束",
            "",
            *paper_constraints,
            "",
            "## Codex 建议",
            "",
            f"- 建议选择 **选项 2**：`{question}-{scheme}` 已通过复审，可以作为本问最终模型；但论文中必须同步写清假设、误差和适用边界。",
            "- 选择选项 2 后，下一步不是直接写论文，而是由 Codex 生成中文最终图，再进入图表审批。",
            "",
            "## 你可以这样回复",
            "",
            "```text",
            f"模型确认选择 {question} 选项 2。理由：接受方案 {scheme} 作为最终模型，但论文中需写清模型假设、误差来源和适用边界。",
            "```",
            "",
            "或：",
            "",
            "```text",
            f"模型确认选择 {question} 选项 3。理由：我不满意当前模型，需要 Codex 重新生成返修方案。",
            "```",
            "",
        ]
    )


def model_confirmation_metric_lines(question: str, scheme: str) -> list[str]:
    metrics = read_metrics_summary(question, scheme)
    if not metrics:
        return ["- 核心指标：未发现结构化指标表，请以完成报告和 Codex 复审为准。"]
    preferred = [
        "n_samples_total_rows",
        "n_files",
        "model",
        "random_seed",
        "r2",
        "rmse",
        "mae",
        "cv_rmse",
        "cv_r2",
    ]
    lines = []
    for key in preferred:
        value = metrics.get(key)
        if value not in (None, ""):
            lines.append(f"- {key}：{value}")
    if lines:
        return lines[:8]
    return [f"- {key}：{value}" for key, value in list(metrics.items())[:8] if value not in (None, "")]


def model_confirmation_paper_constraints(question: str, scheme: str) -> list[str]:
    return [
        "- 论文中必须列出模型假设、参数来源、数据清洗边界和不确定性来源。",
        "- 不得把当前结果夸大为超出题目范围或数据支持范围的结论。",
    ]


def read_metrics_summary(question: str, scheme: str) -> dict[str, str]:
    path = PROJECT_ROOT / "06_results" / question / "tables" / f"scheme_{scheme}_metrics.csv"
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else {}


def scheme_summary(question: str, scheme: str) -> dict[str, str]:
    path = PROJECT_ROOT / "03_methods" / question / f"scheme_{scheme}.md"
    text = path.read_text(encoding="utf-8") if path.exists() else ""
    position = find_metadata(text, "定位") or scheme_position(scheme)
    idea = compact_markdown_section(text, "建模思路")
    outputs = compact_markdown_section(text, "预期输出")
    pros = compact_markdown_section(text, "优点")
    risks = compact_markdown_section(text, "风险")
    return {
        "position": position,
        "idea": idea,
        "outputs": outputs,
        "pros": pros,
        "risks": risks,
        "idea_one_line": first_sentence(idea),
        "pros_one_line": first_sentence(pros),
        "risks_one_line": first_sentence(risks),
    }


def find_metadata(text: str, key: str) -> str:
    match = re.search(rf"^- {re.escape(key)}：(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else ""


def compact_markdown_section(text: str, title: str, max_lines: int = 8) -> str:
    section = extract_section(text, title)
    if section.startswith(f"## {title}\n未找到") or section == f"## {title}\n未找到。":
        return "待补充。"
    lines = section.splitlines()[1:]
    cleaned = [line.rstrip() for line in lines if line.strip()]
    return "\n".join(cleaned[:max_lines]) if cleaned else "待补充。"


def first_sentence(text: str, max_len: int = 48) -> str:
    plain = re.sub(r"[*`$|#>-]", "", text)
    plain = re.sub(r"\s+", " ", plain).strip()
    for sep in ["。", "；", ";", "."]:
        if sep in plain:
            plain = plain.split(sep)[0]
            break
    if len(plain) > max_len:
        plain = plain[: max_len - 1] + "…"
    return plain or "待补充"


def render_codex_review_template(question: str, scheme: str, report: str) -> str:
    from ._util import today

    return f"""# Codex Review: {question} Scheme {scheme}

## 基本信息

- 问题：{question}
- 方案：{scheme}
- Claude 完成报告：`{report}`
- 审查日期：{today()}
- 审查结论：PASS / REVISE / BLOCKED

## 路线一致性

- 是否严格遵守 `03_methods/{question}/scheme_{scheme}.md`：
- 是否偏离已审批边界：
- 是否需要用户仲裁：

## 代码审查

- 可复现性：
- 随机种子：
- 路径处理：
- 数据清洗：
- 异常处理：

## 结果审查

- 输出表格：
- 输出图表：
- 核心指标：
- 是否支持题目结论：

## 数模论文补强

- 敏感性分析：
- 误差分析：
- 鲁棒性检验：
- 对比基准：

## 退回 Claude Code 的修改项

1. 待填写。

## 可进入论文的材料

- 表格：
- 图：
- 文字结论：
"""
