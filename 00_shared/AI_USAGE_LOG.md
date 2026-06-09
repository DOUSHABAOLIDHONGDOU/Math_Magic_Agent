# AI Usage Log

本文件用于记录 Codex 和 Claude Code 的关键使用情况，后续可整理为 AI 使用说明和支撑材料。

## 记录模板

```markdown
## AILOG-000

- 日期：
- 工具：Codex / Claude Code / 其他
- 用途：
- 输入摘要：
- 输出摘要：
- 采纳情况：全部采纳 / 部分采纳 / 未采纳
- 人工修改：
- 关联文件：
- 备注：
```

## AILOG-001

- 日期：2026-06-08
- 工具：Codex
- 用途：设计赛前训练用多 Agent 数学建模工作流。
- 输入摘要：用户说明希望由 Codex 负责建模分析、论文写作、图表插入和验收，由 Claude Code 负责代码实现和调试。
- 输出摘要：建立项目目录、共享状态文件、决策日志、工单模板和评分表。
- 采纳情况：全部采纳。
- 人工修改：待后续补充。
- 关联文件：`00_shared/`, `02_references/`, `04_claude_workorders/`, `08_agent_design/`
- 备注：赛前训练场景。

## AILOG-002

- 日期：2026-06-08
- 工具：Codex
- 用途：解压并整理 LaTeX 模板和历年优秀论文 PDF。
- 输入摘要：项目根目录中的 `数模latex模版.zip` 和 `math_exmaple.zip`。
- 输出摘要：优秀论文解压到 `02_references/excellent_papers/`，LaTeX 模板解压到 `07_paper/template_raw/` 并复制工作版到 `07_paper/`。
- 采纳情况：全部采纳。
- 人工修改：将 `main.tex` 改为模块化论文骨架。
- 关联文件：`02_references/excellent_papers/`, `07_paper/main.tex`, `07_paper/sections/`, `07_paper/appendix/`
- 备注：模板内嵌 zip 使用 `bsdtar` 处理中文文件名。

## AILOG-003

- 日期：2026-06-08
- 工具：Codex
- 用途：整理并验证工作版 LaTeX 论文骨架。
- 输入摘要：`07_paper/template_raw/SJT-code/main.tex` 和 `JXUSTmodeling.cls`。
- 输出摘要：将论文拆分为 `sections/` 与 `appendix/`，修复 macOS 中文字体配置，并成功编译生成 `07_paper/main.pdf`。
- 采纳情况：全部采纳。
- 人工修改：将模板字体从默认 mac 字体集改为显式中文字体映射。
- 关联文件：`07_paper/main.tex`, `07_paper/JXUSTmodeling.cls`, `07_paper/sections/`, `07_paper/appendix/`
- 备注：编译命令为 `xelatex -interaction=nonstopmode -halt-on-error main.tex`。

## AILOG-004

- 日期：2026-06-08
- 工具：Codex + imagegen skill 文档
- 用途：制定论文图表和生图资产生成规范。
- 输入摘要：用户要求 Codex 负责最终图表生成与插入，并在必要时使用生图技能。
- 输出摘要：补充真实数据图与结构示意图的分轨规则，新增 imagegen 项目资产保存和审批规范。
- 采纳情况：全部采纳。
- 人工修改：未生成实际图片，仅建立规则和模板。
- 关联文件：`07_paper/figure_generation_workflow.md`, `04_claude_workorders/templates/codex_figure_task_template.md`
- 备注：真实数值图不得由生图替代。

## AILOG-005

- 日期：2026-06-08
- 工具：Codex
- 用途：配置 PDF OCR 和数模 Python 环境。
- 输入摘要：优秀论文 PDF 为扫描版，直接文本抽取结果为空。
- 输出摘要：在 conda base 安装并验证 `pypdf`, `pymupdf`, `tesseract`, `pytesseract`, `numpy`, `pandas`, `matplotlib`, `seaborn`, `scipy`, `scikit-learn`, `openpyxl`, `xlrd`, `statsmodels`, `networkx`。
- 采纳情况：全部采纳。
- 人工修改：接受 Anaconda 默认源 ToS 后使用 conda-forge 安装 OCR 依赖。
- 关联文件：`08_agent_design/ENVIRONMENT_SETUP.md`
- 备注：Tesseract 已确认包含 `chi_sim` 和 `eng`。

## AILOG-006

- 日期：2026-06-08
- 工具：Codex + OCR
- 用途：建立优秀论文风格索引。
- 输入摘要：`02_references/excellent_papers/` 下 23 篇优秀论文 PDF。
- 输出摘要：生成结构索引、CSV 统计和优秀论文风格约束。
- 采纳情况：全部采纳。
- 人工修改：将 OCR 观察整理为论文写作约束。
- 关联文件：`05_code/tools/pdf_style_extractor.py`, `02_references/excellent_papers_style_signals.md`, `02_references/excellent_papers_style_signals.csv`, `02_references/paper_style_guide.md`
- 备注：默认轻量 OCR 每篇前 3 页和后 2 页；深读时再针对特定论文全篇 OCR。

## AILOG-007

