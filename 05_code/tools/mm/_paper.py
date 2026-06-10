"""LaTeX compile, layout check, question-section writers.

Phase 1 cleanups applied here:
- ``run_latex_compile`` now runs xelatex twice so cross-references resolve.
- ``_assert_layout_ok`` extracted to remove three near-duplicate copies of
  the print-and-exit block.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

from ._paths import PROJECT_ROOT, paper_summary_sections, question_section_path
from ._util import now_iso, read_text, rel, write_text


# Layout check tuning constants (previously magic numbers in detect_large_pdf_gaps).
PIXMAP_SCALE = 0.55                # pymupdf rasterisation scale; balances speed vs accuracy
MIN_INK_WIDTH_RATIO = 0.012        # a row counts as "ink" if at least this fraction of width is dark
INK_GRAY_THRESHOLD = 245           # 0..255 grayscale; anything darker is "ink"
TOP_MARGIN_RATIO = 0.08            # skip header/top margin when looking for internal gaps
BOTTOM_MARGIN_RATIO = 0.92         # skip footer/bottom margin similarly
LATEX_LOG_TAIL_CHARS = 4000        # truncate xelatex stdout to last N chars for readability


def _latex_escape(value) -> str:
    """Minimal LaTeX escaping for cell values inside an auto-rendered tabular."""
    s = str(value)
    replacements = [
        ("\\", r"\textbackslash{}"),
        ("&", r"\&"),
        ("%", r"\%"),
        ("$", r"\$"),
        ("#", r"\#"),
        ("_", r"\_"),
        ("{", r"\{"),
        ("}", r"\}"),
        ("^", r"\^{}"),
        ("~", r"\~{}"),
    ]
    for old, new in replacements:
        s = s.replace(old, new)
    return s


def _metrics_to_latex_table(metrics: dict, question: str, scheme: str) -> str:
    if not metrics:
        return ""
    items = [(k, v) for k, v in metrics.items() if v not in (None, "")]
    if not items:
        return ""
    rows = "\n".join(f"  {_latex_escape(k)} & {_latex_escape(v)} \\\\" for k, v in items)
    return (
        f"\\begin{{table}}[H]\n"
        f"\\centering\n"
        f"\\caption{{问题{question[1:]} 方案 {scheme} 核心指标}}\n"
        f"\\label{{tab:metrics_{question.lower()}_{scheme.lower()}}}\n"
        f"\\begin{{tabular}}{{ll}}\n"
        f"\\hline\n"
        f"  指标 & 数值 \\\\\n"
        f"\\hline\n"
        f"{rows}\n"
        f"\\hline\n"
        f"\\end{{tabular}}\n"
        f"\\end{{table}}\n"
    )


def _summarise_completion_report(question: str, scheme: str) -> str:
    """Pull the '关键结果' / 'key results' section out of the Claude completion report."""
    from ._paths import expected_completion_path

    path = expected_completion_path(question, scheme)
    if not path.exists():
        return ""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return ""
    for marker in ("关键结果", "核心结果", "Key results", "key results", "Results"):
        idx = text.find(marker)
        if idx == -1:
            continue
        head = text.find("\n", idx) + 1
        tail = text.find("\n## ", head)
        if tail == -1:
            tail = min(len(text), head + 800)
        snippet = text[head:tail].strip()
        if snippet:
            return snippet
    return ""


def render_question_paper_section(state: dict, question: str) -> str:
    from ._briefs import read_metrics_summary
    from ._review import confirmed_scheme

    scheme = confirmed_scheme(state, question)
    title_num = question[1:] if question[1:].isdigit() else question

    metrics = read_metrics_summary(question, scheme) if scheme != "待确认" else {}
    metrics_table = _metrics_to_latex_table(metrics, question, scheme) if metrics else ""
    completion_summary = _summarise_completion_report(question, scheme) if scheme != "待确认" else ""
    completion_block = ""
    if completion_summary:
        # Render line-by-line so the markdown bullets degrade gracefully to LaTeX.
        escaped_lines = [
            _latex_escape(line.lstrip("-* ").rstrip())
            for line in completion_summary.splitlines()
            if line.strip()
        ]
        if escaped_lines:
            items = "\n".join(f"  \\item {line}" for line in escaped_lines[:10])
            completion_block = (
                "\\begin{itemize}\n"
                f"{items}\n"
                "\\end{itemize}\n"
            )

    results_body = []
    if metrics_table:
        results_body.append(metrics_table)
    if completion_block:
        results_body.append("Claude Code 实现总结：")
        results_body.append(completion_block)
    if not results_body:
        results_body.append(
            f"待 Codex 根据 `06_results/{question}/tables/` 中的结果表补充；已审批中文图表可后续补入。"
        )
    results_section = "\n\n".join(results_body)

    return f"""\\subsection{{问题{title_num}模型的建立与求解}}\\label{{sub:5.{title_num}}}

