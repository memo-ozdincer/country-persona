# Owner-bound claim admission and repair

A typed submission carries a message ID, a role, and explicit lists of accepted and excluded packages. A trusted scheduler supplies the sending role and a separate role-local evidence receipt. The public ledger sees only the admitted claim. Admission withholds a contradicted, ambiguous or unverified sign. It retains the other signs under selective admission and withholds the whole message under atomic admission. The verification sweep enumerates all 1,728 combinations of proposed and verified signs on a three-package menu under both rules. It also rejects five malformed requests or owner mismatches. [Ingress and audit](admit.py) · [Verification](evidence/ingress.json)

On the recorded Mali agreement path, withholding the exclusion leaves a valid positive sign that can still certify agreement. Atomic admission loses that certificate. A false acceptance and a false exclusion on the alternate France mandate are both withheld. A question without a typed declaration leaves the ledger unresolved. Giving a parser the authority to publish an envelope under the speaker's identity would still let the same mistaken acceptance through if the mandate permits that package. The owner binding and the source of the approval receipt must therefore be enforced by the calling environment. [Fixed-suffix ledger cases](evidence/ledger.json)

## Routing with disrupted continuation claims

The simulator attaches a fixed drop/flip tape to each role, turn and package. This matches interventions across policies. Opening disclosures are unchanged. Scope returns are exact or missing as before. A corrupted continuation sign is either dropped by the simulator or rejected by the role's verified receipt. Continuation slots are charged even when an intended publication fails. The policy sees the public ledger and its legal local actions. It receives no fault tape or opposing mandate.

The fit accepts eight table changes on width-four and width-five training menus. It preserves per-class training counts across clean and noisy training panels. All scored tests have 1,600 cases per class. Selective and atomic columns use the same bundle-first schedule.

| Test panel | Agreement, selective / atomic / noise-trained | Impasse, selective / atomic / noise-trained |
|---|---:|---:|
| Clean | 572 / 572 / 572 | 1,058 / 1,058 / 1,058 |
| 12% drop and 7% flip | 566 / 565 / 565 | 1,027 / 1,023 / 1,022 |
| 28% drop and 12% flip, some scope returns missing | 523 / 513 / 519 | 624 / 612 / 620 |

The noise-trained policy ties the selective script on clean outcome counts and trails it on both noisy panels. The prior learned policy gets 1,032 moderate and 631 heavy impasses, with 560 and 519 agreements. All admitted signs remain truthful to their fictional mandates throughout rollout. That assurance depends on the simulated verified receipts. The rates are interventions, with no inferred claim about real reader accuracy. [Fit and held-out comparisons](evidence/results.json)

On recorded Mali signs, inject each single drop or inversion at every continuation site, including sites a policy never reaches. Across both speaker orders, all 2,688 agreement and 1,792 impasse presentations retain their original disposition under selective bundle-first, atomic bundle-first and the prior learned policy. The noise-trained policy loses 20 impasse certificates. Only 132 faults reach a proposed sign under either fixed schedule. This evidence separates changes in route exposure from vulnerability after a message actually fails. [Fault receipts and paired outcomes](evidence/mali-faults.json)

## Resending a withheld claim

The sender can use one extra slot to resend just the verified signs that were withheld. A resend remains subject to the same gate and fault tape. The original action and handoff logic are shared across arms. The immediate-proof script resends when the missing sign would complete an agreement already supported by the peer or provide the last exclusions required for impasse. The learned residual sees the type of withheld sign, current coverage, remaining slots and handoff. It cannot read a peer's private menu or a future fault.

| Held-out panel | Resend rule | Agreement certificates | Impasse certificates | Aggregate resends |
|---|---|---:|---:|---:|
| Moderate | Never | 472 | 938 | 0 |
| Moderate | Immediate proof | 475 | 945 | 99 |
| Moderate | Always | 477 | 943 | 877 |
| Moderate | Learned | 475 | 945 | 128 |
| Heavy | Never | 447 | 560 | 0 |
| Heavy | Immediate proof | 462 | 574 | 200 |
| Heavy | Always | 470 | 567 | 2,045 |
| Heavy | Learned | 462 | 572 | 418 |