- 日期：2026-06-08
- 工具：Codex
- 用途：建立多 Agent 工作流轻量控制脚本。
- 输入摘要：用户希望先跑通一次，再开发成 agent。
- 输出摘要：新增 `agentctl.py`，支持环境检查、状态读取、工单生成和 LaTeX 编译。
- 采纳情况：全部采纳。
- 人工修改：已通过临时工单、环境检查和 LaTeX 编译验证。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/README.md`, `08_agent_design/AGENT_SPEC.md`
- 备注：这是 agent 编排器的最小雏形。

## AILOG-008

- 日期：2026-06-08
- 工具：Codex
- 用途：建立可复现依赖安装入口和工具注册表。
- 输入摘要：用户要求开发智能体时维护 tools，让数学建模工作流能执行下去，并方便他人直接安装依赖。
- 输出摘要：新增 conda 环境文件、pip requirements、安装说明、机器可读工具注册表和人类可读工具注册表，并扩展 `agentctl.py tools` 命令。
- 采纳情况：全部采纳。
- 人工修改：已验证 `agentctl.py tools` 和 `agentctl.py env-check`。
- 关联文件：`environment.yml`, `requirements.txt`, `INSTALL.md`, `05_code/tools/tool_registry.json`, `08_agent_design/TOOL_REGISTRY.md`, `05_code/tools/agentctl.py`
- 备注：后续新增工具或依赖时必须同步维护注册表和安装文件。

## AILOG-009

- 日期：2026-06-08
- 工具：Codex
- 用途：开发 V0.2 命令式 agent 工作流。
- 输入摘要：用户要求继续完成整套 agent 开发流，后续将提供一套题进行测试和完善验证。
- 输出摘要：扩展 `agentctl.py`，新增机器可读状态文件、题目导入、数据扫描、语言审批、方案准备、方案审批、Claude 工单生成、完成报告摄取、Codex 审查、方案对比、模型确认、图表审批、论文写入标记、论文检查和 readiness 命令。
- 采纳情况：全部采纳。
- 人工修改：已验证语法、工具注册表 JSON、工具读取、readiness、paper-check、latex-check 和临时工单生成。
- 关联文件：`05_code/tools/agentctl.py`, `00_shared/workflow_state.json`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/VERSION_PLAN.md`, `05_code/tools/tool_registry.json`
- 备注：未用假题运行导入流程，避免污染真实测试前状态。

## AILOG-AUTO-2026-06-08T17:24:36 题目导入

- 日期：2026-06-08
- 工具：agentctl import-problem
- 用途：导入训练题目 `C题 NIPT 的时点选择与胎儿的异常判定`。
- 关联文件：`01_problem/problem_statement.md`

## AILOG-010

- 日期：2026-06-08
- 工具：Codex + `problem_statement_extractor.py` + `agentctl.py`
- 用途：用 CUMCM2025 题包进行首次真实题目入口测试。
- 输入摘要：`CUMCM2025Problems.zip`，选择 C 题作为首轮端到端测试题，包含 `C题.pdf` 和 `附件.xlsx`。
- 输出摘要：解压 GBK 文件名题包，抽取 C 题题面为 Markdown，导入题面，扫描 Excel 数据字典，确认 C 题包含 Q1-Q4 四问。
- 采纳情况：全部采纳。
- 人工修改：首轮默认选择 C 题；如用户要求可切换 A/B/D/E 题重新导入。
- 关联文件：`01_problem/source/CUMCM2025Problems/C题/C题_statement.md`, `01_problem/problem_statement.md`, `01_problem/data_dictionary.md`
- 备注：男胎检测数据 1082 行，女胎检测数据 605 行。

## AILOG-011

- 日期：2026-06-08
- 工具：Codex
- 用途：为 CUMCM2025 C 题 Q1-Q4 生成 A/B/C 三套建模方案。
- 输入摘要：C 题题面、数据字典、优秀论文风格约束和数学建模评分表。
- 输出摘要：Q1-Q4 均生成稳健解释型、竞赛均衡型、冲奖增强型三套方案，覆盖数学模型、数据需求、预期图表、敏感性分析、误差分析和 Claude Code 实现提示。
- 采纳情况：等待用户审批。
- 人工修改：未生成 Claude Code 工单，遵守方案审批边界。
- 关联文件：`03_methods/Q1/scheme_A.md`, `03_methods/Q1/scheme_B.md`, `03_methods/Q1/scheme_C.md`, `03_methods/Q2/scheme_A.md`, `03_methods/Q2/scheme_B.md`, `03_methods/Q2/scheme_C.md`, `03_methods/Q3/scheme_A.md`, `03_methods/Q3/scheme_B.md`, `03_methods/Q3/scheme_C.md`, `03_methods/Q4/scheme_A.md`, `03_methods/Q4/scheme_B.md`, `03_methods/Q4/scheme_C.md`
- 备注：该说法已被 AILOG-013 修正；正式流程改为逐问推进，由用户先选择当前问题方案。

## AILOG-012

- 日期：2026-06-08
- 工具：Codex
- 用途：修复多 Agent 并行状态写入风险。
- 输入摘要：并行运行 Q1-Q4 `prepare-schemes` 时，Markdown 方案文件均存在，但机器状态只记录 Q4。
- 输出摘要：`agentctl.py` 增加工作流状态文件锁，已有方案文件不覆盖只补录状态，artifact 按 kind/path/note 去重，数据扫描默认跳过非数据文件并记录 Excel 工作表总行数。
- 采纳情况：全部采纳。
- 人工修改：重新并行补录 Q1-Q4 状态并验证 readiness。
- 关联文件：`05_code/tools/agentctl.py`, `00_shared/workflow_state.json`, `01_problem/data_dictionary.md`
- 备注：这是多 agent 并行工作流的关键稳定性修复。

## AILOG-013

