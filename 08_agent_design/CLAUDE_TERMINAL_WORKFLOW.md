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

`auto` 等价于 `terminal`。脚本会写入 `04_claude_workorders/terminal_runs/` 并在可见终端里运行 Claude Code。macOS/Linux 生成 bash 脚本；Windows 生成 PowerShell 脚本。终端启动目录固定为项目根目录，Claude Code 默认追加 `--continue`，复用该项目目录下最近一次 Claude Code 会话上下文；Codex 继续在本对话中监听完成报告。

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
--terminal-permission-mode bypassPermissions
```

当前本地训练工作流默认同时使用 `--dangerously-skip-permissions` 和 `--permission-mode bypassPermissions`，减少 Claude Code 每次编辑/运行时的人工点击。该默认值只适用于用户已确认可信的本地题目仓库和明确工单边界。

如果确实需要让 Claude Code 开启一个全新上下文，必须显式加：

```bash
--claude-session-mode new
```

普通优化轮次不要使用 `new`，否则 Claude Code 记忆不到上一轮实现和调试上下文。

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