Each panel contains 1,500 cases per class. Two counterfactual updates are accepted on moderate training noise. On the heavy test, the learned residual gains and loses two agreements, gains two impasses and loses four relative to immediate proof. The immediate-proof rule adds 15 agreements and 14 impasses over never retry under heavy faults, and uses 1,845 fewer resends than always retry. In Mali, immediate-proof and learned resend retain every certificate on both role orders. Both reduce aggregate agreement slots from 4,092 to 4,062 across the single-site fault presentations and tie the original schedule on impasse slots. Most of those paired presentations contain faults the route never encounters. [Training and paired tests](evidence/retry/results.json) · [Mali transfer](evidence/retry/mali-faults.json)

Reproduce both fits with `python3 robust_bundle.py replay evidence` and `python3 retry.py replay evidence/retry`. Both runs changed routing tables on Aurora CPU. Model language parameters and the archived private evidence were frozen.

## Shared neural policy trained on team returns

Two fits train the same small shared neural actor. It chooses among legal bundle, offer, verification and ordinary disclosure actions on either delegate's turn. Its inputs contain the active role's verified signs, the public ledger, remaining slots and legal action indicators. The centralized teacher uses the simulator to evaluate paired alternatives under the team objective. One teacher maximizes return with full future simulator knowledge. The other records the return of an alternative action followed by bundle-first on both roles' turns. The second fit preserves the observation sampling and changes the continuation used to label actions. Both run 2,772 gradient updates from 16,154 decision examples, with the same fixed inference margin. A visibility perturbation preserves the view and legal action IDs across 1,190 visited states after changing peer private evidence and the fault tape. [Visibility audit](evidence/neural/visibility.json)

| Test | Router | Agreement certificates | Impasse certificates |
|---|---|---:|---:|
| Clean | Bundle-first | 620 / 1,800 | 1,201 / 1,800 |
| Clean | Either shared neural actor | 620 / 1,800 | 1,201 / 1,800 |
| With claim faults and missing scope returns | Bundle-first | 585 / 1,800 | 718 / 1,800 |
| With claim faults and missing scope returns | Either shared neural actor | 584 / 1,800 | 718 / 1,800 |

Under faults, verification-first certifies 529 agreements and 732 impasses. Offer-first certifies 591 and 702. Both models keep all Mali outcomes in either speaker order and make zero overrides on that previously studied family. Their results match the default they executed in those traces. These are learned routing weights and frozen language-model evidence. [Optimal-continuation fit](evidence/neural/results.json) · [Fixed-suffix fit](evidence/neural-suffix/results.json) · [Mali traces](evidence/neural-suffix/mali.json)

On a fixed 128-presentation subset per class, the centralized oracle certifies 91 clean impasses versus 89 for the script and 65 noisy impasses versus 56. Noisy agreements rise from 38 to 41 under that oracle. It knows both private mandates and the future fault tape. A separate aliasing audit finds seven exact feature signatures on the fault panel for which a single alternative costs a certificate in one world and gains one in another. The clean panel has one such conflict. These witnesses expose limitations of the current observation and the training target. They neither establish what a richer history can recover nor measure a new policy's gain. [Centralized bounds](evidence/neural-suffix/results.json) · [Matched observation witnesses](evidence/neural-suffix/aliasing.json)

The fits use the project's NumPy environment with one OpenBLAS thread on Aurora CPU. Verify with the `replay` subcommand for `neural_router.py` and `neural_suffix.py` against the corresponding evidence directories. The transfer and visibility scripts reproduce their JSON on standard output. No language-model parameters were updated.

## Asking for one package sign

A delegate can spend the shared question credit to request the peer's sign for a package it has already offered or for one of the last two unblocked packages whose sign it lacks. These targets are derived from the current delegate's evidence and the public ledger. A request and response consume two continuation slots. A response remains bound to the responding role and must be supported by its verification receipt. An unanswered request consumes the same budget. The [isolated witness](evidence/query/witness.json) holds the requester view fixed while the respondent approves, excludes, or abstains. It also shows a targeted exclusion completing a one-package-gap impasse.

