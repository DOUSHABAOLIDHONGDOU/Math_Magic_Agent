# Workflow Commands

本文件定义 Math Magic 多 Agent 工作流的命令式推进方式。

## 0. 环境检查

```bash
python 05_code/tools/agentctl.py env-check
python 05_code/tools/agentctl.py tools
python 05_code/tools/agentctl.py init-state
```

## 1. 导入题目和数据

如果题面是 PDF，先抽取为 Markdown：

```bash
python 05_code/tools/problem_statement_extractor.py \
  --input 01_problem/source/problem.pdf \
  --out 01_problem/source/problem_statement.md
```

```bash
python 05_code/tools/agentctl.py import-problem \
  --statement 01_problem/source/problem_statement.md \
  --title "训练题目名称" \
  --problem-id "TRAIN-001" \
  --data-dir 01_problem/data
```

`import-problem` 默认会先归档上一题生成物，避免旧方案、旧工单、旧图表或旧论文段落污染新题。若只想检查或手动清理旧题残留：

```bash
python 05_code/tools/agentctl.py archive-stale-artifacts --dry-run
python 05_code/tools/agentctl.py archive-stale-artifacts --force --reason "archive old generated artifacts before continuing current problem"
```

扫描数据字段：

```bash
python 05_code/tools/agentctl.py scan-data --data-dir 01_problem/data
```

默认只登记可解析的数据文件；需要保留 PDF/Markdown 等非数据文件诊断时，增加 `--include-unsupported`。

审批默认代码语言：

```bash
python 05_code/tools/agentctl.py approve-language --language Python --notes "用户批准 Python 作为默认实现语言"
```

## 2. Codex 逐问生成三套方案

设置当前问题。正式流程从第一问开始，后续问题要等前一问写入 LaTeX、编译 PDF 并通过版面检查后再解锁：

```bash
python 05_code/tools/agentctl.py set-active-question --question Q1 --defer-later
```

为当前问题生成方案文件和 Codex 提示：

```bash
python 05_code/tools/agentctl.py prepare-schemes --question Q1
```

Codex 读取生成的：

```text
03_methods/Q1/codex_scheme_generation_prompt.md
```

并将 A/B/C 三套方案写入：

```text
03_methods/Q1/scheme_A.md
03_methods/Q1/scheme_B.md
03_methods/Q1/scheme_C.md
```

生成给用户看的三方案审批简报：

```bash
python 05_code/tools/agentctl.py create-approval-brief --question Q1
```

该命令会把三套方案直接输出到终端。Codex 必须在聊天中向用户列出 A/B/C 选项；只给 `03_methods/Q1/approval_brief.md` 路径不算完成审批告知。

用户审批方案。可以只选一个，也可以明确多选：

```bash
python 05_code/tools/agentctl.py approve-schemes --question Q1 --schemes B --notes "用户选择 Q1 方案 B 交给 Claude Code 执行"
```

## 3. 给 Claude Code 的执行提示词

生成工单和 Claude Code 执行提示词：

```bash
python 05_code/tools/agentctl.py create-claude-prompt --question Q1 --scheme B
```

提示词会写入：

```text
04_claude_workorders/Q1_scheme_B_claude_prompt.md
```

如用户批准多个方案，可分别生成多个提示词，但仍然只处理当前问题。

主流程不再要求用户复制粘贴。Codex 可以打开一个可见 Claude Code 终端：

```bash
python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --mode auto \
  --watch \
  --require-standard-outputs
```

当前主流程默认使用 `--mode auto`，它等价于 `--mode terminal`：在当前系统生成可见终端脚本，从项目根目录运行 Claude Code。默认会追加 `--continue`，让 Claude Code 续接该项目目录下最近一次会话上下文。

默认权限模式为 `bypassPermissions`，并通过配置追加 `--dangerously-skip-permissions`，适用于用户已确认可信的本地训练仓库，减少每次编辑/运行的审批点击。只有明确需要断开 Claude Code 记忆时，才追加 `--claude-session-mode new`。

打开可见监控终端：

