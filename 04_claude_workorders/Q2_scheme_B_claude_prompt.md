# Prompt for Claude Code: Q2 Scheme B

你是 Math Magic 多 Agent 数学建模流程中的 Claude Code。请只执行本轮被用户批准的 `Q2` 方案 `B`，不要推进其他问题。

## 必须先读取

- `00_shared/WORKFLOW_PROTOCOL.md`
- `00_shared/PROJECT_STATE.md`
- `00_shared/QUESTION_BOUNDARIES.md`
- `01_problem/problem_statement.md`
- `01_problem/data_dictionary.md`
- `03_methods/Q2/scheme_B.md`
- `04_claude_workorders/Q2_scheme_B_workorder_001.md`
- `05_code/Q1/q1_scheme_B.py`
- `06_results/Q1/tables/scheme_B_metrics.csv`
- `07_paper/sections/model_q1.tex`

## 执行边界

- 你只负责代码实现、运行、调试和结果输出。
- 不允许修改 `03_methods/Q2/scheme_B.md` 中的建模路线。
- 必须承接 Q1 已确认模型结果，但不得改写 Q1 代码、Q1 结果或 Q1 论文结论。
- 不允许修改 `03_methods/**/approved.md`、`00_shared/DECISION_LOG.md` 或论文最终结论。
- 如果发现方案不可实现、字段缺失、指标冲突或边界不确定，请写入完成报告的 blocker 区，不要自行换模型。
- 当前只执行 `Q2`，不要生成或运行 Q3/Q4 的代码。

## 任务

1. 在 `05_code/` 下创建或修改可复现脚本。
2. 从项目根目录运行脚本，固定随机种子。
3. 按工单输出表格、基础图表或绘图数据到 `06_results/Q2/`。
4. 必须输出数据驱动分组、经验 BMI 分组基准对比、权重/组数/最小样本量敏感性分析。
5. 记录完整运行命令、依赖、输入文件、输出文件和关键结果。
6. 完成后写 Markdown 报告到 `04_claude_workorders/completions/Q2_scheme_B_completion.md`。

## 完成报告必须包含

- 修改文件清单。
- 运行命令。
- 核心结果表和图的路径。
- 是否完全遵守 `Q2` 方案 `B`。
- blocker 或需要 Codex/用户决策的问题。
- 可供 Codex 审查的结论摘要。
