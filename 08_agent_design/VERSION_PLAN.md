# Version Plan

## V0.1 已完成

- 目录骨架。
- 共享 Markdown 协议。
- LaTeX 模板整理和编译。
- 优秀论文 OCR 索引。
- 工具注册表。
- 环境安装入口。

## V0.2 当前版本

目标：完成多 Agent 工作流的命令式开发流。

能力：

- 机器可读状态文件。
- 题目导入。
- 数据扫描。
- 语言审批。
- A/B/C 方案文件和 Codex 方案生成提示。
- 用户审批记录。
- Claude Code 工单生成。
- Claude Code 完成报告摄取。
- Codex 审查模板和审查结果记录。
- 方案对比模板。
- 模型确认。
- 图表审批。
- 论文写入标记。
- 状态和 readiness 检查。
- PDF 题面抽取入口。
- 状态文件锁，支持多个问题并行推进时避免覆盖状态。
- 数据扫描默认跳过非数据文件，并记录 Excel 工作表总行数。

## V0.2.1 C 题实测补丁

- 支持导入本地训练题面和附件数据。
- 已为 Q1-Q4 生成 A/B/C 三套方案。
- 已验证并发 `prepare-schemes` 不再丢失状态。
- 用户反馈后确认：不能将 Q1-Q4 同时推进到审批和 Claude Code 执行。

## V0.2.2 逐问推进修正

- 正式流程改为逐问推进；当前规则要求前一问单题入文、PDF 编译和版面检查通过后才解锁下一问。
- 新增 `set-active-question`，用于设置当前解锁问题并延后后续问题。
- 新增 `create-approval-brief`，生成只面向当前问题的三方案用户审批简报。
- 新增 `create-claude-prompt`，用户选定方案后生成可直接发给 Claude Code 的提示词。
- `approve-schemes` 支持用户只选择一个或多个方案，未选方案标记为 `not_selected`。
- `create-workorder(s)` 和 `create-claude-prompt` 默认要求方案已审批，并受逐问守卫限制。
- 当前阻塞点：等待用户选择 Q1 的 A/B/C 方案。

## V0.2.3 Claude 完成监听修正

- 新增 `check-claude`，用于单次检查 Claude Code 完成报告和标准输出文件。
- 新增 `watch-claude`，用于定时轮询 Claude Code 是否完成。
- 支持检测到完成后自动摄取完成报告，并生成 Codex 审查模板。
- 首次自动检测成功后，Codex 可记录 `PASS` / `REVISE` / `BLOCKED` 并生成返修提示词。

## V0.2.4 Claude 自动调度适配器

- 新增 `dispatch-claude`，用于把正式提示词或最新返修提示词发送给 Claude Code。
- 若配置了 Claude Code CLI，通过 stdin 自动投递提示词。
- 若未配置 CLI，自动写入 `04_claude_workorders/outbox/` 队列，避免用户手动复制散落文本。
- 新增 `04_claude_workorders/claude_dispatch_config.example.json`。

## V0.2.5 VSCode Claude Code 桥接

- 新增 `dispatch-claude --mode vscode`。
- 当 Claude Code 只在 VSCode 面板中使用、没有 CLI 时，Codex 写入固定桥接文件 `04_claude_workorders/vscode_bridge/CURRENT_TASK.md`。
- 新增 `CURRENT_TASK_STATUS.json`，记录当前任务、原始提示词、预期完成报告和标准输出。
- `--mode auto` 在无 CLI 时可退化为 VSCode 桥接文件。

## V0.2.6 VSCode 插件 native binary 自动发现

- `dispatch-claude --mode auto` 会自动搜索 PATH 中的 `claude`/`claude-code`。
- 若 PATH 中没有命令，会继续搜索 VSCode/Cursor/Windsurf Claude Code 插件目录中的 `resources/native-binary/claude`。
- 当时自动发现命令使用 CLI/stdin 方式；该历史权限策略已被 V0.2.25 的可见终端、`bypassPermissions` 和 `--continue` 默认策略取代。
- 用户仍可显式使用 `--mode vscode` 保留 VSCode 面板读固定任务文件的工作方式。

## V0.2.7 VSCode 面板派发

