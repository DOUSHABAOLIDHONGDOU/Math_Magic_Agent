# Claude Terminal Workflow

本文件记录当前稳定的 Claude Code 调度路线。

## 主路线

Codex 使用：

```bash
python 05_code/tools/agentctl.py dispatch-claude \
  --question QX \
  --scheme B \
  --mode auto \
  --watch \
  --require-standard-outputs
```

`auto` 等价于 `terminal`。脚本会写入 `04_claude_workorders/terminal_runs/` 并在可见终端里运行 Claude Code。macOS/Linux 生成 bash 脚本；Windows 生成 PowerShell 脚本。用户可以看到 Claude 的实时输出和权限审批；Codex 继续在本对话中监听完成报告。

## 监控界面

用户需要看到 Codex 对 Claude 任务状态的判断时，Codex 使用：

```bash
python 05_code/tools/agentctl.py open-claude-monitor \
  --question QX \
  --scheme B
```

该命令会打开另一个 Terminal 窗口，循环显示 Claude 执行终端状态、完成报告、标准输出是否齐全。它只负责观察，不负责执行；正式执行仍由 `dispatch-claude --mode auto` 的 Claude Code 终端完成。

## VS Code 集成终端

如果用户不想切到 macOS Terminal，而是希望在 VS Code 面板里看到 Claude 执行过程和 Codex 监控状态，Codex 使用：

```bash
python 05_code/tools/agentctl.py install-vscode-tasks \
  --question QX \
  --scheme B \
  --target-os windows
```

然后用户在 VS Code 运行任务 `Math Magic: Claude QX-B visible session`。该任务并行打开两个集成终端：一个运行 Claude Code，一个显示监控面板。Windows 端使用 PowerShell，macOS/Linux 端使用 bash。此路线不依赖 VS Code Claude 插件 URI、剪贴板或焦点粘贴。

## 首次自检

新机器先运行：

```bash
python 05_code/tools/agentctl.py doctor --target-os windows --write-vscode-smoke-task
```

然后在 VS Code 运行任务 `Math Magic: Claude smoke test`，确认集成终端能调用 `claude --version` 和项目环境检查。

## 权限

默认：

```bash
--terminal-permission-mode default
```

此时 Claude Code 的权限请求显示在终端中，由用户批准或拒绝。

如果用户已确认工作区和任务边界，可以显式使用：

```bash
--terminal-permission-mode acceptEdits
```

`bypassPermissions` 不作为常规默认，只能临时用于完全可信的训练环境。

## 后台备用

```bash
python 05_code/tools/agentctl.py dispatch-claude \
  --question QX \
  --scheme B \
  --mode cli \
  --watch \
  --require-standard-outputs
```

`cli` 模式不会显示 Claude Code 终端界面，只写入 `04_claude_workorders/dispatch_logs/*.log`。它适合短任务、烟雾测试或用户明确不需要观察实时输出时使用。

## 不再维护的路线

VSCode URI、前台粘贴、固定桥接文件和旧队列派发已经从当前接口中移除。原因是这些路线依赖 VSCode 焦点、扩展 URI 行为、剪贴板或人工粘贴，不能稳定投递到用户正在看的 Claude Code 会话。