- 日期：2026-06-08
- 工具：Codex
- 用途：根据用户反馈修正数学建模 agent 的推进逻辑。
- 输入摘要：用户指出不能一次性把 Q1-Q3/Q4 都推进到三方案审批和 Claude Code 执行，因为后续问题可能依赖前一问结果；方案审批应先给用户当前问题的三方案选择，再生成给 Claude Code 的提示词。
- 输出摘要：正式流程改为逐问推进，新增当前问题守卫、审批简报生成、Claude Code 提示词生成，Q2-Q4 状态改为等待前序模型确认。
- 采纳情况：全部采纳。
- 人工修改：保留已生成的 Q2-Q4 文件作为预分析草稿，不进入正式审批。
- 关联文件：`05_code/tools/agentctl.py`, `03_methods/Q1/approval_brief.md`, `00_shared/WORKFLOW_PROTOCOL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `00_shared/PROJECT_STATE.md`
- 备注：当前阻塞点改为用户选择 Q1 的 A/B/C 方案。

## AILOG-014

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：记录 Q1 方案审批并生成 Claude Code 执行提示词。
- 输入摘要：用户选择 Q1 方案 B，理由为主力方案，先交给 Claude Code 执行。
- 输出摘要：记录决策 `D-005`，生成 Q1-B 工单和可直接发给 Claude Code 的提示词。
- 采纳情况：全部采纳。
- 人工修改：补强 Q1-B 工单中的已批准建模路线，明确不允许推进 Q2/Q3/Q4。
- 关联文件：`04_claude_workorders/Q1_scheme_B_claude_prompt.md`, `04_claude_workorders/Q1_scheme_B_workorder_001.md`, `03_methods/Q1/scheme_B.md`, `00_shared/DECISION_LOG.md`, `00_shared/PROJECT_STATE.md`
- 备注：下一步等待 Claude Code 输出完成报告 `04_claude_workorders/completions/Q1_scheme_B_completion.md`。

## AILOG-015

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：补齐 Claude Code 完成状态的自动检测机制。
- 输入摘要：用户指出 Codex 不应依赖用户通知 Claude Code 已完成，工作流需要定时监控完成报告和结果文件。
- 输出摘要：新增 `check-claude` 单次检查命令和 `watch-claude` 定时轮询命令；本次已自动检测并摄取 Q1-B 完成报告，生成 Codex 审查模板。
- 采纳情况：全部采纳。
- 人工修改：将项目状态从“等待 Claude 执行”推进到“等待 Codex 审查”。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/completions/Q1_scheme_B_completion.md`, `06_results/Q1/logs/scheme_B_codex_review.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`
- 备注：以后 Claude Code 执行期间应运行 `watch-claude --ingest --create-review --require-standard-outputs`。

## AILOG-016

- 日期：2026-06-08
- 工具：Codex
- 用途：审查 Claude Code 的 Q1-B 代码和结果。
- 输入摘要：`05_code/Q1/q1_scheme_B.py`、Q1-B 完成报告、输出表格、输出图表和运行日志。
- 输出摘要：审查结论为 `REVISE`，主要问题包括交叉验证预处理泄漏、BMI bootstrap 置信带异常、孕周上限与题面不一致、Matplotlib 缓存设置顺序错误。
- 采纳情况：退回 Claude Code 修订。
- 人工修改：生成返修提示词 `04_claude_workorders/Q1_scheme_B_revision_prompt_001.md`。
- 关联文件：`06_results/Q1/logs/scheme_B_codex_review.md`, `04_claude_workorders/Q1_scheme_B_revision_prompt_001.md`, `00_shared/PROJECT_STATE.md`
- 备注：返修后继续使用 `watch-claude` 自动检测完成。

## AILOG-017

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：补齐向 Claude Code 自动投递提示词的调度机制。
- 输入摘要：用户指出复制提示词给 Claude Code 仍然繁琐，希望自动化。
- 输出摘要：新增 `dispatch-claude`，支持配置 Claude Code CLI 后通过 stdin 自动投递；未配置 CLI 时写入 `04_claude_workorders/outbox/` 队列。当前 Q1-B 返修任务已进入 outbox。
- 采纳情况：全部采纳。
- 人工修改：新增 Claude dispatch 配置示例，并更新工具注册表和工作流文档。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/claude_dispatch_config.example.json`, `04_claude_workorders/outbox/20260608_184502_Q1_scheme_B_Q1_scheme_B_revision_prompt_001.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `05_code/tools/tool_registry.json`
- 备注：本机当前未检测到 `claude` 或 `claude-code` 命令，因此本次使用 outbox 队列模式。

## AILOG-AUTO-2026-06-08T18:45:02 Claude dispatch queued

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q1` 方案 `B` 提示词放入 Claude Code outbox。
- 关联文件：`04_claude_workorders/outbox/20260608_184502_Q1_scheme_B_Q1_scheme_B_revision_prompt_001.md`

## AILOG-018

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：适配用户在 VSCode 内使用 Claude Code、没有终端 CLI 的实际工作方式。
- 输入摘要：用户说明没有 `claude` 命令的原因是 Claude Code 直接运行在 VSCode 中。
- 输出摘要：新增 `dispatch-claude --mode vscode`，`auto` 模式在未配置 CLI 时写入固定桥接文件 `04_claude_workorders/vscode_bridge/CURRENT_TASK.md`，并生成状态文件 `CURRENT_TASK_STATUS.json`。
- 采纳情况：全部采纳。
- 人工修改：同步工具说明、工具注册表和项目状态。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`, `04_claude_workorders/vscode_bridge/README.md`, `05_code/tools/README.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`
- 备注：VSCode 插件若不暴露 CLI/API，Codex 无法直接把文本注入 Claude Code 面板；固定文件桥接可把每次长提示词复制缩短为一次固定读文件指令。

## AILOG-AUTO-2026-06-08T18:50:34 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q1` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-019

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：识别 VSCode Claude Code 插件自带 native binary，并接入自动调度。
- 输入摘要：用户说明已在 VSCode 中安装 Claude Code 插件。
- 输出摘要：本机插件路径为 `/Users/lwb/.vscode/extensions/anthropic.claude-code-2.1.168-darwin-arm64`，其中包含可执行文件 `resources/native-binary/claude`；`dispatch-claude --mode auto` 已支持自动发现该二进制并使用 `-p --ide --permission-mode acceptEdits` 进行非交互调度。
- 采纳情况：全部采纳。
- 人工修改：更新 dispatch 配置示例、工具说明、工作流命令文档和项目状态。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/claude_dispatch_config.example.json`, `05_code/tools/README.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `00_shared/PROJECT_STATE.md`
- 备注：若用户希望仍在 VSCode 面板中手动启动，可显式使用 `dispatch-claude --mode vscode`。

