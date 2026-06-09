# Math Magic 多 Agent 数学建模工作流

本项目用于搭建和跑通 Codex + Claude Code + 人类队伍的数学建模协作流程。

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

## 当前工作流状态

已完成：

1. 建立多 Agent 协作目录。
2. 解压优秀论文 PDF。
3. 解压 LaTeX 模板并生成工作版论文骨架。
4. 修复本机 XeLaTeX 中文字体配置。
5. 验证 `07_paper/main.tex` 可编译为 `07_paper/main.pdf`。
6. 配置 conda base 建模和 OCR 环境。
7. 对 23 篇优秀论文生成 OCR 结构索引。
8. 生成优秀论文写作风格约束。
9. 导入 `CUMCM2025Problems.zip`，完成 C 题题面抽取和数据扫描。
10. 为 C 题 Q1-Q4 生成 A/B/C 预分析方案。
11. 修复 `agentctl.py` 并发状态写入覆盖问题，并验证 Q1-Q4 并行补录成功。
12. 根据用户反馈，将正式流程改为逐问推进。
13. Q1-B 已完成模型确认、图表审批、论文写入和 PDF 版面检查。
14. Q2-B 已完成 Claude Code 执行、Codex 复审和模型确认。
15. Q2 已生成中文候选图，等待用户图表审批。
16. agent 已支持 Windows VS Code 集成终端任务和 `doctor` 首次安装自检。

下一步：

1. 用户审批 Q2 中文候选图。
2. Codex 写入 Q2/5.2 LaTeX 小节并编译 PDF。
3. Q2 入文通过版面检查后，再推进 Q3 方案审批。

## 安装依赖

推荐使用独立 conda 环境：

```bash
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py env-check
```

查看当前工具注册表：

```bash
python 05_code/tools/agentctl.py tools
```

查看完整命令流：

```bash
python 05_code/tools/agentctl.py readiness
```

Windows 新用户应优先运行：

```powershell
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

随后在 VS Code 运行任务 `Math Magic: Claude smoke test`。
