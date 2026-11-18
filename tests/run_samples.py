"""运行可复现测试样例并写出结果。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agent_core import RentAgent  # noqa: E402


def main() -> None:
    cases = json.loads((ROOT / "tests" / "sample_queries.json").read_text(encoding="utf-8"))
    agent = RentAgent(top_k=5)
    agent.load()
    rows = []
    passed = 0
    for case in cases["cases"]:
        inp = case["input"]
        out = agent.run(
            budget=float(inp["budget"]),
            district=inp.get("district"),
            min_area=float(inp["min_area"]),
            max_area=float(inp["max_area"]),
            rooms=inp.get("rooms"),
            use_model=bool(inp.get("use_model", True)),
        )
        exp = case["expect"]
        ok = True
        reasons = []
        if "ok" in exp and out.ok != exp["ok"]:
            ok = False
            reasons.append(f"ok expect {exp['ok']} got {out.ok}")
        if exp.get("min_items") and len(out.items) < exp["min_items"]:
            ok = False
            reasons.append("items too few")
        if exp.get("need_human_review") and not out.need_human_review:
            ok = False
            reasons.append("expected human review")
        if exp.get("advice_contains"):
            adv = " ".join(str(i.get("advice")) for i in out.items)
            if exp["advice_contains"] not in adv and not out.items:
                # 无模型且有结果时检查；若无 items 另计
                if out.items:
                    ok = False
                    reasons.append("advice missing ablation tag")
            elif out.items and exp["advice_contains"] not in adv:
                ok = False
                reasons.append("advice missing ablation tag")
        passed += int(ok)
        rows.append(
            {
                "id": case["id"],
                "name": case["name"],
                "passed": ok,
                "agent_ok": out.ok,
                "success": out.success,
                "need_human_review": out.need_human_review,
                "n_items": len(out.items),
                "message": out.message,
                "reasons": "; ".join(reasons),
            }
        )
        print(f"[{'PASS' if ok else 'FAIL'}] {case['id']}: {out.message}")

    out_path = ROOT / "results" / "sample_test_report.json"
    payload = {
        "passed": passed,
        "total": len(rows),
        "pass_rate": passed / max(len(rows), 1),
        "rows": rows,
    }
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"passed": passed, "total": len(rows), "pass_rate": payload["pass_rate"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
