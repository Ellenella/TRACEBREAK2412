# T3 versus T4 on seeds 11–14

Utility episodes only. T4 is the completed holdout and is not rerun. T3 is eight new episodes under `outputs/t3_utility`. Neither set is pooled with the 108-run cohort on seeds 1–3.

The question was whether hiding the receiver's assignment, rather than deleting the action event, accounts for the coordination failures previously seen under T3. Both policies already hide the action event. The protocol in `T3_UTILITY_PROTOCOL.md` was frozen before these eight calls. No noninferiority margin was set.

## Deterministic contrast

Before any model call, seeds 11–14 were checked with the launcher configuration and the prompt `get_user_prompt` returns. That returned string is what `model_request.jsonl` stores. On each seed:

- T3 and T4 both hide action events, leave canonicalization off, and leave the codebook off.
- T3 sets the assignment mask to the receiver. T4 does not.
- The executed assignment and the tool log match. The log records `assign_task_direct`.
- Sender and third-agent prompts match across the two policies.
- Receiver prompts differ only by the current-assignment section. T4 contains it, including `ISSUE-0001::review`. T3 does not.
- Neither receiver prompt contains an action event or a selected tool name.

That check is a property of the constructed request. It is not a claim about what the model later did. The unit suite, including this check, was 11 tests, `OK`.

## Episodes

Eight T3 jobs, two utility repetitions on seeds 11, 12, 13, and 14. All eight returned exit code 0 and `status=complete`. No failed attempt was produced. Model settings in every returned request: `gpt-4.1-mini-2025-04-14`, temperature 0.7, max tokens 1500. Codebook flag false for every agent. Event hiding true. Canonicalization false. The mask in the logged request is the receiver's name.

The same request-boundary comparison used on the 72 holdout episodes holds here. `model_request.jsonl` matches the returned-phase prompt. The execution-phase prompt is the same string, because utility mode does not append a codebook.

The two repetitions on each seed produced the same assignment and the same joint reward. The table uses that repeated value once. T4 values are the stored holdout utility runs, also identical across their two repetitions, rounded to three decimals as in `T4_MATCHED_RESULTS.md`.

| Seed | T3 joint | T4 joint | T3 − T4 | T3 distinct | T4 distinct | T3 violations | T4 violations | T3 duplicate |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 11 | 87.354 | 106.342 | −18.988 | 2 | 3 | 1 | 0 | yes |
| 12 | 99.004 | 99.004 | 0 | 3 | 3 | 0 | 0 | no |
| 13 | 65.050 | 83.738 | −18.689 | 2 | 3 | 1 | 0 | yes |
| 14 | 90.247 | 107.059 | −16.813 | 2 | 3 | 1 | 0 | yes |

`tasks_done` is 3 on every run, including the duplicates. T4 has no duplicate and no violation on these utility runs.

## What the receiver saw and chose

The receiver observation below is the user prompt in `model_request.jsonl` for the receiver, not a prompt reconstructed after the run.

| Seed | Receiver task under T3 | Sender task under T3 | Receiver saw the assignment | Third agent saw the assignment | T4 receiver task |
| --- | --- | --- | --- | --- | --- |
| 11 | `ISSUE-0001::triage` | `ISSUE-0001::triage` | no | yes | `ISSUE-0001::review` |
| 12 | `ISSUE-0001::triage` | `ISSUE-0002::review` | no | yes | `ISSUE-0001::triage` |
| 13 | `ISSUE-0002::review` | `ISSUE-0002::review` | no | yes | `ISSUE-0002::test` |
| 14 | `ISSUE-0002::review` | `ISSUE-0002::review` | no | yes | `ISSUE-0002::test` |

No T3 or T4 receiver prompt in this comparison contains `action_executed`. Both policies had already deleted the event. The logged tool on T3 rep 1 of each seed is `assign_task_direct` for the sender and the receiver. Rep 2 claims the same task ids.

## Mechanism on the runs that diverged

Seeds 11, 13, and 14 are the runs where T3 scores lower. On each, both repetitions, the receiver claimed the sender's task. The sender's task is the same task that sender claimed under T4 on that seed. The sender's reward is lower by 10, which is half of the violation penalty of 20. On seed 11 the third agent claimed `ISSUE-0002::review` under both policies and the reward is unchanged at 36.611.

The joint score is `20 × tasks_done + 20 × priority_sum − total_cost − 20 × violations`. Adding the penalty term back, the remaining T3 score is higher than T4 by 1.012, 1.311, and 3.187 on seeds 11, 13, and 14. The lower joint reward is the penalty for the duplicate claim, not a worse priority and cost total underneath it.

Seed 12 does not follow that pattern. The assignment, the three agent rewards, the cost, and the joint reward match T4 on both repetitions. The receiver still did not see the assignment section, and the receiver's task was not the sender's task. Hiding the assignment did not produce a duplicate on this seed.

## Reading

Assignment visibility is the field that differs in the returned request. On three of the four seeds, hiding it from the receiver is followed by a duplicate of the sender's task and one violation. On seed 12 the same hidden field is followed by the same legal assignment T4 produced. The action event is absent under both policies, so these gaps are not an effect of deleting the event. Four seeds and two draws do not make this a utility bound, and the seed-12 tie is part of the result.
