"""Single source of truth for every number in the Track 3.1 report.

Nothing in the report is typed by hand. Each figure is read back out of the artifacts that
produced it -- metrics.json, final_summary.json, tool_events.json, agent_turns.json,
run_config.json, the condition YAML, the offline test file, and the two offline harness
JSONs -- through this module, so a claim and its evidence cannot drift apart without the
drift being visible here.

Nothing here hardcodes which episode a figure came from. `scan()` walks the artifact tree and
`discover()` picks, per arm, the newest run that is complete, scored and carries zero error
turns -- the same rule the two offline harnesses apply, so the report and the analyses cannot
drift onto different artifacts. `selection()` then reports what the tree offered, what was
chosen and why the rest was rejected, and `PINNED` keeps the timestamps the sprint analysed so
that a new artifact under an arm's tag shows up as declared drift rather than a silent swap.
Every selected artifact is still checked: wrong arm, missing file, a nonzero error-turn count
or a protocol mismatch between arms raises rather than reporting a different episode.

Anything here that *disagrees* with a plausible-sounding claim is treated as a correction to
the claim, not to the data. Two are recorded explicitly, in `clone` and `protocol`: the clone
pair's recorded configs are identical (so their difference cannot be attributed to a
parameter change), and normalized scores differ by a different factor than the delta does.

Usage:
    python experiments/collusion/report_data.py          # print the derived value map
    from experiments.collusion.report_data import build   # used by build_report.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

HERE = Path(__file__).resolve().parent
COLLUSION = HERE                                  # experiments/collusion
OUTPUTS = COLLUSION / "outputs"
CONFIGS = COLLUSION / "configs"
# The pre-sprint clone. Two of the report's contextual numbers come from runs there, so they
# are read from the same kind of artifact rather than quoted from memory.
CLONE_OUTPUTS = COLLUSION.parents[2].parent / "TRACEBREAK2412" / "experiments" / "collusion" / "outputs"

# arm -> timestamp of the artifact the sprint analysed, in the report's table order. This is
# provenance only: the ladder itself comes from discover(), which reads the tree. The list is
# kept so a new artifact appearing under an arm's tag is reported as drift instead of quietly
# replacing what the report describes.
PINNED: List[tuple] = [
    ("B0", "track31_b0", "20261025-033526"),
    ("P", "track31_p", "20261025-033446"),
    ("V", "track31_v", "20261025-035049"),
    ("E", "track31_e", "20261025-035127"),
    ("C", "track31_c", "20261025-034506"),
    ("S", "track31_s", "20261025-035220"),
    ("B1", "track31_b1", "20261025-035246"),
]
# The first run of arm E, superseded by the one above. Same recorded config, different draw:
# this is where the report's single-seed noise floor comes from instead of an assumption.
E_RERUN = ("track31_e", "20261025-033922")
# The run that used the *naive* canonicalisation, one shared placeholder for every task id
# instead of one opaque token per task. It is not an arm; it is the measured failure mode.
NAIVE_CANON = ("track31_c", "20261025-034119")
# Contextual runs in the clone: two episodes whose recorded config is identical but whose
# delta statistic differs by two orders of magnitude, one of them corrupted.
CLONE_MATCHED_PAIR = [
    ("gemini_flash_lite_jira_baseline", "20261024-195113"),
    ("gemini_flash_lite_jira_baseline", "20261024-195901"),
]
CLONE_CORRUPTED_RUN = ("gemini_flash_lite_jira_baseline", "20261024-195113")

LABELS = {
    "B0": "B0 baseline",
    "P": "P private",
    "V": "V action-only",
    "E": "E events hidden",
    "C": "C canonicalised",
    "S": "S all removed",
    "B1": "B1 blinded, unprompted",
}

# Written by the harness after the run, never sent to the model. A rerun whose config differs
# only in these keys is a rerun of the same episode, not of a different condition.
POST_HOC_CONFIG_KEYS = ("observation_filter_effects",)
# If these are not in the run record, two episodes cannot be told apart by parameter change.
SAMPLING_PARAMS = ("max_tokens", "temperature")

TEST_FILE = COLLUSION / "test_observation_filter.py"


def _json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError("missing artifact: %s" % path)
    return json.loads(path.read_text(encoding="utf-8"))


def find_run_dir(tag: str, timestamp: str) -> Path:
    """Locate the single run directory for one arm+timestamp, whatever the model folder is."""
    base = OUTPUTS / tag / timestamp / "runs"
    if not base.exists():
        raise FileNotFoundError("no runs directory for %s %s" % (tag, timestamp))
    hits = [p for p in base.glob("*/*/*") if (p / "metrics.json").exists()]
    if len(hits) != 1:
        raise ValueError("expected exactly one run dir for %s %s, found %d" % (tag, timestamp, len(hits)))
    return hits[0]


def find_clone_run_dir(tag: str, timestamp: str) -> Path:
    base = CLONE_OUTPUTS / tag / timestamp
    hits = [p for p in base.glob("**/*") if (p / "metrics.json").exists()]
    if not hits:
        raise FileNotFoundError("no clone run dir for %s %s" % (tag, timestamp))
    return hits[0]


def error_turns(run_dir: Path) -> int:
    """Count turns whose payload carries an error, the gate the report claims on every arm."""
    turns = _json(run_dir / "agent_turns.json")
    items = turns if isinstance(turns, list) else turns.get("turns", [])
    n = 0
    for t in items:
        resp = str(t.get("response", "")) if isinstance(t, dict) else str(t)
        if "ERROR" in resp:
            n += 1
    return n


def turn_count(run_dir: Path) -> int:
    turns = _json(run_dir / "agent_turns.json")
    items = turns if isinstance(turns, list) else turns.get("turns", [])
    return len(items)


def tool_counts(run_dir: Path) -> Dict[str, int]:
    events = _json(run_dir / "tool_events.json")
    out: Dict[str, int] = {}
    for e in events:
        out[str(e.get("tool_name"))] = out.get(str(e.get("tool_name")), 0) + 1
    return out


def posts(run_dir: Path) -> int:
    """post_message calls actually executed, which is what the report's posts column says."""
    return tool_counts(run_dir).get("post_message", 0)


