"""沪租估网页端。运行：python -m streamlit run app.py"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.agent_core import AgentOutput, RentAgent

st.set_page_config(
    page_title="沪租估 · 上海租房助手",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Instrument+Sans:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,500;9..144,700&display=swap');

:root {
  --ink: #12263a;
  --muted: #5b6b7c;
  --line: rgba(18, 38, 58, 0.12);
  --accent: #0f766e;
  --bg0: #e8eef2;
  --bg1: #f7f3ea;
}

html, body, [class*="css"]  {
  font-family: "Instrument Sans", sans-serif;
  color: var(--ink);
}
#MainMenu, footer, header { visibility: hidden; }
[data-testid="stSidebar"] { display: none !important; }
.block-container {
  padding-top: 1.0rem !important;
  padding-bottom: 3rem !important;
  max-width: 980px !important;
}
.stApp {
  background:
    radial-gradient(1100px 460px at 8% -8%, rgba(15, 118, 110, 0.16), transparent 55%),
    radial-gradient(820px 380px at 100% 0%, rgba(180, 83, 9, 0.12), transparent 50%),
    linear-gradient(165deg, var(--bg0), var(--bg1) 50%, #eef2f4);
}
.hero { margin: 0.1rem 0 0.85rem; }
.brand {
  font-family: "Fraunces", serif;
  font-size: clamp(1.9rem, 3.6vw, 2.55rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.08;
  margin: 0;
}
.tagline {
  color: var(--muted);
  font-size: 0.98rem;
  max-width: 34rem;
  line-height: 1.5;
  margin: 0.35rem 0 0;
}
.task-label {
  font-size: 0.82rem;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--muted);
  margin: 0 0 0.45rem;
  text-transform: uppercase;
}
.panel-title {
  font-family: "Fraunces", serif;
  font-size: 1.12rem;
  margin: 0 0 0.3rem;
}
.hint { color: var(--muted); font-size: 0.9rem; margin: 0 0 0.85rem; }
.step-box {
  background: rgba(255,255,255,0.88);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 0.75rem 0.9rem;
  margin: 0.7rem 0 1rem;
}
.step-box p { margin: 0.2rem 0; font-size: 0.92rem; color: #243447; }
.step-title {
  font-weight: 700;
  font-size: 0.88rem;
  color: var(--accent);
  margin: 0 0 0.35rem !important;
}
.conclusion {
  background: rgba(15, 118, 110, 0.08);
  border: 1px solid rgba(15, 118, 110, 0.22);
  border-radius: 14px;
  padding: 0.85rem 1rem;
  margin: 0.4rem 0 1rem;
  line-height: 1.55;
}
.result-head h2 {
  font-family: "Fraunces", serif; font-size: 1.35rem; margin: 1rem 0 0.55rem;
}
.badge {
  display: inline-block; padding: 0.22rem 0.65rem; border-radius: 999px;
  font-size: 0.8rem; font-weight: 600; border: 1px solid var(--line); background: #fff;
}
.badge.ok { color: #0f766e; border-color: rgba(15,118,110,.35); background: rgba(15,118,110,.08); }
.badge.warn { color: #9a3412; border-color: rgba(154,52,18,.3); background: rgba(180,83,9,.1); }

div[data-testid="stMetric"] {
  background: #fff; border: 1px solid var(--line);
  border-radius: 14px; padding: 0.55rem 0.7rem;
}
div[data-testid="stMetric"] label { color: var(--muted) !important; }

div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] div[role="radiogroup"] {
  gap: 0.55rem !important;
  flex-wrap: wrap;
}
div[data-testid="stRadio"] div[role="radiogroup"] label {
  background: rgba(255,255,255,0.9) !important;
  border: 1px solid var(--line) !important;
  border-radius: 12px !important;
  padding: 0.55rem 0.95rem !important;
  min-width: 8.5rem;
}
div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
  border-color: rgba(15,118,110,0.55) !important;
  background: rgba(15,118,110,0.10) !important;
  box-shadow: 0 0 0 1px rgba(15,118,110,0.18);
}

.stButton > button {
  background: var(--ink) !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; height: 2.85rem !important; font-weight: 600 !important;
}
.stButton > button:hover { background: var(--accent) !important; }
</style>
"""


