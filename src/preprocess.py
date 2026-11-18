"""清洗上海链家租房数据（整套面积，更符合常识）。"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "lianjia_rent_gps.csv"
OUT = ROOT / "data" / "processed" / "shanghai_listings.csv"
META = ROOT / "data" / "processed" / "preprocess_meta.txt"

# 粗略行政区映射：部分小区名无法精确定位时记为未知，模型用 One-Hot 处理
DISTRICT_KEYWORDS = [
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


def parse_area(text) -> float:
    s = str(text)
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else float("nan")


def parse_price(text) -> float:
    s = str(text).replace(",", "").replace("元", "").strip()
    m = re.search(r"(\d+(?:\.\d+)?)", s)
    return float(m.group(1)) if m else float("nan")


def parse_rooms(layout: str) -> tuple[int, int]:
    text = str(layout)
    m = re.search(r"(\d+)\s*室", text)
    n = re.search(r"(\d+)\s*厅", text)
    return int(m.group(1) if m else 1), int(n.group(1) if n else 0)


def guess_district_from_text(title: str, community: str) -> str:
    blob = f"{title}{community}"
    # 优先匹配括号内行政区，如 金桥新城（浦东）
    m = re.search(r"[（(](" + "|".join(DISTRICT_KEYWORDS) + r")[)）]", blob)
    if m:
        return m.group(1)
    for d in DISTRICT_KEYWORDS:
        if d in blob:
            return d
    return ""


def guess_district_from_gps(lng: float, lat: float) -> str:
    """基于经纬度的粗分区（课程可用近似，报告中说明局限）。"""
    if pd.isna(lng) or pd.isna(lat):
        return "未知"
    # 先匹配相对明确的郊区/外围，再匹配中心城区，最后浦东
    boxes = [
        ("崇明", 121.30, 121.95, 31.45, 31.85),
        ("金山", 120.95, 121.40, 30.70, 30.95),
        ("奉贤", 121.35, 121.75, 30.85, 31.05),
        ("青浦", 120.90, 121.30, 31.05, 31.30),
        ("松江", 121.10, 121.40, 30.95, 31.15),
        ("嘉定", 121.10, 121.40, 31.25, 31.50),
        ("闵行", 121.30, 121.52, 31.00, 31.20),
        ("宝山", 121.35, 121.55, 31.28, 31.48),
        ("黄浦", 121.45, 121.51, 31.20, 31.25),
        ("徐汇", 121.42, 121.48, 31.14, 31.22),
        ("长宁", 121.36, 121.45, 31.18, 31.24),
        ("静安", 121.42, 121.48, 31.22, 31.28),
        ("普陀", 121.36, 121.46, 31.22, 31.30),
        ("虹口", 121.46, 121.52, 31.25, 31.31),
        ("杨浦", 121.48, 121.58, 31.26, 31.35),
        ("浦东", 121.50, 121.95, 30.95, 31.40),
    ]
    for name, lng0, lng1, lat0, lat1 in boxes:
        if lng0 <= lng <= lng1 and lat0 <= lat <= lat1:
            return name
    return "未知"


def guess_district(title: str, community: str, lng, lat) -> str:
    text_hit = guess_district_from_text(title, community)
    if text_hit:
        return text_hit
    return guess_district_from_gps(lng, lat)


def infer_orient(title: str) -> str:
    t = str(title)
    for o in ["南北", "东南", "西南", "东北", "西北", "南", "北", "东", "西"]:
        if o in t:
            return o
    return "未知"


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["area"] = df["面积"].map(parse_area)
    df["price"] = df["价格"].map(parse_price)
    rooms_halls = df["户型"].map(parse_rooms)
    df["rooms"] = rooms_halls.map(lambda x: x[0])
    df["halls"] = rooms_halls.map(lambda x: x[1])
    df["title"] = df["标题"].astype(str)
    df["community"] = df["小区"].astype(str)
    df["layout"] = df["户型"].astype(str)
    df["lng"] = pd.to_numeric(df.get("经度"), errors="coerce")
    df["lat"] = pd.to_numeric(df.get("纬度"), errors="coerce")
    df["district"] = [
        guess_district(t, c, lng, lat)
        for t, c, lng, lat in zip(df["title"], df["community"], df["lng"], df["lat"])
    ]
    df["orient"] = df["title"].map(infer_orient)
    df["rent_type"] = "整租"  # 该数据集为整套出租挂牌
    df["floor_ratio"] = 0.5  # 原表无楼层，用中性占位，避免丢掉样本
    df["private_bath"] = 1
    df["balcony"] = 0
    df["has_metro"] = df["title"].map(lambda x: int("地铁" in str(x) or "号线" in str(x)))
    df["price_per_sqm"] = df["price"] / df["area"].clip(lower=0.1)
    df["listing_id"] = df["链接"].astype(str)
    df["address"] = df["community"]

    out = df[
        [
            "listing_id",
            "title",
            "rent_type",
            "area",
            "rooms",
            "halls",
            "layout",
            "floor_ratio",
            "orient",
            "private_bath",
            "balcony",
            "district",
            "has_metro",
            "price",
            "price_per_sqm",
            "address",
            "community",
            "lng",
            "lat",
        ]
    ].dropna(subset=["area", "price"])

    # 整租常识范围
    out = out[(out["area"] >= 15) & (out["area"] <= 250)]
    out = out[(out["price"] >= 1500) & (out["price"] <= 40000)]
    out = out[(out["price_per_sqm"] >= 30) & (out["price_per_sqm"] <= 500)]
    out = out.drop_duplicates(subset=["listing_id"]).reset_index(drop=True)
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    raw = pd.read_csv(RAW, encoding="utf-8")
    cleaned = clean(raw)
    cleaned.to_csv(OUT, index=False, encoding="utf-8-sig")
    meta = [
        f"source=lianjia_rent_gps.csv",
        f"raw_rows={len(raw)}",
        f"clean_rows={len(cleaned)}",
        f"area_mean={cleaned['area'].mean():.1f}",
        f"area_median={cleaned['area'].median():.1f}",
        f"price_mean={cleaned['price'].mean():.1f}",
        f"price_median={cleaned['price'].median():.1f}",
        f"districts={cleaned['district'].value_counts().head(12).to_dict()}",
        f"rooms={cleaned['rooms'].value_counts().to_dict()}",
    ]
    META.write_text("\n".join(meta), encoding="utf-8")
    print("\n".join(meta))
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