本节内容由 Codex 在该问题完成模型确认后写入并编译。当前采用方案为 {scheme}。

\\subsubsection{{模型建立}}

待 Codex 根据已确认模型补充数学表达式、参数说明和约束条件。

\\subsubsection{{模型求解与结果分析}}

{results_section}

\\subsubsection{{本问小结}}

待 Codex 概括本问结论，并说明对后续问题的输入或约束影响。
"""


def _run_xelatex(paper_dir: Path, halt_on_error: bool) -> subprocess.CompletedProcess:
    """Run xelatex once with safe Windows-friendly stdout decoding."""
    cmd = ["xelatex", "-interaction=nonstopmode"]
    if halt_on_error:
        cmd.append("-halt-on-error")
    cmd.append("main.tex")
    try:
        return subprocess.run(
            cmd,
            cwd=paper_dir,
            # bytes mode + manual UTF-8/errors=replace so the Windows GBK console
            # can't crash decoding xelatex's mixed-language log output.
            capture_output=True,
            check=False,
        )
    except FileNotFoundError as exc:
        raise SystemExit(
            "xelatex not found in PATH; install TeX Live/MiKTeX or add xelatex to PATH before compiling"
        ) from exc


def _decode_output(data) -> str:
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    return data.decode("utf-8", errors="replace")


def run_latex_compile() -> Path:
    """Compile main.tex twice with xelatex so cross-references resolve in one shot."""
    paper_dir = PROJECT_ROOT / "07_paper"
    first = _run_xelatex(paper_dir, halt_on_error=False)
    if first.returncode != 0:
        print(_decode_output(first.stdout)[-LATEX_LOG_TAIL_CHARS:])
        print(_decode_output(first.stderr))
        raise SystemExit(first.returncode)
    second = _run_xelatex(paper_dir, halt_on_error=True)
    print(_decode_output(second.stdout)[-LATEX_LOG_TAIL_CHARS:])
    if second.returncode != 0:
        print(_decode_output(second.stderr))
        raise SystemExit(second.returncode)
    return paper_dir / "main.pdf"


def parse_aux_label_pages(aux_path: Path) -> dict[str, int]:
    if not aux_path.exists():
        return {}
    labels: dict[str, int] = {}
    pattern = re.compile(r"\\newlabel\{([^}]+)\}\{\{[^{}]*\}\{(\d+)\}")
    for line in read_text(aux_path).splitlines():
        match = pattern.search(line)
        if match:
            labels[match.group(1)] = int(match.group(2))
    return labels


def parse_label_expectations(expectations: list[str]) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for value in expectations:
        if "=" not in value:
            raise SystemExit(f"invalid label expectation `{value}`; expected label=page")
        label, page = value.split("=", 1)
        label = label.strip()
        try:
            parsed[label] = int(page.strip())
        except ValueError as exc:
            raise SystemExit(f"invalid page in label expectation `{value}`") from exc
    return parsed


def detect_large_pdf_gaps(pdf_path: Path, max_internal_gap_ratio: float) -> list[dict]:
    try:
        import fitz
    except ImportError as exc:
        raise SystemExit("layout-check requires pymupdf; install project dependencies first") from exc

    if not pdf_path.exists():
        raise SystemExit(f"PDF not found: {rel(pdf_path)}")

    document = fitz.open(pdf_path)
    findings: list[dict] = []
    for page_index, page in enumerate(document, start=1):
        pix = page.get_pixmap(matrix=fitz.Matrix(PIXMAP_SCALE, PIXMAP_SCALE), colorspace=fitz.csGRAY, alpha=False)
        width, height = pix.width, pix.height
        samples = pix.samples
        min_ink_pixels = max(4, int(width * MIN_INK_WIDTH_RATIO))
        content_rows: list[int] = []
        for row in range(height):
            start = row * width
            end = start + width
            ink = sum(1 for value in samples[start:end] if value < INK_GRAY_THRESHOLD)
            if ink >= min_ink_pixels:
                content_rows.append(row)
        if len(content_rows) < 2:
            continue
        top_guard = int(height * TOP_MARGIN_RATIO)
        bottom_guard = int(height * BOTTOM_MARGIN_RATIO)
        largest_gap = 0
        largest_pair = None
        for previous, current in zip(content_rows, content_rows[1:]):
            gap = current - previous - 1
            if gap <= largest_gap:
                continue
            if previous < top_guard or current > bottom_guard:
                continue
            largest_gap = gap
            largest_pair = (previous, current)
        ratio = largest_gap / height if height else 0.0
        if largest_pair and ratio > max_internal_gap_ratio:
            findings.append(
                {
                    "page": page_index,
                    "gap_ratio": ratio,
                    "gap_start_ratio": largest_pair[0] / height,
                    "gap_end_ratio": largest_pair[1] / height,
                }
            )
    return findings


def run_layout_check(
    pdf_path: Path,
    aux_path: Path,
    max_internal_gap_ratio: float,
    label_expectations: list[str],
) -> list[str]:
    issues: list[str] = []
    for finding in detect_large_pdf_gaps(pdf_path, max_internal_gap_ratio):
        issues.append(
            "page {page}: internal blank gap {gap:.1%} from {start:.1%} to {end:.1%}".format(
                page=finding["page"],
                gap=finding["gap_ratio"],
                start=finding["gap_start_ratio"],
                end=finding["gap_end_ratio"],
            )
        )

    expected_pages = parse_label_expectations(label_expectations)
    if expected_pages:
        label_pages = parse_aux_label_pages(aux_path)
        for label, expected_page in expected_pages.items():
            actual_page = label_pages.get(label)
            if actual_page is None:
                issues.append(f"label `{label}` not found in {rel(aux_path)}")
            elif actual_page != expected_page:
                issues.append(f"label `{label}` is on page {actual_page}, expected page {expected_page}")

    # Phase 5: figure lint runs against the PDF too. Pure WARN by default unless gap/label fail.
    try:
        from . import _figure_lint

        issues.extend(_figure_lint.run_figure_lint(pdf_path))
    except (ImportError, FileNotFoundError):
        # _figure_lint is optional; skip silently if not installed yet.
        pass

    return issues


def _assert_layout_ok(issues: list[str]) -> None:
    """Print layout issues and SystemExit(1) on failure; print "ok" otherwise.

    Extracted so the three sites that previously inlined this had a single
    source of truth.
    """
    print("== Paper Layout Check ==")
    if issues:
        for issue in issues:
            print(f"FAIL: {issue}")
        raise SystemExit(1)
    print("layout: ok")


# ---------------------------------------------------------------------------
# CLI command implementations


def command_layout_check(args):
    pdf_path = args.pdf if args.pdf.is_absolute() else PROJECT_ROOT / args.pdf
    aux_path = args.aux if args.aux.is_absolute() else PROJECT_ROOT / args.aux
    issues = run_layout_check(
        pdf_path=pdf_path,
        aux_path=aux_path,
        max_internal_gap_ratio=args.max_internal_gap_ratio,
        label_expectations=args.expect_label_page,
    )
    print(f"pdf: {rel(pdf_path)}")
    print(f"max_internal_gap_ratio: {args.max_internal_gap_ratio:.2f}")
    if args.expect_label_page:
        print(f"label_expectations: {', '.join(args.expect_label_page)}")
    _assert_layout_ok(issues)


def command_write_question_paper(args):
    from ._archive import is_template_question_section
    from ._state import (
        active_question_ids,
        advance_current_question_after_paper_written,
        append_artifact,
        ensure_question,
        load_state,
        save_state,
        set_stage,
    )

    state = load_state()
    question = ensure_question(args.question)
    qstate = state["questions"][question]
    if not qstate.get("model_confirmed") and not args.force:
        raise SystemExit(f"{question} model is not confirmed; run confirm-model first or use --force")
    if args.require_figures_approved and not qstate.get("figures_approved") and not args.force:
        raise SystemExit(f"{question} figures are not approved; run approve-figures first or use --force")
    section_path = question_section_path(question)
    section_text = render_question_paper_section(state, question)
    if section_path.exists() and not args.force:
        current = read_text(section_path)
        if not is_template_question_section(current) and current.strip() != section_text.strip():
            raise SystemExit(f"{rel(section_path)} already has non-template content; use --force to overwrite")
    write_text(section_path, section_text)
    qstate["paper_section"] = rel(section_path)
    append_artifact(state, "paper_question_section", section_path, question)
    pdf_path = None
    if args.compile:
        try:
            pdf_path = run_latex_compile()
            layout_issues = run_layout_check(
                pdf_path=pdf_path,
                aux_path=PROJECT_ROOT / "07_paper" / "main.aux",
                max_internal_gap_ratio=0.24,
                label_expectations=[],
            )
            if layout_issues:
                _assert_layout_ok(layout_issues)
        except SystemExit:
            qstate["paper_written"] = False
            qstate["status"] = "paper_compile_failed"
            state["current_question"] = question
            save_state(state)
            raise
        qstate["latex_compiled_at"] = now_iso()
        append_artifact(state, "latex_pdf", pdf_path, f"after {question} paper write")
    qstate["paper_written"] = True
    qstate["status"] = "paper_written"
    advance_current_question_after_paper_written(state, question)
    active_questions = active_question_ids(state)
    if all(state["questions"][q]["paper_written"] for q in active_questions):
        set_stage(state, "PAPER_WRITTEN")
    save_state(state)
    print(section_path)
    if pdf_path:
        print(pdf_path)


def command_finalize_summary_paper(args):
    from ._state import active_question_ids, append_artifact, load_state, save_state

    state = load_state()
    active_questions = active_question_ids(state)
    missing = [q for q in active_questions if not state["questions"][q].get("paper_written")]
    if missing and not args.force:
        raise SystemExit(
            f"summary sections are locked until all question sections are written; missing: {', '.join(missing)}"
        )
    for section in paper_summary_sections():
        if not section.exists():
            raise SystemExit(f"missing summary section: {rel(section)}")
    if args.compile:
        pdf_path = run_latex_compile()
        layout_issues = run_layout_check(
            pdf_path=pdf_path,
            aux_path=PROJECT_ROOT / "07_paper" / "main.aux",
            max_internal_gap_ratio=0.24,
            label_expectations=[],
        )
        if layout_issues:
            _assert_layout_ok(layout_issues)
        append_artifact(state, "latex_pdf", pdf_path, "after summary finalize check")
    save_state(state)
    print("summary sections are ready for final Codex writing")


def command_paper_check(args):
    checks = []
    for path in [
        PROJECT_ROOT / "07_paper" / "main.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "abstract.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "problem_analysis.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "model_validation.tex",
        PROJECT_ROOT / "07_paper" / "sections" / "evaluation.tex",
        PROJECT_ROOT / "07_paper" / "appendix" / "code_appendix.tex",
        PROJECT_ROOT / "07_paper" / "appendix" / "ai_usage_appendix.tex",
        PROJECT_ROOT / "02_references" / "paper_style_guide.md",
        PROJECT_ROOT / "02_references" / "scoring_rubric.md",
    ]:
        checks.append((rel(path), path.exists()))
    print("== Paper Check ==")
    failed = False
    for path, ok in checks:
        print(f"{path}: {'ok' if ok else 'missing'}")
        failed = failed or not ok
    if failed:
        raise SystemExit(1)


def command_latex_check(args):
    pdf_path = run_latex_compile()
    print(pdf_path)
    if args.skip_layout_check:
        return
    issues = run_layout_check(
        pdf_path=pdf_path,
        aux_path=PROJECT_ROOT / "07_paper" / "main.aux",
        max_internal_gap_ratio=args.max_internal_gap_ratio,
        label_expectations=args.expect_label_page,
    )
    _assert_layout_ok(issues)
