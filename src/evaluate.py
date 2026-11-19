"""实验评估：指标、对照/消融、失败案例、任务完成率。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from skills.rent_filter_skill import RentFilterSkill  # noqa: E402

RESULT = ROOT / "results"
MODEL = ROOT / "models" / "best_model.joblib"
DATA = ROOT / "data" / "processed" / "shanghai_listings.csv"


def task_suite(df: pd.DataFrame) -> list[dict]:
    """构造正常查询和边界任务。"""
    districts = df["district"].value_counts().index.tolist()
    tasks = []
    for d in districts[:5]:
        tasks.append(
            {
                "name": f"整租_{d}_预算6500",
                "budget": 6500,
                "district": d,
                "rent_type": "整租",
                "min_area": 30,
                "max_area": 90,
            }
        )
    tasks.append(
        {
            "name": "边界_预算过低",
            "budget": 1200,
            "district": districts[0],
            "rent_type": "整租",
            "min_area": 40,
            "max_area": 80,
        }
    )
    tasks.append(
        {
            "name": "整租_高预算",
            "budget": 15000,
            "district": districts[0],
            "rent_type": "整租",
            "min_area": 50,
            "max_area": 120,
        }
    )
    tasks.append(
        {
            "name": "边界_未知区域",
            "budget": 6000,
            "district": "不存在区",
            "rent_type": "整租",
            "min_area": 30,
            "max_area": 80,
        }
    )
    return tasks


def run_ablation(listings: pd.DataFrame, model) -> dict:
    skill_on = RentFilterSkill(model=model, top_k=5)
    skill_off = RentFilterSkill(model=model, top_k=5)
    tasks = [t for t in task_suite(listings) if not t["name"].startswith("边界_未知")]
    rows = []
    for t in tasks:
        r_on = skill_on.run(
            listings,
            budget=t["budget"],
            district=t["district"],
            rent_type=t["rent_type"],
            min_area=t["min_area"],
            max_area=t["max_area"],
            use_model=True,
        )
        r_off = skill_off.run(
            listings,
            budget=t["budget"],
            district=t["district"],
            rent_type=t["rent_type"],
            min_area=t["min_area"],
            max_area=t["max_area"],
            use_model=False,
        )
        fair_ratio = 0.0
        if r_on.items:
            fair_ratio = np.mean(
                [1.0 if i["advice"] in {"价格合理", "偏便宜"} else 0.0 for i in r_on.items]
            )
        rows.append(
            {
                "task": t["name"],
                "with_model_ok": r_on.ok,
                "without_model_ok": r_off.ok,
                "with_model_matched": r_on.summary.get("matched", 0),
                "without_model_matched": r_off.summary.get("matched", 0),
                "fair_or_cheap_ratio_top": fair_ratio,
                "review_flagged": r_on.need_human_review,
            }
        )
    return {"ablation_rows": rows}


def failure_cases(pred_csv: Path) -> list[dict]:
    df = pd.read_csv(pred_csv)
    worst = df.sort_values("pct_error", ascending=False).head(8)
    cases = []
    for _, r in worst.iterrows():
        cases.append(
            {
                "title": r.get("title"),
                "district": r.get("district"),
                "rent_type": r.get("rent_type"),
                "area": float(r["area"]),
                "price": float(r["price"]),
                "pred_price": float(r["pred_price"]),
                "pct_error": float(r["pct_error"]),
                "possible_reason": "特征不足/区域细分粗糙/特殊装修或楼盘溢价未建模",
            }
        )
    return cases


def main() -> None:
    RESULT.mkdir(parents=True, exist_ok=True)
    train_report = json.loads((RESULT / "train_report.json").read_text(encoding="utf-8"))
    listings = pd.read_csv(DATA)
    model = joblib.load(MODEL)
    skill = RentFilterSkill(model=model, top_k=5)

    tasks = task_suite(listings)
    task_results = []
    success = 0
    for t in tasks:
        r = skill.run(
            listings,
            budget=t["budget"],
            district=t["district"],
            rent_type=t["rent_type"],
            min_area=t["min_area"],
            max_area=t["max_area"],
            use_model=True,
        )
        if t["name"].startswith("边界_"):
            ok = (not r.ok) or r.need_human_review
        else:
            ok = r.ok and len(r.items) > 0
        success += int(ok)
        task_results.append({"task": t["name"], "ok": ok, "message": r.message})

    ablation = run_ablation(listings, model)
    fails = failure_cases(RESULT / "test_predictions.csv")

    out = {
        "model_metrics": train_report,
        "task_completion_rate": success / len(tasks),
        "task_results": task_results,
        "ablation": ablation,
        "failure_cases": fails,
        "notes": [
            "定量指标以测试集 MAE/RMSE/R2/MAPE 为主。",
            "消融：关闭回归模型后仅能规则筛选，无法给出偏贵/合理判断。",
            "失败案例取测试集百分比误差最大的样本，用于误差分析。",
        ],
    }
    (RESULT / "evaluation_report.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    pd.DataFrame(task_results).to_csv(RESULT / "task_results.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(ablation["ablation_rows"]).to_csv(
        RESULT / "ablation.csv", index=False, encoding="utf-8-sig"
    )
    pd.DataFrame(fails).to_csv(RESULT / "failure_cases.csv", index=False, encoding="utf-8-sig")
    print(json.dumps({
        "task_completion_rate": out["task_completion_rate"],
        "selected_model": train_report.get("selected_model"),
        "test_metrics": train_report["models"][train_report["selected_model"]]["test"],
        "baseline_test": train_report["baseline"]["test"],
        "n_failure_cases": len(fails),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
