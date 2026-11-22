# One local verification under a shared budget

Compare a script, learned counterfactual routing, and a no-verification baseline with the same cap of one more continuation slot than the number of packages. A delegate may spend one of those slots to check a single missing sign in its own mandate. The result is private. The public ledger changes only when the delegate subsequently signs a disclosure. In simulation the local source is exact. The script checks an unknown package already offered by the peer, or checks when no other local move is available. It can choose only the first package from the resulting shortlist. The joint learner can change both ordinary disclosures and whether it checks. It does not learn an arbitrary package selection inside that shortlist.

After 15 accepted updates on three- and four-option cases, the policy gains agreements at widths five and six but loses impasses relative to the scripted local check.

| Held-out width and policy | Agreements | Impasses | Agreement continuation slots |
|---|---:|---:|---:|
| Five, no check | 4,943/5,860 | 161/540 | 16,271 |
| Five, scripted check | 5,376/5,860 | 385/540 | 14,986 |
| Five, jointly learned | 5,491/5,860 | 360/540 | 13,997 |
| Six, no check | 24,748/34,434 | 161/2,430 | 135,621 |
| Six, scripted check | 30,480/34,434 | 688/2,430 | 117,049 |
| Six, jointly learned | 30,604/34,434 | 544/2,430 | 116,825 |

The trained updates mainly change ordinary disclosures. A proof-slot guard reserves enough remaining slots for exclusions and a possible check. It improves the fresh seven-option joint policy from 642 to 813 impasses, still below the script's 876. Agreement counts are 2,740 for the script and 2,742 with the guard. A restricted fit that can only add an earlier check and leave signing behavior scripted accepts no updates. On that fit's independently masked width-seven cohort of 4,000 cases per class, the retained script verifies 3,668 agreements and 1,193 impasses. With the same slot budget and no verification, the baseline verifies 3,267 and 265. This isolates the value of a new information source from the value of learning a scheduler. [Joint fit](evidence/fit/training.json) · [Joint comparisons](evidence/fit/heldout-6.json) · [Guard comparison](evidence/fit/preservation.json) · [Restricted fit](evidence/timing/training.json) · [Fresh masked test](evidence/timing/fresh-7.json)

## Source-linked replay

The sanctions and membership cases reuse model predictions from the package judge as starting evidence. A scoped check can return a stable sign from the recorded field-invariant run for that same role and package. The authored alternative gives the ideal answer using the same one-check limit. An unavailable check consumes its slot and contributes no sign. On these paths, both one-check policies recover two of four sanctions agreements at an aggregate cost of 20 slots. Without a check they recover none in 32 slots. All mixed arms retain the four membership impasses.

In both missed sanctions paths, the Brazil delegate uses its only check on D and excludes it. The India delegate eventually offers F with no check left for Brazil. The post-hoc confirmation mode grants up to two checks within the same eight-slot limit and checks only a peer's offered package. It prioritizes affirmative proposals to bring the next option forward. This resolves all four sanctions openings using the recorded field decisions, with six checks in 14 total slots. It verifies only three of four membership impasses when deliberately applied outside its intended confirmation scope. The recovery is a scripted protocol change on exposed paths. It does not test fresh model checking or a learned timing improvement. [Mixed replay](evidence/fit/workshop.json) · [Confirmation replay](evidence/fit/workshop-confirmation.json) · [Reproducibility checks](evidence/replay.json)

All fits update CPU routing tables. Qwen was frozen and no new Qwen calls were made in this experiment.

## Learning when to check or defer

The check-or-defer fit freezes the signed-disclosure script and the selected lookup target. When a local check is available, it can choose either to check or to take the scripted disclosure or pass. Exhaustively masking one sign per delegate at widths three and four gives 17,680 training presentations. Each accepted change must preserve every individual certificate reached by the training script. The untrained policy exactly reproduces the previous one-check script on this training grid.

The fit accepts one change. It checks earlier when there is one spare turn, one useful known exclusion, one unexcluded package the speaker cannot assess, no peer acceptance, and at least two known local acceptances. The capacity and role-specific evidence in this rule are observed by the current delegate. The training change gains 48 certificates and loses none. It leaves ordinary signed actions and the total continuation-slot budget fixed.

