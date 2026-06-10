"""Workflow state default/load/save/migrate plus the file lock."""

from __future__ import annotations

import contextlib
import json
import shutil
from pathlib import Path

from ._paths import (
    LOCK_PATH,
    PROJECT_ROOT,
    QUESTIONS,
    SCHEMES,
    STAGES,
    STATE_PATH,
    state_snapshots_dir,
)
from ._util import (
    archive_timestamp,
    now_iso,
    read_text,
    rel,
    write_text,
)


STATE_VERSION = "0.3.0"
TRUST_PROFILES = ["strict", "normal", "fast"]
DEFAULT_TRUST_PROFILE = "strict"
SNAPSHOT_RETENTION = 10


def default_state() -> dict:
    return {
        "version": STATE_VERSION,
        "stage": "INIT",
        "current_question": None,
        "trust_profile": DEFAULT_TRUST_PROFILE,
        "workflow": {
            "mode": "sequential",
            "allow_parallel_questions": False,
            "question_dependency_rule": "later questions wait until previous question paper_written",
        },
        "language": {
            "recommended": "Python",
            "approved": False,
            "decision_id": None,
        },
        "problem": {
            "title": None,
            "statement_file": "01_problem/problem_statement.md",
            "data_dictionary": "01_problem/data_dictionary.md",
            "raw_data_dir": None,
            "question_ids": [],
        },
        "questions": {
            q: {
                "status": "not_started",
                "schemes_generated": False,
                "schemes_approved": False,
                "scheme_decision_id": None,
                "workorders_created": False,
                "code_completed": False,
                "code_reviewed": False,
                "model_confirmed": False,
                "confirmed_scheme": None,
                "model_decision_id": None,
                "figures_generated": False,
                "figures_approved": False,
                "figure_decision_id": None,
                "figure_language": None,
                "paper_written": False,
                "paper_section": None,
                "latex_compiled_at": None,
                "schemes": {
                    s: {
                        "status": "not_started",
                        "workorder": None,
                        "claude_prompt": None,
                        "dispatch_status": None,
                        "dispatch_mode": None,
                        "dispatch_created_at": None,
                        "dispatch_opened_at": None,
                        "claude_session_mode": None,
                        "claude_session_id": None,
                        "dispatch_prompt": None,
                        "dispatch_log": None,
                        "dispatch_terminal_script": None,
                        "dispatch_terminal_status": None,
                        "completion_report": None,
                        "review": None,
                    }
                    for s in SCHEMES
                },
            }
            for q in QUESTIONS
        },
        "artifacts": [],
        "archived_artifacts": [],
        "updated_at": now_iso(),
    }


def load_state() -> dict:
    if not STATE_PATH.exists():
        state = default_state()
        save_state(state)
        return state
    state = json.loads(read_text(STATE_PATH))
    changed = migrate_state(state)
    if changed:
        save_state(state)
    return state


def migrate_state(state: dict) -> bool:
    """Bring a stored state dict up to the current schema. Returns True if changed."""
    changed = False
    default = default_state()
    if state.get("version") != default["version"]:
        state["version"] = default["version"]
        changed = True
    if "trust_profile" not in state:
        state["trust_profile"] = DEFAULT_TRUST_PROFILE
        changed = True
    if "workflow" not in state:
        state["workflow"] = default["workflow"]
        changed = True
    elif state["workflow"].get("question_dependency_rule") != default["workflow"]["question_dependency_rule"]:
        state["workflow"]["question_dependency_rule"] = default["workflow"]["question_dependency_rule"]
        changed = True
    if "question_ids" not in state.get("problem", {}):
        state.setdefault("problem", {})["question_ids"] = []
        changed = True
    if "archived_artifacts" not in state:
        state["archived_artifacts"] = []
        changed = True
    state.setdefault("questions", {})
    for question in QUESTIONS:
        if question not in state["questions"]:
            state["questions"][question] = default["questions"][question]
            changed = True
            continue
        qstate = state["questions"][question]
        default_qstate = default["questions"][question]
        for key, value in default_qstate.items():
            if key not in qstate:
                qstate[key] = value
                changed = True
        qstate.setdefault("schemes", {})
        for scheme in SCHEMES:
            if scheme not in qstate["schemes"]:
                qstate["schemes"][scheme] = default_qstate["schemes"][scheme]
                changed = True
                continue
            for key, value in default_qstate["schemes"][scheme].items():
                if key not in qstate["schemes"][scheme]:
                    qstate["schemes"][scheme][key] = value
                    changed = True
    return changed


def save_state(state: dict, *, snapshot: bool = True) -> None:
    state["updated_at"] = now_iso()
    write_text(STATE_PATH, json.dumps(state, ensure_ascii=False, indent=2) + "\n")
    if snapshot:
        _write_state_snapshot(state)
    # Late binding so _project_state_summary can update PROJECT_STATE.md without
    # importing here (avoids a cycle: _project_state -> _state -> _project_state).
    updater = globals().get("update_project_state_summary")
    if updater is not None:
        updater(state)


