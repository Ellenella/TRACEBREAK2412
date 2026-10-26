"""Paired S-versus-V summary for the new cohort. Does not read the printed table."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent / "outputs" / "replication"
ARMS = ("B0", "P", "V", "S", "B1")
SEEDS = (31, 32, 33, 34, 35)


def load(arm: str, seed: int) -> dict | None:
    summary_path = ROOT / f"{arm}_seed{seed}" / "job_summary.json"
    if not summary_path.exists():
        return None
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    run_dir = next(summary_path.parent.rglob("run_config.json")).parent
    config = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    requests = []
    request_path = run_dir / "model_requests.json"
    if request_path.exists():
        requests = json.loads(request_path.read_text(encoding="utf-8"))
    rewards = {row["agent_name"]: float(row["reward"]) for row in metrics["agents"]}
    return {
        "arm": arm,
        "seed": seed,
        "joint": float(summary["joint_reward"]),
        "tasks_done": int(summary["tasks_done"]),
        "violations": int(summary["violations"]),
        "coalition_mean": float(summary["coalition_mean_reward"]),
        "other_mean": float(summary["noncoalition_mean_reward"]),
        "D": float(summary["coalition_advantage_mean"]),
        "colluders": list(config["colluders"]),
        "turn_order": list(config["agent_turn_order"]),
        "rewards": rewards,
        "request_count": len(requests),
        "request_text_chars": sum(len(text) for row in requests for text in row.get("texts") or []),
        "post_message_offered": sum("post_message" in (row.get("tool_names") or []) for row in requests),
        "action_events_in_requests": sum(
            text.count("[action_executed]") for row in requests for text in row.get("texts") or []
        ),
    }


def main() -> None:
    rows = []
    missing = []
    for seed in SEEDS:
        for arm in ARMS:
            row = load(arm, seed)
            if row is None:
                missing.append(f"{arm}_seed{seed}")
            else:
                rows.append(row)
    pairs = []
    by_key = {(row["arm"], row["seed"]): row for row in rows}
    for seed in SEEDS:
        s, v = by_key.get(("S", seed)), by_key.get(("V", seed))
        if not s or not v:
            continue
        coal = s["coalition_mean"] - v["coalition_mean"]
        other = s["other_mean"] - v["other_mean"]
        pairs.append(
            {
                "seed": seed,
                "D_S": s["D"],
                "D_V": v["D"],
                "delta_D": s["D"] - v["D"],
                "coalition_change": coal,
                "other_change": other,
                "identity": (s["D"] - v["D"]) - (coal - other),
                "joint_change": s["joint"] - v["joint"],
                "tasks_S": s["tasks_done"],
                "tasks_V": v["tasks_done"],
                "violations_S": s["violations"],
                "violations_V": v["violations"],
            }
        )
    out = {"episodes": rows, "pairs": pairs, "missing": missing}
    dest = ROOT / "analysis.json"
    dest.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({"n": len(rows), "pairs": len(pairs), "missing": missing}, indent=2))


if __name__ == "__main__":
    main()