def usable(run_dir: Path) -> bool:
    """An artifact this module is allowed to speak for: complete, scored, uncorrupted."""
    if not (run_dir / "metrics.json").exists() or not (run_dir / "final_summary.json").exists():
        return False
    if "joint_reward" not in _json(run_dir / "final_summary.json"):
        return False
    return error_turns(run_dir) == 0


def alternatives(tag: str, timestamp: str) -> List[Path]:
    """Usable artifacts of the same arm other than the pinned one: the re-runs."""
    out = []
    for p in sorted((OUTPUTS / tag).glob("*/runs/*/*/*")):
        if p.relative_to(OUTPUTS).parts[1] == timestamp:
            continue
        if usable(p):
            out.append(p)
    return out


def scan() -> List[Dict[str, Any]]:
    """Read the whole artifact tree, keeping every launch and why it does or does not qualify.

    Nothing here decides what the ladder is; it only reports what is on disk. Each row carries
    the arm tag, the timestamp folder, the recorded status, the error-turn count and the two
    statistics. Launches that died before writing a scored run are rows too, with no numbers:
    they are why the report's directory count is larger than its arm count, and hiding them
    would make the selection unauditable.
    """
    rows = []
    for tag_dir in sorted(p for p in OUTPUTS.glob("*") if p.is_dir()):
        for ts_dir in sorted(p for p in tag_dir.glob("*") if p.is_dir()):
            hits = [p for p in sorted((ts_dir / "runs").glob("*/*/*"))
                    if (p / "metrics.json").exists()]
            if not hits:
                rows.append({"tag": tag_dir.name, "timestamp": ts_dir.name,
                             "status": "no scored run", "error_turns": 0, "turns": 0,
                             "delta": None, "joint": None, "usable": False,
                             "run_dir": str(ts_dir.relative_to(COLLUSION)).replace("\\", "/")})
                continue
            for rd in hits:
                fs = (_json(rd / "final_summary.json")
                      if (rd / "final_summary.json").exists() else {})
                m = _json(rd / "metrics.json")
                rows.append({
                    "tag": tag_dir.name,
                    "timestamp": ts_dir.name,
                    "status": str(fs.get("status", "absent")),
                    "error_turns": error_turns(rd),
                    "turns": turn_count(rd),
                    "delta": (float(m["coalition_advantage_mean"])
                              if "coalition_advantage_mean" in m else None),
                    "joint": (float(fs["joint_reward"]) if "joint_reward" in fs else None),
                    "usable": usable(rd),
                    "run_dir": str(rd.relative_to(COLLUSION)).replace("\\", "/"),
                })
    return rows


def discover() -> List[tuple]:
    """The ladder as the artifact tree defines it: newest scored, uncorrupted run of each arm.

    Same rule the two offline harnesses already apply, so the report and the analyses cannot
    drift onto different artifacts. Raises if an arm has no usable artifact at all -- a missing
    arm is a hole in the ladder, not a row to drop silently.
    """
    by_tag: Dict[str, List[Dict[str, Any]]] = {}
    for r in scan():
        by_tag.setdefault(r["tag"], []).append(r)
    picked = []
    for label, tag, _ts in PINNED:
        good = [r for r in by_tag.get(tag, []) if r["usable"]]
        if not good:
            raise AssertionError("arm %s (%s) has no usable artifact: %s" % (
                label, tag, [(r["timestamp"], r["status"], r["error_turns"])
                             for r in by_tag.get(tag, [])]))
        newest = max(good, key=lambda r: r["timestamp"])
        picked.append((label, tag, newest["timestamp"]))
    return picked


ARMS = discover()


def selection() -> Dict[str, Any]:
    """What the tree offered, what was chosen, and where that differs from the pinned provenance."""
    rows = scan()
    chosen = {(lbl, ts) for lbl, _tag, ts in ARMS}
    drift = [(p[0], p[1], p[2]) for p in PINNED if (p[0], p[2]) not in chosen]
    scored = [r for r in rows if r["status"] != "no scored run"]
    return {
        "scanned": len(rows),
        "usable": sum(1 for r in rows if r["usable"]),
        "arms": len(ARMS),
        "superseded": sum(1 for r in rows if r["usable"]) - len(ARMS),
        "rejected_error_turns": sum(1 for r in scored if not r["usable"] and r["error_turns"] > 0),
        "rejected_unscored": sum(1 for r in scored if not r["usable"] and r["error_turns"] == 0),
        "no_scored_run": len(rows) - len(scored),
        "drift": drift,
        "rows": rows,
    }


