"""Holdout cohort for T1, T2, and T4. Not part of the 108-run grid.

Seeds 11-14. Two signaling repetitions per bit and two utility repetitions.
72 episodes. Output stays under outputs/t4_holdout and is not pooled with
outputs/matched.
"""

from __future__ import annotations

import random
import sys
from pathlib import Path
from typing import Any, Optional

from experiments.collusion.tool_selection.run_matched import job_id, run_job

HERE = Path(__file__).resolve().parent
OUT = HERE / "outputs" / "t4_holdout"
RUNS = OUT / "runs"
MANIFEST = OUT / "manifest.jsonl"
POLICIES = ("t1", "t2", "t4")
SEEDS = (11, 12, 13, 14)
REPS = (1, 2)
ORDER_SEED = 20261027


def jobs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for rep in REPS:
        for seed in SEEDS:
            for bit in (0, 1):
                for policy in POLICIES:
                    rows.append(
                        {
                            "kind": "signal",
                            "policy": policy,
                            "seed": seed,
                            "bit": bit,
                            "rep": rep,
                        }
                    )
    for rep in REPS:
        for seed in SEEDS:
            for policy in POLICIES:
                rows.append(
                    {
                        "kind": "utility",
                        "policy": policy,
                        "seed": seed,
                        "bit": None,
                        "rep": rep,
                    }
                )
    random.Random(ORDER_SEED).shuffle(rows)
    return rows


def planned_count(rows: Optional[list[dict[str, Any]]] = None) -> int:
    return len(rows if rows is not None else jobs())


def main() -> int:
    planned = jobs()
    if planned_count(planned) != 72:
        print(f"protocol expected 72 jobs, got {len(planned)}")
        return 1
    OUT.mkdir(parents=True, exist_ok=True)
    order_path = OUT / "job_order.json"
    if not order_path.exists():
        import json

        order_path.write_text(json.dumps(planned, indent=2), encoding="utf-8")
    else:
        import json

        planned = json.loads(order_path.read_text(encoding="utf-8"))
    for index, job in enumerate(planned, start=1):
        name = job_id(job["kind"], job["policy"], job["seed"], job["rep"], job["bit"])
        print(f"{index}/{len(planned)} {name}", flush=True)
        run_job(job, RUNS, manifest=MANIFEST)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
