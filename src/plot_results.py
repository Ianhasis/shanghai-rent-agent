"""生成对照实验图。"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RESULT = ROOT / "results"


def main() -> None:
    report = json.loads((RESULT / "train_report.json").read_text(encoding="utf-8"))
    names = list(report["models"].keys()) + ["Baseline"]
    maes = [report["models"][n]["test"]["MAE"] for n in report["models"]] + [
        report["baseline"]["test"]["MAE"]
    ]
    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(names, maes, color=["#4C78A8", "#F58518", "#54A24B", "#E45756"])
    plt.ylabel("Test MAE (CNY/month)")
    plt.title("Shanghai Rent Prediction: Model vs Baseline")
    for b, v in zip(bars, maes):
        plt.text(b.get_x() + b.get_width() / 2, v + 5, f"{v:.0f}", ha="center", va="bottom", fontsize=9)
    plt.tight_layout()
    out = RESULT / "mae_comparison.png"
    plt.savefig(out, dpi=150)
    plt.close()

    pred = pd.read_csv(RESULT / "test_predictions.csv")
    plt.figure(figsize=(5.5, 5.5))
    plt.scatter(pred["price"], pred["pred_price"], s=12, alpha=0.45)
    lim = max(pred["price"].max(), pred["pred_price"].max())
    plt.plot([0, lim], [0, lim], "r--", linewidth=1)
    plt.xlabel("Listed price")
    plt.ylabel("Predicted fair rent")
    plt.title("Test set: predicted vs listed")
    plt.tight_layout()
    out2 = RESULT / "pred_vs_true.png"
    plt.savefig(out2, dpi=150)
    plt.close()
    print(f"saved {out}")
    print(f"saved {out2}")


if __name__ == "__main__":
    main()
