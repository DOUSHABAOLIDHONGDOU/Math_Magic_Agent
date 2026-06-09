# Codex Review: Q1 Scheme B v2

## 基本信息

- 问题：Q1
- 方案：B
- Claude 完成报告：`04_claude_workorders/completions/Q1_scheme_B_completion.md`
- 审查日期：2026-06-08
- 审查结论：PASS

## 路线一致性

- 是否严格遵守 `03_methods/Q1/scheme_B.md`：是。仍采用 `SplineTransformer + Ridge` 的 GAM 风格路线，并保留孕周、BMI、交互项和质量控制变量。
- 是否偏离已审批边界：否。未推进 Q2/Q3/Q4，未修改建模路线文件。
- 是否需要用户仲裁：需要进入模型确认审批，由人类队伍决定是否将 Q1-B v2 作为 Q1 最终模型。

## 代码审查

- 可复现性：PASS。固定 `SEED=42`，路径以项目根目录构造，输出文件齐全。
- 随机种子：PASS。bootstrap 使用 `RandomState(SEED+i)`。
- 路径处理：PASS。`MPLCONFIGDIR` 已在 `import matplotlib` 前设置到项目 `.cache/matplotlib`。
- 数据清洗：PASS。主分析使用题面边界 `10 <= 孕周 <= 25`，并额外输出 `<=26` 敏感性表。
- 交叉验证：PASS。外层 GroupKFold 中样条基函数、交互项、标准化器和 Ridge 均只在训练折拟合，测试折只 transform/predict；alpha 选择使用孕妇代码分组的内层 GroupKFold。

## 结果审查

- 输出表格：PASS。核心表、fold 表、样条度敏感性、孕周边界敏感性、偏效应表和热力图网格均存在。
- 输出图表：PASS for modeling review。主图不再被异常置信带拉坏，残差图可用于论文误差分析；最终论文图表仍建议由 Codex 统一重绘成中文 CUMCM 风格。
- 核心指标：Spline-Ridge v2 的 GroupKFold-5 CV-RMSE 为 0.03236，CV-R2 为 0.0382；线性基线 CV-RMSE 为 0.03285，CV-R2 为 0.0073。
- 是否支持题目结论：基本支持 Q1 的关系分析。模型解释度较低，应在论文中明确 Y 浓度受未观测个体差异和检测误差影响较大。

## 数模论文补强

- 敏感性分析：已具备。样条度 3-6 对比显示 degree=3 最优，`<=25` 与 `<=26` 孕周边界 CV-RMSE 几乎相同。
- 误差分析：已具备。残差 Shapiro p≈5.25e-17，说明残差非正态；论文中应使用 bootstrap 和稳健表述。
- 鲁棒性检验：已具备。GroupKFold 按孕妇分组，可防止同一孕妇重复检测记录泄漏。
- 对比基准：已具备。线性 Ridge 基线纳入同一外层折比较。

## 仍需论文说明的注意点

1. CV-R2 仅约 0.038，说明 Q1 模型主要用于刻画趋势和后续时点优化的关系基础，不宜夸大预测精度。
2. BMI 高端区域样本稀少，bootstrap 原始 CI 下界最小约 -0.0206，已裁剪到 0；论文图注应标注高 BMI 区域不确定性较大。
3. 残差显著非正态，参数式显著性结论应谨慎，建议以分组交叉验证、bootstrap CI 和敏感性分析支撑结论。
4. Claude 输出图表是验收图，最终入论文前建议由 Codex 重绘中文图、统一字体、色彩和编号。

## 可进入论文的材料

- 表格：`scheme_B_metrics.csv`, `scheme_B_cv_comparison.csv`, `scheme_B_sensitivity_degree.csv`, `scheme_B_sensitivity_gestation_cutoff.csv`
- 图：`scheme_B_raw.png`, `scheme_B_residuals.png` 可作为重绘参考
- 文字结论：孕周与 Y 浓度呈非线性关系；BMI 的边际效应存在非线性和高端不确定性；非线性样条模型较线性基线有小幅但稳定的 CV-RMSE 改进。
