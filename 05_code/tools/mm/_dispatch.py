"""dispatch-claude / watch-claude / check-claude + terminal script generation.

This module is large because it owns the Claude Code interaction surface:
configured-command discovery, posix/windows visible-terminal script generation,
status payloads, the monitor terminal, and the VS Code task installer.
The core behaviour is preserved from the original agentctl.py.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ._paths import (
    PROJECT_ROOT,
    SELECTED_SCHEME_STATUSES,
    dispatch_config_path,
    dispatch_log_dir,
    dispatch_monitor_dir,
    dispatch_terminal_dir,
    dispatch_terminal_status_path,
    expected_completion_path,
    expected_standard_outputs,
    resolve_project_path,
    vscode_tasks_path,
)
from ._state import (
    append_artifact,
    approved_schemes,
    assert_question_unlocked,
    ensure_question,
    ensure_scheme,
    load_state,
    save_state,
    set_stage,
    workflow_lock,
)
from ._util import (
    append_markdown_log,
    claude_command_extra_args,
    claude_session_args,
    current_target_os,
    ensure_target_os,
    format_claude_command,
    now_iso,
    parse_iso_datetime,
    powershell_claude_executable,
    ps_args,
    ps_single_quote,
    read_text,
    rel,
    today,
    write_powershell_script,
    write_text,
)


# ---------------------------------------------------------------------------
# Claude command discovery


def load_dispatch_config() -> dict:
    path = dispatch_config_path()
    if path.exists():
        return json.loads(read_text(path))
    return {}


def discover_claude_binary():
    for command in ["claude", "claude-code"]:
        executable = shutil.which(command)
        if executable:
            return command
    try:
        npm_prefix = subprocess.run(
            ["npm", "config", "get", "prefix"],
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        npm_prefix = None
    if npm_prefix is not None and npm_prefix.returncode == 0:
        npm_root = Path((npm_prefix.stdout or b"").decode("utf-8", errors="replace").strip())
        for name in ["claude.cmd", "claude.ps1", "claude", "claude-code.cmd", "claude-code.ps1", "claude-code"]:
            candidate = npm_root / name
            if candidate.exists():
                return candidate
    extension_roots = [
        Path.home() / ".vscode" / "extensions",
        Path.home() / ".vscode-insiders" / "extensions",
        Path.home() / ".cursor" / "extensions",
        Path.home() / ".windsurf" / "extensions",
    ]
    candidates: list[Path] = []
    for root in extension_roots:
        if not root.exists():
            continue
        candidates.extend(root.glob("anthropic.claude-code-*/resources/native-binary/claude"))
    candidates = [path for path in candidates if path.exists() and os.access(path, os.X_OK)]
    if not candidates:
        return None
    return sorted(candidates, key=lambda path: path.stat().st_mtime)[-1]


def auto_discovered_claude_command() -> str:
    binary = discover_claude_binary()
    if not binary:
        return ""
    return format_claude_command(binary)


def configured_claude_command(args: argparse.Namespace) -> str:
    if getattr(args, "command", ""):
        return args.command
    env_command = os.environ.get("CLAUDE_CODE_COMMAND", "")
    if env_command:
        return env_command
    config = load_dispatch_config()
    if config.get("command", ""):
        return config["command"]
    if config.get("auto_discover", True):
        return auto_discovered_claude_command()
    return ""


def terminal_claude_command(permission_mode: str) -> str:
    config = load_dispatch_config()
    if config.get("terminal_command", ""):
        return config["terminal_command"]
    command = configured_claude_command(argparse.Namespace(command=""))
    if command:
        parts = [part for part in shlex.split(command, posix=False) if part not in {"-p", "--print"}]
        return " ".join(shlex.quote(part.strip("\"'")) for part in parts)
    return f"claude --dangerously-skip-permissions --permission-mode {shlex.quote(permission_mode)}"


# ---------------------------------------------------------------------------
# Prompt resolution


def latest_revision_prompt(question: str, scheme: str):
    pattern = f"{question}_scheme_{scheme}_revision_prompt_*.md"
    matches = sorted((PROJECT_ROOT / "04_claude_workorders").glob(pattern), key=lambda p: p.stat().st_mtime)
    return matches[-1] if matches else None


def resolve_dispatch_prompt(state: dict, question: str, scheme: str, prompt, use_revision: bool) -> Path:
    if prompt:
        path = prompt if prompt.is_absolute() else PROJECT_ROOT / prompt
        if not path.exists():
            raise SystemExit(f"prompt not found: {path}")
        return path
    if use_revision:
        revision = latest_revision_prompt(question, scheme)
        if revision:
            return revision
        raise SystemExit(f"no revision prompt found for {question} scheme {scheme}")
    scheme_state = state["questions"][question]["schemes"][scheme]
    if scheme_state.get("claude_prompt"):
        path = PROJECT_ROOT / scheme_state["claude_prompt"]
        if path.exists():
            return path
    default_path = PROJECT_ROOT / "04_claude_workorders" / f"{question}_scheme_{scheme}_claude_prompt.md"
    if default_path.exists():
        return default_path
    raise SystemExit(f"no Claude prompt found for {question} scheme {scheme}")


# ---------------------------------------------------------------------------
# Status payloads


def terminal_status_payload(
    *,
    question: str,
    scheme: str,
    prompt_path: Path,
    script_path: Path,
    permission_mode: str,
    claude_session_mode: str,
    claude_session_id,
    expected_report: Path,
    standard_output_list: list[str],
) -> dict:
    timestamp = now_iso()
    return {
        "status": "terminal_script_created",
        "return_code": "",
        "created_at": timestamp,
        "updated_at": timestamp,
        "run_started_at": "",
        "question": question,
        "scheme": scheme,
        "prompt": rel(prompt_path),
        "script": rel(script_path),
        "permission_mode": permission_mode,
        "claude_session_mode": claude_session_mode,
        "claude_session_id": claude_session_id or "",
        "expected_completion_report": rel(expected_report),
        "expected_standard_outputs": standard_output_list,
    }


def write_terminal_dispatch_script(
    state: dict,
    question: str,
    scheme: str,
    prompt_path: Path,
    permission_mode: str,
    claude_session_mode: str = "continue",
    claude_session_id=None,
    target_os: str = "auto",
) -> Path:
    target_os = ensure_target_os(target_os)
    if target_os == "windows":
        return write_windows_dispatch_script(
            state,
            question,
            scheme,
            prompt_path,
            permission_mode,
            claude_session_mode=claude_session_mode,
            claude_session_id=claude_session_id,
        )
    return write_posix_dispatch_script(
        state,
        question,
        scheme,
        prompt_path,
        permission_mode,
        claude_session_mode=claude_session_mode,
        claude_session_id=claude_session_id,
    )


def write_posix_dispatch_script(
    state: dict,
    question: str,
    scheme: str,
    prompt_path: Path,
    permission_mode: str,
    claude_session_mode: str = "continue",
    claude_session_id=None,
) -> Path:
    dispatch_terminal_dir().mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = dispatch_terminal_dir() / f"{stamp}_{question}_scheme_{scheme}.sh"
    status_path = dispatch_terminal_status_path()
    expected_report = expected_completion_path(question, scheme)
    standard_outputs = expected_standard_outputs(question, scheme)
    command = terminal_claude_command(permission_mode)
    command_args = shlex.split(command, posix=False)
    if command_args:
        command_parts = (
            [command_args[0].strip("\"'")]
            + claude_command_extra_args(command)
            + claude_session_args(claude_session_mode, claude_session_id)
        )
        command = " ".join(shlex.quote(part) for part in command_parts)
    command = f"{command} --permission-mode {shlex.quote(permission_mode)}"
    standard_output_list = [rel(path) for path in standard_outputs]
    status = terminal_status_payload(
        question=question,
        scheme=scheme,
        prompt_path=prompt_path,
        script_path=script_path,
        permission_mode=permission_mode,
        claude_session_mode=claude_session_mode,
        claude_session_id=claude_session_id,
        expected_report=expected_report,
        standard_output_list=standard_output_list,
    )
    script = f"""#!/usr/bin/env bash
