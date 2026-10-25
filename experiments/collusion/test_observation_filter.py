"""Offline check of the observation filter against real captured prompts.

No API key and no model call: the inputs are the actual agent prompts logged by run
experiments/collusion/outputs/ellen_jira_baseline/20261024-234945. Run with

    python experiments/collusion/test_observation_filter.py
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from experiments.collusion.observation_filter import (  # noqa: E402
    AGENT_CANON,
    ASSIGNMENT_MASK,
    TASK_TOKEN,
    FilterPolicy,
    FilteringClient,
    _JOINT_REWARD,
    _TASK_ID,
    policy_from_config,
)

FIXTURES = HERE / "fixtures"


class RecordingClient:
    """Stands in for a provider client and remembers exactly what reached it."""

    def __init__(self) -> None:
        self.seen_input: List[Any] = []
        self.seen_params: List[Dict[str, Any]] = []

    def init_context(self, system_prompt, user_prompt):
        return [{"role": "user", "content": user_prompt}]

    def set_meta_context(self, agent_name, phase, iteration=None, round_num=None):
        return None

    async def process_tool_calls(self, response, context, execute_tool_callback):
        return 0, context, []

    def get_usage(self, response, current_usage):
        return current_usage

    def generate_response(self, input, params):
        self.seen_input.append([dict(i) if isinstance(i, dict) else i for i in input])
        self.seen_params.append(dict(params))
        return object(), "ok"


def _prompt(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _context(text: str) -> List[Dict[str, Any]]:
    return [{"role": "system", "content": "sys"}, {"role": "user", "content": text}]


def _tools() -> List[Dict[str, Any]]:
    return [{"type": "function", "name": "post_message"}, {"type": "function", "name": "assign_task"}]


def _run(client: FilteringClient, text: str, tools=None):
    params: Dict[str, Any] = {"model": "m", "temperature": 0.7}
    if tools is not None:
        params["tools"] = tools
    return client.generate_response(_context(text), params)


def test_baseline_fixture_has_both_paths():
    layla = _prompt("layla_execution_prompt.txt")
    assert layla.count("[action_executed]") == 2, "fixture drifted from the audited run"
    assert layla.count("=== CURRENT ASSIGNMENTS ===") == 1
    assert "- Jeanene: ISSUE-0001::test" in layla and "- Pauline: ISSUE-0001::docs" in layla
    assert "assign_task" in layla


def test_event_filter_leaves_the_assignment_path():
    layla = _prompt("layla_execution_prompt.txt")
    inner = RecordingClient()
    client = FilteringClient(inner, FilterPolicy(hide_action_events=True), "Layla")
    client.set_meta_context("Layla", "execution", 1, None)
    _run(client, layla)
    sent = inner.seen_input[0][1]["content"]
    assert "[action_executed]" not in sent
    assert "=== CURRENT ASSIGNMENTS ===" in sent
    assert "- Jeanene: ISSUE-0001::test" in sent, "E must not touch Path A"
    assert client.filter_stats["events_removed"] == 2


def test_assignment_filter_leaves_the_event_path():
    layla = _prompt("layla_execution_prompt.txt")
    inner = RecordingClient()
    client = FilteringClient(inner, FilterPolicy(mask_current_assignments=True), "Layla")
    _run(client, layla)
    sent = inner.seen_input[0][1]["content"]
    assert ASSIGNMENT_MASK in sent
    assert "- Jeanene: ISSUE-0001::test" not in sent
    assert "[action_executed]" in sent, "masking state alone must not remove the event"


def test_both_paths_removed_only_under_S():
    layla = _prompt("layla_execution_prompt.txt")
    inner = RecordingClient()
    client = FilteringClient(inner, policy_from_config("S"), "Layla")
    _run(client, layla)
    sent = inner.seen_input[0][1]["content"]
    assert "[action_executed]" not in sent
    assert "- Jeanene: ISSUE-0001::test" not in sent
    assert "ISSUE-0001::docs" not in sent.split("=== CURRENT ASSIGNMENTS ===")[1].split("=== BLACKBOARD")[0]


def test_post_message_blocked_for_target_only():
    layla = _prompt("layla_execution_prompt.txt")
    scoped = FilterPolicy(block_post_message=True, agents=("Layla",))
    inner = RecordingClient()
    client = FilteringClient(inner, scoped, "Layla")
    _run(client, layla, tools=_tools())
    assert [t["name"] for t in inner.seen_params[0]["tools"]] == ["assign_task"]

    other = RecordingClient()
    plain = FilteringClient(other, scoped, "Pauline")
    _run(plain, layla, tools=_tools())
    assert len(other.seen_params[0]["tools"]) == 2, "non-target agent must keep messaging"
    assert other.seen_input[0][1]["content"] == layla


def test_V_preset_blocks_messaging_for_everyone():
    layla = _prompt("layla_execution_prompt.txt")
    inner = RecordingClient()
    client = FilteringClient(inner, policy_from_config("V"), "Pauline")
    _run(client, layla, tools=_tools())
    assert [t["name"] for t in inner.seen_params[0]["tools"]] == ["assign_task"]


def test_agent_scoping_ignores_others():
    layla = _prompt("layla_execution_prompt.txt")
    inner = RecordingClient()
    client = FilteringClient(inner, FilterPolicy(hide_action_events=True, agents=("Jeanene",)), "Layla")
    _run(client, layla)
    assert inner.seen_input[0][1]["content"] == layla
    assert client.filter_stats["calls"] == 0


def test_first_mover_prompt_is_unaffected():
    jeanene = _prompt("jeanene_execution_prompt.txt")
    assert "[action_executed]" not in jeanene and "CURRENT ASSIGNMENTS" not in jeanene
    inner = RecordingClient()
    client = FilteringClient(inner, policy_from_config("S"), "Jeanene")
    _run(client, jeanene)
    assert inner.seen_input[0][1]["content"] == jeanene


def test_policy_rejects_unknown_preset():
    try:
        policy_from_config("Z")
    except ValueError as exc:
        assert "unknown observation_filter preset" in str(exc)
        return
    raise AssertionError("expected ValueError")


def test_describe_records_the_roster_it_was_bound_to():
    # run.py writes filter_policy.describe() into run_config.json, so the roster an arm
    # actually ran with has to be visible there. Every artifact written before the binding
    # was moved shows "roster": [], which is indistinguishable from a policy that hides
    # nothing -- the metadata has to agree with the behaviour.
    policy = policy_from_config("V").with_roster(("Jeanene", "Pauline", "Layla", "Mona"))
    d = policy.describe()
    assert d["roster"] == ["Jeanene", "Pauline", "Layla", "Mona"]
    assert d["block_post_message"] is True
    assert policy_from_config("V").describe()["roster"] == []


def test_gemini_style_parts_are_filtered():
    text = _prompt("layla_execution_prompt.txt")
    parts = [{"type": "text", "text": text}]
    inner = RecordingClient()
    client = FilteringClient(inner, FilterPolicy(hide_action_events=True, mask_current_assignments=True), "Layla")
    client.generate_response([{"role": "user", "content": parts}], {"model": "m"})
    assert parts[0]["text"].count("[action_executed]") == 0
    assert ASSIGNMENT_MASK in parts[0]["text"]


def test_scoped_policy_still_blanks_the_whole_roster():
    layla = _prompt("layla_execution_prompt.txt")
    scoped = FilterPolicy(canonicalise_actions=True, agents=("Layla",)).with_roster(
        ("Jeanene", "Pauline", "Layla")
    )
    assert scoped.applies_to("Layla") and not scoped.applies_to("Pauline")
    sent = scoped.filter_text(layla)
    assert "Pauline" not in sent, "a policy scoped to one agent must still hide the others"


def test_C_preset_neutralises_without_deleting():
    layla = _prompt("layla_execution_prompt.txt")
    n_ids = len(_TASK_ID.findall(layla))
    assert n_ids >= 2
    inner = RecordingClient()
    policy = policy_from_config("C").with_roster(("Jeanene", "Pauline", "Layla"))
    client = FilteringClient(inner, policy, "Layla")
    _run(client, layla)
    sent = inner.seen_input[0][1]["content"]
    assert sent.count("[action_executed]") == layla.count("[action_executed]"), "C must not delete events"
    assert len(sent.split("\n")) == len(layla.split("\n")), "C must not change episode length"
    assert "ISSUE-0001::test" not in sent and "ISSUE-0001::docs" not in sent
    tokens = TASK_TOKEN.findall(sent)
    assert len(tokens) == n_ids and not _TASK_ID.search(sent)
    assert len(set(tokens)) == len(set(_TASK_ID.findall(layla))), "distinct tasks must not collapse to one token"
    assert "Jeanene" not in sent and "Pauline" not in sent and AGENT_CANON in sent
    assert _JOINT_REWARD.search(sent) is None, "the running joint_reward must not survive"
    assert client.filter_stats["tasks_canonicalised"] == n_ids


def test_C_blanks_the_agent_name_in_prose_and_payload_alike():
    layla = _prompt("layla_execution_prompt.txt")
    policy = policy_from_config("C").with_roster(("Jeanene",))
    sent = policy.filter_text(layla)
    assert "Jeanene" not in sent
    assert '"agent":"[member]"' in sent or '"agent": "[member]"' in sent


def test_filter_without_roster_leaves_names():
    policy = policy_from_config("C")
    assert "Jeanene" in policy.filter_text("Jeanene takes ISSUE-0001::test")
    assert TASK_TOKEN.search(policy.filter_text("Jeanene takes ISSUE-0001::test"))


def test_C_restores_the_token_in_the_action_argument():
    """The model can only name a task by the token it was shown, and the environment rejects an
    unknown task_id, so arm C is only runnable if the filter expands its own output on the way out."""
    class EchoClient(RecordingClient):
        def __init__(self):
            super().__init__()
            self.forwarded = None

        async def process_tool_calls(self, response, context, execute_tool_callback):
            self.forwarded = response
            return 1, context, ["assign_task"]

    layla = _prompt("layla_execution_prompt.txt")
    real = _TASK_ID.findall(layla)[0]
    inner = EchoClient()
    client = FilteringClient(inner, policy_from_config("C").with_roster(("Jeanene",)), "Layla")
    _run(client, layla)
    token = TASK_TOKEN.search(inner.seen_input[0][1]["content"]).group(0)
    response = {"choices": [{"message": {"tool_calls": [{
        "id": "c1", "function": {"name": "assign_task", "arguments": json.dumps({"task_id": token})},
    }]}}]}
    asyncio.run(client.process_tool_calls(response, [], None))
    sent = json.loads(inner.forwarded["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"])
    assert sent["task_id"] == real
    assert client.filter_stats["actions_restored"] == 1


def test_client_contract_matches_terrarium():
    """terrarium runs generate_response through run_blocking (a thread pool) and awaits
    process_tool_calls directly. Getting either wrong yields an un-awaited coroutine, so the
    wrapper's syncness is part of the contract, not a style choice."""
    import inspect
    from llm_server.clients.abstract_client import AbstractClient

    assert not inspect.iscoroutinefunction(FilteringClient.generate_response)
    assert not inspect.iscoroutinefunction(AbstractClient.generate_response)
    assert inspect.iscoroutinefunction(FilteringClient.process_tool_calls)


def main() -> int:
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print("  PASS  %s" % name)
        except Exception as exc:
            failures += 1
            print("  FAIL  %s -> %s: %s" % (name, type(exc).__name__, exc))
    print("\n%d/%d passed" % (len(tests) - failures, len(tests)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
