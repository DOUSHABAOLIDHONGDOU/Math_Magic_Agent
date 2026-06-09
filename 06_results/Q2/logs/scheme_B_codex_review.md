# Codex Review: Q2 Scheme B

## 基本信息

- 问题：Q2
- 方案：B
- Claude 完成报告：`04_claude_workorders/completions/Q2_scheme_B_completion.md`
- 审查日期：2026-06-09
- 审查结论：PASS（实现通过；模型确认需用户选择论文口径）

## 路线一致性

- 是否严格遵守 `03_methods/Q2/scheme_B.md`：是。脚本以 Q1-B v2 模型估计个体达标时间 $T_i^*$，再按 BMI 排序做一维动态规划分组，并枚举 $K=3,4,5,6$ 和最小组样本量。
- 是否偏离已审批边界：无。未修改 Q1 代码、Q1 结果、已审批方案或论文结论。
- 是否需要用户仲裁：需要模型确认审批。核心不是代码错误，而是主结论口径选择：是否接受模型预测 $T_i^*$ 高度集中于 10 周这一结果，或要求改用概率化/实测达标时间作为主线。

## 代码审查

- 可复现性：PASS。Codex 已从项目根目录运行 `python 05_code/Q2/q2_scheme_B.py`，脚本完整跑通并覆盖生成 Q2 输出。
- 随机种子：PASS。脚本设置 `SEED=42`，Bootstrap 使用 `np.random.RandomState(SEED + i_b)`。
- 路径处理：PASS。项目根目录由 `__file__` 推导，输出到 `06_results/Q2/`，Matplotlib 缓存写入项目内 `.cache/matplotlib`。
- 数据清洗：PASS。读取男胎检测数据，解析孕周，保留 10--25 周、Y 浓度为正且核心字段完整样本，共 1068 行、267 名孕妇。
- 异常处理：PASS with note。脚本对未达标个体设置右删失；实测达标时间中 9 名从未观测到 Y≥4%，已记录在输出表。

## 结果审查

- 输出表格：PASS。`scheme_B_group_timing.csv`、`scheme_B_metrics.csv`、`scheme_B_boundary_sensitivity.csv`、`scheme_B_empirical_baseline.csv`、`scheme_B_bootstrap_stability.csv`、`scheme_B_individual_time.csv` 均存在；Codex 复跑后新增 `scheme_B_empirical_tstar_grouping.csv`。
- 输出图表：PASS for review only。三张图可用于验收，但为英文且含多面板，不能直接入最终论文；后续 5.2 入文必须由 Codex 重绘中文最终图。
- 核心指标：模型预测 $T_i^*$ 中 263/267 名孕妇为 10 周，最优 $K=3$，BMI 分界约 29.3、30.0；G3（BMI≥30.1）推荐 11w+4d；总风险与经验 BMI 基准均为 1.0。
- 是否支持题目结论：部分支持。能给出 BMI 分组和最佳检测时点，但“数据驱动优于经验分组”没有风险降幅证据；论文应强调边界约 30 与临床分级一致、G3 时点略晚，以及 Q1 模型解释度有限导致 $T_i^*$ 退化。

## 数模论文补强

- 敏感性分析：已覆盖 $K$、最小组样本量、早检/晚检权重和复杂度惩罚。
- 误差分析：已通过 Bootstrap 给出 BMI 边界和最优时点稳定性；还应在论文中说明 Q1 残差和低 $R^2$ 对 $T_i^*$ 的影响。
- 鲁棒性检验：已加入实测达标时间 `emp_T_star` 的二级分析，可作为模型预测退化时的稳健性补充。
- 对比基准：已与经验 BMI 区间 `[20,28),[28,32),[32,36),[36,40),[40,+∞)` 对比。

## 退回 Claude Code 的修改项

无必须退回项。若用户不接受模型预测 $T_i^*$ 主线，则需要新工单批准“概率化 $T_i^*$”或“实测 $T_i^*$ 主线”，这属于建模路线变更，不是 Claude 自行返修。

## 可进入论文的材料

- 表格：`scheme_B_group_timing.csv`、`scheme_B_bootstrap_stability.csv`、`scheme_B_empirical_baseline.csv`、`scheme_B_empirical_tstar_grouping.csv`。
- 图：当前英文图仅作验收参考；最终论文建议重绘 2--3 张中文图：BMI-T* 散点与分界、Bootstrap 边界稳定性、实测 T* 对照。
- 文字结论：Q2-B 可进入模型确认审批。推荐论文口径为“模型预测主线 + 实测 T* 稳健性补充”，并明确本问结论依赖 Q1 趋势模型，不能夸大为高精度医学预测。
