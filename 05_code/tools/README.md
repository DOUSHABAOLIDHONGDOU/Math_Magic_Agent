# Tools

## `pdf_style_extractor.py`

用途：从优秀论文 PDF 中抽取高层结构信号，辅助 Codex 对照优秀论文风格。

扫描版 PDF 需要 OCR：

```bash
conda run -n base python 05_code/tools/pdf_style_extractor.py \
  --input-dir 02_references/excellent_papers \
  --out-csv 02_references/excellent_papers_style_signals.csv \
  --out-md 02_references/excellent_papers_style_signals.md \
  --ocr
```

快速测试一篇：

```bash
conda run -n base python 05_code/tools/pdf_style_extractor.py \
  --input-dir 02_references/excellent_papers \
  --out-csv 02_references/excellent_papers_style_signals_ocr_sample.csv \
  --out-md 02_references/excellent_papers_style_signals_ocr_sample.md \
  --ocr \
  --limit 1
```

## `agentctl.py`

用途：多 Agent 工作流的轻量控制脚本。

检查环境：

```bash
conda run -n base python 05_code/tools/agentctl.py env-check
```

首次安装自检，Windows 交付推荐：

```powershell
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

随后在 VS Code 运行任务 `Math Magic: Claude smoke test`，检查集成终端是否能调用 Claude Code 和项目环境。

查看共享状态：

```bash
conda run -n base python 05_code/tools/agentctl.py status
```

查看工具注册表：

```bash
conda run -n base python 05_code/tools/agentctl.py tools
```

编译论文：

```bash
conda run -n base python 05_code/tools/agentctl.py latex-check
```

`latex-check` 会先编译 `07_paper/main.tex`，然后自动执行版面检查，扫描 PDF 内部异常大空白。若某张图必须落在指定页，可追加：

```bash
conda run -n base python 05_code/tools/agentctl.py latex-check \
  --expect-label-page fig:q1_surface=5
```

也可只检查现有 PDF：

```bash
conda run -n base python 05_code/tools/agentctl.py layout-check \
  --expect-label-page fig:q1_surface=5
```

从模板生成 Claude Code 工单：

```bash
conda run -n base python 05_code/tools/agentctl.py create-workorder --question Q1 --scheme A --force
```

正式逐问流程中，先生成给用户看的审批简报：

```bash
conda run -n base python 05_code/tools/agentctl.py create-approval-brief --question Q1
```

该命令会直接输出 A/B/C 方案选项。Codex 必须把这些选项在聊天中列给用户；只给 `03_methods/QX/approval_brief.md` 路径不算完成审批告知。

用户选择方案后，生成给 Claude Code 的提示词：

```bash
conda run -n base python 05_code/tools/agentctl.py approve-schemes --question Q1 --schemes B
conda run -n base python 05_code/tools/agentctl.py create-claude-prompt --question Q1 --scheme B
```

Claude Code 完成且 Codex 复审通过后，先生成模型确认审批简报：

```bash
conda run -n base python 05_code/tools/agentctl.py create-model-confirmation-brief --question Q1
```

该命令会直接输出模型确认选项。Codex 必须把这些选项在聊天中列给用户；只给 `03_methods/QX/model_confirmation_brief.md` 路径不算完成审批告知。

用户选择模型确认选项后，再运行 `confirm-model`。

自动调度给 Claude Code：

```bash
conda run -n base python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --mode auto \
  --watch \
  --require-standard-outputs
```

`auto` 是数学建模训练阶段的默认主路线，等价于 `terminal`：打开 macOS Terminal，运行交互式 Claude Code，并让用户在终端中看到实时输出和权限审批。Codex 在当前会话中继续通过 `watch-claude` 检测完成报告和标准输出。

默认终端权限模式为 `default`。需要减少编辑审批时可追加 `--terminal-permission-mode acceptEdits`；不建议把 `bypassPermissions` 作为常规默认。

打开 Claude 任务监控终端：

```bash
conda run -n base python 05_code/tools/agentctl.py open-claude-monitor \
  --question Q1 \
  --scheme B
