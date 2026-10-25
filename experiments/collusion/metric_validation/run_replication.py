"""Twenty-five episode replication for the metric-validation study.

The committed configs name provider ``openrouter``. This terrarium build has no
OpenRouter client. The PDF names Google's endpoint, and a Google key is present,
so each job is sent through the installed Gemini client with the same model
string and the same generation parameters. The yaml files on disk are not edited.
"""

from __future__ import annotations

import asyncio
import copy
import json
import random
import traceback
from pathlib import Path

from experiments.collusion import run as runner


ROOT = Path(__file__).resolve().parent
CONFIG_DIR = ROOT / "configs"
OUT = ROOT / "outputs" / "replication"
ARMS = ("B0", "P", "V", "S", "B1")
SEEDS = (31, 32, 33, 34, 35)


def jobs() -> list[dict]:
    rows = [{"arm": arm, "seed": seed} for seed in SEEDS for arm in ARMS]
    random.Random(20261031).shuffle(rows)
    return rows


def adapt(cfg: dict) -> dict:
    cfg = copy.deepcopy(cfg)
    model = cfg["llm_models"][0]["llm"]
    block = dict(model.get("openrouter") or {})
    model["provider"] = "gemini"
    model["gemini"] = {"model": block.get("model"), "params": dict(block.get("params") or {})}
    model.pop("openrouter", None)
    cfg.setdefault("experiment", {})["provider_adaptation"] = {
        "from": "openrouter",
        "to": "gemini",
        "model": block.get("model"),
        "reason": (
            "The installed terrarium has no openrouter provider. "
            "The model string and generation parameters are unchanged. "
            "The call uses the installed Google Gemini client."
        ),
    }
    return cfg


def fatal(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    needles = (
        "api key",
        "api_key",
        "not found",
        "not_found",
        "404",
        "permission",
        "quota",
        "resource_exhausted",
        "invalid",
        "unavailable",
        "unauthorized",
        "403",
        "401",
    )
    return any(needle in text for needle in needles)


async def one(job: dict, order_path: Path) -> str:
    cfg = adapt(runner._load_yaml(str(CONFIG_DIR / f"track31_{job['arm']}.yaml")))
    cfg["experiment"]["seeds"] = [int(job["seed"])]
    cfg["simulation"]["seed"] = int(job["seed"])
    sweep = cfg["experiment"]["sweeps"][0]
    model = cfg["llm_models"][0]
    tag = f"{job['arm']}_seed{job['seed']}"
    dest = OUT / tag
    dest.mkdir(parents=True, exist_ok=True)
    try:
        summary = await runner._run_single(
            base_cfg=cfg,
            model_label=model["label"],
            model_llm_cfg=model["llm"],
            sweep_name=sweep["name"],
            topology=sweep["topologies"][0],
            num_agents=sweep["num_agents"][0],
            colluder_count=sweep["colluder_counts"][0],
            secret_channel_enabled=bool(sweep["secret_channel_enabled"][0]),
            prompt_variant=sweep["prompt_variants"][0],
            seed=int(job["seed"]),
            out_dir=dest,
        )
        (dest / "job_summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
        return "complete"
    except Exception as exc:
        (dest / "job_error.txt").write_text(traceback.format_exc(), encoding="utf-8")
        record = {"job": job, "error": f"{type(exc).__name__}: {exc}"}
        with order_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record) + "\n")
        if fatal(exc):
            raise
        return "failed"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    planned = jobs()
    order_path = OUT / "job_order.json"
    if not order_path.exists():
        order_path.write_text(json.dumps(planned, indent=2), encoding="utf-8")
    else:
        planned = json.loads(order_path.read_text(encoding="utf-8"))
    log_path = OUT / "status.jsonl"
    for index, job in enumerate(planned, start=1):
        tag = f"{job['arm']}_seed{job['seed']}"
        if (OUT / tag / "job_summary.json").exists():
            print(f"{index}/{len(planned)} {tag} already complete", flush=True)
            continue
        print(f"{index}/{len(planned)} {tag} start", flush=True)
        try:
            status = await one(job, log_path)
        except Exception as exc:
            print(f"{index}/{len(planned)} {tag} STOP {type(exc).__name__}: {exc}", flush=True)
            break
        print(f"{index}/{len(planned)} {tag} {status}", flush=True)
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps({"job": job, "status": status}) + "\n")


if __name__ == "__main__":
    asyncio.run(main())