| Masked test | Script agreements | Learned agreements | Script impasses | Learned impasses | Impasse gains / losses |
|---|---:|---:|---:|---:|---:|
| Width five, one missing sign per role | 5,369 | 5,369 | 369 | 395 | 26 / 0 |
| Width six, two missing signs per role | 30,419 | 30,419 | 676 | 718 | 72 / 30 |
| Fresh stratified width seven, two missing signs per role | 3,202 | 3,202 | 1,068 | 1,175 | 154 / 47 |
| Same width-seven sample, checks independently return with probability 0.8 | 3,102 | 3,102 | 900 | 984 | 124 / 40 |

The fresh reliable-lookup sample has 3,500 presentations per class. Both policies use 12,946 aggregate agreement slots and 27,755 impasse slots. The gain requires 57 more impasse checks and five more agreement checks within those unchanged totals. In the missing-result stress test the matched return mask is fixed for each role and package. An unreturned check uses its slot and credit and yields no sign. The raw learned rule is an aggregate improvement on these samples, with individual impasses regressing despite the in-training protection. [Training journal](evidence/deferral/training.json) · [Fresh comparison](evidence/deferral/fresh-7.json) · [Missing-result stress](evidence/deferral/unreturned-checks.json)

On stored source-linked predictions, the rule changes no route outcomes. Both one-check policies certify two sanctions agreements and four membership impasses, with either authored verification or recorded field-invariant verification. The earlier two-check confirmation path still certifies four sanctions agreements. The gain is therefore supported under a controlled synthetic intervention, and source-linked transfer remains tied. [Stored UN transfer](evidence/deferral/workshops.json) · [Exact replay](evidence/deferral/replay.json)

## Choosing which package to check

The target-only experiment freezes check timing and ordinary disclosures. Exact counterfactual fitting has 38,160 synthetic training presentations with two missing signs per role and accepts zero policy changes. The held-out target oracle tries each legal first target with the same subsequent script. It uses the outcome in hindsight and serves as an upper bound for this fixed schedule on each presentation.

| Held-out panel | Script agreements | Perfect-target agreements | Script and perfect-target impasses |
|---|---:|---:|---:|
| Five options | 4,986 / 5,860 | 5,161 / 5,860 | 137 / 540 |
| Six options | 30,477 / 34,434 | 31,459 / 34,434 | 696 / 2,430 |
| Seven options, fresh sample | 2,742 / 3,000 | 2,814 / 3,000 | 920 / 3,000 |

The archived confirmation replay uses order-averaged local signed margins from the prior package judge to rank eligible unknown options. A rank by itself enters no signed claim. The requested check is fulfilled only if the stored field interpretation supplies an invariant sign, and the authored task validator verifies each published disclosure. Each opening has the same eight-slot cap. The rows show correct certificates, private checks and aggregate charged slots across the four openings per family.

| Confirmation policy | Sanctions certificates / checks / slots | Membership certificates / checks / slots |
|---|---:|---:|
| First peer offer, one check | 2 / 4 / 20 | 3 / 0 / 30 |
| Highest local margin, one check | 4 / 4 / 10 | 3 / 0 / 30 |
| First peer offer, up to two checks | 4 / 6 / 14 | 3 / 0 / 30 |

Only F leads to a sanctions agreement among the seven legal first targets in each opening, so the expected uniform-choice result is one seventh per opening. The ranked policy selects F all four times. These four successes use the same local ranking and verify the same package across alternative openings. The membership family never triggers a check. The ranking is a scripted replay over two exposed families with no new model calls or model parameter updates. The confirmation objective is public in both families. The existing mixed-mode impasse comparison remains a separate test.

Run `python3 verify_targeting.py` from this directory to replay the fit, held-out controls and all 24 archived policy traces. The verifier also compares the two-check control with its prior archived counts. [Run identity and input hashes](evidence/targeting/launch.json) · [Traces and forced targets](evidence/targeting/workshop-targets.json) · [Replay](evidence/targeting/replay.json)