- 新增 `dispatch-claude --mode vscode-panel`。
- Codex 仍将完整任务写入 `04_claude_workorders/vscode_bridge/CURRENT_TASK.md`，避免长提示词通过 URI 传输。
- 同时生成 `CURRENT_TASK_URI.txt`，通过 VSCode URI 打开 Claude Code 面板，并传入短指令要求读取固定任务文件。
- 该模式适合用户希望在 VSCode 面板中看见 Claude Code 会话，但又不想手动复制 Codex 长提示词的场景。

## V0.2.8 默认派发路线改为 VSCode 面板

- `dispatch-claude` 的默认 `--mode` 从 `auto` 改为 `vscode-panel`。
- 主流程文档和工具示例均改为 `--mode vscode-panel`。
- `--mode auto` 保留为无人值守后台执行路线，不再作为训练阶段默认路线。

## V0.2.9 增量论文写入与中文图规则

- 新增 `write-question-paper`：每个问题完成模型确认后，写入对应 `model_qX.tex` 并默认编译一次 PDF；最终中文图可在图表审批后补入。
- 新增 `finalize-summary-paper`：守卫摘要、模型检验、模型评价、AI 使用说明等总结性内容，未完成全部问题前不允许进入最终总结写作。
- 论文流程明确：每题入文后必须编译 `07_paper/main.pdf`。
- 图表规则明确：最终入论文图必须中文化，Claude Code 英文图只作为验收和重绘参考。

## V0.2.10 模型确认审批简报

- 新增 `create-model-confirmation-brief`。
- Codex 复审 `PASS` 后，必须先给用户模型确认选项：标准批准、带论文约束批准、不批准返修/重跑。
- 用户选择后，Codex 才能运行 `confirm-model`。

## V0.2.11 单题真实入文渲染

- `write-question-paper --question QX` 在模型确认后，可根据结果表生成真实 LaTeX 小节并编译 PDF。
- 单题小节包含模型表达式、变量定义、核心指标表、敏感性分析、误差分析和本问小结；中文图表在图表审批后补入。
- 入文图使用 Codex 审批通过的中文最终图，不直接采用 Claude Code 的英文验收图。

## V0.2.12 VSCode 面板重复打开守卫

- `dispatch-claude --mode vscode-panel` 会先读取 `CURRENT_TASK_STATUS.json`。
- 若同一 Claude Code 任务仍处于活动状态且完成报告尚未生成，默认不重复打开新的 VSCode Claude Code 面板。
- 新增 `--force-open-panel`，仅在确实需要强制新开面板时使用。

## V0.2.13 VSCode 面板复用投递

- 修正 V0.2.12 过度跳过派发的问题。
- 若同一 Claude Code 任务仍处于活动状态，`dispatch-claude --mode vscode-panel` 会复用现有面板并通过 URI 再次投递短指令，不要求用户复制粘贴。
- 若另一个未完成任务正在活动，仍默认阻止覆盖，除非显式使用 `--force-open-panel`。

## V0.2.14 已有 Claude 输入框前台粘贴

- 明确 `vscode://Anthropic.claude-code/open?prompt=...` 不能稳定定位到某个已有 editor tab 会话。
- 新增 `dispatch-claude --mode vscode-active-input --active-input-confirmed`。
- 该模式在用户确认焦点位于目标 Claude Code 输入框后，使用 macOS 前台粘贴发送短指令，避免新建 Claude main 面板。

## V0.2.15 恢复 CLI/native binary 为主派发路线

- 用户实测确认 VSCode URI 和前台粘贴路线不好用：会新开 Claude main 面板，且前台粘贴依赖焦点、剪贴板和 macOS 辅助功能权限。
- `dispatch-claude` 默认 `--mode` 从 `vscode-panel` 改回 `auto`。
- 主流程优先调用 Claude Code CLI 或 VSCode/Cursor/Windsurf 插件自带 native binary；VSCode 面板模式只保留为人工兜底和观察路线。
- 文档和工具注册表同步更新，防止后续 agent 再把 `vscode-panel` 当作稳定自动化主路线。

## V0.2.16 全局 Claude Code CLI 固定入口