```bash
python 05_code/tools/agentctl.py open-claude-monitor \
  --question Q1 \
  --scheme B
```

监控终端用于显示 Claude 终端状态、完成报告和标准输出文件，不负责执行建模代码。Claude 真正执行仍由 `dispatch-claude --mode auto` 的可见终端完成。

如果用户明确希望在 VS Code 面板中观察 Claude 与 Codex 状态，安装 VS Code 集成终端任务：

```bash
python 05_code/tools/agentctl.py install-vscode-tasks \
  --question Q1 \
  --scheme B \
  --target-os windows
```

安装后在 VS Code 执行任务 `Math Magic: Claude QX-B visible session`。该任务并行打开 Claude 执行终端和监控终端；Windows 下生成 PowerShell 脚本，macOS/Linux 下生成 bash 脚本。不要再使用 VS Code Claude 插件 URI 或自动粘贴路线作为主流程。

后台备用路线：

```bash
python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --mode cli \
  --watch \
  --require-standard-outputs
```

`cli` 模式使用配置好的 Claude Code CLI 非交互执行，不提供可见终端界面，只保留 `04_claude_workorders/dispatch_logs/*.log`。

返修时发送最新返修提示词：

```bash
python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --revision \
  --mode auto \
  --watch \
  --require-standard-outputs
```

CLI 配置方式：

- 临时配置：`CLAUDE_CODE_COMMAND="claude" python 05_code/tools/agentctl.py dispatch-claude ...`
- 持久配置：复制 `04_claude_workorders/claude_dispatch_config.example.json` 为 `04_claude_workorders/claude_dispatch_config.json`，并填写本机 Claude Code 命令。
- 主流程默认使用 `--mode auto` 打开可见终端；只有确实需要后台执行时才使用 `--mode cli`。可见终端脚本生成后会记录 `terminal_script_created`，真正运行时才记录 `running/run_started_at`。

Codex 应定时监听 Claude Code 是否完成，而不是等待用户通知。建议在另一个终端运行：

```bash
python 05_code/tools/agentctl.py watch-claude \
  --question Q1 \
  --scheme B \
  --interval 30 \
  --ingest \
  --create-review \
  --require-standard-outputs
```

如果只想单次检查：

```bash
python 05_code/tools/agentctl.py check-claude \
  --question Q1 \
  --scheme B \
  --ingest \
  --create-review \
  --require-standard-outputs
```

## 模型确认审批

Claude Code 完成、Codex 复审 `PASS` 后，不得直接确认模型。必须先生成用户可读的模型确认审批简报：

```bash
python 05_code/tools/agentctl.py create-model-confirmation-brief --question Q1
```

该命令会把模型确认选项直接输出到终端。Codex 必须在聊天中向用户列出选项 1/2/3；只给 `03_methods/Q1/model_confirmation_brief.md` 路径不算完成审批告知。

用户在简报中选择：

- 选项 1：标准批准；
- 选项 2：带论文约束批准；
- 选项 3：不批准，返修或重跑。

用户回复后，Codex 才能运行：

```bash
python 05_code/tools/agentctl.py confirm-model --question Q1 --scheme B --notes "用户选择模型确认选项 2。"
```

## 单题入文与编译

每个问题完成以下条件后，Codex 必须立即将该问题写入 LaTeX 并编译一次 PDF：

- 模型确认完成；
- 已有可支撑正文的公式、结果表、日志或运行结论。

图表不再阻塞第一次单题入文。尚未审批最终中文图时，`write-question-paper` 先写正文、公式和结果表；图表审批后再补入最终中文图并重新编译。若某次任务确实要求恢复旧的严格门禁，可显式使用 `--require-figures-approved`。

图表审批默认按中文最终图处理：

```bash
python 05_code/tools/agentctl.py approve-figures --question Q1 --figures q1_relation_zh.png
```

命令：

```bash
python 05_code/tools/agentctl.py write-question-paper --question Q1
```

该命令只允许写 `07_paper/sections/model_qX.tex`。摘要、整体问题分析、模型检验、模型评价及推广、全局 AI 使用说明等跨问题内容保持锁定。

