# Revision Prompt for Claude Code: Q1 Scheme B

你是 Math Magic 多 Agent 数学建模流程中的 Claude Code。Codex 已审查你完成的 Q1 方案 B，结论为 `REVISE`。请只修改 Q1-B，不要推进 Q2/Q3/Q4。

## 必须先读取

- `00_shared/WORKFLOW_PROTOCOL.md`
- `00_shared/PROJECT_STATE.md`
- `03_methods/Q1/scheme_B.md`
- `04_claude_workorders/Q1_scheme_B_workorder_001.md`
- `04_claude_workorders/completions/Q1_scheme_B_completion.md`
- `06_results/Q1/logs/scheme_B_codex_review.md`

## 返修目标

保持 Q1 方案 B 的建模路线不变：样条/GAM 思路、`SplineTransformer + Ridge`、GroupKFold、防止同一孕妇泄漏、输出偏效应和模型对比。

## 必须修改

1. 将 `MPLCONFIGDIR` 设置移动到 `import matplotlib` 之前，避免访问 `/Users/lwb/.matplotlib`。
2. 修复交叉验证泄漏：每个 GroupKFold fold 内只用训练集拟合样条基函数、交互项、标准化器和 Ridge 模型，再对测试集 transform/predict；线性基线也必须这样做。
3. alpha 选择不能混入同一孕妇记录。可在外层训练集内用按孕妇代码分组的内层验证，或手动网格搜索并清晰记录。
4. 修复 BMI 偏效应 bootstrap 置信带。当前 `scheme_B_partial_bmi.csv` 的 `ci_lo` 出现 -23，图不可用。优先按 `孕妇代码` 做 group bootstrap，并避免用重采样模型对全局 BMI 网格外推。
5. 将孕周清洗上限改为 25 周；如保留 26 周，必须额外输出 `<=25` 与 `<=26` 的敏感性对比表，并说明理由。
6. 增加 sanity check：预测值或置信带若出现明显不合理负值，日志必须报警，并且论文候选图不能使用异常置信带。
7. 重新生成所有 Q1-B 输出表格、图表、运行日志和完成报告。

## 输出要求

- 更新 `05_code/Q1/q1_scheme_B.py`
- 更新 `06_results/Q1/tables/scheme_B_*.csv`
- 更新 `06_results/Q1/figures/scheme_B_raw.png`
- 更新 `06_results/Q1/figures/scheme_B_residuals.png`
- 更新 `06_results/Q1/logs/scheme_B_run.md`
- 更新 `04_claude_workorders/completions/Q1_scheme_B_completion.md`

## 完成报告必须说明

- 已修复哪些 Codex 退回项。
- 修复后 CV-RMSE、CV-R2 与线性基线对比。
- BMI 和孕周偏效应置信带的数值范围。
- 是否仍存在负预测或异常置信带。
- 是否完全遵守 `03_methods/Q1/scheme_B.md`。
