"""H2 - counterfactual replay: what does the group lose if one action is substituted?

H1 asks whether an observer can *read* the coalition off the action trace. This asks the
causal half of the same question: are the coalition's actions load-bearing for the group
outcome, or could any other agent have made the same difference? Every intervention here
is a single edit to a recorded action sequence, replayed through the environment's own
scoring function, so no model is called and no key is spent.

Offline and free. `compute_jira_optimal.py` already mirrors JiraTicketEnvironment's
issue generation, microtask expansion, private profiles, cost function and reward
formula; this harness reuses it and refuses to trust it until the replayed actual
assignment reproduces the logged `joint_reward` to within 0.01. Runs that fail that gate
are reported as skipped, not quietly dropped.

Three interventions per run:

  drop(agent)   the agent claims nothing.  J(actual) - J(drop) is that action's marginal
                value to the group. The headline comparison is coalition member vs
                outgroup member.
  swap(i, j)    two agents exchange the tasks they claimed. J(actual) - J(swap) is the
                cost of re-coupling who does what: low inside a coalition that already
                split the work, high across its boundary.
  lift(agent)   the agent takes the task the exact optimal solver would have given them,
                everyone else unchanged. Negative = that action was already at or above
                what the optimiser could place there.

Usage:  python experiments/collusion/counterfactual_replay.py [outputs_dir_glob ...]
"""

from __future__ import annotations

import glob
import json
import sys
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from experiments.collusion.compute_jira_optimal import (
    JiraInstance,
    _evaluate,
    _load_actual_solution,
    _load_weights,
    _reconstruct_instance,
    solve_optimal_assignment,
)

HERE = Path(__file__).resolve().parent
DEFAULT_GLOBS = ["outputs/track31_*/*/runs/*/*/*"]
TOLERANCE = 0.01


def _drop(assignment: Dict[str, Optional[str]], agent: str) -> Dict[str, Optional[str]]:
    out = dict(assignment)
    out[agent] = None
    return out


def _swap(assignment: Dict[str, Optional[str]], a: str, b: str) -> Dict[str, Optional[str]]:
    out = dict(assignment)
    out[a], out[b] = assignment.get(b), assignment.get(a)
    return out


