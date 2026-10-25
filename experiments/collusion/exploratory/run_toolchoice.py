"""Launch the tool-choice prototype without editing run_tracebreak.py.

Patches the prompt class used by the frozen runner, then calls its main().
"""

from __future__ import annotations

import experiments.collusion.run_tracebreak as runner
from experiments.collusion.exploratory.prompts_toolchoice import ToolChoicePrompts


def main() -> None:
    runner.CollusionPrompts = ToolChoicePrompts
    runner.main()


if __name__ == "__main__":
    main()
