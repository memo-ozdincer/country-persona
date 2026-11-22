# Written-vote corroboration benchmark

The native draft S/2020/852 and vote provenance are in the pinned accession. The new fixture keeps the original common paragraph and five private criteria. It transports Indonesia's national explanation and the Council President's transmission as distinct passages. The source registry verifies each passage before assembly. The joint U.S. and Russian comparison can enter only when both explanations arrive.

The first replay transfers the learned channel model to a public payoff matrix over pairs of admitted sources. It compares the intended and measured language schedules, exact no-probe and calibrated controls, and the prior-informed interactive and silent reference policies. The Qwen classifier fails on both procedural paraphrases. This failure stays in the measured replay.

The CPU team fit uses authenticated focal identities, the same declared development priors and the source-grounded score. A separate paired-action search tests coordination after the fit. Both the original and repaired policies are executed through all inventory and loss branches. These tests use exact supplied evidence and a finite simulated channel. They leave natural-language role classification and independent human review open.

```bash
"$MODEL_PY" corroboration.py
"$MODEL_PY" role_sender.py score role-evidence
"$MODEL_PY" corroboration_receiver.py
"$MODEL_PY" corroboration_receiver.py --actions role-evidence/actions.json
"$MODEL_PY" joint_fit.py
"$MODEL_PY" joint_repair.py
"$MODEL_PY" written_vote_protocol.py
```

## Natural-language archival lookup

The two stages separately test whether an assignment specifies one record and which verified record it asks for. The first stage sees only the assignment. The second stage sees authenticated card descriptions in two label orders and requires agreement. No card is transmitted on failed scope or inconsistent retrieval. The dispatcher checks local ownership before emitting the learned request. The protected two-desk protocol assembles the actual archive excerpts under every loss branch. This does not automatically generalize to unconstrained instructions or new institutional roles.

```bash
"$MODEL_PY" role_lookup.py score lookup-evidence
"$MODEL_PY" scope_gate.py score scope-evidence
"$MODEL_PY" scoped_lookup.py score scoped-lookup-evidence
"$MODEL_PY" language_dispatch.py
```

The additional ten scope controls test single-record, multi-record and vague assignments. They preserve the existing scope prompt. They expose both false admissions and false abstentions, so the measured dispatch success applies only to its 14 authored inputs.

```bash
"$MODEL_PY" scope_reserve.py score scope-reserve-evidence
```

## One record, several records and alternatives

`intent_set.py` and `semantic_intent.py` distinguish required sets, acceptable alternatives and unresolved scope. Neither free-form lookup is reliable on the full panel. `intent_operator.py` tests an independent scope check and `operator_replay.py` measures the cost of withholding uncertain dispatches. `scoped_relay.py` tests fulfillment with named source requests under the existing one-reply cap. The scorer distinguishes fulfillment, claimed completion and admitted records outside the requested scope. `target_bandwidth.py` fits a separate one-bit team whose reward matches a two-record request with one required card already protected. The named control has richer communication. All inventory and loss evaluations remain synthetic.

```bash
"$MODEL_PY" intent_set.py score intent-evidence
"$MODEL_PY" semantic_intent.py score semantic-intent-evidence
"$MODEL_PY" intent_operator.py score operator-evidence
"$MODEL_PY" scoped_relay.py
"$MODEL_PY" operator_replay.py
"$MODEL_PY" target_bandwidth.py
```

## Quoted request witnesses and resolution

`request_witness.py` uses a frozen model to propose exact requested-action spans. The guard resolves a narrow archive vocabulary and fails closed if it cannot bind the spans to an operator and card set. `witness_context.py` replays the measured outputs with explicit exclusion checks and uses manually supplied spans to separate extractor and grammar errors. Authored lexical probes expose why exact quotation alone cannot establish scope. `explicit_resolution.py` supports an explicit operator and card confirmation after a withheld dispatch. Its successful recovery is conditional on supplied correct confirmations. A larger confirmed request remains intact and can be partially served under the one-reply limit.

```bash
"$MODEL_PY" request_witness.py score witness-evidence
"$MODEL_PY" witness_replay.py
"$MODEL_PY" witness_context.py
"$MODEL_PY" explicit_resolution.py
```

## Receipt-dependent routing

The test reuses the four verified cards on the Indonesia written-vote docket. Each of the 12 cases has three explicitly confirmed required cards, including one protected local card. Two simulated desks have private two-card rosters. The chair may stop or send the current missing set to either desk. A responding desk can return one held card from that set. The two legs independently deliver with probability .90. An attempted request costs .05 and an attempted reply .20. No receipt can mean the desk had no matching card or one leg failed. The chair sees no roster or undelivered reply. For the scripted baselines, a desk sends the first eligible card in canonical order.

Compare at the same contact budget and under the same rule for optional stopping. The fixed baseline commits to a contact sequence per case and can use receipts to stop. The adaptive baseline also chooses which desk to contact after observing a receipt or its absence. Both optimize on the same mixture of four roster distributions. The completion objective uses 28 points for covering the confirmed set. The record objective awards the pre-existing exact-span final-record points, starting at 35 for the fixed public paragraph. Both objectives subtract message cost. The compiler admits only verified cards in scope, gives required material priority, and omits the optional comparison if it would take the supplement beyond 85 words. Partial coverage preserves the list of missing records. The 30 dialogue points and free-form judge are outside this transport pilot.