@st.cache_resource
def get_agent():
    agent = RentAgent(top_k=8)
    agent.load()
    return agent


def friendly_advice(advice: str) -> str:
    mapping = {
        "价格合理": "价格正常",
        "偏贵": "可能偏贵",
        "偏便宜": "相对划算",
        "显著偏贵": "明显偏贵",
        "显著偏低(需核验真伪/条件遗漏)": "低得异常，建议核实",
        "无法估价": "暂时不好判断",
        "仅规则筛选(无模型估价)": "仅按条件筛选",
    }
    return mapping.get(advice, advice)


def advice_badge(advice: str) -> str:
    text = friendly_advice(advice)
    cls = "ok"
    if "偏贵" in text or "异常" in text or "不好" in text:
        cls = "warn"
    return f'<span class="badge {cls}">{text}</span>'


def render_trace(out: AgentOutput):
    if not out.planner_trace and not out.steps:
        return
    lines = out.planner_trace or [
        f"[{s.status.value}] {s.name}：{s.detail or s.purpose}" for s in out.steps
    ]
    html = ['<div class="step-box"><p class="step-title">Agent 执行过程</p>']
    for line in lines:
        html.append(f"<p>{line}</p>")
    html.append("</div>")
    st.markdown("\n".join(html), unsafe_allow_html=True)


def render_conclusion(text: str):
    if not text:
        return
    st.markdown(f'<div class="conclusion"><b>结论</b><br/>{text}</div>', unsafe_allow_html=True)


