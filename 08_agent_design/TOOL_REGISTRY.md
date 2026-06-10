# Tool Registry

本文件维护数学建模多 Agent 工作流可调用工具。机器可读版本见 `05_code/tools/tool_registry.json`。

## 安装入口

- Conda 环境：`environment.yml`
- pip 备选：`requirements.txt`
- 安装说明：`INSTALL.md`

推荐：

```bash
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py env-check
```

## 工具列表

| 工具 | 路径 | 负责人 | 用途 |
|---|---|---|---|
| Agent Controller | `05_code/tools/agentctl.py` | Codex | 环境检查、状态读取、数据扫描、审批记录、工单生成、LaTeX 编译 |
| PDF Style Extractor | `05_code/tools/pdf_style_extractor.py` | Codex | OCR 读取优秀论文并抽取结构信号 |
| Problem Statement Extractor | `05_code/tools/problem_statement_extractor.py` | Codex | 从题目 PDF 抽取题面 Markdown |
| LaTeX Paper Builder | `07_paper/main.tex` | Codex | 编译中文 CUMCM 风格论文 |
| Figure Pipeline | `07_paper/figure_generation_workflow.md` | Codex | 管理真实数据图和生图示意图 |
| Claude Workorder Template | `04_claude_workorders/templates/claude_workorder_template.md` | Codex | 生成 Claude Code 实现工单 |

## 维护规则

新增工具时必须同步修改：

1. `05_code/tools/tool_registry.json`
2. `08_agent_design/TOOL_REGISTRY.md`
3. `INSTALL.md` 或 `environment.yml`，如果新增依赖
4. `05_code/tools/agentctl.py env-check`，如果工具有可验证依赖

`agentctl.py` 当前维护以下流程命令：

- `init-state`
- `import-problem`
- `archive-stale-artifacts`
- `scan-data`
- `approve-language`
- `set-active-question`
- `prepare-schemes`
- `create-approval-brief`
- `create-model-confirmation-brief`
- `approve-schemes`
- `create-workorder`
- `create-workorders`
- `create-claude-prompt`
- `dispatch-claude`
- `open-claude-monitor`
- `install-vscode-tasks`
- `ingest-claude-report`
- `check-claude`
- `watch-claude`
- `create-review`
- `mark-reviewed`
- `compare-schemes`
- `confirm-model`
- `approve-figures`
- `mark-paper-written`
- `write-question-paper`
- `finalize-summary-paper`
- `paper-check`
- `layout-check`
- `latex-check`
- `readiness`

## 并发规则

- `agentctl.py` 的状态读写命令使用 `00_shared/.workflow_state.lock` 串行化，避免覆盖 `workflow_state.json`。
- 正式流程采用逐问推进：当前问题完成单题入文、PDF 编译和版面检查前，后续问题不能进入审批或 Claude Code 工单阶段。
- Claude Code 执行期间，Codex 应使用 `watch-claude` 定时轮询完成报告和标准输出，不能只依赖用户通知。
- 数学建模训练阶段主流程默认使用 `dispatch-claude --mode auto`。当前 `auto` 等价于 `terminal`：生成 `04_claude_workorders/terminal_runs/*.sh` 或 Windows PowerShell 脚本，从项目根目录打开可见终端并运行 Claude Code。
- 用户需要可见进度界面时，Codex 应运行 `open-claude-monitor` 打开监控终端，显示 Claude 终端状态、完成报告和标准输出。该监控终端不能替代 Claude 执行终端。
- 用户希望全部界面留在 VS Code 时，Codex 应运行 `install-vscode-tasks` 生成集成终端任务，用户运行 `Math Magic: Claude QX-B visible session` 后即可同时看到 Claude 执行终端和监控终端。
- Windows 交付环境必须优先使用 `doctor --target-os windows --write-vscode-smoke-task` 检查依赖和 VS Code Claude smoke task；正式任务使用 `install-vscode-tasks --target-os windows` 生成 PowerShell 版集成终端脚本。
- 当前本地训练工作流默认使用 `--terminal-permission-mode bypassPermissions`，并由配置追加 `--dangerously-skip-permissions`；同时默认 `--claude-session-mode continue`，复用 Claude Code 在当前项目目录的最近会话上下文。Codex 仍通过 `watch-claude` 监听完成报告和标准输出。
- `dispatch-claude --mode cli` 只作为后台备用路线，输出到 `04_claude_workorders/dispatch_logs/*.log`。当前接口不再提供 VSCode URI、前台粘贴或队列派发模式。
- Codex 生成 `create-approval-brief` 或 `create-model-confirmation-brief` 后，必须把命令输出中的选项直接发到用户聊天中；只写文件、只给路径或要求用户自行打开文件都不算完成审批告知。
- Codex 复审 PASS 后，必须运行 `create-model-confirmation-brief` 并在聊天中给用户明确选项；不得直接让用户执行 `confirm-model`。
- 每个问题完成模型确认后，Codex 必须运行 `write-question-paper` 写入对应 LaTeX 小节并编译 PDF；图表审批后再补入最终中文图并重编译。
- 每次编译 PDF 后必须通过 `layout-check` 版面验收。若用户或 Codex 给出明确页码目标，使用 `--expect-label-page label=page` 写成机器约束；例如 `fig:q1_surface=5`。
- 摘要、模型检验、模型评价与推广、论文 AI 使用说明等总结性章节必须等全部问题入文后再运行 `finalize-summary-paper`。
- 最终入论文图必须使用中文坐标轴、中文图例和中文图题；Claude Code 英文图只作为验收参考。
- 最终入论文图不得带图内底部长批注，例如“条件：变量取样本中位或均值”；这类条件写入正文或图注。最终入论文图不得使用红色虚线作为参考线、阈值线或分组边界线。
- 已存在的方案文件再次执行 `prepare-schemes` 时不会覆盖正文，只会补录机器状态和 artifact。
- `scan-data` 默认只登记可解析的数据文件；如需记录 PDF/Markdown 等非数据文件，可加 `--include-unsupported`。
- 换题时 `import-problem` 默认会先归档上一题生成物；若在中途发现旧题污染，先运行 `archive-stale-artifacts --dry-run` 查看清单，再显式加 `--force` 归档到 `00_shared/archive/stale_artifacts/<timestamp>/`。归档目录是本地审计/回滚产物，不随公共仓库发布。

## 工具边界

- Codex 可以维护工具注册表、模板、论文和图表工具。
- Claude Code 可以使用工具生成代码和结果，但不能修改已审批建模路线。
- 图表工具必须区分真实数据图和生图示意图。
- PDF OCR 结果只用于风格参考，不直接复制优秀论文内容。
