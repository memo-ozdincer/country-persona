# Learned clarification and counteroffers in a two-role workshop

Can shared-reward learning allocate two clarification opportunities better than an honest first-option protocol? This test uses the existing simulated climate and sanctions menus for training and exhaustively evaluates the four-option women, peace and security menu. It measures learning under a different menu size. The policies do not read country names or draft language.

## Protocol

Each role starts by naming its first acceptable option in the public display order. The leader can accept the responder's opening if it is in the leader's own mandate. Otherwise it asks about an option it can accept. The responder gives a truthful yes or no. After a no it may disclose a different, previously undisclosed option from its own mandate. An accepted query or mutually acceptable counteroffer verifies agreement. Deadlock requires a truthful no on every locally acceptable option. The protocol records an unresolved outcome if the two-query budget expires without either certificate. Truthful replies and valid candidate choices are enforced by the environment.

The asking policy learns which remaining candidate to query. The response policy learns whether and what to counteroffer. Neither receives the other role's private menu. Both receive the same terminal REINFORCE reward, one for a verified agreement or deadlock, zero for unresolved, minus 0.04 per question–reply pair and 0.01 per counteroffer. There are 160 updates and 128 sampled episodes per update, balanced across feasible and infeasible cases. All weight updates are to these two small CPU policies. The Qwen checkpoint and semantic judge were outside the run.

## Results

The test covers 225 nonempty private-mandate pairs, 24 display orders and both leader assignments. These 10,800 presentations are exhaustive coverage of this simulated menu, with correlated views of the same profiles.

| Policy | Agreements / 8,400 | Verified deadlocks / 2,400 | Question pairs | Counteroffers | Mean reward |
|---|---:|---:|---:|---:|---:|
| Scripted, binary replies | 8,256 | 2,208 | 7,056 | 0 | 0.942756 |
| Scripted, first available counteroffer | 8,400 | 2,208 | 6,240 | 2,016 | 0.957244 |
| Greedy untrained actor pair | 8,400 | 2,208 | 6,096 | 1,632 | 0.958133 |
| Greedy learned actor pair | 8,400 | 2,208 | 6,192 | 432 | 0.958889 |
| Learned question policy, counters removed | 8,352 | 2,208 | 6,624 | 0 | 0.953244 |

The counteroffer protocol already recovered every feasible agreement before training. Relative to initialization, learning traded 96 additional question pairs for 1,200 fewer counteroffers. The terminal counts stayed constant. The net mean reward gain was 0.000756 per presentation at the declared costs. Removing the learned policy's counteroffers lost 48 otherwise verified agreements without repairing any case. This is communication-efficiency evidence in the simulated protocol. No language-quality or national-policy inference follows.

Every one of the 192 unresolved presentations had an infeasible three-option leader mandate and a one-option responder mandate. Two negative answers left one locally acceptable option untested. Neither learned ordering nor a positive counteroffer can rule out that option under this contract. An additional question or a truthful subset-response certificate can address this failure. A broader MARL comparison should measure how the agents obtain and preserve the necessary evidence when responses are language-model actions.

Both policy components had nonzero finite gradients in all 160 updates and all eight parameter tensors changed. The saved weights replayed the five arms and the paired counteroffer ablation. Each decision trace was checked against the sets and evidence at the time of disposition. [Scores](scores.json) · [Replay and unresolved profiles](replay.json) · [Learning trace](updates.jsonl) · [Example decisions](selected_traces.json)
