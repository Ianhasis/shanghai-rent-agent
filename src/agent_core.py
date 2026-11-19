"""Agent 编排：校验输入、连数据、调模型、生成建议、异常时提示人工确认。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from skills.rent_filter_skill import RentFilterSkill

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "shanghai_listings.csv"
MODEL = ROOT / "models" / "best_model.joblib"


class StepStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class Step:
    name: str
    purpose: str
    status: StepStatus = StepStatus.PENDING
    detail: str = ""


@dataclass
class AgentOutput:
    ok: bool
    success: bool
    message: str
    need_human_review: bool
    steps: list[Step] = field(default_factory=list)
    items: list[dict[str, Any]] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
    safety: dict[str, Any] = field(default_factory=dict)
    success_criteria: dict[str, Any] = field(default_factory=dict)


class RentAgent:
    def __init__(self, top_k: int = 8):
        self.top_k = top_k
        self.listings: pd.DataFrame | None = None
        self.model = None
        self.skill: RentFilterSkill | None = None

    def _init_steps(self) -> list[Step]:
        return [
            Step("任务入口", "接收并校验用户输入（预算/区域/面积等）"),
            Step("连接数据工具", "加载本地上海房源库，核对可用性"),
            Step("加载 ML 组件", "加载回归模型（验证集最优）"),
            Step("硬约束筛选", "按预算、区域、面积过滤候选房源"),
            Step("公允租金预测", "对候选调用回归模型推理"),
            Step("建议生成", "比较挂牌价与预测价，输出偏贵/合理/偏便宜"),
            Step("失败与安全检查", "处理无结果、异常输入、高偏差，必要时人工复核"),
        ]

    def load(self) -> None:
        if not DATA.exists():
            raise FileNotFoundError(f"数据不存在: {DATA}")
        if not MODEL.exists():
            raise FileNotFoundError(f"模型不存在: {MODEL}")
        self.listings = pd.read_csv(DATA)
        self.model = joblib.load(MODEL)
        self.skill = RentFilterSkill(model=self.model, top_k=self.top_k)

    @staticmethod
    def validate_input(
        budget: float | None,
        min_area: float | None,
        max_area: float | None,
        district: str | None,
    ) -> list[str]:
        errors = []
        if budget is None or budget <= 0:
            errors.append("预算必须为正数")
        if budget is not None and (budget < 1000 or budget > 50000):
            errors.append("预算超出合理范围（建议 1000–50000 元/月），请确认是否输入错误")
        if min_area is not None and max_area is not None and min_area > max_area:
            errors.append("最小面积不能大于最大面积")
        if min_area is not None and (min_area < 10 or min_area > 300):
            errors.append("最小面积异常")
        if max_area is not None and (max_area < 10 or max_area > 300):
            errors.append("最大面积异常")
        if district is not None and district.strip() == "":
            errors.append("区域不能为空字符串")
        return errors

    def run(
        self,
        *,
        budget: float,
        district: str | None = None,
        min_area: float = 30,
        max_area: float = 90,
        rooms: int | None = None,
        use_model: bool = True,
        top_k: int | None = None,
    ) -> AgentOutput:
        if top_k:
            self.top_k = top_k
        steps = self._init_steps()

        steps[0].status = StepStatus.RUNNING
        errs = self.validate_input(budget, min_area, max_area, district)
        if errs:
            steps[0].status = StepStatus.FAILED
            steps[0].detail = "；".join(errs)
            for s in steps[1:]:
                s.status = StepStatus.SKIPPED
            return AgentOutput(
                ok=False,
                success=False,
                message="输入异常，已拒绝执行。" + "；".join(errs),
                need_human_review=True,
                steps=steps,
                safety={"reason": "invalid_input", "errors": errs},
                success_criteria=self._criteria(False, False, False),
            )
        steps[0].status = StepStatus.DONE
        steps[0].detail = (
            f"budget={budget}, district={district or '不限'}, "
            f"area=[{min_area},{max_area}], rooms={rooms or '不限'}"
        )

        steps[1].status = StepStatus.RUNNING
        try:
            if self.listings is None or self.model is None or self.skill is None:
                self.load()
            assert self.listings is not None and self.skill is not None
            steps[1].status = StepStatus.DONE
            steps[1].detail = f"已连接房源库，共 {len(self.listings)} 条"
            steps[2].status = StepStatus.DONE if use_model else StepStatus.SKIPPED
            steps[2].detail = "已加载 best_model.joblib" if use_model else "消融：未启用模型"
        except Exception as e:
            steps[1].status = StepStatus.FAILED
            steps[1].detail = str(e)
            for s in steps[2:]:
                s.status = StepStatus.SKIPPED
            return AgentOutput(
                ok=False,
                success=False,
                message=f"工具/数据连接失败：{e}",
                need_human_review=True,
                steps=steps,
                safety={"reason": "tool_failure", "error": str(e)},
                success_criteria=self._criteria(False, False, False),
            )

        steps[3].status = StepStatus.RUNNING
        pool = self.listings.copy()
        if rooms is not None:
            pool = pool[pool["rooms"] == int(rooms)]
        self.skill.top_k = self.top_k
        result = self.skill.run(
            pool,
            budget=float(budget),
            district=district,
            rent_type=None,
            min_area=float(min_area),
            max_area=float(max_area),
            use_model=use_model,
        )

        if not result.ok:
            steps[3].status = StepStatus.FAILED
            steps[3].detail = result.message
            steps[4].status = StepStatus.SKIPPED
            steps[5].status = StepStatus.SKIPPED
            steps[6].status = StepStatus.DONE
            steps[6].detail = "无匹配结果，已请求用户调整或人工协助"
            return AgentOutput(
                ok=False,
                success=False,
                message=result.message,
                need_human_review=True,
                steps=steps,
                items=[],
                summary=result.summary,
                safety={"reason": "no_match"},
                success_criteria=self._criteria(False, False, True),
            )

        steps[3].status = StepStatus.DONE
        steps[3].detail = f"硬约束后剩余 {result.summary.get('matched')} 套"
        if use_model:
            steps[4].status = StepStatus.DONE
            steps[4].detail = "完成候选房源公允租金推理"
            steps[5].status = StepStatus.DONE
            steps[5].detail = "已生成建议标签与排序"
        else:
            steps[4].status = StepStatus.SKIPPED
            steps[4].detail = "消融关闭 ML"
            steps[5].status = StepStatus.DONE
            steps[5].detail = "仅按价格排序（无公允判断）"

        steps[6].status = StepStatus.DONE
        high_risk = sum(1 for i in result.items if i.get("need_human_review"))
        steps[6].detail = (
            f"高偏差条目 {high_risk}/{len(result.items)}；"
            + ("触发人工复核" if result.need_human_review else "未触发强制复核")
        )

        has_items = len(result.items) > 0
        has_advice = use_model and any(
            i.get("advice") not in {None, "", "仅规则筛选(无模型估价)"} for i in result.items
        )
        core_success = has_items and (has_advice if use_model else True)

        return AgentOutput(
            ok=True,
            success=core_success,
            message=result.message,
            need_human_review=result.need_human_review,
            steps=steps,
            items=result.items,
            summary={**result.summary, "rooms": rooms, "high_risk_items": high_risk},
            safety={
                "reason": "high_deviation" if result.need_human_review else "ok",
                "note": "预测不等于成交价，签约前请自行核实。",
                "data_boundary": "历史公开挂牌，可能过时；仅课程原型。",
            },
            success_criteria=self._criteria(core_success, has_advice if use_model else True, True),
        )

    @staticmethod
    def _criteria(got_result: bool, got_valuation: bool, handled_fail: bool) -> dict[str, Any]:
        return {
            "定义": {
                "返回可检查结果": "至少返回 1 条房源或明确无匹配说明",
                "估价建议可用": "启用模型时，结果含预测公允价与建议标签",
                "异常可处置": "输入错误/无匹配/高偏差有明确提示或人工复核",
            },
            "本次判定": {
                "返回可检查结果": got_result,
                "估价建议可用": got_valuation,
                "异常可处置": handled_fail,
            },
            "总体成功": bool(got_result and got_valuation and handled_fail),
        }

    def valuate_one(self, features: dict[str, Any], listed_price: float) -> dict[str, Any]:
        if self.skill is None or self.model is None:
            self.load()
        assert self.skill is not None
        if listed_price <= 0:
            return {
                "ok": False,
                "need_human_review": True,
                "message": "挂牌价输入异常",
            }
        pred = self.skill.predict_one(features)
        tag, ratio, need = self.skill._label(float(listed_price), pred)
        return {
            "ok": True,
            "pred_price": round(pred, 1),
            "listed_price": float(listed_price),
            "advice": tag,
            "price_gap_ratio": round(ratio, 3),
            "need_human_review": need,
            "message": "单套估价完成" + ("，建议人工复核" if need else ""),
        }
