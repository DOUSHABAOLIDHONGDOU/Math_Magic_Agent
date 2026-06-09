# Q1 Scheme B v2 – Run Log

## 运行信息

- 版本：v2（Codex 返修后重写）
- 执行日期：2026-06-08
- Python 版本：3.9.6 (`/usr/bin/python3`)
- 随机种子：42（`SEED=42`，bootstrap 使用 `RandomState(SEED+i)`）

## 运行命令

```bash
# 从项目根目录运行
python3 05_code/Q1/q1_scheme_B.py
```

## 依赖

| 包 | 版本 |
|---|---|
| pandas | 2.3.3 |
| numpy | 2.0.2 |
| scikit-learn | 1.6.1 |
| scipy | 1.13.1 |
| matplotlib | 3.9.4 |
| openpyxl | 3.1.5 |

```bash
pip3 install pandas numpy scikit-learn scipy matplotlib openpyxl
```

## v1→v2 修复清单（对应 Codex 返修项）

| # | 返修项 | 修复方式 |
|---|---|---|
| 1 | MPLCONFIGDIR 在 import matplotlib 之后设置 | 移至文件顶部，`import matplotlib` 前设置 |
| 2 | CV 预处理泄漏：全局 fit_transform 后再做 GroupKFold | 每个外层 fold 内只用训练集 fit `SplineTransformer + StandardScaler`，测试集只 `transform` |
| 3 | RidgeCV 内层 cv=5 不按孕妇分组 | 外层每个训练折内使用内层 GroupKFold-3（group=孕妇代码）手动搜索 alpha |
| 4 | BMI bootstrap CI 出现 -23（行 bootstrap + 重新拟合样条结点外推导致） | 改为固定基函数 group bootstrap：按孕妇代码做有放回抽样，只重拟 Ridge 权重；避免对全局网格外推 |
| 5 | 孕周上限为 26 周，与题目 "10-25 周" 不符 | 主分析改为 <=25 周；额外输出 <=25 vs <=26 周的敏感性对比表 |
| 6 | 无 sanity check，异常值进入输出图表 | 增加 `_sanity()` 和 `_clip_ci()` 函数；预测/置信带出现负值时日志报警；图表使用 clip 后的 CI |
| 7 | 需重新生成所有输出 | 全部表格、图表、日志已重新生成 |

## 输入文件

| 文件 | 说明 |
|---|---|
| `01_problem/source/CUMCM2025Problems/C题/附件.xlsx` | 男胎检测数据工作表 |

## 输出文件

| 文件 | 说明 |
|---|---|
| `06_results/Q1/tables/scheme_B_metrics.csv` | 最优模型关键指标 |
| `06_results/Q1/tables/scheme_B_cv_comparison.csv` | 各样条度聚合 CV 指标（spline + linear 对比） |
| `06_results/Q1/tables/scheme_B_cv_folds.csv` | 每个外层 fold 详细记录 |
| `06_results/Q1/tables/scheme_B_sensitivity_degree.csv` | 样条度 3-6 敏感性 |
| `06_results/Q1/tables/scheme_B_sensitivity_gestation_cutoff.csv` | <=25 vs <=26 周敏感性对比 |
| `06_results/Q1/tables/scheme_B_partial_gestation.csv` | 孕周偏效应（含 bootstrap 95% CI，裁剪前后均保存） |
| `06_results/Q1/tables/scheme_B_partial_bmi.csv` | BMI 偏效应（含 bootstrap 95% CI，裁剪前后均保存） |
| `06_results/Q1/tables/scheme_B_heatmap_grid.csv` | 二维热力图网格预测值（已 clip≥0） |
| `06_results/Q1/figures/scheme_B_raw.png` | 主图：偏效应 + 热力图 + CV 对比 |
| `06_results/Q1/figures/scheme_B_residuals.png` | 残差诊断图 |

## 数据清洗（主分析）

- 原始行数：1082
- 去除孕周缺失/超出 [10,25]、Y浓度 ≤ 0 后：**1068 行，267 孕妇**
- 孕周字符串解析：`'12w+3'` → `12.429`，`'13w'` → `13.0`

## 关键结果

| 指标 | 线性基线 | Spline-Ridge v2 (度=3) |
|---|---|---|
| GroupKFold-5 CV-RMSE（无泄漏） | 0.03285 | **0.03236** |
| GroupKFold-5 CV-R² | 0.0073 | **0.0382** |
| ΔRMSE（非线性改进） | — | 0.00050 |
| 训练集 RMSE | — | 0.03151 |
| 训练集 R² | — | 0.1208 |
| Ridge alpha | — | 88.59 |

## 置信带范围

| 偏效应 | CI lo | CI hi | 是否有裁剪 |
|---|---|---|---|
| 孕周（固定 BMI@中位） | 0.0579 | 0.1068 | 无 |
| BMI（固定孕周@中位） | 0.0000 | 0.1266 | 是（9 个点从 -0.021 → 0） |

## Sanity 报警（1 条）

```
[SANITY WARN] CI_bmi: 9 CI bounds clamped to [0, 0.50];
  raw lo_min=-0.0206, hi_max=0.1266
```

原始最小值 -0.021，为 BMI 高端区域 bootstrap 的边界效应（极端 BMI 处样本稀少，少量 bootstrap 样本导致略微负值）。已 clip 至 0，图表和 CSV 均使用裁剪后值；原始值保留在 `ci_lo_raw` 列供参考。

## 孕周上限敏感性

| 数据集 | 行数 | CV-RMSE | CV-R² |
|---|---|---|---|
| <=25 周（主分析） | 1068 | 0.03236 | 0.0382 |
| <=26 周 | 1074 | 0.03235 | 0.0562 |

两个版本 CV-RMSE 几乎相同（差 0.00001），但 <=26 周 CV-R² 略高（0.056 vs 0.038）。主分析以 <=25 周为准（符合题目边界）；6 行 26 周记录可作为鲁棒性参考。

## 运行耗时

约 4-6 分钟（主要耗时：外层 5 fold × 4 度 × 内层 alpha 搜索 × spline + linear，共约 1600 次 Ridge 拟合；200 次 group bootstrap）
