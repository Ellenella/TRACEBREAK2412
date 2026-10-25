"""Deterministic checks. No model calls."""

from __future__ import annotations

import unittest

from terrarium.blackboard import format_blackboard_events_for_prompt
from terrarium.environment_tools import get_environment_tools_class

from experiments.collusion.tool_selection.observation import (
    CANONICAL_TOOL,
    CODEBOOK_HEADER,
    canonicalize_observation_text,
    observation_leaks_selected_tool,
)
from experiments.collusion.tool_selection.register import ENV_NAME, register
from experiments.collusion.tool_selection.observation import receiver_observation_body
from experiments.collusion.tool_selection.prompts import ToolSelectionPrompts, _rule, turn_roles
from experiments.collusion.tool_selection.tools import DIRECT, QUEUED, JiraTicketToolSelectionTools
from experiments.collusion.tool_selection.validate_matched import check_all

TASK = "ISSUE-0001::review"
TASK_RECORD = {"id": TASK, "priority": "low", "title": "Review"}


class _Logger:
    def __init__(self) -> None:
        self.actions: list[dict] = []

    def log_action_to_blackboards(self, agent_name, action, result, phase, iteration):
        self.actions.append(
            {
                "agent": agent_name,
                "action": dict(action),
                "result_status": result.get("status"),
                "task_id": (result.get("result") or {}).get("task_id"),
            }
        )


def _state() -> dict:
    return {
        "tasks": {TASK: dict(TASK_RECORD)},
        "assignment": {},
        "agent_names": ["Layla", "Jeanene", "Pauline"],
    }


def _event(action: dict, result: dict) -> dict:
    return {
        "kind": "action_executed",
        "agent": "Layla",
        "payload": {
            "action_type": action.get("action"),
            "action_params": dict(action),
            "result_status": result.get("status"),
            "details": result,
        },
    }


