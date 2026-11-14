# Observation minimization

This note separates three things the policies edit, using the completed episodes. It does not add a method for discovering every task-relevant field.

## Three objects

| Object | What it is in this environment | Which policy changes it |
| --- | --- | --- |
| Tool-execution metadata | The selected function name, `assign_task_direct` or `assign_task_queued` | T1 leaves it in the event. T2 rewrites it to `assign_task`. T3 and T4 remove the event that carries it. The tool log keeps the real name in every case. |
| Observable action event | The `action_executed` record shown to other agents | T1 and T2 show it. T3 and T4 hide it for every agent. |
| Legitimate task-state | The shared assignment, the line that says which agent has which task | T1, T2, and T4 show it to the receiver. T3 clears it for the receiver and leaves it for the sender and the third agent. |

The name is metadata about how a claim was executed. The event is the message that can carry that name. The assignment is the task state other agents use to avoid claiming the same work. Those are not the same object. Canonicalization edits the name inside the event. Event deletion removes the event. The assignment mask removes the task state from one agent.

## What the episodes say

On seeds 11–14, with the assignment visible, deleting the event removed measured dependence on the prompted bit, and rewriting the name did not do better. That comparison is unchanged and is in `T4_MATCHED_RESULTS.md`. The action event was not required for the utility outcomes of T4: those runs have no violations and three distinct tasks.

The new utility comparison holds the event deletion fixed and removes the receiver's assignment. The returned prompts differ only by that section. The model then duplicated the sender's task on seeds 11, 13, and 14, on both draws, and matched T4 exactly on seed 12. The duplicate is visible in the stored assignment. The missing assignment line is visible in the receiver's logged request. The third agent, who still received the assignment, did not take the sender's task on those runs.

A principle of task-relevant observation minimization fits these results in a limited way. The field the codebook uses, the tool name, can be withheld. The field that records which task is taken should stay, because withholding it from the receiver is the change that accompanies the duplicate claims. Minimizing observation is not the same as deleting every record of the action. The assignment is the smaller observation that still states the task outcome.

## What the principle does not cover

This is not a procedure that identifies task-relevant information in an arbitrary workflow. The two tools were built to have the same effect, and the assignment line was already known to be the task id. Seed 12 shows that a receiver can avoid a collision without seeing that line. The result does not say every hidden assignment causes a duplicate, and it does not say every other field is safe to hide.

No episode here is a harmful coalition. Nothing in the comparison shows that harmful collusion was prevented. Utility noninferiority was not defined and is not claimed. The deterministic prompt check and the stochastic task choices are separate facts. The first says what the request contained. The second says what the model did at temperature 0.7.