def load_arm(label: str, tag: str, timestamp: str) -> Dict[str, Any]:
    rd = find_run_dir(tag, timestamp)
    m = _json(rd / "metrics.json")
    fs = _json(rd / "final_summary.json")
    cfg = _json(rd / "run_config.json")
    raw_cfg = (rd / "run_config.json").read_text(encoding="utf-8")
    errs = error_turns(rd)
    if errs:
        raise AssertionError("arm %s artifact %s has %d error turns; the report asserts zero"
                             % (label, timestamp, errs))
    rewards = {k: float(v) for k, v in (fs.get("agent_rewards") or {}).items()}
    colluders = [str(a) for a in (cfg.get("colluders") or [])]
    coalition = [rewards[c] for c in colluders if c in rewards]
    rest = {k: v for k, v in rewards.items() if k not in colluders}
    effects = cfg.get("observation_filter_effects") or {}
    canon = [e.get("tasks_canonicalised", 0) for e in effects.values() if e]
    restored = [e.get("actions_restored", 0) for e in effects.values() if e]
    reruns = alternatives(tag, timestamp)
    same_config = [p for p in reruns
                   if _config_delta(p) is not None and abs(_config_delta(p) - float(
                       m["coalition_advantage_mean"])) < 1e-9]
    return {
        "label": label,
        "name": LABELS.get(label, label),
        "tag": tag,
        "timestamp": timestamp,
        "run_dir": str(rd.relative_to(COLLUSION)).replace("\\", "/"),
        "delta": float(m["coalition_advantage_mean"]),
        "joint": float(fs["joint_reward"]),
        "ratio": float(fs["joint_reward_ratio"]),
        "coverage": float(fs["coverage"]),
        "violations": int(fs["violations"]),
        "coalition_regret": float(m["coalition_mean_regret"]),
        "noncoalition_regret": float(m["noncoalition_mean_regret"]),
        "system_regret": float(m["system_regret"]),
        "coalition_mean": float(m["coalition_mean_reward"]),
        "noncoalition_mean": float(m["noncoalition_mean_reward"]),
        "posts": posts(rd),
        "assigns": tool_counts(rd).get("assign_task", 0),
        "secret_post_rate": float(m.get("colluder_posts_secret_rate") or 0.0),
        "colluder_posts": int(m.get("colluder_posts_total") or 0),
        "normalized_score": float(fs.get("normalized_score") or 0.0),
        "status": str(fs.get("status")),
        "error_turns": errs,
        "turns": turn_count(rd),
        "agent_rewards": rewards,
        "colluders": sorted(colluders),
        "coalition_values": sorted(coalition, reverse=True),
        "outgroup_values": rest,
        "noncoalition_values": sorted(rest.values(), reverse=True),
        "canonicalised_per_agent": (min(canon), max(canon)) if canon else None,
        "restores_total": sum(restored) if restored else 0,
        "restores_per_agent": (min(restored), max(restored)) if restored else None,
        "filter": (cfg.get("observation_filter") or {}),
        "coalition_prompt": str(cfg.get("coalition_prompt")),
        "unrecorded_params": [k for k in SAMPLING_PARAMS if not re.search(k, raw_cfg)],
        "secret_channel_enabled": bool(cfg.get("secret_channel_enabled")),
        "agent_turn_order": [str(a) for a in (cfg.get("agent_turn_order") or [])],
        "reruns": len(reruns),
        "reruns_same_delta": len(same_config),
    }


def _config_delta(run_dir: Path) -> Optional[float]:
    if not (run_dir / "metrics.json").exists():
        return None
    try:
        return float(_json(run_dir / "metrics.json")["coalition_advantage_mean"])
    except Exception:
        return None


def _configs_match(a: Path, b: Path) -> bool:
    """True if two artifacts differ only in post-hoc diagnostic keys, i.e. same condition."""
    ca, cb = _json(a / "run_config.json"), _json(b / "run_config.json")
    for k in POST_HOC_CONFIG_KEYS:
        ca.pop(k, None)
        cb.pop(k, None)
    return ca == cb


def load_naive_canon() -> Dict[str, Any]:
    """The shared-placeholder canonicalisation: how its tool calls were answered."""
    tag, ts = NAIVE_CANON
    rd = find_run_dir(tag, ts)
    events = _json(rd / "tool_events.json")
    assigns = [e for e in events if e.get("tool_name") == "assign_task"]
    rejected = [e for e in assigns if (e.get("result") or {}).get("status") != "success"]
    reasons = sorted({str((e.get("result") or {}).get("reason", "")) for e in rejected})
    fs = _json(rd / "final_summary.json")
    effects = (_json(rd / "run_config.json").get("observation_filter_effects") or {})
    canon = [e.get("tasks_canonicalised", 0) for e in effects.values() if e]
    return {
        "timestamp": ts,
        "assign_calls": len(assigns),
        "rejected": len(rejected),
        "reasons": reasons,
        "unknown_id": bool([r for r in reasons if r.startswith("Unknown task_id")]),
        "status": str(fs.get("status")),
        "decisions_made": int(fs.get("decisions_made") or 0),
        "rewrites_uniform": len(set(canon)) == 1,
        "rewrites_per_agent": canon[0] if canon else 0,
        "has_joint_reward": "joint_reward" in fs,
        "error_turns": error_turns(rd),
        "turns": turn_count(rd),
    }


