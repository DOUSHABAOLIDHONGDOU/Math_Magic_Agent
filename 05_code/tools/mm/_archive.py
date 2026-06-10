"""Stale-artifact archival: detect generated files from a previous problem and move them aside."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

from ._paths import PROJECT_ROOT, QUESTIONS, resolve_project_path, safe_project_file
from ._state import append_artifact
from ._util import (
    archive_timestamp,
    dedupe_paths,
    now_iso,
    read_text,
    rel,
    write_text,
)


GENERATED_ARTIFACT_PATTERNS = [
    "01_problem/problem_statement.md",
    "01_problem/data_dictionary.md",
    "03_methods/*APPROVAL_BRIEF*.md",
    "03_methods/Q*/codex_scheme_generation_prompt.md",
    "03_methods/Q*/scheme_*.md",
    "03_methods/Q*/approval_brief.md",
    "03_methods/Q*/model_confirmation_brief.md",
    "03_methods/Q*/figure_approval_brief.md",
    "03_methods/Q*/approved.md",
    "03_methods/Q*/q*_figure_approval_sheet.png",
    "03_methods/Q*/q*_final_figures_manifest.csv",
    "04_claude_workorders/Q*_scheme_*_workorder_*.md",
    "04_claude_workorders/Q*_scheme_*_claude_prompt.md",
    "04_claude_workorders/Q*_scheme_*_revision_prompt_*.md",
    "04_claude_workorders/completions/Q*_scheme_*_completion.md",
    "05_code/Q*/*.py",
    "06_results/Q*/figures/*",
    "06_results/Q*/logs/*",
    "06_results/Q*/tables/*",
    "07_paper/sections/model_q*.tex",
    "07_paper/figures/q*_fig*.*",
]
STALE_TOPIC_KEYWORDS = [
    "NIPT",
    "BMI",
    "Y 染色体",
    "孕周",
    "孕妇",
    "男胎",
    "女胎",
    "检测时点",
    "CUMCM2025 C",
]
DEFAULT_CURRENT_TOPIC_KEYWORDS: list[str] = []
TOPIC_KEYWORD_STOPWORDS = {
    "问题",
    "题目",
    "名称",
    "题面",
    "来源",
    "文件",
    "附件",
    "列表",
    "训练",
    "赛前",
    "待填写",
    "待定",
    "根据",
    "建立",
    "模型",
    "确定",
    "problem",
    "source",
    "real",
    "run",
    "pdf",
    "xlsx",
}
TEXT_ARTIFACT_SUFFIXES = {
    ".csv",
    ".json",
    ".log",
    ".md",
    ".ps1",
    ".py",
    ".sh",
    ".tex",
    ".txt",
    ".yaml",
    ".yml",
}


def collect_generated_artifact_paths() -> list[Path]:
    paths: list[Path] = []
    for pattern in GENERATED_ARTIFACT_PATTERNS:
        paths.extend(path for path in PROJECT_ROOT.glob(pattern) if path.is_file())
    return sorted(dedupe_paths(paths), key=lambda path: rel(path).lower())


def artifact_contains_keyword(path: Path, keywords: list[str]) -> bool:
    if path.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
        return False
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return False
    lowered = text.lower()
    return any(keyword.lower() in lowered for keyword in keywords)


def artifact_matches_stale_topic(path: Path, keywords: list[str], current_keywords: list[str]) -> bool:
    if path.suffix.lower() not in TEXT_ARTIFACT_SUFFIXES:
        return False
    try:
        text = read_text(path)
    except UnicodeDecodeError:
        return False
    lowered = text.lower()
    stale_score = keyword_evidence_score(lowered, keywords)
    current_score = keyword_evidence_score(lowered, current_keywords)
    if stale_score == 0:
        return False
    # A current run report may mention old artifacts as cleanup context. Keep it
    # when current-topic evidence is at least as strong as old-topic evidence.
    return not (current_score >= 4 and current_score >= stale_score)


def keyword_evidence_score(text_lower: str, keywords: list[str]) -> int:
    score = 0
    for keyword in keywords:
        value = str(keyword).strip()
        lower = value.lower()
        if not lower or lower in TOPIC_KEYWORD_STOPWORDS or lower.isdigit() or lower not in text_lower:
            continue
        if re.search(r"[一-鿿]", value):
            if len(value) < 2:
                continue
            if "的" in value and len(value) < 4:
                continue
            score += 1 if len(value) <= 2 else 2
        else:
            score += 1 if len(value) <= 3 else 2
    return score


def title_topic_ngrams(text: str) -> list[str]:
    keywords: list[str] = []
    for chunk in re.findall(r"[A-Za-z0-9一-鿿]+", text):
        if len(chunk) < 2 or chunk in TOPIC_KEYWORD_STOPWORDS:
            continue
        if re.search(r"[一-鿿]", chunk):
            max_n = min(6, len(chunk))
            for n in range(2, max_n + 1):
                for index in range(0, len(chunk) - n + 1):
                    value = chunk[index : index + n]
                    if value not in TOPIC_KEYWORD_STOPWORDS:
                        keywords.append(value)
        else:
            keywords.append(chunk)
    return keywords


def derive_current_topic_keywords(state: dict, extras: list[str] | None = None) -> list[str]:
    keywords: list[str] = list(DEFAULT_CURRENT_TOPIC_KEYWORDS)
    title = state.get("problem", {}).get("title") or ""
    if title:
        keywords.append(title)
        keywords.extend(title_topic_ngrams(title))
    statement_value = state.get("problem", {}).get("statement_file") or "01_problem/problem_statement.md"
    statement_path = resolve_project_path(statement_value)
    if statement_path and statement_path.exists():
        lines = read_text(statement_path).splitlines()
        for line in lines[:80]:
            if "题目名称" in line or re.search(r"[A-Z]\s*题", line):
                keywords.append(line)
                keywords.extend(title_topic_ngrams(line))
    keywords.extend(extras or [])
    result: list[str] = []
    for keyword in keywords:
        value = str(keyword).strip()
        if len(value) < 2 or value.isdigit() or value.lower() in TOPIC_KEYWORD_STOPWORDS:
            continue
        if value not in result:
            result.append(value)
    return result


def question_from_artifact_path(path: Path) -> str | None:
    relative = rel(path).replace("\\", "/")
    patterns = [
        r"(?:^|/)Q([1-5])(?:/|_)",
        r"model_q([1-5])\.tex$",
        r"q([1-5])_fig",
        r"q([1-5])_figure_approval",
        r"q([1-5])_final_figures",
    ]
    for pattern in patterns:
        match = re.search(pattern, relative, flags=re.IGNORECASE)
        if match:
            return f"Q{match.group(1)}"
    return None


def related_stale_artifacts(stale_text_paths: list[Path]) -> list[Path]:
    related: list[Path] = []
    questions = sorted(
        {question_from_artifact_path(path) for path in stale_text_paths if question_from_artifact_path(path)}
    )
    for question in questions:
        qlower = question.lower()
        qtext_paths = [path for path in stale_text_paths if question_from_artifact_path(path) == question]
        if any(
            rel(path).replace("\\", "/").endswith(
                (
                    f"03_methods/{question}/figure_approval_brief.md",
                    f"07_paper/sections/model_{qlower}.tex",
                )
            )
            for path in qtext_paths
        ):
            related.extend((PROJECT_ROOT / "03_methods" / question).glob(f"{qlower}_figure_approval_sheet.*"))
            related.extend((PROJECT_ROOT / "03_methods" / question).glob(f"{qlower}_final_figures_manifest.*"))
            related.extend((PROJECT_ROOT / "07_paper" / "figures").glob(f"{qlower}_fig*.*"))

        if question != "Q1" and any(
            re.search(r"03_methods/" + re.escape(question) + r"/", rel(path).replace("\\", "/"))
            or re.search(r"04_claude_workorders/" + re.escape(question) + r"_", rel(path).replace("\\", "/"))
            or re.search(r"05_code/" + re.escape(question) + r"/", rel(path).replace("\\", "/"))
            or re.search(r"06_results/" + re.escape(question) + r"/", rel(path).replace("\\", "/"))
            for path in qtext_paths
        ):
            related.extend((PROJECT_ROOT / "03_methods" / question).glob("*"))
            related.extend((PROJECT_ROOT / "04_claude_workorders").glob(f"{question}_scheme_*.md"))
            related.extend((PROJECT_ROOT / "04_claude_workorders" / "completions").glob(f"{question}_scheme_*_completion.md"))
            related.extend((PROJECT_ROOT / "05_code" / question).glob("*.py"))
            related.extend((PROJECT_ROOT / "06_results" / question).rglob("*"))
            related.extend((PROJECT_ROOT / "07_paper" / "figures").glob(f"{qlower}_fig*.*"))
        elif question == "Q1":
            related.extend((PROJECT_ROOT / "03_methods" / question).glob(f"{qlower}_figure_approval_sheet.*"))
            related.extend((PROJECT_ROOT / "03_methods" / question).glob(f"{qlower}_final_figures_manifest.*"))
    return [path for path in related if path.is_file()]


def collect_detected_stale_artifact_paths(
    keywords: list[str],
    current_keywords: list[str],
    include_related: bool = True,
) -> list[Path]:
    candidates = collect_generated_artifact_paths()
    stale_text_paths = [path for path in candidates if artifact_matches_stale_topic(path, keywords, current_keywords)]
    paths = list(stale_text_paths)
    if include_related:
        paths.extend(related_stale_artifacts(stale_text_paths))
    return sorted(dedupe_paths([path for path in paths if safe_project_file(path)]), key=lambda path: rel(path).lower())


def render_question_placeholder_section(question: str) -> str:
    title_num = question[1:] if question[1:].isdigit() else question
    return f"""\\subsection{{问题{title_num}模型的建立与求解}}\\label{{sub:5.{title_num}}}