- 用户决定安装全局 Claude Code，避免继续依赖 VSCode 插件私有 binary。
- base 环境已安装 Node.js/npm，并通过 npm 安装 `@anthropic-ai/claude-code`。
- 新增 `04_claude_workorders/claude_dispatch_config.json`，用于固定本机 Claude Code 调度命令；当前命令格式以 V0.2.25 为准。
- 自动发现命令默认去掉 `--ide`，避免后台执行时等待 VSCode 插件连接。
- `environment.yml` 增加 `nodejs`，`INSTALL.md` 增加 Claude Code CLI 安装说明。

## V0.2.17 Claude 实时对话面板

- 用户反馈 CLI 后台静默执行会造成不安，无法看到 Codex 与 Claude Code 的交互情况。
- `dispatch-claude` 默认生成 `04_claude_workorders/live/CURRENT_CLAUDE_DIALOGUE.md`。
- 实时面板包含发给 Claude 的提示词、Claude stdout/stderr、返回码、输出字符数和状态。
- `run_claude_command` 从 `subprocess.run(..., capture_output=True)` 改为 `subprocess.Popen` 流式读取并写入日志。
- 新增 `--no-live-log` 作为后台执行备用开关。

## V0.2.18 Claude 可见终端模式

- 用户进一步要求看到像真实终端中运行 Claude Code 一样的实时界面，同时 Codex 仍能继续对话和监听。
- 新增 `dispatch-claude --mode terminal`。
- 该模式会生成 `04_claude_workorders/terminal_runs/*.sh`，打开 macOS Terminal 并运行交互式 Claude Code。
- 当时默认让权限审批显示在终端中由用户处理；当前本地训练默认已在 V0.2.25 改为 `bypassPermissions`，减少重复点击。
- 终端状态写入 `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`。

## V0.2.19 调度瘦身与图表版面守卫

- 删除当前接口中的 VSCode URI、前台粘贴、固定桥接文件和 outbox 队列路线。
- `dispatch-claude --mode auto` 固定为可见终端路线；`--mode terminal` 显式等价；`--mode cli` 仅作后台备用。
- 删除旧的 VSCode 双面板说明，新增 `08_agent_design/CLAUDE_TERMINAL_WORKFLOW.md`。
- 图表规范新增硬约束：最多双子图、禁止四宫格诊断面板、控制单图宽高、禁止整页堆图。
- Q1 论文图 4 从四宫格改为单结论敏感性图，模型检验内容改入表格；LaTeX 浮动参数收紧以保持图文交错。

## V0.2.20 PDF 版面自动验收

- 新增 `layout-check`，用于扫描 `07_paper/main.pdf` 内部异常大空白。
- `layout-check` 支持 `--expect-label-page label=page`，可将“图 3 必须在第 5 页”这类版面要求写成机器约束。
- `latex-check` 默认在编译后执行版面检查；必要时可使用 `--skip-layout-check` 临时跳过。

## V0.2.21 Claude 可见监控终端

- 新增 `open-claude-monitor`，用于打开 Claude 任务状态监控终端。
- 监控终端循环显示 `CURRENT_TERMINAL_STATUS.json`、完成报告和标准输出文件状态，解决用户无法直观看到 Codex 如何判断 Claude 是否完成的问题。
- `dispatch-claude --mode auto/terminal` 仍是唯一正式可见执行路线；监控终端只观察，不执行或修改建模结果。

## V0.2.22 VS Code 集成终端任务

- 新增 `install-vscode-tasks`，生成 `.vscode/tasks.json` 中的 Claude 执行、监控和一键可见会话任务。
- 推荐给希望留在 VS Code 面板内观察的用户运行 `Math Magic: Claude QX-B visible session`，该任务并行打开 Claude 执行终端和监控终端。
- 该路线替代旧的 VS Code Claude 插件 URI/自动粘贴方案，不依赖焦点、剪贴板或已有 Claude 面板。

## V0.2.23 审批选项必须显式呈现

- `create-approval-brief` 和 `create-model-confirmation-brief` 不再只输出文件路径，而是直接输出完整用户审批选项。
- 命令输出追加 `ACTION_REQUIRED`，提醒 Codex 必须在聊天中转述选项并等待审批。
- 工作流协议明确：只写文件、只给路径或让用户自行打开文件，不算完成审批告知。

