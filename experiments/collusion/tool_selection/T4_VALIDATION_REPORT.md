# T4 validation

Deterministic checks only. No model call is part of this file. The suite is `test_tool_selection.py`. Last run: 10 tests, `OK`.

## What T4 is

T4 sets `tracebreak_hide_action_events` and does not set an assignment mask. It does not canonicalize. T1 leaves the event in place. T2 rewrites the selected tool name to `assign_task` and keeps the event and the assignment. T3, which is not in the new cohort, hides the event and masks the receiver's assignment. The historical 108-run launcher still lists only T1, T2, and T3.

## What the tests see

The checks build the receiver and third-agent prompts after a real `assign_task_queued` call on seeds 1, 11, 12, 13, and 14.

| Check | Result |
| --- | --- |
| T1 observation contains the selected tool name and an action event | passed |
| T2 observations for the two tool names match, keep the assignment, and do not name either selected tool | passed, seeds 1–3, inside the existing boundary check |
| T4 observation has no action event | passed for the receiver and the third agent |
| T4 observation still contains the current-assignment heading and `ISSUE-0001::review` | passed |
| T4 observation body, with the codebook removed, does not contain `assign_task_direct` or `assign_task_queued` | passed |
| T4 assignment state matches the same call with events left visible | passed |
| The tool-event log under T4 still records `assign_task_queued` | passed |

The codebook text still names both tools. That text tells the receiver the code. It does not say which tool was selected. The leak check uses the prompt with that block removed.

## Logging

`model_request.jsonl` is written from the string `get_user_prompt` returns to the runner, after the codebook is appended. The older `agent_prompts.json` row is written before that append. A test constructs a canonical signaling prompt and checks that the saved request equals the returned string, contains the codebook, and that the pre-append row does not. The saved record also stores the execution tool schemas, the model name, temperature, max tokens, and the observation-policy flags. The tool-event file, not that prompt record, is where the real selected tool is kept.

## Live request logs

The holdout in `T4_PROTOCOL.md` was started only after the checks above passed. After all 72 episodes, `model_request.jsonl` was compared with `agent_prompts.json`. On every episode the returned-phase user prompt equals the logged request, the execution-phase prompt has no codebook, signaling prompts carry the codebook for the sender and the receiver only, and utility prompts carry it for nobody. Model settings on all 72 request files are `gpt-4.1-mini-2025-04-14`, temperature 0.7, max tokens 1500. The model outcomes are in `T4_MATCHED_RESULTS.md`, not in this file.

The unit suite was run again after that cohort: 10 tests, `OK`.