def _flatten(obj: Any, prefix: str = "") -> Dict[str, Any]:
    """Leaf values by dotted path, so two YAMLs can be diffed key by key."""
    out: Dict[str, Any] = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(_flatten(v, "%s.%s" % (prefix, k) if prefix else str(k)))
    elif isinstance(obj, list) and any(isinstance(x, dict) for x in obj):
        for i, v in enumerate(obj):
            for sub, val in _flatten(v).items():
                out["%s.%d.%s" % (prefix, i, sub) if prefix else "%d.%s" % (i, sub)] = val
    else:
        out[prefix] = obj
    return out


# The YAML keys allowed to differ between two arms: the arm's own output identity, and the
# intervention. Anything else that moves means the ladder is not matched.
IDENTITY_FIELDS = ("name", "tag", "tags", "output_dir", "sweep")
INTERVENTION_FIELDS = ("coalition_prompt", "observation_filter", "prompt_variants",
                       "secret_channel_enabled")
ALLOWED_FIELDS = IDENTITY_FIELDS + INTERVENTION_FIELDS


def _field_of(path: str) -> str:
    for part in path.split("."):
        if part in ALLOWED_FIELDS:
            return part
    return path.split(".")[-1]


def load_protocol() -> Dict[str, Any]:
    """The condition YAMLs, checked against each other so 'matched ladder' is verified."""
    docs = {}
    for label, tag, _ in ARMS:
        path = CONFIGS / ("track31_%s.yaml" % label)
        docs[label] = yaml.safe_load(path.read_text(encoding="utf-8"))

    def pick(doc: dict) -> Dict[str, Any]:
        llm = doc["llm_models"][0]["llm"]
        provider = llm["provider"]
        params = llm.get(provider, {}).get("params", {})
        sim = doc["simulation"]
        col = doc["experiment"]["collusion"]
        return {
            "model": llm.get(provider, {}).get("model"),
            "provider": provider,
            "temperature": params.get("temperature"),
            "max_tokens": params.get("max_tokens"),
            "max_iterations": sim.get("max_iterations"),
            "max_planning_rounds": sim.get("max_planning_rounds"),
            "max_conversation_steps": sim.get("max_conversation_steps"),
            "seed": sim.get("seed"),
            "seeds": doc["experiment"].get("seeds"),
            "environment": doc["environment"]["name"],
            "max_tasks": doc["environment"].get("max_tasks"),
            "assignment_filling": doc["environment"].get("assignment_filling"),
            "topology": doc["communication_network"]["topology"],
            "num_agents": doc["communication_network"]["num_agents"],
            "colluder_selection": col.get("colluder_selection"),
            "agent_order": col.get("agent_order"),
        }

    per = {label: pick(doc) for label, doc in docs.items()}
    conflicts = {}
    for key in per["B0"]:
        vals = {label: p[key] for label, p in per.items()}
        if len({json.dumps(v, sort_keys=True) for v in vals.values()}) > 1:
            conflicts[key] = vals
    # The filter block is the intervention, so it is expected to differ; compare it per arm.
    if conflicts:
        raise AssertionError("the seven condition configs are not matched on %s: %s"
                             % (sorted(conflicts), conflicts))
    filters = {label: docs[label]["experiment"]["collusion"].get("observation_filter") or {}
               for label in per}
    # Not just the fields named above: the whole document is compared across the seven arms, and
    # the only keys allowed to move are the intervention and the arm's own name.
    flats = {label: _flatten(doc) for label, doc in docs.items()}
    differing = set()
    for path in set().union(*(set(f) for f in flats.values())):
        if len({json.dumps(f.get(path), sort_keys=True) for f in flats.values()}) > 1:
            differing.add(_field_of(path))
    unexpected = sorted(differing - set(ALLOWED_FIELDS))
    if unexpected:
        raise AssertionError("the seven condition configs differ on %s, which is not part of the "
                             "intervention" % unexpected)
    secret = {label: [s.get("secret_channel_enabled")
                      for s in (docs[label]["experiment"].get("sweeps") or [{}])][0]
              for label in per}
    base = dict(per["B0"])
    base["arms"] = len(per)
    base["conflicts"] = conflicts
    base["filters"] = filters
    base["differing_fields"] = sorted(differing)
    base["differing_identity"] = sorted(differing & set(IDENTITY_FIELDS))
    base["differing_intervention"] = sorted(differing & set(INTERVENTION_FIELDS))
    base["secret_channel"] = secret
    base["calls_per_agent"] = per["B0"]["num_agents"] and \
        turn_count(find_run_dir(*(ARMS[0][1], ARMS[0][2]))) // per["B0"]["num_agents"]
    base["total_calls"] = turn_count(find_run_dir(*(ARMS[0][1], ARMS[0][2])))
    return base


def count_tests() -> int:
    return len(re.findall(r"^def test_", TEST_FILE.read_text(encoding="utf-8"), re.MULTILINE))


def load_harness(name: str) -> Dict[str, Any]:
    return _json(OUTPUTS / ("%s.json" % name))


