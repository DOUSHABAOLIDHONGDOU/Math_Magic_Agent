# Q1 图表审批简报

## 当前审批对象

- 问题：`Q1`
- 模型：`Q1-B v2`，已由用户确认，决策 ID `D-006`
- 生成脚本：`05_code/Q1/q1_final_figures.py`
- 审批总览图：`03_methods/Q1/q1_figure_approval_sheet.png`
- 图表清单：`03_methods/Q1/q1_final_figures_manifest.csv`

## 候选图表

| 图号 | 文件 | 类型 | 表达结论 |
|---|---|---|---|
| Q1-FIG-001 | `07_paper/figures/q1_fig1_gestation_effect.png` | 真实数据图 | 孕周对 Y 染色体浓度存在非线性影响，整体随孕周后段升高 |
| Q1-FIG-002 | `07_paper/figures/q1_fig2_bmi_effect.png` | 真实数据图 | BMI 与 Y 染色体浓度呈非线性关系，边界 BMI 区间不确定性较高 |
| Q1-FIG-003 | `07_paper/figures/q1_fig3_gestation_bmi_surface.png` | 真实数据图 | 展示孕周与 BMI 联合作用下的预测浓度面和 4% 等值线 |
| Q1-FIG-004 | `07_paper/figures/q1_fig4_validation_sensitivity.png` | 真实数据图 | 汇总交叉验证、样条阶数敏感性、孕周上界敏感性和残差检验 |
| Q1-FIG-005 | `07_paper/figures/q1_fig5_model_flow.png` | 流程图 | 展示 Q1 样条岭回归从数据清洗到敏感性分析的建模流程 |

## Codex 审查意见

- 所有最终图均为中文坐标轴、中文图例或中文说明，满足论文入文语言要求。
- Q1-FIG-001 至 Q1-FIG-004 均由已复审通过的结果表重绘，不改变模型结果。
- Q1-FIG-005 是流程图，只说明建模步骤，不包含虚构数值。
- Q1-FIG-002 的 BMI 边界区间置信带较宽，若入文应在正文中说明高/低 BMI 边界预测不确定性更大。

## 审批选项

| 选项 | 结论 | 后续动作 |
|---|---|---|
| 1 | 全部通过（推荐） | Codex 记录图表审批，通过后写入 Q1 LaTeX 小节并编译 PDF |
| 2 | 部分通过，要求修改指定图 | 用户指出要修改的图号和修改意见，Codex 返修后重新提交审批 |
| 3 | 不通过，废弃本轮图表 | Codex 重新设计 Q1 图表风格或减少/更换图表 |

## 推荐回复

```text
Q1 图表审批选择选项 1。理由：全部图表通过，可进入 Q1 论文小节写入和 PDF 编译。
```

或：

```text
Q1 图表审批选择选项 2。需要修改：Q1-FIG-002，理由：请调整 BMI 图的置信区间表达。
```
