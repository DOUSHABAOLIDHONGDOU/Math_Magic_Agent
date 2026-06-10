"""Phase 3a: auto-eda — generate 6 diagnostic figures plus an eda_summary.md.

Reads the raw data dir registered in the workflow state, samples every parsable
file, and writes findings to ``06_results/<question>/eda/``. The summary is then
auto-injected into Codex's scheme-generation prompt by ``_briefs``.
"""

from __future__ import annotations

import os
from pathlib import Path

from ._paths import PROJECT_ROOT
from ._state import (
    active_question_ids,
    append_artifact,
    ensure_question,
    load_state,
    save_state,
)
from ._util import now_iso, read_text, rel, write_text


MAX_DISTRIBUTION_SUBPLOTS = 9
TOP_K_FOR_PAIRPLOT = 5


def _ensure_mpl_cache() -> None:
    os.environ.setdefault("MPLCONFIGDIR", str(PROJECT_ROOT / ".cache" / "matplotlib"))


def _gather_dataframe(data_dir: Path, sample_rows: int):
    """Concatenate all parsable tabular files into one wide DataFrame (sampled)."""
    import pandas as pd

    frames = []
    for path in sorted(p for p in data_dir.rglob("*") if p.is_file()):
        suffix = path.suffix.lower()
        try:
            if suffix in (".csv", ".txt"):
                frames.append(pd.read_csv(path, nrows=sample_rows))
            elif suffix == ".xlsx":
                xls = pd.ExcelFile(path)
                for sheet in xls.sheet_names:
                    frames.append(pd.read_excel(path, sheet_name=sheet, nrows=sample_rows))
            elif suffix == ".json":
                try:
                    frames.append(pd.read_json(path, lines=True, nrows=sample_rows))
                except (TypeError, ValueError):
                    frames.append(pd.read_json(path))
        except Exception:  # noqa: BLE001 - diagnostic tool, skip bad files
            continue
    if not frames:
        return None
    # Outer-concat without merging row index, keeps wide structure for EDA.
    return pd.concat(frames, axis=0, ignore_index=True, sort=False)


def _classify_distribution(series) -> str:
    import numpy as np

    s = series.dropna()
    if len(s) < 5:
        return "few"
    if s.dtype.kind not in {"f", "i", "u"}:
        return "categorical"
    skew = float(s.skew()) if hasattr(s, "skew") else 0.0
    if abs(skew) < 0.5:
        return "normal-like"
    if skew > 1.0:
        return "right-skewed"
    if skew < -1.0:
        return "left-skewed"
    # Cheap bimodality probe: split at median, compare both halves' std.
    median = float(np.median(s))
    left = s[s < median]
    right = s[s >= median]
    if len(left) > 5 and len(right) > 5:
        if abs(left.std() - right.std()) / (s.std() + 1e-9) > 0.6:
            return "possibly-bimodal"
    return "skewed"


def _outliers_iqr(series) -> int:
    s = series.dropna()
    if len(s) < 4 or s.dtype.kind not in {"f", "i", "u"}:
        return 0
    q1 = s.quantile(0.25)
    q3 = s.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return 0
    low = q1 - 1.5 * iqr
    high = q3 + 1.5 * iqr
    return int(((s < low) | (s > high)).sum())


