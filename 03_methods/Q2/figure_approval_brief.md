# Q2 图表审批简报

## 当前审批对象

- 当前只审批 Q2 的最终论文候选图。
- Q2-B 已确认作为最终模型；本轮图表不改变建模路线。
- 这些图均为 Codex 根据已复审 CSV 表重绘的中文图，Claude Code 英文图不直接入论文。

## 候选图

| 图号 | 文件 | 表达结论 | 是否建议入文 |
|---|---|---|---|
| Q2-FIG-001 | `07_paper/figures/q2_fig1_bmi_group_timing.png` | 展示 BMI 三组分界和各组推荐检测时点 | 建议入文 |
| Q2-FIG-002 | `07_paper/figures/q2_fig2_bootstrap_stability.png` | 展示自助抽样下分界和推荐时点稳定性 | 建议入文，可与敏感性表配合 |
| Q2-FIG-003 | `07_paper/figures/q2_fig3_tstar_robustness.png` | 展示模型 T* 退化及实测 T* 稳健性补充 | 建议入文，但正文必须保守解释 |

## 审批总览

- 总览图：`03_methods/Q2/q2_figure_approval_sheet.png`
- 清单：`03_methods/Q2/q2_final_figures_manifest.csv`

## Codex 建议

- 建议通过三张图，但 5.2 中不要堆图；优先图 1 主结果、图 2 稳定性，图 3 可放在稳健性分析段落。
- 若担心版面过满，可批准图 1 和图 3 入正文，图 2 的数值改为表格。

## 你可以这样回复

```text
Q2 图表审批通过：图1、图2、图3都可以入文。
```

或：

```text
Q2 图表审批通过：只入文图1和图3，图2改为表格或附录。
```
