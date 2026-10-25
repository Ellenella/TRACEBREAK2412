# Original experiment provenance

Checked on 25 October 2026. No episode was rerun for this note, and no model response was reconstructed.

## Source commit

Branch `origin/track31-action-carriers`, commit `5feedab` (`Add the Track 3.1 arm ladder, offline analyses and report pipeline`), parent `35a414d`.

That commit adds:

- `experiments/collusion/observation_filter.py`
- `experiments/collusion/test_observation_filter.py`
- `experiments/collusion/configs/track31_{B0,B1,C,E,P,S,V}.yaml`
- `experiments/collusion/report_data.py`, `decode_actions.py`, `build_report.py`, `counterfactual_replay.py`
- `experiments/collusion/track31-patches/0001` through `0010`
- `experiments/collusion/README.track31.md`

`git diff 35a414d 5feedab` is empty for `run.py`, `prompts.py`, and `metrics.py`. The patch file describes a twelve-line edit to `colosseum/experiments/collusion/run.py` that would wrap the client. That hunk is not in the committed `experiments/collusion/run.py`.

## Execution configuration, as committed

Every arm config sets a path of four agents, `colluder_selection: first_and_last`, `agent_order: random`, `max_conversation_steps: 1`, `max_planning_rounds: 2`, `max_tasks: 8`, and `seeds: [1]`.

| Arm | Secret channel | Prompt variant in the sweep | `coalition_prompt` | Filter flags |
| --- | --- | --- | --- | --- |
| B0 | false | control | never | none (`agents: []`) |
| P | true | simple | absent, so the historical runner treats it as auto | no filter block |
| V | false | simple | always | `block_post_message` |
| E | false | simple | always | `block_post_message`, `hide_action_events` |
| C | false | simple | always | `canonicalise_actions` |
| S | false | simple | always | `block_post_message`, `hide_action_events`, `mask_current_assignments` |
| B1 | false | control | never | same flags as S |

The provider block in every config is OpenRouter, model `gemini-3.5-flash-lite`, temperature 0.7, max tokens 1500. The PDF says the calls went through Google's OpenAI-compatible endpoint on a free-tier key. Those are not the same route. The committed runner cannot say which one was used.

## What the committed runner would have done

`_select_colluders` at `5feedab` accepts `random` and `first` only. `first_and_last` raises before an episode starts. The observation filter is never constructed. When the secret channel is off, the prompt variant is forced to `control` and no agent receives the coalition role. Under that runner, V, E, S, and C would not have carried the coalition prompt even if selection had succeeded, and P is the only arm whose sweep turns the secret channel on.

## Saved outputs

`**/outputs/` is gitignored. Commit `5feedab` contains none of the episode directories. The timestamps in the PDF appendix (B0 `20261025-033526`, P `20261025-033446`, V `20261025-035049`, E `20261025-035127`, C `20261025-034506`, S `20261025-035220`, B1 `20261025-035246`) occur in `report_data.py` as recorded provenance, not as `agent_turns.json`, `tool_events.json`, `run_config.json`, or `final_summary.json`.

This worktree's `experiments/collusion/outputs/` has the TRACEBREAK tags only. No `track31_*` directory was found there. No tool-event log and no model request from the seven-arm table is available.

## Conclusion

The exact code and logs that generated the printed seven-arm table cannot be recovered from this repository. The table remains a printed result. It is not an artifact-backed result. The filter module and the seven configs are recoverable. The runner wiring, the endpoint, and the episode logs are not.
