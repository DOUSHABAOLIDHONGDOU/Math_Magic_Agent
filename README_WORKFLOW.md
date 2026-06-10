# Math Magic 多 Agent 数学建模工作流

本项目用于搭建和运行 Codex + Claude Code + 人类队伍的数学建模协作流程。当前仓库是可分发的 agent 模板，不包含具体题目的运行结果。

## 快速入口

- 总协议：`00_shared/WORKFLOW_PROTOCOL.md`
- 当前状态：`00_shared/PROJECT_STATE.md`
- 决策日志：`00_shared/DECISION_LOG.md`
- AI 使用记录：`00_shared/AI_USAGE_LOG.md`
- Claude 工单模板：`04_claude_workorders/templates/claude_workorder_template.md`
- 优秀论文评分表：`02_references/scoring_rubric.md`
- Agent 设计：`08_agent_design/AGENT_SPEC.md`
- 环境说明：`08_agent_design/ENVIRONMENT_SETUP.md`
- 优秀论文风格约束：`02_references/paper_style_guide.md`
- 控制脚本：`05_code/tools/agentctl.py`
- 工具注册表：`08_agent_design/TOOL_REGISTRY.md`
- 安装说明：`INSTALL.md`
- 命令式工作流：`08_agent_design/WORKFLOW_COMMANDS.md`
- 版本计划：`08_agent_design/VERSION_PLAN.md`
- 打包发布：`08_agent_design/PACKAGING_AND_RELEASE.md`

## 初始状态

当前模板已保留：

1. 多 Agent 协作目录结构。
2. Agent 控制脚本和工具注册表。
3. Claude Code 工单、完成报告和图表任务模板。
4. 中文 CUMCM 风格 LaTeX 论文骨架。
5. 论文写作规范、评分表和设计文档。
6. 逐问推进、小问入文编译、总结后置等流程规则。

当前模板不包含：

1. 具体题目 PDF、附件或 OCR 结果。
2. 具体问题的方案、工单、代码实现和运行结果。
3. 已生成的论文 PDF、图表和历史归档。
4. 本地 Claude 会话、终端运行记录和缓存。

## 基本使用

```bash
python 05_code/tools/agentctl.py init-state --force
python 05_code/tools/agentctl.py env-check
python 05_code/tools/agentctl.py import-problem --statement 01_problem/source/problem.md --title 训练题目 --data-dir 01_problem/source/data
python 05_code/tools/agentctl.py readiness
```

Windows 新用户应优先运行：

```powershell
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```
