# Packaging And Release

本文件定义 Math Magic agent 的交付包和 GitHub 仓库内容。

## 必须包含

- `README.md`, `README_WORKFLOW.md`, `INSTALL.md`
- `environment.yml`, `requirements.txt`
- `00_shared/WORKFLOW_PROTOCOL.md`
- `05_code/tools/agentctl.py`
- `05_code/tools/tool_registry.json`
- `04_claude_workorders/templates/`
- `04_claude_workorders/claude_dispatch_config.example.json`
- `08_agent_design/`
- `07_paper/`
- `07_paper/template_raw/`
- `02_references/excellent_papers/`
- `02_references/paper_style_guide.md`
- `02_references/scoring_rubric.md`

这些内容保证新用户拿到仓库后能安装环境、读取优秀论文风格、使用国赛 LaTeX 模板，并运行 Codex + Claude Code 工作流。

## 可选包含

- `01_problem/source/`：训练题和样例数据。完整训练仓库可以保留；干净 agent 包可移除。
- `06_results/`：当前测试结果。完整训练仓库可以保留；干净 agent 包可移除。
- `03_methods/Q*/`：当前测试题的方案和审批记录。完整训练仓库可以保留；干净 agent 包可移除。

## 不应包含

- `.venv/`, `venv/`, `env/`
- `.cache/`
- `__pycache__/`
- LaTeX 临时文件：`*.aux`, `*.log`, `*.out`, `*.toc`
- Claude 运行时日志和终端脚本：`04_claude_workorders/dispatch_logs/*.log`, `04_claude_workorders/terminal_runs/*`
- 本机 Claude Code 配置：`04_claude_workorders/claude_dispatch_config.json`
- 本机生成的 `.vscode/tasks.json`
- 旧题归档审计目录：`00_shared/archive/stale_artifacts/`

## Windows 首次自检

新用户克隆仓库后，在 PowerShell 中运行：

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

通过标准：

- VS Code 集成终端能启动；
- `claude --version` 能输出版本；
- `agentctl.py env-check` 能检查 Python 包、XeLaTeX 和 Tesseract；
- `02_references/excellent_papers/` 与 `07_paper/template_raw/` 存在。

## GitHub 发布前检查

```bash
python 05_code/tools/agentctl.py doctor --strict
python -m py_compile 05_code/tools/agentctl.py
python -m json.tool 05_code/tools/tool_registry.json
python -m json.tool 04_claude_workorders/claude_dispatch_config.example.json
python 05_code/tools/agentctl.py archive-stale-artifacts --dry-run
python 05_code/tools/agentctl.py tools
```

如果要发布完整训练仓库，确认没有单文件超过 GitHub 100MB 限制。当前优秀论文压缩包 `math_exmaple.zip` 约 80MB，低于单文件限制；如后续超过限制，应拆包或使用 Git LFS。

发布前还要确认 `environment.yml` 未固定 Python 小版本，且仓库内没有个人 Windows 用户名、VS Code 扩展绝对路径、Claude 运行状态文件或旧题归档目录。