## AILOG-020

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：停止重复自动派发，转为验收用户手动投递 Claude Code 后生成的 Q1-B v2 结果。
- 输入摘要：用户说明已手动复制粘贴并投用 Claude Code 返修提示词。
- 输出摘要：Codex 终止误触发的自动派发进程，只保留用户 VSCode Claude Code 任务；随后检测到 Q1-B v2 完成报告和标准输出，完成代码、表格、图表、日志复审，结论为 `PASS`。
- 采纳情况：全部采纳。
- 人工修改：写入正式复审记录并将机器状态标记为 `Q1 B: PASS`。
- 关联文件：`04_claude_workorders/completions/Q1_scheme_B_completion.md`, `05_code/Q1/q1_scheme_B.py`, `06_results/Q1/logs/scheme_B_codex_review.md`, `06_results/Q1/tables/scheme_B_metrics.csv`, `06_results/Q1/figures/scheme_B_raw.png`, `00_shared/workflow_state.json`
- 备注：Q1-B v2 可进入模型确认审批；最终论文图表仍建议由 Codex 统一重绘成中文 CUMCM 风格。

## AILOG-021

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：解决“不要复制 Codex 长提示词到 Claude Code，同时希望在 VSCode 面板中看到 Claude Code 会话”的工作流问题。
- 输入摘要：用户希望减少 Codex 到 Claude Code 的手动复制，并希望在 VSCode 面板中同时观察 Claude Code 与 Codex。
- 输出摘要：新增 `dispatch-claude --mode vscode-panel`，该模式写入固定任务文件后生成 VSCode URI，打开 Claude Code 面板并传入短指令；新增 VSCode 双面板工作流说明。
- 采纳情况：全部采纳。
- 人工修改：更新工具脚本、工具注册表、工作流命令文档和 VSCode 双面板说明。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/vscode_bridge/README.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `05_code/tools/tool_registry.json`
- 备注：`--mode auto` 适合无人值守执行；若需要 Claude 会话在 VSCode 面板可见，推荐 `--mode vscode-panel`。

## AILOG-022

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：将 Claude Code 主派发路线从 `auto` 改为 `vscode-panel`。
- 输入摘要：用户要求直接把主路线改成 `--mode vscode-panel`。
- 输出摘要：`dispatch-claude` 默认模式已改为 `vscode-panel`，工具示例和工作流文档也同步改为 VSCode 面板派发；`auto` 保留为无人值守后台执行。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/README.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `05_code/tools/tool_registry.json`
- 备注：后续生成 Claude Code 工单时，若不显式传 `--mode`，默认打开 VSCode Claude Code 面板并让其读取固定任务文件。

## AILOG-023

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：补齐每题入文、每题编译和中文最终图规则。
- 输入摘要：用户指出每完成一个问题后应将该问题内容和图片插入 LaTeX，并立即编译 PDF；摘要等总结性内容必须等全部问题完成后再填写；最终论文图像应为中文。
- 输出摘要：新增 `write-question-paper` 和 `finalize-summary-paper`，更新论文增量写入流程、图表生成规则、优秀论文风格约束和共享协议。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `07_paper/incremental_paper_workflow.md`, `07_paper/figure_generation_workflow.md`, `07_paper/figure_insertion_rules.md`, `00_shared/WORKFLOW_PROTOCOL.md`, `02_references/paper_style_guide.md`
- 备注：当前 Q1 仍处于模型确认待审批；确认模型并完成中文图审批后，才进入 `write-question-paper --question Q1`。

## AILOG-024

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：补齐模型确认审批选项。
- 输入摘要：用户指出 Codex 没有给出 Q1 模型确认的可选项。
- 输出摘要：新增 `create-model-confirmation-brief`，在 Codex 复审 PASS 后生成用户可读的模型确认选项；Q1 已生成 `03_methods/Q1/model_confirmation_brief.md`。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `03_methods/Q1/model_confirmation_brief.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `05_code/tools/tool_registry.json`, `00_shared/WORKFLOW_PROTOCOL.md`
- 备注：模型确认选项分为标准批准、带论文约束批准、不批准返修/重跑。

## AILOG-025

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：记录 Q1 最终模型确认。
- 输入摘要：用户选择 Q1 模型确认选项 1，即标准批准 Q1-B v2。
- 输出摘要：执行 `confirm-model --question Q1 --scheme B`，将 Q1-B v2 记录为 Q1 最终模型，决策 ID `D-006`；同步更新共享项目状态。
- 采纳情况：全部采纳。
- 关联文件：`00_shared/workflow_state.json`, `03_methods/Q1/approved.md`, `00_shared/DECISION_LOG.md`, `00_shared/PROJECT_STATE.md`
- 备注：Q1 下一步进入中文最终图生成和图表审批；Q2 已在机器状态中解锁。

## AILOG-026

- 日期：2026-06-08
- 工具：Codex + Python 绘图脚本
- 用途：生成 Q1 中文最终候选图并提交图表审批。
- 输入摘要：用户已确认 Q1-B v2 为最终模型，要求最终论文图表由 Codex 生成并使用中文表达。
- 输出摘要：新增 `05_code/Q1/q1_final_figures.py`，基于 Q1 复审通过的结果表重绘 5 张中文候选图，生成审批总览图和图表审批简报。
- 采纳情况：全部采纳，用户已审批通过。
- 关联文件：`05_code/Q1/q1_final_figures.py`, `07_paper/figures/q1_fig1_gestation_effect.png`, `07_paper/figures/q1_fig2_bmi_effect.png`, `07_paper/figures/q1_fig3_gestation_bmi_surface.png`, `07_paper/figures/q1_fig4_validation_sensitivity.png`, `07_paper/figures/q1_fig5_model_flow.png`, `03_methods/Q1/figure_approval_brief.md`, `03_methods/Q1/q1_figure_approval_sheet.png`
- 备注：用户随后批准全部 Q1 图表，进入论文写入。

## AILOG-027

- 日期：2026-06-08
- 工具：Codex + `agentctl.py` + XeLaTeX
- 用途：记录 Q1 图表审批通过、论文小节写入和 PDF 编译。
- 输入摘要：用户回复“审批全部通过”，即批准 Q1 全部中文最终候选图。
- 输出摘要：执行 `approve-figures --question Q1`，记录图表审批决策 `D-007`；将 `agentctl.py` 升级到 `0.2.11`，使 `write-question-paper --question Q1` 能根据 Q1 结果表生成真实 LaTeX 小节；写入 `07_paper/sections/model_q1.tex` 并成功编译 `07_paper/main.pdf`。
- 采纳情况：全部采纳。
- 关联文件：`00_shared/workflow_state.json`, `00_shared/DECISION_LOG.md`, `07_paper/sections/model_q1.tex`, `07_paper/main.pdf`, `05_code/tools/agentctl.py`, `05_code/tools/tool_registry.json`, `08_agent_design/VERSION_PLAN.md`
- 备注：二次编译后未发现未定义引用；日志仅保留字体替代和宏包兼容性常规警告。

## AILOG-028

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：生成 Q2 方案审批单。
- 输入摘要：Q1 已完成三次审批和论文入文，工作流解锁 Q2。
- 输出摘要：生成并校正 `03_methods/Q2/approval_brief.md`，给出 Q2 的 A/B/C 三套方案和 Codex 建议。
- 采纳情况：待用户审批。
- 关联文件：`03_methods/Q2/approval_brief.md`, `03_methods/Q2/scheme_A.md`, `03_methods/Q2/scheme_B.md`, `03_methods/Q2/scheme_C.md`
- 备注：Codex 推荐 Q2 先执行方案 B，但尚未记录任何 Q2 方案审批。

## AILOG-029

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：记录 Q2 方案审批并生成 Claude Code 工单。
- 输入摘要：用户回复“那就选方案2”，按 Q2 审批简报解释为选择方案 B。
- 输出摘要：执行 `approve-schemes --question Q2 --schemes B`，记录方案审批决策 `D-008`；生成 `Q2_scheme_B_claude_prompt.md` 和 `Q2_scheme_B_workorder_001.md`，并补强工单中承接 Q1 已确认模型、数据驱动 BMI 最优分组、经验分组基准对比和敏感性分析的要求。
- 采纳情况：全部采纳。
- 关联文件：`00_shared/workflow_state.json`, `00_shared/DECISION_LOG.md`, `03_methods/Q2/approved.md`, `04_claude_workorders/Q2_scheme_B_workorder_001.md`, `04_claude_workorders/Q2_scheme_B_claude_prompt.md`, `00_shared/PROJECT_STATE.md`
- 备注：下一步由 Claude Code 执行 Q2-B；Codex 等待完成报告后进行审查。

## AILOG-030

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：修复 VSCode Claude Code 面板重复打开问题。
- 输入摘要：用户指出已经打开了 Claude Code 对话面板，Codex 再派发任务时应先检查是否已有面板/活动任务。
- 输出摘要：将 `agentctl.py` 升级到 `0.2.12`，新增 `CURRENT_TASK_STATUS.json` 活动任务检查；同一任务未完成时，`dispatch-claude --mode vscode-panel` 默认不重复打开新面板，只刷新任务文件和 URI；新增 `--force-open-panel` 用于强制新开。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/tool_registry.json`, `05_code/tools/README.md`, `04_claude_workorders/vscode_bridge/README.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`
- 备注：已用 Q2-B 重复派发回归测试，输出 `skipped_existing_panel`，未重复打开 VSCode 面板。

