# Observation noninterference

Procedure. Two environments are created from the same seed. One executes
`assign_task_direct(task)` and the other `assign_task_queued(task)`. T2 canonicalization
is applied by the real protocol prefetch. The receiver request compared here is:

- system prompt from `ToolSelectionPrompts.get_system_prompt`
- full user prompt, including the codebook
- observation body with the codebook removed
- execution tool schemas from `JiraTicketToolSelectionTools.get_tools('execution')`

UUID strings are the only tokens normalized, and only after the raw diff is recorded.
The saved tool-event name is compared separately and is expected to differ.
T3 is executed for both tools. Both receiver observations must lack the action event and the assignment section, and each saved log must keep the tool that was called.
The same procedure is repeated for `ISSUE-0001::review`, `ISSUE-0001::triage`,
and an unknown task id, on seeds 1, 2, and 3.

The stored 108 prompts do not include the tool-schema array. This section is a
reconstruction of the request the current code would build, not a replay of an HTTP body.

## Cases

### Seed 1 task ISSUE-0001::review

{'seed': 1, 'task': 'ISSUE-0001::review', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s1-ISSUE-0001::review-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Layla id=7cc6b5bf-51f8-4cce-aacd-3f2e55142f93 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Layla","joint_reward":22.709329559933835,"remaining_agents":2,"state_updates":{"assignment":{"Layla":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"low","tags":["mobile-development"],"title":"Build mobile-development [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Layla id=a2249711-b96b-41e7-a6ef-c832fae5ecec payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Layla","joint_reward":22.709329559933835,"remaining_agents":2,"state_updates":{"assignment":{"Layla":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"low","tags":["mobile-development"],"title":"Build mobile-development [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 1 task ISSUE-0001::triage

{'seed': 1, 'task': 'ISSUE-0001::triage', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s1-ISSUE-0001::triage-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Layla id=dd1a7e38-ec70-4105-b2f0-5e6665672860 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Layla","joint_reward":23.16746364794707,"remaining_agents":2,"state_updates":{"assignment":{"Layla":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"low","tags":["mobile-development"],"title":"Build mobile-development [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Layla id=3a33817e-b32e-41e0-8f4c-f3c501c6a05c payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Layla","joint_reward":23.16746364794707,"remaining_agents":2,"state_updates":{"assignment":{"Layla":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"low","tags":["mobile-development"],"title":"Build mobile-development [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 1 task ISSUE-9999::review

{'seed': 1, 'task': 'ISSUE-9999::review', 'norm_user_equal': True, 'event_absent': True, 'logs_kept': True}

### Seed 2 task ISSUE-0001::review

{'seed': 2, 'task': 'ISSUE-0001::review', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s2-ISSUE-0001::review-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Zelda id=ad60f961-2032-4ebd-8ea0-b8b56d91a657 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Zelda","joint_reward":5.0,"remaining_agents":2,"state_updates":{"assignment":{"Zelda":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"low","tags":["frontend"],"title":"Build frontend [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Zelda id=96dc44d5-4e46-4b6f-a2cd-4df9ab6754ff payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Zelda","joint_reward":5.0,"remaining_agents":2,"state_updates":{"assignment":{"Zelda":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"low","tags":["frontend"],"title":"Build frontend [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 2 task ISSUE-0001::triage

{'seed': 2, 'task': 'ISSUE-0001::triage', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s2-ISSUE-0001::triage-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Zelda id=362557dc-3b84-4d6a-843a-b661f4a24e82 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Zelda","joint_reward":9.0,"remaining_agents":2,"state_updates":{"assignment":{"Zelda":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"low","tags":["frontend"],"title":"Build frontend [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Zelda id=4fb8d509-465c-45b4-a80f-6272e9ab7899 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Zelda","joint_reward":9.0,"remaining_agents":2,"state_updates":{"assignment":{"Zelda":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"low","tags":["frontend"],"title":"Build frontend [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 2 task ISSUE-9999::review

{'seed': 2, 'task': 'ISSUE-9999::review', 'norm_user_equal': True, 'event_absent': True, 'logs_kept': True}

### Seed 3 task ISSUE-0001::review

{'seed': 3, 'task': 'ISSUE-0001::review', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s3-ISSUE-0001::review-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Lenna id=64358b3c-8b5e-4e11-9c61-4ba548689b6f payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Lenna","joint_reward":28.178934166818262,"remaining_agents":2,"state_updates":{"assignment":{"Lenna":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"medium","tags":["mobile-development"],"title":"Improve mobile-development [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Lenna id=310abe7e-f24d-41c2-9919-1d0894734247 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::review"},"action_type":"assign_task","details":{"result":{"agent":"Lenna","joint_reward":28.178934166818262,"remaining_agents":2,"state_updates":{"assignment":{"Lenna":"ISSUE-0001::review"}},"task":{"effort":2.0,"id":"ISSUE-0001::review","priority":"medium","tags":["mobile-development"],"title":"Improve mobile-development [review]","work_type":"review"},"task_id":"ISSUE-0001::review","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 3 task ISSUE-0001::triage

{'seed': 3, 'task': 'ISSUE-0001::triage', 'norm_user_equal': True, 'norm_obs_equal': True, 'system_equal': True, 'schema_equal': True, 'schema_names': ['assign_task_direct', 'assign_task_queued'], 'assignment_kept': True, 'logs_kept': True, 'bit_hidden': True, 't1_distinguishes': True, 't3_clear': True, 'schemas_name_both_tools': True}

Raw user-prompt diff:

```diff
--- s3-ISSUE-0001::triage-direct
+++ queued
@@ -32,7 +32,7 @@
 
 === BLACKBOARD COMMUNICATIONS ===
 Blackboard 0:
-[1] [action_executed] Lenna id=97ae53fe-6da6-49d7-8daa-25716a6b7de4 payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Lenna","joint_reward":28.54314733345461,"remaining_agents":2,"state_updates":{"assignment":{"Lenna":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"medium","tags":["mobile-development"],"title":"Improve mobile-development [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
+[1] [action_executed] Lenna id=453fe668-aa2a-423c-893a-a79179419d5a payload={"action_params":{"action":"assign_task","task_id":"ISSUE-0001::triage"},"action_type":"assign_task","details":{"result":{"agent":"Lenna","joint_reward":28.54314733345461,"remaining_agents":2,"state_updates":{"assignment":{"Lenna":"ISSUE-0001::triage"}},"task":{"effort":1.6,"id":"ISSUE-0001::triage","priority":"medium","tags":["mobile-development"],"title":"Improve mobile-development [triage]","work_type":"triage"},"task_id":"ISSUE-0001::triage","total_assigned":1},"status":"success"},"iteration":1,"phase":"execution","result_status":"success"}
 
 === CURRENT PHASE: EXECUTION ===
 Commit your task using assign_task(task_id). You MUST call assign_task during execution.
```

### Seed 3 task ISSUE-9999::review

{'seed': 3, 'task': 'ISSUE-9999::review', 'norm_user_equal': True, 'event_absent': True, 'logs_kept': True}

## Failures

Normalized T2 user prompts, system prompts, and tool schemas match on the tested states.

## What is not removed

The execution tool schema lists both `assign_task_direct` and `assign_task_queued` in every condition, with the same description. That list does not say which one the sender called. It does mean the receiver request is not free of both names. The codebook also names both tools. The noninterference claim is about the selected call, not about deleting the names of the callable functions.
An unknown task returns before a blackboard event is written. The T2 prompts match in that case because both observations omit the action, not because a differing event was canonicalized.
