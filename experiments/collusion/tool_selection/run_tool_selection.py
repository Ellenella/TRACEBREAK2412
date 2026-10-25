"""Run the tool-selection extension through the frozen runner without editing it."""

from __future__ import annotations

import experiments.collusion.run_tracebreak as runner
from experiments.collusion.tool_selection.prompts import ToolSelectionPrompts
from experiments.collusion.tool_selection.protocol import ToolSelectionProtocol

# Importing the environment module registers the tool class.
from experiments.collusion.tool_selection import env as _env  # noqa: F401


def main() -> None:
    runner.CollusionPrompts = ToolSelectionPrompts
    runner.LocalCommunicationProtocol = ToolSelectionProtocol
    runner.main()


if __name__ == "__main__":
    main()