## AILOG-031

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：修正 VSCode 面板守卫导致仍需人工粘贴的问题。
- 输入摘要：用户指出既然已实现自动派发，就不应再要求用户把短指令粘贴到 Claude Code 对话中。
- 输出摘要：将 `agentctl.py` 升级到 `0.2.13`；同一 Claude Code 任务已活动时，`dispatch-claude --mode vscode-panel` 改为复用现有面板并通过 URI 再次投递短指令；仅当另一个未完成任务活动时才阻止覆盖。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/tool_registry.json`, `05_code/tools/README.md`, `04_claude_workorders/vscode_bridge/README.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`
- 备注：目标行为是不让用户复制粘贴 Codex 提示词；由 Codex 写入 `CURRENT_TASK.md` 并通过 VSCode URI 投递短指令。

## AILOG-032

- 日期：2026-06-08
- 工具：Codex + `agentctl.py`
- 用途：新增已有 Claude Code 对话输入框的前台粘贴模式。
- 输入摘要：用户截图指出 `vscode-panel` URI 实际打开了 Claude main 面板，没有粘贴到已经打开的 Claude Code editor tab。
- 输出摘要：确认 Claude Code 扩展的 `open?prompt` URI 不能稳定定向到某个已有会话输入框；将 `agentctl.py` 升级到 `0.2.14`，新增 `dispatch-claude --mode vscode-active-input --active-input-confirmed`，用于在用户确认焦点位于目标 Claude 输入框后粘贴并发送短指令。
- 采纳情况：全部采纳。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/tool_registry.json`, `05_code/tools/README.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`
- 备注：该模式依赖前台焦点，默认不会自动运行，避免误粘贴到 Codex 输入框。

## AILOG-AUTO-2026-06-08T23:27:07 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-AUTO-2026-06-08T23:27:07 Claude dispatch vscode panel

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：生成 VSCode Claude Code 面板 URI，用短指令打开 `Q2` 方案 `B` 当前任务。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_URI.txt`

## AILOG-AUTO-2026-06-08T23:27:43 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-AUTO-2026-06-08T23:27:43 Claude dispatch vscode panel

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：生成 VSCode Claude Code 面板 URI，用短指令打开 `Q2` 方案 `B` 当前任务。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_URI.txt`

## AILOG-AUTO-2026-06-08T23:33:14 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-AUTO-2026-06-08T23:33:14 Claude dispatch vscode panel

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：生成 VSCode Claude Code 面板 URI，用短指令打开 `Q2` 方案 `B` 当前任务。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_URI.txt`

## AILOG-AUTO-2026-06-08T23:41:41 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-AUTO-2026-06-08T23:41:41 Claude dispatch vscode panel

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：生成 VSCode Claude Code 面板 URI，用短指令打开 `Q2` 方案 `B` 当前任务。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_URI.txt`

## AILOG-AUTO-2026-06-08T23:51:13 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-AUTO-2026-06-08T23:52:28 Claude dispatch vscode bridge