set -u
cd {shlex.quote(str(PROJECT_ROOT))}

STATUS_PATH={shlex.quote(rel(status_path))}
PROMPT_PATH={shlex.quote(rel(prompt_path))}
QUESTION={shlex.quote(question)}
SCHEME={shlex.quote(scheme)}

write_status() {{
  local status="$1"
  local rc="${{2:-}}"
  python - "$STATUS_PATH" "$status" "$rc" <<'PY'
import datetime as dt
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
path.parent.mkdir(parents=True, exist_ok=True)
now = dt.datetime.now().isoformat(timespec="seconds")
payload = {{}}
if path.exists():
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        payload = {{}}
run_started_at = payload.get("run_started_at", "")
if sys.argv[2] == "running" and not run_started_at:
    run_started_at = now
payload = {{
    "status": sys.argv[2],
    "return_code": sys.argv[3],
    "created_at": payload.get("created_at", "{status['created_at']}"),
    "updated_at": now,
    "run_started_at": run_started_at,
    "question": "{question}",
    "scheme": "{scheme}",
    "prompt": "{rel(prompt_path)}",
    "script": "{rel(script_path)}",
    "permission_mode": "{permission_mode}",
    "claude_session_mode": "{claude_session_mode}",
    "claude_session_id": "{claude_session_id or ''}",
    "expected_completion_report": "{rel(expected_report)}",
    "expected_standard_outputs": {json.dumps(standard_output_list, ensure_ascii=False)},
}}
path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
PY
}}

write_status running
echo "=== Math Magic Claude Code Terminal Dispatch ==="
echo "Question: $QUESTION"
echo "Scheme: $SCHEME"
echo "Prompt: $PROMPT_PATH"
echo "Expected completion: {rel(expected_report)}"
echo "Permission mode: {permission_mode}"
echo "Claude session mode: {claude_session_mode}"
echo "Project root: {PROJECT_ROOT}"
echo
echo "This terminal is the visible Claude Code interface."
echo "Claude runs from the project root and uses the configured permission mode above."
echo "If Claude Code still asks a question, answer it in this terminal."
echo "Codex will keep watching the completion files from the other chat."
echo

if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
  source "$HOME/miniconda3/etc/profile.d/conda.sh"
  conda activate base
elif command -v conda >/dev/null 2>&1; then
  eval "$(conda shell.bash hook)"
  conda activate base
fi

