# Claude Code Work Order

## 基本信息

- 工单 ID：Q2_B_001
- 相关问题：Q2
- 方案：B
- 创建方：Codex
- 执行方：Claude Code
- 状态：待执行

## 权限边界

你只负责代码实现、运行、调试和结果输出，不允许修改已批准建模路线。

如发现方案不可实现、数据不足、指标冲突或实现细节不确定，请写入 blocker 或边界问题，不要自行更换模型。

## 已批准建模路线

- 问题目标：执行 `Q2` 方案 `B`，严格服务题面中 `Q2` 的建模任务。
- 模型方法：将 BMI 分组视为一维最优分割问题。先基于 Q1 的非线性模型估计每名孕妇的达标时间，再用动态规划或 CART 风格的最优切分寻找 BMI 区间，使总潜在风险最小。 详见 `03_methods/Q2/scheme_B.md`。
- 输入数据：`01_problem/data_dictionary.md` 中登记的数据；本题当前数据源为 `01_problem/source/CUMCM2025Problems/C题/附件.xlsx`。
- 输出目标：- 表格：最优组数、BMI 边界、组内样本量、最佳时点、风险。 - 图：BMI 切分图、组内达标时间箱线图、误差扰动下边界稳定性图。
- 评价指标：输出总风险、各 BMI 组样本量、各组最佳 NIPT 时点、达标率/早检失败风险、晚检风险、分组边界稳定性和可供 Codex 重绘的图表数据。
- 关键假设：同一孕妇重复检测需避免数据泄漏；孕周字符串需转换为连续周数；随机过程必须固定 seed。
- 禁止修改的边界：不允许更换 `03_methods/Q2/scheme_B.md` 中的数据驱动 BMI 最优分组路线；不允许修改 Q1 已确认模型、Q1 结果或 Q1 论文结论；不允许推进 Q3/Q4。

## 必须承接的 Q1 结果

- Q1 最终模型：`Q1-B v2`，已由用户确认，决策 ID `D-006`。
- Q1 代码参考：`05_code/Q1/q1_scheme_B.py`。
- Q1 结果表：`06_results/Q1/tables/scheme_B_metrics.csv`、`scheme_B_partial_gestation.csv`、`scheme_B_partial_bmi.csv`、`scheme_B_heatmap_grid.csv`。
- Q1 论文小节：`07_paper/sections/model_q1.tex`。
- Q2 可以复用 Q1-B 的特征工程和已确认超参数（degree=3, n_knots=5, Ridge alpha 见 Q1 metrics），在 Q2 脚本内重新拟合用于达标时间估计；但这只是 Q2 的计算输入，不构成对 Q1 模型的重新审批或改写。

## Q2 实现细化要求

1. 以孕妇为基本单位估计达标时间。对每名孕妇，用其 BMI 和质控变量，在候选孕周网格上预测 Y 染色体浓度，取首次达到 4% 的孕周作为 $T_i^*$；若未达到，记录为右侧未达标并在风险中惩罚。
2. BMI 分组必须是一维有序切分，枚举 $K=3,4,5,6$，并设置最小组样本量敏感性：20、30、40。
3. 每组最佳 NIPT 时点必须通过显式风险函数选择。主结果应给出默认权重，并对早检失败权重、晚检风险权重和复杂度惩罚做敏感性分析。
4. 结果必须包含一个经验分组基准对比（可使用题面常见 BMI 区间 `[20,28),[28,32),[32,36),[36,40),[40,+∞)`），用于说明数据驱动分组是否更优。
5. 输出时点既给连续周数，也给便于论文表达的“周+天”格式。

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
- `03_methods/Q2/scheme_B.md`
- `05_code/Q1/q1_scheme_B.py`
- `06_results/Q1/tables/scheme_B_metrics.csv`
- `07_paper/sections/model_q1.tex`

## 输出文件

- `06_results/Q2/tables/scheme_B_metrics.csv`
- `06_results/Q2/tables/scheme_B_group_timing.csv`
- `06_results/Q2/tables/scheme_B_boundary_sensitivity.csv`
- `06_results/Q2/tables/scheme_B_empirical_baseline.csv`
- `06_results/Q2/tables/scheme_B_individual_time.csv`
- `06_results/Q2/figures/scheme_B_raw.png`
- `06_results/Q2/figures/scheme_B_boundaries.png`
- `06_results/Q2/figures/scheme_B_sensitivity.png`
- `06_results/Q2/logs/scheme_B_run.md`

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
