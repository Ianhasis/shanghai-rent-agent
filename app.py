"""沪租估网页端。运行：python -m streamlit run app.py"""
from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from src.agent_core import RentAgent

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
  padding-top: 1.1rem !important;
  padding-bottom: 3rem !important;
  max-width: 1080px !important;
}
.stApp {
  background:
    radial-gradient(1100px 460px at 8% -8%, rgba(15, 118, 110, 0.16), transparent 55%),
    radial-gradient(820px 380px at 100% 0%, rgba(180, 83, 9, 0.12), transparent 50%),
    linear-gradient(165deg, var(--bg0), var(--bg1) 50%, #eef2f4);
}
.hero { margin: 0.2rem 0 1.2rem; animation: rise .55s ease both; }
.brand {
  font-family: "Fraunces", serif;
  font-size: clamp(2.3rem, 4.4vw, 3.2rem);
  font-weight: 700;
  letter-spacing: -0.03em;
  line-height: 1.05;
  margin: 0;
}
.tagline {
  color: var(--muted);
  font-size: 1.02rem;
  max-width: 36rem;
  line-height: 1.55;
  margin: 0.45rem 0 0;
}
.panel-title {
  font-family: "Fraunces", serif;
  font-size: 1.22rem;
  margin: 0 0 0.35rem;
}
.hint { color: var(--muted); font-size: 0.92rem; margin: 0 0 0.95rem; }
.result-head {
  display: flex; justify-content: space-between; align-items: baseline;
  gap: 1rem; margin: 1.35rem 0 0.75rem;
}
.result-head h2 {
  font-family: "Fraunces", serif; font-size: 1.5rem; margin: 0;
}
.badge {
  display: inline-block; padding: 0.25rem 0.7rem; border-radius: 999px;
  font-size: 0.82rem; font-weight: 600; border: 1px solid var(--line); background: #fff;
}
.badge.ok { color: #0f766e; border-color: rgba(15,118,110,.35); background: rgba(15,118,110,.08); }
.badge.warn { color: #9a3412; border-color: rgba(154,52,18,.3); background: rgba(180,83,9,.1); }

div[data-testid="stMetric"] {
  background: #fff; border: 1px solid var(--line);
  border-radius: 14px; padding: 0.65rem 0.8rem;
}
div[data-testid="stMetric"] label { color: var(--muted) !important; }

.stButton > button {
  background: var(--ink) !important; color: #fff !important; border: none !important;
  border-radius: 12px !important; height: 3rem !important; font-weight: 600 !important;
  transition: transform .15s ease, background .15s ease !important;
}
.stButton > button:hover { background: var(--accent) !important; transform: translateY(-1px); }

@keyframes rise {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@media (max-width: 768px) {
  .brand { font-size: 2.05rem; }
  .result-head { flex-direction: column; align-items: flex-start; }
}
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


def main():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
          <p class="brand">沪租估</p>
          <p class="tagline">在上海找房时，帮你按预算筛房，并看看挂牌价正不正常。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    agent = get_agent()
    listings = agent.listings
    assert listings is not None
    districts = sorted([d for d in listings["district"].dropna().unique() if d != "未知"])
    default_dist = "浦东" if "浦东" in districts else districts[0]

    mode = st.radio(
        "选择任务",
        ["帮我找房", "判断这套房贵不贵"],
        horizontal=True,
        label_visibility="collapsed",
    )

    if mode == "帮我找房":
        with st.container(border=True):
            st.markdown('<p class="panel-title">填写找房条件</p>', unsafe_allow_html=True)
            st.markdown(
                '<p class="hint">填好后点开始，我会给你几套更合适的房子，并标出贵不贵。</p>',
                unsafe_allow_html=True,
            )

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
                top_k = st.slider("想看几套", 3, 12, 8)

            go = st.button("开始帮我找", width="stretch")

        if not go:
            return

        with st.spinner("正在按你的条件筛选并比较价格…"):
            out = agent.run(
                budget=float(budget),
                district=None if district == "不限" else district,
                min_area=float(min_area),
                max_area=float(max_area),
                rooms=None if rooms_opt == "不限" else int(rooms_opt),
                use_model=True,
                top_k=int(top_k),
            )

        if not out.ok:
            st.error("暂时没有合适房源，或条件有点冲突。")
            st.info("可以试试：提高预算、换个区，或把面积范围放宽一点。")
            return

        st.markdown(
            """
            <div class="result-head">
              <h2>为你找到的房源</h2>
            </div>
            """,
            unsafe_allow_html=True,
        )
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

                if pred is not None and gap is not None:
                    if gap > 0.05:
                        st.caption(f"这套可能偏贵，参考价大约 {pred:.0f} 元/月。")
                    elif gap < -0.05:
                        st.caption(f"这套相对划算，参考价大约 {pred:.0f} 元/月。")
                    else:
                        st.caption(f"价格比较正常，参考价大约 {pred:.0f} 元/月。")

        with st.expander("这是怎么帮我判断的？"):
            st.write(
                "先按你的预算、区域、面积找出候选，再估算每套房大概值多少钱，"
                "最后和房东要价对比，优先给你更合适的。"
            )

        st.caption("参考价仅供参考，不代表当前成交价；看房签约前请实地确认。")
        return

    with st.container(border=True):
        st.markdown('<p class="panel-title">填写这套房的信息</p>', unsafe_allow_html=True)
        st.markdown(
            '<p class="hint">适合你已经看到一套具体房子，想快速判断贵不贵。</p>',
            unsafe_allow_html=True,
        )
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

    with st.spinner("正在对比参考价…"):
        out = agent.valuate_one(
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

    if not out["ok"]:
        st.error("信息好像不太对，请检查后再试。")
        return

    st.markdown(
        f"""
        <div class="result-head">
          <h2>判断结果</h2>
          {advice_badge(out['advice'])}
        </div>
        """,
        unsafe_allow_html=True,
    )
    a, b, c = st.columns(3)
    a.metric("参考合理价", f"{out['pred_price']:.0f} 元/月")
    b.metric("房东要价", f"{out['listed_price']:.0f} 元/月")
    c.metric("大概相差", f"{abs(out['price_gap_ratio'])*100:.1f}%")

    if out["need_human_review"]:
        st.warning("差得比较多，建议你再核实后再决定。")
    else:
        st.success("可以继续约看；签约前仍建议实地确认。")

    st.caption("参考价仅供参考，不代表当前成交价。")


if __name__ == "__main__":
    main()
