# Venezuela dual-draft transfer test

The Security Council considered two drafts at the same meeting on 28 February 2019. The U.S. draft S/2019/186 failed 9–3–3 because China and the Russian Federation voted against it. The Russian draft S/2019/190 failed 4–7–4 because it fell short of nine affirmative votes. The benchmark requires the judge to identify the instrument, tally, speaker capacity and reason for non-adoption. [Official meeting record, pp. 3, 6 and 9](https://digitallibrary.un.org/record/3794247/files/S_PV.8476-EN.pdf)

Both draft texts occur in the pinned UNBench draft archive. The U.S. draft matches the full roll call of row 26 in the pinned UNSC-Bench vetoed split. The Russian draft is a primary-record companion. Neither symbol and date matched the pinned UNBench Task 2 author rows. [Archive alignment and digests](references.json) · [Archive verifier](audit.py)

## Fixed protocol transfer

The fictional U.S.–Russia workshop concerns a proposed humanitarian needs assessment. It uses explicit private constraints on access, consent and reporting. One Russia profile has exactly one option in common with the U.S. profile. The other has no overlap. The simulation's signed acceptances and exclusions only establish workshop decisions. [Case and option meanings](case.json)

Each arm sees the same 30 agreement and 20 impasse presentations, spanning opening offers and both speaker orders. The baseline selected a target before opening its receipt. The positive-only change gives the responder permission to read a single role-local receipt and then select one compatible requested option. The scope variant also permits a verified exclusion if the receipt supplies no compatible requested option. The ledger admits only the evidence the responder owns and actually discloses. The request itself confers no commitment.

| Fixed action rule | Agreement | Impasse | Total slots | Fresh checks |
|---|---:|---:|---:|---:|
| Select before verification | 3/30 | 20/20 | 345 | 50 |
| Select a compatible answer from the receipt | 30/30 | 10/20 | 256 | 50 |
| Select from the receipt or disclose verified exclusions | 30/30 | 20/20 | 226 | 50 |

In the `original/ru-overlap/AC` opening the U.S. asks about B and G. The baseline returns no answer. The revised rule publishes Russia's verified acceptance of B, enabling a proof when the U.S. also accepts B. The path enumerator finds a legal agreement path for six openings before the change and all 30 after it. This tests reachability per opening with authored receipts. [Exact witnesses and ledgers](evidence/receipt-select-scope.json) · [Frozen policy comparisons and menu rotations](evidence/transfer.json)

## Wider synthetic replay

Each cell below has 850 agreement and 850 impasse presentations with the same menu draws and fault tapes across protocol arms. Cells give agreement and impasse certificates in that order.

| Delivery faults | Retry policy | Select before verification | Select compatible answer or disclose exclusions |
|---|---|---:|---:|
| Independent | Immediate | 541 / 332 | 560 / 331 |
| Independent | Delayed | 539 / 329 | 556 / 326 |
| Independent | Frozen learned | 539 / 330 | 556 / 327 |
| Persistent | Immediate | 450 / 299 | 466 / 297 |
| Persistent | Delayed | 454 / 301 | 470 / 299 |
| Persistent | Frozen learned | 454 / 299 | 470 / 297 |

The fixed change increases agreement certificates across all six comparisons and slightly reduces impasse certificates. The prior learned retry policy has no advantage over the fixed schedules on agreement and impasse counts jointly. This replay assumes exact simulated receipt contents and evaluates fixed policies with no new parameter updates. [Detailed counts and replay settings](evidence/receipt-robustness.json)

## Authority guard

Four authored pairs test whether the judge can keep the two failure mechanisms separate, distinguish the Council president's chair role from Equatorial Guinea's vote, and separate Indonesia's appeal for dialogue from an unsupported financial commitment. Each bounded claim and its foil share the same evidence packet. Each is presented in both binary answer orders. The frozen scorer reports both stable and mean-logit decisions, with exact ties recorded as uncertain. [Evidence and fixtures](facts.json) · [Frozen decoder and suite](guard_transfer.py)

The frozen Qwen3.5-4B judge makes one correct stable judgment and abstains on seven. The locked mean-logit pooling rule makes six correct judgments out of eight. It catches all four authored fabrications and rejects two of the four accurate clauses, the veto explanation and the distinction between the chair's announcement and the country's vote. The accurate and fabricated variants disagree by answer order in seven of the eight cases. Count false rejection and missed fabrication separately, alongside answer-order agreement and coverage. These are assistant-authored calibration pairs from one family. [Per-clause logits and decisions](evidence/authority/metrics.json) · [Raw predictions](evidence/authority/predictions.jsonl) · [Frozen input hashes](guard-transfer-lock.json)

The pooled margin ranks the fabrication above the accurate clause in all four matched pairs. An archive-only midpoint threshold still rejects the same two accurate Venezuela clauses. Fitting the midpoint on Venezuela instead and transferring it back would clear an unsupported attribution in the Gaza archive. Keep within-pair ranking and absolute classification as separate calibration outcomes. [Threshold transfer replay](evidence/authority/threshold-diagnostic.json)

## Learning which reply to send

A shared policy learned to choose between a scope-only response and the usual package reply when its receipt finds no compatible requested positive. It uses the responder's own receipt and the public state. The usual reply can itself include the same scope exclusions plus a signed negative about the selected package. The fit compares both legal continuations on each synthetic episode with immediate retry and everything else fixed. Its team reward uses 200 units per certificate, minus three per slot and one per verification. Both training and development require preserving certificate counts separately by outcome class and fault regime. Each split uses distinct draws, and the trained policy sees neither the outcome class nor the fault regime. [Fit and evaluation code](learn_scope.py) · [Full results](evidence/learn-scope/results.json)

| Held-out synthetic panels, 1,000 per class and regime | Agreement | Impasse | Slots | Checks |
|---|---:|---:|---:|---:|
| Independent faults, always use scope-only when eligible | 648 | 404 | 12,228 | 2,639 |
| Independent faults, learned selector | 648 | 405 | 12,226 | 2,639 |
| Persistent faults, always use scope-only when eligible | 520 | 366 | 12,829 | 2,683 |
| Persistent faults, learned selector | 520 | 366 | 12,829 | 2,687 |

The learned policy changes no certificates, slots or verification counts on the three UN-linked workshop families. In the single synthetic gain, a compound reply rules out the selected package along with the three exclusions in the scope-only reply. A resend delivers a missing signature, and the peer later supplies the remaining exclusions. The scope-only arm admits 11 distinct signed propositions including the opening, while the successful arm needs 10. The result rewards which evidence arrives, and when. [Deciding message ledger](evidence/learn-scope/heldout-trace.json)

A fixed control devised after reading that trace prefers the compound reply whenever the ordinary target exists. It matches the learned policy on certificates, slots and checks in both held-out synthetic panels and all Venezuela conditions. It chooses the compound arm more often on the synthetic panels. This comparison supports treating the fixed rule as the baseline for later runs. This fit uses textual role constraints only through authored or saved receipt projections and makes no language-model updates. [Matched fixed control](evidence/learn-scope/fixed-control.json) · [Exact fit replay](evidence/learn-scope/replay.json)

## Learning when to query

An exact routing search uses the stronger fixed reply choice and immediate retry, and examines every legal routing action through the same turn limit. The search can see future simulated faults. On independent-fault Venezuela presentations, the existing query schedule certifies 257 agreements and 176 impasses, and the search reaches 354 and 240. Under persistent faults those counts are 180 and 49 for the schedule, and 250 and 182 for the search. Taking the union of certificates across three fixed schedules covers 221 agreements and 167 impasses under persistent faults. Several failures still require decisions beyond those schedules. [Enumeration and proof paths](evidence/noisy-frontier/results.json)

The first experiment allows the actor to forgo the query at its first opportunity. Publishing only recovers 110 persistent-fault Venezuela impasses and loses all 180 agreements from the query schedule. The synthetic team-return fit accepts zero rules under separate agreement and impasse guards. The second experiment gives the actor a reversible alternative. It can spend one slot on the usual disclosure and reconsider the query on subsequent turns. Both arms use the same initial policy and receipt interface. [Irrevocable query choice](evidence/query-gate/results.json) · [One-turn deferral fit](evidence/query-deferral/results.json)

| Synthetic holdout, 840 presentations per class and regime | Agreement | Impasse | Slots | Checks |
|---|---:|---:|---:|---:|
| Independent faults, query schedule | 537 | 340 | 10,389 | 2,214 |
| Independent faults, learned deferral | 549 | 343 | 10,375 | 2,229 |
| Persistent faults, query schedule | 444 | 291 | 10,812 | 2,240 |
| Persistent faults, learned deferral | 450 | 292 | 10,804 | 2,248 |

The independent panel gains 12 agreements and three impasses with zero lost certificates. The persistent panel gains seven agreements and one impasse while losing one previous agreement. No learned deferral fires in Venezuela, Myanmar or Mali. Every eligible Venezuela decision has a cold peer receipt. Across its 18 exact decision patterns, two allow safe deferral in an in-sample table fitted to preserve each fixed-schedule certificate. The table recovers one agreement and four impasses under independent faults and eight impasses under persistent faults. The difference between that table and the trained policy distinguishes observed transfer from what the same local representation could express on those cases. [Activation and exact-observation audit](evidence/query-deferral/support.json)

A follow-up fits only to cold-receipt decisions on new synthetic training and development draws. This activates on Venezuela and does change outcomes. On the fresh 920-per-class synthetic holdout it loses one independent-fault and three persistent-fault agreements net, with one net persistent-fault impasse gain. On the exposed Venezuela replay it loses 56 agreements and gains two impasses net under independent faults. Under persistent faults it loses 18 agreements and gains 47 impasses net. The plain one-turn deferral arm reaches 190 agreements and 120 impasses under persistent faults, compared with 162 and 96 for the cold-fitted rule. Matching cache status repairs activation and leaves the agreement–impasse tradeoff. These are structured policies with authored/saved receipts and simulated delivery faults. [Cold-receipt split and paired wins and losses](evidence/query-deferral/cold-fit.json)

## Reading the role's mandate from prose

Qwen3.5-4B saw each of three fictional private mandates under two reversed orders of the same 16 answer profiles. The profile encodes allowed publication timing, coordination and consent. The locked pooled decoder sums field-level log marginals across orders, using the same rule as the Mali probe. In the comparison below, Qwen supplies both the initial available signs and the later receipt. The authored admission gate can suppress a package sign contradicted by the mandate, but contributes no replacement sign. All arms use the same clean delivery, opening schedule and fixed after-opening router. [Frozen prompts and actual logits](evidence/model-receipt/predictions.jsonl) · [Input lock](model-receipt-lock.json)

| Decoder | Fields correct out of 9 | Package signs correct out of 21 | Agreement | Impasse |
|---|---:|---:|---:|---:|
| First order | 8 | 20 | 0/30 | 20/20 |
| Reversed order | 7 | 17 | 30/30 | 0/20 |
| Retain only stable fields | 7 | 11 | 0/30 | 0/20 |
| Pool field margins | 9 | 21 | 30/30 | 20/20 |
| Authored fields | 9 | 21 | 30/30 | 20/20 |

The stable decoder leaves two timing fields unknown. Restoring only U.S. timing in a counterfactual replay restores all 20 impasses, with zero agreements. Restoring only the overlap Russia timing restores all 30 agreements when the initial signs come from the authored fixture. When Qwen must also supply the initial signs, that one-field repair yields zero agreements. Keeping authored initial signs can therefore hide a reader failure. [Single-field repairs and matched opening controls](evidence/model-receipt/attribution.json)

All six stored prompts and logit records pass the replay checks. Recomputing the scores and routing traces from the saved logits gives an exact match. The run used 3,978 input tokens and zero optimizer updates. These are three model-read mandates in one exposed fictional family, reused over 50 opening presentations. [Detailed routing outcomes](evidence/model-receipt/metrics.json) · [Replay receipt](evidence/model-receipt/replay.json)

## Learning routing actions throughout the workshop

A shared actor can now change the router at any eligible turn. Its inputs are the public ledger, the acting role's known signs, the remaining clock and public verification credits. Both delegates use the same weights. Training enumerates legal actions in synthetic states and fits action advantages from team returns. One fit assigns credit using the same fixed continuation after each alternative. The other uses the best achievable continuation on the training tape. Selected margins must preserve both certificate classes in each synthetic development condition. The model-read Venezuela mandates and both other UN-linked workshop families are excluded from this fit. [Fitter](../../routing_fit.py) · [Training evidence, learned weights and comparisons](evidence/sequential-routing/results.json)

| Model-read Venezuela | Agreement, fixed | Agreement, learned | Impasse, fixed | Impasse, learned |
|---|---:|---:|---:|---:|
| Clean | 30/30 | 30/30 | 20/20 | 20/20 |
| Independent faults | 227/300 | 246/300 | 135/200 | 134/200 |
| Persistent faults | 156/300 | 168/300 | 36/200 | 34/200 |

The learned column uses fixed-continuation training. On the synthetic holdout it gains 38 agreements and nine impasses net across the three conditions, with 300 presentations per class and condition. On ten new Venezuela fault draws per regime it recovers 31 agreements and loses zero previously certified agreements. It also recovers six impasses and loses nine. It loses agreements in both other UN-linked families, including some clean cases. The optimized-continuation actor makes no Venezuela overrides at its selected margin.

The post-hoc action mask shows that every Venezuela change is a one-turn delay of a set request. Isolating that action preserves the Venezuela gains and still loses agreements on Myanmar and Mali. An independent-fault Venezuela witness verifies agreement in five slots using seven distinct signed propositions, while the fixed router uses eight slots and eight propositions and leaves the decision unresolved. A clean Myanmar witness loses the certificate only when both delaying a set request and issuing a focused request are enabled. Preserve matched transcripts because effects can depend on the interaction between routing decisions. [Action masks and paired transcripts](evidence/sequential-routing/action-audit.json)

The actor's observation, default and options agree across 980 sampled states and matched alternatives that alter hidden peer evidence and future delivery. The fit and scores replay exactly. The CPU router is fitted by ridge regression. Qwen weights and logits are frozen. [Observation isolation](evidence/sequential-routing/locality.json) · [Exact fit replay](evidence/sequential-routing/replay.json)

## Using delivery acknowledgments to choose when to defer

Each sender can compare the signed propositions it intended to send with the public ledger after the turn. Requiring a sender to observe a missing proposition of its own before overriding the fixed router preserves clean cases and eliminates all Venezuela gains. The deciding delegate usually needs to act before its own missing payload can supply that signal. A second control makes a reliably delivered complete/incomplete status bit public after each signed ordinary message. The bit reveals no package content, and its bandwidth is charged separately from debate slots. Applying the frozen learned policy only to set-request delays after a peer failure preserves all 31 Venezuela agreement gains and all clean cases. Noisy agreement losses shrink in Myanmar and Mali. [Local acknowledgment control](evidence/ack-routing/frozen-guard.json) · [Public status control](evidence/ack-routing/shared-status.json)

A separate synthetic fit chooses whether to defer once at the first eligible set request after a peer delivery failure. The UN families supplied neither examples nor rewards during fitting. Clean transcripts match the fixed policy. The after-opening baseline and learned counts are below. [Fitter](../../ack_deferral_fit.py) · [Rule fit and paired transitions](evidence/ack-routing/fit.json)

| Family and simulated faults | Agreement, fixed → learned | Impasse, fixed → learned |
|---|---:|---:|
| Venezuela, independent | 227 → 244 | 135 → 129 |
| Venezuela, persistent | 156 → 165 | 36 → 43 |
| Myanmar, independent | 126 → 139 | 105 → 105 |
| Myanmar, persistent | 101 → 102 | 59 → 69 |
| Mali, independent | 94 → 85 | 78 → 80 |
| Mali, persistent | 70 → 61 | 77 → 79 |

Each synthetic holdout condition has 800 presentations per class. The refit loses four independent-fault agreements and gains one impasse net. Under persistent faults it gains one agreement and four impasses net. On Mali, each regime loses nine previously certified agreements and recovers two impasses. On Venezuela, the earlier frozen actor with the public peer-status guard still preserves more agreements.

A table fit retrospectively to all three families finds 30 distinct eligible actor observations. Deferring under 17 of them can recover some certificates and lose others in matched replays. Only four permit a safe recovery across the evaluated panels. A single table preserving every fixed-policy certificate can add one impasse per Mali fault condition and no agreements. The per-episode ceiling, with outcome access, can recover six and three certificates on those two panels. This bounds the decision under its current information and action interface. [Exact observation-level certificate bound](evidence/ack-routing/observation-bound.json) · [Exact fit replay](evidence/ack-routing/fit-replay.json)

## Repairing an ordinary disclosure that failed to arrive

The sender records which propositions from its last ordinary signed message reached the public ledger. A shared policy trained on synthetic team outcomes can use its next eligible ordinary slot to resend up to two still-relevant missing propositions. The option consumes that slot and may displace a new disclosure or verification. Both delegates use the same rules. The clean controls make zero resend attempts. [Resend implementation](../../ordinary_resend.py) · [Fit and paired results](evidence/ordinary-repair/resend.json)

In Myanmar's independent-fault panel, the learned resend raises agreement certificates from 126 to 131 and preserves 105 impasses. In Mali, it lowers independent-fault impasses from 78 to 71 and persistent-fault impasses from 77 to 67. The paired Mali witness sends an already checked exclusion successfully. The resend displaces a verification, and the remaining public exclusions fail to prove the impasse. In the Myanmar witness both arms send the same exclusion and both lose delivery at that slot. The resend action hands the next turn to the peer, while the ordinary action retains the floor. The peer then submits the acceptance that completes the proof. Keep retransmitted propositions, actual admissions, who speaks next, verification opportunities and final certificates visible separately. [Matched gain and loss transcripts](evidence/ordinary-repair/witnesses.json)

The same-slot control appends one missing proposition to an otherwise one-sign message, retaining the planned sign, the two-sign cap and the original packet convention of one acceptance and one exclusion. It is never eligible on the three UN families. The baseline contains 870 Venezuela ordinary decision turns with a relevant missing proposition. Of these, 344 already use both signed positions, 34 have no newly planned ordinary disclosure, and 492 have a single planned disclosure and a missing claim of the same polarity. The synthetic holdout gives the appending action ten opportunities and no certificate improvement. The fit accepts zero rules under this interface. [Same-slot fit](evidence/ordinary-repair/piggyback.json) · [Eligibility by family and condition](evidence/ordinary-repair/funnel.json) · [Exact replays](evidence/ordinary-repair/replay.json)

## Separating packet repair from turn ownership

The revised packet can include two different signs of the same polarity. It keeps the original disclosure, the two-sign cap, the scheduled next speaker, the turn cost and the verification credits. An outstanding copy of the sign already being sent uses no additional slot. On independent-fault Venezuela presentations, the fixed same-polarity rule uses the extra position 22 times, delivers 16 additional propositions and gains one impasse. Agreement certificates stay at 227. Under persistent faults 10 of 23 extra propositions arrive without a certificate change. No other linked workshop gains a certificate. The synthetic fit accepts zero rules, and the two synthetic fault panels contain only five eligible same-polarity episodes each. [Packet implementation](../../same_polarity_repair.py) · [Eligibility, admissions and results](evidence/ordinary-repair/same-polarity.json)

The speaker-only experiment keeps the actual signed packet and admitted ledger fixed through the intervention. After an ordinary send loses a proposition and the existing scheduler would keep the floor, the sender can hand the next turn to the peer. Doing so on the exact earlier Myanmar witness restores the agreement, even though the exclusion is still missing. The learned rule keeps the fixed order on that witness and recovers two different Myanmar agreements. It also recovers one Venezuela agreement. All three gains occur under independent faults, with no lost certificate across the evaluated linked workshops. Always handing off instead loses three Venezuela impasses. The synthetic holdout has a different tradeoff. The learned rule gains six agreements net across the two fault panels and loses one impasse net. [Handoff fit](evidence/ordinary-repair/handoff.json) · [Identical-prefix witnesses and per-role distinct propositions](evidence/ordinary-repair/handoff-witness.json) · [Exact replays](evidence/ordinary-repair/combined-replay.json)

## Joint credit for two interacting decisions

For each workshop, enumerate four runs on the same delivery tape. Each decision can be enabled alone, both can be enabled, or both can follow the fixed schedule. A rule can depend on what is observed at its actual decision, including a public delivery acknowledgment for query deferral. The actor never sees the crossed branches. Simple local rules are selected on synthetic training and development with separate agreement and impasse preservation checks. Compare jointly selected rules against a composition of rules selected separately, using the same candidate menu and terminal team reward. [Packet and handoff implementation](../../joint_repair_fit.py) · [Query deferral and handoff implementation](../../joint_deferral_fit.py)

The packet and speaker fit selects only a handoff rule, activated when the sender has a live public offer. On ten new fault draws per regime it recovers four Venezuela, four Myanmar and five Mali agreements, with no agreement or impasse losses. In the synthetic holdout it gains two agreements and one impasse net, with two individual agreement losses. Only 16 synthetic and 12 linked-family presentations offer both decisions on any branch. [Matched packet and handoff results](evidence/joint-repair/repair.json)

The query and speaker fit also selects handoff only. The joint and separately fitted rules coincide. In the Venezuela conditional replay, however, one independent-fault impasse requires one delegate to defer the query and the other delegate to hand off later. In a second Venezuela replay under persistent faults, both actions by the same delegate are required to certify agreement. Each fixed single-intervention arm misses each result. The fitted policy misses those combinations. Always using both interventions raises persistent-fault Venezuela certificates from 150 to 171 for agreement and 40 to 70 for impasse, but loses ten agreements net in the matching Mali regime. Log whether both decisions were available, the actor that made each decision, and the outcome with each intervention removed. [Deferral comparisons](evidence/joint-repair/deferral.json) · [Both-needed witnesses](evidence/joint-repair/synergy-witnesses.json)

The frozen policies also run on the linked outer-space family, using separately retained model predictions and authored receipts. With two package signs per role initially withheld, the deferral-and-handoff fit recovers eight persistent-fault impasses from authored receipts. Neither schedule certifies an agreement on that input. With the holdback removed, the recorded Qwen inputs certify 18/18 clean agreements and 0/12 clean impasses in every policy arm. The authored-input controls likewise certify every clean agreement and zero clean impasses in the no-holdback variant. Receipt availability changes which signs the fixed scheduler releases, so report controlled variation in the initial evidence as well as the information each audience actually receives. This fourth-family replay uses older predictions and makes zero model updates. [Outer-space case provenance](../space/README.md) · [Frozen transfer](evidence/joint-repair/space-transfer.json) · [No-holdback control](evidence/joint-repair/space-unheld.json) · [Fit replays](evidence/joint-repair/replay.json)

## Coverage of episodes that need both actions

A matched selection experiment gives priority to synthetic episodes where both interventions can occur or are necessary. Both arms use the same candidate rules, draws, and separate agreement and impasse guards. Of 10,200 training presentations, 17 expose both decisions in one branch and none need both. In 7,440 development presentations, 20 expose both and none need both. The 8,400-presentation synthetic holdout also contains none. The ordinary objective picks two active rules. On new Venezuela fault draws they recover 51 agreements and 15 impasses net, with no previously certified agreement lost. The same rules lose 11 agreements net on Myanmar while recovering 19 impasses, and lose four net agreements on persistent-fault Mali. On the one Venezuela impasse requiring both roles, the policy defers the query and keeps the original speaker order, leaving the decision unresolved. The joint-priority fit keeps the fixed policy. [Matched curriculum results and held-out support](evidence/coordination-curriculum/results.json) · [Exact replay](evidence/coordination-curriculum/replay.json)

Two synthetic challenge searches change the delivery tape before running the same four branches. The first starts only where both decisions occur and the combined branch already certifies an outcome. It finds no training starts and produces zero challenge cases. The second starts whenever both decisions occur, including unsuccessful traces, and permits changes to signed-proposition loss and flip bits. It finds 32 eligible training starts, 23 development starts and 21 test starts. The only jointly necessary case is in development. It is an agreement requiring role 0 to defer at slot 1 and role 1 to hand off at slot 7. All three comparison branches remain unresolved. A single bit change on the tape makes that matched example identifiable. Keep its selected-case status visible. No fit uses the constructed case, and it supplies no estimate of how often cooperation succeeds. [First search](evidence/coordination-curriculum/joint-challenge.json) · [Expanded search](evidence/coordination-curriculum/coordination-search.json) · [Four complete branch transcripts](evidence/coordination-curriculum/synthetic-branch-transcript.json)
