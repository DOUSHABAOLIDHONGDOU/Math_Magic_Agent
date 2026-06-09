"""
Generate final Chinese figures for Q1 from reviewed Scheme B result tables.

The script only redraws reproducible result figures. It does not refit the
model or change any approved modeling result.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "06_results" / "Q1" / "tables"
PAPER_FIG_DIR = ROOT / "07_paper" / "figures"
APPROVAL_DIR = ROOT / "03_methods" / "Q1"
MPL_CACHE_DIR = ROOT / ".cache" / "matplotlib"

PAPER_FIG_DIR.mkdir(parents=True, exist_ok=True)
APPROVAL_DIR.mkdir(parents=True, exist_ok=True)
MPL_CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE_DIR))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import FuncFormatter
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
    "yellow": "#d5a638",
    "fill_blue": "#b9d7ea",
    "fill_green": "#bfe1d2",
}


def pct_fmt(x: float, _pos: int | None = None) -> str:
    return f"{x * 100:.1f}%"


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


def draw_gestation_effect() -> Path:
    df = pd.read_csv(TABLE_DIR / "scheme_B_partial_gestation.csv")
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.plot(df["gestation_week"], df["predicted_Y_conc"], color=COLORS["green"], linewidth=2.3, label="样条岭回归预测")
    ax.fill_between(
        df["gestation_week"],
        df["ci_lo"],
        df["ci_hi"],
        color=COLORS["fill_green"],
        alpha=0.75,
        label="95% Bootstrap 置信区间",
    )
    ax.axhline(0.04, color=COLORS["orange"], linewidth=1.2, linestyle="--", label="4% 临床参考线")
    ax.set_title("孕周对男胎 Y 染色体浓度的非线性影响")
    ax.set_xlabel("检测孕周/周")
    ax.set_ylabel("预测 Y 染色体浓度")
    ax.yaxis.set_major_formatter(FuncFormatter(pct_fmt))
    style_axis(ax)
    ax.legend(loc="best", frameon=True, facecolor="white", edgecolor="#c8d0cc")
    ax.text(
        0.02,
        0.04,
        "条件：BMI 和测序质控变量取样本中位或均值",
        transform=ax.transAxes,
        color="#5d6864",
        fontsize=8.5,
    )
    return save(fig, "q1_fig1_gestation_effect.png")


def draw_bmi_effect() -> Path:
    df = pd.read_csv(TABLE_DIR / "scheme_B_partial_bmi.csv")
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    ax.plot(df["bmi"], df["predicted_Y_conc"], color=COLORS["blue"], linewidth=2.3, label="样条岭回归预测")
    ax.fill_between(
        df["bmi"],
        df["ci_lo"],
        df["ci_hi"],
        color=COLORS["fill_blue"],
        alpha=0.78,
        label="95% Bootstrap 置信区间",
    )
    ax.axhline(0.04, color=COLORS["orange"], linewidth=1.2, linestyle="--", label="4% 临床参考线")
    ax.set_title("BMI 对男胎 Y 染色体浓度的非线性影响")
    ax.set_xlabel("孕妇 BMI")
    ax.set_ylabel("预测 Y 染色体浓度")
    ax.yaxis.set_major_formatter(FuncFormatter(pct_fmt))
    style_axis(ax)
    ax.legend(loc="best", frameon=True, facecolor="white", edgecolor="#c8d0cc")
    ax.text(
        0.02,
        0.04,
        "条件：孕周和测序质控变量取样本中位或均值；低端区间下界按浓度非负约束截断",
        transform=ax.transAxes,
        color="#5d6864",
        fontsize=8.2,
    )
    return save(fig, "q1_fig2_bmi_effect.png")


def draw_surface_heatmap() -> Path:
    df = pd.read_csv(TABLE_DIR / "scheme_B_heatmap_grid.csv")
    pivot = df.pivot(index="bmi", columns="gestation_week", values="predicted_Y_conc").sort_index()
    x = pivot.columns.to_numpy(dtype=float)
    y = pivot.index.to_numpy(dtype=float)
    z = pivot.to_numpy(dtype=float)

    fig, ax = plt.subplots(figsize=(7.2, 4.8))
    levels = np.linspace(np.nanmin(z), np.nanmax(z), 18)
    cf = ax.contourf(x, y, z, levels=levels, cmap="YlGnBu")
    contour = ax.contour(x, y, z, levels=[0.04], colors=[COLORS["red"]], linewidths=1.5)
    ax.clabel(contour, fmt={0.04: "4% 等值线"}, inline=True, fontsize=8)
    cbar = fig.colorbar(cf, ax=ax, pad=0.02)
    cbar.ax.yaxis.set_major_formatter(FuncFormatter(pct_fmt))
    cbar.set_label("预测 Y 染色体浓度")
    ax.set_title("孕周-BMI 联合作用下的 Y 染色体浓度预测面")
    ax.set_xlabel("检测孕周/周")
    ax.set_ylabel("孕妇 BMI")
    style_axis(ax)
    ax.grid(False)
    return save(fig, "q1_fig3_gestation_bmi_surface.png")


def draw_spline_sensitivity() -> Path:
    cv = pd.read_csv(TABLE_DIR / "scheme_B_cv_comparison.csv")
    cv["degree"] = pd.to_numeric(cv["degree"])
    cv["spline_cv_rmse_mean"] = pd.to_numeric(cv["spline_cv_rmse_mean"])
    cv["spline_cv_rmse_std"] = pd.to_numeric(cv["spline_cv_rmse_std"])
    best = cv.loc[cv["spline_cv_rmse_mean"].idxmin()]

    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    ax.plot(cv["degree"], cv["spline_cv_rmse_mean"], color=COLORS["purple"], marker="o", linewidth=2.1)
    ax.fill_between(
        cv["degree"],
        cv["spline_cv_rmse_mean"] - cv["spline_cv_rmse_std"],
        cv["spline_cv_rmse_mean"] + cv["spline_cv_rmse_std"],
        color="#d8cfe8",
        alpha=0.75,
        label="折间标准差",
    )
    ax.scatter([best["degree"]], [best["spline_cv_rmse_mean"]], s=55, color=COLORS["orange"], zorder=4, label="最优阶数")
    ax.annotate(
        f"最优：{int(best['degree'])} 阶",
        xy=(best["degree"], best["spline_cv_rmse_mean"]),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        fontsize=8.5,
        color=COLORS["ink"],
    )
    ax.set_title("样条阶数对交叉验证误差的影响")
    ax.set_xlabel("样条阶数")
    ax.set_ylabel("CV-RMSE")
    ax.set_xticks(cv["degree"].astype(int))
    y_min = cv["spline_cv_rmse_mean"].min()
    y_max = cv["spline_cv_rmse_mean"].max()
    pad = max((y_max - y_min) * 0.45, 0.00001)
    ax.set_ylim(y_min - pad, y_max + pad)
    style_axis(ax)
    ax.legend(loc="best", frameon=True, facecolor="white", edgecolor="#c8d0cc")
    return save(fig, "q1_fig4_spline_sensitivity.png")


def draw_model_flow() -> Path:
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    boxes = [
        (0.06, 0.56, 0.16, 0.22, "男胎检测数据\n孕周、BMI、质控"),
        (0.28, 0.56, 0.16, 0.22, "数据清洗\n10-25 周、浓度非负"),
        (0.50, 0.56, 0.16, 0.22, "样条特征\n孕周、BMI、交互项"),
        (0.72, 0.56, 0.16, 0.22, "GroupKFold\n按孕妇分组验证"),
        (0.28, 0.16, 0.16, 0.22, "岭回归拟合\n内层选择 alpha"),
        (0.50, 0.16, 0.16, 0.22, "Bootstrap\n置信区间估计"),
        (0.72, 0.16, 0.16, 0.22, "关系解释\n敏感性与误差分析"),
    ]
    box_color = "#f4f7f5"
    edge_colors = [COLORS["green"], COLORS["green"], COLORS["blue"], COLORS["blue"], COLORS["purple"], COLORS["orange"], COLORS["red"]]
    centers = []
    for (x, y, w, h, text), edge in zip(boxes, edge_colors):
        patch = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.018,rounding_size=0.025",
            linewidth=1.5,
            edgecolor=edge,
            facecolor=box_color,
        )
        ax.add_patch(patch)
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9, color=COLORS["ink"], linespacing=1.35)
        centers.append((x + w / 2, y + h / 2))

    arrows = [(0, 1), (1, 2), (2, 3), (3, 4), (4, 5), (5, 6)]
    for i, j in arrows:
        x1, y1 = centers[i]
        x2, y2 = centers[j]
        arrow = FancyArrowPatch(
            (x1 + 0.09 if y1 == y2 else x1, y1 - 0.13 if y1 > y2 else y1),
            (x2 - 0.09 if y1 == y2 else x2, y2 + 0.13 if y1 > y2 else y2),
            arrowstyle="-|>",
            mutation_scale=13,
            linewidth=1.3,
            color="#64716d",
            connectionstyle="arc3,rad=0.0",
        )
        ax.add_patch(arrow)

    ax.text(0.06, 0.92, "Q1 样条岭回归建模流程", fontsize=13, weight="bold", color=COLORS["ink"])
    ax.text(0.06, 0.86, "流程图仅说明可复现建模步骤，不包含虚构数值。", fontsize=8.5, color="#66736f")
    return save(fig, "q1_fig5_model_flow.png")


def draw_contact_sheet(paths: list[Path]) -> Path:
    n = len(paths)
    cols = 2
    rows = math.ceil(n / cols)
    fig, axes = plt.subplots(rows, cols, figsize=(10, rows * 3.4))
    axes_arr = np.atleast_1d(axes).ravel()
    titles = [
        "图1 孕周效应",
        "图2 BMI 效应",
        "图3 孕周-BMI 预测面",
        "图4 样条阶数敏感性",
        "图5 建模流程",
    ]
    for ax, path, title in zip(axes_arr, paths, titles):
        img = plt.imread(path)
        ax.imshow(img)
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    for ax in axes_arr[n:]:
        ax.axis("off")
    fig.suptitle("Q1 论文候选图审批总览", y=0.995, fontsize=14, color=COLORS["ink"])
    out = APPROVAL_DIR / "q1_figure_approval_sheet.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white", dpi=220)
    plt.close(fig)
    return out


def main() -> None:
    paths = [
        draw_gestation_effect(),
        draw_bmi_effect(),
        draw_surface_heatmap(),
        draw_spline_sensitivity(),
        draw_model_flow(),
    ]
    sheet = draw_contact_sheet(paths)
    manifest = APPROVAL_DIR / "q1_final_figures_manifest.csv"
    pd.DataFrame(
        [
            {"figure_id": f"Q1-FIG-{i:03d}", "path": str(path.relative_to(ROOT)), "kind": "真实数据图" if i <= 4 else "流程图"}
            for i, path in enumerate(paths, start=1)
        ]
        + [{"figure_id": "Q1-FIG-SHEET", "path": str(sheet.relative_to(ROOT)), "kind": "审批总览"}]
    ).to_csv(manifest, index=False)
    print("Generated Q1 final figures:")
    for path in paths:
        print(f"- {path.relative_to(ROOT)}")
    print(f"- {sheet.relative_to(ROOT)}")
    print(f"- {manifest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
