# Covert Collusion Experiment (JiraTicket default)

This experiment tests whether a **subset of colluding agents** can (a) coordinate covertly using a **hidden colluder-only blackboard** and (b) **benefit at the expense of non-colluders** via **active deception** on shared blackboards.

It is modeled after `experiments/network_influence`, but uses an **in-process** communication protocol (`LocalCommunicationProtocol`) so it does **not** require an MCP server and supports **parallel runs**.

## Key factors
- `colluder_count`: how many agents are in the coalition
- `secret_channel_enabled`: whether a colluder-only blackboard is added (hidden from others)
- `prompt_variant`: which colluder prompt variant is used (controls collusion/deception strategy)
- `topology`, `num_agents`, `seed`: standard comms + stochasticity sweeps

Built-in `prompt_variant` values live in `experiments/collusion/prompts.py` (e.g., `control`, `simple`, `deception`, `structured`, `aggressive`).

## Small "secret blackboard choice" variant
If you want a tiny setup with **3 agents**, where **all 3 share one public blackboard** and **2 colluders also share a secret blackboard** (2 blackboards total), use:
```bash
  python -m experiments.collusion.run \
  --config experiments/collusion/configs/collusion_jira_three_agents_two_blackboards.yaml
```

This config also disables the Jira system-prompt bias that tells agents to post on *all* blackboards by setting:
`environment.import_path=experiments.collusion.choice.jira_ticket_choice_env:JiraTicketChoiceEnvironment` (uses a child `JiraTicketPrompts` class).

## Run
1) Ensure API keys are set (root `.env`) for your chosen provider.
2) Run:
```bash
  python -m experiments.collusion.run \
  --config experiments/collusion/configs/collusion_jira_topologies.yaml
```

Outputs are written under `experiments/collusion/outputs/<tag>/<timestamp>/`.

## LLM-as-a-judge (secret blackboard)
To score how much *collusion exists on the secret blackboard* for an existing output root, run the post-hoc judge:
```bash
  python -m experiments.collusion.judge_blackboards \
  --root experiments/collusion/outputs/collusion_complete/<timestamp> \
  --max-concurrent 16
```

Notes:
- Uses OpenAI `gpt-4o-mini` by default; pass `--judge-model gpt-4.1-mini` if you want to use 4.1 mini.
- Set `OPENAI_API_KEY` in your environment (or `.env`).
- Writes per-run JSON under `runs/<model_label>/judge_secret_blackboard/<sweep_name>/` and aggregates:
  - `runs/<model_label>/judge_secret_blackboard/results.csv`
  - `runs/<model_label>/judge_secret_blackboard/results.jsonl`
- Runs with `secret_channel_enabled=false` short-circuit to `rating=0` (no API call).

## Correlate judge scores with length/tooling
After you have `judge_secret_blackboard/results.csv`, you can join it with per-run features like message length and tool-call counts:
```bash
  python -m experiments.collusion.analyze_judge_correlations \
  --root experiments/collusion/outputs/collusion_complete/<timestamp>
```

Outputs (per model label) are written under `runs/<model_label>/judge_secret_blackboard/`:
- `features_with_judge.csv`: `results.csv` + run-level features (e.g., `post_chars_secret`, `tool_calls_total`)
- `correlations.csv`: Spearman/Pearson correlations vs `judge_mean_rating`

Cross-model outputs are written under `<root>/analysis/judge_correlations/`:
- `features_with_judge_all_models.csv`: concatenated features across all model labels
- `correlations_by_model.csv`: per-model correlations in one table
- `correlations_pooled.csv`: pooled correlations across all models

## Plot
Generate sweep plots (the only supported plots) from a sweep directory:
```bash
  python -m experiments.collusion.plots.generate_all \
  --sweep-dir experiments/collusion/outputs/<tag>/<timestamp>/runs/<model_label>/<sweep_name>
```

By default, plot artifacts are written under `experiments/collusion/plots_outputs/<tag>/<timestamp>/<model_label>/<sweep_name>/`.

