"""Codex review templates, mark-reviewed, scheme comparison.

Phase 3b: ``command_compare_schemes`` is now data-driven — it reads every
``06_results/<question>/tables/scheme_*_metrics.csv`` it finds, joins them on
column name, marks the best value per row with ★, and recommends a winner
combining metric score with each scheme's Codex review verdict.
"""

from __future__ import annotations

import csv
from pathlib import Path

from ._briefs import render_codex_review_template
from ._paths import PROJECT_ROOT, SCHEMES
from ._state import (
    append_artifact,
    approved_schemes,
    ensure_question,
    ensure_scheme,
    load_state,
    save_state,
    set_stage,
)
from ._util import now_iso, rel, write_text


def confirmed_scheme(state: dict, question: str) -> str:
    scheme = state["questions"][question].get("confirmed_scheme")
    if scheme:
        return scheme
    for candidate in SCHEMES:
        if state["questions"][question]["schemes"][candidate].get("review_result") == "PASS":
            return candidate
    return "待确认"


def create_review_file(state: dict, question: str, scheme: str) -> Path:
    out_path = PROJECT_ROOT / "06_results" / question / "logs" / f"scheme_{scheme}_codex_review.md"
    report = state["questions"][question]["schemes"][scheme].get("completion_report") or "待 Claude Code 提供"
    text = render_codex_review_template(question, scheme, report)
    write_text(out_path, text)
    state["questions"][question]["schemes"][scheme]["review"] = rel(out_path)
    state["questions"][question]["schemes"][scheme]["status"] = "review_template_created"
    append_artifact(state, "codex_review", out_path, f"{question} scheme {scheme}")
    return out_path


