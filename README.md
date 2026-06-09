# Math Magic

面向中国大学生数学建模训练的 Codex + Claude Code 多 Agent 工作流。

## 核心能力

- 逐问推进：当前问题模型确认前，不推进后续问题的 Claude Code 工单。
- 三段审批：方案审批、模型确认、图表审批都必须在聊天中直接给出选项。
- 职责分离：Codex 负责建模统筹、图表、论文、验收；Claude Code 负责代码实现、运行和调试。
- 可见执行：支持 VS Code 集成终端中运行 Claude Code，并同步打开监控终端。
- 论文资源：仓库包含国赛 LaTeX 模板、优秀论文参考和中文 CUMCM 风格写作规范。

## 首次安装

推荐 Windows 用户使用 PowerShell：

```powershell
conda env create -f environment.yml
conda activate math-magic
npm install -g @anthropic-ai/claude-code
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

然后在 VS Code 中运行任务：

```text
Math Magic: Claude smoke test
```

该任务应在 VS Code 集成终端中输出 Claude Code 版本和环境检查结果。

## 常用命令

```bash
python 05_code/tools/agentctl.py readiness
python 05_code/tools/agentctl.py tools
python 05_code/tools/agentctl.py create-approval-brief --question Q1
python 05_code/tools/agentctl.py install-vscode-tasks --question Q1 --scheme B --target-os windows
```

更多说明见：

- [INSTALL.md](INSTALL.md)
- [README_WORKFLOW.md](README_WORKFLOW.md)
- [08_agent_design/WORKFLOW_COMMANDS.md](08_agent_design/WORKFLOW_COMMANDS.md)
- [08_agent_design/PACKAGING_AND_RELEASE.md](08_agent_design/PACKAGING_AND_RELEASE.md)

## 资源目录

- `02_references/excellent_papers/`：历年优秀论文 PDF。
- `02_references/paper_style_guide.md`：优秀论文风格约束。
- `07_paper/template_raw/`：国赛 LaTeX 模板原始文件。
- `07_paper/`：当前论文工作版。
- `05_code/tools/agentctl.py`：工作流控制脚本。