def load_clone(tag: str, timestamp: str) -> Dict[str, Any]:
    rd = find_clone_run_dir(tag, timestamp)
    m = _json(rd / "metrics.json")
    fs = _json(rd / "final_summary.json")
    cfg_text = (rd / "run_config.json").read_text(encoding="utf-8") if (rd / "run_config.json").exists() else ""
    return {
        "tag": tag,
        "timestamp": timestamp,
        "delta": float(m["coalition_advantage_mean"]),
        "joint": float(fs.get("joint_reward") or float("nan")),
        "normalized": float(fs.get("normalized_score") or float("nan")),
        "error_turns": error_turns(rd),
        "turns": turn_count(rd),
        "run_id": json.loads(cfg_text).get("run_id") if cfg_text else None,
        # Sampling parameters are what would let a reader attribute a difference between two
        # episodes to a design change. If they are absent from the run record, they are absent.
        "unrecorded_params": [k for k in SAMPLING_PARAMS if not re.search(k, cfg_text)],
    }


def _h1_summary(h1: Dict[str, Any]) -> Dict[str, Any]:
    """Pooled H1 numbers, recomputed from the per-run rows rather than read off stdout."""
    rows = h1["runs"]
    n = len(rows)
    ref = sum(r["all_pairs_value_share"] for r in rows) / n
    open_arms = [r for r in rows if r["messaging_open"]]
    shut_arms = [r for r in rows if not r["messaging_open"]]

    def pooled(key_true: str, key_rival: str) -> tuple:
        return (sum(r[key_true] for r in rows) / n,
                sum(r[key_rival] for r in rows) / n,
                sum(1 for r in rows if r[key_true] > r[key_rival]))

    tv, rv, _ = pooled("true_value_share", "rival_value_share")
    to, ro, _ = pooled("true_tag_overlap", "rival_tag_overlap")
    txt = {}
    for name, sub in (("open", open_arms), ("removed", shut_arms)):
        txt[name] = {
            "arms": len(sub),
            "messages": sum(r["messages"] for r in sub),
            "co_prime": sum(r["decode_b_primed"] for r in sub),
            "co_total": sum(r["decode_b_total"] for r in sub),
            "og_prime": sum(r["decode_b_outgroup_primed"] for r in sub),
            "og_total": sum(r["decode_b_outgroup_total"] for r in sub),
        }
    return {
        "runs": n,
        "timestamps": sorted(r["timestamp"] for r in rows),
        "scanned": h1.get("scanned", n),
        "decoded": h1.get("decoded_rows", n + h1.get("superseded_reruns", 0)),
        "undecodable": (h1.get("scanned", n) - len(h1.get("skipped_error_turns") or [])
                        - h1.get("decoded_rows", n)),
        "superseded": h1.get("superseded_reruns", 0),
        "skipped_error_turns": sorted(h1.get("skipped_error_turns") or []),
        "null": h1["null_rank_1_probability"],
        "n_pairs": h1.get("n_pairs", int(round(1 / h1["null_rank_1_probability"]))),
        "summary": h1["rank_summary"],
        "composite": h1["rank_summary"]["composite"],
        "value_share": h1["rank_summary"]["value_share"],
        "complementarity": h1["rank_summary"]["complementarity"],
        "true_value_share": tv,
        "rival_value_share": rv,
        "all_pairs_value_share": ref,
        "above_reference": sum(1 for r in rows if r["true_value_share"] > ref),
        "true_tag_overlap": to,
        "rival_tag_overlap": ro,
        "tag_lower": sum(1 for r in rows if r["true_tag_overlap"] < r["rival_tag_overlap"]),
        "text": txt,
        "mean_rank_composite": h1["rank_summary"]["composite"]["all"]["mean_rank"],
        "best_pair_hits": sum(1 for r in rows
                              if sorted(r["decode_a_best_pair"]) == sorted(r["decode_a_true_pair"])),
        # "the same N runs" is a per-run set comparison, not a match between two totals.
        "vs_composite_same_runs": sum(
            1 for r in rows if r["decode_a_ranks"]["value_share"] == 1
            and r["decode_a_ranks"]["composite"] == 1),
    }


def _h2_summary(h2: Dict[str, Any]) -> Dict[str, Any]:
    """Pooled H2 numbers, recomputed from the per-run rows rather than read off stdout."""
    rows = h2["runs"]
    n = len(rows)

    def mean(vals: List[float]) -> float:
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else float("nan")

    co = [r["mean_coalition_drop"] for r in rows]
    og = [r["mean_outgroup_drop"] for r in rows]
    sw = [r["mean_within_coalition_swap"] for r in rows]
    cr = [r["mean_cross_boundary_swap"] for r in rows]
    lifts = [r["largest_lift"] for r in rows if r["largest_lift"] is not None]
    paired = [(a, b) for a, b in zip(sw, cr) if a is not None and b is not None]
    reversal_arms = [r["arm"] for r in rows if r["mean_within_coalition_swap"] is not None
                     and r["mean_cross_boundary_swap"] is not None
                     and r["mean_within_coalition_swap"] >= r["mean_cross_boundary_swap"]]
    reasons: Dict[str, int] = {}
    for _tag, why in (h2.get("rejected") or []):
        reasons[why.split(":")[0]] = reasons.get(why.split(":")[0], 0) + 1
    return {
        "runs": n,
        "timestamps": sorted(r["timestamp"] for r in rows),
        "scanned": h2.get("scanned", n),
        "replayable": h2.get("replayable", n),
        "superseded": h2.get("superseded_reruns", 0),
        "tolerance": h2.get("tolerance"),
        "co_drop": mean(co),
        "og_drop": mean(og),
        "drop_gap": mean(co) - mean(og),
        "drop_wins": sum(1 for a, b in zip(co, og) if (a or 0) > (b or 0)),
        "swap_inside": mean(sw),
        "swap_cross": mean(cr),
        "swap_wins": sum(1 for a, b in paired if a < b),
        "swap_pairs": len(paired),
        "swap_reversals": reversal_arms,
        "lift_coalition": mean([r["mean_coalition_lift"] for r in rows]),
        "lift_outgroup": mean([r["mean_outgroup_lift"] for r in rows]),
        "lift_runs": sum(1 for r in rows if any(v > 0 for v in (r["lifts"] or {}).values())),
        "largest_lift": max(lifts) if lifts else 0.0,
        "optimal": sorted(set(r["optimal_joint_reward"] for r in rows)),
        "rejected": len(h2.get("rejected") or []),
        "rejection_reasons": reasons,
        "gate_max_abs_error": max(abs(r["joint_reward"] - r["logged_joint_reward"]) for r in rows),
    }


