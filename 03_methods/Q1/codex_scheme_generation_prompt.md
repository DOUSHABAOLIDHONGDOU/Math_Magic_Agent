# Codex Scheme Generation Prompt: Q1

你是数学建模多 Agent 系统中的 Codex Agent。请读取：

- `00_shared/WORKFLOW_PROTOCOL.md`
- `00_shared/PROJECT_STATE.md`
- `01_problem/problem_statement.md`
- `01_problem/data_dictionary.md`
- `02_references/paper_style_guide.md`
- `02_references/scoring_rubric.md`
- `03_methods/method_scheme_template.md`

任务：为 `Q1` 生成 A/B/C 三套可执行方案，并分别写入：

- `03_methods/Q1/scheme_A.md`
- `03_methods/Q1/scheme_B.md`
- `03_methods/Q1/scheme_C.md`

硬性要求：

1. A/B/C 必须有实质差异，不得只是换算法名。
2. 每套方案都要包含数学模型、数据需求、预期图表、敏感性分析、误差分析、实现风险和 Claude Code 实现提示。
3. 推荐 Python，但最终语言以用户审批为准。
4. 不得直接确认最终模型，必须等待用户审批。
5. 如题目信息不足，将边界问题写入 `00_shared/QUESTION_BOUNDARIES.md`。