The version that can only retrieve a peer's existing verified sign is weaker than no questions at all. With clean six- and seven-option panels, the fit changes 549 agreement and 1,049 impasse paths into certificates, versus 553 and 1,103 for no questions. The fit learns eight overrides that skip a query. Under faults it reaches 528 and 604, versus 530 and 628. Meeting the visibility constraint alone leaves many queries redundant or unanswered. [Asking for existing evidence](evidence/query/results.json)

The focused-lookup version uses the respondent's existing verification allowance when its initial package sign is missing. The simulator returns one exact sign or abstains. The original scope verification is then unavailable for that respondent. This intervention changes the evidence channel, with the two-slot question budget and the proof rules unchanged.

| Panel | Selected schedule | Agreement certificates | Impasse certificates |
|---|---|---:|---:|
| Clean | No questions | 553 / 1,700 | 1,103 / 1,700 |
| Clean | Focused lookup, fixed match then hole | 913 / 1,700 | 982 / 1,700 |
| Clean | Focused lookup, learned schedule | 913 / 1,700 | 995 / 1,700 |
| Faults | No questions | 530 / 1,700 | 628 / 1,700 |
| Faults | Focused lookup, fixed match then hole | 714 / 1,700 | 497 / 1,700 |
| Faults | Focused lookup, learned schedule | 715 / 1,700 | 503 / 1,700 |

Under clean conditions learning adds 13 impasses over its initialized schedule, and it ties the stronger fixed match-only rule at 995 impasses. Under faults it adds one agreement and a net six impasses over its initialized schedule, with nine impasse gains and three losses. The fixed rule that asks a matching question only in the first two slots still certifies 506 impasses, with fewer agreements. On the preselected wider panel, the focused lookup retains the large agreement gain and lower impasse counts relative to no questions. [Fit and width transfer](evidence/focused-query/results.json)

In both role orders on Mali, every schedule retains all ten recorded decisions. A recorded scope may verify a new negative package sign, while a new positive needs a separate source. The authored transport control can provide both. The focused learned schedule increases charged turns over no questions in both orders. The ledger audit checks that the answer belongs to the respondent and that every published sign satisfies its fictional mandate. [Mali query paths](evidence/focused-query/mali.json)

## A scope clause can answer a focused question

When an exact negative answer has a verified scope clause covering that package and another unblocked package, the respondent can publish the clause and its consequences. Both actions cost the same two continuation slots and consume the same verification allowance in this simulator. The richer response uses the available scope receipt and the focused sign from the simulated verifier. Each published consequence still goes through selective admission. The comparison isolates the information returned by the verifier. The costs of obtaining such a receipt from a language model are separate.

| New width-eight/nine panel | Fixed schedule | Agreements / 1,300 | Impasses / 1,300 |
|---|---|---:|---:|
| Reliable | No questions | 472 | 858 |
| Reliable | Ask for focused sign on a pending offer | 713 | 726 |
| Reliable | Allow the matching scope proof in the response | 713 | 886 |
| Reliable | Learned query timing with scope response | 713 | 889 |
| Faults | No questions | 453 | 494 |
| Faults | Ask for focused sign on a pending offer | 577 | 379 |
| Faults | Allow the matching scope proof in the response | 577 | 416 |
| Faults | Learned query timing with scope response | 577 | 416 |

Holding the match-only schedule fixed, the scope proof gains 160 reliable impasses without losses. Under faults it gains 38 and loses one. It uses 1,014 fewer reliable impasse continuation slots and 191 fewer with faults, with the paired agreement counts and individual agreement certificates unchanged. The learned variant has a small reliable difference and ties the match-only counts under faults. Compared with no questions, impasse counts remain lower under faults despite agreement gains. Mali preserves all certificates in both speaker orders and supplies no new model calls. [Fit and controlled responses](evidence/scope-reply/results.json) · [Paired scope effects](evidence/scope-reply/paired-responses.json) · [Mali ledger review](evidence/scope-reply/mali.json)

