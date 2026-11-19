"""房源筛选 + 公允价建议。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd

NUM_FEATURES = ["area", "rooms", "halls", "has_metro", "lng", "lat"]
CAT_FEATURES = ["orient", "district"]


@dataclass
class SkillResult:
    ok: bool
    message: str
    need_human_review: bool = False
    steps: list[str] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)


class RentFilterSkill:
    name = "rent_filter_skill"
    version = "1.0.0"

    def __init__(self, model, fair_band: float = 0.15, review_band: float = 0.30, top_k: int = 5):
        self.model = model
        self.fair_band = fair_band
        self.review_band = review_band
        self.top_k = top_k

    def _label(self, listed: float, pred: float) -> tuple[str, float, bool]:
        if pred <= 0:
            return "无法估价", 0.0, True
        ratio = (listed - pred) / pred
        if abs(ratio) >= self.review_band:
            tag = "显著偏贵" if ratio > 0 else "显著偏低(需核验真伪/条件遗漏)"
            return tag, ratio, True
        if ratio > self.fair_band:
            return "偏贵", ratio, False
        if ratio < -self.fair_band:
            return "偏便宜", ratio, False
        return "价格合理", ratio, False

    def predict_one(self, features: dict[str, Any]) -> float:
        row = pd.DataFrame([features])[NUM_FEATURES + CAT_FEATURES]
        return float(self.model.predict(row)[0])

    def run(
        self,
        listings: pd.DataFrame,
        *,
        budget: float | None = None,
        district: str | None = None,
        rent_type: str | None = None,
        min_area: float | None = None,
        max_area: float | None = None,
        use_model: bool = True,
    ) -> SkillResult:
        steps = ["解析用户约束", "连接本地房源库", "按硬约束筛选"]
        df = listings.copy()
        if district:
            df = df[df["district"] == district]
        if rent_type:
            df = df[df["rent_type"] == rent_type]
        if min_area is not None:
            df = df[df["area"] >= min_area]
        if max_area is not None:
            df = df[df["area"] <= max_area]
        if budget is not None:
            df = df[df["price"] <= budget * 1.15]

        if df.empty:
            return SkillResult(
                ok=False,
                message="无匹配房源：请放宽预算、区域或面积约束。",
                need_human_review=True,
                steps=steps + ["筛选结果为空 -> 请求用户调整条件或人工协助"],
            )

        if use_model:
            steps.append("调用回归模型预测公允租金")
            X = df[NUM_FEATURES + CAT_FEATURES]
            preds = self.model.predict(X)
            df = df.copy()
            df["pred_price"] = preds
            labels, ratios, reviews = [], [], []
            for listed, pred in zip(df["price"], df["pred_price"]):
                tag, ratio, need = self._label(float(listed), float(pred))
                labels.append(tag)
                ratios.append(ratio)
                reviews.append(need)
            df["advice"] = labels
            df["price_gap_ratio"] = ratios
            df["need_review"] = reviews
            if budget is not None:
                df["within_budget"] = df["price"] <= budget
            else:
                df["within_budget"] = True
            df["score"] = (
                df["within_budget"].astype(int) * 2
                - df["price_gap_ratio"].abs()
                - (df["price"] / (budget if budget else df["price"].median()))
            )
            df = df.sort_values(["within_budget", "score"], ascending=[False, False])
            steps.append("生成建议并对高偏差标记人工复核")
        else:
            steps.append("消融模式：仅规则筛选")
            df = df.sort_values("price")
            df["pred_price"] = np.nan
            df["advice"] = "仅规则筛选(无模型估价)"
            df["price_gap_ratio"] = np.nan
            df["need_review"] = False

        top = df.head(self.top_k)
        items = []
        for _, r in top.iterrows():
            items.append(
                {
                    "title": r.get("title"),
                    "district": r.get("district"),
                    "rent_type": r.get("rent_type"),
                    "area": float(r["area"]),
                    "rooms": int(r["rooms"]),
                    "listed_price": float(r["price"]),
                    "pred_price": None if pd.isna(r["pred_price"]) else round(float(r["pred_price"]), 1),
                    "advice": r["advice"],
                    "price_gap_ratio": None
                    if pd.isna(r["price_gap_ratio"])
                    else round(float(r["price_gap_ratio"]), 3),
                    "need_human_review": bool(r["need_review"]),
                    "address": r.get("address"),
                }
            )

        need_review = any(i["need_human_review"] for i in items)
        msg = f"找到 {len(df)} 套房源，返回 Top-{len(items)}。"
        if need_review:
            msg += " 存在高偏差报价，建议人工确认后再联系房东。"

        return SkillResult(
            ok=True,
            message=msg,
            need_human_review=need_review,
            steps=steps,
            items=items,
            summary={
                "matched": int(len(df)),
                "returned": len(items),
                "budget": budget,
                "district": district,
                "rent_type": rent_type,
                "use_model": use_model,
            },
        )