本节内容待用户完成方案审批、Claude Code 实现、Codex 复审和模型确认后写入并编译；最终中文图可在图表审批后补入。
"""


def is_template_question_section(text: str) -> bool:
    template_markers = [
        "待用户完成方案审批和模型确认后写入",
        "待用户完成方案审批、Claude Code 实现、Codex 复审、模型确认和图表审批后写入",
        "待用户完成方案审批、Claude Code 实现、Codex 复审和模型确认后写入并编译",
        "待 Codex 根据已确认模型补充",
    ]
    return any(marker in text for marker in template_markers)


def restore_required_placeholders(archived_sources: list[Path]) -> None:
    from ._paths import question_section_path

    for path in archived_sources:
        match = re.search(r"model_q([1-5])\.tex$", path.name, flags=re.IGNORECASE)
        if not match:
            continue
        question = f"Q{match.group(1)}"
        section_path = question_section_path(question)
        if section_path.exists():
            continue
        write_text(section_path, render_question_placeholder_section(question))


def write_archive_markdown_manifest(path: Path, manifest: dict) -> None:
    lines = [
        "# Stale Artifact Archive",
        "",
        f"- created_at: `{manifest['created_at']}`",
        f"- reason: {manifest['reason']}",
        f"- profile: `{manifest['profile']}`",
        f"- count: {manifest['count']}",
        "",
        "## Files",
        "",
    ]
    for item in manifest["files"]:
        lines.append(f"- `{item['source']}`")
    write_text(path, "\n".join(lines) + "\n")


def archive_artifact_paths(
    state: dict,
    paths: list[Path],
    *,
    reason: str,
    profile: str,
    dry_run: bool = False,
):
    safe_paths = sorted(dedupe_paths([path for path in paths if safe_project_file(path)]), key=lambda path: rel(path).lower())
    rows = [{"source": rel(path), "status": "would_archive" if dry_run else "archived"} for path in safe_paths]
    if dry_run or not safe_paths:
        return None, rows

    archive_dir = PROJECT_ROOT / "00_shared" / "archive" / "stale_artifacts" / archive_timestamp()
    archived_sources: list[Path] = []
    for path in safe_paths:
        relative = Path(rel(path))
        dest = archive_dir / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(dest))
        archived_sources.append(path)
    restore_required_placeholders(archived_sources)
    manifest = {
        "created_at": now_iso(),
        "reason": reason,
        "profile": profile,
        "archive_dir": rel(archive_dir),
        "count": len(rows),
        "files": rows,
    }
    manifest_path = archive_dir / "manifest.json"
    write_text(manifest_path, json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    write_archive_markdown_manifest(archive_dir / "manifest.md", manifest)
    state.setdefault("archived_artifacts", []).append(
        {
            "archive_dir": rel(archive_dir),
            "manifest": rel(manifest_path),
            "reason": reason,
            "profile": profile,
            "count": len(rows),
            "created_at": now_iso(),
        }
    )
    append_artifact(state, "stale_artifact_archive", manifest_path, reason)
    return manifest_path, rows
