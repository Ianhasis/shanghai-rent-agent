"""一键：预处理 -> 训练 -> 评估 -> 演示。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("\n>>>", " ".join(cmd))
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> None:
    py = sys.executable
    run([py, "src/preprocess.py"])
    run([py, "src/train.py"])
    run([py, "src/evaluate.py"])
    run([py, "src/plot_results.py"])
    run([py, "tests/run_samples.py"])
    run([py, "src/agent.py", "--demo", "--json-out", "results/demo_run.json"])
    run(
        [
            py,
            "src/agent.py",
            "--budget",
            "6000",
            "--district",
            "浦东",
            "--min-area",
            "30",
            "--max-area",
            "80",
            "--json-out",
            "results/demo_pudong.json",
        ]
    )
    print("\nALL DONE. See results/ and models/")


if __name__ == "__main__":
    main()
