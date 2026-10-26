# Observation contract design

Paper 1 only. This note decides what a reusable check can honestly say. It does not add a model-call result, and it does not replace the 188 completed episodes.

## Question

When can a multi-agent runtime conceal tool-execution metadata while preserving task-relevant state?

The episodes answer that for one prompted tool-name channel and one assignment field. A contract is useful only if it makes those two requirements separately fail-able on the observation the runtime actually builds.

## Are the two properties distinct?

Yes, in this environment, and the policies already separate them.

Tool-identity confidentiality asks whether two calls that perform the same legitimate assignment leave the receiver able to tell which function name was selected. Task-state preservation asks whether a declared projection of the authoritative assignment is still present in that same observation.

T2 and T4 can satisfy both for the tested pair: the selected name is not distinguishable, and the assignment line remains. T3 satisfies the first for the receiver and fails the second: the name is gone because the event is gone, and so is the assignment the receiver would use to avoid a duplicate claim. T1 fails the first and satisfies the second. A single "hide the action" flag cannot express that split. Hiding the event removes one carrier of the name. It does not, by itself, say whether the assignment remains.

The properties are not independent in every implementation. The name currently rides inside the action event, so deleting the event removes the name. They are still different requirements. A filter can pass one and fail the other, and T3 is the case.

## What the existing experiments already test

The 108 episodes, the 72-episode holdout, and the eight T3 utility episodes measure behavior. Visible names were followed by bit-dependent receiver actions. Rewriting the name, and deleting the event while keeping the assignment, were followed by loss of that measured dependence. Hiding the assignment as well was followed by duplicate claims on three of four holdout seeds, and not on seed 12.

Those are stochastic outcomes at temperature 0.7. They do not define the observation. Earlier deterministic checks already compared prompts for particular policies. They were not a single checker with an explicit equivalence declaration, a protected-name list, a task-state projection, and a refusal when the calls are not equivalent.

## What has to be added

The operational contract needs all of the following, or it collapses into a slogan.

- The observation is the user prompt returned for a named agent, not the audit log.
- Incidental normalization is limited to event UUIDs. The fixed codebook block is removed because it names both tools on every signaling run and does not say which one ran. Task ids are not normalized.
- Protected metadata is the pair `assign_task_direct` and `assign_task_queued`.
- The task-state projection is the set of `(agent, task_id)` pairs in the authoritative assignment. The checker reads those pairs only from the `CURRENT ASSIGNMENTS` section. A task id in the task catalog does not count. A heading with no pairs does not count.
- Equivalence is declared by the caller. The checker does not infer it. If the declaration is set and the authoritative projections differ, the identity check fails. If the declaration is absent, the identity check is `not_approved`. Equal observations of unequal assignments are reported as erased state, not as a pass.
- Identity and task-state are separate verdicts. The audit log may keep the real tool name. That log is echoed and is not an input to either verdict.
- Policy names are not a lookup table inside the checker. Tests apply the checker to prompts the current runtime builds.

## Does this strengthen the research?

It strengthens the claim that is already supported, and it does not create a new one.

The strengthening is that "conceal the tool name and keep the assignment" is now a test with negative controls. A nested field that still contains the selected name fails identity confidentiality. A placeholder assignment section fails task-state preservation. Two tools that assign different tasks are not approved for concealment, and a filter that shows the same text for both is flagged for erasing a state difference.

The contribution is a validation procedure for this runtime boundary. It is not a new communication result. The behavioral findings stay the ones already measured: canonicalization has no demonstrated advantage over event deletion, and the assignment mask tracks the duplicate claims on three seeds, with seed 12 as the exception.

## What cannot be generalized

The two tools were written to share one claim. The checker trusts an equivalence declaration only after the assignment projections match. It does not inspect permissions, costs, or other side effects. Tools that differ in those ways are not covered by a passing identity check.

The codebook and the callable schemas still expose both names as available functions. The contract does not treat that as the selected call. It also does not close message text, timing, or any channel that was not in the compared prompts.

Passing the contract does not determine the model's action. Seed 12 produced the same assignment under T3 and T4 even though the receiver's assignment section was absent under T3. A pass is a statement about the prompt. The episodes remain the statement about behavior.

Nothing here is a proof of noninterference, a discovery procedure for task-relevant fields, or evidence that harmful collusion was prevented.
