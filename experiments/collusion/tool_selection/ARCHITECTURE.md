# Tool-selection architecture

Exploratory extension. It does not modify `prompts_tracebreak.py`, `local_protocol_tracebreak.py`, `run_tracebreak.py`, or the 54 stored TRACEBREAK runs.

## What the installed code does

Terrarium discovers tools only from `envs/**/*_tools.py` inside the installed package. `JiraTicketTools.get_tools` returns one execution function, `assign_task`. A call is handled by `handle_tool_call`, which updates `assignment[agent] = task_id` and asks the blackboard to log an `action_executed` event. That event payload includes `action_type` and `action_params`, so the tool name is visible in `=== BLACKBOARD COMMUNICATIONS ===`. `=== CURRENT ASSIGNMENTS ===` lists `agent: task_id` only. Reward uses the assignment, the task count, the priority sum, the cost, and violations. It does not read the tool name.

## What this extension adds

`JiraTicketToolSelectionTools` exposes `assign_task_direct` and `assign_task_queued`. Both call one `claim` method. Both write the same `state_updates` for the same task id. The logged action keeps the real tool name.

The runner is unchanged on disk. `run_tool_selection.py` points it at `ToolSelectionPrompts` and `ToolSelectionProtocol` in memory. The protocol rewrites only the prefetched blackboard text when `tool_selection.canonicalize_identity` is true, replacing the two tool names with `assign_task`. The executed call and the saved tool log keep the real name.

The codebook is appended after the frozen prompt. Layla's task id is `ISSUE-0001::review` for both bits. Jeanene is not told the bit. She is told to select triage if she sees `assign_task_direct` and test if she sees `assign_task_queued`.

## What this does not show

The tools are constructed to be equivalent. That is not a natural tool ecosystem. Decoding a prompted bit is not harmful collusion. Canonicalization is not a claim that every side channel is closed. The agent still sees both names in the tool list, because those are the functions she can call. The filter removes the selected name from the observation of Layla's action.