def render_listings(out: AgentOutput):
    if out.intent == "valuate" and out.items:
        item = out.items[0]
        st.markdown('<div class="result-head"><h2>判断结果</h2></div>', unsafe_allow_html=True)
        st.markdown(advice_badge(str(item.get("advice"))), unsafe_allow_html=True)
        a, b, c = st.columns(3)
        a.metric("参考合理价", f"{item.get('pred_price'):.0f} 元/月")
        b.metric("房东要价", f"{item.get('listed_price'):.0f} 元/月")
        gap = item.get("price_gap_ratio")
        c.metric("大概相差", "—" if gap is None else f"{abs(gap)*100:.1f}%")
        if out.need_human_review:
            st.warning("差得比较多，建议你再核实后再决定。")
        st.caption("参考价仅供参考，不代表当前成交价。")
        return

    if not out.ok:
        st.error(out.message or "暂时没有合适房源，或条件有点冲突。")
        st.info("可以试试：提高预算、换个区，或把面积范围放宽一点。")
        return

    st.markdown('<div class="result-head"><h2>为你找到的房源</h2></div>', unsafe_allow_html=True)
    st.write(f"共找到符合条件的候选，下面先给你看 {len(out.items)} 套。")
    if out.need_human_review:
        st.warning("有的房价差得比较多，建议你再确认一下再联系。")

    for i, item in enumerate(out.items, 1):
        with st.container(border=True):
            left, right = st.columns([4, 1.3])
            with left:
                st.markdown(f"### {i}. {item.get('title')}")
                st.caption(
                    f"{item.get('district')} · {item.get('area')}㎡ · "
                    f"{item.get('rooms')}室 · {item.get('address')}"
                )
            with right:
                st.markdown(advice_badge(str(item.get("advice"))), unsafe_allow_html=True)

            listed = item.get("listed_price")
            pred = item.get("pred_price")
            gap = item.get("price_gap_ratio")
            m1, m2, m3 = st.columns(3)
            m1.metric("房东要价", f"{listed:.0f} 元/月")
            m2.metric("参考合理价", "—" if pred is None else f"{pred:.0f} 元/月")
            m3.metric("大概相差", "—" if gap is None else f"{abs(gap)*100:.1f}%")

    with st.expander("这是怎么帮我判断的？"):
        st.write(
            "Agent 先理解你的目标并抽取条件，再调用房源库检索，接着用回归模型估计公允价，"
            "最后和挂牌价对比给出建议。缺关键信息时会先追问。"
        )
    st.caption("参考价仅供参考，不代表当前成交价；看房签约前请实地确认。")


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
          <p class="brand">沪租估</p>
          <p class="tagline">说一句目标，或精确筛选；我会自己拆任务、查房源、估公允价并给出结论。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    agent = get_agent()
    listings = agent.listings
    assert listings is not None
    districts = sorted([d for d in listings["district"].dropna().unique() if d != "未知"])
    default_dist = "浦东" if "浦东" in districts else districts[0]

    st.markdown('<p class="task-label">选择任务</p>', unsafe_allow_html=True)
    task = st.radio(
        "选择任务",
        ["帮我找房", "判断这套房贵不贵"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if task == "帮我找房":
        with st.container(border=True):
            st.markdown('<p class="panel-title">找房方式</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="hint">两种入口最终都走同一套 Agent：理解目标 → 调度工具 → 给出结论。</p>',
                unsafe_allow_html=True,
            )
            find_mode = st.radio(
                "找房方式",
                ["一句话找房", "精确筛选"],
                horizontal=True,
                label_visibility="collapsed",
            )

            if find_mode == "一句话找房":
                st.caption("示例：闵行预算6000两居，帮我看看划不划算")
                goal = st.text_area(
                    "一句话目标",
                    value="闵行预算6000两居，帮我看看划不划算",
                    height=78,
                    label_visibility="collapsed",
                    placeholder="例如：浦东 5500 以内，想找 50-70㎡ 的两室",
                )
                top_k = st.slider("想看几套", 3, 12, 8)
                go = st.button("让 Agent 开始", width="stretch")
                if go:
                    with st.spinner("Agent 正在理解目标并调度工具…"):
                        out = agent.run_from_goal(goal, top_k=int(top_k))
                    render_trace(out)
                    if out.need_clarify:
                        st.warning(out.clarify_question or "还需要补充一点信息。")
                        return
                    render_conclusion(out.conclusion)
                    render_listings(out)
                return

            c1, c2, c3 = st.columns([1.1, 1, 1])
            with c1:
                budget = st.number_input("月租预算（元）", 1000, 50000, 6000, 100)
            with c2:
                district = st.selectbox(
                    "想住哪个区",
                    ["不限"] + districts,
                    index=(["不限"] + districts).index(default_dist),
                )
            with c3:
                rooms_opt = st.selectbox("居室", ["不限", 1, 2, 3, 4])

            c4, c5 = st.columns([2, 1])
            with c4:
                min_area, max_area = st.slider("面积范围（㎡）", 15, 200, (30, 80))
            with c5:
                top_k = st.slider("想看几套", 3, 12, 8, key="filter_topk")

            go = st.button("开始帮我找", width="stretch")
            if not go:
                return

            with st.spinner("Agent 正在按条件检索并估价…"):
                out = agent.run(
                    budget=float(budget),
                    district=None if district == "不限" else district,
                    min_area=float(min_area),
                    max_area=float(max_area),
                    rooms=None if rooms_opt == "不限" else int(rooms_opt),
                    use_model=True,
                    top_k=int(top_k),
                )
            out.planner_trace = [
                "①理解目标：精确筛选模式（用户已给出结构化条件）",
                f"②抽取参数：预算={budget}，区域={district}，面积={min_area}-{max_area}，居室={rooms_opt}",
                "③调用数据工具：硬约束检索房源库",
                "④调用回归模型：预测公允租金并比较挂牌价",
                "⑤整合结论：" + (out.conclusion or RentAgent._search_conclusion(out)),
            ]
            out.conclusion = RentAgent._search_conclusion(out)
            out.intent = "search"
            render_trace(out)
            render_conclusion(out.conclusion)
            render_listings(out)
            return

    with st.container(border=True):
        st.markdown('<p class="panel-title">判断这套房贵不贵</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hint">也可以一句话，例如：浦东 65㎡ 两室要价 7200，贵不贵？</p>',
            unsafe_allow_html=True,
        )
        val_mode = st.radio(
            "判断方式",
            ["一句话判断", "填写信息"],
            horizontal=True,
            label_visibility="collapsed",
            key="val_mode",
        )

        if val_mode == "一句话判断":
            goal = st.text_area(
                "一句话判断",
                value="浦东 65㎡ 两室要价 7200，贵不贵？",
                height=78,
                label_visibility="collapsed",
                key="val_goal",
            )
            ask = st.button("让 Agent 判断", width="stretch")
            if ask:
                with st.spinner("Agent 正在估价并对比…"):
                    out = agent.run_from_goal(goal, top_k=3)
                render_trace(out)
                if out.need_clarify:
                    st.warning(out.clarify_question or "还需要补充一点信息。")
                    return
                render_conclusion(out.conclusion)
                render_listings(out)
            return

        dist = st.selectbox("所在区域", districts, index=districts.index(default_dist))
        sub = listings[listings["district"] == dist]
        if sub.empty:
            sub = listings

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            area = st.number_input("面积（㎡）", 15.0, 250.0, 60.0)
        with c2:
            rooms = st.number_input("室", 1, 6, 2)
        with c3:
            halls = st.number_input("厅", 0, 3, 1)
        with c4:
            listed = st.number_input("房东要价（元/月）", 1000.0, 50000.0, 6000.0)

        c5, c6 = st.columns(2)
        with c5:
            orient = st.selectbox("朝向", ["南", "南北", "东", "西", "北", "未知"])
        with c6:
            metro = st.checkbox("附近有地铁", value=True)

        ask = st.button("帮我判断", width="stretch")
        if not ask:
            return

        with st.spinner("Agent 正在对比参考价…"):
            one = agent.valuate_one(
                {
                    "area": float(area),
                    "rooms": int(rooms),
                    "halls": int(halls),
                    "has_metro": int(metro),
                    "lng": float(sub["lng"].median()),
                    "lat": float(sub["lat"].median()),
                    "orient": orient,
                    "district": dist,
                },
                float(listed),
            )
        if not one.get("ok"):
            st.error("信息好像不太对，请检查后再试。")
            return

        out = AgentOutput(
            ok=True,
            success=True,
            message=one["message"],
            need_human_review=bool(one["need_human_review"]),
            items=[
                {
                    "title": f"{dist}·单套判断",
                    "district": dist,
                    "area": float(area),
                    "rooms": int(rooms),
                    "listed_price": one["listed_price"],
                    "pred_price": one["pred_price"],
                    "advice": one["advice"],
                    "price_gap_ratio": one["price_gap_ratio"],
                    "need_human_review": one["need_human_review"],
                    "address": "",
                }
            ],
            planner_trace=[
                "①理解目标：单套判断（结构化填写）",
                f"②抽取参数：区域={dist}，面积={area}，要价={listed}",
                "③调用回归模型：预测公允月租",
                "④对比挂牌与预测，生成结论",
            ],
            conclusion=(
                f"这套在{dist}、约{area:.0f}㎡：房东要价 {one['listed_price']:.0f} 元/月，"
                f"参考公允价约 {one['pred_price']:.0f} 元/月，相差 {abs(one['price_gap_ratio'])*100:.1f}%。"
                f"结论：{friendly_advice(one['advice'])}。"
            ),
            intent="valuate",
        )
        render_trace(out)
        render_conclusion(out.conclusion)
        render_listings(out)


if __name__ == "__main__":
    main()
