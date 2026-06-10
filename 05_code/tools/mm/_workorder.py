"""Claude workorder + Claude prompt builders.

This module implements **Phase 2** of the agent improvement plan:
the Claude prompt now inlines the approved scheme sections, a data
dictionary digest, the paper style guide highlights, and any prior
revision blockers, so Claude does not need to chase down five files
before starting.

Backward compatibility: the prompt still lists the canonical file
paths so Claude can re-read them on demand, but the heavy lifting is
inlined.
"""

from __future__ import annotations

import re
from pathlib import Path

from ._briefs import compact_markdown_section, scheme_summary
from ._paths import PROJECT_ROOT
from ._util import read_text, rel, write_text


SCHEME_INLINE_SECTIONS = [
    "数学模型",
    "算法流程",
    "数据需求",
    "预期输出",
    "敏感性分析设计",
    "误差分析设计",
    "Claude Code 实现提示",
]

PROMPT_TOKEN_WARN_THRESHOLD = 80_000  # ~80k tokens, roughly the soft limit per turn


def estimate_prompt_tokens(text: str) -> int:
    """Rough token estimate: 1 token ≈ 3 chars for mixed CJK/English."""
    return max(1, len(text) // 3)


# ---------------------------------------------------------------------------
# Workorder creation (the template file under 04_claude_workorders/templates/)


def create_workorder(question: str, scheme: str, workorder_id: str | None = None, out: Path | None = None) -> Path:
    from ._state import load_state

    state = load_state()
    template_path = PROJECT_ROOT / "04_claude_workorders" / "templates" / "claude_workorder_template.md"
    template = read_text(template_path)
    workorder_id = workorder_id or f"{question}_{scheme}_001"
    out_path = out or PROJECT_ROOT / "04_claude_workorders" / f"{question}_scheme_{scheme}_workorder_001.md"
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    text = template
    text = text.replace("- 工单 ID：", f"- 工单 ID：{workorder_id}")
    text = text.replace("- 相关问题：Q1 / Q2 / Q3", f"- 相关问题：{question}")
    text = text.replace("- 相关问题：QX", f"- 相关问题：{question}")
    text = text.replace("- 方案：A / B / C", f"- 方案：{scheme}")
    text = text.replace("- 方案：X", f"- 方案：{scheme}")
    text = text.replace(
        "`06_results/QX/tables/scheme_X_metrics.csv`",
        f"`06_results/{question}/tables/scheme_{scheme}_metrics.csv`",
    )
    text = text.replace(
        "`06_results/QX/figures/scheme_X_raw.png`",
        f"`06_results/{question}/figures/scheme_{scheme}_raw.png`",
    )
    text = text.replace(
        "`06_results/QX/logs/scheme_X_run.md`",
        f"`06_results/{question}/logs/scheme_{scheme}_run.md`",
    )
    summary = scheme_summary(question, scheme)
    scheme_path = PROJECT_ROOT / "03_methods" / question / f"scheme_{scheme}.md"
    method_text = re.sub(r"\s+", " ", summary["idea"]).strip()
    output_text = re.sub(r"\s+", " ", summary["outputs"]).strip()
    data_dir = state.get("problem", {}).get("raw_data_dir") or "01_problem/source"
    data_dictionary = state.get("problem", {}).get("data_dictionary") or "01_problem/data_dictionary.md"
    text = text.replace(
        "- 问题目标：",
        f"- 问题目标：执行 `{question}` 方案 `{scheme}`，严格服务题面中 `{question}` 的建模任务。",
    )
    text = text.replace("- 模型方法：", f"- 模型方法：{method_text} 详见 `{rel(scheme_path)}`。")
    text = text.replace(
        "- 输入数据：",
        f"- 输入数据：`{data_dictionary}` 中登记的数据；本题当前数据源为 `{data_dir}`。",
    )
    text = text.replace("- 输出目标：", f"- 输出目标：{output_text}")
    text = text.replace(
        "- 评价指标：",
        "- 评价指标：按方案文件要求输出核心指标、可靠性/误差分析、可复查表格和可供 Codex 重绘的图表数据。",
    )
    text = text.replace(
        "- 关键假设：",
        "- 关键假设：严格采用已审批方案中的物理/统计假设；涉及随机过程必须固定 seed；所有单位转换必须在日志中说明。",
    )
    text = text.replace(
        "- 禁止修改的边界：",
        f"- 禁止修改的边界：不允许更换 `{rel(scheme_path)}` 中的建模路线，不允许推进未审批的后续问题。",
    )
    text = text.replace(
        "- 待填写。",
        f"- `01_problem/problem_statement.md`\n- `01_problem/data_dictionary.md`\n- `{rel(scheme_path)}`",
        1,
    )
    write_text(out_path, text)
    return out_path


# ---------------------------------------------------------------------------
# Phase 2: rich Claude prompt with inlined context


def extract_scheme_sections(scheme_path: Path, section_titles: list[str]) -> str:
    """Pull the named ``## title`` sections out of a method_scheme markdown file.

    Returns the requested sections concatenated as markdown, with ``## title``
    headers preserved. Missing sections are silently skipped; callers can detect
    an empty return and fall back to a placeholder.
    """
    if not scheme_path.exists():
        return ""
    try:
        text = scheme_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    chunks: list[str] = []
    for title in section_titles:
        marker = f"## {title}"
        start = text.find(marker)
        if start == -1:
            continue
        end = text.find("\n## ", start + len(marker))
        if end == -1:
            end = len(text)
        chunks.append(text[start:end].rstrip())
    return "\n\n".join(chunks).strip()


def summarize_data_dictionary(path: Path, max_fields: int = 30) -> str:
    """Return the first ``max_fields`` field rows of the data dictionary table, plus the data-dir line."""
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    header_lines: list[str] = []
    for line in text.splitlines()[:20]:
        if line.startswith("- 数据目录") or line.startswith("- 扫描时间"):
            header_lines.append(line)
    table_lines = [line for line in text.splitlines() if line.startswith("| ")]
    if not table_lines:
        return "\n".join(header_lines) if header_lines else ""
    # The first two table lines are the header and separator.
    body_rows = table_lines[2:] if len(table_lines) >= 2 else []
    chosen = body_rows[:max_fields]
    omitted = max(0, len(body_rows) - len(chosen))
    parts: list[str] = []
    if header_lines:
        parts.append("\n".join(header_lines))
    parts.append("\n".join(table_lines[:2] + chosen))
    if omitted:
        parts.append(f"_（已折叠 {omitted} 行字段，详见 `{rel(path)}`）_")
    return "\n\n".join(parts)


def style_guide_highlights(path: Path, max_lines: int = 60) -> str:
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    lines = text.splitlines()
    return "\n".join(lines[:max_lines]).strip()


def extract_revision_blockers(state: dict, question: str, scheme: str) -> str:
    """Look at the most recent completion report for blocker/risk callouts."""
    completion_path = PROJECT_ROOT / "04_claude_workorders" / "completions" / f"{question}_scheme_{scheme}_completion.md"
    if not completion_path.exists():
        return ""
    try:
        text = completion_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    sections = []
    for marker in ("blocker", "Blocker", "BLOCKER", "需要 Codex", "需要用户", "不确定", "返修"):
        idx = text.find(marker)
        if idx == -1:
            continue
        # Walk back to the surrounding `##` heading, then grab until the next one.
        head = text.rfind("\n## ", 0, idx)
        if head == -1:
            head = max(0, idx - 80)
        else:
            head += 1
        tail = text.find("\n## ", idx)
        if tail == -1:
            tail = min(len(text), idx + 600)
        sections.append(text[head:tail].strip())
    if not sections:
        return ""
    # Dedupe and cap length.
    seen = set()
    deduped: list[str] = []
    for section in sections:
        key = section[:200]
        if key in seen:
            continue
        seen.add(key)
        deduped.append(section)
    return "\n\n".join(deduped)[:3000]


def render_claude_prompt(question: str, scheme: str, workorder_path: Path) -> str:
    """Build the rich Claude execution prompt for one (question, scheme) pair."""
    from ._state import load_state

    state = load_state()
    scheme_path = PROJECT_ROOT / "03_methods" / question / f"scheme_{scheme}.md"
    completion_path = PROJECT_ROOT / "04_claude_workorders" / "completions" / f"{question}_scheme_{scheme}_completion.md"
    data_dict_path = PROJECT_ROOT / (state.get("problem", {}).get("data_dictionary") or "01_problem/data_dictionary.md")
    style_path = PROJECT_ROOT / "02_references" / "paper_style_guide.md"

    if not scheme_path.exists():
        raise SystemExit(
            f"scheme file not found: {rel(scheme_path)}. Run `prepare-schemes --question {question}` and "
            "have Codex write the scheme content first."
        )

    inline_scheme = extract_scheme_sections(scheme_path, SCHEME_INLINE_SECTIONS)
    if not inline_scheme:
        inline_scheme = scheme_path.read_text(encoding="utf-8").strip()
    # A freshly-prepared scheme is full of "待填写" placeholder rows. Dispatching
    # such a prompt to Claude wastes a turn — fail loudly with a hint.
    placeholder_marker_count = inline_scheme.count("待填写") + inline_scheme.count("待 Codex 补充")
    if placeholder_marker_count >= 5:
        raise SystemExit(
            f"{rel(scheme_path)} still looks like a blank template "
            f"({placeholder_marker_count} placeholder markers). Have Codex fill in 数学模型 / 数据需求 / "
            "预期输出 / 实现提示 first, then re-run create-claude-prompt."
        )

    inline_data = summarize_data_dictionary(data_dict_path, max_fields=30)
    inline_style = style_guide_highlights(style_path, max_lines=60)
    inline_revision = extract_revision_blockers(state, question, scheme)

    data_warning = ""
    if not inline_data:
        data_warning = (
            "\n\n> ⚠️ 数据字典还是占位模板。请先运行 "
            "`python 05_code/tools/agentctl.py scan-data --data-dir <你的数据目录>`，"
            "再回头执行本任务。\n"
        )

    parts: list[str] = []
    parts.append(f"# Prompt for Claude Code: {question} Scheme {scheme}\n")
    parts.append(
        f"你是 Math Magic 多 Agent 数学建模流程中的 Claude Code。请只执行本轮被用户批准的 `{question}` 方案 `{scheme}`，"
        "不要推进其他问题。所有关键上下文已经在下面内联，先读完本提示，再去打开任何外部文件。\n"
    )

    parts.append("## 必读路径（如需重读原文）\n")
    parts.append(
        "\n".join(
            [
                "- `00_shared/WORKFLOW_PROTOCOL.md`",
                "- `00_shared/PROJECT_STATE.md`",
                "- `00_shared/QUESTION_BOUNDARIES.md`",
                "- `01_problem/problem_statement.md`",
                f"- `{rel(data_dict_path)}`",
                f"- `{rel(scheme_path)}`",
                f"- `{rel(workorder_path)}`",
            ]
        )
    )
    parts.append("")

    parts.append(f"## 已批准建模路线（来自 `{rel(scheme_path)}`）\n")
    parts.append(inline_scheme if inline_scheme else "_未能解析方案 section；请打开方案文件原文_")
    parts.append("")

    parts.append("## 数据字典摘要\n")
    parts.append(inline_data if inline_data else "_数据字典暂未填充，详情见警告_")
    if data_warning:
        parts.append(data_warning)
    parts.append("")

    if inline_style:
        parts.append("## 优秀论文风格约束（节选）\n")
        parts.append(inline_style)
        parts.append("")

    if inline_revision:
        parts.append("## 上轮 blocker / 需要复核的边界\n")
        parts.append(inline_revision)
        parts.append("")

    parts.append("## 执行边界\n")
    parts.append(
        "\n".join(
            [
                "- 你只负责代码实现、运行、调试和结果输出。",
                f"- 不允许修改 `{rel(scheme_path)}` 中的建模路线。",
                "- 不允许修改 `03_methods/**/approved.md`、`00_shared/DECISION_LOG.md` 或论文最终结论。",
                "- 如果发现方案不可实现、字段缺失、指标冲突或边界不确定，请写入完成报告的 blocker 区，不要自行换模型。",
                f"- 当前只执行 `{question}`，不要生成或运行其他问题的代码。",
            ]
        )
    )
    parts.append("")

    parts.append("## 任务\n")
    parts.append(
        "\n".join(
            [
                "1. 在 `05_code/` 下创建或修改可复现脚本。",
                "2. 从项目根目录运行脚本，固定随机种子。",
                f"3. 按工单输出表格、基础图表或绘图数据到 `06_results/{question}/`。",
                "4. 记录完整运行命令、依赖、输入文件、输出文件和关键结果。",
                f"5. 完成后写 Markdown 报告到 `{rel(completion_path)}`。",
            ]
        )
    )
    parts.append("")

    parts.append("## 完成报告必须包含\n")
    parts.append(
        "\n".join(
            [
                "- 修改文件清单。",
                "- 运行命令。",
                "- 核心结果表和图的路径。",
                f"- 是否完全遵守 `{question}` 方案 `{scheme}`。",
                "- blocker 或需要 Codex/用户决策的问题。",
                "- 可供 Codex 审查的结论摘要。",
            ]
        )
    )
    parts.append("")

    prompt = "\n".join(parts)
    estimated = estimate_prompt_tokens(prompt)
    if estimated > PROMPT_TOKEN_WARN_THRESHOLD:
        prompt = (
            f"<!-- WARNING: estimated ~{estimated} tokens; consider reducing data dictionary or scheme detail. -->\n"
            + prompt
        )
    return prompt
