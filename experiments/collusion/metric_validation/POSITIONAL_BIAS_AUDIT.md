# Positional-bias audit

This is an offline reading of commit `5feedab` on `origin/track31-action-carriers` and of Tables 2 and 3 in the PDF. No episode log was available, so none of the five checks below is a verification of an executed turn order. Relabeling the printed rewards is not a causal experiment, and none was run.

## Name order at seed 1

`JiraTicketEnvironment._generate_agent_names` draws `random.Random(seed + 1337).sample(sorted(name_pool), k=num_agents)` from the `names` package. For seed 1 and four agents, this environment returns:

`Layla`, `Jeanene`, `Pauline`, `Mona`.

If `colluder_selection: first_and_last` selected the ends of that list, the coalition would be Layla and Mona, and the middle agents would be Jeanene and Pauline. That is the pairing the PDF prints. The committed runner does not implement `first_and_last`. It raises on that config value. The name order is evidence about what the config was trying to select. It is not evidence about who was labeled a colluder in a stored run, because those runs are not in the tree and this runner would not have started them.

A path built in that name order has edges Layla—Jeanene, Jeanene—Pauline, and Pauline—Mona. The endpoints do not share an edge. That topological fact is about the name list. It is not a logged blackboard inventory.

## The five checks

1. Which agent acts first. Not recoverable. `agent_order: random` is set in every Track 3.1 config. In `run.py`, that branch shuffles the agent list with the same `random.Random(seed)` object created at the start of the run. Who is first therefore depends on every earlier draw from that object. The PDF asserts that Mona acts before any filtered observation can affect her. No `agent_turn_order` field was available to test that sentence.

2. Whether the first agent is always a coalition member. The committed configs do not make this true by construction. `agent_order: random` is independent of path position. `colluders_first` exists in `_order_agent_turns` and would place every selected colluder ahead of the others, but no Track 3.1 config selects it. Even that mode would not mean "the path endpoint moves first" unless membership itself is the endpoint pair. Membership is not implemented.

3. Whether the same agent is unaffected by observation filtering. In the printed table Mona is 32.56 on every arm, and Layla, Jeanene, and Pauline all change. A constant printed reward is consistent with an agent whose observation never mattered, including a first mover. It is also consistent with that agent taking the same task for some other reason. The filter never runs in the committed `run.py`, so this repository cannot attribute her constant value to the filter. The PDF's own §6.3 already treats her invariance as a threat to validity. The table supports the invariance. It does not identify its cause.

4. Whether coalition advantage changes because the middle agents lose information. On the printed S-versus-V rows, only Jeanene and Pauline change, and both fall. Those are the middle names in the seed-1 list. That pattern matches the story that the agents who sit on shared boards are the ones the blinding hurts. It does not test the story. There is no run in which the same rewards are recomputed under a different order or a different membership.

5. Whether D is nonzero with coalition prompting off. The printed B0 value is 5.12, and B1 is 11.73. Both configs set `coalition_prompt: never` and `prompt_variants: [control]`, and the runner would also force `control` whenever the secret channel is off. The printed nonzero B0 is the PDF's evidence for a structural baseline. It is one seed, and the logs that would show the prompt text are missing. B1 is not a clean measurement of that baseline: it also applies the S filter, so its larger D mixes the label with the blinding.

## What relabeling would not show

Swapping the coalition labels on these seven reward vectors would change D by arithmetic. It would not change what the agents did, what they saw, or who moved first. That calculation was not used as a result. A positional test has to execute a new order, or a new membership, and read the order back from the log.
