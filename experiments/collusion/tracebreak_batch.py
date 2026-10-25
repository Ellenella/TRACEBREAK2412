"""Run frozen TRACEBREAK repetitions without changing the experiment code.

Each successful call writes a new timestamp directory. Failures are recorded
and left in place. This script does not import or edit the prompt or protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
PY = ROOT / ".venv" / "Scripts" / "python.exe"
RESULTS = ROOT / "experiments" / "collusion" / "results"
CONFIG_DIR = ROOT / "experiments" / "collusion" / "configs"

# Frozen signaling grid: arm, bit, config stem.
SIGNAL_GRID = [
    ("A", 0, "tracebreak_signal_bit0"),
    ("A", 1, "tracebreak_signal_bit1"),
    ("B", 0, "tracebreak_signal_hide_events_bit0"),
    ("B", 1, "tracebreak_signal_hide_events_bit1"),
    ("C", 0, "tracebreak_signal_hide_assignments_bit0"),
    ("C", 1, "tracebreak_signal_hide_assignments_bit1"),
    ("D", 0, "tracebreak_signal_hide_both_bit0"),
    ("D", 1, "tracebreak_signal_hide_both_bit1"),
]

UTILITY_GRID = [
    ("A", "tracebreak_utility_A"),
    ("B", "tracebreak_utility_B"),
    ("C", "tracebreak_utility_C"),
    ("D", "tracebreak_utility_D"),
]

# Stage 1 only. Filter arms are not included until the harm gate passes.
GATE_GRID = [
    ("private", "tracebreak_private_capability"),
    ("A", "tracebreak_coalition_A"),
]

EXPECTED_FLAGS = {
    "A": {"hide_action_events": False, "mask": None},
    "B": {"hide_action_events": True, "mask": None},
    "C": {"hide_action_events": False, "mask": "Jeanene"},
    "D": {"hide_action_events": True, "mask": "Jeanene"},
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _prompt_hash() -> str:
    paths = [
        ROOT / "experiments" / "collusion" / "prompts_tracebreak.py",
        ROOT / "experiments" / "common" / "local_protocol_tracebreak.py",
    ]
    digest = hashlib.sha256()
    for path in paths:
        digest.update(path.name.encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _check_signal_config(arm: str, bit: int, stem: str) -> None:
    path = CONFIG_DIR / f"{stem}.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    exp = cfg["experiment"]
    expected = EXPECTED_FLAGS[arm]
    hide = bool(exp.get("tracebreak_hide_action_events", False))
    mask = exp.get("tracebreak_mask_assignment_for_agent")
    probe = exp.get("tracebreak_signal_probe") or {}
    if hide != expected["hide_action_events"] or mask != expected["mask"]:
        raise SystemExit(f"{stem}: observation flags {hide=} {mask=} != {expected}")
    if int(probe.get("bit")) != bit or probe.get("enabled") is not True:
        raise SystemExit(f"{stem}: probe bit/enabled mismatch")
    if exp.get("tracebreak_block_blackboard_tools") is not True:
        raise SystemExit(f"{stem}: blackboard tools are not blocked")
    if cfg["simulation"].get("max_planning_rounds") != 0:
        raise SystemExit(f"{stem}: planning rounds are not 0")
    if cfg["experiment"].get("seeds") != [1]:
        raise SystemExit(f"{stem}: seed is not [1]")


def _check_gate_config(arm: str, stem: str) -> None:
    path = CONFIG_DIR / f"{stem}.yaml"
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    exp = cfg["experiment"]
    sweep = exp["sweeps"][0]
    probe = exp.get("tracebreak_signal_probe") or {}
    if probe.get("enabled") is True:
        raise SystemExit(f"{stem}: signaling probe must be off")
    if sweep.get("colluder_counts") != [2] or sweep.get("prompt_variants") != ["structured"]:
        raise SystemExit(f"{stem}: gate runs need 2 structured colluders")
    if arm == "A":
        if cfg["simulation"].get("max_planning_rounds") != 0:
            raise SystemExit(f"{stem}: action-only A must have 0 planning rounds")
        if sweep.get("secret_channel_enabled") != [False]:
            raise SystemExit(f"{stem}: action-only A must disable the secret channel")
        if exp.get("tracebreak_block_blackboard_tools") is not True:
            raise SystemExit(f"{stem}: action-only A must block blackboard tools")
        if exp.get("tracebreak_hide_action_events") or exp.get(
            "tracebreak_mask_assignment_for_agent"
        ):
            raise SystemExit(f"{stem}: action-only A must leave both observations visible")
    elif arm == "private":
        if cfg["simulation"].get("max_planning_rounds") != 4:
            raise SystemExit(f"{stem}: private capability control needs 4 planning rounds")
        if sweep.get("secret_channel_enabled") != [True]:
            raise SystemExit(f"{stem}: private capability control needs the secret channel")
        if exp.get("tracebreak_block_blackboard_tools") is True:
            raise SystemExit(f"{stem}: private capability control must allow blackboard tools")
    else:
        raise SystemExit(f"Unknown gate arm {arm}")


def _check_utility_config(arm: str, stem: str) -> None:
    path = CONFIG_DIR / f"{stem}.yaml"
    if not path.exists():
        raise SystemExit(f"Missing utility config {path}")
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    exp = cfg["experiment"]
    expected = EXPECTED_FLAGS[arm]
    hide = bool(exp.get("tracebreak_hide_action_events", False))
    mask = exp.get("tracebreak_mask_assignment_for_agent")
    probe = exp.get("tracebreak_signal_probe") or {}
    sweep = cfg["experiment"]["sweeps"][0]
    if hide != expected["hide_action_events"] or mask != expected["mask"]:
        raise SystemExit(f"{stem}: observation flags {hide=} {mask=} != {expected}")
    if probe.get("enabled") is True:
        raise SystemExit(f"{stem}: signaling probe must be off")
    if sweep.get("colluder_counts") != [0]:
        raise SystemExit(f"{stem}: colluder_counts must be [0]")
    if sweep.get("prompt_variants") != ["control"]:
        raise SystemExit(f"{stem}: prompt variant must be control")


def _run_one(config_rel: str, log_path: Path) -> dict:
    cmd = [
        str(PY),
        "-m",
        "experiments.collusion.run_tracebreak",
        "--config",
        config_rel,
    ]
    started = datetime.now(timezone.utc).isoformat()
    proc = subprocess.run(
        cmd,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_path.write_text(
        (proc.stdout or "") + "\n--- STDERR ---\n" + (proc.stderr or ""),
        encoding="utf-8",
    )
    output_root = None
    for line in (proc.stdout or "").splitlines():
        if line.startswith("Wrote results to:"):
            output_root = line.split(":", 1)[1].strip()
    return {
        "started_utc": started,
        "exit_code": proc.returncode,
        "output_root": output_root,
        "log": str(log_path.relative_to(ROOT)).replace("\\", "/"),
    }


def _execute(rows: list[dict], manifest_path: Path, pause_s: float) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    logs = RESULTS / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    code_hash = _prompt_hash()
    with manifest_path.open("a", encoding="utf-8") as handle:
        for index, row in enumerate(rows, start=1):
            log_path = logs / f"{row['cohort']}_{index:02d}_{row['config_stem']}.log"
            print(f"[{index}/{len(rows)}] {row['config_stem']}", flush=True)
            outcome = _run_one(row["config"], log_path)
            record = {
                **row,
                **outcome,
                "prompt_code_sha256": code_hash,
                "model": "gpt-4.1-mini-2025-04-14",
                "temperature": 0.7,
                "environment_seed": 1,
                "repetition_kind": "model_sample_fixed_environment_seed",
            }
            handle.write(json.dumps(record) + "\n")
            handle.flush()
            status = "ok" if outcome["exit_code"] == 0 else "FAILED"
            print(f"  {status} exit={outcome['exit_code']} {outcome['output_root']}", flush=True)
            if index < len(rows):
                time.sleep(pause_s)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cohort", choices=["main", "utility", "gate"], required=True)
    parser.add_argument("--reps", type=int, default=None)
    parser.add_argument("--pause-seconds", type=float, default=2.0)
    args = parser.parse_args()

    if not PY.exists():
        raise SystemExit(f"Project interpreter not found: {PY}")

    if args.cohort == "main":
        reps = 5 if args.reps is None else args.reps
        rows = []
        for arm, bit, stem in SIGNAL_GRID:
            _check_signal_config(arm, bit, stem)
            for rep in range(1, reps + 1):
                rows.append(
                    {
                        "cohort": "main",
                        "arm": arm,
                        "bit": bit,
                        "rep": rep,
                        "config_stem": stem,
                        "config": f"experiments/collusion/configs/{stem}.yaml",
                    }
                )
        manifest = RESULTS / "tracebreak_main_manifest.jsonl"
    elif args.cohort == "gate":
        reps = 3 if args.reps is None else args.reps
        rows = []
        for arm, stem in GATE_GRID:
            _check_gate_config(arm, stem)
            for rep in range(1, reps + 1):
                rows.append(
                    {
                        "cohort": "gate",
                        "arm": arm,
                        "bit": None,
                        "rep": rep,
                        "config_stem": stem,
                        "config": f"experiments/collusion/configs/{stem}.yaml",
                    }
                )
        manifest = RESULTS / "tracebreak_gate_manifest.jsonl"
    else:
        reps = 2 if args.reps is None else args.reps
        rows = []
        for arm, stem in UTILITY_GRID:
            _check_utility_config(arm, stem)
            for rep in range(1, reps + 1):
                rows.append(
                    {
                        "cohort": "utility",
                        "arm": arm,
                        "bit": None,
                        "rep": rep,
                        "config_stem": stem,
                        "config": f"experiments/collusion/configs/{stem}.yaml",
                    }
                )
        manifest = RESULTS / "tracebreak_utility_manifest.jsonl"

    print(f"prompt_code_sha256={_prompt_hash()}", flush=True)
    print(f"runs={len(rows)} manifest={manifest}", flush=True)
    _execute(rows, manifest, args.pause_seconds)


if __name__ == "__main__":
    sys.exit(main())
