"""命令行入口（调试用）。正式演示请用：python -m streamlit run app.py"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent_core import RentAgent


def main() -> None:
    p = argparse.ArgumentParser(description="上海租房 Agent CLI")
    p.add_argument("--budget", type=float, default=6000)
    p.add_argument("--district", type=str, default="浦东")
    p.add_argument("--min-area", type=float, default=30)
    p.add_argument("--max-area", type=float, default=80)
    p.add_argument("--rooms", type=int, default=None)
    p.add_argument("--top-k", type=int, default=5)
    p.add_argument("--no-model", action="store_true")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--json-out", type=str, default=None)
    args = p.parse_args()
    if args.demo:
        args.budget, args.district, args.min_area, args.max_area = 6000, "浦东", 30, 80

    agent = RentAgent(top_k=args.top_k)
    out = agent.run(
        budget=args.budget,
        district=args.district,
        min_area=args.min_area,
        max_area=args.max_area,
        rooms=args.rooms,
        use_model=not args.no_model,
        top_k=args.top_k,
    )

    print("=" * 60)
    print("上海租房 Agent（CLI 调试）")
    print("=" * 60)
    for i, s in enumerate(out.steps, 1):
        print(f"{i}. [{s.status.value}] {s.name}: {s.purpose}")
        if s.detail:
            print(f"   -> {s.detail}")
    print("成功判定:", out.success_criteria["本次判定"], "总体:", out.success_criteria["总体成功"])
    print("结果:", out.message)
    if out.need_human_review:
        print("【人工复核】需要")
    for i, item in enumerate(out.items, 1):
        print("-" * 40)
        print(f"#{i} {item.get('title')}")
        print(
            f"  {item.get('district')} | {item.get('area')}㎡ | {item.get('rooms')}室 | "
            f"挂牌{item.get('listed_price')} | 预测{item.get('pred_price')} | {item.get('advice')}"
        )
    print("安全:", out.safety.get("note"))

    if args.json_out:
        payload = {
            "ok": out.ok,
            "success": out.success,
            "message": out.message,
            "need_human_review": out.need_human_review,
            "steps": [
                {"name": s.name, "purpose": s.purpose, "status": s.status.value, "detail": s.detail}
                for s in out.steps
            ],
            "items": out.items,
            "summary": out.summary,
            "safety": out.safety,
            "success_criteria": out.success_criteria,
        }
        Path(args.json_out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print("json ->", args.json_out)


if __name__ == "__main__":
    main()
