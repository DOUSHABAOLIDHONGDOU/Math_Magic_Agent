# Project State

## 当前阶段

- 阶段：Q2-B 已通过 Codex 复审，等待用户模型确认
- 当前负责人：Codex
- 当前问题：CUMCM2025 C 题 Q2
- 当前状态：用户已确认 Q2-B 作为 Q2 最终模型，决策 ID `D-009`。Codex 已生成 Q2 中文候选图和图表审批简报。agent 产品化要求已推进到 `0.2.24`：支持 Windows VS Code PowerShell 任务、首次安装 `doctor` 自检、图表洁净规则和打包清单。下一步等待用户在聊天中审批 Q2 图表；只给简报路径不算完成审批告知。

## 题目与任务

| 问题 | 任务摘要 | 输出要求 | 状态 |
|---|---|---|---|
| Q1 | 分析男胎 Y 染色体浓度与孕周、BMI 等因素关系 | 关系模型、显著性检验、残差与敏感性分析 | 三次审批完成，已写入论文并编译 PDF |
| Q2 | 男胎 BMI 分组并确定最佳 NIPT 时点 | BMI 分组、最佳检测时点、检测误差影响 | 方案 B 已执行并复审 PASS，待模型确认 |
| Q3 | 引入更多因素和检测误差后优化 BMI 分组与时点 | 多因素模型、稳健时点、误差/敏感性分析 | 等待 Q2 模型确认后重审/修订方案 |
| Q4 | 女胎染色体异常判定 | 异常分类模型、阈值/分类指标、误差分析 | 等待前序问题推进后再进入正式审批 |

## 数据情况

| 文件 | 字段 | 说明 | 数据质量 | 状态 |
|---|---|---|---|---|
| `01_problem/source/CUMCM2025Problems/C题/附件.xlsx` | 男胎检测数据 31 字段，1082 行 | Q1-Q3 使用，含孕周、BMI、Y 浓度、质量指标等 | 已扫描，需建模脚本进一步清洗 | 可用 |
| `01_problem/source/CUMCM2025Problems/C题/附件.xlsx` | 女胎检测数据 31 字段，605 行 | Q4 使用，含 Z 值、GC、质量指标和异常标记 | 已扫描，存在空列和类别不平衡风险 | 可用 |

## 全局技术路线

- 推荐语言：Python
- 是否已由用户批准：是，决策 ID `D-004`
- LaTeX 风格：中文 CUMCM / 中国数模国赛论文风格
- 英文摘要：当前模板说明不需要英文摘要
- LaTeX 编译：`07_paper/main.tex` 已成功生成 `07_paper/main.pdf`
- 优秀论文读取：扫描版 PDF 已通过 OCR 建立结构索引
- 优秀论文风格约束：`02_references/paper_style_guide.md`
- Agent 控制脚本：`05_code/tools/agentctl.py` 已通过环境检查、工具注册表读取、状态读取、C 题导入、数据扫描、并发方案状态补录、LaTeX 编译和临时工单生成测试
- 工作流推进方式：逐问推进，当前问题确认模型后才解锁下一问
- 机器状态文件：`00_shared/workflow_state.json`
- 命令式流程文档：`08_agent_design/WORKFLOW_COMMANDS.md`
- Claude 可见终端工作流：`08_agent_design/CLAUDE_TERMINAL_WORKFLOW.md`
- 依赖安装入口：`environment.yml`, `requirements.txt`, `INSTALL.md`
- 工具注册表：`05_code/tools/tool_registry.json`, `08_agent_design/TOOL_REGISTRY.md`
- Windows 交付自检：`doctor --target-os windows --write-vscode-smoke-task`
- 图表最终负责人：Codex
- 代码实现负责人：Claude Code
- Claude 默认派发路线：`dispatch-claude --mode auto`，等价于打开可见 Terminal 会话；`--mode cli` 仅作后台备用
- Claude 可见终端模式：`dispatch-claude --mode terminal`，终端状态文件 `04_claude_workorders/terminal_runs/CURRENT_TERMINAL_STATUS.json`
- Claude 可见监控界面：`open-claude-monitor --question QX --scheme B`，显示终端状态、完成报告和标准输出文件
- VS Code 可见会话：`install-vscode-tasks --question QX --scheme B`，生成集成终端任务 `Math Magic: Claude QX-B visible session`
- 打包发布清单：`08_agent_design/PACKAGING_AND_RELEASE.md`，明确包含国赛 LaTeX 模板和优秀论文资源
- 模型确认审批：Codex 复审 PASS 后先运行 `create-model-confirmation-brief --question QX`，由用户选择确认选项
- 单题入文规则：模型确认和图表审批后运行 `write-question-paper --question QX`，并立即编译 PDF
- 综合内容规则：摘要、模型检验、模型评价与推广等在全部问题入文后再运行 `finalize-summary-paper`
- 最终图像语言：中文坐标轴、中文图例、中文图题；Claude Code 英文图只作验收参考

