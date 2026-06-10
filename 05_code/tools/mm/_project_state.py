"""Render the human-readable PROJECT_STATE.md from the workflow state dict.

Registered via ``_state.save_state`` through ``globals().get(...)`` so the
write-back path stays cycle-free.
"""

from __future__ import annotations

from ._paths import PROJECT_ROOT
from ._util import write_text


def project_question_task_summary(qstate: dict) -> str:
    status = qstate.get("status", "not_started")
    confirmed = qstate.get("confirmed_scheme")
    if qstate.get("paper_written"):
        return "已写入论文"
    if status == "paper_compile_failed":
        return "单题已写入 LaTeX，但 PDF 编译或版面检查失败"
    if qstate.get("figures_approved"):
        return "图表已审批"
    if qstate.get("model_confirmed"):
        return f"模型已确认：方案 {confirmed}"
    if qstate.get("code_reviewed"):
        return "代码已由 Codex 复审通过，等待模型确认"
    if qstate.get("code_completed"):
        return "Claude Code 已完成实现，等待 Codex 复审"
    if qstate.get("workorders_created"):
        return "Claude Code 工单已创建"
    if qstate.get("schemes_approved"):
        return "方案已审批，等待创建/执行 Claude 工单"
    if qstate.get("schemes_generated"):
        return "方案已生成，等待审批"
    if status == "inactive":
        return "不在当前题目范围"
    return "待方案生成/审批"


def project_approval_label(done: bool, detail: str = "") -> str:
    if done:
        return f"已完成{(': ' + detail) if detail else ''}"
    return "未完成"


def update_project_state_summary(state: dict, *, note: str = "") -> None:
    question_ids = state["problem"].get("question_ids") or []
    question_rows = []
    approval_rows = []
    for question in question_ids:
        qstate = state["questions"].get(question, {})
        confirmed = qstate.get("confirmed_scheme") or ""
        question_rows.append(
            "| {question} | {summary} | 见方案/结果目录 | {status} |".format(
                question=question,
                summary=project_question_task_summary(qstate),
                status=qstate.get("status", "not_started"),
            )
        )
        approval_rows.append(
            "| {question} | {scheme} | {model} | {figures} | {paper} |".format(
                question=question,
                scheme=project_approval_label(
                    bool(qstate.get("schemes_approved")),
                    qstate.get("scheme_decision_id") or "",
                ),
                model=project_approval_label(
                    bool(qstate.get("model_confirmed")),
                    f"方案 {confirmed}" if confirmed else "",
                ),
                figures=project_approval_label(
                    bool(qstate.get("figures_approved")),
                    qstate.get("figure_decision_id") or "",
                ),
                paper=project_approval_label(
                    bool(qstate.get("paper_written")),
                    qstate.get("paper_section") or "",
                ),
            )
        )
    if not question_rows:
        question_rows.append("| 待定 | 待导入 | 待确认 | not_started |")
    if not approval_rows:
        approval_rows.append("| 待定 | 未完成 | 未完成 | 未完成 | 未完成 |")

    data_dir = state["problem"].get("raw_data_dir") or "待扫描"
    data_dictionary = state["problem"].get("data_dictionary") or "待扫描"
    current_question = state.get("current_question") or "待定"
    qstate = state["questions"].get(current_question, {}) if current_question in state.get("questions", {}) else {}
    language = state.get("language", {})
    approval = "是" if language.get("approved") else "否"
    decision = language.get("decision_id") or "待确认"
    trust_profile = state.get("trust_profile", "strict")
    extra = f"\n- 备注：{note}" if note else ""
    current_status = project_question_task_summary(qstate) if qstate else "待导入题目"
    text = f"""# Project State

## 当前阶段

- 阶段：{state['stage']}
- 当前负责人：Codex
- 当前问题：{current_question}
- 当前状态：{current_status}
- 信任配置：{trust_profile}
- 题目：`{state['problem'].get('title') or '题目名称待定'}`{extra}

## 题目与任务

| 问题 | 任务摘要 | 输出要求 | 状态 |
|---|---|---|---|
{chr(10).join(question_rows)}

## 数据情况

| 文件/目录 | 字段 | 说明 | 数据质量 | 状态 |
|---|---|---|---|---|
| `{data_dir}` | 见 `{data_dictionary}` | 当前导入题目的原始数据目录 | 建模脚本已可进一步清洗/验证 | 可用 |

## 全局技术路线

- 推荐语言：{language.get('recommended', 'Python')}
- 是否已由用户批准：{approval}，决策 ID `{decision}`
- LaTeX 风格：中文 CUMCM / 中国数模国赛论文风格
- 工作流推进方式：逐问推进，当前问题入文、编译和版面检查通过后才解锁下一问
- 信任配置：`{trust_profile}`（strict=训练严格；normal=演练；fast=赛时快速通道）
- 机器状态文件：`00_shared/workflow_state.json`
- 命令式流程文档：`08_agent_design/WORKFLOW_COMMANDS.md`
- 依赖安装入口：`environment.yml`, `requirements.txt`, `INSTALL.md`
- 工具注册表：`05_code/tools/tool_registry.json`, `08_agent_design/TOOL_REGISTRY.md`
- 图表最终负责人：Codex
- 代码实现负责人：Claude Code

## 三次审批状态

| 问题 | 方案审批 | 模型确认 | 图表审批 | 论文写入 |
|---|---|---|---|---|
{chr(10).join(approval_rows)}
"""
    write_text(PROJECT_ROOT / "00_shared" / "PROJECT_STATE.md", text)


# Register with _state so save_state can invoke this without a hard import cycle.
def _install_into_state() -> None:
    from . import _state

    _state.__dict__["update_project_state_summary"] = update_project_state_summary


_install_into_state()