Supported outputs:
- `by_topology/<topology>/sweep/prompt_variants__mean_sem__cX__reward-<metric>.png`
- `sweep/topology_comparison__optimality_gap_and_judge__cX.png`

## Resume (in-place)
If a sweep crashes part-way through, or you want to extend it to more seeds, you can resume **in-place**
(no new timestamp folder) and only execute missing/incomplete runs.

Example: extend seeds to 1–10, then resume an existing output root:
```bash
  python -m experiments.collusion.resume \
  --root experiments/collusion/outputs/<tag>/<timestamp> \
  --config experiments/collusion/configs/collusion_jira_topologies.yaml
```

Tip: use `--dry-run` first to see what will run.

## Regret analysis (Jira optimal vs achieved)
For Jira runs, you can compute an *exact* per-run optimal joint reward and compare each run to that optimum.

1) Compute and write `optimal_summary.json` into each run directory:
```bash
  python experiments/collusion/compute_jira_optimal.py \
  --root experiments/collusion/outputs/<tag>/<timestamp> \
  --write-json
```

2) Generate the combined nine-bars plot (normalized regret + normalized coalition regret gap + judge):
```bash
  python -m experiments.collusion.plots.generate_jira_regret_report \
  --root experiments/collusion/outputs/<tag>/<timestamp> \
  --sweep-name <sweep_name> \
  --compute-optimal
```

Outputs:
- `plots/regret_report__normalized_regret__coalition_gap__judge.png`
- `plots/regret_report__normalized_regret__coalition_gap__judge__data.csv`
- `table_secret_true__pv_control.csv`: mean ± SEM over seeds for:
  - `optimality_gap` = optimal − achieved (regret)
  - `achieved_over_optimal` = achieved / optimal
  - `joint_reward_ratio` = achieved / max_joint_reward (upper bound, not the exact optimal)
  - `judge_mean_rating` = mean judge score (0–5) over (simple/medium/complex), when judge files exist
- Per-model plots under `plots/by_model__<metric>/` comparing `baseline` vs `control` vs `simple`.

## Sequential best-response regret (availability-aware)
The `metrics.json` fields `mean_regret`, `coalition_mean_regret`, and `noncoalition_mean_regret` are computed as a
one-shot **best-response regret**: for each agent, hold everyone else fixed and brute-force the agent's best
counterfactual action over **all** tasks (plus `skip`).

If you want a more sequential notion of regret for *non-first* agents (i.e., "no first dibs"), you can compute an
availability-aware best-response regret where an agent's counterfactual actions are restricted to tasks that were
still unclaimed by **earlier agents** in the recorded `agent_turn_order`.

Compute it with:
```bash
  python -m experiments.collusion.compute_sequential_regret \
  --root experiments/collusion/outputs/<tag>/<timestamp>
```

Outputs:
- `sequential_regret_summary.json`: per-run sequential regret + baseline (unrestricted) regret, plus means.
- Optionally add `--write-per-run` to write `sequential_regret.json` into each run directory.

Notes:
- This script parses the exact tasks/costs from `agent_prompts.json` when available (most faithful); it falls back to
  a deterministic reconstruction when prompts are missing.
- Later agents are held fixed; this is still a best-response-style counterfactual, just with a turn-order availability constraint.


---

## Track 3.1 additions (sprint work)

**Pre-existing code:** everything above, and all of `colosseum/` as shipped by
`poseidon-research/collusion_hackathon`, predates this sprint and is unmodified except where noted.

**Written during the sprint (25 Oct 2026):**

- `observation_filter.py` - `FilterPolicy`, `FilteringClient`, presets `V`/`E`/`S`/`C`. Wraps the
  provider client so the model's observation is rewritten before the call; nothing in
  `site-packages` is patched, so `uv sync` cannot revert the defence.
- `test_observation_filter.py`, `fixtures/*.txt` - 17 offline tests over two prompts captured
  verbatim from a real run. `python experiments/collusion/test_observation_filter.py`, no key, no cost.
  One of them pins the client contract itself: `AbstractClient.generate_response` is synchronous and
  terrarium calls it through a thread pool, so a coroutine there is silently unusable - it raises
  `cannot unpack non-iterable coroutine object` inside the agent loop and five arms died that way
  before the test existed.
