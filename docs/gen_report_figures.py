"""生成报告用实验图（精简学术风格）。运行：python docs/gen_report_figures.py"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.rcParams.update(
    {
        "font.sans-serif": ["Microsoft YaHei", "SimHei", "Arial Unicode MS", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 160,
        "savefig.dpi": 200,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
    }
)
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"

C_BLUE = "#2F6F8F"
C_ORANGE = "#C56A27"
C_GREEN = "#3F7D5A"
C_RED = "#B24C4C"
C_TEAL = "#0F766E"
C_GRAY = "#6B7280"
PAL = [C_BLUE, C_ORANGE, C_GREEN, C_RED]


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(RES / name, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("saved", name)


def style_ax(ax):
    ax.set_facecolor("#FBFCFD")


def main() -> None:
    RES.mkdir(parents=True, exist_ok=True)
    report = json.loads((RES / "train_report.json").read_text(encoding="utf-8"))
    pred = pd.read_csv(RES / "test_predictions.csv")
    fi = pd.read_csv(RES / "feature_influence_Lasso.csv")
    fails = pd.read_csv(RES / "failure_cases.csv")
    sample = json.loads((RES / "sample_test_report.json").read_text(encoding="utf-8"))
    ablation = pd.read_csv(RES / "ablation.csv") if (RES / "ablation.csv").exists() else None

    keys = ["LinearRegression", "Ridge", "Lasso"]
    short = ["Linear", "Ridge", "Lasso", "基线"]
    maes = [report["models"][k]["test"]["MAE"] for k in keys] + [report["baseline"]["test"]["MAE"]]
    r2s = [report["models"][k]["test"]["R2"] for k in keys] + [report["baseline"]["test"]["R2"]]
    mapes = [report["models"][k]["test"]["MAPE_%"] for k in keys] + [
        report["baseline"]["test"]["MAPE_%"]
    ]

    # 1 MAE
    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    style_ax(ax)
    bars = ax.bar(short, maes, color=PAL, width=0.68, edgecolor="white", linewidth=0.8)
    ax.set_ylabel("测试集 MAE（元/月）")
    ax.set_title("租金预测误差对照（MAE，越低越好）")
    for b, v in zip(bars, maes):
        ax.text(b.get_x() + b.get_width() / 2, v + 35, f"{v:.0f}", ha="center", fontsize=9)
    ax.set_ylim(0, max(maes) * 1.18)
    save(fig, "fig_mae_cn.png")

    # 2 R2 + MAPE
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 4.2))
    for ax in axes:
        style_ax(ax)
    axes[0].bar(short, r2s, color=C_BLUE, width=0.68, edgecolor="white")
    axes[0].set_title("测试集 R²（越高越好）")
    axes[0].set_ylim(0, 1)
    for i, v in enumerate(r2s):
        axes[0].text(i, v + 0.02, f"{v:.3f}", ha="center", fontsize=9)
    axes[1].bar(short, mapes, color=C_ORANGE, width=0.68, edgecolor="white")
    axes[1].set_title("测试集 MAPE%（越低越好）")
    for i, v in enumerate(mapes):
        axes[1].text(i, v + 0.8, f"{v:.1f}", ha="center", fontsize=9)
    save(fig, "fig_r2_mape_cn.png")

    # 3 pred vs true
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    style_ax(ax)
    hb = ax.hexbin(
        pred["price"],
        pred["pred_price"],
        gridsize=35,
        cmap="YlGnBu",
        mincnt=1,
        linewidths=0.2,
    )
    lim = float(max(pred["price"].quantile(0.995), pred["pred_price"].quantile(0.995)))
    ax.plot([0, lim], [0, lim], color=C_RED, ls="--", lw=1.2, label="理想线 y=x")
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_xlabel("挂牌价（元/月）")
    ax.set_ylabel("预测公允价（元/月）")
    ax.set_title("测试集：预测值 vs 挂牌价")
    ax.legend(frameon=False, loc="upper left")
    cb = fig.colorbar(hb, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("样本密度")
    save(fig, "fig_pred_vs_true_cn.png")

    # 4 residual
    resid = pred["pred_price"] - pred["price"]
    fig, ax = plt.subplots(figsize=(7.6, 4.4))
    style_ax(ax)
    ax.hist(resid, bins=45, color=C_BLUE, edgecolor="white", alpha=0.92)
    ax.axvline(0, color=C_RED, ls="--", lw=1.2)
    ax.set_xlabel("残差 = 预测价 − 挂牌价（元）")
    ax.set_ylabel("样本数")
    ax.set_title("测试集残差分布")
    save(fig, "fig_residual_cn.png")

    # 5 error by rooms
    tmp = pred.copy()
    tmp["abs_err"] = (tmp["pred_price"] - tmp["price"]).abs()
    g = tmp.groupby("rooms")["abs_err"].mean().sort_index()
    g = g[g.index <= 5]
    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    style_ax(ax)
    ax.bar([f"{int(i)}室" for i in g.index], g.values, color=C_GREEN, edgecolor="white", width=0.7)
    ax.set_ylabel("平均绝对误差（元）")
    ax.set_title("不同居室的预测误差")
    save(fig, "fig_error_by_rooms_cn.png")

    # 6 error by district
    g2 = tmp.groupby("district")["abs_err"].mean().sort_values(ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    style_ax(ax)
    ax.barh(g2.index[::-1], g2.values[::-1], color=C_RED, edgecolor="white", height=0.7)
    ax.set_xlabel("平均绝对误差（元）")
    ax.set_title("平均误差较高的行政区（Top8）")
    save(fig, "fig_error_by_district_cn.png")

    # 7 feature
    top = fi.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8.0, 5.0))
    style_ax(ax)
    colors = np.where(top["coefficient"] >= 0, C_TEAL, C_ORANGE)
    ax.barh(top["feature"], top["coefficient"], color=colors, edgecolor="white", height=0.72)
    ax.axvline(0, color=C_GRAY, lw=0.8)
    ax.set_xlabel("系数")
    ax.set_title("Lasso 特征影响 Top10")
    save(fig, "fig_feature_cn.png")

    # 8 workflow
    fig, ax = plt.subplots(figsize=(10.8, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    steps = [
        "①任务入口\n预算/区域/面积",
        "②数据工具\n硬约束筛选",
        "③ML组件\n预测公允价",
        "④建议流程\n偏贵/合理/划算",
        "⑤安全处理\n人工复核",
    ]
    xs = [1, 3, 5, 7, 9]
    for i, (x, s) in enumerate(zip(xs, steps)):
        ax.add_patch(
            plt.Rectangle(
                (x - 0.9, 0.95),
                1.8,
                1.35,
                facecolor="#EEF6F4",
                edgecolor="#1F3347",
                lw=1.4,
                zorder=2,
            )
        )
        ax.text(x, 1.62, s, ha="center", va="center", fontsize=9, zorder=3)
        if i < len(xs) - 1:
            ax.annotate(
                "",
                xy=(xs[i + 1] - 0.95, 1.62),
                xytext=(x + 0.95, 1.62),
                arrowprops=dict(arrowstyle="->", color="#1F3347", lw=1.4),
            )
    ax.set_title("Agent 端到端流程", fontsize=13, pad=8)
    save(fig, "fig_workflow_cn.png")

    # 9 district counts
    meta_dist = {
        "闵行": 3132,
        "宝山": 2851,
        "黄浦": 1623,
        "浦东": 1617,
        "嘉定": 1495,
        "长宁": 1492,
        "青浦": 1332,
        "静安": 1327,
        "松江": 1059,
        "奉贤": 543,
        "徐汇": 523,
        "虹口": 426,
    }
    fig, ax = plt.subplots(figsize=(9.0, 4.5))
    style_ax(ax)
    ax.bar(list(meta_dist.keys()), list(meta_dist.values()), color=C_BLUE, edgecolor="white")
    ax.set_ylabel("房源数量")
    ax.set_title("清洗后房源行政区分布")
    plt.xticks(rotation=28, ha="right")
    save(fig, "fig_district_cn.png")

    # 10 split
    fig, ax = plt.subplots(figsize=(5.3, 5.0))
    sizes = [report["n_train_fit"], report["n_valid"], report["n_test"]]
    ax.pie(
        sizes,
        labels=[f"训练拟合\n{sizes[0]}", f"验证\n{sizes[1]}", f"测试\n{sizes[2]}"],
        autopct="%1.1f%%",
        colors=[C_BLUE, C_ORANGE, C_GREEN],
        startangle=90,
        wedgeprops=dict(width=0.72, edgecolor="white"),
        pctdistance=0.75,
    )
    ax.set_title("数据集划分（随机种子 42）")
    save(fig, "fig_split_cn.png")

    # 11 failure
    f = fails.copy()
    f["short"] = f["title"].astype(str).str.slice(0, 10) + "…"
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    style_ax(ax)
    ax.barh(f["short"][::-1], f["pct_error"][::-1], color=C_RED, edgecolor="white", height=0.7)
    ax.set_xlabel("百分比误差 %")
    ax.set_title("高误差失败案例（测试集 Top）")
    save(fig, "fig_failure_cn.png")

    # 12 sample tests
    fig, ax = plt.subplots(figsize=(8.0, 4.2))
    style_ax(ax)
    rows = sample["rows"]
    labels = [r["id"] for r in rows]
    vals = [1 if r["passed"] else 0 for r in rows]
    ax.bar(labels, vals, color=[C_GREEN if v else C_RED for v in vals], edgecolor="white")
    ax.set_ylim(0, 1.25)
    ax.set_ylabel("是否通过")
    ax.set_title(f"Agent 可复现样例测试（通过率 {sample['pass_rate']*100:.0f}%）")
    plt.xticks(rotation=22, ha="right")
    save(fig, "fig_sample_tests_cn.png")

    # 13 ablation
    if ablation is not None and len(ablation):
        fig, ax = plt.subplots(figsize=(8.2, 4.5))
        style_ax(ax)
        x = np.arange(len(ablation))
        if "with_model_matched" in ablation.columns:
            ax.plot(x, ablation["with_model_matched"], "o-", color=C_TEAL, lw=1.8, label="启用模型")
        if "without_model_matched" in ablation.columns:
            ax.plot(
                x,
                ablation["without_model_matched"],
                "s--",
                color=C_ORANGE,
                lw=1.6,
                label="关闭模型（消融）",
            )
        ax.set_xticks(x)
        ax.set_xticklabels(ablation["task"].astype(str).str.slice(0, 12), rotation=22, ha="right")
        ax.set_ylabel("匹配房源数")
        ax.set_title("消融对照：启用/关闭模型后的检索规模")
        ax.legend(frameon=False)
        save(fig, "fig_ablation_cn.png")

    # 14 architecture
    fig, ax = plt.subplots(figsize=(9.6, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (3.5, 4.6, 3.0, 1.0, "用户任务入口\n(Streamlit 网页)"),
        (0.5, 2.6, 2.8, 1.2, "RentAgent 编排\n校验 / 步骤 / 安全"),
        (3.6, 2.6, 2.8, 1.2, "RentFilterSkill\n筛选 + 建议 + 排序"),
        (6.7, 2.6, 2.8, 1.2, "ML 模型\nLasso Pipeline"),
        (2.0, 0.7, 2.8, 1.1, "数据工具\n上海房源 CSV"),
        (5.5, 0.7, 2.8, 1.1, "人工复核\n高偏差 / 无匹配"),
    ]
    for x, y, w, h, t in boxes:
        ax.add_patch(
            plt.Rectangle(
                (x, y), w, h, facecolor="#F7FBFA", edgecolor="#1F3347", lw=1.35, zorder=2
            )
        )
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=10, zorder=3)
    ax.annotate("", xy=(5, 4.6), xytext=(5, 3.8), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.annotate("", xy=(1.9, 3.8), xytext=(4.2, 4.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(8.1, 3.8), xytext=(5.8, 4.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(3.4, 1.8), xytext=(3.4, 2.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(6.9, 1.8), xytext=(6.9, 2.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.set_title("系统设计：模型 / 工具 / 数据 / 人工确认", fontsize=13, pad=8)
    save(fig, "fig_architecture_cn.png")

    # 15 metrics table-like bar for report appendix visual
    fig, ax = plt.subplots(figsize=(7.8, 4.0))
    style_ax(ax)
    metrics_names = ["MAE↓", "RMSE↓", "MAPE%↓"]
    lasso = [
        report["models"]["Lasso"]["test"]["MAE"] / 1000,
        report["models"]["Lasso"]["test"]["RMSE"] / 1000,
        report["models"]["Lasso"]["test"]["MAPE_%"],
    ]
    base = [
        report["baseline"]["test"]["MAE"] / 1000,
        report["baseline"]["test"]["RMSE"] / 1000,
        report["baseline"]["test"]["MAPE_%"],
    ]
    x = np.arange(len(metrics_names))
    w = 0.36
    ax.bar(x - w / 2, lasso, w, label="Lasso", color=C_TEAL, edgecolor="white")
    ax.bar(x + w / 2, base, w, label="基线", color=C_GRAY, edgecolor="white")
    ax.set_xticks(x)
    ax.set_xticklabels(metrics_names)
    ax.set_ylabel("MAE/RMSE 为千元；MAPE 为 %")
    ax.set_title("Lasso 与基线关键指标对照")
    ax.legend(frameon=False)
    save(fig, "fig_metrics_compare_cn.png")

    print("all figures done")


if __name__ == "__main__":
    main()