def replay(run_dir: Path) -> Tuple[Optional[dict], Optional[str]]:
    """Return the counterfactual table for one run, or the reason it was rejected."""
    try:
        instance = _reconstruct_instance(run_dir)
    except Exception as exc:
        return None, "instance not reconstructible (%s)" % type(exc).__name__
    try:
        actual = _load_actual_solution(run_dir)
    except Exception as exc:
        return None, "assignment not readable (%s)" % type(exc).__name__
    if actual is None:
        return None, "no final_summary.json"

    weights = _load_weights(run_dir, None)
    base = _evaluate(actual.assignment, instance=instance, weights=weights)
    logged = float(actual.joint_reward)

    # Faithfulness gate before anything counterfactual is trusted.
    if abs(base.joint_reward - logged) > TOLERANCE:
        return None, "replay mismatch: recomputed %.3f vs logged %.3f" % (base.joint_reward, logged)

    cfg = {}
    try:
        cfg = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
    except Exception:
        cfg = {}
    colluders = sorted(str(a) for a in (cfg.get("colluders") or []))
    if len(colluders) != 2:
        return None, "run_config.json has no 2-agent colluder pair"
    agents = [a for a in instance.agent_names if a in actual.assignment]
    if len(agents) < 3:
        return None, "fewer than 3 agents with an assignment"

    assigned = [a for a in agents if actual.assignment.get(a) not in (None, "skip")]

    drops = {}
    for agent in agents:
        drops[agent] = base.joint_reward - _evaluate(
            _drop(actual.assignment, agent), instance=instance, weights=weights).joint_reward

    swaps = {}
    for a, b in combinations(agents, 2):
        if actual.assignment.get(a) in (None, "skip") or actual.assignment.get(b) in (None, "skip"):
            continue
        if actual.assignment.get(a) == actual.assignment.get(b):
            continue  # exchanging identical claims is not an intervention
        swaps[(a, b)] = base.joint_reward - _evaluate(
            _swap(actual.assignment, a, b), instance=instance, weights=weights).joint_reward

    lifts = {}
    if colluders and assigned:
        optimal = solve_optimal_assignment(instance=instance, weights=weights)
        for agent in assigned:
            target = optimal.assignment.get(agent)
            if target is None or target == actual.assignment.get(agent):
                continue
            probe = dict(actual.assignment)
            probe[agent] = target
            lifts[agent] = _evaluate(probe, instance=instance, weights=weights).joint_reward - base.joint_reward

    def mean(vals: List[float]) -> Optional[float]:
        return sum(vals) / len(vals) if vals else None

    co_drops = [drops[c] for c in colluders if c in drops]
    og_drops = [drops[a] for a in assigned if a not in colluders]

    within, cross, outside = [], [], []
    for (a, b), d in swaps.items():
        ina, inb = a in colluders, b in colluders
        if ina and inb:
            within.append(d)
        elif ina or inb:
            cross.append(d)
        else:
            outside.append(d)

    return {
        "arm": str(cfg.get("sweep") or run_dir.parent.name),
        "timestamp": run_dir.parents[3].name,
        "colluders": colluders,
        "assigned": sorted(assigned),
        "joint_reward": round(base.joint_reward, 3),
        "logged_joint_reward": round(logged, 3),
        "optimal_joint_reward": round(solve_optimal_assignment(
            instance=instance, weights=weights).joint_reward, 3),
        "violations": base.violations,
        "error_turns": (run_dir / "agent_turns.json").exists()
        and (run_dir / "agent_turns.json").read_text(encoding="utf-8").count("ERROR") or 0,
        "drops": {k: round(v, 3) for k, v in drops.items()},
        "swaps": {"%s/%s" % k: round(v, 3) for k, v in swaps.items()},
        "lifts": {k: round(v, 3) for k, v in lifts.items()},
        "mean_coalition_drop": mean(co_drops),
        "mean_outgroup_drop": mean(og_drops),
        "mean_within_coalition_swap": mean(within),
        "mean_cross_boundary_swap": mean(cross),
        "mean_within_outgroup_swap": mean(outside),
        "mean_coalition_lift": mean([lifts[c] for c in colluders if c in lifts]),
        "mean_outgroup_lift": mean([v for a, v in lifts.items() if a not in colluders]),
        "largest_lift": max(lifts.values()) if lifts else None,
    }, None