def command_create_review(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    out_path = create_review_file(state, question, scheme)
    save_state(state)
    print(out_path)


def command_mark_reviewed(args):
    state = load_state()
    question = ensure_question(args.question)
    scheme = ensure_scheme(args.scheme)
    status = args.result.upper()
    if status not in ["PASS", "REVISE", "BLOCKED"]:
        raise SystemExit("result must be PASS, REVISE, or BLOCKED")
    state["questions"][question]["schemes"][scheme]["review_result"] = status
    state["questions"][question]["schemes"][scheme]["status"] = f"review_{status.lower()}"
    state["questions"][question]["status"] = f"review_{status.lower()}"
    selected = approved_schemes(state["questions"][question]) or [scheme]
    state["questions"][question]["code_reviewed"] = all(
        state["questions"][question]["schemes"][s].get("review_result") == "PASS" for s in selected
    )
    if state["questions"][question]["code_reviewed"]:
        set_stage(state, "CODE_REVIEWED")
    save_state(state)
    print(f"{question} {scheme}: {status}")


# ---------------------------------------------------------------------------
# Phase 3b: data-driven scheme comparison


# A small set of metrics where "smaller is better". Everything else assumed
# "bigger is better". Codex can override by passing --invert-metric in future.
LOWER_IS_BETTER_KEYWORDS = (
    "rmse",
    "mae",
    "mse",
    "loss",
    "err",
    "time",
    "latency",
    "memory",
    "param_count",
)
# Columns that are bookkeeping, not optimization targets. Excluded from ★/score.
METADATA_KEYWORDS = (
    "seed",
    "random_state",
    "n_samples",
    "n_files",
    "n_rows",
    "total_rows",
    "version",
    "model",   # text label, not a number
    "method",
    "algorithm",
)


def _is_metadata_column(name: str) -> bool:
    lower = name.lower()
    return any(token in lower for token in METADATA_KEYWORDS)


def load_metrics_for_question(question: str) -> dict[str, dict[str, str]]:
    """Return ``{scheme: {metric: value}}`` for every metrics CSV that exists."""
    tables_dir = PROJECT_ROOT / "06_results" / question / "tables"
    if not tables_dir.exists():
        return {}
    results: dict[str, dict[str, str]] = {}
    for path in sorted(tables_dir.glob("scheme_*_metrics.csv")):
        # Filename is scheme_X_metrics.csv; extract X.
        name = path.stem  # scheme_B_metrics
        parts = name.split("_")
        if len(parts) < 2:
            continue
        scheme = parts[1].upper()
        if scheme not in SCHEMES:
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        if not rows:
            continue
        results[scheme] = {k: (v if v is not None else "") for k, v in rows[0].items()}
    return results


def _as_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def score_schemes(metrics: dict[str, dict[str, str]]) -> dict[str, dict]:
    """Compute per-metric winners and a normalized aggregate score per scheme.

    Returns ``{scheme: {"wins": int, "score": float, "metrics": {metric: (value, is_winner)}}}``.
    """
    if not metrics:
        return {}
    all_keys: list[str] = []
    for scheme in metrics:
        for key in metrics[scheme]:
            if key not in all_keys:
                all_keys.append(key)

    per_scheme: dict[str, dict] = {scheme: {"wins": 0, "score": 0.0, "metrics": {}} for scheme in metrics}
    score_counts = {scheme: 0 for scheme in metrics}
    single_scheme = len(metrics) < 2  # spread is meaningless with one scheme
    for key in all_keys:
        is_meta = _is_metadata_column(key)
        numeric_values: dict[str, float] = {}
        for scheme, row in metrics.items():
            value = _as_float(row.get(key))
            if value is not None:
                numeric_values[scheme] = value
        if not numeric_values:
            for scheme in metrics:
                per_scheme[scheme]["metrics"][key] = (metrics[scheme].get(key, ""), False)
            continue
        if is_meta or single_scheme:
            # Show the value but don't crown anybody — keeps single-scheme runs honest.
            for scheme in metrics:
                per_scheme[scheme]["metrics"][key] = (metrics[scheme].get(key, ""), False)
            continue
        lower_better = any(token in key.lower() for token in LOWER_IS_BETTER_KEYWORDS)
        if lower_better:
            best = min(numeric_values.values())
        else:
            best = max(numeric_values.values())
        spread = max(numeric_values.values()) - min(numeric_values.values()) or 1.0
        for scheme, value in numeric_values.items():
            is_winner = value == best
            per_scheme[scheme]["metrics"][key] = (metrics[scheme].get(key, ""), is_winner)
            if is_winner:
                per_scheme[scheme]["wins"] += 1
            normalized = (best - value) / spread if lower_better else (value - min(numeric_values.values())) / spread
            per_scheme[scheme]["score"] += normalized
            score_counts[scheme] += 1
        # Non-numeric schemes for this row.
        for scheme in metrics:
            if scheme not in numeric_values and key not in per_scheme[scheme]["metrics"]:
                per_scheme[scheme]["metrics"][key] = (metrics[scheme].get(key, ""), False)
    for scheme in metrics:
        if score_counts[scheme]:
            per_scheme[scheme]["score"] /= score_counts[scheme]
    return per_scheme


def render_scheme_comparison(state: dict, question: str) -> str:
    metrics = load_metrics_for_question(question)
    scored = score_schemes(metrics)
    qstate = state["questions"][question]
    lines = [
        f"# {question} 方案对比",
        "",
        f"- 生成时间：{now_iso()}",
        f"- 题目：`{state['problem'].get('title') or '题目名称待定'}`",
        "",
    ]
    if not metrics:
        lines.extend(
            [
                "## 未发现结构化指标表",
                "",
                f"请确认 Claude Code 已经把方案的核心指标写入 `06_results/{question}/tables/scheme_*_metrics.csv`。",
                "",
            ]
        )
        return "\n".join(lines)
    metric_keys: list[str] = []
    for scheme_data in scored.values():
        for key in scheme_data["metrics"]:
            if key not in metric_keys:
                metric_keys.append(key)
    header = "| 指标 | " + " | ".join(sorted(metrics.keys())) + " |"
    sep = "|---" + "|---" * len(metrics) + "|"
    lines.append("## 核心指标对比")
    lines.append("")
    lines.append(header)
    lines.append(sep)
    for key in metric_keys:
        cells = []
        for scheme in sorted(metrics.keys()):
            value, is_winner = scored[scheme]["metrics"].get(key, ("", False))
            cells.append(f"★ {value}" if is_winner else str(value))
        lines.append(f"| `{key}` | " + " | ".join(cells) + " |")
    lines.extend(["", "## 评分与复审摘要", ""])
    single_scheme = len(metrics) < 2
    if single_scheme:
        lines.append("> 单方案运行：跳过综合分计算（spread 为 0），仅展示原始指标和复审结论。")
        lines.append("")
    lines.append("| 方案 | wins | 综合分（0~1） | Codex 复审 | 状态 |")
    lines.append("|---|---|---|---|---|")
    ranking = sorted(scored.items(), key=lambda kv: (kv[1]["score"], kv[1]["wins"]), reverse=True)
    for scheme, data in ranking:
        scheme_state = qstate["schemes"][scheme]
        review = scheme_state.get("review_result") or "—"
        status = scheme_state.get("status", "")
        wins_cell = "—" if single_scheme else str(data["wins"])
        score_cell = "—" if single_scheme else f"{data['score']:.3f}"
        lines.append(
            f"| {scheme} | {wins_cell} | {score_cell} | {review} | {status} |"
        )
    lines.append("")
    if ranking:
        winner, top = ranking[0]
        top_review = qstate["schemes"][winner].get("review_result") or "—"
        lines.append("## 推荐")
        lines.append("")
        if single_scheme:
            if top_review == "PASS":
                lines.append(
                    f"- **建议确认方案 {winner}**：仅跑了单方案，Codex 复审 PASS，可进入模型确认审批。"
                )
            else:
                lines.append(
                    f"- **方案 {winner}** Codex 复审为 `{top_review}`；建议先补强或返修再做模型确认。"
                )
        elif top_review == "PASS":
            lines.append(
                f"- **建议确认方案 {winner}**：综合分 {top['score']:.3f}，Codex 复审 PASS，可直接进入模型确认审批。"
            )
        else:
            lines.append(
                f"- **暂时领先方案 {winner}**：综合分 {top['score']:.3f}，但 Codex 复审为 `{top_review}`，建议先补强或返修，再做模型确认。"
            )
        lines.append("- 推荐仅供参考，最终模型确认仍需用户在 `create-model-confirmation-brief` 审批。")
    lines.append("")
    return "\n".join(lines)


def command_compare_schemes(args):
    state = load_state()
    question = ensure_question(args.question)
    out_path = PROJECT_ROOT / "06_results" / question / f"{question}_scheme_comparison.md"
    text = render_scheme_comparison(state, question)
    write_text(out_path, text)
    append_artifact(state, "scheme_comparison", out_path, question)
    save_state(state)
    print(out_path)
