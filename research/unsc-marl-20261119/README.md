# UN negotiation evaluation and structured MARL pilot

The [research guide](RESEARCH_GUIDE.md) explains the simulation strategy,
benchmark, results and reproduction steps. The [experiment index](EXPERIMENTS.md)
links the archived runs and their evidence.

Use the closed [UN Deliberation Benchmark v1.7](benchmark-v1.7/README.md)
or its [standalone archive](un-deliberation-benchmark-v1.7.zip) for evaluation.
The [MARL handoff](MARL_HANDOFF.md) summarizes the current evidence.
This page records the initial structured policy experiments.

The first UN pilot exposes a large failure hidden by aggregate performance. A policy trained with a shared outcome reward learned to use proposals to find agreements. It never correctly held on an infeasible world in the exhaustive test. The [evaluation protocol](GENERAL_EVALUATION.md) keeps agreement, deadlock, historical prediction and source fidelity separate.

The environment has two actors, private simulated mandates, simultaneous proposals and simultaneous final choices. An independent set-based oracle checked the reward over 176,384 possible world-and-action combinations for three- and four-option menus. The public context comes from actual UN meetings. The option lists and mandates are workshop constructs, with no historical-vote or private national-utility labels. [Climate meeting](https://docs.un.org/en/S/PV.8923) · [Sanctions record](https://digitallibrary.un.org/record/3997276) · [Women, peace and security record](https://digitallibrary.un.org/record/3801516)

## Structured policy result

A small shared policy ran 160 on-policy REINFORCE updates with entropy regularization, through both actors and both decisions. No text model weights were involved. The training sample contains 20,480 episodes from three-option climate and sanctions menus. The four-option women, peace and security menu and its private profiles were excluded. Since the structured policy sees only numeric features, its held-family result measures transfer to a larger menu. The policy receives no topic text. This is one seed. [Frozen sources and scenario cards](families.json) · [Update trace](evidence/updates.jsonl) · [Random versus trained policy](evidence/scores.json)

| Women, peace and security condition | Strict agreement when feasible | Correct mutual hold when infeasible | Class-balanced success |
|---|---:|---:|---:|
| Learned policy with true peer proposals | 3,720 / 4,200 | 0 / 1,200 | 44.3% |
| Learned policy with peer proposals removed | 2,040 / 4,200 | 0 / 1,200 | 24.3% |
| Learned policy with proposals from a different private profile | 2,628 / 4,200 | 0 / 1,200 | 31.3% |
| Scripted peer priority, same message width | 2,880 / 4,200 | 0 / 1,200 | 34.3% |
| Always hold | 0 / 4,200 | 1,200 / 1,200 | 50.0% |
| Full support exchange, larger channel | 4,200 / 4,200 | 1,200 / 1,200 | 100.0% |

The four-option audit covers 225 distinct nonempty mandate pairs, each shown in all 24 orders. The learned peer condition's strict pass changed with order for 60 of the 225 profiles. Targets and permutations are correlated, so the 5,400 rows are coverage counts. Relative to silent evaluation, the true proposals yielded 1,680 strict corrections and zero regressions for this particular trained policy. Agreement recall benefits from peer information, while deadlock capability remains absent. The learning signal therefore failed a basic robustness check despite showing an interaction effect. [Exhaustive comparison](evidence/exhaustive.json)

The initial exhaustive stress run shuffled adjacent rows, often exchanging different renderings of the same private profile. Its output remains available. The corrected run requires every donor to come from a different profile and verifies exact message routing. No refit was needed. [Original shuffle result](evidence/exhaustive-adjacent-shuffle-initial.json)

## The message channel limits what the policy can know

With four options, the other delegate has 15 possible nonempty mandates but only five possible first messages, including hold. Some different mandates must produce the same message under any deterministic protocol. Consider two such mandates and an observing delegate whose singleton mandate lies in their symmetric difference. The observer sees the same message and has the same information in two worlds that require different final choices. Perfect agreement and deadlock recognition are therefore impossible across the full test with this single simultaneous message turn. The full-exchange comparator illustrates that the reward and state allow both outcomes once enough information is exchanged.

That diagnosis favors an evaluation of a clarifying round or more informative proposals before changing the reward or running another fit. For a language model, the source-ownership and authority gates still need separate response review, including the case where amendment support gets misread as support for the adopted text.

## Frozen Qwen baseline

Qwen3.5-4B evaluated eight four-option WPS mandate profiles, each in two orders, on CPU with zero optimizer updates. It selected the highest-probability legal action token. All 128 action records, actual prompts, routed messages and scores replay.

| Condition | Strict agreements | Correct deadlocks | Episodes with an unsupported ballot |
|---|---:|---:|---:|
| True peer proposals | 6/12 | 0/4 | 5/16 |
| No peer proposal | 4/12 | 0/4 | 0/16 |
| Proposals from a different profile | 2/12 | 0/4 | 5/16 |

Relative to solo, the real peer condition repaired two feasible cases but introduced five episodes in which at least one agent selected outside its own mandate. Those endpoints describe different errors. No arm correctly resolved a deadlock. [Frozen Qwen replay](evidence/qwen/replay.json) · [Actual action records](evidence/qwen/actions.jsonl)

The [judge design](judge/README.md) extends the evaluation to both named benchmarks and evidence-linked language judgments.
