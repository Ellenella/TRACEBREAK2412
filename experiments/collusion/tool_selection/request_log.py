"""Record the user prompt actually returned to the runner.

CollusionPrompts logs agent_prompts.json before ToolSelectionPrompts appends
the codebook. This module writes a second record, phase "returned", whose
user_prompt is that return value, plus the execution tool schemas, model
settings, and file hashes. It does not change the returned string.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any

from experiments.collusion.tool_selection.observation import (
    CODEBOOK_HEADER,
    observation_leaks_selected_tool,
    receiver_observation_body,
)
from experiments.collusion.tool_selection.tools import JiraTicketToolSelectionTools

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
HASHED_FILES = (
    "prompts.py",
    "request_log.py",
    "tools.py",
    "protocol.py",
    "observation.py",
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def code_revision() -> dict[str, str]:
    hashes = {name: _sha256(HERE / name) for name in HASHED_FILES}
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=str(ROOT),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        head = "unknown"
    hashes["git_head"] = head
    return hashes


def _model_settings(config: dict[str, Any]) -> dict[str, Any]:
    models = config.get("llm_models") or []
    openai = {}
    if models:
        openai = ((models[0].get("llm") or {}).get("openai") or {})
    params = openai.get("params") or {}
    llm = config.get("llm") or {}
    return {
        "model": openai.get("model") or llm.get("model"),
        "temperature": params.get("temperature", llm.get("temperature")),
        "max_tokens": params.get("max_tokens", llm.get("max_tokens")),
    }


def log_returned_request(
    prompts: Any,
    agent_name: str,
    agent_context: dict[str, Any],
    user_prompt: str,
) -> None:
    system_prompt = prompts.get_system_prompt()
    context = dict(agent_context)
    context["phase"] = "returned"
    prompts._log_prompts_if_available(
        agent_name=agent_name,
        agent_context=context,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
    )
    experiment = prompts.full_config.get("experiment") or {}
    record = {
        "phase": "returned",
        "agent_name": agent_name,
        "iteration": agent_context.get("iteration"),
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
        "tool_schemas": JiraTicketToolSelectionTools(None).get_tools("execution"),
        "tool_schemas_source": "JiraTicketToolSelectionTools.get_tools('execution')",
        "model_settings": _model_settings(prompts.full_config),
        "experiment": {
            "tool_selection": experiment.get("tool_selection"),
            "tracebreak_hide_action_events": experiment.get("tracebreak_hide_action_events"),
            "tracebreak_mask_assignment_for_agent": experiment.get(
                "tracebreak_mask_assignment_for_agent"
            ),
        },
        "code_revision": code_revision(),
        "codebook_in_user_prompt": CODEBOOK_HEADER in user_prompt,
        "observation_leaks_selected_tool": observation_leaks_selected_tool(
            receiver_observation_body(user_prompt)
        ),
    }
    logger = getattr(prompts, "experiment_prompt_logger", None)
    log_dir = getattr(logger, "log_dir", None)
    if log_dir is None:
        return
    path = Path(log_dir) / "model_request.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