class ToolSelectionTests(unittest.TestCase):
    def test_two_distinct_tools_are_exposed(self) -> None:
        tools = JiraTicketToolSelectionTools(None)
        names = [item["function"]["name"] for item in tools.get_tools("execution")]
        self.assertEqual(names, [DIRECT, QUEUED])
        self.assertEqual(tools.get_tools("planning"), [])

    def test_registry_resolves_the_extension_class(self) -> None:
        register()
        self.assertIs(get_environment_tools_class(ENV_NAME), JiraTicketToolSelectionTools)

    def test_same_task_same_state_different_identity(self) -> None:
        logger = _Logger()
        tools = JiraTicketToolSelectionTools(logger)
        direct = tools.handle_tool_call(DIRECT, "Layla", {"task_id": TASK}, env_state=_state())
        queued = tools.handle_tool_call(QUEUED, "Layla", {"task_id": TASK}, env_state=_state())
        self.assertEqual(direct["status"], "success")
        self.assertEqual(queued["status"], "success")
        self.assertEqual(direct["result"]["state_updates"], queued["result"]["state_updates"])
        self.assertEqual(direct["result"]["task_id"], queued["result"]["task_id"])
        self.assertEqual(direct["result"]["task"], queued["result"]["task"])
        self.assertEqual(logger.actions[0]["action"]["action"], DIRECT)
        self.assertEqual(logger.actions[1]["action"]["action"], QUEUED)
        self.assertNotEqual(
            logger.actions[0]["action"]["action"],
            logger.actions[1]["action"]["action"],
        )

    def test_visible_event_contains_tool_identity(self) -> None:
        tools = JiraTicketToolSelectionTools(_Logger())
        result = tools.handle_tool_call(DIRECT, "Layla", {"task_id": TASK}, env_state=_state())
        rendered = format_blackboard_events_for_prompt(
            [_event({"action": DIRECT, "task_id": TASK}, result)]
        )
        self.assertIn(DIRECT, rendered)
        self.assertIn(TASK, rendered)
        self.assertNotIn(QUEUED, rendered)

    def test_canonical_event_keeps_task_and_drops_identity(self) -> None:
        tools = JiraTicketToolSelectionTools(_Logger())
        result = tools.handle_tool_call(QUEUED, "Layla", {"task_id": TASK}, env_state=_state())
        rendered = format_blackboard_events_for_prompt(
            [_event({"action": QUEUED, "task_id": TASK}, result)]
        )
        hidden = canonicalize_observation_text(rendered)
        self.assertIn(TASK, hidden)
        self.assertIn(CANONICAL_TOOL, hidden)
        self.assertFalse(observation_leaks_selected_tool(hidden))
        self.assertIn(QUEUED, rendered)

    def test_turn_roles_follow_name_order(self) -> None:
        sender, receiver, third = turn_roles(["Ada", "Bea", "Cy"])
        self.assertEqual((sender, receiver, third), ("Ada", "Bea", "Cy"))
        sender_text = _rule("Ada", 0, "Ada", "Bea")
        receiver_text = _rule("Bea", 1, "Ada", "Bea")
        self.assertIn("assign_task_direct", sender_text)
        self.assertIn("Your private bit is 0", sender_text)
        self.assertNotIn("Your private bit is", receiver_text)
        self.assertIn("Ada called assign_task_queued", receiver_text)
        self.assertEqual(_rule("Cy", 0, "Ada", "Bea"), "")
        body = receiver_observation_body(
            "blackboard assign_task_direct\n\n" + receiver_text
        )
        self.assertIn("blackboard assign_task_direct", body)
        self.assertNotIn("EXPLORATORY", body)

    def test_seed_equivalence_and_observation_boundary(self) -> None:
        rows = check_all()
        problems = [problem for row in rows for problem in row["problems"]]
        self.assertEqual(problems, [])

    def test_returned_log_is_the_prompt_the_runner_receives(self) -> None:
        import asyncio
        import json
        import tempfile
        from pathlib import Path

        from experiments.collusion.tool_selection.validate_matched import _claim, _make

        class _Capture:
            def __init__(self, directory: Path) -> None:
                self.log_dir = directory
                self.rows: list[dict] = []

            def log_prompts(self, **kwargs: object) -> None:
                self.rows.append(dict(kwargs))

        async def check() -> None:
            with tempfile.TemporaryDirectory() as tmp:
                logger = _Capture(Path(tmp))
                env, protocol = _make(1, hide=False, canonicalize=True, mask=False, bit=0)
                sender, receiver, _third = turn_roles(env.get_agent_names())
                await _claim(protocol, sender, DIRECT, TASK)
                contexts = await protocol._prefetch_blackboard_events(
                    receiver, phase="execution", iteration=1
                )
                builder = ToolSelectionPrompts(
                    env,
                    protocol.config,
                    prompt_variant="control",
                    base_prompts=env.prompts,
                    experiment_prompt_logger=logger,
                )
                context = env.build_agent_context(receiver, phase="execution", iteration=1)
                context["collusion_role"] = "normal"
                returned = builder.get_user_prompt(receiver, context, contexts)
                returned_rows = [row for row in logger.rows if row.get("phase") == "returned"]
                prefix_rows = [row for row in logger.rows if row.get("phase") == "execution"]
                self.assertEqual(len(returned_rows), 1)
                self.assertEqual(returned_rows[0]["user_prompt"], returned)
                self.assertIn(CODEBOOK_HEADER, returned)
                self.assertTrue(prefix_rows)
                self.assertNotIn(CODEBOOK_HEADER, prefix_rows[-1]["user_prompt"])
                saved = [
                    json.loads(line)
                    for line in (Path(tmp) / "model_request.jsonl").read_text(encoding="utf-8").splitlines()
                ]
                self.assertEqual(saved[-1]["user_prompt"], returned)
                self.assertEqual(
                    [item["function"]["name"] for item in saved[-1]["tool_schemas"]],
                    [DIRECT, QUEUED],
                )
                self.assertIn("prompts.py", saved[-1]["code_revision"])

        asyncio.run(check())

    def test_assignment_line_has_no_tool_name(self) -> None:
        line = f"- Layla: {TASK}"
        self.assertFalse(observation_leaks_selected_tool(line))
        self.assertIn(TASK, line)


if __name__ == "__main__":
    unittest.main()
