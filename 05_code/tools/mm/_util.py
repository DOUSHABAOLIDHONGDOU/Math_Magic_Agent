"""I/O primitives, formatting, console helpers, CLI argument helpers."""

from __future__ import annotations

import argparse
import datetime as dt
import shlex
import sys
from pathlib import Path

from ._paths import PROJECT_ROOT


def configure_console_output() -> None:
    """Force UTF-8 on stdout/stderr so Chinese output works on Windows shells."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_powershell_script(path: Path, text: str) -> None:
    """PowerShell scripts must be UTF-8 with BOM for non-ASCII user-name paths."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8-sig")


def today() -> str:
    return dt.date.today().isoformat()


def now_iso() -> str:
    return dt.datetime.now().replace(microsecond=0).isoformat()


def archive_timestamp() -> str:
    return dt.datetime.now().strftime("%Y%m%d_%H%M%S")


def rel(path: Path) -> str:
    """Project-relative POSIX-style path.

    POSIX style ('foo/bar.md') is used everywhere — including on Windows — so
    that generated prompts, JSON state files, and Markdown links stay portable
    across machines and don't mix '\\' and '/' in the same document.
    """
    try:
        return path.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return Path(str(path)).as_posix()


def add_boolean_optional_argument(
    parser: argparse.ArgumentParser,
    flag: str,
    *,
    default: bool,
    help: str | None = None,
) -> None:
    action = getattr(argparse, "BooleanOptionalAction", None)
    if action is not None:
        parser.add_argument(flag, action=action, default=default, help=help)
        return
    flag_name = flag[2:] if flag.startswith("--") else flag
    dest = flag_name.replace("-", "_")
    parser.add_argument(flag, dest=dest, action="store_true", default=default, help=help)
    parser.add_argument(f"--no-{flag_name}", dest=dest, action="store_false", help=argparse.SUPPRESS)


def ps_single_quote(value) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def ps_args(args: list[str]) -> str:
    return " ".join(ps_single_quote(arg) for arg in args)


def parse_iso_datetime(value):
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value)
    except ValueError:
        return None


def dedupe_paths(paths: list[Path]) -> list[Path]:
    seen: set[str] = set()
    result: list[Path] = []
    for path in paths:
        try:
            key = str(path.resolve()).lower()
        except OSError:
            key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(path)
    return result


def extract_section(text: str, title: str) -> str:
    marker = f"## {title}"
    start = text.find(marker)
    if start == -1:
        return f"{marker}\n未找到。"
    next_start = text.find("\n## ", start + len(marker))
    if next_start == -1:
        next_start = len(text)
    return text[start:next_start].strip()


def append_markdown_log(path: Path, title: str, lines: list[str]) -> None:
    existing = read_text(path) if path.exists() else f"# {path.stem}\n"
    block = "\n\n" + f"## {title}\n\n" + "\n".join(lines).rstrip() + "\n"
    write_text(path, existing.rstrip() + block)


def print_user_facing_brief(path: Path, text: str, brief_type: str) -> None:
    print(f"USER_FACING_BRIEF: {brief_type}")
    print(f"path: {rel(path)}")
    print()
    print(text.rstrip())
    print()
    print("ACTION_REQUIRED: Codex must paste/summarize these options in the user chat and wait for approval.")


# ---------------------------------------------------------------------------
# Claude command parsing helpers (used by dispatch scripts)


def claude_command_extra_args(command: str) -> list[str]:
    args = shlex.split(command, posix=False)
    if not args:
        return []
    extras: list[str] = []
    skip_next = False
    for arg in args[1:]:
        clean = arg.strip("\"'")
        if skip_next:
            skip_next = False
            continue
        if clean in {"-p", "--print"}:
            continue
        if clean == "--permission-mode":
            skip_next = True
            continue
        if clean.startswith("--permission-mode="):
            continue
        if clean in {"-c", "--continue"}:
            continue
        if clean in {"-r", "--resume", "--session-id"}:
            skip_next = True
            continue
        if clean.startswith("--resume=") or clean.startswith("--session-id="):
            continue
        extras.append(clean)
    return extras


def claude_session_args(session_mode: str | None, session_id: str | None = None) -> list[str]:
    mode = (session_mode or "continue").lower()
    if mode == "new":
        return []
    if mode == "continue":
        return ["--continue"]
    if mode == "resume":
        if session_id:
            return ["--resume", session_id]
        return ["--resume"]
    raise SystemExit("claude session mode must be continue, new, or resume")


def powershell_claude_executable(command: str) -> str:
    args = shlex.split(command, posix=False)
    if not args:
        return "claude"
    return args[0].strip("\"'")


def format_claude_command(executable) -> str:
    return f"{shlex.quote(str(executable))} -p --dangerously-skip-permissions --permission-mode bypassPermissions"


def current_target_os() -> str:
    return "windows" if sys.platform.startswith("win") else "posix"


def ensure_target_os(value: str) -> str:
    value = (value or "auto").lower()
    if value == "auto":
        return current_target_os()
    if value in {"windows", "posix"}:
        return value
    raise SystemExit("target os must be auto, windows, or posix")
