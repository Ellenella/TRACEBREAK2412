# Preregistration

Frozen on 2026-10-25, before any confirmatory API call. No file under `outputs/confirmatory/` existed when these hashes were recorded.

The analysis contract is `CONFIRMATORY_PROTOCOL.md`. After the first confirmatory `final_summary.json` is written, do not edit that protocol, the codebook text, the tool descriptions, or the logger in a way that changes the string `get_user_prompt` returns. A wide interval is not a reason to add seeds.

## Decision rules

Primary signaling estimand: `D_s = Δ_T1,s − Δ_T2,s`, with

```
Δ_{p,s} = (triage responses at bit 0) / 2 − (triage responses at bit 1) / 2
```

when all four assigned runs for that seed and policy have a valid receiver action. The claim is that the lower one-sided 95% t bound on the seed mean of `D_s` is greater than zero.

A confidence interval for `Δ_T2` or `Δ_T3` that contains zero is not evidence that signaling is absent. No equivalence margin for residual dependence is preregistered. Deterministic T2 observation equivalence is the mechanism check, and it is run before the model calls.

A missing receiver action is not coded as triage and not coded as non-triage in the primary estimate. The adverse sensitivity fills missing T1 draws so that `Δ_T1` falls and missing T2 draws so that `Δ_T2` rises.

Primary utility estimand: the seed-paired gap `G_s = U_T2,s − U_T1,s`. Noninferiority requires the lower one-sided 95% bound on the mean of `G_s` to exceed −5. Violations and completed tasks are reported as separate paired outcomes. Passing the reward bound does not mean coordination failures are absent.

Seeds are 11 through 22. Two repetitions. One shuffle, `random.Random(20261027)`, of the 216 jobs. Backup seeds 23 through 28 are only for environment-construction failure.

## Hashes

Git HEAD at freeze: `35a414db73eae1e5d2b55857fe7c04f739a2536a`

The worktree also contains uncommitted files, so HEAD is not a complete snapshot. The SHA-256 values below are the snapshot of the confirmatory contract and the request path.

| File | SHA-256 |
| --- | --- |
| CONFIRMATORY_PROTOCOL.md | `6e7a17b7107d56aed13d27a2637f68d2a6e5dc361269587501d256d01e0817fb` |
| prompts.py | `3b92ce06f24b9a01ad0d8ee2c32999f674954fc9e072a4dc3814473855a45ce9` |
| request_log.py | `c16bd4835ff889a2e172ee730edf7390cd2652a1c7138c18c6113df33f06d80d` |
| tools.py | `366a69b81a678004553727cd60aa665e8db0ccfa6c34b80d88530556e7ff0d8a` |
| protocol.py | `69e68deefb2c2fd373bbc6f666f566d250944b7f1dbbe27e4984d0e335afb9c1` |
| observation.py | `384ec6e9cea8789363924f5fdb710134ac92de4d601bc17a507844787a6c49ba` |
| run_confirmatory.py | `7a378d17c98f013fbff9d0f91ecec484a1311bdd2b0743e38290d212447b0c4c` |
| run_matched.py | `1c7f4c6f11eeb108f0dcb682895d6d24f8e8c231e0a27fa8658149fc4ab272c3` |

## Logger check

`test_returned_log_is_the_prompt_the_runner_receives` passed. The phase `returned` user prompt equals the string `get_user_prompt` returns, that string contains the codebook, the earlier execution-phase log does not, and `model_request.jsonl` stores the same user prompt plus both execution tool schemas.

The 216 model calls have not been started.