- 日期：2026-06-08
- 工具：agentctl dispatch-claude
- 用途：将 `Q2` 方案 `B` 提示词写入 VSCode Claude Code 固定任务文件。
- 关联文件：`04_claude_workorders/vscode_bridge/CURRENT_TASK.md`, `04_claude_workorders/vscode_bridge/CURRENT_TASK_STATUS.json`

## AILOG-034 Claude dispatch route rollback to CLI

- 日期：2026-06-08
- 工具：Codex / agentctl
- 用途：根据用户实测反馈，停止把 VSCode 面板 URI 和前台粘贴作为主派发路线。
- 输入摘要：用户指出该方法不好用；此前实测出现新开 Claude main 面板、无法投递到既有 Claude Code 对话、前台粘贴依赖 macOS 辅助功能权限等问题。
- 输出摘要：将 `dispatch-claude` 默认模式从 `vscode-panel` 改回 `auto`；主流程优先使用 Claude Code CLI 或插件 native binary，VSCode 相关模式仅作为人工兜底和观察用途。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/tool_registry.json`, `05_code/tools/README.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`
- 备注：后续 Q2-B 及返修任务应优先通过 CLI/native binary 执行，再由 `watch-claude` 轮询完成报告。

## AILOG-035 Global Claude Code CLI installed

- 日期：2026-06-09
- 工具：Codex / conda / npm / agentctl
- 用途：根据用户最新决策，安装全局 Claude Code CLI，并将其作为数学建模 agent 的主执行入口。
- 输入摘要：用户确认“干脆直接装一个全局的 Claude Code”，不再依赖 VSCode 插件内置 Claude。
- 输出摘要：base 环境已安装 Node.js/npm；`@anthropic-ai/claude-code` 已安装到 conda base 全局 npm 前缀；`claude --version` 返回 `2.1.169 (Claude Code)`；新增 `04_claude_workorders/claude_dispatch_config.json`，命令固定为 `claude -p --permission-mode acceptEdits`；自动发现默认命令去掉 `--ide`。
- 关联文件：`environment.yml`, `INSTALL.md`, `05_code/tools/agentctl.py`, `04_claude_workorders/claude_dispatch_config.json`, `04_claude_workorders/claude_dispatch_config.example.json`, `05_code/tools/tool_registry.json`, `00_shared/PROJECT_STATE.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`
- 备注：VSCode Claude Code 插件仍可作为人工观察和兜底，但不再作为自动派发主入口。

## AILOG-036 Claude live dialogue panel

- 日期：2026-06-09
- 工具：Codex / agentctl
- 用途：解决 Claude CLI 后台执行时用户无法看到 Codex 与 Claude Code 交互过程的问题。
- 输入摘要：用户反馈“想看到你与 Claude Code 的对话情况，不应该给我个界面嘛”，当前静默后台执行造成不安。
- 输出摘要：停止不可见的 Q2-B 后台执行；将 `agentctl.py` 升级到 `0.2.17`；`dispatch-claude` 默认写入 `04_claude_workorders/live/CURRENT_CLAUDE_DIALOGUE.md`；CLI 输出改为流式写入 live 面板和 dispatch log；新增 `--no-live-log` 备用开关。
- 关联文件：`05_code/tools/agentctl.py`, `04_claude_workorders/live/CURRENT_CLAUDE_DIALOGUE.md`, `05_code/tools/README.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`, `05_code/tools/tool_registry.json`, `00_shared/PROJECT_STATE.md`
- 备注：后续执行 Q2-B 前，应先让用户打开 live 面板观察。

## AILOG-037 Claude visible terminal mode

- 日期：2026-06-09
- 工具：Codex / agentctl
- 用途：为 Claude Code 调度增加真实终端界面，解决 Markdown 面板仍不够像终端、权限审批不直观的问题。
- 输入摘要：用户询问 Claude Code 是否可能需要审批，以及是否能看到像在终端开启 Claude 一样的实时运行输出，同时 Codex 仍可继续对话。
- 输出摘要：停止卡住的 Q2-B 后台 Claude 进程；将 `agentctl.py` 升级到 `0.2.18`；新增 `dispatch-claude --mode terminal`；默认打开 macOS Terminal 运行交互式 Claude Code；新增 `--terminal-permission-mode` 和 `--terminal-app`；终端状态写入 `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/README.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/VSCODE_DUAL_PANEL.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`, `05_code/tools/tool_registry.json`, `00_shared/PROJECT_STATE.md`
- 备注：`acceptEdits` 会减少编辑审批，但不等于完全无审批；需要用户可见审批时推荐 `--mode terminal --terminal-permission-mode default`。

## AILOG-AUTO-2026-06-09T08:48:21 Claude dispatch cli

- 日期：2026-06-09
- 工具：agentctl dispatch-claude
- 用途：通过 CLI 调用 Claude Code 执行 `Q2` 方案 `B`。
- 关联文件：`04_claude_workorders/claude_live_smoke_prompt.md`, `04_claude_workorders/dispatch_logs/20260609_084815_Q2_scheme_B.log`, `04_claude_workorders/live/CURRENT_CLAUDE_DIALOGUE.md`
- 返回码：0

## AILOG-AUTO-2026-06-09T09:03:00 Claude dispatch terminal

- 日期：2026-06-09
- 工具：agentctl dispatch-claude
- 用途：生成可见终端 Claude Code 执行脚本 `Q2` 方案 `B`。
- 关联文件：`04_claude_workorders/claude_live_smoke_prompt.md`, `04_claude_workorders/terminal_runs/20260609_090300_Q2_scheme_B.sh`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`
- 权限模式：`default`

## AILOG-038 Agent dispatch cleanup and figure layout guard

