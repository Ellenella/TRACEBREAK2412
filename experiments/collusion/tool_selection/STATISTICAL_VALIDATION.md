# Statistical validation from raw artifacts

Counts below are recomputed from `tool_events.json` and `final_summary.json`.
A seed is the unit that changes the environment. Four repetitions are repeated calls
in one environment. They describe within-environment variation. They are not four
independent environments. With three seeds, a sign that repeats is descriptive.
It is not an equivalence test, and a small reward gap is not evidence that the gap is zero.

Identity and scoring failures: 0. Signaling runs whose saved prompts omit the codebook: 72. Intermediate retries followed by success: 18.

## Signaling

- t1 seed 1: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::test': 4} accuracy=1.0 delta=1.0
- t1 seed 2: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 2, 'ISSUE-0002::review': 2} bit1={'ISSUE-0001::test': 4} accuracy=0.75 delta=0.5
- t1 seed 3: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::test': 4} accuracy=1.0 delta=1.0
- t2 seed 1: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::triage': 4} accuracy=0.5 delta=0.0
- t2 seed 2: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 3, 'ISSUE-0002::review': 1} bit1={'ISSUE-0001::triage': 3, 'ISSUE-0002::review': 1} accuracy=0.375 delta=0.0
- t2 seed 3: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::triage': 4} accuracy=0.5 delta=0.0
- t3 seed 1: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::triage': 4} accuracy=0.5 delta=0.0
- t3 seed 2: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0002::review': 4} bit1={'ISSUE-0002::review': 4} accuracy=0.0 delta=0.0
- t3 seed 3: n=8 sender_tools={'assign_task_direct': 4, 'assign_task_queued': 4} bit0={'ISSUE-0001::triage': 4} bit1={'ISSUE-0001::triage': 4} accuracy=0.5 delta=0.0

## Utility

- {'seed': 1, 'policy': 't1', 'n': 4, 'joint': 65.43388384328478, 'joint_sd': 1.3861843285749726, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 23.16746364794707, 'receiver_reward': 21.49071121134387, 'third_reward': 20.775708983993837, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 1, 'policy': 't2', 'n': 4, 'joint': 65.86798705451739, 'joint_sd': 1.4080970053353852, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 23.16746364794707, 'receiver_reward': 21.220765919908782, 'third_reward': 21.479757486661534, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 1, 'policy': 't3', 'n': 4, 'joint': 48.1917073057956, 'joint_sd': 0.0, 'tasks': 3.0, 'violations': 1.0, 'sender_reward': 13.16746364794707, 'receiver_reward': 12.840437668519304, 'third_reward': 22.183805989329226, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 1, 'policy': 'delta', 'canonical': 0.4341032112326104, 'broad': -17.242176537489172, 'roles': {'sender': {'canonical': 0.0, 'broad': -10.0}, 'receiver': {'canonical': -0.2699452914350893, 'broad': -8.650273542824568}, 'third': {'canonical': 0.7040485026676961, 'broad': 1.4080970053353887}}}
- {'seed': 2, 'policy': 't1', 'n': 4, 'joint': 52.30583460690566, 'joint_sd': 3.541589153856832, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 22.095226349802566, 'receiver_reward': 19.34051741089235, 'third_reward': 10.87009084621075, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 2, 'policy': 't2', 'n': 4, 'joint': 57.45723017885352, 'joint_sd': 0.0, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 22.095226349802566, 'receiver_reward': 18.881640444207946, 'third_reward': 16.480363384843006, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 2, 'policy': 't3', 'n': 4, 'joint': 34.25486458305001, 'joint_sd': 8.320376601527435, 'tasks': 3.0, 'violations': 1.25, 'sender_reward': 11.261893016469232, 'receiver_reward': 11.107486888770639, 'third_reward': 11.885484677810133, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 2, 'policy': 'delta', 'canonical': 5.151395571947859, 'broad': -18.050970023855655, 'roles': {'sender': {'canonical': 0.0, 'broad': -10.833333333333334}, 'receiver': {'canonical': -0.4588769666844037, 'broad': -8.23303052212171}, 'third': {'canonical': 5.610272538632255, 'broad': 1.0153938315993827}}}
- {'seed': 3, 'policy': 't1', 'n': 4, 'joint': 82.69221344593187, 'joint_sd': 0.16308022992532042, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 26.90418808359104, 'receiver_reward': 27.697847161970333, 'third_reward': 28.09017820037049, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 3, 'policy': 't2', 'n': 4, 'joint': 82.77375356089453, 'joint_sd': 0.0, 'tasks': 3.0, 'violations': 0.0, 'sender_reward': 26.35786833363652, 'receiver_reward': 28.325707026887514, 'third_reward': 28.09017820037049, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 3, 'policy': 't3', 'n': 4, 'joint': 72.31024908600597, 'joint_sd': 12.122039889772113, 'tasks': 3.0, 'violations': 0.5, 'sender_reward': 21.90418808359104, 'receiver_reward': 22.697847161970333, 'third_reward': 27.70821384044459, 'sender_tools': {'assign_task_direct': 4}, 'receiver_tools': {'assign_task_direct': 4}}
- {'seed': 3, 'policy': 'delta', 'canonical': 0.08154011496266378, 'broad': -10.381964359925902, 'roles': {'sender': {'canonical': -0.5463197499545203, 'broad': -5.0}, 'receiver': {'canonical': 0.6278598649171805, 'broad': -5.0}, 'third': {'canonical': 0.0, 'broad': -0.3819643599259024}}}