{command} "$(cat "$PROMPT_PATH")"
RC=$?
write_status finished "$RC"

echo
echo "=== Claude exited with code $RC ==="
echo "Checking expected completion files..."
python 05_code/tools/agentctl.py check-claude --question "$QUESTION" --scheme "$SCHEME" --ingest --create-review --require-standard-outputs || true
echo
echo "Terminal dispatch finished. You can keep this window open for review."
"""
    write_text(script_path, script)
    script_path.chmod(0o755)
    write_text(status_path, json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    scheme_state = state["questions"][question]["schemes"][scheme]
    scheme_state["dispatch_status"] = "terminal_script_created"
    scheme_state["dispatch_mode"] = "terminal"
    scheme_state["dispatch_created_at"] = now_iso()
    scheme_state["claude_session_mode"] = claude_session_mode
    scheme_state["claude_session_id"] = claude_session_id
    scheme_state["dispatch_prompt"] = rel(prompt_path)
    scheme_state["dispatch_terminal_script"] = rel(script_path)
    scheme_state["dispatch_terminal_status"] = rel(status_path)
    append_artifact(state, "claude_dispatch_terminal_script", script_path, f"{question} scheme {scheme}")
    append_artifact(state, "claude_dispatch_terminal_status", status_path, f"{question} scheme {scheme}")
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} Claude dispatch terminal",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl dispatch-claude",
            f"- 用途：生成可见终端 Claude Code 执行脚本 `{question}` 方案 `{scheme}`。",
            f"- 关联文件：`{rel(prompt_path)}`, `{rel(script_path)}`, `{rel(status_path)}`",
            f"- 权限模式：`{permission_mode}`",
        ],
    )
    return script_path


def write_windows_dispatch_script(
    state: dict,
    question: str,
    scheme: str,
    prompt_path: Path,
    permission_mode: str,
    claude_session_mode: str = "continue",
    claude_session_id=None,
) -> Path:
    dispatch_terminal_dir().mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = dispatch_terminal_dir() / f"{stamp}_{question}_scheme_{scheme}.ps1"
    status_path = dispatch_terminal_status_path()
    expected_report = expected_completion_path(question, scheme)
    standard_outputs = expected_standard_outputs(question, scheme)
    standard_output_list = [rel(path) for path in standard_outputs]
    status = terminal_status_payload(
        question=question,
        scheme=scheme,
        prompt_path=prompt_path,
        script_path=script_path,
        permission_mode=permission_mode,
        claude_session_mode=claude_session_mode,
        claude_session_id=claude_session_id,
        expected_report=expected_report,
        standard_output_list=standard_output_list,
    )
    output_array = "@(" + ", ".join(ps_single_quote(path) for path in standard_output_list) + ")"
    command = terminal_claude_command(permission_mode)
    claude_executable = powershell_claude_executable(command)
    claude_args = " ".join(ps_single_quote(arg) for arg in claude_command_extra_args(command))
    claude_arg_prefix = f"{claude_args} " if claude_args else ""
    claude_session = ps_args(claude_session_args(claude_session_mode, claude_session_id))
    claude_session_prefix = f"{claude_session} " if claude_session else ""
    script = f"""Set-StrictMode -Version Latest
$Host.UI.RawUI.WindowTitle = "Claude Code {question}-{scheme}"
Set-Location {ps_single_quote(PROJECT_ROOT)}

$StatusPath = {ps_single_quote(rel(status_path))}
$PromptPath = {ps_single_quote(rel(prompt_path))}
$Question = {ps_single_quote(question)}
$Scheme = {ps_single_quote(scheme)}
$ExpectedOutputs = {output_array}

function Write-TaskStatus {{
  param([string]$Status, [string]$ReturnCode = "")
  $Now = (Get-Date).ToString("s")
  $Existing = $null
  if (Test-Path $StatusPath) {{
    try {{
      $Existing = Get-Content -Raw -Encoding UTF8 $StatusPath | ConvertFrom-Json
    }} catch {{
      $Existing = $null
    }}
  }}
  $ExistingCreatedAt = ""
  $RunStartedAt = ""
  if ($null -ne $Existing) {{
    $PropertyNames = $Existing.PSObject.Properties.Name
    if ($PropertyNames -contains "created_at") {{ $ExistingCreatedAt = [string]$Existing.created_at }}
    if ($PropertyNames -contains "run_started_at") {{ $RunStartedAt = [string]$Existing.run_started_at }}
  }}
  if ($Status -eq "running" -and -not $RunStartedAt) {{ $RunStartedAt = $Now }}
  $Payload = [ordered]@{{
    status = $Status
    return_code = $ReturnCode
    created_at = if ($ExistingCreatedAt) {{ $ExistingCreatedAt }} else {{ {ps_single_quote(status["created_at"])} }}
    updated_at = $Now
    run_started_at = $RunStartedAt
    question = {ps_single_quote(question)}
    scheme = {ps_single_quote(scheme)}
    prompt = {ps_single_quote(rel(prompt_path))}
    script = {ps_single_quote(rel(script_path))}
    permission_mode = {ps_single_quote(permission_mode)}
    claude_session_mode = {ps_single_quote(claude_session_mode)}
    claude_session_id = {ps_single_quote(claude_session_id or "")}
    expected_completion_report = {ps_single_quote(rel(expected_report))}
    expected_standard_outputs = $ExpectedOutputs
  }}
  $Parent = Split-Path -Parent $StatusPath
  if ($Parent) {{ New-Item -ItemType Directory -Force -Path $Parent | Out-Null }}
  $Payload | ConvertTo-Json -Depth 5 | Set-Content -Path $StatusPath -Encoding UTF8
}}

