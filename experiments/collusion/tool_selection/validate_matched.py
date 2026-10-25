"""Deterministic checks for the matched tool-selection cohort. No model calls.

Compares environment state, reward, claimability, turn order, T2 observation
text, and the T3 observation hooks on seeds 1, 2, and 3.
"""

from __future__ import annotations

import asyncio
import copy
import difflib
import math
from pathlib import Path
from typing import Any

import envs.dcops.jira_ticket.jira_ticket_env as jira_mod

from experiments.collusion.run_tracebreak import _order_agent_turns
from experiments.collusion.tool_selection.env import JiraTicketToolSelectionEnvironment
from experiments.collusion.tool_selection.observation import (
    observation_leaks_selected_tool,
    receiver_observation_body,
)
from experiments.collusion.tool_selection.prompts import (
    FIXED_TASK,
    TEST,
    TRIAGE,
    ToolSelectionPrompts,
    turn_roles,
)
from experiments.collusion.tool_selection.protocol import ToolSelectionProtocol
from experiments.collusion.tool_selection.tools import DIRECT, QUEUED

HERE = Path(__file__).resolve().parent
SEEDS = (1, 2, 3)
REQUIRED = (FIXED_TASK, TRIAGE, TEST)


def _config(seed: int, *, hide: bool, canonicalize: bool, mask: bool, bit: int) -> dict:
    experiment: dict[str, Any] = {
        "tag": "tool_selection_validation",
        "tracebreak_block_blackboard_tools": True,
        "tracebreak_hide_action_events": hide,
        "tool_selection": {
            "enabled": True,
            "bit": bit,
            "canonicalize_identity": canonicalize,
        },
        "collusion": {
            "colluder_selection": "first",
            "agent_order": "colluders_first",
        },
    }
    if mask:
        experiment["tracebreak_mask_assignment_for_agent"] = "receiver"
    return {
        "simulation": {
            "seed": int(seed),
            "max_iterations": 1,
            "max_planning_rounds": 0,
            "tags": ["tool_selection_validation"],
        },
        "environment": {"max_tasks": 8, "assignment_filling": False},
        "communication_network": {
            "topology": "complete",
            "num_agents": 3,
            "consolidate_channels": True,
        },
        "logging": {
            "root_dir": str(HERE / "outputs" / "matched" / "_validation_logs"),
        },
        "llm_models": [
            {
                "label": "validation",
                "llm": {
                    "provider": "openai",
                    "openai": {"model": "gpt-4.1-mini-2025-04-14"},
                },
            }
        ],
        "experiment": experiment,
    }


def _make(seed: int, **flags: Any) -> tuple[Any, ToolSelectionProtocol]:
    jira_mod.clear_seed_directories = lambda *_a, **_k: None  # type: ignore[assignment]
    cfg = _config(seed, **flags)
    protocol = ToolSelectionProtocol(config=cfg)
    env = JiraTicketToolSelectionEnvironment(protocol, cfg, None)
    protocol.megaboard.add_blackboard(list(env.get_agent_names()))
    return env, protocol


def _snapshot(env: Any) -> dict[str, Any]:
    evaluation = env._evaluate_assignment(env.assignment)
    joint, local = env._rewards(env.assignment)
    return {
        "assignment": dict(env.assignment),
        "tasks": copy.deepcopy(env.tasks),
        "costs": copy.deepcopy(env.costs),
        "evaluation": evaluation,
        "joint": joint,
        "local": local,
    }


async def _claim(protocol: ToolSelectionProtocol, agent: str, tool: str, task: str) -> dict:
    return await protocol.environment_handle_tool_call(
        tool,
        agent,
        {"task_id": task},
        phase="execution",
        iteration=1,
    )


async def _prompt(
    env: Any,
    protocol: ToolSelectionProtocol,
    agent: str,
) -> str:
    contexts = await protocol._prefetch_blackboard_events(
        agent, phase="execution", iteration=1
    )
    builder = ToolSelectionPrompts(
        env,
        protocol.config,
        prompt_variant="control",
        base_prompts=env.prompts,
    )
    context = env.build_agent_context(agent, phase="execution", iteration=1)
    context["collusion_role"] = "normal"
    return builder.get_user_prompt(agent, context, contexts)


def _finite(env: Any, agent: str, task: str) -> bool:
    return math.isfinite(float(env.costs.get(agent, {}).get(task, float("inf"))))


