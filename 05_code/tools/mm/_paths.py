"""Project path constants and dispatch directory helpers."""

from __future__ import annotations

from pathlib import Path

# Project root is two levels above this file: 05_code/tools/mm/_paths.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_PATH = PROJECT_ROOT / "00_shared" / "workflow_state.json"
LOCK_PATH = PROJECT_ROOT / "00_shared" / ".workflow_state.lock"

QUESTIONS = ["Q1", "Q2", "Q3", "Q4", "Q5"]
SCHEMES = ["A", "B", "C"]
STAGES = [
    "INIT",
    "PROBLEM_LOADED",
    "SCHEMES_GENERATED",
    "SCHEMES_APPROVED",
    "CLAUDE_WORKORDERS_CREATED",
    "CODE_COMPLETED",
    "CODE_REVIEWED",
    "MODEL_CONFIRMED",
    "FIGURES_GENERATED",
    "FIGURES_APPROVED",
    "PAPER_WRITTEN",
    "APPENDIX_READY",
    "FINAL_REVIEW",
]
SELECTED_SCHEME_STATUSES = {
    "approved_to_run",
    "workorder_created",
    "code_completed",
    "review_template_created",
    "review_pass",
    "review_revise",
    "review_blocked",
}


def expected_completion_path(question: str, scheme: str) -> Path:
    return PROJECT_ROOT / "04_claude_workorders" / "completions" / f"{question}_scheme_{scheme}_completion.md"


def expected_standard_outputs(question: str, scheme: str) -> list[Path]:
    return [
        PROJECT_ROOT / "06_results" / question / "tables" / f"scheme_{scheme}_metrics.csv",
        PROJECT_ROOT / "06_results" / question / "figures" / f"scheme_{scheme}_raw.png",
        PROJECT_ROOT / "06_results" / question / "logs" / f"scheme_{scheme}_run.md",
    ]


def question_section_path(question: str) -> Path:
    return PROJECT_ROOT / "07_paper" / "sections" / f"model_{question.lower()}.tex"


def paper_summary_sections() -> list[Path]:
    return [
        PROJECT_ROOT / "07_paper" / "sections" / "abstract.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "problem_analysis.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "model_validation.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "evaluation.tex",
        PROJECT_ROOT / "07_paper" / "appendix" / "ai_usage_appendix.tex",
    ]


def dispatch_log_dir() -> Path:
    return PROJECT_ROOT / "04_claude_workorders" / "dispatch_logs"


def dispatch_terminal_dir() -> Path:
    return PROJECT_ROOT / "04_claude_workorders" / "terminal_runs"


def dispatch_monitor_dir() -> Path:
    return dispatch_terminal_dir() / "monitors"


def dispatch_terminal_status_path() -> Path:
    return dispatch_terminal_dir() / "CURRENT_TERMINAL_STATUS.json"


def dispatch_config_path() -> Path:
    return PROJECT_ROOT / "04_claude_workorders" / "claude_dispatch_config.json"


def vscode_tasks_path() -> Path:
    return PROJECT_ROOT / ".vscode" / "tasks.json"


def state_snapshots_dir() -> Path:
    return PROJECT_ROOT / "00_shared" / "snapshots"


def resolve_project_path(path) -> Path | None:
    if not path:
        return None
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = PROJECT_ROOT / candidate
    return candidate


def safe_project_file(path: Path) -> bool:
    try:
        resolved = path.resolve()
        root = PROJECT_ROOT.resolve()
        return resolved.is_file() and (resolved == root or root in resolved.parents)
    except OSError:
        return False
