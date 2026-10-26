# Runner repair

The repair lives in the shared collusion runner and in `experiments/collusion/metric_validation/`. Paper 1 (`experiments/collusion/tool_selection/`) was not edited. Configurations that do not set `coalition_prompt` or `observation_filter` keep the previous behavior: `coalition_prompt` defaults to `auto`, and an inactive filter does not wrap the client.

The seven arm yaml files were copied from commit `5feedab` into `metric_validation/configs/` and were not retuned.

## What was wrong

At `5feedab`, `experiments/collusion/run.py` is identical to its parent. That runner:

1. Never constructs `FilteringClient`, so the observation-filter flags in the yaml are unused.
2. Accepts only `random` and `first` in `_select_colluders`. Every arm sets `first_and_last`, which raises before an episode starts.
3. Forces the prompt variant to `control` and the role to normal whenever `secret_channel_enabled` is false. The `coalition_prompt` key is ignored, so V, E, C, and S lose the coalition objective.
4. Names provider `openrouter`. This terrarium build does not implement that provider. `get_model_name` raises `Unknown provider: openrouter`. The PDF names Google's endpoint and the same model string. Those are not the same route, and the historical logs that would settle the route were not recovered.

## What changed

`first_and_last` returns the first and last names in the generated roster and does not draw from the seed RNG. It requires exactly two colluders. On the path used here, those names are the two endpoints. The random turn-order shuffle still consumes the same stream it would have consumed with no earlier draw.

`experiment.collusion.coalition_prompt` is one of:

| Mode | Secret channel off | Secret channel on |
| --- | --- | --- |
| absent or `auto` | cooperative prompt, no coalition role | configured prompt for coalition members |
| `always` | configured prompt for coalition members | configured prompt for coalition members |
| `never` | cooperative prompt for everyone | cooperative prompt for everyone |

An unknown mode raises. It is not coerced.

`FilteringClient` wraps each agent client only when the observation policy is active. Paper 1 configs have no `observation_filter` block, so they are not wrapped. The wrapper records each request after filtering, and `_run_single` writes those records to `model_requests.json` when any wrapped client sent one. `run_config.json` now also stores `agent_names`, `coalition_prompt`, the filter description, and `agent_turn_order`.

## Intended arm semantics, checked against the copied yaml

| Arm | Coalition objective | Private channel | Observation policy |
| --- | --- | --- | --- |
| B0 | off (`never`) | off | none |
| P | on, because the secret channel is on and the key is absent (`auto`) | on | none |
| V | on (`always`) | off, and `post_message` is removed | no event or assignment hiding |
| S | on (`always`) | off, and `post_message` is removed | hide action events and mask the assignment list |
| B1 | off (`never`) | off | same hiding as S |

E and C are not in the new cohort. Their copied configs still say `always`, with event hiding only (E) or canonicalization only (C). The request-boundary tests cover C.

## What was not changed

Prompts, scores, topologies, seeds in the yaml, temperature, and max tokens were not edited to make a configuration execute. The production runner still raises on provider `openrouter`. The replication launcher, not the yaml and not the shared runner, points a copy of the config at the installed Gemini client and records that substitution. See `run_replication.py`.

`post_message` is a planning-phase tool in the environment. Its absence from an execution request is phase gating, not evidence that the filter ran.

The installed Gemini client does not use an OpenAI `content` field. Its context is `parts[].text` plus `_system_prompt`. The wrapper now rewrites those fields before the inner client sees them. A request-boundary test uses `GeminiClient.init_context` and checks the inner client's copy. The first live episode was stored before that rewrite existed; it is kept under `outputs/replication/invalid_unfiltered/` and is not an S run.
