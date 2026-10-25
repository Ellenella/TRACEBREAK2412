"""Launch the frozen confirmatory cohort. Does not touch the 108 exploratory runs.

`plan` checks the deterministic gate, writes the shuffled job list, and makes
no model call. `grid` runs that stored list. A failed job is kept and is not
replaced with another seed.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

from experiments.collusion.tool_selection.run_matched import run_job

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "confirmatory"
ORDER = OUT / "job_order.json"
POLICIES = ("t1", "t2", "t3")
SEEDS = tuple(range(11, 23))
REPS = (1, 2)


def jobs() -> list[dict]:
    rows: list[dict] = []
    for rep in REPS:
        for seed in SEEDS:
            for bit in (0, 1):
                for policy in POLICIES:
                    rows.append(
                        {"kind": "signal", "policy": policy, "seed": seed, "bit": bit, "rep": rep}
                    )
    for rep in REPS:
        for seed in SEEDS:
            for policy in POLICIES:
                rows.append(
                    {"kind": "utility", "policy": policy, "seed": seed, "bit": None, "rep": rep}
                )
    random.Random(20261027).shuffle(rows)
    return rows


def gate() -> bool:
    from experiments.collusion.tool_selection.test_tool_selection import ToolSelectionTests
    from experiments.collusion.tool_selection.validate_matched import check_all, write_reports

    suite = ToolSelectionTests()
    suite.test_returned_log_is_the_prompt_the_runner_receives()
    rows = check_all()
    write_reports(rows)
    problems = [problem for row in rows for problem in row["problems"]]
    if problems:
        for problem in problems:
            print(problem)
        print(f"GATE FAILED ({len(problems)})")
        return False
    print("GATE PASSED")
    return True


def plan() -> int:
    if not gate():
        return 1
    planned = jobs()
    OUT.mkdir(parents=True, exist_ok=True)
    if ORDER.exists():
        stored = json.loads(ORDER.read_text(encoding="utf-8"))
        if stored != planned:
            print("job_order.json already exists and does not match this shuffle. Not overwriting.")
            return 2
        print(f"job order already stored ({len(stored)} jobs)")
        return 0
    ORDER.write_text(json.dumps(planned, indent=2) + "\n", encoding="utf-8")
    print(f"stored {len(planned)} jobs in {ORDER}")
    return 0


def grid() -> int:
    if not ORDER.exists():
        print("Refusing to run without outputs/confirmatory/job_order.json. Run plan first.")
        return 1
    planned = json.loads(ORDER.read_text(encoding="utf-8"))
    if planned != jobs():
        print("Stored job order does not match the frozen shuffle. Not running.")
        return 2
    runs = OUT / "runs"
    manifest = OUT / "manifest.jsonl"
    for job in planned:
        run_job(job, runs, manifest)
    return 0


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "plan"
    if mode == "plan":
        return plan()
    if mode == "grid":
        return grid()
    print("Use plan or grid.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