def _write_state_snapshot(state: dict) -> None:
    snap_dir = state_snapshots_dir()
    snap_dir.mkdir(parents=True, exist_ok=True)
    stamp = archive_timestamp()
    snap_path = snap_dir / f"state_{stamp}.json"
    snap_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    snapshots = sorted(snap_dir.glob("state_*.json"))
    # Keep only the newest SNAPSHOT_RETENTION snapshots.
    for old in snapshots[:-SNAPSHOT_RETENTION]:
        try:
            old.unlink()
        except OSError:
            pass


@contextlib.contextmanager
def workflow_lock():
    LOCK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with LOCK_PATH.open("w", encoding="utf-8") as lock_file:
        try:
            import fcntl

            fcntl.flock(lock_file, fcntl.LOCK_EX)
            held = True
        except ImportError:
            held = False
            fcntl = None  # noqa: F841 - placeholder for finally branch
        try:
            yield
        finally:
            if held:
                import fcntl as _fcntl

                _fcntl.flock(lock_file, _fcntl.LOCK_UN)


# ---------------------------------------------------------------------------
# State helpers used throughout the workflow


def set_stage(state: dict, stage: str) -> None:
    if stage not in STAGES:
        raise SystemExit(f"unknown stage: {stage}")
    state["stage"] = stage


def append_artifact(state: dict, kind: str, path: Path, note: str = "") -> None:
    artifact_path = rel(path)
    state.setdefault("artifacts", [])
    already_recorded = any(
        item.get("kind") == kind and item.get("path") == artifact_path and item.get("note", "") == note
        for item in state["artifacts"]
    )
    if not already_recorded:
        state["artifacts"].append({"kind": kind, "path": artifact_path, "note": note, "created_at": now_iso()})


def ensure_question(question: str) -> str:
    question = question.upper()
    if question not in QUESTIONS:
        raise SystemExit(f"question must be one of {', '.join(QUESTIONS)}")
    return question


def question_choices() -> list[str]:
    return QUESTIONS + [q.lower() for q in QUESTIONS]


def ensure_scheme(scheme: str) -> str:
    scheme = scheme.upper()
    if scheme not in SCHEMES:
        raise SystemExit(f"scheme must be one of {', '.join(SCHEMES)}")
    return scheme


def active_question_ids(state: dict) -> list[str]:
    return state["problem"].get("question_ids") or QUESTIONS


def next_question_to_solve(state: dict) -> str | None:
    for question in active_question_ids(state):
        if not state["questions"][question].get("paper_written"):
            return question
    return None


def previous_question(state: dict, question: str) -> str | None:
    questions = active_question_ids(state)
    if question not in questions:
        return None
    index = questions.index(question)
    return questions[index - 1] if index > 0 else None


def advance_current_question_after_paper_written(state: dict, question: str) -> None:
    questions = active_question_ids(state)
    if question not in questions:
        return
    index = questions.index(question)
    if index + 1 >= len(questions):
        state["current_question"] = None
        return
    next_q = questions[index + 1]
    state["current_question"] = next_q
    if state["questions"][next_q]["status"] == "deferred_waiting_previous_question":
        state["questions"][next_q]["status"] = "active"


def assert_question_unlocked(state: dict, question: str, force: bool = False) -> None:
    if force or state.get("workflow", {}).get("allow_parallel_questions"):
        return
    if question not in active_question_ids(state):
        raise SystemExit(f"{question} is not an active question for the imported problem")
    next_q = next_question_to_solve(state)
    if next_q and question != next_q:
        prev = previous_question(state, question)
        reason = f"{prev} has not been paper_written" if prev else f"current question is {next_q}"
        raise SystemExit(
            f"sequential workflow guard: {question} is locked; solve {next_q} first ({reason}). "
            "Use --force only for explicit diagnostic tests."
        )


def approved_schemes(qstate: dict) -> list[str]:
    from ._paths import SELECTED_SCHEME_STATUSES

    return [scheme for scheme in SCHEMES if qstate["schemes"][scheme].get("status") in SELECTED_SCHEME_STATUSES]


def reset_problem_workflow_state(state: dict, question_ids: list[str]) -> None:
    default = default_state()
    state["stage"] = "PROBLEM_LOADED"
    state["current_question"] = question_ids[0] if question_ids else None
    state["questions"] = default["questions"]
    for question in QUESTIONS:
        qstate = state["questions"][question]
        if question in question_ids:
            qstate["status"] = "active" if question == state["current_question"] else "not_started"
        else:
            qstate["status"] = "inactive"
    state["artifacts"] = []


def get_trust_profile(state: dict) -> str:
    profile = state.get("trust_profile") or DEFAULT_TRUST_PROFILE
    if profile not in TRUST_PROFILES:
        return DEFAULT_TRUST_PROFILE
    return profile


def set_trust_profile(state: dict, profile: str) -> None:
    if profile not in TRUST_PROFILES:
        raise SystemExit(f"trust profile must be one of {', '.join(TRUST_PROFILES)}")
    state["trust_profile"] = profile
