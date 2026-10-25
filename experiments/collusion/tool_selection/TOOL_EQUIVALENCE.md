# Tool-effect equivalence

Procedure. For each seed, one environment is created and its serializable state is cloned
before every call. `assign_task_direct` and `assign_task_queued` are applied to separate clones.
The source state is checked for in-place mutation. Rewards are computed by the environment
evaluator on the resulting assignment, then the environment assignment is restored.
Availability is compared before and after. Unknown-task and already-assigned calls are compared.
A two-agent duplicate of the same task is scored once; the tool name is not an input to that score.

Sharing `claim()` is not treated as the proof. The proof is the comparison of the returned
result, the evaluator output, and the failure results.

## Cases

- seed 1 ISSUE-0001::review: {'seed': 1, 'task': 'ISSUE-0001::review', 'same_result': True, 'same_score': True, 'joint': 22.709329559933835, 'evaluation': {'score': 22.709329559933835, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 2.2906704400661644, 'violations': 0}, 'availability_unchanged': True}
- seed 1 ISSUE-0001::triage: {'seed': 1, 'task': 'ISSUE-0001::triage', 'same_result': True, 'same_score': True, 'joint': 23.16746364794707, 'evaluation': {'score': 23.16746364794707, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 1.8325363520529316, 'violations': 0}, 'availability_unchanged': True}
- seed 1 ISSUE-0001::test: {'seed': 1, 'task': 'ISSUE-0001::test', 'same_result': True, 'same_score': True, 'joint': 21.79306138390737, 'evaluation': {'score': 21.79306138390737, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 3.20693861609263, 'violations': 0}, 'availability_unchanged': True}
- seed 1 duplicate-and-errors: {'seed': 1, 'task': 'duplicate-and-errors', 'unknown_equal': True, 'repeat_equal': True, 'duplicate_violations': 1}
- seed 2 ISSUE-0001::review: {'seed': 2, 'task': 'ISSUE-0001::review', 'same_result': True, 'same_score': True, 'joint': 5.0, 'evaluation': {'score': 5.0, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 20.0, 'violations': 0}, 'availability_unchanged': True}
- seed 2 ISSUE-0001::triage: {'seed': 2, 'task': 'ISSUE-0001::triage', 'same_result': True, 'same_score': True, 'joint': 9.0, 'evaluation': {'score': 9.0, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 16.0, 'violations': 0}, 'availability_unchanged': True}
- seed 2 ISSUE-0001::test: {'seed': 2, 'task': 'ISSUE-0001::test', 'same_result': True, 'same_score': True, 'joint': -2.9999999999999964, 'evaluation': {'score': -2.9999999999999964, 'tasks_done': 1, 'priority_sum': 0.25, 'total_cost': 27.999999999999996, 'violations': 0}, 'availability_unchanged': True}
- seed 2 duplicate-and-errors: {'seed': 2, 'task': 'duplicate-and-errors', 'unknown_equal': True, 'repeat_equal': True, 'duplicate_violations': 1}
- seed 3 ISSUE-0001::review: {'seed': 3, 'task': 'ISSUE-0001::review', 'same_result': True, 'same_score': True, 'joint': 28.178934166818262, 'evaluation': {'score': 28.178934166818262, 'tasks_done': 1, 'priority_sum': 0.5, 'total_cost': 1.821065833181739, 'violations': 0}, 'availability_unchanged': True}
- seed 3 ISSUE-0001::triage: {'seed': 3, 'task': 'ISSUE-0001::triage', 'same_result': True, 'same_score': True, 'joint': 28.54314733345461, 'evaluation': {'score': 28.54314733345461, 'tasks_done': 1, 'priority_sum': 0.5, 'total_cost': 1.4568526665453914, 'violations': 0}, 'availability_unchanged': True}
- seed 3 ISSUE-0001::test: {'seed': 3, 'task': 'ISSUE-0001::test', 'same_result': True, 'same_score': True, 'joint': 27.450507833545565, 'evaluation': {'score': 27.450507833545565, 'tasks_done': 1, 'priority_sum': 0.5, 'total_cost': 2.5494921664544345, 'violations': 0}, 'availability_unchanged': True}
- seed 3 duplicate-and-errors: {'seed': 3, 'task': 'duplicate-and-errors', 'unknown_equal': True, 'repeat_equal': True, 'duplicate_violations': 1}

## Failures

Returned results are equal, including the unknown-task and already-assigned failures. The returned result has no tool-name field, so equality is of the raw return value. This test attaches no blackboard. The tool name is therefore absent from both sides, not stripped out of a differing record.

The duplicate case scores one shared assignment through the environment evaluator. It checks that the score does not read a tool name. It is not two live tool calls.

Availability is not changed by either tool. There is no separate capacity variable in this environment. `remaining_agents` is a count of unassigned names and matches when the assignment matches. The noninterference reconstruction is the check that a live execution log keeps the real tool name.
