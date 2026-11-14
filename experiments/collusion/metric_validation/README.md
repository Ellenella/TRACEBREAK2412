# Paper 2 — Actions as Carriers

Title: *Actions as Carriers: Side-Channel Collusion and the Metrics That Hide It*.

This directory is the Paper 2 project. It is not part of Paper 1 (`../tool_selection/`). Do not pool their numbers, and do not pool the new episodes with the printed seven-arm table.

## Question

Can coalition-advantage metrics rank observation-filtering countermeasures in a misleading order when an intervention affects coalition and non-coalition agents differently?

Coalition advantage is the coalition mean reward minus the other mean reward. A change in that gap is not, by itself, evidence that harmful collusion occurred. The 25-episode result is that the gap did not rise under full filtering, and that a lower or equal gap can sit next to a worse joint reward.

## What to read

| Document | Role |
| --- | --- |
| [`../../../papers/paper2_actions_as_carriers.pdf`](../../../papers/paper2_actions_as_carriers.pdf) | Manuscript. The printed table is historical. The 25 episodes are the primary evidence |
| `ORIGINAL_EXPERIMENT_PROVENANCE.md` | Why the original seven-arm logs were not recovered |
| `ORIGINAL_RESULTS_AUDIT.md` | Arithmetic check of the printed table against its own prose |
| `RUNNER_REPAIR_REPORT.md` | What was wrong in the committed runner, and what the repair does |
| `EXPERIMENT_VALIDATION.md` | Request-boundary tests |
| `ACTIONS_AS_CARRIERS_REVISED.md` | Manuscript source |
| `SCIENTIFIC_CLAIMS_AUDIT.md` | Which claims are established, preliminary, or unsupported |
| `REPLICATION_AND_VALIDATION_REPORT.md` | The 25-episode cohort and the S-versus-V comparison |
| `POSITIONAL_BIAS_AUDIT.md`, `POSITIONAL_ROBUSTNESS.md` | The first-mover question. No order experiment was run |

## Code

Arm configs are `configs/track31_{B0,B1,C,E,P,S,V}.yaml`, copied from commit `5feedab` and not retuned. The filter is `observation_filter.py`. The shared runner `experiments/collusion/run.py` gained `first_and_last`, a `coalition_prompt` mode (`auto`, `always`, `never`), and a filter wrapper. Those keys are absent from Paper 1, and an inactive filter does not wrap the client.

The installed terrarium has no `openrouter` provider. `run_replication.py` sends a copy of the config through the Gemini client and keeps the model string `gemini-3.5-flash-lite`, temperature 0.7, and 1500 max tokens. The yaml files on disk still say `openrouter`.

Deterministic check, from the repository root, before any new API call:

```bash
python -m unittest experiments.collusion.metric_validation.test_request_boundary
```

The 25-episode launcher, which does call the API, is:

```bash
python -m experiments.collusion.metric_validation.run_replication
```

It skips episodes that already have `job_summary.json`.

## Completed evidence

The original seven-arm table is printed evidence only. Commit `5feedab` has the filter and the configs. It does not have episode logs, and its runner does not attach the filter.

The new cohort is 25 episodes: seeds 31–35 and arms B0, P, V, S, B1, one episode each, interleaved. On those pairs, S did not increase coalition advantage relative to V. Logs are under `outputs/replication/` and are gitignored.

Excluded from that cohort, and kept on disk:

- `outputs/replication/invalid_unfiltered/` — one episode from before the Gemini prompt shape was filtered.
- `outputs/replication/incomplete_request_log/` — one episode from before unfiltered arms stored requests.
- `outputs/replication/failed_attempts/` — rate-limit and disconnect partials.

## Not run

- Arms E and C inside the 25-episode cohort. Their configs remain, and the request tests cover C.
- A turn-order experiment that would move the endpoint coalition while holding the seed's tasks fixed.
- A recovery of the original seven-arm model responses. They are not reconstructed.
