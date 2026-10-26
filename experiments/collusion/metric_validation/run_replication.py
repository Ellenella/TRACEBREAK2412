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
import shutil
import time
import traceback
from pathlib import Path

from experiments.collusion import run as runner


class _RequestLog:
    """Records the request the provider client receives, including unfiltered arms."""

    def __init__(self, inner, agent_name: str | None = None):
        self._inner = inner
        self.agent_name = agent_name
        self.sent_requests = []

    def generate_response(self, input, params):
        texts = []
        for item in input or []:
            if not isinstance(item, dict):
                continue
            if isinstance(item.get("content"), str):
                texts.append(item["content"])
            if isinstance(item.get("_system_prompt"), str):
                texts.append(item["_system_prompt"])
            for part in item.get("parts") or []:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    texts.append(part["text"])
        tools = params.get("tools") or []
        names = []
        for tool in tools:
            if isinstance(tool, dict):
                names.append(str(tool.get("name") or (tool.get("function") or {}).get("name") or ""))
        self.sent_requests.append(
            {
                "agent": self.agent_name,
                "model": params.get("model"),
                "temperature": params.get("temperature"),
                "max_tokens": params.get("max_tokens"),
                "param_keys": sorted(str(key) for key in params.keys()),
                "tool_names": names,
                "texts": texts,
            }
        )
        return self._inner.generate_response(input, params)

    def __getattr__(self, name):
        return getattr(self._inner, name)


_ORIGINAL_GET_CLIENT = runner.get_client_instance


def _logged_client(*args, **kwargs):
    return _RequestLog(_ORIGINAL_GET_CLIENT(*args, **kwargs), kwargs.get("agent_name"))


runner.get_client_instance = _logged_client


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


PAUSE_S = 55
MAX_ATTEMPTS = 4


def retryable(exc: BaseException) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    needles = (
        "429",
        "resource_exhausted",
        "quota",
        "disconnect",
        "timeout",
        "timed out",
        "503",
        "502",
        "500",
        "unavailable",
        "remoteprotocol",
    )
    return any(needle in text for needle in needles)


def preserve_incomplete(dest: Path, tag: str) -> None:
    """Keep a failed or partial attempt. The next try writes a fresh directory."""
    if not dest.exists() or (dest / "job_summary.json").exists():
        return
    failed = OUT / "failed_attempts"
    failed.mkdir(parents=True, exist_ok=True)
    n = 1
    while (failed / f"{tag}_attempt{n}").exists():
        n += 1
    shutil.move(str(dest), str(failed / f"{tag}_attempt{n}"))


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
        raise


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
        finished = False
        for attempt in range(1, MAX_ATTEMPTS + 1):
            preserve_incomplete(OUT / tag, tag)
            print(f"{index}/{len(planned)} {tag} start attempt {attempt}", flush=True)
            try:
                status = await one(job, log_path)
            except Exception as exc:
                print(
                    f"{index}/{len(planned)} {tag} attempt {attempt} "
                    f"{type(exc).__name__}: {exc}",
                    flush=True,
                )
                if retryable(exc) and attempt < MAX_ATTEMPTS:
                    print(f"transient error, waiting {PAUSE_S}s", flush=True)
                    time.sleep(PAUSE_S)
                    continue
                if retryable(exc):
                    print(f"{index}/{len(planned)} {tag} failed after {MAX_ATTEMPTS} attempts", flush=True)
                    break
                print(f"{index}/{len(planned)} {tag} STOP", flush=True)
                return
            print(f"{index}/{len(planned)} {tag} {status}", flush=True)
            with log_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps({"job": job, "status": status, "attempt": attempt}) + "\n")
            finished = True
            break
        if finished and index < len(planned):
            # Free-tier Gemini allows 15 generate requests per minute for this model.
            time.sleep(PAUSE_S)


if __name__ == "__main__":
    asyncio.run(main())