- 日期：2026-06-09
- 工具：Codex / agentctl / LaTeX / Matplotlib
- 用途：清理多轮迭代遗留的 Claude Code 冗余派发模块，并修正 Q1 论文图表排版。
- 输入摘要：用户指出旧 VSCode 面板/复制粘贴路线不好用，并要求参考优秀论文修正图 3 过大、图 4 四宫格、图表堆满一页等问题。
- 输出摘要：`dispatch-claude` 当前接口收敛为 `auto/terminal/cli`；删除旧 VSCode 双面板说明，新增可见终端工作流；图表规范新增最多双子图、禁止四宫格、控制图宽高度、禁止整页堆图等硬约束；Q1 图 4 改为单结论样条阶数敏感性图，模型检验改入表格；重新编译 `07_paper/main.pdf` 并检查第 6/7 页版面。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/Q1/q1_final_figures.py`, `07_paper/sections/model_q1.tex`, `07_paper/JXUSTmodeling.cls`, `07_paper/figure_insertion_rules.md`, `07_paper/figure_generation_workflow.md`, `02_references/paper_style_guide.md`, `08_agent_design/CLAUDE_TERMINAL_WORKFLOW.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `05_code/tools/tool_registry.json`, `00_shared/PROJECT_STATE.md`, `07_paper/main.pdf`
- 人工修改：Codex 根据用户边界要求保留最多双子图，不采用“一律禁用 subfigure”的规则。

## AILOG-039 Q1 figure float layout refinement

- 日期：2026-06-09
- 工具：Codex / LaTeX
- 用途：修正 Q1 中表 2、图 2、图 3 的跨页和空白问题。
- 输入摘要：用户指出图 2 与表 2 附近存在大空白，并要求图 3 回到第 5 页。
- 输出摘要：缩小图 2 双子图和图 3 宽度，改用 `[!ht]` 与 `\FloatBarrier` 控制浮动顺序，收紧浮动体和标题间距；重新编译 `07_paper/main.pdf`，确认图 3 已位于第 5 页。
- 关联文件：`07_paper/sections/model_q1.tex`, `05_code/tools/agentctl.py`, `07_paper/JXUSTmodeling.cls`, `07_paper/figure_insertion_rules.md`, `07_paper/figure_generation_workflow.md`, `07_paper/main.pdf`

## AILOG-040 PDF layout-check agent guard

- 日期：2026-06-09
- 工具：Codex / agentctl / PyMuPDF
- 用途：将图表跨页、大空白和指定图表页码要求写入 agent 自动验收流程。
- 输入摘要：用户要求“为了避免这样的情况再出现你应该写入 agent 里”。
- 输出摘要：将 `agentctl.py` 升级到 `0.2.20`；新增 `layout-check` 命令，扫描 PDF 页面内部异常大空白，并支持 `--expect-label-page label=page`；`latex-check` 默认编译后运行版面检查；`write-question-paper` 和 `finalize-summary-paper` 编译后运行默认版面检查。
- 验证：`layout-check --expect-label-page fig:q1_surface=5` 通过；故意设置 `fig:q1_surface=6` 可触发失败；`latex-check --expect-label-page fig:q1_surface=5` 通过。
- 关联文件：`05_code/tools/agentctl.py`, `05_code/tools/README.md`, `05_code/tools/tool_registry.json`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `08_agent_design/VERSION_PLAN.md`, `00_shared/WORKFLOW_PROTOCOL.md`, `07_paper/figure_insertion_rules.md`

## AILOG-AUTO-2026-06-09T20:09:46 Claude monitor terminal

- 日期：2026-06-09
- 工具：agentctl open-claude-monitor
- 用途：打开 `Q2` 方案 `B` 的可见 Claude 监控终端。
- 关联文件：`04_claude_workorders/terminal_runs/monitors/20260609_200946_Q2_scheme_B_monitor.sh`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`, `04_claude_workorders/completions/Q2_scheme_B_completion.md`

## AILOG-041 Q2 5.2 workflow gate test and visible monitor

- 日期：2026-06-09
- 工具：Codex / agentctl / Python
- 用途：完整测试 5.2/Q2-B 从 Claude 完成报告到 Codex 复审、模型确认门禁和可见监控界面的工作流。
- 输入摘要：用户要求继续测试 5.2，并要求看到 Codex 与 Claude Code 的对话/执行界面。
- 输出摘要：Codex 重跑 `05_code/Q2/q2_scheme_B.py` 并核验输出；`06_results/Q2/logs/scheme_B_codex_review.md` 已标记 PASS；生成 `03_methods/Q2/model_confirmation_brief.md`，给出 4 个模型确认选项；`write-question-paper --question Q2` 在模型未确认时正确阻断；新增 `open-claude-monitor` 打开可见监控终端。
- 验证：`python -m py_compile 05_code/tools/agentctl.py` 通过；`open-claude-monitor --question Q2 --scheme B --no-open` 成功生成脚本；`readiness` 显示当前停在 Q2 模型确认门。
- 关联文件：`05_code/tools/agentctl.py`, `03_methods/Q2/model_confirmation_brief.md`, `06_results/Q2/logs/scheme_B_codex_review.md`, `04_claude_workorders/terminal_runs/monitors/20260609_200946_Q2_scheme_B_monitor.sh`, `05_code/tools/tool_registry.json`, `08_agent_design/CLAUDE_TERMINAL_WORKFLOW.md`, `00_shared/PROJECT_STATE.md`

## AILOG-AUTO-2026-06-09T20:21:06 Claude dispatch terminal

- 日期：2026-06-09
- 工具：agentctl dispatch-claude
- 用途：生成可见终端 Claude Code 执行脚本 `Q2` 方案 `B`。
- 关联文件：`04_claude_workorders/Q2_scheme_B_claude_prompt.md`, `04_claude_workorders/terminal_runs/20260609_202106_Q2_scheme_B.sh`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`
- 权限模式：`default`

## AILOG-AUTO-2026-06-09T20:21:06 Claude monitor terminal

