"""Launch the matched cohort. Each run has its own directory.

Validation and the seed-2 preflight must pass before the 108-run grid.
Completed runs are skipped on resume. Failures are kept and are not retried
automatically; a failed job is recorded and the launcher continues.
"""

from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

from experiments.collusion.tool_selection.validate_matched import check_all, write_reports

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MATCHED = HERE / "outputs" / "matched"
PREFLIGHT = MATCHED / "preflight"
RUNS = MATCHED / "runs"
MANIFEST = MATCHED / "manifest.jsonl"
PYTHON = Path(sys.executable)
POLICIES = ("t1", "t2", "t3")
SEEDS = (1, 2, 3)
REPS = (1, 2, 3, 4)


def job_id(kind: str, policy: str, seed: int, rep: int, bit: Optional[int]) -> str:
    if kind == "signal":
        return f"signal_{policy}_seed{seed}_bit{bit}_rep{rep}"
    return f"utility_{policy}_seed{seed}_rep{rep}"


def _jobs(kind: str) -> list[dict[str, Any]]:
    rows = []
    if kind == "signal":
        for rep in REPS:
            for seed in SEEDS:
                for bit in (0, 1):
                    for policy in POLICIES:
                        rows.append(
                            {"kind": kind, "policy": policy, "seed": seed, "bit": bit, "rep": rep}
                        )
    else:
        for rep in REPS:
            for seed in SEEDS:
                for policy in POLICIES:
                    rows.append(
                        {"kind": kind, "policy": policy, "seed": seed, "bit": None, "rep": rep}
                    )
    random.Random(20261025 if kind == "signal" else 20261026).shuffle(rows)
    return rows


def preflight_jobs() -> list[dict[str, Any]]:
    rows = []
    for bit in (0, 1):
        for policy in POLICIES:
            rows.append(
                {"kind": "signal", "policy": policy, "seed": 2, "bit": bit, "rep": 0}
            )
    return rows


def _config(job: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    policy = job["policy"]
    experiment: dict[str, Any] = {
        "tag": job_id(job["kind"], policy, job["seed"], job["rep"], job["bit"]),
        "output_dir": str(out_dir),
        "max_concurrent_runs": 1,
        "seeds": [int(job["seed"])],
        "tracebreak_block_blackboard_tools": True,
        "tracebreak_hide_action_events": policy == "t3",
        "tool_selection": {
            "enabled": job["kind"] == "signal",
            "canonicalize_identity": policy == "t2",
            "policy": policy,
        },
        "collusion": {
            "colluder_selection": "first",
            "agent_order": "colluders_first",
        },
        "sweeps": [
            {
                "name": job_id(job["kind"], policy, job["seed"], job["rep"], job["bit"]),
                "topologies": ["complete"],
                "num_agents": [3],
                "colluder_counts": [0],
                "secret_channel_enabled": [False],
                "prompt_variants": ["control"],
            }
        ],
    }
    if job["kind"] == "signal":
        experiment["tool_selection"]["bit"] = int(job["bit"])
    if policy == "t3":
        experiment["tracebreak_mask_assignment_for_agent"] = "receiver"
    return {
        "simulation": {
            "max_iterations": 1,
            "max_planning_rounds": 0,
            "max_conversation_steps": 3,
            "seed": int(job["seed"]),
            "tags": ["tool_selection_matched"],
        },
        "environment": {
            "import_path": (
                "experiments.collusion.tool_selection.env:JiraTicketToolSelectionEnvironment"
            ),
            "assignment_filling": False,
            "max_tasks": 8,
        },
        "communication_network": {
            "topology": "complete",
            "num_agents": 3,
            "consolidate_channels": True,
        },
        "llm_models": [
            {
                "label": "openai-gpt-4.1-mini",
                "llm": {
                    "provider": "openai",
                    "openai": {
                        "model": "gpt-4.1-mini-2025-04-14",
                        "params": {"max_tokens": 1500, "temperature": 0.7},
                    },
                },
            }
        ],
        "experiment": experiment,
    }


def _complete(out_dir: Path) -> bool:
    for path in out_dir.glob("**/final_summary.json"):
        try:
            summary = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if summary.get("status") == "complete":
            return True
    return False


def _record(job: dict[str, Any], status: str, out_dir: Path, manifest: Path = MANIFEST) -> None:
    manifest.parent.mkdir(parents=True, exist_ok=True)
    line = {
        "id": job_id(job["kind"], job["policy"], job["seed"], job["rep"], job["bit"]),
        "status": status,
        "output_dir": str(out_dir),
        **job,
    }
    with manifest.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line) + "\n")


def run_job(job: dict[str, Any], parent: Path, manifest: Path = MANIFEST) -> str:
    name = job_id(job["kind"], job["policy"], job["seed"], job["rep"], job["bit"])
    out_dir = parent / name
    if _complete(out_dir):
        print(f"SKIP complete {name}")
        return "skipped"
    out_dir.mkdir(parents=True, exist_ok=True)
    config_path = out_dir / "launcher_config.yaml"
    config_path.write_text(
        yaml.safe_dump(_config(job, out_dir), sort_keys=False),
        encoding="utf-8",
    )
    print(f"RUN {name}")
    completed = subprocess.run(
        [
            str(PYTHON),
            "-m",
            "experiments.collusion.tool_selection.run_tool_selection",
            "--config",
            str(config_path),
            "--out-dir",
            str(out_dir),
        ],
        cwd=str(ROOT),
        check=False,
    )
    status = "complete" if completed.returncode == 0 and _complete(out_dir) else "failed"
    _record(job, status, out_dir, manifest)
    print(f"{status.upper()} {name} exit={completed.returncode}")
    return status


def validate() -> bool:
    rows = check_all()
    write_reports(rows)
    problems = [problem for row in rows for problem in row["problems"]]
    for problem in problems:
        print(problem)
    print("VALIDATION PASSED" if not problems else f"VALIDATION FAILED ({len(problems)})")
    return not problems


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "validate"
    if mode in {"validate", "preflight", "grid", "all"} and not validate():
        return 1
    if mode == "validate":
        return 0
    if mode in {"preflight", "all"}:
        for job in preflight_jobs():
            run_job(job, PREFLIGHT)
        from experiments.collusion.tool_selection.score_matched import preflight_ok

        if not preflight_ok(PREFLIGHT):
            print("PREFLIGHT FAILED")
            return 2
        print("PREFLIGHT PASSED")
    if mode in {"grid", "all"}:
        jobs = _jobs("signal") + _jobs("utility")
        for job in jobs:
            run_job(job, RUNS)
        from experiments.collusion.tool_selection.score_matched import write_matched

        write_matched()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