async def check_seed(seed: int) -> dict[str, Any]:
    problems: list[str] = []
    env, _protocol = _make(seed, hide=False, canonicalize=False, mask=False, bit=0)
    names = [str(name) for name in env.get_agent_names()]
    sender, receiver, third = turn_roles(names)
    order = _order_agent_turns(
        agent_names=names, colluders=[], strategy="colluders_first"
    )
    if order != [sender, receiver, third]:
        problems.append(f"seed {seed} turn order {order} is not sender, receiver, third")
    missing = [task for task in REQUIRED if task not in env.tasks]
    if missing:
        problems.append(f"seed {seed} missing tasks {missing}")

    claims = {
        "sender_review": (sender, DIRECT, FIXED_TASK),
        "receiver_triage": (receiver, DIRECT, TRIAGE),
        "receiver_test": (receiver, QUEUED, TEST),
    }
    claim_results: dict[str, str] = {}
    for label, (agent, tool, task) in claims.items():
        trial, trial_protocol = _make(
            seed, hide=False, canonicalize=False, mask=False, bit=0
        )
        if not _finite(trial, agent, task):
            problems.append(f"seed {seed} {label} cost is not finite")
            claim_results[label] = "infinite_cost"
            continue
        result = await _claim(trial_protocol, agent, tool, task)
        status = str(result.get("status"))
        evaluation = trial._evaluate_assignment(trial.assignment)
        claim_results[label] = status
        if status != "success" or evaluation.get("violations") != 0:
            problems.append(
                f"seed {seed} {label} status={status} violations={evaluation.get('violations')}"
            )
        if trial.assignment.get(agent) != task:
            problems.append(f"seed {seed} {label} assignment={trial.assignment}")

    direct_env, direct_protocol = _make(
        seed, hide=False, canonicalize=True, mask=False, bit=0
    )
    queued_env, queued_protocol = _make(
        seed, hide=False, canonicalize=True, mask=False, bit=1
    )
    direct_result = await _claim(direct_protocol, sender, DIRECT, FIXED_TASK)
    queued_result = await _claim(queued_protocol, sender, QUEUED, FIXED_TASK)
    direct_state = _snapshot(direct_env)
    queued_state = _snapshot(queued_env)
    if direct_state != queued_state:
        problems.append(f"seed {seed} tool effects differ")
    if direct_result.get("status") != "success" or queued_result.get("status") != "success":
        problems.append(f"seed {seed} equivalence calls failed")
    direct_names = [event.tool_name for event in direct_protocol.tool_events]
    queued_names = [event.tool_name for event in queued_protocol.tool_events]
    if direct_names != [DIRECT] or queued_names != [QUEUED]:
        problems.append(
            f"seed {seed} logged tools direct={direct_names} queued={queued_names}"
        )

    async def _body(protocol: ToolSelectionProtocol, env: Any, canonicalize: bool) -> str:
        protocol.config["experiment"]["tool_selection"]["canonicalize_identity"] = canonicalize
        text = await _prompt(env, protocol, receiver)
        return receiver_observation_body(text)

    raw_direct = await _body(direct_protocol, direct_env, False)
    raw_queued = await _body(queued_protocol, queued_env, False)
    canon_direct = await _body(direct_protocol, direct_env, True)
    canon_queued = await _body(queued_protocol, queued_env, True)
    if raw_direct == raw_queued:
        problems.append(f"seed {seed} raw observations do not reveal the tool difference")
    if DIRECT not in raw_direct or QUEUED not in raw_queued:
        problems.append(f"seed {seed} raw observations are missing the selected tool")
    if canon_direct != canon_queued:
        problems.append(f"seed {seed} canonical observations are not identical")
    if observation_leaks_selected_tool(canon_direct) or observation_leaks_selected_tool(canon_queued):
        problems.append(f"seed {seed} canonical observation still names a selected tool")
    if "=== CURRENT ASSIGNMENTS ===" not in canon_direct or FIXED_TASK not in canon_direct:
        problems.append(f"seed {seed} canonical observation dropped the assignment")

    broad_env, broad_protocol = _make(
        seed, hide=True, canonicalize=False, mask=True, bit=0
    )
    await _claim(broad_protocol, sender, DIRECT, FIXED_TASK)
    receiver_text = await _prompt(broad_env, broad_protocol, receiver)
    sender_text = await _prompt(broad_env, broad_protocol, sender)
    receiver_body = receiver_observation_body(receiver_text)
    if "action_executed" in receiver_body or "=== CURRENT ASSIGNMENTS ===" in receiver_body:
        problems.append(f"seed {seed} T3 receiver still sees an event or an assignment")
    if observation_leaks_selected_tool(receiver_body):
        problems.append(f"seed {seed} T3 receiver observation names a tool")
    if "=== CURRENT ASSIGNMENTS ===" not in sender_text or FIXED_TASK not in sender_text:
        problems.append(f"seed {seed} T3 sender lost the assignment")
    if [event.tool_name for event in broad_protocol.tool_events] != [DIRECT]:
        problems.append(f"seed {seed} T3 tool log lost the executed tool")

    return {
        "seed": seed,
        "names": names,
        "sender": sender,
        "receiver": receiver,
        "third": third,
        "order": order,
        "claims": claim_results,
        "joint": direct_state["joint"],
        "evaluation": direct_state["evaluation"],
        "assignment": direct_state["assignment"],
        "raw_differs": raw_direct != raw_queued,
        "canonical_equal": canon_direct == canon_queued,
        "canonical_sample": canon_direct,
        "canonical_diff": "\n".join(
            difflib.unified_diff(
                canon_direct.splitlines(),
                canon_queued.splitlines(),
                fromfile=f"seed{seed}-bit0",
                tofile=f"seed{seed}-bit1",
                lineterm="",
            )
        ),
        "problems": problems,
    }