- 日期：2026-06-09
- 工具：agentctl open-claude-monitor
- 用途：打开 `Q2` 方案 `B` 的可见 Claude 监控终端。
- 关联文件：`04_claude_workorders/terminal_runs/monitors/20260609_202106_Q2_scheme_B_monitor.sh`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`, `04_claude_workorders/completions/Q2_scheme_B_completion.md`

## AILOG-AUTO-2026-06-09T20:21:06 VSCode Claude terminal tasks

- 日期：2026-06-09
- 工具：agentctl install-vscode-tasks
- 用途：为 `Q2` 方案 `B` 生成 VS Code 集成终端任务。
- 关联文件：`.vscode/tasks.json`, `04_claude_workorders/terminal_runs/20260609_202106_Q2_scheme_B.sh`, `04_claude_workorders/terminal_runs/monitors/20260609_202106_Q2_scheme_B_monitor.sh`
- 权限模式：`default`

## AILOG-042 User-facing approval options guard

- 日期：2026-06-09
- 工具：Codex / agentctl
- 用途：修正审批简报只写入文件、未直接向用户展示选项的问题。
- 输入摘要：用户指出 agent 开发中不能忘记给出 Q2 的几个选项。
- 输出摘要：将 `agentctl.py` 升级到 `0.2.23`；`create-approval-brief` 和 `create-model-confirmation-brief` 现在会直接输出完整审批选项，并追加 `ACTION_REQUIRED` 提醒 Codex 必须在聊天中转述；工作流协议、命令手册和工具注册表同步写入“只给文件路径不算完成审批告知”的硬规则。
- 关联文件：`05_code/tools/agentctl.py`, `00_shared/WORKFLOW_PROTOCOL.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `08_agent_design/TOOL_REGISTRY.md`, `05_code/tools/README.md`, `05_code/tools/tool_registry.json`, `00_shared/PROJECT_STATE.md`

## AILOG-043 Q2-B model confirmation and final Chinese figures

- 日期：2026-06-09
- 工具：Codex / agentctl / Matplotlib
- 用途：记录用户确认 Q2-B，并生成 Q2 5.2 候选中文图。
- 输入摘要：用户回复“我选择Q2B”。
- 输出摘要：运行 `confirm-model --question Q2 --scheme B`，记录决策 `D-009`；新增 `05_code/Q2/q2_final_figures.py`，从已复审结果表重绘 3 张中文候选图和审批总览；`03_methods/Q2/approved.md` 写入 Q2-B 保守论文口径。
- 关联文件：`03_methods/Q2/approved.md`, `05_code/Q2/q2_final_figures.py`, `07_paper/figures/q2_fig1_bmi_group_timing.png`, `07_paper/figures/q2_fig2_bootstrap_stability.png`, `07_paper/figures/q2_fig3_tstar_robustness.png`, `03_methods/Q2/figure_approval_brief.md`, `03_methods/Q2/q2_figure_approval_sheet.png`, `00_shared/PROJECT_STATE.md`
- 备注：Q2 图表尚未审批，不得写入 5.2 正文。

## AILOG-044 Windows packaging and clean-figure guard

- 日期：2026-06-09
- 工具：Codex / agentctl
- 用途：将 agent 产品化交付要求写入工具和文档。
- 输入摘要：用户要求后续画图不要生成图内长批注和红虚线；agent 主要适配 Windows；新用户拿到后要能安装环境、测试 Claude Code 在 VS Code 终端中可用；打包需包含国赛 LaTeX 模板和历年优秀论文；后续上传 GitHub。
- 输出摘要：`agentctl.py` 升级到 `0.2.24`，新增 `doctor` 自检；`install-vscode-tasks` 支持 `--target-os windows` 并生成 PowerShell 版 Claude 执行/监控脚本；新增 Windows VS Code smoke task；新增 `.gitignore`, `.gitattributes`, `README.md`, `08_agent_design/PACKAGING_AND_RELEASE.md`；图表规则新增禁止图内底部长批注和红色虚线参考线。
- 验证：`python -m py_compile 05_code/tools/agentctl.py 05_code/Q2/q2_final_figures.py` 通过；`doctor --target-os windows --write-vscode-smoke-task` 成功生成 VS Code smoke task；`install-vscode-tasks --target-os windows` 成功生成 PowerShell 任务脚本。
- 关联文件：`05_code/tools/agentctl.py`, `INSTALL.md`, `README.md`, `README_WORKFLOW.md`, `08_agent_design/PACKAGING_AND_RELEASE.md`, `08_agent_design/CLAUDE_TERMINAL_WORKFLOW.md`, `08_agent_design/WORKFLOW_COMMANDS.md`, `07_paper/figure_generation_workflow.md`, `07_paper/figure_insertion_rules.md`, `.gitignore`, `.gitattributes`
- 备注：当前机器 `doctor` 报告 `xelatex` 不在 PATH；Windows 交付文档已要求安装 TeX Live/MiKTeX 并加入 PATH。

## AILOG-AUTO-2026-06-09T21:02:13 Claude dispatch terminal

- 日期：2026-06-09
- 工具：agentctl dispatch-claude
- 用途：生成 Windows/PowerShell 可见终端 Claude Code 执行脚本 `Q2` 方案 `B`。
- 关联文件：`04_claude_workorders/Q2_scheme_B_claude_prompt.md`, `04_claude_workorders/terminal_runs/20260609_210213_Q2_scheme_B.ps1`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`
- 权限模式：`default`

## AILOG-AUTO-2026-06-09T21:02:13 Claude monitor terminal

- 日期：2026-06-09
- 工具：agentctl open-claude-monitor
- 用途：生成 `Q2` 方案 `B` 的 Windows/PowerShell Claude 监控终端脚本。
- 关联文件：`04_claude_workorders/terminal_runs/monitors/20260609_210213_Q2_scheme_B_monitor.ps1`, `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`, `04_claude_workorders/completions/Q2_scheme_B_completion.md`

## AILOG-AUTO-2026-06-09T21:02:13 VSCode Claude terminal tasks

- 日期：2026-06-09
- 工具：agentctl install-vscode-tasks
- 用途：为 `Q2` 方案 `B` 生成 VS Code 集成终端任务。
- 关联文件：`.vscode/tasks.json`, `04_claude_workorders/terminal_runs/20260609_210213_Q2_scheme_B.ps1`, `04_claude_workorders/terminal_runs/monitors/20260609_210213_Q2_scheme_B_monitor.ps1`
- 权限模式：`default`
- 目标系统：`windows`
