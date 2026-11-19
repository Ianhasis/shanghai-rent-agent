"""规则调度用的自然语言目标解析（不依赖外部大模型 API）。"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

DISTRICTS = [
    "浦东",
    "闵行",
    "徐汇",
    "长宁",
    "静安",
    "普陀",
    "虹口",
    "杨浦",
    "黄浦",
    "宝山",
    "嘉定",
    "青浦",
    "松江",
    "奉贤",
    "金山",
    "崇明",
]

CN_NUM = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
}


@dataclass
class ParsedGoal:
    intent: str  # search | valuate | unknown
    budget: float | None = None
    district: str | None = None
    rooms: int | None = None
    min_area: float | None = None
    max_area: float | None = None
    listed_price: float | None = None
    area: float | None = None
    halls: int | None = None
    has_metro: bool | None = None
    raw: str = ""
    slots: dict[str, Any] = field(default_factory=dict)
    missing: list[str] = field(default_factory=list)
    clarify_question: str | None = None
    defaults_used: list[str] = field(default_factory=list)


def _parse_money(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*万", text)
    if m:
        return float(m.group(1)) * 10000
    m = re.search(r"(\d+(?:\.\d+)?)\s*[kK千]", text)
    if m:
        return float(m.group(1)) * 1000
    for ch, n in CN_NUM.items():
        m = re.search(rf"{ch}\s*千", text)
        if m:
            return float(n * 1000)
    m = re.search(
        r"(?:预算|月租|租金|要价|挂牌|价格|房价)?\s*(?:是|为|在)?\s*(\d{3,5})\s*(?:元|块)?",
        text,
    )
    if m:
        return float(m.group(1))
    m = re.search(r"(\d{4,5})", text)
    if m:
        return float(m.group(1))
    return None


def _parse_rooms(text: str) -> int | None:
    m = re.search(r"(\d)\s*室", text)
    if m:
        return int(m.group(1))
    m = re.search(r"([一二两三四五六])\s*居", text)
    if m:
        return CN_NUM.get(m.group(1))
    m = re.search(r"([一二两三四五六])\s*室", text)
    if m:
        return CN_NUM.get(m.group(1))
    return None


def _parse_area_range(text: str) -> tuple[float | None, float | None, float | None]:
    m = re.search(r"(\d+(?:\.\d+)?)\s*[-~～到至]\s*(\d+(?:\.\d+)?)\s*(?:平|㎡|m2|平方米)?", text)
    if m:
        a, b = float(m.group(1)), float(m.group(2))
        return min(a, b), max(a, b), None
    m = re.search(r"(?:约|大概|左右)?\s*(\d+(?:\.\d+)?)\s*(?:平|㎡|m2|平方米)", text)
    if m:
        v = float(m.group(1))
        return None, None, v
    return None, None, None


def _detect_intent(text: str) -> str:
    # 单套判断：强信号（具体房 + 要价/贵不贵）
    strong_valuate = ["贵不贵", "贵吗", "值不值", "这套房", "这套房子"]
    if any(k in text for k in strong_valuate):
        return "valuate"
    if (("要价" in text) or ("挂牌" in text)) and (
        "平" in text or "㎡" in text or "m2" in text or "平方米" in text
    ):
        return "valuate"

    # 找房：预算/推荐/找房；“划算”若伴随预算或居室，仍视为找房比价
    search_keys = ["找房", "帮我找", "有没有", "推荐", "求租", "想租", "租房", "预算", "以内"]
    if any(k in text for k in search_keys):
        return "search"
    if "看看" in text or "划算" in text or "偏贵" in text:
        return "search"
    return "search"


def parse_goal(text: str) -> ParsedGoal:
    raw = (text or "").strip()
    g = ParsedGoal(intent="unknown", raw=raw)
    if not raw:
        g.missing = ["目标描述"]
        g.clarify_question = "你想找房，还是判断某套房贵不贵？可以一句话说清楚。"
        return g

    g.intent = _detect_intent(raw)
    for d in DISTRICTS:
        if d in raw:
            g.district = d
            break

    money = _parse_money(raw)
    rooms = _parse_rooms(raw)
    min_a, max_a, single_a = _parse_area_range(raw)
    g.rooms = rooms
    if "地铁" in raw:
        g.has_metro = True

    if g.intent == "valuate":
        g.listed_price = money
        g.area = single_a
        if min_a is not None and max_a is not None:
            g.area = (min_a + max_a) / 2
        if g.listed_price is None:
            g.missing.append("房东要价")
        if g.area is None:
            g.missing.append("面积")
        if g.district is None:
            g.missing.append("所在区域")
        if g.rooms is None:
            g.rooms = 2
            g.defaults_used.append("居室默认2室")
        g.halls = 1
        if g.missing:
            g.clarify_question = (
                "判断单套房还缺："
                + "、".join(g.missing)
                + "。例如：「浦东 65㎡ 两室要价 7200，贵不贵？」"
            )
    else:
        g.intent = "search"
        g.budget = money
        if min_a is not None and max_a is not None:
            g.min_area, g.max_area = min_a, max_a
        elif single_a is not None:
            g.min_area, g.max_area = max(15, single_a - 15), single_a + 15
            g.defaults_used.append(f"面积按约{single_a}㎡放宽为{g.min_area:.0f}-{g.max_area:.0f}")
        else:
            g.min_area, g.max_area = 30, 80
            g.defaults_used.append("面积默认30-80㎡")
        if g.budget is None:
            g.missing.append("预算")
            g.clarify_question = "还缺月租预算。例如：「闵行预算6000两居，帮我看看划不划算」"
        if g.district is None:
            g.defaults_used.append("区域暂不限")

    g.slots = {
        "intent": g.intent,
        "budget": g.budget,
        "district": g.district,
        "rooms": g.rooms,
        "min_area": g.min_area,
        "max_area": g.max_area,
        "listed_price": g.listed_price,
        "area": g.area,
    }
    return g
