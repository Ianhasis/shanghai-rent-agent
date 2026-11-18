"""训练 Linear / Ridge / Lasso，并保存最优模型与评估结果。"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "shanghai_listings.csv"
MODEL_DIR = ROOT / "models"
RESULT_DIR = ROOT / "results"

NUM_FEATURES = ["area", "rooms", "halls", "has_metro", "lng", "lat"]
CAT_FEATURES = ["orient", "district"]
TARGET = "price"
SEED = 42


def metrics(y_true, y_pred) -> dict:
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))
    mape = float(np.mean(np.abs((y_true - y_pred) / np.clip(np.abs(y_true), 1, None))) * 100)
    return {"MAE": mae, "RMSE": rmse, "R2": r2, "MAPE_%": mape}


def build_preprocessor() -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            ("num", StandardScaler(), NUM_FEATURES),
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CAT_FEATURES,
            ),
        ]
    )


def baseline_area_unit_price(train_df: pd.DataFrame, test_df: pd.DataFrame) -> np.ndarray:
    """基线：同租类型的均单价 × 面积。"""
    unit = train_df.groupby("rent_type")["price_per_sqm"].median()
    fallback = float(train_df["price_per_sqm"].median())
    pred = test_df.apply(
        lambda r: r["area"] * float(unit.get(r["rent_type"], fallback)),
        axis=1,
    )
    return pred.to_numpy()


def feature_influence(pipe: Pipeline, model_name: str) -> list[dict]:
    pre: ColumnTransformer = pipe.named_steps["pre"]
    model = pipe.named_steps["model"]
    num_names = NUM_FEATURES
    cat_names = list(pre.named_transformers_["cat"].get_feature_names_out(CAT_FEATURES))
    names = num_names + cat_names
    coefs = model.coef_
    rows = [
        {"feature": n, "coefficient": float(c), "abs_coef": float(abs(c))}
        for n, c in zip(names, coefs)
    ]
    rows.sort(key=lambda x: x["abs_coef"], reverse=True)
    for r in rows:
        r["model"] = model_name
    return rows


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA)
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=SEED)
    # 再从 train 划出 valid 仅用于选模型（报告可说明）
    fit_df, valid_df = train_test_split(train_df, test_size=0.2, random_state=SEED)

    X_fit = fit_df[NUM_FEATURES + CAT_FEATURES]
    y_fit = fit_df[TARGET]
    X_valid = valid_df[NUM_FEATURES + CAT_FEATURES]
    y_valid = valid_df[TARGET]
    X_test = test_df[NUM_FEATURES + CAT_FEATURES]
    y_test = test_df[TARGET]

    candidates = {
        "LinearRegression": LinearRegression(),
        "Ridge": Ridge(alpha=1.0, random_state=SEED),
        "Lasso": Lasso(alpha=1.0, max_iter=20000, random_state=SEED),
    }

    report = {
        "n_total": int(len(df)),
        "n_train_fit": int(len(fit_df)),
        "n_valid": int(len(valid_df)),
        "n_test": int(len(test_df)),
        "features_num": NUM_FEATURES,
        "features_cat": CAT_FEATURES,
        "models": {},
        "baseline": {},
        "selected_model": None,
    }

    best_name = None
    best_mae = float("inf")
    best_pipe = None

    for name, model in candidates.items():
        pipe = Pipeline([("pre", build_preprocessor()), ("model", model)])
        pipe.fit(X_fit, y_fit)
        valid_pred = pipe.predict(X_valid)
        test_pred = pipe.predict(X_test)
        m_valid = metrics(y_valid.to_numpy(), valid_pred)
        m_test = metrics(y_test.to_numpy(), test_pred)
        report["models"][name] = {"valid": m_valid, "test": m_test}
        joblib.dump(pipe, MODEL_DIR / f"{name}.joblib")
        infl = feature_influence(pipe, name)
        pd.DataFrame(infl).to_csv(RESULT_DIR / f"feature_influence_{name}.csv", index=False, encoding="utf-8-sig")
        if m_valid["MAE"] < best_mae:
            best_mae = m_valid["MAE"]
            best_name = name
            best_pipe = pipe

    # 基线
    base_pred = baseline_area_unit_price(fit_df, test_df)
    report["baseline"] = {
        "name": "median_unit_price_by_rent_type * area",
        "test": metrics(y_test.to_numpy(), base_pred),
    }

    report["selected_model"] = best_name
    joblib.dump(best_pipe, MODEL_DIR / "best_model.joblib")
    # 保存划分后的测试集，便于评估与 Agent 演示复现
    test_df.to_csv(RESULT_DIR / "test_listings.csv", index=False, encoding="utf-8-sig")
    fit_df.to_csv(RESULT_DIR / "fit_listings.csv", index=False, encoding="utf-8-sig")
    (RESULT_DIR / "train_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 测试集预测明细（用最优模型）
    test_out = test_df.copy()
    test_out["pred_price"] = best_pipe.predict(X_test)
    test_out["abs_error"] = (test_out["pred_price"] - test_out["price"]).abs()
    test_out["pct_error"] = test_out["abs_error"] / test_out["price"].clip(lower=1) * 100
    test_out.to_csv(RESULT_DIR / "test_predictions.csv", index=False, encoding="utf-8-sig")

    print(json.dumps(report, ensure_ascii=False, indent=2))
    print(f"selected={best_name} saved -> {MODEL_DIR / 'best_model.joblib'}")


if __name__ == "__main__":
    main()
