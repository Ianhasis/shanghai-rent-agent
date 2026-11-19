"""Agent 编排：理解目标、调度工具、整合结论；异常时提示人工确认。"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from skills.rent_filter_skill import RentFilterSkill
from .goal_parser import ParsedGoal, parse_goal

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
    need_clarify: bool = False
    clarify_question: str | None = None
    planner_trace: list[str] = field(default_factory=list)
    conclusion: str = ""
    parsed: dict[str, Any] = field(default_factory=dict)
    intent: str = "search"


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

    def run_from_goal(self, text: str, top_k: int = 8) -> AgentOutput:
        """一句话目标：解析 → 缺槽追问 → 调度检索/回归 → 整合结论。"""
        trace: list[str] = []
        parsed = parse_goal(text)
        trace.append(f"①理解目标：判定任务为「{'找房' if parsed.intent == 'search' else '单套判断' if parsed.intent == 'valuate' else '待明确'}」")
        trace.append(f"②抽取参数：{self._slot_brief(parsed)}")

        if parsed.missing:
            trace.append("③发现缺失信息，向用户追问后再继续")
            return AgentOutput(
                ok=False,
                success=False,
                message="信息还不够，需要你补充后我再继续。",
                need_human_review=False,
                need_clarify=True,
                clarify_question=parsed.clarify_question,
                planner_trace=trace,
                parsed=parsed.slots,
                intent=parsed.intent,
                conclusion=parsed.clarify_question or "",
            )

        if parsed.defaults_used:
            trace.append("③补全默认值：" + "；".join(parsed.defaults_used))
        else:
            trace.append("③参数齐全，开始调度工具")

        if parsed.intent == "valuate":
            return self._run_valuate_parsed(parsed, trace)

        trace.append("④调用数据工具：按约束检索房源库")
        trace.append("⑤调用回归模型：预测公允租金并比较挂牌价")
        out = self.run(
            budget=float(parsed.budget or 6000),
            district=parsed.district,
            min_area=float(parsed.min_area or 30),
            max_area=float(parsed.max_area or 80),
            rooms=parsed.rooms,
            use_model=True,
            top_k=top_k,
        )
        out.planner_trace = trace + [f"⑥整合结论：{self._search_conclusion(out)}"]
        out.parsed = parsed.slots
        out.intent = "search"
        out.conclusion = self._search_conclusion(out)
        return out

    def _run_valuate_parsed(self, parsed: ParsedGoal, trace: list[str]) -> AgentOutput:
        if self.listings is None or self.skill is None:
            self.load()
        assert self.listings is not None
        dist = parsed.district or "浦东"
        sub = self.listings[self.listings["district"] == dist]
        if sub.empty:
            sub = self.listings
        trace.append("④调用回归模型：对这套房预测公允月租")
        features = {
            "area": float(parsed.area or 60),
            "rooms": int(parsed.rooms or 2),
            "halls": int(parsed.halls or 1),
            "has_metro": int(bool(parsed.has_metro)),
            "lng": float(sub["lng"].median()),
            "lat": float(sub["lat"].median()),
            "orient": "南",
            "district": dist,
        }
        one = self.valuate_one(features, float(parsed.listed_price or 0))
        if not one.get("ok"):
            trace.append("⑤估价失败，请检查要价等信息")
            return AgentOutput(
                ok=False,
                success=False,
                message=str(one.get("message")),
                need_human_review=True,
                planner_trace=trace,
                parsed=parsed.slots,
                intent="valuate",
                conclusion="信息不足或要价异常，暂时无法判断。",
            )

        gap = float(one["price_gap_ratio"])
        advice = str(one["advice"])
        conclusion = (
            f"这套在{dist}、约{features['area']:.0f}㎡：房东要价 {one['listed_price']:.0f} 元/月，"
            f"参考公允价约 {one['pred_price']:.0f} 元/月，相差 {abs(gap)*100:.1f}%。"
            f"结论：{advice}。"
            + ("建议你再核实后再决定。" if one["need_human_review"] else "可以继续约看，签约前仍建议实地确认。")
        )
        trace.append("⑤对比挂牌与预测，生成溢价判断")
        trace.append("⑥整合结论：" + conclusion)
        return AgentOutput(
            ok=True,
            success=True,
            message=one["message"],
            need_human_review=bool(one["need_human_review"]),
            items=[
                {
                    "title": f"{dist}·单套判断",
                    "district": dist,
                    "area": features["area"],
                    "rooms": features["rooms"],
                    "listed_price": one["listed_price"],
                    "pred_price": one["pred_price"],
                    "advice": advice,
                    "price_gap_ratio": one["price_gap_ratio"],
                    "need_human_review": one["need_human_review"],
                    "address": "",
                }
            ],
            summary={"matched": 1, "returned": 1, "district": dist},
            planner_trace=trace,
            parsed=parsed.slots,
            intent="valuate",
            conclusion=conclusion,
            success_criteria=self._criteria(True, True, True),
            safety={
                "reason": "high_deviation" if one["need_human_review"] else "ok",
                "note": "预测不等于成交价，签约前请自行核实。",
            },
        )

    @staticmethod
    def _slot_brief(parsed: ParsedGoal) -> str:
        parts = []
        if parsed.district:
            parts.append(f"区域={parsed.district}")
        if parsed.budget:
            parts.append(f"预算={parsed.budget:.0f}")
        if parsed.rooms:
            parts.append(f"居室={parsed.rooms}")
        if parsed.min_area and parsed.max_area:
            parts.append(f"面积={parsed.min_area:.0f}-{parsed.max_area:.0f}")
        if parsed.area:
            parts.append(f"面积≈{parsed.area:.0f}")
        if parsed.listed_price:
            parts.append(f"要价={parsed.listed_price:.0f}")
        return "，".join(parts) if parts else "暂未抽到足够参数"

    @staticmethod
    def _search_conclusion(out: "AgentOutput") -> str:
        if not out.ok:
            return out.message
        n = len(out.items)
        cheap = sum(1 for i in out.items if i.get("advice") in {"偏便宜", "价格合理"})
        expensive = sum(1 for i in out.items if "偏贵" in str(i.get("advice", "")))
        text = f"按你的目标找到候选，先给你看 {n} 套；其中约 {cheap} 套相对正常/划算"
        if expensive:
            text += f"，{expensive} 套可能偏贵"
        text += "。优先看排在前面的。"
        if out.need_human_review:
            text += "有的房价差较大，建议核实后再联系。"
        return text
