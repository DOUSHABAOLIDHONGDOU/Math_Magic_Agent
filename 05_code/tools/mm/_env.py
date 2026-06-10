"""Environment checks, doctor, VS Code task installer.

Phase 6b: ``command_readiness`` now emits ``suggest_next_actions`` self-healing
hints so users see "install MiKTeX" / "run prepare-schemes" instead of staring
at a status dump.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

from ._paths import (
    PROJECT_ROOT,
    QUESTIONS,
    STATE_PATH,
    vscode_tasks_path,
)
from ._state import (
    active_question_ids,
    load_state,
    next_question_to_solve,
)
from ._util import (
    ensure_target_os,
    read_text,
    rel,
    write_text,
)


def command_env_check(args):
    modules = [
        "pypdf",
        "fitz",
        "pytesseract",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scipy",
        "sklearn",
        "openpyxl",
        "xlrd",
        "statsmodels",
        "networkx",
    ]
    print("== Python Modules ==")
    for module in modules:
        ok = importlib.util.find_spec(module) is not None
        print(f"{module}: {'ok' if ok else 'missing'}")
    print()
    print("== Commands ==")
    for command in ["xelatex", "tesseract"]:
        found = shutil.which(command)
        print(f"{command}: {found or 'missing'}")
    tesseract = shutil.which("tesseract")
    if tesseract:
        result = subprocess.run(
            [tesseract, "--list-langs"],
            capture_output=True,
            check=False,
        )
        langs = (result.stdout or b"").decode("utf-8", errors="replace")
        print(f"tesseract lang chi_sim: {'ok' if 'chi_sim' in langs else 'missing'}")
        print(f"tesseract lang eng: {'ok' if 'eng' in langs else 'missing'}")
    print()
    cache_dir = PROJECT_ROOT / ".cache" / "matplotlib"
    cache_dir.mkdir(parents=True, exist_ok=True)
    print(f"Matplotlib cache: {cache_dir}")


def command_doctor(args):
    target_os = ensure_target_os(args.target_os)
    modules = [
        "pypdf",
        "fitz",
        "pytesseract",
        "numpy",
        "pandas",
        "matplotlib",
        "seaborn",
        "scipy",
        "sklearn",
        "openpyxl",
        "xlrd",
        "statsmodels",
        "networkx",
        "PIL",
        "rank_bm25",
    ]
    commands = ["python", "xelatex", "tesseract", "node", "npm", "claude", "code"]
    checks: list[tuple[str, bool, str]] = []
    for module in modules:
        checks.append(
            (
                f"python module {module}",
                importlib.util.find_spec(module) is not None,
                "install environment.yml",
            )
        )
    for command in commands:
        found = shutil.which(command)
        required = command != "code"
        checks.append(
            (
                f"command {command}",
                bool(found) or not required,
                found or ("optional but useful for VS Code tasks" if command == "code" else "missing"),
            )
        )
    excellent_dir = PROJECT_ROOT / "02_references" / "excellent_papers"
    excellent_count = len(list(excellent_dir.rglob("*.pdf"))) if excellent_dir.exists() else 0
    checks.append(("excellent papers", excellent_count > 0, f"{excellent_count} pdf files"))
    checks.append(("paper template", (PROJECT_ROOT / "07_paper" / "main.tex").exists(), "07_paper/main.tex"))
    checks.append(("template raw archive", (PROJECT_ROOT / "07_paper" / "template_raw").exists(), "07_paper/template_raw"))
    checks.append(("workflow state", STATE_PATH.exists(), rel(STATE_PATH)))
    if args.write_vscode_smoke_task:
        task_path = write_vscode_smoke_task(target_os=target_os)
        checks.append(("VS Code Claude smoke task", True, rel(task_path)))
    else:
        checks.append(("VS Code tasks", vscode_tasks_path().exists(), rel(vscode_tasks_path())))
    print("== Math Magic Doctor ==")
    print(f"target_os: {target_os}")
    failed = False
    for name, ok, detail in checks:
        print(f"{name}: {'ok' if ok else 'missing'} ({detail})")
        failed = failed or not ok
    print()
    if args.write_vscode_smoke_task:
        print("Run VS Code task: Math Magic: Claude smoke test")
        print("It should open an integrated terminal and print the Claude Code version.")
    if failed and args.strict:
        raise SystemExit(1)


def write_vscode_smoke_task(target_os: str) -> Path:
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
    smoke_label = "Math Magic: Claude smoke test"
    tasks[:] = [task for task in tasks if task.get("label") != smoke_label]
    if target_os == "windows":
        command = "powershell"
        args = [
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            "Write-Host 'Math Magic Claude smoke test'; claude --version; python 05_code/tools/agentctl.py env-check",
        ]
    else:
        command = "bash"
        args = ["-lc", "echo 'Math Magic Claude smoke test'; claude --version; python 05_code/tools/agentctl.py env-check"]
    tasks.append(vscode_shell_task(smoke_label, command, args, dedicated_panel=True, focus=True))
    write_text(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return path


def vscode_shell_task(label, command, args, dedicated_panel, focus) -> dict:
    return {
        "label": label,
        "type": "shell",
        "command": command,
        "args": args,
        "options": {"cwd": "${workspaceFolder}"},
        "presentation": {
            "reveal": "always",
            "panel": "dedicated" if dedicated_panel else "shared",
            "clear": True,
            "focus": focus,
        },
        "problemMatcher": [],
    }


def command_tools(args):
    registry_path = PROJECT_ROOT / "05_code" / "tools" / "tool_registry.json"
    registry = json.loads(read_text(registry_path))
    print(f"Tool registry version: {registry['version']}")
    print(f"Project: {registry['project']}")
    print()
    for tool in registry["tools"]:
        print(f"== {tool['id']} ==")
        print(f"name: {tool['name']}")
        print(f"path: {tool['path']}")
        print(f"owner: {tool['owner']}")
        print(f"purpose: {tool['purpose']}")
        print("commands:")
        for command in tool.get("command_examples", []):
            print(f"  - {command}")
        print()


def command_status(args):
    from ._util import extract_section

    state = load_state()
    state_path = PROJECT_ROOT / "00_shared" / "PROJECT_STATE.md"
    boundary_path = PROJECT_ROOT / "00_shared" / "QUESTION_BOUNDARIES.md"
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Machine state: {STATE_PATH}")
    print(f"Stage: {state['stage']}")
    print(f"Updated at: {state['updated_at']}")
    print()
    print("== Project State ==")
    print(extract_section(read_text(state_path), "当前阶段"))
    print(extract_section(read_text(state_path), "全局技术路线"))
    print(extract_section(read_text(state_path), "三次审批状态"))
    print()
    print("== Boundaries ==")
    print(extract_section(read_text(boundary_path), "待确认边界"))


# ---------------------------------------------------------------------------
# Phase 6b: readiness with self-healing suggestions


def suggest_next_actions(state: dict) -> list[str]:
    """Translate the current state into human-actionable hints."""
    hints: list[str] = []
    if not state["problem"].get("title"):
        hints.append("→ 题目未导入，运行 `python 05_code/tools/agentctl.py import-problem --statement <题面.md>`")
        return hints
    if not state["language"].get("approved"):
        hints.append("→ 默认实现语言未审批，运行 `agentctl.py approve-language --language Python`")

    if not shutil.which("xelatex"):
        hints.append(
            "→ 未在 PATH 找到 xelatex。Windows 安装 MiKTeX：`https://miktex.org/download`，或 `conda install -c conda-forge tectonic`"
        )

    for question in active_question_ids(state):
        qstate = state["questions"][question]
        if qstate.get("paper_written"):
            continue
        scheme_path = PROJECT_ROOT / "03_methods" / question
        if not qstate.get("schemes_generated") and not scheme_path.exists():
            hints.append(f"→ {question} 方案未生成，运行 `agentctl.py prepare-schemes --question {question}`")
            break
        if qstate.get("status") == "paper_compile_failed":
            hints.append(
                f"→ {question} PDF 编译失败：先解决 xelatex 缺失，然后重新运行 "
                f"`agentctl.py write-question-paper --question {question}`"
            )
            break
        if not qstate.get("schemes_approved"):
            hints.append(
                f"→ {question} 方案未审批，运行 `agentctl.py create-approval-brief --question {question}` 并在聊天中告知用户审批"
            )
            break
        if not qstate.get("code_completed"):
            hints.append(
                f"→ {question} Claude Code 尚未完成，运行 `agentctl.py watch-claude --question {question} --scheme <X> --interval 30 --ingest --create-review`"
            )
            break
        if not qstate.get("model_confirmed"):
            hints.append(
                f"→ {question} 模型未确认，运行 `agentctl.py create-model-confirmation-brief --question {question}` 并在聊天中转述选项"
            )
            break
        if not qstate.get("paper_written"):
            hints.append(f"→ {question} 单题未入文，运行 `agentctl.py write-question-paper --question {question}`")
            break
    return hints


def command_readiness(args):
    state = load_state()
    active_questions = active_question_ids(state)
    next_q = next_question_to_solve(state)
    print("== Workflow Readiness ==")
    print(f"stage: {state['stage']}")
    print(f"trust profile: {state.get('trust_profile', 'strict')}")
    print(f"workflow mode: {state.get('workflow', {}).get('mode', 'sequential')}")
    print(f"problem loaded: {'ok' if state['problem']['title'] else 'pending'}")
    print(f"language approved: {'ok' if state['language']['approved'] else 'pending'}")
    print(f"question order: {', '.join(active_questions)}")
    print(f"current unlocked question: {next_q or 'all question papers written'}")
    for question in active_questions:
        qstate = state["questions"][question]
        print(
            f"{question}: status={qstate['status']} schemes={qstate['schemes_generated']} "
            f"approved={qstate['schemes_approved']} workorders={qstate['workorders_created']} "
            f"model={qstate['model_confirmed']} figures={qstate['figures_approved']} paper={qstate['paper_written']}"
        )
    suggestions = suggest_next_actions(state)
    if suggestions:
        print()
        print("== 自愈建议 ==")
        for hint in suggestions:
            print(hint)