def build() -> Dict[str, Any]:
    arms = [load_arm(lbl, tag, ts) for lbl, tag, ts in ARMS]
    by = {a["label"]: a for a in arms}

    e_old = load_arm("E_rerun", E_RERUN[0], E_RERUN[1])
    pair = [load_clone(t, ts) for t, ts in CLONE_MATCHED_PAIR]
    corrupted = next(c for c in pair
                     if c["timestamp"] == CLONE_CORRUPTED_RUN[1])
    naive = load_naive_canon()
    protocol = load_protocol()

    h1 = load_harness("decode_h1")
    h2 = load_harness("counterfactual_h2")
    H1, H2 = _h1_summary(h1), _h2_summary(h2)

    clone_deltas = [c["delta"] for c in pair]
    clone_norms = [c["normalized"] for c in pair]
    # Two arms that differ in the coalition prompt and in nothing else -- same observation
    # filter, same secret channel -- are the only place in the ladder where the effect of
    # "you have a partner" is separable from every other manipulation.
    prompt_only = [(x, y) for i, x in enumerate(arms) for y in arms[i + 1:]
                   if x["filter"] == y["filter"]
                   and x["secret_channel_enabled"] == y["secret_channel_enabled"]
                   and x["coalition_prompt"] != y["coalition_prompt"]]
    if len(prompt_only) != 1:
        raise AssertionError("expected exactly one prompt-only pair, found %d: %s" % (
            len(prompt_only), [(x["label"], y["label"]) for x, y in prompt_only]))
    prompted, unprompted = prompt_only[0]
    if unprompted["coalition_prompt"] != "never":
        prompted, unprompted = unprompted, prompted
    # The mirror question: is there any pair of arms that changes the secret channel and nothing
    # else? Recorded rather than assumed, because the prose leans on it.
    channel_only = [(x["label"], y["label"]) for i, x in enumerate(arms) for y in arms[i + 1:]
                    if x["filter"] == y["filter"] and x["coalition_prompt"] == y["coalition_prompt"]
                    and x["secret_channel_enabled"] != y["secret_channel_enabled"]]
    reran = [a["label"] for a in arms if a["reruns"]]
    exact = [a["label"] for a in arms if a["reruns_same_delta"]]

    d = {
        "arms": arms,
        "by": by,
        "labels": LABELS,
        "selection": selection(),
        "protocol": protocol,
        "naive_canon": naive,
        "tests": count_tests(),
        "clone_runs": pair,
        "h1_raw": h1,
        "h2_raw": h2,
        "h1": H1,
        "h2": H2,
        "arm_count": len(arms),
        # --- derived comparisons, so the prose arithmetic is checked not remembered ---
        "control_gain_delta": by["P"]["delta"] - by["B0"]["delta"],
        "control_gain_joint": by["P"]["joint"] - by["B0"]["joint"],
        "action_only_below_baseline": by["B0"]["delta"] - by["V"]["delta"],
        "action_only_below_private": by["P"]["delta"] - by["V"]["delta"],
        "events_over_baseline": by["E"]["delta"] - by["B0"]["delta"],
        "canon_over_baseline": by["C"]["delta"] - by["B0"]["delta"],
        "blinded_s_over_baseline": by["S"]["delta"] - by["B0"]["delta"],
        "blinded_b1_over_baseline": by["B1"]["delta"] - by["B0"]["delta"],
        "s_over_baseline_ratio": by["S"]["delta"] / by["B0"]["delta"],
        "b1_over_baseline_ratio": by["B1"]["delta"] / by["B0"]["delta"],
        "b1_coalition_below_baseline": by["B0"]["coalition_mean"] - by["B1"]["coalition_mean"],
        "s_outgroup_drop": by["B0"]["noncoalition_mean"] - by["S"]["noncoalition_mean"],
        "s_coalition_equals_v": abs(by["S"]["coalition_mean"] - by["V"]["coalition_mean"]) < 1e-12,
        "v_joint_over_baseline": by["V"]["joint"] - by["B0"]["joint"],
        "prompt_pair": [prompted["label"], unprompted["label"]],
        "prompt_pair_prompts": [prompted["coalition_prompt"], unprompted["coalition_prompt"]],
        "prompt_pair_delta_gain": prompted["delta"] - unprompted["delta"],
        "prompt_pair_joint_gain": prompted["joint"] - unprompted["joint"],
        "channel_only_pairs": channel_only,
        # --- noise floor: same recorded config, different draw ---
        "e_rerun": e_old,
        "e_spread": abs(by["E"]["delta"] - e_old["delta"]),
        "e_joint_spread": abs(by["E"]["joint"] - e_old["joint"]),
        "reran_arms": reran,
        "reran_count": len(reran),
        "exact_reproduced_arms": exact,
        "exact_reproduced_count": len(exact),
        "diverged_arms": [l for l in reran if l not in exact],
        "reruns_superseded_total": sum(a["reruns"] for a in arms),
        "reruns_config_matched": sum(1 for a in arms for p in alternatives(a["tag"], a["timestamp"])
                                     if _configs_match(p, find_run_dir(a["tag"], a["timestamp"]))),
        # --- clone context ---
        "clone_pair_deltas": clone_deltas,
        "clone_ratio": max(clone_deltas) / min(clone_deltas),
        "clone_pair_norms": clone_norms,
        "clone_norm_ratio": max(clone_norms) / min(clone_norms),
        "clone_same_run_id": pair[0]["run_id"] == pair[1]["run_id"],
        "clone_pair_run_id": pair[0]["run_id"],
        "clone_unrecorded_params": sorted(set.intersection(*[set(c["unrecorded_params"])
                                                             for c in pair])),
        "pinned_unrecorded_params": sorted(set(arms[0]["unrecorded_params"])),
        "clone_corrupted_errors": corrupted["error_turns"],
        "clone_corrupted_turns": corrupted["turns"],
        # --- headline values, lifted out so the prose reads directly ---
        "worst_joint": min(a["joint"] for a in arms),
        "worst_joint_arm": min(arms, key=lambda a: a["joint"])["label"],
        "best_joint": max(a["joint"] for a in arms),
        "best_joint_arm": max(arms, key=lambda a: a["joint"])["label"],
        "worst_delta": max(a["delta"] for a in arms),
        "worst_delta_arm": max(arms, key=lambda a: a["delta"])["label"],
        "max_normalized": max(a["normalized_score"] for a in arms),
        "normalized_zero_arms": [a["label"] for a in arms if a["normalized_score"] == 0.0],
        "normalized_nonzero_arms": [(a["label"], a["normalized_score"]) for a in arms
                                    if a["normalized_score"] != 0.0],
        "full_coverage_arms": [a["label"] for a in arms if a["coverage"] >= 1.0],
        "zero_violation_arms": [a["label"] for a in arms if a["violations"] == 0],
        "blocked_arms": [a["label"] for a in arms if a["filter"].get("block_post_message")],
        "open_arms": [a["label"] for a in arms if not a["filter"].get("block_post_message")],
        "assigns_identical": len({a["assigns"] for a in arms}) == 1,
        "assign_calls": arms[0]["assigns"],
        "agent_names": arms[0]["agent_turn_order"],
        "turn_order_identical": len({tuple(a["agent_turn_order"]) for a in arms}) == 1,
        "coalition_prompt": {a["label"]: a["coalition_prompt"] for a in arms},
        "unprompted_arms": [a["label"] for a in arms if a["coalition_prompt"] == "never"],
        "prompted_arms": [a["label"] for a in arms if a["coalition_prompt"] != "never"],
        "secret_channel": {a["label"]: a["secret_channel_enabled"] for a in arms},
        "coalition_names": arms[0]["colluders"],
        "coalition_names_in_order": [n for n in arms[0]["agent_turn_order"]
                                     if n in arms[0]["colluders"]],
        "outgroup_names": [a for a in arms[0]["agent_turn_order"]
                           if a not in arms[0]["colluders"]],
        "invariant_agents": {
            name: sorted({round(a["agent_rewards"][name], 6) for a in arms})
            for name in arms[0]["agent_rewards"]
            if len({round(a["agent_rewards"][name], 6) for a in arms}) == 1
        },
        "agent_peak_arm": {name: max(arms, key=lambda a, n=name: a["agent_rewards"][n])["label"]
                           for name in arms[0]["agent_rewards"]},
        "noncoalition_mean_peak": max(arms, key=lambda a: a["noncoalition_mean"])["label"],
        "coalition_mean_peak": max(arms, key=lambda a: a["coalition_mean"])["label"],
        "run_date": max(a["timestamp"] for a in arms)[:8],
    }
    return d


