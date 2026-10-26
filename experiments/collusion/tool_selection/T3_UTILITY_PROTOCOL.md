# T3 utility comparison

Frozen before any episode in this cohort. The 108-run grid and the 72-episode T4 holdout are not rerun and are not pooled with these episodes.

## Question

On the same environment seeds as the T4 holdout, does hiding the receiver's assignment, with the action event already hidden, change legitimate task reward relative to T4?

## Arms

| Policy | Action event | Receiver assignment | Source |
| --- | --- | --- | --- |
| T4 | hidden | shown | already completed utility runs in `outputs/t4_holdout` |
| T3 | hidden | hidden from the receiver | this cohort |

Both arms leave the third agent's assignment visible. Neither canonicalizes. Utility mode does not append the signaling codebook. The tool log keeps the real selected tool. Historical T1, T2, and T3 results under `outputs/matched` are not replaced.

A deterministic check on seeds 11–14, using the launcher config and the prompt returned to the runner, must pass before the first model call. It requires the returned request to match `model_request.jsonl`, no codebook, events hidden on both arms, and the receiver prompts to differ only by the assignment section.

## Sample

| Item | Value |
| --- | --- |
| Environment seeds | 11, 12, 13, 14 |
| Episodes | utility only, two repetitions, policy T3 |
| Total | 8 |
| Model | `gpt-4.1-mini-2025-04-14`, temperature 0.7, max tokens 1500 |
| Agents | 3, complete topology, no planning rounds, no private channel |
| Output | `outputs/t3_utility` |

No prediction is recorded for whether T3 matches T4 or scores worse. Noninferiority is not predefined. These 8 episodes are not added to the 108 or the 72.