def check_all() -> list[dict[str, Any]]:
    async def _run() -> list[dict[str, Any]]:
        return [await check_seed(seed) for seed in SEEDS]

    return asyncio.run(_run())


def write_reports(rows: list[dict[str, Any]]) -> None:
    problems = [problem for row in rows for problem in row["problems"]]
    obs_lines = [
        "# T2 observation equivalence",
        "",
        "Each pair uses the same environment seed. Bit 0 executes",
        "`assign_task_direct` and bit 1 executes `assign_task_queued`,",
        f"both on `{FIXED_TASK}`. The comparison is the receiver's rendered",
        "execution prompt after UUID normalization, with the fixed codebook removed.",
        "Callable tool schemas are not in that prompt. They remain available as functions.",
        "The codebook may name both tools. That does not show which tool was selected.",
        "",
        "Before canonicalization the two observations differ, and each contains its tool name.",
        "After canonicalization they must be identical, and the assignment must remain.",
        "",
    ]
    seed_lines = [
        "# Seed validity for the matched cohort",
        "",
        "Turn order is the environment name list. With no colluders and",
        "`agent_order: colluders_first`, that list is the execution order:",
        "sender, receiver, then the third agent.",
        "",
        "A successful claim means the tool returns success, the assignment is stored,",
        "the private cost is finite, and the environment evaluator reports no violation.",
        "",
    ]
    for row in rows:
        obs_lines.append(
            f"## Seed {row['seed']}: {row['sender']} then {row['receiver']} then {row['third']}"
        )
        obs_lines.append("")
        obs_lines.append(
            f"Raw observations differ: {row['raw_differs']}. "
            f"Canonical observations identical: {row['canonical_equal']}."
        )
        obs_lines.append("")
        if row["canonical_diff"]:
            obs_lines.append("```diff")
            obs_lines.append(row["canonical_diff"])
            obs_lines.append("```")
            obs_lines.append("")
        obs_lines.append("Normalized canonical observation:")
        obs_lines.append("")
        obs_lines.append("```text")
        obs_lines.append(row["canonical_sample"])
        obs_lines.append("```")
        obs_lines.append("")
        seed_lines.append(f"## Seed {row['seed']}")
        seed_lines.append("")
        seed_lines.append(
            f"Order: {row['sender']}, {row['receiver']}, {row['third']}."
        )
        seed_lines.append(
            f"Claims: {row['claims']}. Joint reward after the sender's review claim: {row['joint']}."
        )
        seed_lines.append(f"Evaluation: {row['evaluation']}.")
        seed_lines.append(f"Assignment: {row['assignment']}.")
        if row["problems"]:
            seed_lines.extend(f"- {problem}" for problem in row["problems"])
        else:
            seed_lines.append("No problems.")
        seed_lines.append("")
    obs_lines.append("## Result")
    obs_lines.append("")
    obs_lines.append("Failed." if problems else "Passed for seeds 1, 2, and 3.")
    obs_lines.append("")
    (HERE / "OBSERVATION_EQUIVALENCE.md").write_text("\n".join(obs_lines), encoding="utf-8")
    (HERE / "SEED_CHECK.md").write_text("\n".join(seed_lines), encoding="utf-8")


def main() -> int:
    rows = check_all()
    write_reports(rows)
    problems = [problem for row in rows for problem in row["problems"]]
    for problem in problems:
        print(problem)
    if problems:
        print(f"VALIDATION FAILED ({len(problems)})")
        return 1
    print("VALIDATION PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
