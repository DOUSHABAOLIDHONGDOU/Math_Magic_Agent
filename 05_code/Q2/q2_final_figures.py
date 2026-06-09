"""
Generate final Chinese figures for Q2 from reviewed Scheme B result tables.

The script only redraws approved result tables. It does not refit the model or
change the confirmed Q2-B modeling route.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "06_results" / "Q2" / "tables"
PAPER_FIG_DIR = ROOT / "07_paper" / "figures"
APPROVAL_DIR = ROOT / "03_methods" / "Q2"
MPL_CACHE_DIR = ROOT / ".cache" / "matplotlib"

PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Rectangle
import numpy as np
import pandas as pd

FONT_PATH = Path("/System/Library/Fonts/STHeiti Medium.ttc")
if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    font_name = font_manager.FontProperties(fname=str(FONT_PATH)).get_name()
else:
    font_name = "Arial Unicode MS"

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": [font_name, "PingFang SC", "Songti SC", "Arial Unicode MS"],
        "axes.unicode_minus": False,
        "figure.dpi": 150,
        "savefig.dpi": 320,
        "axes.titlesize": 12,
        "axes.labelsize": 10,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
    }
)

COLORS = {
    "ink": "#22302d",
    "grid": "#d8ddd8",
    "blue": "#2f6f9f",
    "green": "#2f7d62",
    "orange": "#c46a2c",
    "red": "#b94b4b",
    "purple": "#705b94",
    "fill_blue": "#b9d7ea",
    "fill_green": "#bfe1d2",
    "fill_orange": "#f0d0b4",
}


def style_axis(ax: plt.Axes) -> None:
    ax.grid(True, color=COLORS["grid"], linewidth=0.7, alpha=0.75)
    ax.set_axisbelow(True)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#8c9692")
    ax.spines["bottom"].set_color("#8c9692")
    ax.tick_params(colors=COLORS["ink"])


def save(fig: plt.Figure, filename: str) -> Path:
    path = PAPER_FIG_DIR / filename
    fig.savefig(path, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def draw_group_timing() -> Path:
    groups = pd.read_csv(TABLE_DIR / "scheme_B_group_timing.csv")
    groups = groups.sort_values("group_idx")
    fig, ax = plt.subplots(figsize=(6.8, 3.2))
    y_positions = np.arange(len(groups))[::-1]
    palette = [COLORS["fill_green"], COLORS["fill_blue"], COLORS["fill_orange"]]
    edge_palette = [COLORS["green"], COLORS["blue"], COLORS["orange"]]

    for y, (_, row), fill, edge in zip(y_positions, groups.iterrows(), palette, edge_palette):
        width = row["bmi_hi"] - row["bmi_lo"]
        rect = Rectangle((row["bmi_lo"], y - 0.28), width, 0.56, facecolor=fill, edgecolor=edge, linewidth=1.5)
        ax.add_patch(rect)
        range_label = f"{row['bmi_lo']:.1f}-{row['bmi_hi']:.1f}"
        if width >= 2.8:
            ax.text(row["bmi_lo"] + width / 2, y, range_label, ha="center", va="center", color=COLORS["ink"], fontsize=8.6)
        else:
            ax.text(row["bmi_hi"] + 0.15, y + 0.20, range_label, ha="left", va="center", color=edge, fontsize=8.0)
        detail = f"G{int(row['group_idx'])}：n={int(row['n'])}，{row['optimal_t_wday']}"
        ax.text(47.25, y, detail, ha="right", va="center", color=COLORS["ink"], fontsize=8.6)

    for boundary in groups["bmi_hi"].iloc[:-1]:
        ax.axvline(boundary, color=COLORS["red"], linestyle="--", linewidth=1.0, alpha=0.85)
    boundary_text = "BMI 边界：" + "、".join(f"{value:.1f}" for value in groups["bmi_hi"].iloc[:-1])
    ax.text(29.65, -0.50, boundary_text, ha="center", va="top", fontsize=7.8, color=COLORS["red"])

    ax.set_xlim(groups["bmi_lo"].min() - 1.0, groups["bmi_hi"].max() + 1.0)
    ax.set_ylim(-0.7, len(groups) - 0.3)
    ax.set_yticks(y_positions)
    ax.set_yticklabels([f"第 {int(g)} 组" for g in groups["group_idx"]])
    ax.set_xlabel("孕妇 BMI")
    ax.set_title("Q2-B BMI 分组与推荐检测时点", pad=10)
    style_axis(ax)
    ax.grid(axis="y", visible=False)
    ax.text(
        0.01,
        -0.23,
        "注：时点来自模型预测达标时间 T* 的动态规划分组；论文中按保守口径解释。",
        transform=ax.transAxes,
        color="#5d6864",
        fontsize=8.2,
    )
    return save(fig, "q2_fig1_bmi_group_timing.png")


def draw_bootstrap_stability() -> Path:
    boot = pd.read_csv(TABLE_DIR / "scheme_B_bootstrap_stability.csv").sort_values("group")
    groups = pd.read_csv(TABLE_DIR / "scheme_B_group_timing.csv").sort_values("group_idx")
    boundary_values = groups["bmi_hi"].iloc[:-1].to_numpy()
    boundary_std = [
        float(boot.loc[boot["group"] == 1, "bmi_hi_std"].iloc[0]),
        float(boot.loc[boot["group"] == 2, "bmi_hi_std"].iloc[0]),
    ]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.0), gridspec_kw={"width_ratios": [1.0, 1.05]})
    ax1.errorbar(
        [1, 2],
        boundary_values,
        yerr=boundary_std,
        fmt="o",
        color=COLORS["blue"],
        ecolor=COLORS["fill_blue"],
        elinewidth=6,
        capsize=4,
        markersize=6,
    )
    ax1.set_xticks([1, 2])
    ax1.set_xticklabels(["边界 1", "边界 2"])
    ax1.set_ylabel("BMI 分界值")
    ax1.set_title("BMI 分界稳定性")
    for x, y, s in zip([1, 2], boundary_values, boundary_std):
        ax1.text(x, y + 0.18, f"{y:.2f}±{s:.2f}", ha="center", fontsize=8.0, color=COLORS["ink"])
    style_axis(ax1)

    ax2.errorbar(
        boot["group"],
        boot["opt_t_mean"],
        yerr=boot["opt_t_std"],
        fmt="o-",
        color=COLORS["green"],
        ecolor=COLORS["fill_green"],
        elinewidth=6,
        capsize=4,
        markersize=6,
    )
    ax2.set_xticks(boot["group"])
    ax2.set_xticklabels([f"G{int(g)}" for g in boot["group"]])
    ax2.set_ylabel("推荐时点/周")
    ax2.set_title("推荐时点稳定性")
    ax2.set_ylim(9.5, 12.2)
    for _, row in boot.iterrows():
        ax2.text(row["group"], row["opt_t_mean"] + 0.13, f"{row['opt_t_mean']:.2f}", ha="center", fontsize=8.0, color=COLORS["ink"])
    style_axis(ax2)

    fig.suptitle("自助抽样下分组边界与时点稳定性", y=1.01, fontsize=12.0, color=COLORS["ink"])
    return save(fig, "q2_fig2_bootstrap_stability.png")


def draw_model_empirical_tstar() -> Path:
    df = pd.read_csv(TABLE_DIR / "scheme_B_individual_time.csv")
    groups = pd.read_csv(TABLE_DIR / "scheme_B_group_timing.csv").sort_values("group_idx")
    rng = np.random.default_rng(20260609)
    jitter_model = rng.normal(0, 0.025, size=len(df))
    jitter_emp = rng.normal(0, 0.025, size=len(df))

    fig, ax = plt.subplots(figsize=(6.8, 4.1))
    ax.scatter(
        df["bmi"],
        df["T_star"] + jitter_model,
        s=17,
        color=COLORS["blue"],
        alpha=0.50,
        edgecolors="none",
        label="模型预测 T*",
    )
    ax.scatter(
        df["bmi"],
        df["emp_T_star"] + jitter_emp,
        s=17,
        color=COLORS["orange"],
        alpha=0.56,
        edgecolors="none",
        label="实测首次达标时间",
    )
    censored = df["emp_censored"].astype(str).str.lower().isin(["true", "1"])
    if censored.any():
        ax.scatter(
            df.loc[censored, "bmi"],
            df.loc[censored, "emp_T_star"],
            s=42,
            facecolors="none",
            edgecolors=COLORS["red"],
            linewidth=1.1,
            label="实测右删失",
        )
    for boundary in groups["bmi_hi"].iloc[:-1]:
        ax.axvline(boundary, color=COLORS["red"], linestyle="--", linewidth=1.0, alpha=0.82)
    ax.axhline(10, color="#84908c", linestyle=":", linewidth=1.1, label="10 周基准")
    ax.set_title("模型预测 T* 退化与实测 T* 变化对照")
    ax.set_xlabel("孕妇 BMI")
    ax.set_ylabel("达标时间/周")
    ax.set_ylim(9.5, 25.5)
    style_axis(ax)
    ax.legend(loc="upper right", frameon=True, facecolor="white", edgecolor="#c8d0cc")
    ax.text(
        0.02,
        -0.18,
        "模型 T* 多集中于 10 周；实测 T* 用于稳健性补充，不改变 Q2-B 主线。",
        transform=ax.transAxes,
        color="#5d6864",
        fontsize=8.2,
    )
    return save(fig, "q2_fig3_tstar_robustness.png")


def draw_contact_sheet(paths: list[Path]) -> Path:
    cols = 2
    rows = math.ceil(len(paths) / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(10, rows * 3.5))
    axes_arr = np.atleast_1d(axes).ravel()
    titles = [
        "图1 BMI 分组与时点",
        "图2 自助抽样稳定性",
        "图3 T* 稳健性对照",
    ]
    for ax, path, title in zip(axes_arr, paths, titles):
        img = plt.imread(path)
        ax.imshow(img)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    for ax in axes_arr[len(paths) :]:
        ax.axis("off")
    fig.suptitle("Q2 论文候选图审批总览", y=0.995, fontsize=14, color=COLORS["ink"])
    out = APPROVAL_DIR / "q2_figure_approval_sheet.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return out


def write_approval_brief(paths: list[Path], sheet: Path, manifest: Path) -> Path:
    out = APPROVAL_DIR / "figure_approval_brief.md"
    lines = [
        "# Q2 图表审批简报",
        "",
        "## 当前审批对象",
        "",
        "- 当前只审批 Q2 的最终论文候选图。",
        "- Q2-B 已确认作为最终模型；本轮图表不改变建模路线。",
        "- 这些图均为 Codex 根据已复审 CSV 表重绘的中文图，Claude Code 英文图不直接入论文。",
        "",
        "## 候选图",
        "",
        "| 图号 | 文件 | 表达结论 | 是否建议入文 |",
        "|---|---|---|---|",
        f"| Q2-FIG-001 | `{paths[0].relative_to(ROOT)}` | 展示 BMI 三组分界和各组推荐检测时点 | 建议入文 |",
        f"| Q2-FIG-002 | `{paths[1].relative_to(ROOT)}` | 展示自助抽样下分界和推荐时点稳定性 | 建议入文，可与敏感性表配合 |",
        f"| Q2-FIG-003 | `{paths[2].relative_to(ROOT)}` | 展示模型 T* 退化及实测 T* 稳健性补充 | 建议入文，但正文必须保守解释 |",
        "",
        "## 审批总览",
        "",
        f"- 总览图：`{sheet.relative_to(ROOT)}`",
        f"- 清单：`{manifest.relative_to(ROOT)}`",
        "",
        "## Codex 建议",
        "",
        "- 建议通过三张图，但 5.2 中不要堆图；优先图 1 主结果、图 2 稳定性，图 3 可放在稳健性分析段落。",
        "- 若担心版面过满，可批准图 1 和图 3 入正文，图 2 的数值改为表格。",
        "",
        "## 你可以这样回复",
        "",
        "```text",
        "Q2 图表审批通过：图1、图2、图3都可以入文。",
        "```",
        "",
        "或：",
        "",
        "```text",
        "Q2 图表审批通过：只入文图1和图3，图2改为表格或附录。",
        "```",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def main() -> None:
    paths = [
        draw_group_timing(),
        draw_bootstrap_stability(),
        draw_model_empirical_tstar(),
    ]
    sheet = draw_contact_sheet(paths)
    manifest = APPROVAL_DIR / "q2_final_figures_manifest.csv"
    pd.DataFrame(
        [
            {"figure_id": f"Q2-FIG-{i:03d}", "path": str(path.relative_to(ROOT)), "kind": "真实数据图"}
            for i, path in enumerate(paths, start=1)
        ]
        + [{"figure_id": "Q2-FIG-SHEET", "path": str(sheet.relative_to(ROOT)), "kind": "审批总览"}]
    ).to_csv(manifest, index=False)
    approval = write_approval_brief(paths, sheet, manifest)
    print("Generated Q2 final figure candidates:")
    for path in paths:
        print(f"- {path.relative_to(ROOT)}")
    print(f"- {sheet.relative_to(ROOT)}")
    print(f"- {manifest.relative_to(ROOT)}")
    print(f"- {approval.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