Write-TaskStatus -Status "running"
Write-Host "=== Math Magic Claude Code Terminal Dispatch ==="
Write-Host "Question: $Question"
Write-Host "Scheme: $Scheme"
Write-Host "Prompt: $PromptPath"
Write-Host "Expected completion: {rel(expected_report)}"
Write-Host "Permission mode: {permission_mode}"
Write-Host "Claude session mode: {claude_session_mode}"
Write-Host "Project root: {PROJECT_ROOT}"
Write-Host ""
Write-Host "This terminal is the visible Claude Code interface."
Write-Host "Claude runs from the project root and uses the configured permission mode above."
Write-Host "If Claude Code still asks a question, answer it in this terminal."
Write-Host "Codex will keep watching the completion files from the other chat."
Write-Host ""

$PromptText = Get-Content -Raw -Encoding UTF8 $PromptPath
Write-Host "Starting Claude Code now..."
Write-Host ""
& {ps_single_quote(claude_executable)} {claude_arg_prefix}{claude_session_prefix}--permission-mode {ps_single_quote(permission_mode)} $PromptText
$Rc = 0
$LastExitCodeVariable = Get-Variable -Name LASTEXITCODE -Scope Global -ErrorAction SilentlyContinue
if ($null -ne $LastExitCodeVariable -and $null -ne $LastExitCodeVariable.Value) {{
  $Rc = $LastExitCodeVariable.Value
}}
Write-TaskStatus -Status "finished" -ReturnCode "$Rc"

Write-Host ""
Write-Host "=== Claude exited with code $Rc ==="
Write-Host "Checking expected completion files..."
python 05_code/tools/agentctl.py check-claude --question "$Question" --scheme "$Scheme" --ingest --create-review --require-standard-outputs
Write-Host ""
Write-Host "Terminal dispatch finished. You can keep this terminal open for review."
"""
    write_powershell_script(script_path, script)
    write_text(status_path, json.dumps(status, ensure_ascii=False, indent=2) + "\n")
    scheme_state = state["questions"][question]["schemes"][scheme]
    scheme_state["dispatch_status"] = "terminal_script_created"
    scheme_state["dispatch_mode"] = "terminal"
    scheme_state["dispatch_created_at"] = now_iso()
    scheme_state["claude_session_mode"] = claude_session_mode
    scheme_state["claude_session_id"] = claude_session_id
    scheme_state["dispatch_prompt"] = rel(prompt_path)
    scheme_state["dispatch_terminal_script"] = rel(script_path)
    scheme_state["dispatch_terminal_status"] = rel(status_path)
    append_artifact(state, "claude_dispatch_terminal_script", script_path, f"{question} scheme {scheme}")
    append_artifact(state, "claude_dispatch_terminal_status", status_path, f"{question} scheme {scheme}")
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} Claude dispatch terminal",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl dispatch-claude",
            f"- 用途：生成 Windows/PowerShell 可见终端 Claude Code 执行脚本 `{question}` 方案 `{scheme}`。",
            f"- 关联文件：`{rel(prompt_path)}`, `{rel(script_path)}`, `{rel(status_path)}`",
            f"- 权限模式：`{permission_mode}`",
        ],
    )
    return script_path


def open_terminal_script(script_path: Path, terminal_app: str) -> None:
    if script_path.suffix.lower() == ".ps1":
        command = f"powershell -NoProfile -ExecutionPolicy Bypass -File {shlex.quote(str(script_path))}"
    else:
        command = f"bash {shlex.quote(str(script_path))}"
    if sys.platform == "darwin":
        app = terminal_app.strip() or "Terminal"
        if app.lower() == "iterm":
            osa = f'''
tell application "iTerm"
  activate
  create window with default profile
  tell current session of current window
    write text {json.dumps(command)}
  end tell
end tell
'''
        else:
            osa = f'''
tell application "Terminal"
  activate
  do script {json.dumps(command)}
end tell
'''
        result = subprocess.run(["osascript", "-e", osa], cwd=PROJECT_ROOT, check=False)
        if result.returncode != 0:
            raise SystemExit(result.returncode)
        return
    if script_path.suffix.lower() == ".ps1":
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                "Start-Process",
                "powershell",
                "-ArgumentList",
                f"'-NoProfile -ExecutionPolicy Bypass -NoExit -File \"{script_path}\"'",
                "-WorkingDirectory",
                str(PROJECT_ROOT),
            ],
            cwd=PROJECT_ROOT,
            check=False,
        )
    else:
        result = subprocess.run(["bash", str(script_path)], cwd=PROJECT_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


# ---------------------------------------------------------------------------
# Monitor scripts


def write_claude_monitor_script(state, question, scheme, interval, target_os="auto"):
    target_os = ensure_target_os(target_os)
    if target_os == "windows":
        return write_windows_monitor_script(state, question, scheme, interval)
    return write_posix_monitor_script(state, question, scheme, interval)


def write_posix_monitor_script(state, question, scheme, interval) -> Path:
    dispatch_monitor_dir().mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = dispatch_monitor_dir() / f"{stamp}_{question}_scheme_{scheme}_monitor.sh"
    qstate = state["questions"][question]
    scheme_state = qstate["schemes"][scheme]
    prompt_path = (
        scheme_state.get("dispatch_prompt")
        or scheme_state.get("claude_prompt")
        or f"04_claude_workorders/{question}_scheme_{scheme}_claude_prompt.md"
    )
    status_path = dispatch_terminal_status_path()
    report_path = expected_completion_path(question, scheme)
    standard_outputs = expected_standard_outputs(question, scheme)
    output_array = "\n".join(f'  "{rel(path)}"' for path in standard_outputs)
    interval_seconds = max(1, int(interval))
    script = f"""#!/usr/bin/env bash