## V0.2.24 Windows 交付与图表洁净规则

- VS Code 任务生成支持 `--target-os windows`，可生成 PowerShell 版 Claude 执行和监控脚本。
- 新增 `doctor` 一键自检，检查环境、工具、Claude Code、VS Code smoke task、LaTeX 模板和优秀论文资源。
- 最终论文图表规则新增：禁止图内底部长批注，禁止红色虚线参考线/阈值线/边界线；解释条件转入正文、图注或表格备注。

## V0.2.25 Windows 可见终端与兼容性修正

- `environment.yml` 不再固定 Python 小版本，只声明 `python`，由用户本机或 conda 环境解析可用版本。
- `agentctl.py` 保持对较旧 Python/PowerShell 的兼容写法：布尔参数兼容无 `BooleanOptionalAction` 的环境，Windows 状态脚本避免依赖 `ConvertFrom-Json -AsHashtable`。
- `dispatch-claude --mode auto/terminal` 默认在当前项目根目录打开可见终端运行 Claude Code。
- Claude Code 默认使用 `bypassPermissions` 和 `--dangerously-skip-permissions`，适配本地可信训练工作流，减少逐次权限点击。
- Claude Code 默认追加 `--continue`，复用当前项目目录下最近的 Claude Code 会话上下文；只有显式 `--claude-session-mode new` 才开启新上下文。
- 新增 `dispatch-claude --no-open`，用于只生成并检查终端脚本，不立即打开 Claude。
- 终端状态区分 `terminal_script_created`、`running`、`finished`，并记录 `run_started_at`；`check-claude` 只在 Claude 实际运行后才用新鲜度时间过滤输出，避免预生成脚本把旧结果误判为 stale。
- PowerShell 脚本以 UTF-8 BOM 写入，避免中文 Windows 用户名在 Claude binary 路径中乱码。

## V0.2.26 旧题产物归档与防污染

- 新增 `archive-stale-artifacts`，用于归档疑似旧题/旧主题生成物，默认先 dry-run；显式加 `--force` 后才移动文件。
- `import-problem` 默认在导入新题前归档上一题生成物；可用 `--no-archive-existing-generated` 显式关闭。
- 归档文件移动到 `00_shared/archive/stale_artifacts/<timestamp>/`，同时生成 `manifest.json` 和 `manifest.md`，便于审计和回滚。
- 检测逻辑使用旧主题关键词与当前题面关键词的证据比较，避免当前完成报告因提到“已清理旧文件”而被误归档。
- 归档论文问题小节后自动补回占位 `model_qX.tex`，避免 LaTeX 主文件因旧正文移走而断编译。
- 真实运行验证了旧题产物归档机制；分发模板不保留具体题目的归档内容。

## V0.2.27 小问即入文编译

- `write-question-paper` 默认不再要求图表审批；模型确认后即可写入对应小问正文、公式和结果表，并立即编译 PDF。
- 新增 `write-question-paper --require-figures-approved`，用于需要恢复旧式严格图表门禁的场景。
- `finalize-summary-paper` 的总结性守卫扩展到论文 AI 使用说明，摘要、全局评价和 AI 使用说明必须等全部小问入文后统一整理。
- 逐问推进依赖从 `model_confirmed` 收紧为 `paper_written`：前一问未成功编译入文前，不解锁后一问。
- LaTeX class 新增 Windows/macOS/Fandol 中文字体自动兜底，避免 Windows 安装 `xelatex` 后仍因 macOS 字体名失败。
- 分发模板不内置具体测试题；新用户导入题目后可用任一已确认小问验证“小问入文编译”流程。

## V0.3 待 Claude Code 实验后开发

真实题目跑通后，根据暴露的问题继续完善：

- 针对题型选择优秀论文深读。
- 自动生成更强的 Claude Code 工单上下文。
- 自动检查代码输出文件是否齐全。
- 自动生成图表插入 LaTeX 片段。
- 自动整理代码附录。
- 自动生成最终提交包检查清单。
- 自动对比三套方案的指标、稳定性、论文可写性并给出模型确认建议。