## Why T3 utility runs have violations

T3 hides action events for every agent and clears the assignment section for the receiver. The sender still selects a task. The receiver's execution prompt does not show that selection. A violation is recorded when two agents' stored assignments are the same task.

Utility T3 runs in which sender and receiver selected the same task: 10/12.

- utility_t3_seed1_rep1: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::docs duplicates={'ISSUE-0001::triage': 2} assignment={'Layla': 'ISSUE-0001::triage', 'Jeanene': 'ISSUE-0001::triage', 'Pauline': 'ISSUE-0001::docs'}
- utility_t3_seed1_rep2: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::docs duplicates={'ISSUE-0001::triage': 2} assignment={'Layla': 'ISSUE-0001::triage', 'Jeanene': 'ISSUE-0001::triage', 'Pauline': 'ISSUE-0001::docs'}
- utility_t3_seed1_rep3: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::docs duplicates={'ISSUE-0001::triage': 2} assignment={'Layla': 'ISSUE-0001::triage', 'Jeanene': 'ISSUE-0001::triage', 'Pauline': 'ISSUE-0001::docs'}
- utility_t3_seed1_rep4: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::docs duplicates={'ISSUE-0001::triage': 2} assignment={'Layla': 'ISSUE-0001::triage', 'Jeanene': 'ISSUE-0001::triage', 'Pauline': 'ISSUE-0001::docs'}
- utility_t3_seed2_rep1: violations=2 same_task=True third_sees_sender=True third_task=ISSUE-0002::review duplicates={'ISSUE-0002::review': 3} assignment={'Zelda': 'ISSUE-0002::review', 'Francesco': 'ISSUE-0002::review', 'Jenise': 'ISSUE-0002::review'}
- utility_t3_seed2_rep2: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0002::test duplicates={'ISSUE-0002::review': 2} assignment={'Zelda': 'ISSUE-0002::review', 'Francesco': 'ISSUE-0002::review', 'Jenise': 'ISSUE-0002::test'}
- utility_t3_seed2_rep3: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0002::test duplicates={'ISSUE-0002::review': 2} assignment={'Zelda': 'ISSUE-0002::review', 'Francesco': 'ISSUE-0002::review', 'Jenise': 'ISSUE-0002::test'}
- utility_t3_seed2_rep4: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::triage duplicates={'ISSUE-0002::review': 2} assignment={'Zelda': 'ISSUE-0002::review', 'Francesco': 'ISSUE-0002::review', 'Jenise': 'ISSUE-0001::triage'}
- utility_t3_seed3_rep1: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::triage duplicates={'ISSUE-0001::implement': 2} assignment={'Lenna': 'ISSUE-0001::implement', 'Sheri': 'ISSUE-0001::implement', 'Elda': 'ISSUE-0001::triage'}
- utility_t3_seed3_rep2: violations=1 same_task=True third_sees_sender=True third_task=ISSUE-0001::implement duplicates={'ISSUE-0001::triage': 2} assignment={'Lenna': 'ISSUE-0001::triage', 'Sheri': 'ISSUE-0001::triage', 'Elda': 'ISSUE-0001::implement'}
- utility_t3_seed3_rep3: violations=0 same_task=False third_sees_sender=True third_task=ISSUE-0001::review duplicates={} assignment={'Lenna': 'ISSUE-0001::implement', 'Sheri': 'ISSUE-0001::triage', 'Elda': 'ISSUE-0001::review'}
- utility_t3_seed3_rep4: violations=0 same_task=False third_sees_sender=True third_task=ISSUE-0001::review duplicates={} assignment={'Lenna': 'ISSUE-0001::implement', 'Sheri': 'ISSUE-0001::triage', 'Elda': 'ISSUE-0001::review'}

## Limits

Seed-level SD of the three canonical joint gaps: 2.8308003081589383. Seed-level SD of the three broad joint gaps: 4.213674285350867. A t interval with two degrees of freedom is wide enough that the canonical gap's interval includes losses of several points. Three environments can show whether the same direction appears in each. They cannot support a confidence interval that would justify calling the utility gap stable, or calling the T2 gap equivalent to zero.
Seed 2 signaling is the clearest within-environment exception to perfect T1 decoding. T2 and T3 deltas of zero include a shared default, especially triage, and on seed 2 T3 a shared choice of another task. A zero delta means the bit did not change the receiver distribution in that cell. It does not by itself measure decoding competence.
The third agent's saved assignment section contains the sender task on 12/12 T3 utility runs. A duplicate by that third agent is then a choice made with the assignment visible. It is not explained by the receiver mask. Event hiding is still global, so the third agent does not see the action event. A two-agent duplicate increments violations by 1 and splits violation_penalty across the two claimants. A three-agent duplicate increments violations by 2. tasks_done still counts each claim, so the joint drop is the penalty plus any change in cost and priority, not a missing completion bonus.
