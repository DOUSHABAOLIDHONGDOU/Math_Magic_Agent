# Claude Code Work Order

## 基本信息

- 工单 ID：Q1_B_001
- 相关问题：Q1
- 方案：B
- 创建方：Codex
- 执行方：Claude Code
- 状态：待执行

## 权限边界

你只负责代码实现、运行、调试和结果输出，不允许修改已批准建模路线。

如发现方案不可实现、数据不足、指标冲突或实现细节不确定，请写入 blocker 或边界问题，不要自行更换模型。

## 已批准建模路线

- 问题目标：执行 `Q1` 方案 `B`，严格服务题面中 `Q1` 的建模任务。
- 模型方法：建立广义加性模型思想的样条回归：对孕周和 BMI 使用样条基函数，对年龄、测序质量指标等使用线性项，并使用交叉验证选择复杂度。若本地没有专用 GAM 库，则用 `sklearn` 的 `SplineTransformer + Ridge/LinearRegression` 实现。 详见 `03_methods/Q1/scheme_B.md`。
- 输入数据：`01_problem/data_dictionary.md` 中登记的数据；本题当前数据源为 `01_problem/source/CUMCM2025Problems/C题/附件.xlsx`。
- 输出目标：- 表格：交叉验证误差、模型对比指标。 - 图：孕周偏效应曲线、BMI 偏效应曲线、二维热力图。 - 关键指标：非线性关系是否显著改善预测。
- 评价指标：按方案文件要求输出交叉验证误差、模型对比指标、非线性关系改进证据和可供 Codex 重绘的图表数据。
- 关键假设：同一孕妇重复检测需避免数据泄漏；孕周字符串需转换为连续周数；随机过程必须固定 seed。
- 禁止修改的边界：不允许更换 `03_methods/Q1/scheme_B.md` 中的样条/GAM 思路，不允许推进 Q2/Q3/Q4。

## 实现任务

1. 完成数据读取与清洗。
2. 实现本方案模型。
3. 固定随机种子，保证结果可复现。
4. 输出结果表格。
5. 输出基础图表或绘图数据。
6. 记录运行命令、参数和环境。

## 输入文件

- `01_problem/problem_statement.md`
- `01_problem/data_dictionary.md`
- `03_methods/Q1/scheme_B.md`

## 输出文件

- `06_results/Q1/tables/scheme_B_metrics.csv`
- `06_results/Q1/figures/scheme_B_raw.png`
- `06_results/Q1/logs/scheme_B_run.md`

## 运行要求

- 推荐语言：Python，除非用户另行批准。
- 所有脚本应能从项目根目录运行。
- 所有随机过程必须固定 seed。
- 不得硬编码只适用于单次运行的绝对路径。
- 结果文件必须覆盖写入或带有清晰版本号。
- 绘图脚本必须设置 `MPLCONFIGDIR=.cache/matplotlib` 或在 Python 中写入项目内缓存目录。

## 完成后必须报告

1. 修改了哪些文件。
2. 如何运行。
3. 关键结果。
4. 是否完全遵守建模路线。
5. 不确定边界问题。
6. 是否需要 Codex 或用户决策。
