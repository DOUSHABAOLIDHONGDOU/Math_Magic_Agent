# Figure Generation Workflow

本文件定义 Codex 在论文图表阶段的执行规则。

## 图表分类

## 中文论文图硬约束

进入最终论文的图像必须使用中文表达：

- 坐标轴、图例、图内标注、图题优先使用中文；
- 必要英文缩写如 BMI、NIPT、GC、RMSE、R² 可以保留，但需配合中文说明；
- Claude Code 输出的英文原始图只作为验收和数据核对参考，不直接进入最终论文；
- Codex 负责按中国大学生数学建模竞赛优秀论文风格重绘或再加工最终图；
- 每张最终图进入 LaTeX 前必须经过图表审批。
- 最终论文图不得在图内底部写“条件：……”一类长批注；变量取中位数/均值、参考条件和解释边界应写在正文、图题后说明或表格备注中。
- 最终论文图不得使用红色虚线作为参考线、阈值线或分组边界线；必要参考线应采用低饱和中性灰、细线或点线，并在图例/正文中解释。

## 论文版面硬约束

- 最终图坚持“一图一主要结论”。不同性质的结果不要拼在同一张图里。
- `subfigure` 最多两张，且只能用于同一变量、同一指标或同一结论下的对照；三张及以上子图不得进入最终论文。
- 普通数据图目标宽度为 `0.58\textwidth` 到 `0.70\textwidth`；热力图、流程图、网络图等复杂图目标宽度不超过 `0.76\textwidth`。
- 单图高度不得接近半页；若图像过高，优先缩小画布、改横向信息为表格，或拆成多处图文解释。
- 不允许一页全是图。每个浮动图附近必须有正文解释，跨小节前使用 `\FloatBarrier` 控制漂移。
- 若表格后紧接双子图，图像不得被推到页底形成大空白；优先用 `[!ht]`、缩小子图宽度，并在图后设置 `\FloatBarrier`，确保解释文字跟在图后。
- 敏感性、误差和鲁棒性结论优先用表格承载多项指标，再配一张最关键的单结论图。

### 真实数据图

用于展示计算结果、指标对比、敏感性分析、误差分析和模型输出。

规则：

- 必须由真实数据和可复现脚本生成。
- 不允许用生图能力替代真实数值图。
- Claude Code 可以提供基础绘图脚本和原始图。
- Codex 负责最终图表类型、配色、字体、标注和 LaTeX 插入。
- 最终入论文版本必须是中文图，文件保存到 `07_paper/figures/`。

### 结构和机制示意图

用于展示模型流程、算法框架、机制关系、场景结构和论文说明图。

规则：

- 优先使用可复现的 Mermaid、TikZ、Python 或矢量图工具。
- 当需要更强视觉表达时，Codex 可使用 imagegen skill 生成位图资产。
- 生成后的项目资产必须保存到 `07_paper/figures/`。
- 不得只保留在默认生成目录。

## imagegen 使用规则

Codex 使用 imagegen skill 时：

1. 默认使用内置 `image_gen` 工具。
2. 只在用户明确要求 CLI/API 或透明图确实需要原生透明时，才考虑 CLI fallback。
3. 生成项目用图后，必须移动或复制到 `07_paper/figures/`。
4. 不覆盖已有图，使用版本化文件名。
5. 最终回复或日志必须记录生成提示词、保存路径和使用模式。
6. 透明背景图默认先生成纯色 chroma-key 背景，再本地去背景。

## 论文图审批模板

```markdown
## FIG-000

- 问题：Q1 / Q2 / Q3
- 图名：
- 图类型：真实数据图 / 流程图 / 机制图 / 示意图
- 生成方式：Python / TikZ / Mermaid / imagegen
- 文件路径：
- 表达结论：
- 是否基于真实数据：
- Codex 审查意见：
- 用户审批：通过 / 修改 / 废弃
```

## 图像生成提示模板

```text
Use case: scientific-educational
Asset type: math modeling paper figure
Primary request: 生成用于中文数学建模论文的模型流程示意图。
Scene/backdrop: clean academic white background, no decorative clutter
Subject: clear process diagram with labeled stages
Text: use concise Chinese labels supplied by Codex
Style: polished academic infographic, sharp edges, high readability
Constraints: no fake numeric results, no watermark, no school identity, no irrelevant icons
Output destination: 07_paper/figures/<figure_name>.png
```
