# Learning under incomplete private observations

The prior membership study showed that incomplete local menus can still contain enough evidence to certify an impasse. The exclusion-first script retains the current delegate while it has another useful known exclusion. It passes the floor after an acceptance so the peer can confirm it immediately. The earlier learned policy was trained on complete local menus and could miss these impasses. This study asks whether a shared policy can learn useful deviations from the exclusion-first script under incomplete observations.

At runtime, a delegate sees its own known acceptances and exclusions and the public signed record. An unknown sign is absent from both masks. The simulator masks one sign per role for each legal opening presentation in widths three and four. The frozen test draws new masks for width five with one missing sign per role and for width six with two missing signs per role. An opening is admitted only when its signer observes that acceptance. Each episode has one continuation slot per package. A certificate is a publicly supported agreement or complete exclusion coverage. The shared reward subtracts 0.025 per continuation. The earlier learned baseline receives the same partial inputs, filters out proposals with unknown signs, and uses the exclusion-first script on an unavailable move.

## Fitted policy

Counterfactual policy iteration tries alternate moves for each local observation while holding the subsequent policy fixed. Sixteen accepted changes raised training agreements from 736 to 764 with 31/31 evidence-available impasses preserved, and saved 159 agreement slots. Fourteen of the learned changes replace an exclusion with an unconfirmed positive proposal. After transfer, these choices recovered some agreements and lost certified impasses.

| Held-out partial scenarios | Policy | Agreements | Impasses |
|---|---|---:|---:|
| Width 5, one missing sign per role | Exclusion-first script | 4,678/5,860 | 171/540 |
| Width 5 | Earlier learned router | 4,739/5,860 | 84/540 |
| Width 5 | Partial policy | 4,861/5,860 | 127/540 |
| Width 6, two missing signs per role | Exclusion-first script | 24,226/34,434 | 160/2,430 |
| Width 6 | Earlier learned router | 24,260/34,434 | 75/2,430 |
| Width 6 | Partial policy | 24,377/34,434 | 145/2,430 |

The evidence ceilings are 4,907 agreements and 171 impasses at width five, and 24,557 agreements and 160 impasses at width six. Where the actors have no shared known acceptance, an agreement certificate cannot be produced. A genuine impasse requires at least one known exclusion for every option and an exclusion available to the first continuing speaker. Independently enumerating all legal truthful moves reproduced that ceiling on a separate 1,168-case sample at widths three and four. [Training journal](evidence/training/training.json) · [Width five](evidence/training/heldout-5.json) · [Width six](evidence/training/heldout-6.json) · [Replay](evidence/replay.json)

## Preserving the remaining proof options

A speculative acceptance uses a turn without ruling out an option. When the remaining turns are all needed to cover the unexcluded options, the strict guard blocks any learned replacement of an exclusion with a speculative acceptance. The local guard makes an exception when the role's own observations and the peer's public acceptances already make an impasse certificate impossible. The availability guard also uses a new public bitmask of which options the peer can assess, without revealing the assessments. This is a communication ablation with extra metadata and the same disclosure-slot budget. Real abstention patterns can correlate with mandate contents, unlike the synthetic missingness here. All guards pass the floor when keeping it would leave the delegate without another known exclusion.

The guard was motivated by the width-five and width-six misses. The fresh width-seven test uses two missing signs per role and 4,000 presentations per outcome class, sampled before applying any policy. Evidence permits certificates on 3,193 agreements and 279 impasses.

| Fresh width-seven policy | Verified agreements | Verified impasses | Aggregate agreement slots |
|---|---:|---:|---:|
| Exclusion-first script | 3,139 | 279 | 15,933 |
| Unguarded partial policy | 3,166 | 228 | 15,008 |
| Local guard | 3,138 | 279 | 15,672 |
| Availability guard | 3,136 | 279 | 15,048 |
| Strict guard | 3,139 | 279 | 15,933 |

The availability guard saves 885 slots across the 4,000 feasible presentations, gains one agreement and loses four for a net loss of three. The local guard loses one agreement while retaining every possible impasse. The strict guard exactly matches baseline certificates and aggregate costs. On the previously inspected width-five and width-six panels, the availability guard retains all reachable impasses while gaining 50 and 42 agreements respectively. The fresh results show why those gains cannot be treated as a general policy improvement. [Fresh results](evidence/guards/fresh-7.json) · [Exposed width five](evidence/guards/exposed-5.json) · [Exposed width six](evidence/guards/exposed-6.json)

## UN workshop transfer

The transfer uses exact saved model outputs from the sanctions and membership role-calibration runs. It replays both direct-package predictions and the field-invariant signs under the previous opening and turns rules. An evaluator rejects an incorrect sign and marks that option unavailable to its proposer. It never fills the opposite sign.

For direct package predictions, the learned partial policy and the exclusion-first script get all four membership impasses. The earlier learned router gets none. All methods lack the shared acceptance evidence needed for the sanctions agreement. Under field-invariant predictions, the earlier learned router with positive-offer handoff certifies all eight openings. Unguarded partial learning retains four sanctions agreements but loses the four membership impasses. The guards restore those impasses but fall back to three sanctions agreement certificates. The current partial policy therefore does not replace the best verified router for these source-linked tasks. [Raw transfer](evidence/tasks.json) · [Guarded transfer](evidence/tasks-guarded.json)

This update trains a CPU policy table. The case masks and counterfactual scenes are synthetic, and the source-linked transfer reuses previously observed outputs. Qwen was frozen and no new language model judgments were used as rewards.