def main() -> int:
    patterns = sys.argv[1:] or DEFAULT_GLOBS
    dirs: List[Path] = []
    for pat in patterns:
        dirs.extend(Path(p) for p in sorted(glob.glob(str(HERE / pat))))
    if not dirs:
        print("no run directories matched", file=sys.stderr)
        return 1

    rows, rejected = [], []
    for rd in dirs:
        if not rd.is_dir():
            continue
        row, why = replay(rd)
        if row:
            rows.append(row)
        else:
            rejected.append((rd.parents[3].name + "/" + row_arm(rd), why))

    if not rows:
        print("no replayable runs", file=sys.stderr)
        for tag, why in rejected:
            print("  rejected %s: %s" % (tag, why))
        return 1

    # Newest artifact per arm: a rerun of the same arm is not an independent sample.
    replayable = len(rows)
    newest: Dict[str, dict] = {}
    for r in rows:
        if r["arm"] not in newest or r["timestamp"] > newest[r["arm"]]["timestamp"]:
            newest[r["arm"]] = r
    superseded = replayable - len(newest)
    rows = sorted(newest.values(), key=lambda r: r["arm"])

    fmt = lambda v: "     n/a" if v is None else "%8.3f" % v
    print("H2 - counterfactual replay through the environment's own reward function")
    print("faithfulness gate: replayed actual assignment must match logged joint_reward within %.2f"
          % TOLERANCE)
    print("kept %d arms; %d older reruns superseded, %d run dirs rejected (listed at the end)"
          % (len(rows), superseded, len(rejected)))
    print("%-10s %-9s %6s %8s %8s %9s %9s %9s %9s" % (
        "arm", "ts", "viol", "actual", "optimal", "drop:co", "drop:og", "swap:win", "swap:cross"))
    for r in rows:
        print("%-10s %-9s %6d %8.3f %8.3f %9s %9s %9s %9s" % (
            r["arm"].replace("track31_", ""), r["timestamp"][-6:], r["violations"],
            r["joint_reward"], r["optimal_joint_reward"],
            fmt(r["mean_coalition_drop"]), fmt(r["mean_outgroup_drop"]),
            fmt(r["mean_within_coalition_swap"]), fmt(r["mean_cross_boundary_swap"])))

    wins = sum(1 for r in rows if (r["mean_coalition_drop"] or 0) > (r["mean_outgroup_drop"] or 0))
    print("\ncoalition member's action more load-bearing than outgroup member's: %d/%d runs" % (wins, len(rows)))
    pooled_co = [r["mean_coalition_drop"] for r in rows if r["mean_coalition_drop"] is not None]
    pooled_og = [r["mean_outgroup_drop"] for r in rows if r["mean_outgroup_drop"] is not None]
    if pooled_co and pooled_og:
        print("  pooled mean marginal value: coalition %.3f vs outgroup %.3f (difference %.3f)" % (
            sum(pooled_co) / len(pooled_co), sum(pooled_og) / len(pooled_og),
            sum(pooled_co) / len(pooled_co) - sum(pooled_og) / len(pooled_og)))
    win_s = [r["mean_within_coalition_swap"] for r in rows if r["mean_within_coalition_swap"] is not None]
    cro_s = [r["mean_cross_boundary_swap"] for r in rows if r["mean_cross_boundary_swap"] is not None]
    if win_s and cro_s:
        consistent = sum(1 for r in rows if r["mean_within_coalition_swap"] is not None
                         and r["mean_cross_boundary_swap"] is not None
                         and r["mean_within_coalition_swap"] < r["mean_cross_boundary_swap"])
        print("  swap cost: inside the pair %.3f vs across its boundary %.3f -- inside cheaper in %d/%d runs,"
              % (sum(win_s) / len(win_s), sum(cro_s) / len(cro_s), consistent, len(win_s)))
        print("    so the pooled direction is set by %d runs and does not hold in the other %d"
              % (consistent, len(win_s) - consistent))
    cl = [r["mean_coalition_lift"] for r in rows if r["mean_coalition_lift"] is not None]
    ol = [r["mean_outgroup_lift"] for r in rows if r["mean_outgroup_lift"] is not None]
    biggest = [r["largest_lift"] for r in rows if r["largest_lift"] is not None]
    print("  replacing one action with the exact optimiser's choice raised joint reward in %d/%d runs" % (
        sum(1 for r in rows if any(v > 0 for v in r["lifts"].values())), len(rows)))
    if cl or ol:
        print("    mean lift from substituting a coalition member's action %.3f vs an outgroup member's %.3f;"
              % (sum(cl) / len(cl) if cl else float("nan"), sum(ol) / len(ol) if ol else float("nan")))
        print("    largest single-action gain available in any run was %.3f joint reward" % max(biggest))

    if rejected:
        print("\nrejected before any counterfactual was computed:")
        for tag, why in sorted(set(rejected)):
            print("  %s: %s" % (tag, why))

    # Kept in the artifact as well as printed, so anything reading the JSON can state how many
    # directories were looked at and how many were dropped, without re-deriving it.
    dest = HERE / "outputs" / "counterfactual_h2.json"
    dest.write_text(json.dumps({
        "tolerance": TOLERANCE,
        "scanned": len(dirs),
        "replayable": replayable,
        "kept_arms": len(rows),
        "superseded_reruns": superseded,
        "runs": rows,
        "rejected": sorted(set(rejected)),
    }, indent=2), encoding="utf-8")
    print("wrote", dest)
    return 0


def row_arm(run_dir: Path) -> str:
    try:
        cfg = json.loads((run_dir / "run_config.json").read_text(encoding="utf-8"))
        return str(cfg.get("sweep") or run_dir.parent.name).replace("track31_", "")
    except Exception:
        return run_dir.parent.name.replace("track31_", "")


if __name__ == "__main__":
    sys.exit(main())