An initial wrapper attempt failed with recursion before it produced results. Version 2 installs the wrapper at the episode transition and retains the original focused responder. [Failure receipt](evidence/scope-reply/failed-launch-note.json)

Use the `replay` subcommands of `query_peer.py`, `focused_query.py` and `scope_reply.py` with their corresponding evidence directories. The three small fits update routing tables on Aurora CPU. The model-derived signs remain frozen.

## Choose the evidence source before looking it up

The previous scope-backed response assumes the verifier can return both a target sign and its scope proof. This fit chooses one source before seeing either result. A package lookup can return a positive sign, a negative sign, or no result. A scope lookup can publish several exclusions; it may leave the requested package unresolved. Both use two continuation slots and the same one-question budget. When a source lookup occurs, it consumes the respondent's verification allowance. An isolated test disables the package provider and verifies that the scope action still produces its own receipt. [One-source witness](evidence/exclusive-query/unit-witness.json)

| Router | Reliable agreements | Reliable impasses | Fault-panel agreements | Fault-panel impasses |
|---|---:|---:|---:|---:|
| No questions | 506 | 1,006 | 483 | 597 |
| Focused package first | 837 | 904 | 629 | 469 |
| Scope first | 506 | 993 | 456 | 465 |
| Package early, scope late | 800 | 902 | 602 | 469 |
| Learned lookup choice | 806 | 907 | 602 | 475 |

Each held-out panel contains 1,500 cases per class. The learned router gains six agreements and five impasses over its starting script with reliable returns. It preserves the script's agreement results and adds six impasses under faults. Each of those gains has zero paired losses relative to the same starting script. The stronger fixed focused rule retains more agreements, and no questions retains more impasses. [Fit and paired tests](evidence/exclusive-query/results.json)

### Source receipts from the archived model

The archive audit separately counts direct stable signs, scope implications, and contradictions. The conservative merge withholds the full conflicting scope clause and the positive signs it would negate. The hidden reference is used for scoring after this merge. On Mali, scope contributes one previously unknown negative sign, raising stable coverage from 18 to 19 of 21, with zero incorrect signs. It supplies no new positives. In outer space, one directly judged scope conflicts with a package positive. The conservative merge rejects the conflict, gains two other exclusions, and yields 12 correct signs. The temporal prompt's original wording supplies five new exclusions and does not catch the false package acceptance. Whole-set scope readings conflict with two positives and can remove evidence for a legitimate agreement. [Per-role and per-source audit](evidence/exclusive-query/source-audit.json)

The one-source replay uses the archived package evidence to answer package queries and the archived scope evidence to answer scope queries. A missing package sign stays unknown. On original-order Mali, scope-first preserves all decisions and reduces four impasses to 20 aggregate slots from 24 without questions, while increasing six agreement paths from 9 to 19 slots. The learned route preserves the agreements and loses two impasses. When Mali's order is reversed, the learned route preserves all outcomes and scope-first reaches the four impasses in 16 slots. In outer space the direct-scope evidence supports all agreement openings and zero impasses. The conflicting whole-set evidence supports neither outcome across the paired variants. Different evidence receipts therefore give a materially different test of the exact same policies. [Independent ledger and role-order replay](evidence/exclusive-query/transfer.json)

These replays use cached inference. The underlying Mali run used 42 package evaluations and 5,642 package-prompt input tokens, and six whole-set scope evaluations and 1,130 scope-prompt input tokens. The outer-space direct scope run used 18 evaluations and 3,564 prompt tokens, alongside the 42 earlier package evaluations and their 13,498 input tokens. The simulation's verification allowance charges a logical source check. It does not claim equal underlying inference costs.

Reproduce the fit with `python3 exclusive_query.py replay evidence/exclusive-query` and the other outputs with `receipt_sources.py`, `check_exclusive.py` and `exclusive_transfer.py`. The fit updates routing tables on Aurora CPU, with frozen language-model evidence.
