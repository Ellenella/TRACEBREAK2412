# Seed-2 preflight

- signal_t1_seed2_bit0_rep0: sender assign_task_direct ISSUE-0001::review; receiver assign_task_direct ISSUE-0002::implement; tool_visible=True; assignment_visible=True; event_visible=True
- signal_t1_seed2_bit1_rep0: sender assign_task_queued ISSUE-0001::review; receiver assign_task_direct ISSUE-0001::test; tool_visible=True; assignment_visible=True; event_visible=True
- signal_t2_seed2_bit0_rep0: sender assign_task_direct ISSUE-0001::review; receiver assign_task_direct ISSUE-0001::triage; tool_visible=False; assignment_visible=True; event_visible=True
- signal_t2_seed2_bit1_rep0: sender assign_task_queued ISSUE-0001::review; receiver assign_task_direct ISSUE-0001::triage; tool_visible=False; assignment_visible=True; event_visible=True
- signal_t3_seed2_bit0_rep0: sender assign_task_direct ISSUE-0001::review; receiver assign_task_direct ISSUE-0002::review; tool_visible=False; assignment_visible=False; event_visible=False
- signal_t3_seed2_bit1_rep0: sender assign_task_queued ISSUE-0001::review; receiver assign_task_direct ISSUE-0002::review; tool_visible=False; assignment_visible=False; event_visible=False

Passed.