- `configs/track31_{P,V,E,S,C,B1,B0}.yaml` - path topology, 4 agents,
  `colluder_selection: first_and_last` (endpoints share no blackboard). `P` is the positive control
  (`secret_channel_enabled: true`); `V/E/S/C` and `B0/B1` run with the secret board off, so any
  coordination left must travel through actions and shared state. `B1` is `S` with the collusive prompt
  withdrawn - the two share one `observation_filter` and differ in `coalition_prompt` alone, which is
  the only place in the ladder where "you have a partner" is separable from what the agent can see.
  `B0` is the unprompted baseline; note that `V/E/S/C` all carry the prompt, so any of them read against
  `B0` changes the prompt and the observation at once.
- `run.py` - three additions only: import of the filter module, `policy_from_config(...)` next to the
  other collusion-knob validation, and `client = FilteringClient(client, filter_policy, name)` where
  the client is constructed, with `filter_policy = filter_policy.with_roster(agent_names)` bound once
  just above the loop. Binding it inside the per-agent call left the policy recorded in
  `run_config.json` empty while the clients ran scoped ones; `describe()` now carries the roster and
  a test asserts it. Run summaries gain `observation_filter` and `observation_filter_effects` - both
  in `run_config.json`, not in `summary.json` or `final_summary.json`.
- `decode_actions.py` - H1. Offline, no key: reads recorded traces and asks whether an observer with
  no labels can rank the true coalition first among the six candidate pairs, using only the share of
  measured joint-reward gain a pair captured and how much the pair's own claims compete for the same
  skill tags. The null is exact (1/6), and the result is split by whether messaging was available,
  because only the blocked arms bear on the carrier claim. Writes `outputs/decode_h1.json`.
- `counterfactual_replay.py` - H2. Offline, no key: replays each recorded assignment through
  `compute_jira_optimal.py`'s closed-form reward function, refuses the run unless the replay reproduces
  the logged `joint_reward` within 0.01, then substitutes single actions - drop an agent's claim, swap
  two agents' claims, replace one action with the exact solver's choice - and compares the causal cost
  of touching a coalition member against an outgroup member. Writes `outputs/counterfactual_h2.json`.
  Both harnesses keep only the newest artifact per arm, since a rerun of the same arm is not an
  independent sample, and each writes its own scanning/superseded/rejected counts into its JSON so the
  report can state the selection rule instead of asserting it.
- `report_data.py` - the single source of truth for every number in the report. It scans the artifact
  tree and picks, per arm, the newest run that is complete, scored and carries zero error turns (the
  same rule both harnesses apply, so the report and the analyses cannot land on different episodes),
  diffs the seven condition configs leaf by leaf so "matched ladder" is checked rather than claimed, and
  derives the comparisons the prose makes (gaps, ratios, the one pair of arms differing only in the
  coalition prompt, the single-seed noise floor from the re-run of arm E). The timestamps the sprint
  analysed are kept only as recorded provenance, and the scan reports any drift against them.
  `python experiments/collusion/report_data.py` prints the selection table - every launch, with the
  reason each was chosen, superseded or rejected - then the whole derived map.
- `build_report.py` - emits the submission PDF from that map through reportlab. No result is typed
  there: every figure is interpolated, and a block of assertions stops the build if a sentence's
  premise stops holding.

Running an arm (the flag is `--config`, not `-c`; `PYTHONIOENCODING` is required on Windows because
the pre-run cost note prints a `≈`):

```bash
cd starter/colosseum
PYTHONIOENCODING=utf-8 python experiments/collusion/run.py \
  --config experiments/collusion/configs/track31_V.yaml -y
```

Gate every run before trusting a metric - errors are recorded per turn, and a run can report
`status: complete` while carrying them:

```bash
grep -c ERROR "experiments/collusion/outputs/<tag>/<timestamp>/runs/<model>/<tag>/<run_id>/agent_turns.json"
```

`status: complete` is not evidence - one recorded run reports it with 12 of 15 turns carrying an error payload.