| Three-contact record objective | Scope complete | Record points out of 70 | Expected contacts | Net reward |
| --- | ---: | ---: | ---: | ---: |
| Optimized fixed sequence with canonical replies | 30.36% | 48.54 | 2.33 | 13.15 |
| Joint learned chair and responder | 33.39% | 48.82 | 2.48 | 13.42 |
| Learned chair with canonical replies | 30.37% | 48.51 | 2.50 | 13.11 |
| Exact adaptive chair with canonical replies | 33.47% | 48.84 | 2.45 | 13.44 |

The joint fit is one 180-step exact policy-gradient run on CPU. The chair policy observes the target, protected card and receipt history. The shared responder policy observes the pending card IDs and its own holdings. A two-card choice is learnable at the desk; a sole eligible card is sent automatically. Expected team reward is differentiated over all enumerated paths, including separately charged request and reply failures. The results include the frozen policies under .80 and .95 delivery per leg. At both shifts the fitted pair stays ahead of the fixed route and behind the exact adaptive chair planned at .90. Those shifts reuse the same docket, role vocabulary and roster mixture. The exact adaptive result is the optimum for canonical replies. A jointly optimized responder could use a different reply rule.

The free-form clarification panel uses 12 authored replies and two answer-label orders per reply with frozen Qwen. The paired gate gave eight exact selections, resolved four actionable replies out of seven, withheld two single-record requests and a self-correction, and produced zero wrong action selections on this panel. One unresolved reply gave discordant labels. No real user replies or external dispatches were used. These results are separate from the routing tests, which receive the correct typed confirmation by construction.

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" clarification_turn.py score clarification-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" adaptive_relay.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" adaptive_fit.py
```

[Exact two- and three-contact enumerations](adaptive-relay-results.json) · [Fitted policy, component swaps and link-shift checks](adaptive-fit-results.json) · [Clarification results](clarification-evidence/results.json)

## Transfer by public receipt value

Keep the written-vote policy frozen and replace its four source cards with four cards from the previously sourced Iraq UNAMI and Lebanon UNIFIL records. Neither target docket enters the fit. Both retain their own 70-point rubric. UNAMI starts with vote, existing term and reporting facts. UNIFIL starts with the vote and moves its existing operative summary to an optional card so the two tasks use the same four-card transport. UNIFIL still needs both Brazil and China for the scoped comparison. The banks render authenticated, author-verified summaries for every reachable subset of up to three cards. The request deadline, hidden rosters, synthetic losses, message fees and three-contact budget are unchanged.

Evaluate all 24 aliases from named cards to learned slots, with the 12 target-and-anchor cases at each alias. The fixed control plans a desk order using each target rubric and can stop adaptively. The adaptive control also replans who to contact after each observation. Both scripts use a canonical reply determined by the alias. The table shows the **best** fixed and adaptive results over all aliases, as well as direct frozen transfer averaged over aliases.

| Net final-record gain over the protected anchor, minus message costs | UNAMI | UNIFIL |
| --- | ---: | ---: |
| Frozen team, average of all aliases | 12.680 | 16.366 |
| Best exact fixed route with canonical replies | 13.508 | 17.562 |
| Frozen team with public payoff alignment | 13.671 | 17.693 |
| Best exact adaptive route with canonical replies | 13.885 | 18.114 |

Payoff alignment uses three public quantities. These are the score gains from each individual missing card and from receiving both. Normalize the gains by their largest magnitude. Match the resulting shape to the nearest written-vote training view, allowing the two missing-card names to swap. Equally close views receive equal weight. A common mapping is supplied to both sides before requests. The mapping receives no private rosters or realized target outcomes. Reversing the target aliases leaves the aligned metrics unchanged. This posthoc intervention changes public input to the transport protocol and leaves the learned parameters frozen. Swapping canonical replies into the aligned policy lowers net gain to 13.486 for UNAMI and 17.194 for UNIFIL under the same mapped slots. [Frozen transfer and score banks](adaptive-transfer-results.json) · [Payoff alignment and per-case matches](adaptive-align-results.json)

The original 85-word written-vote renderer has one nonmonotone transition. Adding Indonesia's national statement to the U.S. and Russia pair pushes the comparison out of the supplement, lowering final-record points from 63 to 49. In a separate 92-word counterfactual, retaining the exact comparison removes that score drop. A single 180-step refit on the changed written-vote reward reaches 14.268 expected net points on its own objective. With public alignment it reaches 13.671 on UNAMI and 17.587 on UNIFIL. Remapping the original weights against the changed payoff bank produces essentially the same transfer numbers. The corrected length tradeoff gives a cleaner local objective and supplies no measured transfer improvement. [Renderer counterfactual, fitted policy and mapping-only control](adaptive-cap-fit-results.json)

The outcomes measure evidence retrieval and authored record assembly. Tests of free-form peers, open-language judge reliability and end-to-end outputs need their own observations. The target families already appeared in earlier project work. Their exclusion here applies to the written-vote policy fit.

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" adaptive_transfer.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" adaptive_align.py
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" adaptive_cap_fit.py
```
