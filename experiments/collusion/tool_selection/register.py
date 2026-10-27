"""Register the tool-selection toolset without editing Terrarium.

Terrarium discovers Tools classes only from installed ``envs/**/*_tools.py`` modules.
This extension inserts its class into that registry at runtime.
"""

from __future__ import annotations

from terrarium import environment_tools

from experiments.collusion.tool_selection.tools import JiraTicketToolSelectionTools

ENV_NAME = "JiraTicketToolSelectionEnvironment"


def register() -> None:
    environment_tools._discover_tools()
    environment_tools._TOOL_CLASS_BY_ENV_NAME[ENV_NAME] = JiraTicketToolSelectionTools
    environment_tools._TOOL_CLASS_BY_NAME[JiraTicketToolSelectionTools.__name__] = (
        JiraTicketToolSelectionTools
    )


register()
