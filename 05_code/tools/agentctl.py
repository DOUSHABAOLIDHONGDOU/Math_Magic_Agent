#!/usr/bin/env python3
"""Math Magic workflow helper — CLI entry point.

All the heavy lifting lives in the :mod:`mm` package. This file owns nothing
but argument parsing and command dispatch. See ``mm/__init__.py`` for the
module layout.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from mm import _project_state  # noqa: F401 - registers PROJECT_STATE.md updater
from mm._commands import (
    command_approve_figures,
    command_approve_language,
    command_approve_schemes,
    command_archive_stale_artifacts,
    command_confirm_model,
    command_create_approval_brief,
    command_create_claude_prompt,
    command_create_model_confirmation_brief,
    command_create_workorder,
    command_create_workorders,
    command_gen_ai_log,
    command_import_problem,
    command_init_state,
    command_mark_paper_written,
    command_prepare_schemes,
    command_scan_data,
    command_set_active_question,
    command_set_trust_profile,
)
from mm._dispatch import (
    command_check_claude,
    command_dispatch_claude,
    command_ingest_claude_report,
    command_install_vscode_tasks,
    command_open_claude_monitor,
    command_watch_claude,
)
from mm._eda import command_auto_eda
from mm._env import (
    command_doctor,
    command_env_check,
    command_readiness,
    command_status,
    command_tools,
)
from mm._figure_lint import command_figure_lint
from mm._paper import (
    command_finalize_summary_paper,
    command_latex_check,
    command_layout_check,
    command_paper_check,
    command_write_question_paper,
)
from mm._rag import command_index_papers, command_rag_status, command_retrieve_context
from mm._review import (
    command_compare_schemes,
    command_create_review,
    command_mark_reviewed,
)
from mm._state import question_choices, workflow_lock
from mm._util import add_boolean_optional_argument, configure_console_output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Math Magic workflow helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_state = subparsers.add_parser("init-state", help="create or reset machine-readable workflow state")
    init_state.add_argument("--force", action="store_true")
    init_state.set_defaults(func=command_init_state)

    status = subparsers.add_parser("status", help="print shared project state")
    status.set_defaults(func=command_status)

    env_check = subparsers.add_parser("env-check", help="check local runtime dependencies")
    env_check.set_defaults(func=command_env_check)

    doctor = subparsers.add_parser(
        "doctor", help="run first-install checks and optionally install a VS Code Claude smoke task"
    )
    doctor.add_argument("--target-os", default="auto", choices=["auto", "windows", "posix"])
    doctor.add_argument("--write-vscode-smoke-task", action="store_true")
    doctor.add_argument("--strict", action="store_true")
    doctor.set_defaults(func=command_doctor)

    tools = subparsers.add_parser("tools", help="print registered workflow tools")
    tools.set_defaults(func=command_tools)

    import_problem = subparsers.add_parser("import-problem", help="import a training problem statement")
    import_problem.add_argument("--statement", type=Path, default=None)
    import_problem.add_argument("--title", default=None)
    import_problem.add_argument("--problem-id", default=None)
    import_problem.add_argument("--data-dir", type=Path, default=None)
    import_problem.add_argument("--num-questions", type=int, default=3)
    add_boolean_optional_argument(
        import_problem,
        "--archive-existing-generated",
        default=True,
        help="archive generated artifacts from the previous problem before importing a new one",
    )
    import_problem.set_defaults(func=command_import_problem)

    archive_stale = subparsers.add_parser(
        "archive-stale-artifacts", help="archive generated artifacts that belong to an old problem/topic"
    )
    archive_stale.add_argument(
        "--profile", choices=["detected-old-topic", "all-generated"], default="detected-old-topic"
    )
    archive_stale.add_argument("--keyword", action="append", default=[])
    archive_stale.add_argument("--current-keyword", action="append", default=[])
    archive_stale.add_argument("--path", type=Path, action="append", default=[])
    archive_stale.add_argument(
        "--reason", default="archive stale generated artifacts before continuing the current problem"
    )
    archive_stale.add_argument("--dry-run", action="store_true")
    archive_stale.add_argument("--force", action="store_true")
    archive_stale.add_argument(
        "--no-related", action="store_true", help="do not include related figures/manifests inferred from stale text files"
    )
    archive_stale.set_defaults(func=command_archive_stale_artifacts)

    scan_data = subparsers.add_parser("scan-data", help="scan raw data files into data_dictionary.md")
    scan_data.add_argument("--data-dir", type=Path, required=True)
    scan_data.add_argument("--out", type=Path, default=None)
    scan_data.add_argument("--sample-rows", type=int, default=200)
    scan_data.add_argument("--include-unsupported", action="store_true")
    scan_data.set_defaults(func=command_scan_data)

    approve_language = subparsers.add_parser("approve-language", help="approve the default implementation language")
    approve_language.add_argument("--language", default="Python")
    approve_language.add_argument("--decision-id", default=None)
    approve_language.add_argument("--notes", default="")
    approve_language.set_defaults(func=command_approve_language)

    active_question = subparsers.add_parser("set-active-question", help="set the current sequential question")
    active_question.add_argument("--question", required=True, choices=question_choices())
    active_question.add_argument("--defer-later", action="store_true")
    active_question.set_defaults(func=command_set_active_question)

    prepare_schemes = subparsers.add_parser("prepare-schemes", help="prepare A/B/C scheme files and Codex prompt")
    prepare_schemes.add_argument("--question", required=True, choices=question_choices())
    prepare_schemes.add_argument("--overwrite", action="store_true")
    prepare_schemes.add_argument("--force", action="store_true")
    prepare_schemes.set_defaults(func=command_prepare_schemes)

    approval_brief = subparsers.add_parser("create-approval-brief", help="create a user-facing A/B/C scheme approval brief")
    approval_brief.add_argument("--question", required=True, choices=question_choices())
    approval_brief.add_argument("--force", action="store_true")
    approval_brief.set_defaults(func=command_create_approval_brief)

    model_brief = subparsers.add_parser(
        "create-model-confirmation-brief", help="create user-facing model confirmation options"
    )
    model_brief.add_argument("--question", required=True, choices=question_choices())
    model_brief.add_argument("--scheme", choices=["A", "B", "C", "a", "b", "c"], default=None)
    model_brief.add_argument("--force", action="store_true")
    model_brief.set_defaults(func=command_create_model_confirmation_brief)

    approve_schemes = subparsers.add_parser("approve-schemes", help="record user approval for schemes")
    approve_schemes.add_argument("--question", required=True, choices=question_choices())
    approve_schemes.add_argument("--schemes", default="A,B,C")
    approve_schemes.add_argument("--decision-id", default=None)
    approve_schemes.add_argument("--notes", default="")
    approve_schemes.add_argument("--force", action="store_true")
    approve_schemes.set_defaults(func=command_approve_schemes)

    workorder = subparsers.add_parser("create-workorder", help="create a Claude Code workorder from template")
    workorder.add_argument("--question", required=True, choices=question_choices())
    workorder.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    workorder.add_argument("--workorder-id", default=None)
    workorder.add_argument("--out", type=Path, default=None)
    workorder.add_argument("--force", action="store_true")
    workorder.set_defaults(func=command_create_workorder)

    workorders = subparsers.add_parser("create-workorders", help="create Claude Code workorders for multiple schemes")
    workorders.add_argument("--question", required=True, choices=question_choices())
    workorders.add_argument("--schemes", default="A,B,C")
    workorders.add_argument("--force", action="store_true")
    workorders.set_defaults(func=command_create_workorders)

    claude_prompt = subparsers.add_parser("create-claude-prompt", help="create a copyable Claude Code execution prompt")
    claude_prompt.add_argument("--question", required=True, choices=question_choices())
    claude_prompt.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    claude_prompt.add_argument("--force", action="store_true")
    claude_prompt.set_defaults(func=command_create_claude_prompt)

    dispatch = subparsers.add_parser(
        "dispatch-claude", help="send a prompt to Claude Code; auto opens a visible Terminal session"
    )
    dispatch.add_argument("--question", required=True, choices=question_choices())
    dispatch.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    dispatch.add_argument("--prompt", type=Path, default=None)
    dispatch.add_argument("--revision", action="store_true", help="dispatch the latest revision prompt")
    dispatch.add_argument("--mode", choices=["auto", "terminal", "cli"], default="auto")
    dispatch.add_argument("--command", default="")
    dispatch.add_argument("--terminal-app", default="Terminal", choices=["Terminal", "iTerm"])
    dispatch.add_argument(
        "--terminal-permission-mode",
        default="bypassPermissions",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
    )
    dispatch.add_argument(
        "--claude-session-mode",
        default="continue",
        choices=["continue", "new", "resume"],
        help="continue reuses Claude Code's latest conversation in this project directory",
    )
    dispatch.add_argument("--claude-session-id", default="", help="session id used with --claude-session-mode resume")
    dispatch.add_argument("--timeout", type=float, default=0.0)
    dispatch.add_argument("--watch", action="store_true")
    dispatch.add_argument("--watch-timeout", type=float, default=0.0)
    dispatch.add_argument("--interval", type=float, default=30.0)
    dispatch.add_argument("--require-standard-outputs", action="store_true")
    dispatch.add_argument(
        "--no-open", action="store_true", help="create the terminal dispatch script without opening it"
    )
    dispatch.set_defaults(func=command_dispatch_claude)

    monitor = subparsers.add_parser(
        "open-claude-monitor", help="open a visible Terminal dashboard for Claude task status"
    )
    monitor.add_argument("--question", required=True, choices=question_choices())
    monitor.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    monitor.add_argument("--interval", type=float, default=5.0)
    monitor.add_argument("--terminal-app", default="Terminal", choices=["Terminal", "iTerm"])
    monitor.add_argument("--target-os", default="auto", choices=["auto", "windows", "posix"])
    monitor.add_argument("--no-open", action="store_true", help="only create the monitor script")
    monitor.set_defaults(func=command_open_claude_monitor)

    vscode_tasks = subparsers.add_parser(
        "install-vscode-tasks",
        help="install VS Code integrated-terminal tasks for Claude dispatch and monitoring",
    )
    vscode_tasks.add_argument("--question", required=True, choices=question_choices())
    vscode_tasks.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    vscode_tasks.add_argument("--prompt", type=Path, default=None)
    vscode_tasks.add_argument("--revision", action="store_true", help="use the latest revision prompt")
    vscode_tasks.add_argument("--interval", type=float, default=5.0)
    vscode_tasks.add_argument("--target-os", default="auto", choices=["auto", "windows", "posix"])
    vscode_tasks.add_argument(
        "--terminal-permission-mode",
        default="bypassPermissions",
        choices=["acceptEdits", "auto", "bypassPermissions", "default", "dontAsk", "plan"],
    )
    vscode_tasks.add_argument("--claude-session-mode", default="continue", choices=["continue", "new", "resume"])
    vscode_tasks.add_argument("--claude-session-id", default="")
    vscode_tasks.set_defaults(func=command_install_vscode_tasks)

    ingest = subparsers.add_parser("ingest-claude-report", help="ingest a Claude Code completion report")
    ingest.add_argument("--question", required=True, choices=question_choices())
    ingest.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    ingest.add_argument("--report", type=Path, required=True)
    ingest.set_defaults(func=command_ingest_claude_report)

    check_claude = subparsers.add_parser(
        "check-claude", help="check whether Claude Code has written a completion report"
    )
    check_claude.add_argument("--question", required=True, choices=question_choices())
    check_claude.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    check_claude.add_argument("--ingest", action="store_true")
    check_claude.add_argument("--create-review", action="store_true")
    check_claude.add_argument("--require-standard-outputs", action="store_true")
    check_claude.add_argument("--fail-missing", action="store_true")
    check_claude.set_defaults(func=command_check_claude)

    watch_claude = subparsers.add_parser(
        "watch-claude", help="poll for Claude Code completion and optionally ingest it"
    )
    watch_claude.add_argument("--question", required=True, choices=question_choices())
    watch_claude.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    watch_claude.add_argument("--interval", type=float, default=30.0)
    watch_claude.add_argument("--timeout", type=float, default=0.0)
    watch_claude.add_argument("--once", action="store_true")
    watch_claude.add_argument("--ingest", action="store_true")
    watch_claude.add_argument("--create-review", action="store_true")
    watch_claude.add_argument("--require-standard-outputs", action="store_true")
    watch_claude.add_argument("--quiet", action="store_true")
    watch_claude.set_defaults(func=command_watch_claude)

    review = subparsers.add_parser("create-review", help="create a Codex review template for one scheme")
    review.add_argument("--question", required=True, choices=question_choices())
    review.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    review.set_defaults(func=command_create_review)

    mark_reviewed = subparsers.add_parser("mark-reviewed", help="record Codex review result")
    mark_reviewed.add_argument("--question", required=True, choices=question_choices())
    mark_reviewed.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    mark_reviewed.add_argument(
        "--result", required=True, choices=["PASS", "REVISE", "BLOCKED", "pass", "revise", "blocked"]
    )
    mark_reviewed.set_defaults(func=command_mark_reviewed)

    compare = subparsers.add_parser("compare-schemes", help="data-driven comparison of scheme metrics CSVs")
    compare.add_argument("--question", required=True, choices=question_choices())
    compare.set_defaults(func=command_compare_schemes)

    confirm = subparsers.add_parser("confirm-model", help="record final model confirmation")
    confirm.add_argument("--question", required=True, choices=question_choices())
    confirm.add_argument("--scheme", required=True, choices=["A", "B", "C", "a", "b", "c"])
    confirm.add_argument("--decision-id", default=None)
    confirm.add_argument("--notes", default="")
    confirm.add_argument("--force", action="store_true")
    confirm.set_defaults(func=command_confirm_model)

    figures = subparsers.add_parser("approve-figures", help="record user approval for final figures")
    figures.add_argument("--question", required=True, choices=question_choices())
    figures.add_argument("--figures", default="")
    figures.add_argument("--decision-id", default=None)
    figures.add_argument("--notes", default="")
    figures.add_argument("--allow-non-chinese", action="store_true")
    figures.set_defaults(func=command_approve_figures)

    paper_written = subparsers.add_parser("mark-paper-written", help="mark one question as written into the paper")
    paper_written.add_argument("--question", required=True, choices=question_choices())
    paper_written.set_defaults(func=command_mark_paper_written)

    write_question_paper = subparsers.add_parser(
        "write-question-paper", help="write one confirmed question into LaTeX and compile"
    )
    write_question_paper.add_argument("--question", required=True, choices=question_choices())
    write_question_paper.add_argument("--force", action="store_true")
    write_question_paper.add_argument(
        "--require-figures-approved",
        action="store_true",
        help="restore the stricter gate that requires approved final figures before writing the question section",
    )
    add_boolean_optional_argument(write_question_paper, "--compile", default=True)
    write_question_paper.set_defaults(func=command_write_question_paper)

    finalize_summary = subparsers.add_parser(
        "finalize-summary-paper", help="guard final abstract/evaluation writing until all questions are written"
    )
    finalize_summary.add_argument("--force", action="store_true")
    add_boolean_optional_argument(finalize_summary, "--compile", default=True)
    finalize_summary.set_defaults(func=command_finalize_summary_paper)

    paper_check = subparsers.add_parser("paper-check", help="check required paper files")
    paper_check.set_defaults(func=command_paper_check)

    layout_check = subparsers.add_parser("layout-check", help="check PDF layout gaps and expected figure/table pages")
    layout_check.add_argument("--pdf", type=Path, default=Path("07_paper/main.pdf"))
    layout_check.add_argument("--aux", type=Path, default=Path("07_paper/main.aux"))
    layout_check.add_argument("--max-internal-gap-ratio", type=float, default=0.24)
    layout_check.add_argument("--expect-label-page", action="append", default=[])
    layout_check.set_defaults(func=command_layout_check)

    readiness = subparsers.add_parser("readiness", help="print workflow readiness summary with self-healing hints")
    readiness.set_defaults(func=command_readiness)

    latex = subparsers.add_parser("latex-check", help="compile the current LaTeX paper")
    latex.add_argument("--skip-layout-check", action="store_true")
    latex.add_argument("--max-internal-gap-ratio", type=float, default=0.24)
    latex.add_argument("--expect-label-page", action="append", default=[])
    latex.set_defaults(func=command_latex_check)

    # --- Phase 3a / 3b / 4 / 5 / 6 ---

    auto_eda = subparsers.add_parser(
        "auto-eda", help="generate 6 diagnostic figures + summary into 06_results/<question>/eda/"
    )
    auto_eda.add_argument("--question", required=True, choices=question_choices())
    auto_eda.add_argument("--sample-rows", type=int, default=2000)
    auto_eda.add_argument("--target", default="", help="optional target column for pair-plot Top-K")
    auto_eda.set_defaults(func=command_auto_eda)

    index_papers = subparsers.add_parser(
        "index-papers",
        help="build BM25 index over 02_references/ocr_texts/ and/or 02_references/paper_texts/",
    )
    index_papers.add_argument("--force", action="store_true", help="rebuild even if index already exists")
    index_papers.add_argument(
        "--show-sources",
        action="store_true",
        help="list every .md/.txt file the indexer would pick up, then exit",
    )
    index_papers.set_defaults(func=command_index_papers)

    rag_status = subparsers.add_parser(
        "rag-status", help="diagnose missing pieces of the RAG pipeline (sources / library / index)"
    )
    rag_status.set_defaults(func=command_rag_status)

    retrieve_context = subparsers.add_parser(
        "retrieve-context", help="retrieve excellent-paper passages relevant to <question>"
    )
    retrieve_context.add_argument("--question", required=True, choices=question_choices())
    retrieve_context.add_argument("--top-k", type=int, default=5)
    retrieve_context.add_argument(
        "--query",
        default="",
        help="free-form search text; overrides building the query from problem_statement",
    )
    retrieve_context.set_defaults(func=command_retrieve_context)

    figure_lint = subparsers.add_parser("figure-lint", help="lint figures in the compiled PDF for style violations")
    figure_lint.add_argument("--pdf", type=Path, default=Path("07_paper/main.pdf"))
    figure_lint.set_defaults(func=command_figure_lint)

    trust_profile = subparsers.add_parser(
        "set-trust-profile", help="switch the approval trust profile (strict / normal / fast)"
    )
    trust_profile.add_argument("--profile", required=True, choices=["strict", "normal", "fast"])
    trust_profile.set_defaults(func=command_set_trust_profile)

    gen_ai_log = subparsers.add_parser(
        "gen-ai-log", help="append an auto-summarised AILOG entry from dispatch + state data"
    )
    gen_ai_log.set_defaults(func=command_gen_ai_log)

    return parser


LOCKED_COMMANDS = {
    "init-state",
    "status",
    "import-problem",
    "archive-stale-artifacts",
    "scan-data",
    "approve-language",
    "set-active-question",
    "prepare-schemes",
    "create-approval-brief",
    "create-model-confirmation-brief",
    "approve-schemes",
    "create-workorder",
    "create-workorders",
    "create-claude-prompt",
    "ingest-claude-report",
    "check-claude",
    "create-review",
    "mark-reviewed",
    "compare-schemes",
    "confirm-model",
    "approve-figures",
    "mark-paper-written",
    "write-question-paper",
    "finalize-summary-paper",
    "layout-check",
    "readiness",
    "auto-eda",
    "set-trust-profile",
    "gen-ai-log",
}


def main() -> None:
    configure_console_output()
    parser = build_parser()
    args = parser.parse_args()
    if args.command in LOCKED_COMMANDS:
        with workflow_lock():
            args.func(args)
    else:
        args.func(args)


if __name__ == "__main__":
    main()