全部问题写入后，才允许进入总结性章节：

```bash
python 05_code/tools/agentctl.py finalize-summary-paper
```

最终论文图必须是中文图；Claude Code 输出的英文图只作为验收图或重绘参考。

最终论文图不得在图内底部加入“条件：变量取样本中位或均值”等长批注；这些条件写在正文、图注或表格备注中。最终论文图不得使用红色虚线表示阈值、参考线或分组边界，必要参考线使用中性灰细点线。

Claude Code 完成后，应将完成报告保存为 Markdown。监听命令检测到报告和标准输出后会自动摄取；也可以手动摄取：

```bash
python 05_code/tools/agentctl.py ingest-claude-report --question Q1 --scheme B --report path/to/report.md
```

## 4. Codex 审查

生成 Codex 审查模板：

```bash
python 05_code/tools/agentctl.py create-review --question Q1 --scheme B
```

Codex 填写审查后，记录结果：

```bash
python 05_code/tools/agentctl.py mark-reviewed --question Q1 --scheme B --result PASS
```

如果本问批准并运行了多个方案，生成对比表：

```bash
python 05_code/tools/agentctl.py compare-schemes --question Q1
```

用户确认最终模型：

```bash
python 05_code/tools/agentctl.py confirm-model --question Q1 --scheme B --notes "综合指标最优，论文解释性较好"
```

`confirm-model` 完成后，必须继续运行 `write-question-paper`；该问成功编译入文后，下一问才解锁。

## 5. 图表和论文

模型确认后写入单题正文并编译：

```bash
python 05_code/tools/agentctl.py write-question-paper --question Q1
```

用户审批最终图表：

```bash
python 05_code/tools/agentctl.py approve-figures --question Q1 --figures "q1_result.png,q1_sensitivity.png"
```

图表补入后重新编译：

```bash
python 05_code/tools/agentctl.py latex-check
```

检查论文文件：

```bash
python 05_code/tools/agentctl.py paper-check
python 05_code/tools/agentctl.py latex-check
```

`latex-check` 默认会编译 PDF 并执行版面检查。若当前问题有明确页码目标，必须把标签页码写成机器约束，例如：

```bash
python 05_code/tools/agentctl.py latex-check \
  --expect-label-page fig:q1_surface=5
```

如果只检查现有 PDF，不重新编译：

```bash
python 05_code/tools/agentctl.py layout-check \
  --expect-label-page fig:q1_surface=5
```

版面检查失败时，不允许进入下一问的论文写入或最终总结章节。

## 6. 状态检查

```bash
python 05_code/tools/agentctl.py status
python 05_code/tools/agentctl.py readiness
```

## 状态文件

机器可读状态文件：

```text
00_shared/workflow_state.json
```

人工可读状态文件：

```text
00_shared/PROJECT_STATE.md
00_shared/DECISION_LOG.md
00_shared/QUESTION_BOUNDARIES.md
00_shared/AI_USAGE_LOG.md
```

## 守卫规则

部分命令默认会检查前置状态：

- `prepare-schemes` 要求已导入题目；
- `prepare-schemes`、`create-approval-brief`、`approve-schemes` 和 `create-workorders` 默认只能用于当前解锁问题；
- `create-workorders` 和 `create-claude-prompt` 要求方案已审批；
- `dispatch-claude` 可将当前提示词或最新返修提示词发送到可见 Claude Code 终端；`cli` 模式仅作后台备用；
- `watch-claude` 会轮询完成报告和标准输出文件，发现后可自动摄取并生成 Codex 审查模板；
- `confirm-model` 要求对应方案已通过 Codex 审查。

如需测试命令或人工强制推进，可使用 `--force`。正式流程中不建议跳过守卫。

## 并发状态写入

`agentctl.py` 的状态读写命令会使用 `00_shared/.workflow_state.lock` 加锁。可以并行运行同一问题内的实现或审查辅助命令，但正式流程不允许多个问题同时进入审批和 Claude Code 工单阶段。
