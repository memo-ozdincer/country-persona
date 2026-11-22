# Shared-reward disclosure learning under a two-turn budget

The clean scalar Qwen baseline verifies agreement from its opening and repeats its opening throughout the impasse. This CPU experiment checks whether a shared structured policy can learn to select useful truthful claims, and whether a training bonus for verified exclusions improves both decision classes. This is a test of the learning environment and disclosed evidence. Qwen itself is frozen.

The actor in each role chooses one package or pass in each simultaneous round. Selecting a package publicly discloses the truthful signed claim for that role's private menu. The sign is environment-enforced, so this test does not measure the actor's ability to produce truthful natural language or parse a package. The same network receives the local menu, public package order, role index, own earlier claim, visible peer claim, and round number. No case-label or other private menu enters the policy. The ledger independently verifies each terminal result from emitted claims.

Both fits use the same seed, initialized parameters, batches and 160 updates on the three-option grid with balanced feasible and infeasible draws. The basic training reward is one for a verified terminal result minus 0.01 per nonpass message. The ablation adds up to 0.75 in infeasible training worlds, proportional to the fraction of packages publicly excluded. Only the environment evaluates infeasibility. The 225 held-out four-option profiles never enter the optimizer. Both held-out evaluations use the unshaped terminal reward. The silent evaluation masks peer claims for the same fitted policy. It is a behavior ablation, rather than a separately trained silent comparator.

| Policy | Peer visibility | Agreements /175 | Verified impasses /50 | Distinct signed claims | Mean terminal reward |
|---|---|---:|---:|---:|---:|
| Initialized | Peer | 164 | 0 | 626 | 0.6889 |
| Terminal-only | Peer | 169 | 0 | 816 | 0.7135 |
| Terminal-only | Masked | 153 | 0 | 780 | 0.6453 |
| Exclusion bonus | Peer | 45 | 20 | 884 | 0.2489 |
| Exclusion bonus | Masked | 17 | 14 | 870 | 0.0978 |

The terminal-only policy certifies 16 additional agreements when peer claims are visible, with no paired losses relative to the same policy with masked messages. It also makes fewer repeated disclosures than at initialization. It reaches zero impasses in the final ten sampled training batches, despite half the episodes being infeasible and all three-option impasses being reachable with this budget. The exclusion bonus makes 20 held-out impasse certificates possible while sacrificing a net 124 agreements relative to terminal-only training. It is a failure as a general replacement. In both fits the replayed score counts certified outcomes by class and charges the same message cost.

The fixed simultaneous channel makes eight of the four-option impasses structurally unresolvable at two claims per role. That limit explains neither the terminal-only fit's zero nor the bonus fit's remaining misses on reachable profiles. A useful protocol comparison can let an agent ask an evidenced question after observing a partial message, so it can elicit a rejection where it would change the decision. The earlier counteroffer workshop used a different channel and showed that sequential evidence can help. The next question is whether a language actor can use such a question without recovering the old unsupported or repetitive behavior. [Channel capacity](capacity.json) · [Earlier counteroffer run](../../counteroffers/README.md)

Each saved policy reload reproduces its exact per-profile outcomes, public messages and paired aggregates. Initialization predictions agree and both runs changed the four actor tensors. Results are from one seed and one simulated menu construction. No country preference, diplomatic quality or Qwen weight improvement has been established. [Replay](learning-replay.json) · [Terminal updates](terminal/updates.jsonl) · [Exclusion-bonus updates](dense/updates.jsonl)
