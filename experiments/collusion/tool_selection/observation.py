"""Observation-boundary canonicalization for tool identity.

The executed tool is unchanged. Only the text placed in another agent's
blackboard section is rewritten.
"""

from __future__ import annotations

import re

from experiments.collusion.tool_selection.tools import TOOL_NAMES

CANONICAL_TOOL = "assign_task"
_UUID = re.compile(
    r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b"
)
CODEBOOK_HEADER = "=== EXPLORATORY TOOL-SELECTION RULE"


def canonicalize_observation_text(text: str) -> str:
    rendered = text
    for name in sorted(TOOL_NAMES, key=len, reverse=True):
        rendered = rendered.replace(name, CANONICAL_TOOL)
    return rendered


def observation_leaks_selected_tool(text: str) -> bool:
    return any(name in text for name in TOOL_NAMES)


def normalize_run_identifiers(text: str) -> str:
    """Drop event UUIDs so two runs of the same seed can be compared."""
    return _UUID.sub("UUID", text)


def receiver_observation_body(prompt: str) -> str:
    """Rendered user prompt excluding the fixed codebook.

    Callable tool schemas are not part of this text. They remain available
    as functions. A difference here can reveal which tool was selected.
    """
    cut = prompt.find(CODEBOOK_HEADER)
    body = prompt if cut < 0 else prompt[:cut]
    return normalize_run_identifiers(body).strip()
