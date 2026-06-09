# 增量论文写入流程

本文件约束每完成一个问题后，如何进入 LaTeX 论文。

## 单题完成后的固定动作

每个问题完成以下节点后，才能写入对应小节：

1. 方案已审批；
2. Claude Code 已完成代码和结果；
3. Codex 代码与结果审查为 `PASS`；
4. 用户完成模型确认；
5. Codex 生成中文最终图；
6. 用户完成图表审批。

图表审批默认代表中文最终图审批：

```bash
python 05_code/tools/agentctl.py approve-figures --question Q1 --figures q1_relation_zh.png
```

只有在确有必要时才允许非中文图例外：

```bash
python 05_code/tools/agentctl.py approve-figures --question Q1 --figures q1_relation.png --allow-non-chinese
```

满足条件后运行：

```bash
python 05_code/tools/agentctl.py write-question-paper --question Q1
```

该命令会写入：

```text
07_paper/sections/model_q1.tex
```

并默认编译：

```text
07_paper/main.pdf
```

## 禁止提前填写的内容

以下内容属于总结性或跨问题内容，必须等全部问题完成后再写：

- `07_paper/sections/abstract.tex`
- `07_paper/sections/problem_analysis.tex` 中的整体分析和跨问题依赖总结
- `07_paper/sections/model_validation.tex`
- `07_paper/sections/evaluation.tex`
- 最终参考文献整理
- 总结性关键词和摘要中的综合结果

全部问题写入后，再运行：

```bash
python 05_code/tools/agentctl.py finalize-summary-paper
```

该命令只做守卫检查和编译，不会在问题未完成时允许写摘要。

## 图像语言规则

最终论文图必须是中文图。Claude Code 的英文图只作为验收参考，不能直接插入最终论文。

中文图要求：

- 坐标轴中文；
- 图例中文；
- 图内关键标注中文；
- 图题中文；
- 数学符号和通用缩写允许保留；
- 文件保存至 `07_paper/figures/`。