def _plot_correlation(df_numeric, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    if df_numeric.shape[1] < 2:
        return
    corr = df_numeric.corr()
    fig, ax = plt.subplots(figsize=(max(4, 0.4 * len(corr)), max(4, 0.4 * len(corr))))
    cax = ax.imshow(corr.values, vmin=-1.0, vmax=1.0, cmap="RdBu_r")
    ax.set_xticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=60, ha="right", fontsize=8)
    ax.set_yticks(range(len(corr.columns)))
    ax.set_yticklabels(corr.columns, fontsize=8)
    fig.colorbar(cax, ax=ax, shrink=0.7)
    ax.set_title("Correlation matrix")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def _plot_missing(df, out_path: Path) -> None:
    import matplotlib.pyplot as plt
    import numpy as np

    missing = df.isna().astype(int).values
    if missing.size == 0:
        return
    fig, ax = plt.subplots(figsize=(max(4, 0.3 * df.shape[1]), 4))
    ax.imshow(missing, aspect="auto", cmap="Greys", interpolation="nearest")
    ax.set_xticks(range(df.shape[1]))
    ax.set_xticklabels(df.columns, rotation=60, ha="right", fontsize=8)
    ax.set_ylabel("row index")
    ax.set_title("Missing-value pattern (black = NaN)")
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def _plot_distributions(df_numeric, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    cols = list(df_numeric.columns)[:MAX_DISTRIBUTION_SUBPLOTS]
    if not cols:
        return
    n = len(cols)
    ncols = min(3, n)
    rows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(rows, ncols, figsize=(ncols * 3.5, rows * 2.8), squeeze=False)
    for i, col in enumerate(cols):
        ax = axes[i // ncols][i % ncols]
        series = df_numeric[col].dropna()
        if len(series):
            ax.hist(series.values, bins=30, color="#3a76c7", alpha=0.85)
        ax.set_title(col, fontsize=9)
        ax.tick_params(labelsize=8)
    for j in range(n, rows * ncols):
        axes[j // ncols][j % ncols].axis("off")
    fig.suptitle("Numeric distributions (sampled)", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def _plot_outliers(df_numeric, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    cols = list(df_numeric.columns)[:MAX_DISTRIBUTION_SUBPLOTS]
    if not cols:
        return
    fig, ax = plt.subplots(figsize=(max(5, 0.6 * len(cols)), 4))
    ax.boxplot([df_numeric[c].dropna().values for c in cols], labels=cols, showfliers=True)
    ax.set_title("Boxplot + IQR outliers (numeric fields)")
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right", fontsize=8)
    fig.tight_layout()
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def _plot_pair_top(df_numeric, target_col, out_path: Path) -> None:
    import matplotlib.pyplot as plt

    if df_numeric.shape[1] < 3 or target_col not in df_numeric.columns:
        return
    corrs = df_numeric.corr()[target_col].drop(target_col).abs().sort_values(ascending=False)
    top = corrs.head(TOP_K_FOR_PAIRPLOT).index.tolist()
    if not top:
        return
    fig, axes = plt.subplots(1, len(top), figsize=(3.2 * len(top), 3.2), squeeze=False)
    for i, col in enumerate(top):
        ax = axes[0][i]
        ax.scatter(df_numeric[col], df_numeric[target_col], s=8, alpha=0.6, color="#3a76c7")
        ax.set_xlabel(col, fontsize=8)
        ax.set_ylabel(target_col, fontsize=8)
        ax.set_title(f"|ρ|={corrs[col]:.2f}", fontsize=9)
        ax.tick_params(labelsize=7)
    fig.suptitle(f"Top-{len(top)} vs `{target_col}`", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.92])
    fig.savefig(out_path, dpi=130)
    plt.close(fig)


def _render_summary(df, df_numeric, eda_dir: Path, target_col) -> str:
    lines = [
        "# Auto EDA Summary",
        "",
        f"- 生成时间：{now_iso()}",
        f"- 样本行数：{len(df)}",
        f"- 字段总数：{df.shape[1]}（数值字段：{df_numeric.shape[1]}）",
        "",
        "## 字段诊断",
        "",
        "| 字段 | 类型 | 缺失率 | 分布 | 异常值（IQR） |",
        "|---|---|---|---|---|",
    ]
    for col in df.columns:
        series = df[col]
        miss = series.isna().mean() if len(series) else 0.0
        dist = _classify_distribution(series)
        outliers = _outliers_iqr(series)
        lines.append(f"| `{col}` | {series.dtype} | {miss:.1%} | {dist} | {outliers} |")
    lines.extend(
        [
            "",
            "## 生成的图",
            "",
            f"- 相关矩阵热力图：`{rel(eda_dir / 'eda_correlation.png')}`",
            f"- 缺失模式图：`{rel(eda_dir / 'eda_missing.png')}`",
            f"- 数值字段分布：`{rel(eda_dir / 'eda_distributions.png')}`",
            f"- 异常值箱线图：`{rel(eda_dir / 'eda_outliers.png')}`",
        ]
    )
    if target_col:
        lines.append(f"- 与 `{target_col}` 相关性 Top-{TOP_K_FOR_PAIRPLOT} 散点：`{rel(eda_dir / 'eda_pairplot_top5.png')}`")
    lines.append("")
    return "\n".join(lines)


def command_auto_eda(args):
    _ensure_mpl_cache()
    state = load_state()
    question = ensure_question(args.question)
    data_dir = state.get("problem", {}).get("raw_data_dir")
    if not data_dir:
        raise SystemExit("no raw data dir registered in workflow state; run scan-data first")
    data_path = Path(data_dir)
    if not data_path.is_absolute():
        data_path = PROJECT_ROOT / data_path
    if not data_path.exists():
        raise SystemExit(f"data dir not found: {data_path}")

    import pandas as pd  # noqa: F401  - ensure pandas import error surfaces early

    df = _gather_dataframe(data_path, sample_rows=args.sample_rows)
    if df is None or df.empty:
        raise SystemExit("no parsable tabular data found under the registered data dir")

    df_numeric = df.select_dtypes(include="number")
    eda_dir = PROJECT_ROOT / "06_results" / question / "eda"
    eda_dir.mkdir(parents=True, exist_ok=True)

    if not df_numeric.empty:
        _plot_correlation(df_numeric, eda_dir / "eda_correlation.png")
        _plot_distributions(df_numeric, eda_dir / "eda_distributions.png")
        _plot_outliers(df_numeric, eda_dir / "eda_outliers.png")
    _plot_missing(df, eda_dir / "eda_missing.png")

    target_col = args.target
    if target_col and target_col not in df_numeric.columns:
        target_col = None
    if not target_col and not df_numeric.empty:
        # Pick column with highest variance as fallback target.
        target_col = df_numeric.var().idxmax()
    if target_col:
        _plot_pair_top(df_numeric, target_col, eda_dir / "eda_pairplot_top5.png")

    summary_path = eda_dir / "eda_summary.md"
    write_text(summary_path, _render_summary(df, df_numeric, eda_dir, target_col))
    append_artifact(state, "auto_eda_summary", summary_path, question)
    save_state(state)
    print(summary_path)
