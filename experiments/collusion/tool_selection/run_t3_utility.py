"""Eight utility episodes for T3 on holdout seeds 11-14.

Does not rerun the 108 or the 72-episode T4 holdout. Output stays under
outputs/t3_utility. The deterministic T3-versus-T4 prompt check runs first.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from experiments.collusion.tool_selection.run_matched import job_id, run_job
from experiments.collusion.tool_selection.validate_matched import t3_t4_utility_problems

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "t3_utility"
RUNS = OUT / "runs"
MANIFEST = OUT / "manifest.jsonl"
SEEDS = (11, 12, 13, 14)
REPS = (1, 2)


def jobs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rep in REPS:
        for seed in SEEDS:
            rows.append(
                {
                    "kind": "utility",
                    "policy": "t3",
                    "seed": seed,
                    "bit": None,
                    "rep": rep,
                }
            )
    return rows


def main() -> int:
    planned = jobs()
    if len(planned) != 8:
        print(f"protocol expected 8 jobs, got {len(planned)}")
        return 1

    async def _check() -> list[str]:
        found: list[str] = []
        for seed in SEEDS:
            found.extend(await t3_t4_utility_problems(seed))
        return found

    problems = asyncio.run(_check())
    if problems:
        print("request check failed; no model call was started")
        for problem in problems:
            print(problem)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    order_path = OUT / "job_order.json"
    if not order_path.exists():
        order_path.write_text(json.dumps(planned, indent=2), encoding="utf-8")
    else:
        planned = json.loads(order_path.read_text(encoding="utf-8"))
        if len(planned) != 8:
            print(f"stored order has {len(planned)} jobs")
            return 1
    for index, job in enumerate(planned, start=1):
        name = job_id(job["kind"], job["policy"], job["seed"], job["rep"], job["bit"])
        print(f"{index}/{len(planned)} {name}", flush=True)
        run_job(job, RUNS, manifest=MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
