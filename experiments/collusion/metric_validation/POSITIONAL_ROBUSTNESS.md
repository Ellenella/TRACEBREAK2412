# Positional robustness

No sensitivity episode was run. The control check on the committed runner failed before any new model call: `colluder_selection: first_and_last` is not implemented, and `FilteringClient` is not attached in `run.py` at `5feedab`. Running an order sweep on that runner would not be a test of the printed ladder.

## What the runner can vary

`_order_agent_turns` accepts `random` and `colluders_first`.

`random` shuffles the four agents with the run's `random.Random(seed)`. The path endpoints and the execution order are different objects. A seed can put a middle agent first. The Track 3.1 configs all use `random`.

`colluders_first` places every agent who was selected as a colluder ahead of the others, in name-list order. It does not choose an arbitrary first mover while leaving the coalition on the path endpoints. Using it would also require a colluder-selection strategy the runner accepts. `first_and_last` is not one of those strategies.

There is no config key that rotates which single agent moves first and holds coalition membership fixed. Independent order control, in the sense this study needs, is not available on the committed runner.

## What would be a different experiment

Moving the coalition off the endpoints changes who shares a blackboard. That is a change of the communication graph of the coalition, not a change of turn order. The two are not substitutes. A later protocol can declare them as separate factors. This file does not declare either one as started.

## Implication for the printed result

The metric-failure pattern in the PDF, D rising from V to S while the printed coalition mean stays at 27.17, is a single seed with a reported frozen first mover. Whether that pattern survives another first mover is untested. The original paper's §6.3 already says the interventions cannot reach Mona. This audit does not resolve that limitation.