## 当前已批准方案

| 问题 | 已批准方案 | 决策 ID | 状态 |
|---|---|---|---|
| Q1 | B | D-005 / D-006 / D-007 | Q1-B v2 已完成模型确认、图表审批和论文写入 |
| Q2 | B | D-008 / D-009 | Q2-B 已完成模型确认，中文候选图待审批 |
| Q3 | 未批准 | - | 等待 Q2 模型确认 |
| Q4 | 未批准 | - | 暂不进入审批 |

## 三次审批状态

| 问题 | 方案审批 | 模型确认 | 图表审批 | 论文写入 |
|---|---|---|---|---|
| Q1 | 已完成，D-005 | 已完成，D-006 | 已完成，D-007 | 已完成 |
| Q2 | 已完成，D-008 | 已完成，D-009 | 未完成 | 未完成 |
| Q3 | 未完成 | 未完成 | 未完成 | 未完成 |
| Q4 | 未完成 | 未完成 | 未完成 | 未完成 |

## Claude Code 当前任务

- 当前工单：`04_claude_workorders/Q2_scheme_B_workorder_001.md`
- 输入文件：`04_claude_workorders/Q2_scheme_B_claude_prompt.md`
- 全局 Claude Code CLI：`/Users/lwb/miniconda3/bin/claude`
- 备用插件内置 binary：`/Users/lwb/.vscode/extensions/anthropic.claude-code-2.1.168-darwin-arm64/resources/native-binary/claude`
- 输出文件：`04_claude_workorders/completions/Q2_scheme_B_completion.md`, `06_results/Q2/`
- 监控界面：`04_claude_workorders/terminal_runs/monitors/20260609_200946_Q2_scheme_B_monitor.sh`
- VS Code 任务：`.vscode/tasks.json`，当前可运行 `Math Magic: Claude Q2-B visible session`
- 截止状态：Q2-B 已完成 Claude Code 执行、Codex 复审和模型确认，下一步等待用户审批中文候选图。

## Codex 验收状态

| 工单 | 代码审查 | 结果审查 | 图表审查 | 结论 |
|---|---|---|---|---|
| Q1_B_001 | PASS | PASS | PASS for modeling review | 已确认模型并写入论文 |
| Q2_B_001 | PASS | PASS | 已生成中文候选图，待用户审批 | 模型已确认，待图表审批 |

## 待确认问题

| ID | 问题 | 影响 | 负责人 | 状态 |
|---|---|---|---|---|
| B-001 | 是否批准 Python 作为默认实现语言 | 影响代码工单和环境配置 | 用户 | 已确认，Python |
| B-004 | 导入训练题目和数据 | 进入第一次跑通流程 | 用户 | 已完成，CUMCM2025 C 题 |
| B-005 | 是否批准 Q1-Q4 的 A/B/C 三套方案全部运行 | 原流程会破坏逐问依赖 | 用户 | 已否决，改为逐问推进 |
| B-006 | 用户选择 Q1 的哪一个或哪些方案交给 Claude Code | 影响 Q1 工单和提示词生成 | 用户 | 已确认：方案 B，D-005 |