set -u
cd {shlex.quote(str(PROJECT_ROOT))}

QUESTION={shlex.quote(question)}
SCHEME={shlex.quote(scheme)}
PROMPT_PATH={shlex.quote(prompt_path)}
STATUS_PATH={shlex.quote(rel(status_path))}
REPORT_PATH={shlex.quote(rel(report_path))}
INTERVAL={interval_seconds}
STANDARD_OUTPUTS=(
{output_array}
)

while true; do
  clear || true
  echo "=== Math Magic Claude Monitor ==="
  date "+%Y-%m-%d %H:%M:%S"
  echo
  echo "Task: $QUESTION scheme $SCHEME"
  echo "Prompt: $PROMPT_PATH"
  echo
  echo "Claude terminal status:"
  if [ -f "$STATUS_PATH" ]; then
    cat "$STATUS_PATH"
  else
    echo "No terminal status file yet. Dispatch Claude with agentctl dispatch-claude --mode auto."
  fi
  echo
  echo "Completion report:"
  if [ -s "$REPORT_PATH" ]; then
    echo "FOUND: $REPORT_PATH"
    echo
    tail -n 36 "$REPORT_PATH"
  else
    echo "WAITING: $REPORT_PATH"
  fi
  echo
  echo "Standard outputs:"
  for output in "${{STANDARD_OUTPUTS[@]}}"; do
    if [ -s "$output" ]; then
      printf "  [OK] %s\\n" "$output"
    else
      printf "  [--] %s\\n" "$output"
    fi
  done
  echo
  echo "Press q then Enter to close. Refreshing every $INTERVAL seconds."
  if read -r -t "$INTERVAL" answer; then
    if [ "$answer" = "q" ] || [ "$answer" = "Q" ]; then
      exit 0
    fi
  fi
done
"""
    write_text(script_path, script)
    script_path.chmod(0o755)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} Claude monitor terminal",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl open-claude-monitor",
            f"- 用途：打开 `{question}` 方案 `{scheme}` 的可见 Claude 监控终端。",
            f"- 关联文件：`{rel(script_path)}`, `{rel(status_path)}`, `{rel(report_path)}`",
        ],
    )
    return script_path


def write_windows_monitor_script(state, question, scheme, interval) -> Path:
    dispatch_monitor_dir().mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    script_path = dispatch_monitor_dir() / f"{stamp}_{question}_scheme_{scheme}_monitor.ps1"
    scheme_state = state["questions"][question]["schemes"][scheme]
    prompt_path = (
        scheme_state.get("dispatch_prompt")
        or scheme_state.get("claude_prompt")
        or f"04_claude_workorders/{question}_scheme_{scheme}_claude_prompt.md"
    )
    status_path = dispatch_terminal_status_path()
    report_path = expected_completion_path(question, scheme)
    standard_outputs = expected_standard_outputs(question, scheme)
    output_array = "@(" + ", ".join(ps_single_quote(rel(path)) for path in standard_outputs) + ")"
    interval_seconds = max(1, int(interval))
    script = f"""Set-StrictMode -Version Latest
Set-Location {ps_single_quote(PROJECT_ROOT)}

$Question = {ps_single_quote(question)}
$Scheme = {ps_single_quote(scheme)}
$PromptPath = {ps_single_quote(prompt_path)}
$StatusPath = {ps_single_quote(rel(status_path))}
$ReportPath = {ps_single_quote(rel(report_path))}
$Interval = {interval_seconds}
$StandardOutputs = {output_array}