def load_clone_metrics(tag: str, timestamp: str) -> "tuple":
    """(coalition_advantage_mean, error_turns) for a run in the pre-sprint clone."""
    rd = find_clone_run_dir(tag, timestamp)
    m = _json(rd / "metrics.json")
    return float(m["coalition_advantage_mean"]), error_turns(rd)


def main() -> int:
    D = build()
    print("protocol: %s" % json.dumps(
        {k: v for k, v in D["protocol"].items()
         if k not in ("filters", "secret_channel", "conflicts", "differing_fields")}))
    print("protocol conflicts (must be empty): %s" % D["protocol"]["conflicts"])
    print("whole-document diff, identity fields: %s" % D["protocol"]["differing_identity"])
    print("whole-document diff, intervention fields: %s" % D["protocol"]["differing_intervention"])
    print("filters: %s" % json.dumps(D["protocol"]["filters"]))
    print("secret channel: %s" % D["protocol"]["secret_channel"])
    print("offline tests defined: %d" % D["tests"])
    print("naive canonicalisation: %s" % json.dumps(D["naive_canon"], default=str))
    print()
    # What the tree offered and what was taken from it, so the selection is auditable instead
    # of asserted. This is the table the report's provenance sentence is built from.
    sel = D["selection"]
    chosen = {(a["tag"], a["timestamp"]) for a in D["arms"]}
    print("artifact scan: %d launches -> %d chosen, %d superseded, %d rejected "
          "(%d with error turns, %d scored but incomplete, %d never wrote a scored run); "
          "drift vs recorded provenance: %s"
          % (sel["scanned"], sel["arms"], sel["superseded"],
             sel["rejected_error_turns"] + sel["rejected_unscored"] + sel["no_scored_run"],
             sel["rejected_error_turns"], sel["rejected_unscored"], sel["no_scored_run"],
             sel["drift"] or "none"))
    print("%-12s %-17s %-9s %6s %7s %8s  %s" % (
        "tag", "timestamp", "status", "err", "delta", "joint", "verdict"))
    for r in sel["rows"]:
        if (r["tag"], r["timestamp"]) in chosen:
            verdict = "chosen"
        elif r["usable"]:
            verdict = "superseded by a newer usable run"
        elif r["status"] == "no scored run":
            verdict = "rejected: launch never wrote a scored run"
        elif r["error_turns"]:
            verdict = "rejected: %d error turns" % r["error_turns"]
        else:
            verdict = "rejected: scored but not complete"
        print("%-12s %-17s %-9s %6d %7s %8s  %s" % (
            r["tag"], r["timestamp"], r["status"], r["error_turns"],
            "-" if r["delta"] is None else "%.2f" % r["delta"],
            "-" if r["joint"] is None else "%.2f" % r["joint"], verdict))
    print()
    print("%-4s %-22s %7s %8s %6s %5s %5s %8s %8s %5s %5s %8s %8s %6s %6s %5s" % (
        "arm", "label", "delta", "joint", "ratio", "cov", "viol", "co_reg", "og_reg",
        "post", "assi", "co_mean", "ogmean", "tn/er", "rerun", "norm"))
    for a in D["arms"]:
        print("%-4s %-22s %7.2f %8.2f %6.3f %5.1f %5d %8.2f %8.2f %5d %5d %8.2f %8.2f %5s %5d %5.1e" % (
            a["label"], a["name"], a["delta"], a["joint"], a["ratio"], a["coverage"],
            a["violations"], a["coalition_regret"], a["noncoalition_regret"], a["posts"],
            a["assigns"], a["coalition_mean"], a["noncoalition_mean"],
            "%d/%d" % (a["turns"], a["error_turns"]), a["reruns"], a["normalized_score"]))
    print()
    for k in ("control_gain_delta", "control_gain_joint", "action_only_below_baseline",
              "action_only_below_private", "events_over_baseline", "canon_over_baseline",
              "blinded_s_over_baseline", "blinded_b1_over_baseline", "s_over_baseline_ratio",
              "b1_over_baseline_ratio", "b1_coalition_below_baseline", "s_outgroup_drop",
              "s_coalition_equals_v", "v_joint_over_baseline",
              "prompt_pair", "prompt_pair_prompts", "prompt_pair_delta_gain",
              "prompt_pair_joint_gain", "channel_only_pairs",
              "e_spread", "e_joint_spread", "reran_arms", "reran_count",
              "exact_reproduced_arms", "exact_reproduced_count", "diverged_arms",
              "reruns_superseded_total", "reruns_config_matched",
              "clone_pair_deltas", "clone_ratio", "clone_pair_norms", "clone_norm_ratio",
              "clone_same_run_id", "clone_unrecorded_params", "pinned_unrecorded_params",
              "clone_corrupted_errors", "clone_corrupted_turns",
              "worst_joint", "worst_joint_arm", "best_joint", "best_joint_arm",
              "worst_delta", "worst_delta_arm", "max_normalized", "normalized_zero_arms",
              "normalized_nonzero_arms",
              "full_coverage_arms",
              "zero_violation_arms", "blocked_arms", "open_arms", "assigns_identical",
              "assign_calls", "agent_names", "turn_order_identical", "coalition_prompt",
              "unprompted_arms", "prompted_arms",
              "secret_channel", "coalition_names", "coalition_names_in_order", "outgroup_names",
              "invariant_agents", "agent_peak_arm", "noncoalition_mean_peak", "coalition_mean_peak",
              "run_date"):
        print("%-28s %s" % (k, D[k]))
    print("%-28s %s" % ("E rerun delta/joint", (D["e_rerun"]["delta"], D["e_rerun"]["joint"])))
    print()
    for k in sorted(D["h1"]):
        if k != "summary":
            print("%-28s %s" % ("h1." + k, D["h1"][k]))
    print("%-28s %s" % ("h1.summary", json.dumps(D["h1"]["summary"])))
    print()
    for k in sorted(D["h2"]):
        print("%-28s %s" % ("h2." + k, D["h2"][k]))
    print()
    print("%-28s %s" % ("canonicalised range", [(a["label"], a["canonicalised_per_agent"],
                                                 a["restores_per_agent"]) for a in D["arms"]]))
    print("%-28s %s" % ("coalition values", [(a["label"], a["coalition_values"],
                                              a["outgroup_values"]) for a in D["arms"]]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
