# Install

本项目推荐使用 conda 环境，以保证 OCR、PDF 解析、绘图和数模依赖可复现。目标交付环境优先适配 Windows + VS Code。

## 推荐安装

### Windows + VS Code 推荐流程

在 PowerShell 中运行：

```powershell
conda env create -f environment.yml
conda activate math-magic
npm install -g @anthropic-ai/claude-code
claude --version
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

然后在 VS Code 中运行任务：

```text
Math Magic: Claude smoke test
```

若该任务能在 VS Code 集成终端输出 Claude Code 版本和环境检查结果，则说明“Claude Code terminal in VS Code”可用。

正式给某个已审批方案安装 Claude 执行和监控面板：

```powershell
python 05_code/tools/agentctl.py install-vscode-tasks --question Q1 --scheme B --target-os windows
```

然后在 VS Code 中运行：

```text
Math Magic: Claude QX-B visible session
```

### macOS / Linux

创建独立环境：

```bash
conda env create -f environment.yml
conda activate math-magic
python 05_code/tools/agentctl.py env-check
```

如果希望安装到已有 `base` 环境：

```bash
conda env update -n base -f environment.yml
conda activate base
python 05_code/tools/agentctl.py env-check
```

## pip 备选安装

仅使用 pip 时：

```bash
python -m pip install -r requirements.txt
```

注意：pip 不能安装 Tesseract OCR 二进制程序。若需要读取扫描版优秀论文 PDF，仍需额外安装 `tesseract`，并确保可执行命令在 PATH 中。

## Claude Code CLI

本项目的多 agent 调度默认调用 Claude Code CLI 或 VS Code Claude Code 扩展自带 native binary。创建或更新 conda 环境后安装：

```bash
conda activate math-magic
npm install -g @anthropic-ai/claude-code
claude --version
```

当前项目配置文件为：

```text
04_claude_workorders/claude_dispatch_config.json
```

默认可见终端策略：

```text
claude --dangerously-skip-permissions --permission-mode bypassPermissions --continue
```

正式可见执行优先使用项目根目录中的 PowerShell/bash 终端脚本。默认 `--continue` 用于保留 Claude Code 在当前项目目录的上下文；只有明确需要新对话时才使用 `--claude-session-mode new`。

`environment.yml` 不固定 Python 小版本；如已有可用 conda/base 环境，也可以直接安装 `requirements.txt` 后运行 `agentctl.py env-check`。

## LaTeX

论文编译需要 XeLaTeX：

```bash
cd 07_paper
xelatex -interaction=nonstopmode -halt-on-error main.tex
```

## 验证

项目提供统一检查入口：

```bash
python 05_code/tools/agentctl.py doctor --write-vscode-smoke-task
python 05_code/tools/agentctl.py env-check
python 05_code/tools/agentctl.py status
python 05_code/tools/agentctl.py latex-check
python 05_code/tools/agentctl.py tools
python 05_code/tools/agentctl.py readiness
```

还可以跑测试套件确认本机环境一切就绪（43 个测试，秒级完成，不依赖 xelatex/tesseract/claude）：

```bash
python -m pip install pytest rank-bm25
python -m pytest 05_code/tools/tests/ -q
```

## RAG (可选)

如果希望让方案生成阶段读到同题型的优秀论文：

```bash
# 方式 A：手工放 .md/.txt 进 02_references/paper_texts/，每篇一文件
python 05_code/tools/agentctl.py rag-status
python 05_code/tools/agentctl.py index-papers

# 方式 B：把扫描版优秀论文 PDF 放进 02_references/excellent_papers/，全篇 OCR
python 05_code/tools/pdf_style_extractor.py \
    --input-dir 02_references/excellent_papers \
    --full-ocr --ocr-texts-dir 02_references/ocr_texts --ocr-dpi 300
python 05_code/tools/agentctl.py index-papers
```

索引建好后，`prepare-schemes` 会自动检索相关段并注入 Codex 提示。详见
`02_references/paper_texts/README.md`。