while ($true) {{
  Clear-Host
  Write-Host "=== Math Magic Claude Monitor ==="
  Write-Host (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
  Write-Host ""
  Write-Host "Task: $Question scheme $Scheme"
  Write-Host "Prompt: $PromptPath"
  Write-Host ""
  Write-Host "Claude terminal status:"
  if (Test-Path $StatusPath) {{
    Get-Content -Raw -Encoding UTF8 $StatusPath
  }} else {{
    Write-Host "No terminal status file yet. Run the VS Code dispatch task first."
  }}
  Write-Host ""
  Write-Host "Completion report:"
  if ((Test-Path $ReportPath) -and ((Get-Item $ReportPath).Length -gt 0)) {{
    Write-Host "FOUND: $ReportPath"
    Write-Host ""
    Get-Content -Encoding UTF8 $ReportPath -Tail 36
  }} else {{
    Write-Host "WAITING: $ReportPath"
  }}
  Write-Host ""
  Write-Host "Standard outputs:"
  foreach ($Output in $StandardOutputs) {{
    if ((Test-Path $Output) -and ((Get-Item $Output).Length -gt 0)) {{
      Write-Host "  [OK] $Output"
    }} else {{
      Write-Host "  [--] $Output"
    }}
  }}
  Write-Host ""
  Write-Host "Press Ctrl+C to close. Refreshing every $Interval seconds."
  Start-Sleep -Seconds $Interval
}}
"""
    write_powershell_script(script_path, script)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} Claude monitor terminal",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl open-claude-monitor",
            f"- 用途：生成 `{question}` 方案 `{scheme}` 的 Windows/PowerShell Claude 监控终端脚本。",
            f"- 关联文件：`{rel(script_path)}`, `{rel(status_path)}`, `{rel(report_path)}`",
        ],
    )
    return script_path


# ---------------------------------------------------------------------------
# CLI dispatch entry


def run_claude_command(
    state: dict,
    question: str,
    scheme: str,
    prompt_path: Path,
    command: str,
    timeout: float,
) -> Path:
    dispatch_log_dir().mkdir(parents=True, exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = dispatch_log_dir() / f"{stamp}_{question}_scheme_{scheme}.log"
    args = shlex.split(command)
    if not args:
        raise SystemExit("empty Claude Code command")
    executable = shutil.which(args[0])
    if executable is None:
        raise SystemExit(f"Claude Code command not found: {args[0]}")
    prompt_text = read_text(prompt_path)
    # Bytes mode + manual decode keeps Windows GBK consoles from crashing on
    # Claude's mixed-language stdout. stdin still needs bytes when text=False.
    result = subprocess.run(
        args,
        input=prompt_text.encode("utf-8"),
        capture_output=True,
        cwd=PROJECT_ROOT,
        timeout=timeout if timeout > 0 else None,
        check=False,
    )
    stdout_text = (result.stdout or b"").decode("utf-8", errors="replace")
    stderr_text = (result.stderr or b"").decode("utf-8", errors="replace")
    log = [
        f"# Claude Dispatch Log: {question} Scheme {scheme}",
        "",
        f"- 时间：{now_iso()}",
        f"- 命令：`{command}`",
        f"- 提示词：`{rel(prompt_path)}`",
        f"- 返回码：{result.returncode}",
        "",
        "## stdout",
        "",
        "```text",
        stdout_text.rstrip(),
        "```",
        "",
        "## stderr",
        "",
        "```",
        stderr_text.rstrip(),
        "```",
        "",
    ]
    write_text(log_path, "\n".join(log))
    scheme_state = state["questions"][question]["schemes"][scheme]
    scheme_state["dispatch_status"] = "sent" if result.returncode == 0 else "failed"
    scheme_state["dispatch_mode"] = "cli"
    scheme_state["dispatch_created_at"] = now_iso()
    scheme_state["dispatch_prompt"] = rel(prompt_path)
    scheme_state["dispatch_log"] = rel(log_path)
    append_artifact(state, "claude_dispatch_log", log_path, f"{question} scheme {scheme}")
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} Claude dispatch cli",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl dispatch-claude",
            f"- 用途：通过 CLI 调用 Claude Code 执行 `{question}` 方案 `{scheme}`。",
            f"- 关联文件：`{rel(prompt_path)}`, `{rel(log_path)}`",
            f"- 返回码：{result.returncode}",
        ],
    )
    if result.returncode != 0:
        raise SystemExit(result.returncode)
    return log_path


def dispatch_fresh_after(state: dict, question: str, scheme: str):
    scheme_state = state["questions"][question]["schemes"][scheme]
    terminal_status = resolve_project_path(scheme_state.get("dispatch_terminal_status"))
    if terminal_status and terminal_status.exists():
        try:
            status_payload = json.loads(read_text(terminal_status))
        except json.JSONDecodeError:
            status_payload = {}
        if (
            status_payload.get("question") == question
            and status_payload.get("scheme") == scheme
            and status_payload.get("status") in {"running", "finished"}
        ):
            started = parse_iso_datetime(status_payload.get("run_started_at"))
            if started is not None:
                return started.timestamp()

    if scheme_state.get("dispatch_mode") == "cli":
        created = parse_iso_datetime(scheme_state.get("dispatch_created_at"))
        if created is not None:
            return created.timestamp()

    log_path = resolve_project_path(scheme_state.get("dispatch_log"))
    candidates = [path for path in [log_path] if path and path.exists()]
    if not candidates:
        return None
    return max(path.stat().st_mtime for path in candidates)


def is_fresh_artifact(path: Path, fresh_after) -> bool:
    if not path.exists() or path.stat().st_size <= 0:
        return False
    if fresh_after is None:
        return True
    return path.stat().st_mtime >= fresh_after


def record_claude_completion(state: dict, question: str, scheme: str, report_path: Path) -> Path:
    dest = expected_completion_path(question, scheme)
    if report_path.resolve() != dest.resolve():
        write_text(dest, read_text(report_path))
    qstate = state["questions"][question]
    scheme_state = qstate["schemes"][scheme]
    scheme_state["completion_report"] = rel(dest)
    scheme_state["status"] = "code_completed"
    scheme_state["detected_at"] = now_iso()
    selected = approved_schemes(qstate) or [scheme]
    qstate["code_completed"] = all(qstate["schemes"][s]["completion_report"] for s in selected)
    if qstate["code_completed"]:
        qstate["status"] = "code_completed"
        set_stage(state, "CODE_COMPLETED")
    append_artifact(state, "claude_completion_report", dest, f"{question} scheme {scheme}")
    return dest


def check_claude_once(
    state: dict,
    question: str,
    scheme: str,
    ingest: bool,
    create_review: bool,
    require_standard_outputs: bool,
    quiet: bool,
) -> bool:
    from ._review import create_review_file

    report_path = expected_completion_path(question, scheme)
    standard_outputs = expected_standard_outputs(question, scheme)
    fresh_after = dispatch_fresh_after(state, question, scheme)
    report_found = report_path.exists() and report_path.stat().st_size > 0
    report_ok = is_fresh_artifact(report_path, fresh_after)
    output_status = [(path, is_fresh_artifact(path, fresh_after)) for path in standard_outputs]
    outputs_ok = all(ok for _, ok in output_status)
    found = report_ok and (outputs_ok if require_standard_outputs else True)
    if not quiet:
        print("== Claude Completion Check ==")
        print(f"question: {question}")
        print(f"scheme: {scheme}")
        if fresh_after is not None:
            fresh_text = dt.datetime.fromtimestamp(fresh_after).isoformat(timespec="seconds")
            print(f"fresh_after: {fresh_text}")
        report_label = "found" if report_ok else ("stale" if report_found else "missing")
        print(f"completion_report: {report_label} {rel(report_path)}")
        for path, ok in output_status:
            exists = path.exists() and path.stat().st_size > 0
            label = "found" if ok else ("stale" if exists else "missing")
            print(f"standard_output: {label} {rel(path)}")
    if found and ingest:
        dest = record_claude_completion(state, question, scheme, report_path)
        if not quiet:
            print(f"ingested: {rel(dest)}")
    if found and create_review:
        review = create_review_file(state, question, scheme)
        if not quiet:
            print(f"review_template: {rel(review)}")
    return found


def command_ingest_claude_report(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    src = Path(args.report)
    if not src.is_absolute():
        src = PROJECT_ROOT / src
    if not src.exists():
        raise SystemExit(f"report not found: {src}")
    dest = record_claude_completion(state, question, scheme, src)
    save_state(state)
    print(dest)


def command_check_claude(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    found = check_claude_once(
        state=state,
        question=question,
        scheme=scheme,
        ingest=args.ingest,
        create_review=args.create_review,
        require_standard_outputs=args.require_standard_outputs,
        quiet=False,
    )
    save_state(state)
    if not found and args.fail_missing:
        raise SystemExit(1)


def command_watch_claude(args):
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    start = time.monotonic()
    print(f"watching Claude completion for {question} scheme {scheme}")
    print(f"interval={args.interval}s timeout={args.timeout}s")
    while True:
        with workflow_lock():
            state = load_state()
            found = check_claude_once(
                state=state,
                question=question,
                scheme=scheme,
                ingest=args.ingest,
                create_review=args.create_review,
                require_standard_outputs=args.require_standard_outputs,
                quiet=args.quiet,
            )
            save_state(state)
        if found:
            print(f"Claude completion detected for {question} scheme {scheme}")
            return
        if args.once:
            print(f"Claude completion not found for {question} scheme {scheme}")
            return
        if args.timeout > 0 and time.monotonic() - start >= args.timeout:
            print(f"timeout waiting for {question} scheme {scheme}")
            raise SystemExit(1)
        time.sleep(args.interval)


def command_dispatch_claude(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    assert_question_unlocked(state, question)
    if state["questions"][question]["schemes"][scheme].get("status") not in SELECTED_SCHEME_STATUSES:
        raise SystemExit(f"{question} scheme {scheme} is not approved or under review; cannot dispatch")
    prompt_path = resolve_dispatch_prompt(state, question, scheme, args.prompt, args.revision)
    mode = args.mode
    command = configured_claude_command(args)
    if mode == "auto":
        mode = "terminal"
    if mode == "terminal":
        script_path = write_terminal_dispatch_script(
            state=state,
            question=question,
            scheme=scheme,
            prompt_path=prompt_path,
            permission_mode=args.terminal_permission_mode,
            claude_session_mode=args.claude_session_mode,
            claude_session_id=args.claude_session_id or None,
            target_os=current_target_os(),
        )
        save_state(state)
        print(script_path)
        print(dispatch_terminal_status_path())
        if args.no_open:
            print("created visible Claude Code terminal script; not opened because --no-open was set")
            return
        open_terminal_script(script_path, terminal_app=args.terminal_app)
        state["questions"][question]["schemes"][scheme]["dispatch_opened_at"] = now_iso()
        save_state(state)
        print("opened visible Claude Code terminal in the project root")
        if args.watch:
            command_watch_claude(
                argparse.Namespace(
                    question=question,
                    scheme=scheme,
                    interval=args.interval,
                    timeout=args.watch_timeout,
                    once=False,
                    ingest=True,
                    create_review=True,
                    require_standard_outputs=args.require_standard_outputs,
                    quiet=False,
                )
            )
        return
    if mode != "cli":
        raise SystemExit(f"unsupported dispatch mode after cleanup: {mode}")
    if not command:
        raise SystemExit(
            "Claude Code CLI command is not configured. Pass --command, set CLAUDE_CODE_COMMAND, "
            "or create 04_claude_workorders/claude_dispatch_config.json."
        )
    log_path = run_claude_command(state, question, scheme, prompt_path, command, timeout=args.timeout)
    save_state(state)
    print(log_path)
    if args.watch:
        command_watch_claude(
            argparse.Namespace(
                question=question,
                scheme=scheme,
                interval=args.interval,
                timeout=args.watch_timeout,
                once=False,
                ingest=True,
                create_review=True,
                require_standard_outputs=args.require_standard_outputs,
                quiet=False,
            )
        )


def command_open_claude_monitor(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    script_path = write_claude_monitor_script(state, question, scheme, interval=args.interval, target_os=args.target_os)
    append_artifact(state, "claude_monitor_terminal_script", script_path, f"{question} scheme {scheme}")
    save_state(state)
    print(script_path)
    if args.no_open:
        return
    open_terminal_script(script_path, terminal_app=args.terminal_app)
    print("opened Claude monitor terminal")


def command_install_vscode_tasks(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    target_os = ensure_target_os(args.target_os)
    if state["questions"][question]["schemes"][scheme].get("status") not in SELECTED_SCHEME_STATUSES:
        raise SystemExit(f"{question} scheme {scheme} is not approved or under review; cannot install dispatch task")
    prompt_path = resolve_dispatch_prompt(state, question, scheme, args.prompt, args.revision)
    dispatch_script = write_terminal_dispatch_script(
        state=state,
        question=question,
        scheme=scheme,
        prompt_path=prompt_path,
        permission_mode=args.terminal_permission_mode,
        claude_session_mode=args.claude_session_mode,
        claude_session_id=args.claude_session_id or None,
        target_os=target_os,
    )
    monitor_script = write_claude_monitor_script(state, question, scheme, interval=args.interval, target_os=target_os)
    tasks_path = write_vscode_tasks(question, scheme, dispatch_script, monitor_script, target_os=target_os)
    append_artifact(state, "vscode_tasks", tasks_path, f"{question} scheme {scheme}")
    append_artifact(state, "claude_monitor_terminal_script", monitor_script, f"{question} scheme {scheme}")
    save_state(state)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} VSCode Claude terminal tasks",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl install-vscode-tasks",
            f"- 用途：为 `{question}` 方案 `{scheme}` 生成 VS Code 集成终端任务。",
            f"- 关联文件：`{rel(tasks_path)}`, `{rel(dispatch_script)}`, `{rel(monitor_script)}`",
            f"- 权限模式：`{args.terminal_permission_mode}`",
            f"- 目标系统：`{target_os}`",
        ],
    )
    print(tasks_path)
    print(f"Run VS Code task: Math Magic: Claude {question}-{scheme} visible session")


def write_vscode_tasks(question, scheme, dispatch_script, monitor_script, target_os):
    from ._env import vscode_shell_task

    path = vscode_tasks_path()
    if path.exists():
        try:
            payload = json.loads(read_text(path))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"cannot update invalid VS Code tasks JSON: {path}: {exc}") from exc
    else:
        payload = {"version": "2.0.0", "tasks": []}
    payload["version"] = payload.get("version") or "2.0.0"
    tasks = payload.setdefault("tasks", [])
    dispatch_label = f"Math Magic: Claude {question}-{scheme} dispatch"
    monitor_label = f"Math Magic: Claude {question}-{scheme} monitor"
    watch_label = f"Math Magic: Claude {question}-{scheme} watch"
    session_label = f"Math Magic: Claude {question}-{scheme} visible session"
    managed_labels = {dispatch_label, monitor_label, watch_label, session_label}
    tasks[:] = [task for task in tasks if task.get("label") not in managed_labels]
    tasks.extend(
        [
            vscode_shell_task(
                label=monitor_label,
                command=vscode_script_command(target_os),
                args=vscode_script_args(monitor_script, target_os),
                dedicated_panel=True,
                focus=False,
            ),
            vscode_shell_task(
                label=dispatch_label,
                command=vscode_script_command(target_os),
                args=vscode_script_args(dispatch_script, target_os),
                dedicated_panel=True,
                focus=True,
            ),
            vscode_shell_task(
                label=watch_label,
                command="python",
                args=[
                    "05_code/tools/agentctl.py",
                    "watch-claude",
                    "--question",
                    question,
                    "--scheme",
                    scheme,
                    "--interval",
                    "15",
                    "--ingest",
                    "--create-review",
                    "--require-standard-outputs",
                ],
                dedicated_panel=True,
                focus=False,
            ),
            {
                "label": session_label,
                "dependsOrder": "parallel",
                "dependsOn": [monitor_label, dispatch_label],
                "problemMatcher": [],
                "presentation": {
                    "reveal": "always",
                    "panel": "dedicated",
                    "clear": True,
                    "focus": True,
                },
            },
        ]
    )
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path


def vscode_script_command(target_os: str) -> str:
    return "powershell" if target_os == "windows" else "bash"


def vscode_script_args(script_path: Path, target_os: str) -> list[str]:
    if target_os == "windows":
        return ["-NoProfile", "-ExecutionPolicy", "Bypass", "-File", rel(script_path)]
    return [rel(script_path)]
