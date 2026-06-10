# 多 Agent 数学建模工作流协议

## 目标

本项目用于赛前训练和后续 agent 开发。核心目标是跑通一套可复用流程：

- Codex 负责建模总控、方案设计、论文写作、图表生成与插入、代码审查和结果验收。
- Claude Code 负责代码生成、运行、调试、结果文件输出。
- 人类队伍负责审批、仲裁和最终取舍。

## 总体原则

1. 共享 Markdown 是项目状态机，不是闲聊记录。
2. Claude Code 可以写入结果、运行日志、不确定边界和 blocker，但不能修改已批准建模路线。
3. Codex 可以修改建模文档、论文 LaTeX、图表规范、审查意见和 Claude 工单。
4. 每个问题都必须经过三次审批：方案审批、模型确认、图表审批。
5. 默认逐问推进：只有当前问题完成模型确认、单题入文、PDF 编译和版面检查后，下一问才进入方案生成和审批。
6. 当前问题由 Codex 给出 A/B/C 三套方案，用户选择一个或多个方案后，Codex 再生成并调度给 Claude Code 的执行提示词。
7. 后续问题可以预读题面，但不能在前置问题确认前生成 Claude Code 工单或锁定建模路线。
8. 最终论文遵循中文 CUMCM/中国大学生数学建模竞赛论文风格。
9. 每完成一个问题的模型确认后，Codex 必须写入该问题对应 LaTeX 小节并立即编译一次 PDF；图表审批后再补入最终中文图并重新编译。
10. 摘要、整体问题分析、模型检验、模型评价与推广、论文 AI 使用说明等总结性内容必须等全部问题完成后再填写。
11. 最终入论文图必须为中文图；Claude Code 的英文图仅作为验收参考或重绘依据。
12. Codex 复审通过后，必须先生成模型确认审批简报，并在聊天中直接列出选项；只写入文件或只给文件路径不算完成审批告知。
13. 每次编译 PDF 后必须运行 `layout-check` 或 `latex-check` 的内置版面检查；明确页码要求必须写成 `--expect-label-page label=page`。
14. 代码推荐 Python，最终语言由用户审批确认。
15. 最终论文图不得出现图内底部长批注或红色虚线参考/阈值/边界线；条件说明放正文、图注或表格备注。
16. agent 交付优先适配 Windows + VS Code；新机器必须先运行 `doctor --target-os windows --write-vscode-smoke-task` 并在 VS Code 中完成 Claude smoke test。

## 每个问题的标准流程

以 QX 为例：

1. Codex 读题、读数据、读取优秀论文风格笔记。
2. Codex 生成 QX 的 A/B/C 三套方案，写入 `03_methods/QX/`。
3. Codex 生成 `03_methods/QX/approval_brief.md`，并在聊天中直接列出当前问题的 A/B/C 三套方案。
4. 用户选择 A/B/C 中一个或多个方案。
5. Codex 记录审批，并生成 `04_claude_workorders/QX_scheme_X_claude_prompt.md`。
6. Codex 使用 `dispatch-claude --mode auto` 打开可见 Claude Code 终端；若终端路线不可用，才使用后台 CLI 备用。
7. Claude Code 按提示词和工单实现、运行、调试，并输出结果。
8. Claude Code 写入完成报告、运行日志和不确定问题。
9. Codex 审查代码和结果。
10. 如用户批准多个方案，Codex 汇总方案对比；如只批准一个方案，Codex 审查该方案是否足以进入模型确认。
11. Codex 在聊天中直接列出模型确认选项，用户确认最终模型。
12. Codex 写入该问题对应 LaTeX 小节并立即编译 PDF，运行版面检查。
13. Codex 生成最终论文图表，用户审批后补入 LaTeX 并重新编译。
14. 当前问题 `paper_written=True` 后，下一问才解锁。
15. 全部问题入文后，Codex 再写摘要、全局分析、模型评价、代码附录和论文 AI 使用说明。

## 权限边界

### Codex 可以修改

- `00_shared/PROJECT_STATE.md`
- `00_shared/DECISION_LOG.md`
- `00_shared/AI_USAGE_LOG.md`
- `00_shared/CONFLICT_LOG.md`
- `00_shared/QUESTION_BOUNDARIES.md`
- `02_references/*.md`
- `03_methods/**/*.md`
- `04_claude_workorders/**/*.md`
- `06_results/**/figures/` 中的最终论文图
- `07_paper/**`
- `08_agent_design/**`

### Claude Code 可以修改

- `05_code/**`
- `06_results/**`
- `00_shared/PROJECT_STATE.md` 中的 Claude 状态区
- `00_shared/QUESTION_BOUNDARIES.md` 中的待确认问题区
- `00_shared/CONFLICT_LOG.md` 中的冲突报告区

### Claude Code 不允许修改

- 已审批的建模路线
- `03_methods/**/approved.md`
- 论文最终结论
- 图表最终审美与插入位置
- `DECISION_LOG.md` 中已确认的决策

## 冲突处理

当 Codex 和 Claude Code 对方法、实现或结果解释有不同意见时：

1. 双方只陈述事实、证据和风险。
2. 写入 `00_shared/CONFLICT_LOG.md`。
3. 人类队伍仲裁。
4. 仲裁结果写入 `00_shared/DECISION_LOG.md`。

## 图表生成规则

真实数据图必须基于实际数据和可复现脚本生成，不允许用生图替代真实数值图。

Codex 负责：

- 选择图表类型。
- 设计配色、布局、图题、注释。
- 生成或修改绘图脚本。
- 将最终图表插入 LaTeX。
- 对流程图、机制图、结构图、场景示意图使用生图能力或其他可视化工具辅助。
- 使用 imagegen skill 生成项目用图时，必须将最终资产保存到 `07_paper/figures/` 或对应结果目录。
- 最终论文图遵循“一图一主要结论”；`subfigure` 最多两张且必须服务同一比较结论。
- 普通数据图宽度控制在 `0.58\textwidth` 到 `0.70\textwidth`，复杂图不超过 `0.76\textwidth`；不得出现半页大图或整页堆图。
- 敏感性、误差和鲁棒性等多项结果优先写成表格摘要，再配一张关键单结论图。

Claude Code 负责：

- 生成可复现的数据结果。
- 输出基础图表数据。
- 输出初版绘图脚本。
- 记录运行环境和命令。

## AI 使用记录

每次使用 Codex 或 Claude Code 产生关键内容时，需要在 `AI_USAGE_LOG.md` 记录：

- 日期
- 工具
- 用途
- 输入摘要
- 输出摘要
- 是否采纳
- 人工修改说明
- 对应文件
