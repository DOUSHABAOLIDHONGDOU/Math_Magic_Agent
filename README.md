# Math Magic Agent

[![tests](https://github.com/DOUSHABAOLIDHONGDOU/Math_Magic_Agent/actions/workflows/test.yml/badge.svg)](https://github.com/DOUSHABAOLIDHONGDOU/Math_Magic_Agent/actions/workflows/test.yml)
[![license](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

> 中国大学生数学建模赛前训练用的 **Codex + Claude Code 多 Agent 协作工作流**。
> 从题目导入到论文 PDF，全部命令化驱动，43 个自动化测试覆盖。
>
> 项目缘起、战绩、免责声明：见 [INTRODUCTION.md](INTRODUCTION.md) / [INTRODUCTION.pdf](INTRODUCTION.pdf)

## 它能做什么

- **逐问推进**：当前问题入文 + PDF 编译 + 版面检查通过后，下一问才解锁
- **三段审批**：方案审批 / 模型确认 / 图表审批，每次都直接在聊天里列出选项，由人裁决
- **角色分工**：Codex 负责建模总控 + 论文 + 图表 + 审查；Claude Code 负责代码 + 调试 + 结果输出
- **状态机持久化**：所有进展写到 `00_shared/workflow_state.json`，每次保存自动滚动 10 个快照
- **AutoEDA**：扫描数据后一键生成 6 张诊断图（相关矩阵 / 缺失模式 / 分布 / 异常 / 与目标 Top-5 散点）
- **BM25 RAG 检索**：对优秀论文建索引；方案生成时根据题面自动检索同题型片段注入提示
- **方案自动对比**：扫描每个方案的 metrics CSV，自动 join + 评分 + 推荐
- **PDF 图表 lint**：检测红虚线 / 2×2 网格 / 超宽图（违反论文风格约束）
- **自愈建议**：`readiness` 末尾告诉你下一步该跑什么命令，缺什么依赖怎么装
- **三档 Trust Profile**：strict（训练严格）/ normal（演练）/ fast（赛时快速通道）

## 5 分钟上手

```bash
# 1. 环境
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task

# 2. 导入你的题面 + 数据
python 05_code/tools/agentctl.py import-problem \
    --statement 01_problem/source/B题/statement.md \
    --title "B题 碳化硅外延层厚度的确定" \
    --data-dir 01_problem/source/B题/附件
python 05_code/tools/agentctl.py approve-language --language Python
python 05_code/tools/agentctl.py scan-data --data-dir 01_problem/source/B题/附件
python 05_code/tools/agentctl.py auto-eda --question Q1 --target "反射率 (%)"

# 3. 可选：建 RAG 索引（已经放好 paper_texts 就跳过 OCR）
python 05_code/tools/agentctl.py rag-status
python 05_code/tools/agentctl.py index-papers

# 4. 走 Q1
python 05_code/tools/agentctl.py prepare-schemes --question Q1
python 05_code/tools/agentctl.py create-approval-brief --question Q1
# (Codex 填好 03_methods/Q1/scheme_*.md → 用户聊天里选 B)
python 05_code/tools/agentctl.py approve-schemes --question Q1 --schemes B
python 05_code/tools/agentctl.py create-claude-prompt --question Q1 --scheme B
python 05_code/tools/agentctl.py dispatch-claude --question Q1 --scheme B --watch
# (Claude 跑完 → ingest → review → 模型确认)
python 05_code/tools/agentctl.py create-model-confirmation-brief --question Q1
python 05_code/tools/agentctl.py confirm-model --question Q1 --scheme B
python 05_code/tools/agentctl.py write-question-paper --question Q1
python 05_code/tools/agentctl.py latex-check
```

任何一步卡住，跑 `python 05_code/tools/agentctl.py readiness` 看自愈建议。

## 架构

```
00_shared/                  共享状态（workflow_state.json + 文档 + snapshots）
01_problem/                 题面与数据字典
02_references/              优秀论文 + 风格指南 + BM25 索引
03_methods/Q*/              每问的 A/B/C 方案 + 审批简报 + approved.md
04_claude_workorders/       Claude 工单、提示词、完成报告、终端调度脚本
05_code/                    实现代码（Claude 写）+ tools/agentctl.py + mm/ + tests/
06_results/Q*/              结果表、图、EDA、方案对比
07_paper/                   LaTeX 工作版（main.tex + sections/）
08_agent_design/            Agent 设计文档与版本计划
```

## 命令一览（46 个）

```
环境/状态:     init-state status env-check doctor tools readiness rag-status
题目/数据:     import-problem archive-stale-artifacts scan-data approve-language auto-eda
方案/审批:     set-active-question prepare-schemes create-approval-brief approve-schemes
工单/调度:     create-workorder create-workorders create-claude-prompt
              dispatch-claude open-claude-monitor install-vscode-tasks
              watch-claude check-claude ingest-claude-report
审查:          create-review mark-reviewed compare-schemes
确认/论文:     create-model-confirmation-brief confirm-model approve-figures
              write-question-paper mark-paper-written finalize-summary-paper
              paper-check layout-check figure-lint latex-check
RAG:           index-papers retrieve-context
策略:          set-trust-profile gen-ai-log
```

`python 05_code/tools/agentctl.py --help` 查看所有命令；每个子命令支持 `--help`。

## 测试

```bash
python -m pytest 05_code/tools/tests/ -v
# 43 passed
```

测试不依赖 xelatex / tesseract / Claude Code，可在 CI 里直接跑。

## 设计决策

- **为什么这么多 trust profile**：训练时希望每个审批都过手；赛时希望 Codex 复审 PASS 后直接推进。三档可以一键切。
- **为什么 RAG 用 BM25 而不是向量**：纯 Python、无 GPU、无 embedding 模型下载、单文件 < 200 行；语料只有几十篇时检索质量足够。
- **为什么图表 lint 用 Pillow 而不是 OpenCV**：CUMCM 训练机器很少装 OpenCV，但 Pillow 是 matplotlib 必装依赖。
- **为什么 agentctl 是命令化而不是 Web UI**：训练阶段命令化好 grep / 好截图 / 好审计；论文写作阶段反正主战场是 VS Code 集成终端。

## 公开与版权

- 代码 MIT（见 `LICENSE`）
- LaTeX 模板沿用第三方原许可证（见 `07_paper/template_raw/`）
- 仓库不内置任何赛题题面、附件数据、优秀论文 PDF。这些用户自己导入；`.gitignore` 已默认排除，防止误传

## 文档

- [INSTALL.md](INSTALL.md) — 环境与依赖
- [CONTRIBUTING.md](CONTRIBUTING.md) — 模块布局、开发约定、Windows 兼容性
- [08_agent_design/AGENT_SPEC.md](08_agent_design/AGENT_SPEC.md) — Agent 角色与状态机
- [00_shared/WORKFLOW_PROTOCOL.md](00_shared/WORKFLOW_PROTOCOL.md) — 工作流权威协议
- [08_agent_design/WORKFLOW_COMMANDS.md](08_agent_design/WORKFLOW_COMMANDS.md) — 命令式流程指南
- [08_agent_design/VERSION_PLAN.md](08_agent_design/VERSION_PLAN.md) — 历次版本变更记录
