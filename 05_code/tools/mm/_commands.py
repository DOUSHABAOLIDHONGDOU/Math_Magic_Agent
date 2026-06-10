"""Thin command-function wrappers used by the CLI.

These functions live here rather than in domain modules when they orchestrate
multiple subsystems (e.g. import-problem touches archive, state, problem files
in one flow).
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from ._archive import (
    STALE_TOPIC_KEYWORDS,
    archive_artifact_paths,
    collect_detected_stale_artifact_paths,
    collect_generated_artifact_paths,
    derive_current_topic_keywords,
)
from ._briefs import render_approval_brief, render_model_confirmation_brief, render_scheme_generation_prompt, scheme_position
from ._data import detect_question_ids, inspect_data_file, write_data_dictionary
from ._paths import (
    PROJECT_ROOT,
    QUESTIONS,
    SCHEMES,
    SELECTED_SCHEME_STATUSES,
    question_section_path,
    resolve_project_path,
)
from ._state import (
    active_question_ids,
    append_artifact,
    approved_schemes,
    assert_question_unlocked,
    ensure_question,
    ensure_scheme,
    load_state,
    reset_problem_workflow_state,
    save_state,
    set_stage,
    set_trust_profile,
    TRUST_PROFILES,
)
from ._util import (
    append_markdown_log,
    now_iso,
    print_user_facing_brief,
    read_text,
    rel,
    today,
    write_text,
)
from ._workorder import create_workorder, render_claude_prompt


# ---------------------------------------------------------------------------
# Init / status / import / scan


def command_init_state(args):
    from ._paths import STATE_PATH
    from ._state import default_state

    if STATE_PATH.exists() and not args.force:
        print(STATE_PATH)
        print("state already exists; use --force to reset")
        return
    state = default_state()
    save_state(state)
    print(STATE_PATH)


def command_import_problem(args):
    from ._state import default_state

    state = load_state()
    language_state = state.get("language", default_state()["language"])
    title = args.title or "题目名称待定"
    statement_text = ""
    if args.statement:
        statement_text = read_text(Path(args.statement))
    question_ids = detect_question_ids(statement_text)
    if not question_ids:
        question_ids = QUESTIONS[: args.num_questions]
    problem_path = PROJECT_ROOT / "01_problem" / "problem_statement.md"
    if getattr(args, "archive_existing_generated", True):
        archive_artifact_paths(
            state,
            collect_generated_artifact_paths(),
            reason=f"import-problem archived generated artifacts before loading `{title}`",
            profile="all-generated-before-import",
            dry_run=False,
        )
    question_rows = [
        f"| {qid} | 待 Codex 拆解 | 待填写 | 待填写 | 待填写 |" for qid in question_ids
    ]
    body = [
        "# Problem Statement",
        "",
        "## 题目信息",
        "",
        "- 竞赛类型：赛前训练",
        f"- 题目编号：{args.problem_id or '待填写'}",
        f"- 题目名称：{title}",
        "- 附件列表：待数据扫描后补充",
        "",
        "## 原始题面",
        "",
        statement_text or "待粘贴或导入。",
        "",
        "## 问题拆解",
        "",
        "| 问题 | 原题要求 | 实际建模任务 | 必须输出 | 可选输出 |",
        "|---|---|---|---|---|",
        *question_rows,
        "",
        "## 隐含约束",
        "",
        "- 待 Codex 根据题面整理。",
        "",
        "## 评价指标",
        "",
        "- 待 Codex 根据题面整理。",
        "",
    ]
    write_text(problem_path, "\n".join(body))
    reset_problem_workflow_state(state, question_ids)
    state["language"] = language_state
    state["problem"]["title"] = title
    state["problem"]["statement_file"] = rel(problem_path)
    state["problem"]["question_ids"] = question_ids
    if args.data_dir:
        state["problem"]["raw_data_dir"] = rel(Path(args.data_dir))
    append_artifact(state, "problem_statement", problem_path, "imported problem statement")
    from ._project_state import update_project_state_summary

    update_project_state_summary(state, note="新题导入时已重置题目级工作流状态。")
    save_state(state)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} 题目导入",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl import-problem",
            f"- 用途：导入训练题目 `{title}`。",
            f"- 关联文件：`{rel(problem_path)}`",
        ],
    )
    print(problem_path)


def command_archive_stale_artifacts(args):
    state = load_state()
    keywords = args.keyword or STALE_TOPIC_KEYWORDS
    current_keywords = derive_current_topic_keywords(state, extras=args.current_keyword)
    if args.path:
        paths = [resolve_project_path(path) for path in args.path]
        selected = [path for path in paths if path is not None]
        profile = "explicit-paths"
    elif args.profile == "all-generated":
        selected = collect_generated_artifact_paths()
        profile = "all-generated"
    else:
        selected = collect_detected_stale_artifact_paths(
            keywords,
            current_keywords,
            include_related=not args.no_related,
        )
        profile = "detected-old-topic"

    from ._paths import safe_project_file

    selected = [path for path in selected if path is not None and safe_project_file(path)]
    if not selected:
        print("No stale generated artifacts matched.")
        return

    if args.dry_run or not args.force:
        _, rows = archive_artifact_paths(state, selected, reason=args.reason, profile=profile, dry_run=True)
        print("== Stale Artifact Archive Dry Run ==")
        print(f"profile: {profile}")
        if profile == "detected-old-topic":
            print(f"current_topic_keywords: {', '.join(current_keywords[:12])}")
        print(f"count: {len(rows)}")
        for row in rows:
            print(row["source"])
        if not args.force:
            print("Add --force to move these files into 00_shared/archive/stale_artifacts/.")
        return

    manifest_path, rows = archive_artifact_paths(state, selected, reason=args.reason, profile=profile, dry_run=False)
    save_state(state)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} 旧题产物归档",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl archive-stale-artifacts",
            f"- 用途：归档疑似旧题/污染产物，profile `{profile}`。",
            f"- 归档数量：{len(rows)}",
            f"- 清单：`{rel(manifest_path) if manifest_path else '无'}`",
        ],
    )
    print(f"Archived {len(rows)} files.")
    if manifest_path:
        print(manifest_path)


def command_scan_data(args):
    state = load_state()
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = PROJECT_ROOT / data_dir
    if not data_dir.exists():
        raise SystemExit(f"data dir not found: {data_dir}")
    rows = []
    for path in sorted(p for p in data_dir.rglob("*") if p.is_file()):
        rows.extend(inspect_data_file(path, sample_rows=args.sample_rows, include_unsupported=args.include_unsupported))
    out_path = Path(args.out) if args.out else PROJECT_ROOT / "01_problem" / "data_dictionary.md"
    if not out_path.is_absolute():
        out_path = PROJECT_ROOT / out_path
    write_data_dictionary(out_path, rows, data_dir)
    state["problem"]["raw_data_dir"] = rel(data_dir)
    state["problem"]["data_dictionary"] = rel(out_path)
    append_artifact(state, "data_dictionary", out_path, "scanned raw data files")
    save_state(state)
    print(out_path)


# ---------------------------------------------------------------------------
# Language / question control


def command_approve_language(args):
    state = load_state()
    decision_id = args.decision_id or next_decision_id()
    state["language"]["recommended"] = args.language
    state["language"]["approved"] = True
    state["language"]["decision_id"] = decision_id
    save_state(state)
    append_decision(decision_id, "代码语言审批", "全局", f"批准默认实现语言：{args.language}", args.notes)
    print(decision_id)


def command_set_active_question(args):
    state = load_state()
    question = ensure_question(args.question)
    if question not in active_question_ids(state):
        raise SystemExit(f"{question} is not an active question for the imported problem")
    state["current_question"] = question
    questions = active_question_ids(state)
    current_index = questions.index(question)
    for index, qid in enumerate(questions):
        qstate = state["questions"][qid]
        if index < current_index:
            continue
        if qid == question:
            if qstate["schemes_generated"]:
                qstate["status"] = "schemes_prepared"
            elif qstate["status"] in ["not_started", "deferred_waiting_previous_question"]:
                qstate["status"] = "active"
            continue
        if args.defer_later and not qstate.get("paper_written"):
            qstate["status"] = "deferred_waiting_previous_question"
            qstate["schemes_approved"] = False
            qstate["scheme_decision_id"] = None
            qstate["workorders_created"] = False
            for scheme in SCHEMES:
                scheme_state = qstate["schemes"][scheme]
                if scheme_state.get("status") in ["draft_ready", "draft_template", "not_started"]:
                    scheme_state["status"] = "deferred_draft"
    save_state(state)
    print(question)


# ---------------------------------------------------------------------------
# Schemes / briefs / workorders


def command_prepare_schemes(args):
    state = load_state()
    question = ensure_question(args.question)
    if state["stage"] == "INIT" and not args.force:
        raise SystemExit("problem is not loaded; run import-problem first or use --force")
    assert_question_unlocked(state, question, force=args.force)
    template = read_text(PROJECT_ROOT / "03_methods" / "method_scheme_template.md")
    # Generate the RAG retrieval brief BEFORE rendering the scheme prompt so the
    # latter can inline it. Skips silently when there's no index or no problem yet.
    rag_brief_path = _maybe_generate_rag_brief(state, question)
    prompt_path = PROJECT_ROOT / "03_methods" / question / "codex_scheme_generation_prompt.md"
    prompt = render_scheme_generation_prompt(question)
    write_text(prompt_path, prompt)
    generated = [prompt_path]
    for scheme in SCHEMES:
        out_path = PROJECT_ROOT / "03_methods" / question / f"scheme_{scheme}.md"
        if out_path.exists() and not args.overwrite:
            generated.append(out_path)
            state["questions"][question]["schemes"][scheme]["status"] = "draft_ready"
            continue
        text = template
        text = text.replace("- 问题：Q1 / Q2 / Q3", f"- 问题：{question}")
        text = text.replace("- 问题：QX", f"- 问题：{question}")
        text = text.replace("- 方案：A / B / C", f"- 方案：{scheme}")
        text = text.replace("- 方案：X", f"- 方案：{scheme}")
        text = text.replace(
            "- 定位：稳健解释型 / 竞赛均衡型 / 冲奖增强型",
            f"- 定位：{scheme_position(scheme)}",
        )
        text = text.replace("- 状态：待审批 / 已审批 / 已实现 / 已淘汰", "- 状态：待 Codex 生成")
        write_text(out_path, text)
        generated.append(out_path)
        state["questions"][question]["schemes"][scheme]["status"] = "draft_template"
    state["current_question"] = question
    state["questions"][question]["schemes_generated"] = True
    state["questions"][question]["status"] = "schemes_prepared"
    set_stage(state, "SCHEMES_GENERATED")
    for path in generated:
        append_artifact(state, "scheme_artifact", path, f"{question} scheme workflow artifact")
    if rag_brief_path is not None:
        append_artifact(state, "rag_context_brief", rag_brief_path, f"{question} retrieved passages")
    save_state(state)
    for path in generated:
        print(path)
    if rag_brief_path is not None:
        print(rag_brief_path)


def _maybe_generate_rag_brief(state, question):
    """Run RAG retrieval as a side-effect of prepare-schemes when index is built.

    Returns the brief path on success, or None when the index is missing or
    retrieval throws — we never block prepare-schemes on RAG.
    """
    from ._rag import (
        INDEX_PATH,
        RAG_OUTPUT_DIR,
        _problem_query_for_question,
        classify_topic,
        retrieve,
    )

    if not INDEX_PATH.exists():
        return None
    try:
        query = _problem_query_for_question(state, question)
        if not query.strip():
            return None
        hits = retrieve(query, top_k=5)
    except SystemExit:
        return None
    topic = classify_topic(query)
    RAG_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RAG_OUTPUT_DIR / f"{question}_top_passages.md"
    lines = [
        f"# {question} 参考优秀论文片段（auto-generated by prepare-schemes）",
        "",
        f"- 推断题型：`{topic}`",
        "",
    ]
    if not hits:
        lines.append("_BM25 未命中任何段落_")
    else:
        for hit in hits:
            lines.extend(
                [
                    f"## #{hit['rank']}  score={hit['score']:.3f}  source: `{hit['source']}`",
                    "",
                    "> " + hit["text"].replace("\n", "\n> "),
                    "",
                ]
            )
    write_text(out_path, "\n".join(lines))
    return out_path


def command_create_approval_brief(args):
    state = load_state()
    question = ensure_question(args.question)
    assert_question_unlocked(state, question, force=args.force)
    out_path = PROJECT_ROOT / "03_methods" / question / "approval_brief.md"
    text = render_approval_brief(state, question)
    write_text(out_path, text)
    append_artifact(state, "approval_brief", out_path, f"{question} user-facing scheme approval brief")
    save_state(state)
    print_user_facing_brief(out_path, text, f"{question} scheme approval options")


def command_create_model_confirmation_brief(args):
    state = load_state()
    question = ensure_question(args.question)
    fallback_scheme = ensure_scheme(args.scheme) if args.scheme else "B"
    qstate = state["questions"][question]
    passed = [scheme for scheme in SCHEMES if qstate["schemes"][scheme].get("review_result") == "PASS"]
    if not passed and not args.force:
        raise SystemExit(f"{question} has no PASS review result; cannot create model confirmation brief")
    out_path = PROJECT_ROOT / "03_methods" / question / "model_confirmation_brief.md"
    text = render_model_confirmation_brief(state, question, passed[0] if passed else fallback_scheme)
    write_text(out_path, text)
    append_artifact(state, "model_confirmation_brief", out_path, f"{question} model confirmation options")
    save_state(state)
    print_user_facing_brief(out_path, text, f"{question} model confirmation options")


def command_approve_schemes(args):
    state = load_state()
    question = ensure_question(args.question)
    assert_question_unlocked(state, question, force=args.force)
    schemes = parse_schemes(args.schemes)
    decision_id = args.decision_id or next_decision_id()
    state["questions"][question]["schemes_approved"] = True
    state["questions"][question]["scheme_decision_id"] = decision_id
    state["questions"][question]["status"] = "schemes_approved"
    for scheme in schemes:
        state["questions"][question]["schemes"][scheme]["status"] = "approved_to_run"
        mark_scheme_approval(question, scheme, decision_id, args.notes)
    for scheme in SCHEMES:
        if scheme not in schemes and state["questions"][question]["schemes"][scheme].get("status") in [
            "draft_ready",
            "draft_template",
            "approved_to_run",
        ]:
            state["questions"][question]["schemes"][scheme]["status"] = "not_selected"
    set_stage(state, "SCHEMES_APPROVED")
    save_state(state)
    append_decision(decision_id, f"{question} 方案审批", question, f"批准运行方案：{', '.join(schemes)}", args.notes)
    print(decision_id)


def parse_schemes(value: str) -> list[str]:
    schemes = [ensure_scheme(s.strip()) for s in value.split(",") if s.strip()]
    if not schemes:
        raise SystemExit("at least one scheme is required")
    return schemes


def next_decision_id() -> str:
    log = read_text(PROJECT_ROOT / "00_shared" / "DECISION_LOG.md")
    nums = [int(m.group(1)) for m in re.finditer(r"## D-(\d+)", log)]
    return f"D-{max(nums, default=0) + 1:03d}"


def append_decision(decision_id: str, title: str, scope: str, conclusion: str, notes: str = "") -> None:
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "DECISION_LOG.md",
        f"{decision_id} {title}",
        [
            f"- 日期：{today()}",
            "- 决策人：用户",
            f"- 相关问题：{scope}",
            f"- 结论：{conclusion}",
            f"- 选择理由：{notes or '用户审批通过。'}",
            "- 后续影响：进入下一阶段。",
            "- 是否允许重开：是，需用户重新确认。",
        ],
    )


def mark_scheme_approval(question: str, scheme: str, decision_id: str, notes: str) -> None:
    path = PROJECT_ROOT / "03_methods" / question / f"scheme_{scheme}.md"
    if not path.exists():
        return
    append_markdown_log(
        path,
        "用户审批记录",
        [
            f"- 日期：{today()}",
            f"- 是否批准运行：是",
            f"- 决策 ID：{decision_id}",
            f"- 审批意见：{notes or '批准进入 Claude Code 实现。'}",
        ],
    )


def command_confirm_model(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    if state["questions"][question]["schemes"][scheme].get("review_result") != "PASS" and not args.force:
        raise SystemExit(
            "selected scheme has not passed Codex review; run mark-reviewed --result PASS first or use --force"
        )
    decision_id = args.decision_id or next_decision_id()
    approved_path = PROJECT_ROOT / "03_methods" / question / "approved.md"
    text = [
        f"# {question} Approved Method",
        "",
        "## 审批状态",
        "",
        "- 方案审批：已完成",
        "- 模型确认：已完成",
        f"- 图表审批：{'已完成' if state['questions'][question]['figures_approved'] else '未完成'}",
        "",
        "## 最终采用方案",
        "",
        f"- 方案：{scheme}",
        f"- 决策 ID：{decision_id}",
        f"- 确认日期：{today()}",
        f"- 确认意见：{args.notes or '用户确认该方案作为最终模型。'}",
        "",
        "## 不可修改边界",
        "",
        "- Claude Code 不允许更换模型路线。",
        "- 后续修改必须重新提交用户审批。",
        "",
        "## 论文写入要点",
        "",
        "- Codex 根据最终结果补充。",
        "",
    ]
    write_text(approved_path, "\n".join(text))
    qstate = state["questions"][question]
    qstate["model_confirmed"] = True
    qstate["confirmed_scheme"] = scheme
    qstate["model_decision_id"] = decision_id
    qstate["status"] = "model_confirmed"
    state["current_question"] = question
    set_stage(state, "MODEL_CONFIRMED")
    append_artifact(state, "approved_method", approved_path, f"{question} confirmed scheme {scheme}")
    save_state(state)
    append_decision(decision_id, f"{question} 最终模型确认", question, f"最终采用方案 {scheme}", args.notes)
    print(approved_path)


def command_create_workorder(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    assert_question_unlocked(state, question, force=args.force)
    if state["questions"][question]["schemes"][scheme].get("status") not in SELECTED_SCHEME_STATUSES and not args.force:
        raise SystemExit(f"{question} scheme {scheme} is not approved; run approve-schemes first")
    out_path = create_workorder(
        question=question,
        scheme=scheme,
        workorder_id=args.workorder_id,
        out=Path(args.out) if args.out else None,
    )
    state["questions"][question]["schemes"][scheme]["workorder"] = rel(out_path)
    append_artifact(state, "claude_workorder", out_path, f"{question} scheme {scheme}")
    save_state(state)
    print(out_path)


def command_create_workorders(args):
    state = load_state()
    question = ensure_question(args.question)
    schemes = parse_schemes(args.schemes)
    assert_question_unlocked(state, question, force=args.force)
    if not state["questions"][question]["schemes_approved"] and not args.force:
        raise SystemExit("schemes are not approved; run approve-schemes first or use --force")
    created = []
    for scheme in schemes:
        if state["questions"][question]["schemes"][scheme].get("status") not in SELECTED_SCHEME_STATUSES and not args.force:
            raise SystemExit(f"{question} scheme {scheme} is not selected/approved")
        out = create_workorder(question=question, scheme=scheme)
        created.append(out)
        state["questions"][question]["schemes"][scheme]["workorder"] = rel(out)
        state["questions"][question]["schemes"][scheme]["status"] = "workorder_created"
        append_artifact(state, "claude_workorder", out, f"{question} scheme {scheme}")
    state["questions"][question]["workorders_created"] = True
    state["questions"][question]["status"] = "workorders_created"
    set_stage(state, "CLAUDE_WORKORDERS_CREATED")
    save_state(state)
    for path in created:
        print(path)


def command_create_claude_prompt(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    assert_question_unlocked(state, question, force=args.force)
    qscheme = state["questions"][question]["schemes"][scheme]
    if qscheme.get("status") not in SELECTED_SCHEME_STATUSES and not args.force:
        raise SystemExit(f"{question} scheme {scheme} is not approved; run approve-schemes first")
    workorder_value = qscheme.get("workorder")
    if not workorder_value:
        workorder_path = create_workorder(question=question, scheme=scheme)
    else:
        workorder_path = PROJECT_ROOT / workorder_value
    prompt_path = PROJECT_ROOT / "04_claude_workorders" / f"{question}_scheme_{scheme}_claude_prompt.md"
    prompt = render_claude_prompt(question, scheme, workorder_path)
    write_text(prompt_path, prompt)
    qscheme["workorder"] = rel(workorder_path)
    qscheme["claude_prompt"] = rel(prompt_path)
    if qscheme.get("status") == "approved_to_run":
        qscheme["status"] = "workorder_created"
    selected = approved_schemes(state["questions"][question]) or [scheme]
    state["questions"][question]["workorders_created"] = all(
        state["questions"][question]["schemes"][s].get("workorder") for s in selected
    )
    state["questions"][question]["status"] = "workorders_created"
    set_stage(state, "CLAUDE_WORKORDERS_CREATED")
    append_artifact(state, "claude_workorder", workorder_path, f"{question} scheme {scheme}")
    append_artifact(state, "claude_prompt", prompt_path, f"{question} scheme {scheme}")
    save_state(state)
    print(prompt_path)


# ---------------------------------------------------------------------------
# Figures / paper bookkeeping


def command_approve_figures(args):
    from ._paths import STAGES

    state = load_state()
    question = ensure_question(args.question)
    decision_id = args.decision_id or next_decision_id()
    qstate = state["questions"][question]
    if args.allow_non_chinese:
        qstate["figure_language"] = "non_chinese_exception"
    else:
        qstate["figure_language"] = "zh"
    qstate["figures_generated"] = True
    qstate["figures_approved"] = True
    qstate["figure_decision_id"] = decision_id
    qstate["status"] = "figures_approved"
    if STAGES.index(state.get("stage", "INIT")) < STAGES.index("FIGURES_APPROVED"):
        set_stage(state, "FIGURES_APPROVED")
    save_state(state)
    language_note = "非中文例外审批" if args.allow_non_chinese else "中文最终图"
    append_decision(
        decision_id,
        f"{question} 图表审批",
        question,
        f"批准图表（{language_note}）：{args.figures or '见 07_paper/figures 与 06_results'}",
        args.notes,
    )
    print(decision_id)


def command_mark_paper_written(args):
    from ._state import advance_current_question_after_paper_written

    state = load_state()
    question = ensure_question(args.question)
    state["questions"][question]["paper_written"] = True
    state["questions"][question]["paper_section"] = rel(question_section_path(question))
    state["questions"][question]["status"] = "paper_written"
    advance_current_question_after_paper_written(state, question)
    active_questions = active_question_ids(state)
    if all(state["questions"][q]["paper_written"] for q in active_questions):
        set_stage(state, "PAPER_WRITTEN")
    save_state(state)
    print(f"{question}: paper_written")


# ---------------------------------------------------------------------------
# Phase 6a: trust profile


def command_set_trust_profile(args):
    state = load_state()
    set_trust_profile(state, args.profile)
    save_state(state)
    append_markdown_log(
        PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md",
        f"AILOG-AUTO-{now_iso()} 信任配置变更",
        [
            f"- 日期：{today()}",
            "- 工具：agentctl set-trust-profile",
            f"- 用途：切换信任配置为 `{args.profile}`。",
            f"- 含义：strict=训练严格；normal=演练；fast=赛时快速通道。",
        ],
    )
    print(f"trust profile set to: {args.profile}")
    if args.profile == "fast":
        print("WARN: fast profile skips some approval pauses; intended for competition crunch only.")


# ---------------------------------------------------------------------------
# Phase 6c: AI usage log auto-generation


def command_gen_ai_log(args):
    """Append a draft AILOG entry summarising recent dispatches and decisions."""
    state = load_state()
    log_path = PROJECT_ROOT / "00_shared" / "AI_USAGE_LOG.md"
    existing = read_text(log_path) if log_path.exists() else "# AI Usage Log\n"
    lines = [
        f"- 日期：{today()}",
        "- 工具：agentctl gen-ai-log",
        f"- 题目：`{state['problem'].get('title') or '题目名称待定'}`",
        f"- 当前阶段：`{state.get('stage')}`",
        f"- 信任配置：`{state.get('trust_profile', 'strict')}`",
    ]
    active_questions = active_question_ids(state)
    for question in active_questions:
        qstate = state["questions"][question]
        confirmed = qstate.get("confirmed_scheme") or "—"
        lines.append(
            f"- {question}：confirmed={confirmed}, model_confirmed={qstate.get('model_confirmed')}, "
            f"paper_written={qstate.get('paper_written')}"
        )
    completion_dir = PROJECT_ROOT / "04_claude_workorders" / "completions"
    if completion_dir.exists():
        reports = sorted(completion_dir.glob("Q*_scheme_*_completion.md"))
        if reports:
            lines.append(f"- Claude 完成报告：共 {len(reports)} 份，最新 `{rel(reports[-1])}`")
    dispatch_log = PROJECT_ROOT / "04_claude_workorders" / "dispatch_logs"
    if dispatch_log.exists():
        logs = sorted(dispatch_log.glob("*.log"))
        if logs:
            lines.append(f"- Claude 调度日志：共 {len(logs)} 份，最新 `{rel(logs[-1])}`")
    append_markdown_log(log_path, f"AILOG-AUTO-{now_iso()} 自动汇总", lines)
    print(log_path)
