import json
from pathlib import Path

import matplotlib

matplotlib.rcParams["font.sans-serif"] = [
    "Microsoft YaHei",
    "SimHei",
    "Arial Unicode MS",
    "DejaVu Sans",
]
matplotlib.rcParams["axes.unicode_minus"] = False
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RES = ROOT / "results"


def save(fig, name: str):
    fig.tight_layout()
    fig.savefig(RES / name, dpi=170)
    plt.close(fig)
    print("saved", name)


def main() -> None:
    report = json.loads((RES / "train_report.json").read_text(encoding="utf-8"))
    pred = pd.read_csv(RES / "test_predictions.csv")
    fi = pd.read_csv(RES / "feature_influence_Lasso.csv")
    fails = pd.read_csv(RES / "failure_cases.csv")
    sample = json.loads((RES / "sample_test_report.json").read_text(encoding="utf-8"))
    ablation = pd.read_csv(RES / "ablation.csv") if (RES / "ablation.csv").exists() else None

    # 1 MAE
    names = ["Linear", "Ridge", "Lasso", "基线\n单价×面积"]
    maes = [
        report["models"][n]["test"]["MAE"]
        for n in ["LinearRegression", "Ridge", "Lasso"]
    ] + [report["baseline"]["test"]["MAE"]]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    bars = ax.bar(names, maes, color=["#4C78A8", "#F58518", "#54A24B", "#E45756"])
    ax.set_ylabel("测试集 MAE（元/月）")
    ax.set_title("图：租金预测误差对照（MAE，越低越好）")
    for b, v in zip(bars, maes):
        ax.text(b.get_x() + b.get_width() / 2, v + 25, f"{v:.0f}", ha="center")
    ax.set_ylim(0, max(maes) * 1.18)
    save(fig, "fig_mae_cn.png")

    # 2 R2 + MAPE dual
    metrics = ["R2", "MAPE_%"]
    model_names = ["Linear", "Ridge", "Lasso", "基线"]
    keys = ["LinearRegression", "Ridge", "Lasso"]
    r2s = [report["models"][k]["test"]["R2"] for k in keys] + [report["baseline"]["test"]["R2"]]
    mapes = [report["models"][k]["test"]["MAPE_%"] for k in keys] + [
        report["baseline"]["test"]["MAPE_%"]
    ]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.2))
    axes[0].bar(model_names, r2s, color="#4C78A8")
    axes[0].set_title("测试集 R²（越高越好）")
    axes[0].set_ylim(0, 1)
    for i, v in enumerate(r2s):
        axes[0].text(i, v + 0.02, f"{v:.3f}", ha="center", fontsize=9)
    axes[1].bar(model_names, mapes, color="#F58518")
    axes[1].set_title("测试集 MAPE%（越低越好）")
    for i, v in enumerate(mapes):
        axes[1].text(i, v + 0.8, f"{v:.1f}", ha="center", fontsize=9)
    save(fig, "fig_r2_mape_cn.png")

    # 3 pred vs true
    fig, ax = plt.subplots(figsize=(5.8, 5.8))
    ax.scatter(pred["price"], pred["pred_price"], s=10, alpha=0.35, c="#0f766e")
    lim = max(pred["price"].max(), pred["pred_price"].max())
    ax.plot([0, lim], [0, lim], "r--", lw=1)
    ax.set_xlabel("挂牌价（元/月）")
    ax.set_ylabel("预测公允价（元/月）")
    ax.set_title("测试集：预测值 vs 挂牌价")
    save(fig, "fig_pred_vs_true_cn.png")

    # 4 residual hist
    resid = pred["pred_price"] - pred["price"]
    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.hist(resid, bins=40, color="#4C78A8", edgecolor="white")
    ax.axvline(0, color="red", ls="--", lw=1)
    ax.set_xlabel("残差 = 预测价 - 挂牌价（元）")
    ax.set_ylabel("样本数")
    ax.set_title("测试集残差分布")
    save(fig, "fig_residual_cn.png")

    # 5 error by rooms
    tmp = pred.copy()
    tmp["abs_err"] = (tmp["pred_price"] - tmp["price"]).abs()
    g = tmp.groupby("rooms")["abs_err"].mean().sort_index()
    g = g[g.index <= 5]
    fig, ax = plt.subplots(figsize=(7, 4.3))
    ax.bar([str(int(i)) + "室" for i in g.index], g.values, color="#54A24B")
    ax.set_ylabel("平均绝对误差 MAE（元）")
    ax.set_title("不同居室的预测误差")
    save(fig, "fig_error_by_rooms_cn.png")

    # 6 error by district top
    g2 = tmp.groupby("district")["abs_err"].mean().sort_values(ascending=False).head(8)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.barh(g2.index[::-1], g2.values[::-1], color="#E45756")
    ax.set_xlabel("平均绝对误差（元）")
    ax.set_title("平均误差较高的行政区（Top8）")
    save(fig, "fig_error_by_district_cn.png")

    # 7 feature
    top = fi.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = np.where(top["coefficient"] >= 0, "#0f766e", "#b45309")
    ax.barh(top["feature"], top["coefficient"], color=colors)
    ax.set_xlabel("系数")
    ax.set_title("Lasso 特征影响 Top10（比较特征影响）")
    save(fig, "fig_feature_cn.png")

    # 8 workflow
    fig, ax = plt.subplots(figsize=(10.5, 3.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    steps = [
        "①任务入口\n预算/区域/面积",
        "②数据工具\n查询硬筛选",
        "③ML组件\n预测公允价",
        "④建议流程\n偏贵/合理/划算",
        "⑤安全处理\n人工复核",
    ]
    xs = [1, 3, 5, 7, 9]
    for i, (x, s) in enumerate(zip(xs, steps)):
        ax.add_patch(
            plt.Rectangle((x - 0.9, 1.0), 1.8, 1.25, facecolor="#e8f5f3", edgecolor="#12263a", lw=1.5)
        )
        ax.text(x, 1.62, s, ha="center", va="center", fontsize=9)
        if i < len(xs) - 1:
            ax.annotate(
                "",
                xy=(xs[i + 1] - 0.95, 1.62),
                xytext=(x + 0.95, 1.62),
                arrowprops=dict(arrowstyle="->", color="#12263a", lw=1.4),
            )
    ax.set_title("Agent 端到端流程（对应文档任务流程要求）", fontsize=13, pad=10)
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
    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.bar(list(meta_dist.keys()), list(meta_dist.values()), color="#4C78A8")
    ax.set_ylabel("房源数量")
    ax.set_title("清洗后房源行政区分布（数据工具侧）")
    plt.xticks(rotation=30)
    save(fig, "fig_district_cn.png")

    # 10 split pie
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    sizes = [report["n_train_fit"], report["n_valid"], report["n_test"]]
    ax.pie(
        sizes,
        labels=[f"训练拟合\n{sizes[0]}", f"验证\n{sizes[1]}", f"测试\n{sizes[2]}"],
        autopct="%1.1f%%",
        colors=["#4C78A8", "#F58518", "#54A24B"],
        startangle=90,
    )
    ax.set_title("数据集划分（随机种子42）")
    save(fig, "fig_split_cn.png")

    # 11 failure cases table-like bar
    f = fails.copy()
    f["short"] = f["title"].astype(str).str.slice(0, 10) + "…"
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.barh(f["short"][::-1], f["pct_error"][::-1], color="#E45756")
    ax.set_xlabel("百分比误差 %")
    ax.set_title("失败/高误差案例（测试集 pct_error Top）")
    save(fig, "fig_failure_cn.png")

    # 12 sample tests pass
    fig, ax = plt.subplots(figsize=(8, 4.2))
    rows = sample["rows"]
    labels = [r["id"] for r in rows]
    vals = [1 if r["passed"] else 0 for r in rows]
    ax.bar(labels, vals, color=["#54A24B" if v else "#E45756" for v in vals])
    ax.set_ylim(0, 1.3)
    ax.set_ylabel("是否通过")
    ax.set_title(f"Agent 可复现样例测试（通过率 {sample['pass_rate']*100:.0f}%）")
    plt.xticks(rotation=25, ha="right")
    save(fig, "fig_sample_tests_cn.png")

    # 13 ablation if available
    if ablation is not None and len(ablation):
        fig, ax = plt.subplots(figsize=(8, 4.5))
        x = np.arange(len(ablation))
        ax.plot(x, ablation.get("with_model_matched", ablation.iloc[:, 1]), "o-", label="启用模型")
        if "without_model_matched" in ablation.columns:
            ax.plot(x, ablation["without_model_matched"], "s--", label="关闭模型(消融)")
        ax.set_xticks(x)
        ax.set_xticklabels(ablation["task"].astype(str).str.slice(0, 12), rotation=25, ha="right")
        ax.set_ylabel("匹配房源数")
        ax.set_title("消融对照：启用/关闭模型后的检索规模")
        ax.legend()
        save(fig, "fig_ablation_cn.png")

    # 14 system architecture boxes
    fig, ax = plt.subplots(figsize=(9.5, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    boxes = [
        (3.5, 4.6, 3, 1, "用户任务入口\n(Streamlit 网页)"),
        (0.5, 2.6, 2.8, 1.2, "RentAgent 编排\n校验/步骤/安全"),
        (3.6, 2.6, 2.8, 1.2, "RentFilterSkill\n筛选+建议+排序"),
        (6.7, 2.6, 2.8, 1.2, "ML 模型\nLasso/Ridge Pipeline"),
        (2.0, 0.7, 2.8, 1.1, "数据工具\n上海房源CSV"),
        (5.5, 0.7, 2.8, 1.1, "人工复核\n高偏差/无匹配"),
    ]
    for x, y, w, h, t in boxes:
        ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="#f7fbfa", edgecolor="#12263a", lw=1.4))
        ax.text(x + w / 2, y + h / 2, t, ha="center", va="center", fontsize=10)
    ax.annotate("", xy=(5, 4.6), xytext=(5, 3.8), arrowprops=dict(arrowstyle="->", lw=1.3))
    ax.annotate("", xy=(1.9, 3.8), xytext=(4.2, 4.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(8.1, 3.8), xytext=(5.8, 4.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(3.4, 1.8), xytext=(3.4, 2.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.annotate("", xy=(6.9, 1.8), xytext=(6.9, 2.6), arrowprops=dict(arrowstyle="->", lw=1.0))
    ax.set_title("系统设计：模型 / 工具 / 数据 / 人工确认 的组织关系")
    save(fig, "fig_architecture_cn.png")

    print("all figures done")


if __name__ == "__main__":
    main()