```

监控终端会循环显示当前 Claude 终端状态、完成报告和标准输出是否齐全。正式执行窗口仍由 `dispatch-claude --mode auto` 打开；监控窗口用于让用户和 Codex 同步观察任务进度。

如果用户希望所有界面都在 VS Code 面板内，安装集成终端任务：

```bash
conda run -n base python 05_code/tools/agentctl.py install-vscode-tasks \
  --question Q1 \
  --scheme B \
  --target-os windows
```

然后在 VS Code 运行任务 `Math Magic: Claude QX-B visible session`。Windows 下会生成 PowerShell 脚本；macOS/Linux 可使用 `--target-os posix` 或默认 `auto`。该任务会并行打开 Claude 执行终端和监控终端，比 VS Code Claude 插件面板粘贴路线稳定。

发送最新返修提示词：

```bash
conda run -n base python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --revision \
  --mode auto
```

配置本机 Claude Code 命令：

```bash
cp 04_claude_workorders/claude_dispatch_config.example.json \
   04_claude_workorders/claude_dispatch_config.json
```

主流程默认使用 `--mode auto`，即打开可见终端，并要求终端环境中可以直接调用 `claude`。配置文件主要供 `--mode cli` 后台备用路线使用；此时把 `command` 改成本机实际 Claude Code CLI 命令，例如 `claude -p --permission-mode acceptEdits`。

后台非交互模式仅作为备用：

```bash
conda run -n base python 05_code/tools/agentctl.py dispatch-claude \
  --question Q1 \
  --scheme B \
  --mode cli \
  --watch \
  --require-standard-outputs
```

后台模式使用 `claude -p --permission-mode acceptEdits`，不会显示 Claude Code 的终端审批界面。

监听 Claude Code 是否完成：

```bash
conda run -n base python 05_code/tools/agentctl.py watch-claude \
  --question Q1 \
  --scheme B \
  --interval 30 \
  --ingest \
  --create-review \
  --require-standard-outputs
```

每完成一个问题的模型确认和图表审批后，写入该问题 LaTeX 小节并立即编译：

```bash
conda run -n base python 05_code/tools/agentctl.py approve-figures \
  --question Q1 \
  --figures q1_relation_zh.png
```

```bash
conda run -n base python 05_code/tools/agentctl.py write-question-paper --question Q1
```

该命令只写 `07_paper/sections/model_qX.tex`，不写摘要、模型评价、模型检验等综合内容。

写入后必须通过 `latex-check` 或 `layout-check` 验收，避免图表漂移、图文顺序错误或页面中间出现大块空白。

全部问题都已写入论文后，再解锁摘要和总结性章节：

```bash
conda run -n base python 05_code/tools/agentctl.py finalize-summary-paper
```

单次检查：

```bash
conda run -n base python 05_code/tools/agentctl.py check-claude \
  --question Q1 \
  --scheme B \
  --ingest \
  --create-review \
  --require-standard-outputs
```

## `problem_statement_extractor.py`

用途：从题目 PDF 中抽取题面 Markdown；扫描版题面可加 `--ocr`。

```bash
conda run -n base python 05_code/tools/problem_statement_extractor.py \
  --input 01_problem/source/problem.pdf \
  --out 01_problem/source/problem_statement.md
```

导入工作流：

```bash
conda run -n base python 05_code/tools/agentctl.py import-problem \
  --statement 01_problem/source/problem_statement.md \
  --title "训练题目名称" \
  --problem-id TRAIN-001 \
  --data-dir 01_problem/source/data \
  --num-questions 3
```

扫描数据：

```bash
conda run -n base python 05_code/tools/agentctl.py scan-data \
  --data-dir 01_problem/source/data
```
