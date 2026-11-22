# Validity audit of the ranked workshop decisions · 20 November 2026

**Verdict.** Keep the ranked workshops as a diagnostic for calculating a warranted action from distributed information. They have a clear answer under partial evidence and treat legitimate ties correctly. Their strongest result currently identifies an improvement in the chair's decision procedure. It supplies little evidence about diplomatic judgment, elicitation, drafting or the added value of interaction.

## Replay and attribution

I reconstructed the possible worlds directly from the archived user prompts, applied the declared rule independently and checked the resulting acceptable set on every scored view. I matched the fitted system's recorded top-choice decisions against those sets. I also applied the identical completion-by-completion unanimity procedure to frozen Qwen's archived full-view scores. This holds the decomposition fixed and isolates the decision difference between the frozen and fitted chairs on these inputs. The fitted chair includes hand-parsed grade features as well as a learned adjustment. This comparison does not isolate weight updates from structured inputs.

| System | Both cards, 18 | Original incomplete, 14 | Narrowed one-card, 8 |
|---|---:|---:|---:|
| Frozen Qwen, direct answer | 10 | 0 | 0 |
| Frozen Qwen, same completion procedure | 10 | 12 | 3 |
| Fitted chair, same completion procedure | 18 | 14 | 7 |
| Always answer unresolved | 0 | 14 | 4 |
| Drop the priority for the worse-off delegate and maximize combined grades among feasible options | 18 | 14 | 8 |
| Apply the stipulated rule exactly | 18 | 14 | 8 |

The sum-only shortcut reproduces **the entire acceptable set on every view**. Rotating answer letters or auditing individual choices on these same worlds cannot expose it. This says what the benchmark can distinguish. It gives no reason to infer that the fitted system actually uses this shortcut. Likewise, 14/14 abstentions on the original incomplete panel add no evidence over an always-unresolved baseline. The eight narrowed controls address that issue. They reuse the same 18 complete worlds and each family has the same four narrowed condition labels. Those views measure logical consistency on two exposed decision problems. Counting them as fresh independent events would overstate precision. The headline's 0/8 direct baseline and 7/8 comparison also change the amount of computation and whether the chair sees intact public completions. [Independent replay](replay.json) · [Original comparison and fit design](../README.md#distinguish-missing-evidence-from-an-unresolved-decision)

## Which claims survive?

| Claim | Strongest evidence in the shared tree | Audit judgment |
|---|---|---|
| Better action choice after combining the learned chair and completion procedure | Same-procedure frozen baseline is 10/18, 12/14 and 3/8. Fit optimization is explicitly restricted to synthetic-0 and synthetic-1. | Real descriptive improvement across these panels. Report by family and decision type. A sealed transfer estimate would require untouched event families and frozen model selection. |
| Learned communication caused the 18/18 | The project's own fixed-transport + learned-chair comparison preserves the clean score. Learned transport + frozen chair retains the baseline. | The delivery intervention establishes that private information matters. On the tested route a script delivers it equally well. [Component swaps](../README.md#train-communication-and-ranked-decisions-on-a-shared-return) |
| Agents recover actual preferences or source-faithful national positions | The chair prompt gives package letters and explicit grades. A separate clause-based mandate experiment has six correct disclosures out of twelve in each of two menu orders. These are fictional mandates. | Report disclosure fidelity separately from arithmetic and from dated country–institution behavior. Order rotations are repeated measurements of the same cards. [Actual disclosures](../evidence/relay-ranked-mandates/report.json) |
| A higher action score yields a better diplomatic final record | In a different Mali/Myanmar writer panel, the learned-relay memos scored 49/70 in both cases, with an explicit checked status already supplied. Earlier judge tests rejected sound unresolved records. | Those panels demonstrate a downstream failure mode. There is no paired memo-quality estimate for the ranked 18/14/8 result. Independent ratings on a single frozen end-to-end comparison would address it. [Memos and judge errors](../README.md#test-the-final-prose-after-a-checked-decision) |
| More agents, turns or ideas help | The ranked probe fixes seats, route, intervention types and menus. Private card delivery exhausts the relevant information. | Valid for studying information access. Evidence for deliberation requires observing alternatives introduced, challenges and revisions in generated dialogue and their effects against a resource-matched solo or independent-drafts team. |

## Two changes that make the benchmark more discriminating

**1. Screen the gold key against plausible wrong rules before fitting.** Seven authored contrasts now have exactly checked keys and 22 package permutations. With options scored (1,3) and (2,2), sum-only accepts both, while protection of the worse-off delegate requires the latter. With (1,2) and (1,3), minimum-only accepts both and the stipulated tie-break selects the latter. Each shortcut fails one single-choice presentation and disagrees with the full gold set on two. Report each contrast and all-permutations success. An aggregate 21/22 would hide the specific failure the test was designed to detect. These were authored and checked before the chair evaluation below.

The missing-evidence key also needs a precise witness instruction. With three possible winner sets {A,B}, {B,C}, {A,C}, **every pair shares an answer but no answer is justified across all three**. Ask for a compatible collection of completions with an empty intersection, or one counterexample per candidate. Two worlds having different winner sets alone is insufficient. The same packet contains a two-world positive case with B common to both. These contrasts carry over to constraints, legal conditions and coalition requirements without depending on package letters.

### Measured chair results on the diagnostic contrasts

Use 25 fresh, deduplicated Qwen3.5-4B prompt observations with neutral case labels and the existing frozen fit. Apply the same completion unanimity rule to both chairs. Report every permutation and count a contrast as fully passed only when all permutations are correct.

| Contrast | Presentations | Frozen direct | Frozen completion | Fitted direct | Fitted completion |
|---|---:|---:|---:|---:|---:|
| Priority for the lower grade | 2 | 1 | 1 | 2 | 2 |
| Sum tie-break | 2 | 1 | 1 | 2 | 2 |
| Exact tie | 2 | 2 | 2 | 2 | 2 |
| Zero excludes | 2 | 1 | 1 | 2 | 2 |
| Impasse | 2 | 2 | 2 | 2 | 2 |
| Tied completions with a common choice | 6 | 1 | 2 | 0 | 2 |
| Three completions with no common choice | 6 | 0 | 0 | 6 | 6 |
| Total | 22 | 8 | 9 | 16 | 18 |

The fitted chair passes all permutations on six of seven contrasts. In the four missed common-choice presentations, the fitted head picks a different tied optimum in each complete view, so the unanimity rule returns unresolved even though one package belongs to both optimum sets. The priority and tie-break results provide direct discrimination on the cases that the original 40 views lacked. They remain action-choice results on exposed diagnostics. [Prompts and logits](../evidence/relay-validity-contrasts/actions.jsonl) · [Per-permutation outcomes](../evidence/relay-validity-contrasts/report.json)

A replay expands each model's chosen package to the feasible packages with exactly the same minimum and sum in that completion. It then intersects the expanded classes. This uses the model's original choice and public grades and does not correct a wrong ranking. It recovers all four fitted failures and reproduces the full gold set on all 22 presentations. The same operation leaves the frozen result at 9/22. This repair was designed after inspecting the original failures, with no new inference or optimizer steps. [Tie-aware readout and witnesses](../evidence/relay-validity-contrasts/tie-readout.json)

**2. Give the broad claim its own primary endpoint.** For an unseen episode, freeze a realistic deliverable before any trial, such as a chair's record after separate amendment and draft votes. Give each role a dated source excerpt and a material fact another seat lacks. Retain exact pre-discussion proposals, deliveries and the final record. Use the same case in a pooled solo, independent drafts plus chair, and interactive team with equal total generation and synthesis budgets. A private card outage and a matched irrelevant-message control distinguish helpful information from mere extra text. Hold all translations, amendments and rewrites of an instrument in one event family.

For a development example, the April outer-space record supports a narrow area of common ground while Japan and China differed on the amendment. Freeze a paired instruction asking the same writer for (a) the recorded outcome and (b) a hypothetical next step. Keep the simulated preference cards and package choice identical. Require the first record to preserve the two stages and actual dispositions. Require the second to keep any next step conditional, retain the objection, and avoid claiming a new Council mandate. A scorer using only the cards must return the same answer in both conditions. The endpoint changes when authority, scope or source changes. The case's ten existing final criteria and guard provide an auditable starting key. [Source excerpts and final criteria](../../crossbench/space/historical-task.json)

Publish three results side by side: warranted action accuracy, supported final-record quality out of 70 with critical errors counted, and the paired difference in final quality between interactive and matched controls. Use process coding to explain that difference. Separate supported new propositions, warranted counterarguments and uptake of actually delivered material. Publish private-role fidelity and minority omissions individually. Turn count is descriptive. Have blinded independent raters grade the same archived outputs, including authority reversals and sound impasses, before ranking systems by the semantic rubric. Report raw per-criterion disagreement and abstentions. Until then retain the raw rubric components and label quality scores as provisional.

## Source-record pilot

The pilot packet freezes two event families outside the ranked workshop trials. In January 2009 the United States abstained on the adopted Gaza ceasefire resolution and explained that it wanted the results of Egyptian mediation. In December 2017 it opposed the Jerusalem draft, described its objection in terms of authority over embassy location, and the draft failed. This pairing tests disposition, minority reasoning and Council authority on closely related regional sources. It provides a procedural calibration, with broader transfer still unmeasured. [Frozen packet](source-record-pilot.json) · [2009 roll call and proceedings](https://digitallibrary.un.org/record/645652) · [2017 proceedings](https://digitallibrary.un.org/record/1327435)

The runner's software check verifies five generation slots and an 896-output-token ceiling per arm, shared openings across the team conditions, peer visibility only during interactive revision, and the same source menu at synthesis. The solo analyst receives pooled sources throughout. Both teams' chairs receive the complete source packet and two revised contributions, so any final difference reflects how they used the interaction. The current check uses stand-in strings and has zero model calls. [Episode construction](source_record_episode.py) · [Visibility and budget check](source-record-dry.json)

### Measured source-record pilot

Frozen Qwen3.5-4B made 26 distinct calls, including six final records. All six final drafts fit the 160-word limit. Count the shared team openings in each arm's resource use. Actual output totals range from 803 to 881 tokens per arm and case. Actual inputs differ because the solo analyst sees both portfolios and the interactive reviewers see a peer draft. The recorded budgets show four cap hits in every team arm. No per-stage timing was recorded. [Raw transcript](../evidence/source-record-pilot/transcript.jsonl) · [Token budgets and scores](../evidence/source-record-pilot/scores.json)

| Event family | Pooled solo out of 70 | Independent drafts out of 70 | Interactive out of 70 | Interactive minus independent |
|---|---:|---:|---:|---:|
| Gaza ceasefire, 2009 | 42, guard failed | 49, guard clear | 42, guard failed | −7 |
| Jerusalem draft, 2017 | 49, guard failed | 56, guard uncertain | 56, guard failed | 0 |

All six records retain the minority's reason. In Gaza, the solo and interactive memos change the adopted text's calls into mandates. In Jerusalem, the interactive memo omits the 14–1 tally and cites an agent's generated revision as if it identified the draft considered by the Council. The independent draft's phrase about provisions altering the city's status remains ambiguous. The solo record attributes a hypothetical working group to a delegate statement that did not advocate one. [Final records and exact citations](../evidence/source-record-pilot/final-records.json) · [Arm-free annotation deck](../evidence/source-record-pilot/review-deck.json)

The four process anchors show no traceable peer-specific gain in the final record. The interactive Gaza revision keeps the U.S. rationale that its own opening already stated. That rationale is absent from the length-capped independent revision but present in every final record, whose writer could see the original source block. The UK complement qualification survives both Gaza revisions and appears explicitly only in the independent final. These traces distinguish retention of an existing idea from an improvement attributable to peer exchange. The scores and process labels are same-assistant annotations, with independent review pending. Both families concern the same regional agenda and supply a paired procedural pilot. [Exact reviewed spans](../evidence/source-record-pilot/annotations.json) · [Process witnesses](../evidence/source-record-pilot/process.json)

### Short, source-cited revisions

Reuse the four saved team openings and the same source blocks. Give both team arms a 45-word revision target and ask them to cite local sources only. The chair sees the original source menu and unnumbered revisions, with an explicit instruction to cite only the dated evidence and retain the force of the original wording. Only the interactive reviewers receive the other role's opening. This changes the revision and chair prompts together, so the comparison with the original run does not isolate which instruction helped. Both arms still have the 896-token output ceiling, with the archived openings counted. [Matched implementation](source_record_compact.py) · [Prompts, revisions and chair outputs](../evidence/source-record-compact/transcript.jsonl)

| Event family | Original independent | Compact independent | Original interactive | Compact interactive |
|---|---:|---:|---:|---:|
| Gaza ceasefire, 2009 | 49, clear | 49, clear | 42, failed | 49, clear |
| Jerusalem draft, 2017 | 56, uncertain | 42, failed | 56, failed | 56, failed |

The compact protocol produces eight completed revisions, compared with eight truncations in the original team runs. Seven fit the requested revision word limit. The other stops at 46 words. Total output per arm and episode falls from 803–881 to 629–665 tokens. Both Gaza records preserve the call and avoid presenting it as an implementation mandate. The interactive record retains aid access and omits the UK's complement qualification. The independent record preserves the qualification and omits aid access.

In Jerusalem the compact independent record treats the draft as a proposal to change Jerusalem's status. The compact interactive record initially describes the draft and positions correctly, then says the UK opposed draft provisions when its objection concerned the US decision. That final also reaches the token cap at 182 words, above the 160-word limit. Neither record cites a generated draft ID. The raw score difference in Jerusalem accompanies two critical factual failures. [Scores, budgets and attribution checks](../evidence/source-record-compact/compare.json) · [Exact spans](../evidence/source-record-compact/annotations.json) · [Replay](../evidence/source-record-compact/replay.json)

### Swap one Jerusalem revision at a time

Keep the compact chair prompt, source menu, output cap and one revision fixed. Replace only the other independent revision with the corresponding peer revision, once per seat. The two fresh chair calls complete the four combinations of the archived independent and interactive revisions. This intervention measures the consequence of swapping a whole revision in this one case. It does not identify any individual claim within the revision as the cause. [Swap construction](source_record_crossed.py) · [Actual prompts and outputs](../evidence/source-record-crossed/transcript.jsonl)

| Revisions at the chair | Raw points out of 70 | Factual guard | Words |
|---|---:|---|---:|
| Both independent | 42 | Failed | 134 |
| US peer revision only | 42 | Failed | 181 |
| UK peer revision only | 42 | Failed | 184 |
| Both peer revisions | 56 | Failed | 182 |

The 14-point increase appears only when both peer revisions reach the chair. None of the four cells clears the factual guard and word cap together. A raw-points reward would favor the two-peer combination on this case. A reward requiring both release conditions returns zero for every cell. Preserve the underlying criterion and failure labels so the benchmark can distinguish omissions from factual reversals before fitting a policy. Scores remain same-assistant annotations on an exposed event. [Scored combinations and conditional effects](../evidence/source-record-crossed/compare.json) · [Exact annotations](../evidence/source-record-crossed/annotations.json) · [Replay](../evidence/source-record-crossed/replay.json)

### Check a reward judge against supported omissions and factual reversals

Freeze ten source-claim pairs anchored to the Gaza and Jerusalem dockets. Keep supported omissions distinct from unsupported assertions. Include two pairs where both claims are supported and two where neither is supported. In the pairwise arm, frozen Qwen3.5-4B sees both claims and can accept either, both or neither. In the single-claim arm, it checks each separately. Reverse the claim order for the pairwise calls and the answer-letter meanings for the individual calls. This gives 60 model observations and 14,819 input tokens.

| Protocol | Stable correct pairs | Stable wrong pairs | Order disagreements | False assertions accepted across ordered calls |
|---|---:|---:|---:|---:|
| Pairwise with both/neither available | 9/10 | 0 | 1 | 2 |
| Separate claim judgments | 8/10 | 1 | 1 | 3 |

Neither procedure provides a reliable unconditional reward on this exposed panel. The one pairwise disagreement concerns the actual Jerusalem failure. It asks whether the United Kingdom opposed provisions of the draft or the United States decision on recognition and embassy relocation. Separate judgments accept both accounts in both orders. The pairwise protocol avoids a stable wrong answer but defers the case. Keep uncertainty visible and score missing detail separately from introduced error. [Frozen contrasts](guard-contrast.json) · [Ordered calls and decoded answers](../evidence/source-guard-contrast/report.json)

Average the aligned, legal-answer probabilities across the two orders as a fixed diagnostic. Both protocols then score 9/10 and choose to accept both Jerusalem claims. In the separate mode the false claim scores 0.872 and the true claim 0.816. On that pair, thresholding the reported support cannot accept the supported claim alone. These are probabilities conditional on the permitted answer letters. [Order-aligned scores](../evidence/source-guard-contrast/pooled.json)

### Transfer the source-record protocol to Sudan

Freeze a new regional family from the record of the 9786th meeting. The vote on S/2024/826 separates the Russian negative vote from China's affirmative vote, while their explanations share an interest in involving Sudanese authorities. The record must preserve both sides of that contrast along with the veto, the draft's proposed measures and the limits of Council authority. Freeze the ten scoring units before inference. [Sudan source packet](source-record-sudan-reserve.json) · [Official draft](https://digitallibrary.un.org/record/4066685) · [Verbatim meeting record](https://digitallibrary.un.org/record/4066876)

Run frozen Qwen3.5-4B with fresh Sudan openings and the compact revision/synthesis prompts across all three arms. All six revisions finish before their caps. All three final records are under 160 words, although the interactive chair reaches its token cap. Output use is 658 tokens for pooled solo, 691 for independent drafts and 690 for the interactive team. Shared output ceilings remain 896 tokens. All chairs can read the full source packet. [Unedited transcript](../evidence/source-record-sudan/transcript.jsonl) · [Exact replay](../evidence/source-record-sudan/replay.json)

| Sudan source-record arm | Points out of 70 | Critical guard |
|---|---:|---|
| Pooled solo | 42 | Failed |
| Independent drafts | 42 | Clear |
| Interactive | 49 | Clear |

All three records preserve the differing votes and both delegations' reasons. All omit the complete roll call and the common consultation interest. The solo record attributes implementation-gap concerns to China, which had described missing proposals and concerns in the draft. The interactive record alone preserves humanitarian access as part of the unadopted text. The two compact team chairs receive byte-identical second revisions, identical sources and the same synthesis instruction. Only the first revision differs. Neither revised note supplies the access claim. The paired gain therefore reflects which part of the existing docket the chair used when the first revision changed. The three same-assistant annotations cover one new family, with independent review still pending. The 137-word authored reference demonstrates that the full docket and role contrast fit the cap. [Scores and budgets](../evidence/source-record-sudan/scores.json) · [Single-revision comparison](../evidence/source-record-sudan/process.json) · [Reference record](../evidence/source-record-sudan/reference.txt)

### Fit agents to route verifiable source blocks

Use a separate communication task with a bounded chair view. Each of two simultaneous agents can send one exact source block or stay silent. The chair starts with the public docket and a subset of four role blocks. One Russian position block and one Chinese position block each make a country-position claim verifiable. A common-ground claim requires both qualification blocks. The objective credits newly available proofs and charges 0.2 per transmission. For a fixed start state, including credit for proofs already available adds a constant to every action. Model-generated statements and model judge scores stay outside the fit.

Train a seven-coefficient shared policy on 192 procedural cases for 120 exact team-gradient updates. Agents know the public evidence encoding, their own availability and the common proof requirements. The joint planner can additionally see both seats' availability. The finite-difference gradient check agrees within 0.000000001. The synthetic training objective rises from 8.907 to 12.360. [Fit and all Sudan masks](../evidence/source-route-fit/fit.json)

| Policy | Sudan mean team return, 16 masks | Sudan mean messages | Synthetic mean return, 256 new draws |
|---|---:|---:|---:|
| Independent immediate-coverage script | 17.250 | 1.250 | 10.809 |
| Send the first available new block | 17.638 | 1.500 | 10.979 |
| Learned communication | 17.638 | 1.500 | 11.026 |
| Joint planner | 17.663 | 1.375 | 11.093 |

The synthetic draws use more missing private blocks than training. On Sudan the learned policy matches the new-block script's mean, with 14 of 16 returns tied with the planner. It sends one unnecessary block in each of two masks. When both positions are already public, immediate-coverage routing sends nothing and leaves the two-role consultation comparison unsupported. The learned policy, new-block script and joint planner all send both qualification blocks and make that comparison supportable. These are proof-availability points on variants of one exposed docket, separate from the 70-point prose rubric. [Policy comparisons and gradient audit](../evidence/source-route-fit/audit.json)

### Test whether routed qualifications survive into the memo

Use the frozen Qwen3.5-4B chair with the same public docket and role-position blocks. Vary only receipt of the Russian and Chinese qualification blocks. The no-qualification case reproduces the immediate-coverage route. The two-block case reproduces the learned, new-block and joint-planner routes. All four chair prompts have a 256-token output ceiling. The factual review checks each record against its actual received packet. [Routed prompts and unedited memos](../evidence/source-route-memos/transcript.jsonl)

All four original memos score 56/70 and have a clear material factual guard. None states the supported common ground. The two-block memo gains the complete roll call and ends with an unfinished next step at the token cap. It realizes 14 of 21 routing-related points, like the other three. Verifiable coverage rises from 14 to 21 points as the two messages arrive. That gain did not carry over to the memo in this prompt. The first attempt left a launch receipt and no output. The recovered run used the same prompts and a fresh directory. [Review and exact quotes](../evidence/source-route-memos/scores.json) · [Replay](../evidence/source-route-memos/replay.json)

### Require evidence from both sides before stating common ground

Repeat the four frozen evidence conditions with a 120-word instruction that puts consultation first, asks for a source from each delegation and permits an insufficient-evidence answer. All four meet the shorter word cap. All four turn China's ceasefire position into unsupported common ground, even in the two-block condition. The retest scores 21–28/70, with a failed factual guard in every case. The instruction increases mention of common ground while lowering factual quality. [Unedited retest and source-linked ratings](../evidence/source-route-memos/focused/scores.json)

For a bounded control, retain the reviewed factual portions of the original memos and compile the consultation sentence from the two exact qualification blocks. Where one or both blocks are missing, the added text says the received evidence cannot establish a shared consultation position. The compiler withholds the final analytical section if the original reached the token cap. It retains the other model prose verbatim. All four records fit in 124–149 words. Carry-forward scores are 56, 56, 49 and 63 across no, Russian-only, Chinese-only and both qualifications. The Chinese-only record loses its previously credited next step when the capped section is removed. The full record gains the one compiled criterion. All eight injected changes to received source IDs or text are rejected.

This is a same-case compilation rule with an authored comparison and a reviewed model body. The learned route and both strong scripts deliver the same qualifying packet. The 63-point record establishes transfer from the evidence to an auditable output with that renderer. It supplies no new evidence that the learned route beats those scripts or that free-form writing recovered the supported comparison. [Exact released text, carried-forward points and source checks](../evidence/source-route-memos/release.json)


### Measure whether an availability signal earns its cost

Give each delegate one optional truthful signal that its qualification is available, followed by one evidence slot. Signals are simultaneous and cost 0.05. Each delegate chooses a source block or silence after seeing the two bits. Evidence blocks cost 0.20. Each delegate can privately have neither block, just the position, just the qualification or both. For each public mask, score all 16 equally likely combinations of those inventories. The exact decentralized control enumerates legal signal policies and separately optimizes the two delivery policies conditional on the revealed bits. Neither delegate gets the peer's inventory directly.

| Policy | Mean net proof return |
|---|---:|
| Always announce availability, with optimal delivery | 13.6023 |
| Optimal with no availability signal | 13.6336 |
| Learned from team return, 180 updates | 13.6336 |
| Learned with a truthful-signal warm-up, 580 updates | 13.6336 |
| Optimal with an optional availability signal | 13.6477 |

Both learned policies match the best silent policy on all 16 public masks and send zero signals across the 256 inventory variants. The optional signal helps in four public masks. When both positions are already public, silence yields 15.55 with one block sent per episode on average. Delegates can instead announce availability and send the qualifications only when both have signaled. Both routes prove the comparison in one quarter of episodes. The second route uses one signal and half a block per episode on average, raising mean return to 15.60. This contrast tests selective transmission and its cost. It does not test whether a chair uses the proof correctly in a memo.

Both fits use exact gradients of the expected team return and synthetic training inventories and weights. The warm-up holds the truthful signal policy fixed for 220 updates before 360 joint updates. All evaluation conditions reuse one exposed Sudan docket. No language model was trained or run. [Direct fit and world-level outcomes](../evidence/source-route-signal/report.json) · [Warm-up and joint fit](../evidence/source-route-signal/curriculum.json)

From this directory, run the following with the existing NumPy and PyTorch environment to replay both reports.

```sh
python -B source_route_signal.py | cmp - ../evidence/source-route-signal/report.json
python -B source_route_curriculum.py | cmp - ../evidence/source-route-signal/curriculum.json
```


### Learn paid signaling by searching joint policies

Replace the linear policies with two decentralized tables per public view. A delegate's first action depends on its own inventory. Its evidence choice also sees the two public signals. Each search starts from silence and scores legal mutations on the same shared return. Both variants evaluate 96 proposals for 240 updates per view with a single fixed seed. The coordinated variant makes half those proposals by editing random groups of entries across agents and stages. The single-entry variant changes at most one entry per proposal. Both retain the best sampled return, including ties. They use the full synthetic inventory support and a separate scoring weight at test time. This is direct policy search with simulator access to expected returns. The exact planner is used for evaluation.

| Equal-weight Sudan evaluation | Mean net proof return |
|---|---:|
| Best silent policy | 13.6336 |
| Single-entry search | 13.6219 |
| Coordinated search | 13.6406 |
| Best optional signaling policy | 13.6477 |

Coordinated search improves on silence in two views and ties it elsewhere. Single-entry search improves on silence in three views but fails to beat it when all four role blocks start missing. There, coordinated search sends 18 blocks and eight signals across 16 inventories, compared with 24 blocks for optimal silence. The proofs match world by world. In the other improved view, blocking signals on the fitted table lowers raw proof coverage, but an optimized silent policy recovers that coverage at higher cost. These distinctions separate the value of a learned message from the value of adding the message channel. [Fitted tables and rollouts](../evidence/source-route-signal/policy-search.json) · [Coverage and signal ablations](../evidence/source-route-signal/policy-search-audit.json)

For a separate post-test diagnostic with no public role blocks, give each individual position four proof points and the two-source comparison seven. Fit the same two searches on separate synthetic weights. This checks whether signaling can improve proof coverage even against an optimized silent policy. The enumerated controls are calculated before fitting.

| Comparison-weighted contrast, 16 inventories | Mean raw proof | Mean net proof return |
|---|---:|---:|
| Best silent policy | 4.4375 | 4.1375 |
| Always announce, with optimal evidence delivery | | 4.4500 |
| Either learned policy | 4.8125 | 4.4875 |
| Exact ceiling with optional signaling | 4.8125 | 4.4875 |

Both fitted policies announce for a qualification-only inventory and stay silent when they hold both blocks. A delegate holding both switches its evidence slot to the qualification when the peer announces. They establish the comparison in three of 16 inventories, up from one for optimal silence. Each position is supported in seven inventories, down from eight. That trade improves the stipulated weighted outcome and belongs in the per-criterion scorecard. The test uses a new reward vector and the same exposed docket and information structure. It does not establish transfer to an unseen event or gains in the 70-point final record. [Exact controls, claim counts and learned outcomes](../evidence/source-route-signal/coverage-fit.json)

Reproduce with the same NumPy and PyTorch environment used above.

```sh
python -B source_route_search.py | cmp - ../evidence/source-route-signal/policy-search.json
python -B source_route_search_audit.py | cmp - ../evidence/source-route-signal/policy-search-audit.json
python -B source_route_coverage_fit.py | cmp - ../evidence/source-route-signal/coverage-fit.json
```


### Score the records produced by learned and scripted routes

Freeze the fitted comparison-weighted policy, the exact silent and always-announce controls, and the chair prompt. The chair receives the public vote and draft and only the source blocks each route delivers. It sees neither availability signals nor the routing policy name. All three routes use the same 256-token frozen Qwen3.5-4B chair. The 48 paired assignments across 16 equally likely inventories induce nine distinct source packets. Generate one record per distinct packet, then score all three policies through that shared packet-to-record map. Both control optimizations induce a unique packet schedule on these inventories. The chair prompt and unedited outputs are in the run transcript.

| Route | Simulation return | Authored reference points / 70 | Qwen verified points / 70 | Confirmed guard failures / 16 | Uncertain guards / 16 |
|---|---:|---:|---:|---:|---:|
| Optimal silence | 4.1375 | 56.44 | 47.25 | 3 | 10 |
| Always announce with optimal delivery | 4.4500 | 56.00 | 44.63 | 3 | 9 |
| Learned selective announcement | 4.4875 | 56.44 | 45.94 | 3 | 9 |

The authored source-gated references preserve supported items under 160 words. The learned route proves the comparison in two more inventories than silence and each position in one fewer, so the equally weighted final-record rubric gives them the same reference mean. The frozen chair preserves each position whenever it receives the required block but scores zero on the overlap criterion. With both qualifications it recounts each accurately and gives the vote, then hits the output cap before finishing the next step. It never states the shared consultation position. In the Chinese-qualification-only packet it attributes China's statement to Sudan. In the Russian-position-only packet it overstates the veto as explicit rejection of all measures. Six of nine unique generations hit the cap and all nine stayed within 160 words. Weighted routing points realized in model text are 4.0 for silence, 3.0 for always announce and 3.5 for the learned route.

The equal-weight authored control and the same-assistant evidence-linked annotations answer different questions. The former shows which criteria a source-gated renderer can include. The latter records what the frozen chair actually writes, with confirmed errors, ambiguous claims, and truncation tracked separately. This exposed Sudan docket uses simulated inventories and nine unique records. It does not estimate across-event generalization or independent judge agreement. [Unedited records](../evidence/source-route-endpoint/final-records.json) · [Evidence-linked annotations](../evidence/source-route-endpoint/annotations.json) · [Paired scores and policy traces](../evidence/source-route-endpoint/scores.json) · [Authored references](../evidence/source-route-endpoint/reference.json)

From this directory, replay prompts, tokens and the exact archived generation texts. The executed helper versions are in the run directory. The earlier four-packet runner retains its original hash.

```sh
python -B source_route_endpoint.py replay ../evidence/source-route-endpoint
python -B source_route_endpoint_scores.py ../evidence/source-route-endpoint --score | cmp - ../evidence/source-route-endpoint/scores.json
python -B source_route_endpoint_reference.py | cmp - ../evidence/source-route-endpoint/reference.json
```


### Learn to avoid duplicate evidence on the Venezuela dual-draft record

Freeze an equal-weight 70-point rubric for the 28 February 2019 Venezuela meeting. The chair begins with two draft-text summaries and aggregate vote outcomes. Each of two fictional dispatch desks can have a copy of either, both or neither of two source cards. One card separates Equatorial Guinea’s national votes from the Council President’s procedural announcements. The other supplies Indonesia’s abstentions and its appeal for inclusive dialogue and the Secretary-General’s good offices. These are independently credited rubric units. Review only the excerpts delivered to the chair. The case family was previously used for guard and workshop development. Both drafts have pinned UNBench text records and the U.S. roll call matches the UNSC-Bench vetoed split. [Source packet and frozen rubric](source-record-venezuela-routing.json) · [Benchmark alignment](../../crossbench/venezuela/references.json) · [Official meeting record](https://digitallibrary.un.org/record/3794247?ln=en)

Each desk has one source delivery slot. Before delivery it may truthfully signal that it has the Indonesia card. The signal can help the other desk choose its different card. Costs are 0.05 per signal and 0.20 per block. Two copies of the same card count once, and both copies still cost a delivery. Enumerate the best decentralized policies given silence, always announcing availability, or optional signaling. Train a pair of tabular policies by shared-return search on two synthetic availability distributions, with 240 updates and 96 proposals per update. The same fitted tables are used for both evaluation distributions. The optimization uses the identities of the two abstract slots and equally weighted proof points. It reads no source text or model outputs.

| Routing policy | Authored reference / 70, all 16 inventories | Authored reference / 70, nine nonempty pairs |
|---|---:|---:|
| Exact silent control | 64.75 | 66.89 |
| Always announce, with optimal delivery | 65.19 | 67.67 |
| Learned selective announcement | 65.63 | 68.44 |
| Exact optional signaling control | 65.63 | 68.44 |

Across all inventories, the learned route delivers both cards in seven of 16 cases, compared with five for optimal silence. Equatorial Guinea’s card reaches the chair in ten cases for either route. Indonesia’s card reaches it in twelve cases under learned routing and ten under silence. With only the Indonesia card at desk one and both cards at desk two, the silent control sends two copies of Indonesia’s card. The learned policy sends both signals and desk two sends Equatorial Guinea’s card. It matches the optional proof ceiling under both priors and attains the per-world maximum for all 16 inventories. It matches the net-return ceiling on the full inventory distribution and trails by 0.0222 when both desks always have at least one card. The authored references are generated from the received packet with fixed text and exact source IDs. [Exact control](../evidence/duplicate-card-routes/exact.json) · [Fitted policy and paired actions](../evidence/duplicate-card-routes/fit.json) · [Reference records](../evidence/duplicate-card-routes/references.json)

```sh
python -B duplicate_card_routes.py | cmp - ../evidence/duplicate-card-routes/exact.json
python -B duplicate_card_routes.py --fit | cmp - ../evidence/duplicate-card-routes/fit.json
python -B duplicate_card_records.py | cmp - ../evidence/duplicate-card-routes/references.json
```


#### Pass the four received packets through one frozen chair

Freeze one prompt and use Qwen3.5-4B to produce one record for each combination of received cards. The chair sees the received source excerpts alone. Use the same four outputs for all policy rollouts. The prompt requests 120 words with a 256-token cap. All four records finish in 68–96 words. An exact-span same-assistant review applies the frozen 70-point rubric and factual guard.

| Route | Verified record / 70, all inventories | Confirmed error rate | Verified record / 70, nonempty pairs | Confirmed error rate |
|---|---:|---:|---:|---:|
| Exact silent control | 41.5625 | 10/16 | 44.33 | 4/9 |
| Always announce, with optimal delivery | 41.5625 | 9/16 | 45.11 | 3/9 |
| Learned selective announcement | 42.4375 | 8/16 | 46.67 | 2/9 |

The chair earns no full credit on either private-card criterion. It gives Equatorial Guinea’s two votes without identifying the President’s procedural role. It mentions Indonesia’s two abstentions without preserving the inclusive scope of the requested dialogue. Records with both cards score 49/70 with a clear guard, because they name the Russian draft and attribute its failure to the shortage of affirmative votes. The Equatorial-Guinea-only record wrongly says Russia led opposition to its own draft. The Indonesia-only record incorrectly attributes the Russian draft’s failure to a lack of quorum. Both errors concern public evidence shared across all prompts. The numerical final-record gains arise from the distribution over those outputs. They do not establish faithful uptake of the additional national evidence. Score the two target criteria and the material guard beside every aggregate. One exposed event, four unique generations, synthetic inventories and one reviewer limit the result. [Unedited records](../evidence/duplicate-card-routes/writer/final-records.json) · [Exact-span annotations](../evidence/duplicate-card-routes/writer/annotations.json) · [Paired policy scores](../evidence/duplicate-card-routes/writer/scores.json)

```sh
python -B duplicate_card_writer.py replay ../evidence/duplicate-card-routes/writer
python -B duplicate_card_score.py ../evidence/duplicate-card-routes/writer --score | cmp - ../evidence/duplicate-card-routes/writer/scores.json
```


#### Rerun the chair with explicit evidence-specific fields

Retain the same four evidence packets, writer, decoding, 256-token caps, route tables and frozen rubric. Replace only the writer instruction. Give each draft its own symbol, tally and reason fields. Each available national card gets a dedicated checklist. The CHAIR checklist asks for the speaker, procedural capacity and each national vote. The INDONESIA checklist asks for the two votes, scope of dialogue, and who was asked to accept whose good offices. The checklist specifies fields without supplying their values. [Locked prompts](../evidence/duplicate-card-routes/slots-lock.json) · [Unedited records](../evidence/duplicate-card-routes/slots/final-records.json)

| Received cards | Verified points / 70 | Complete national criteria | Guard | Words |
|---|---:|---|---|---:|
| Neither | 49 | None | Clear | 157 |
| Equatorial Guinea only | 63 | Equatorial Guinea | Uncertain | 142 |
| Indonesia only | 42 | Indonesia | Clear | 179 |
| Both | 49 | Indonesia | Clear | 136 |

All four now identify the two drafts, the tallies and the different reasons they failed. The chair preserves the President’s capacity when it has the Equatorial Guinea card alone. It drops that detail after receiving both cards. It preserves Indonesia’s inclusive dialogue and good-offices appeal both times it receives that card. All four exceed the requested 120 words. The Indonesia-only record also exceeds the 160-word benchmark limit and reaches the token cap. The Equatorial-Guinea-only record’s statement that national statements were absent is ambiguous after its correct procedural and national-vote sentence. None has a confirmed material factual error in completed text. No record earns both national criteria. [Evidence-backed evaluations and scores](../evidence/duplicate-card-routes/slots/scores.json)

With the new writer, learned routing averages 49.44/70 across all 16 inventories. Optimal silence under the evidence reward averages 51.19 and always announcing averages 49.00. Learned routing raises the realized Indonesia criterion from 10 to 12 inventories and lowers the Equatorial Guinea criterion from five to three. It replaces the Equatorial-Guinea-only packet with both cards in two matched inventories. Each replacement loses the chair-capacity criterion and gains the Indonesian criterion. The record also omits the analytical suggestion and the international-observation qualifier. Crediting the partial observation clause would lift both aggregate scores while retaining the direction of the routing comparison.

Retrospective enumeration has the same maximum of 0.9375 complete national criteria per inventory under all three signaling channels for these four texts. Optimizing raw points directly also gives the same 59.5 ceiling for all three channels, using different routes from the ones optimized on evidence. Counting points only on clear, completed records under 160 words gives 24.50 for the learned policy and 18.38 for silent routing, with an exact ceiling of 49.00 for either channel. These criteria capture different outcomes. The adapted prompt improves extraction and factual handling on this exposed case. It still fails to compose both national accounts when both sources are delivered. No language-model weights changed. [Ceilings under alternative endpoints](../evidence/duplicate-card-routes/paired-endpoint-ceilings.json) · [Annotations and exact quote checks](../evidence/duplicate-card-routes/slots/annotations.json)

```sh
python -B duplicate_card_slotted.py replay ../evidence/duplicate-card-routes/slots
python -B duplicate_card_slotted.py score ../evidence/duplicate-card-routes/slots | cmp - ../evidence/duplicate-card-routes/slots/scores.json
python -B duplicate_card_alignment.py ../evidence/duplicate-card-routes/writer/scores.json ../evidence/duplicate-card-routes/slots/scores.json | cmp - ../evidence/duplicate-card-routes/paired-endpoint-ceilings.json
```


#### Generate each national account separately and preserve it in the record

Keep the four Venezuela packets and the routing policies fixed. Use the same frozen Qwen3.5-4B to generate one public component and one component for each national card. Each national generation sees its own card only. Join the original outputs in a stable order, including only components for received cards. The public generation gets up to 144 tokens and each national generation up to 56. The combined ceiling is at most 256 like the single-call chair. The input-token cost and number of component completions differ. Across the 16 learned-route assignments, the modular writer averages 2.375 components, 511.375 input tokens and 170 output tokens. The field-specific single-call writer averages one completion, 462.625 input tokens and 237.3125 output tokens. [Locked prompts](../evidence/duplicate-card-routes/modular-lock.json) · [Unedited components](../evidence/duplicate-card-routes/modular/final-records.json) · [Token and call accounting](../evidence/duplicate-card-routes/modular/costs.json)

Both Qwen national components satisfy their complete criteria. The CHAIR component includes the speaker, Council presidency and two national votes. The INDONESIA component includes the two abstentions, inclusive dialogue and the appeal concerning the Secretary-General’s good offices. When both cards arrive, the raw assembly preserves both components verbatim. Across 16 inventories the learned route preserves both complete national accounts in seven records, against five for optimal silence and six for always announcing. This is the first writer on this fixture that realizes the difference in both-card availability as a difference in both completed national criteria.

The modular public component omits the two draft symbols, the permanent-member veto mechanism and several substantive qualifiers. It invents eight numeric citation IDs. Those defects appear in all four assemblies, so the fully generated version scores 21–35/70 despite successful national uptake. The material factual guard and citation integrity are tracked separately. All three generations finish before their caps. The joined records span 77–118 words. [Raw assemblies](../evidence/duplicate-card-routes/modular/composed.json) · [Evidence-linked scores](../evidence/duplicate-card-routes/modular/scores.json)

As a separate same-case control, place the unchanged model national text between the existing authored public reference and analytical suggestion. Attach the CHAIR source tag where the component omitted it. The resulting records contain 92–134 words, use only delivered citation IDs and meet the authored public plus reviewed national criteria. There is no further model call. The public material and its criterion credits are authored. The two national facts are model-generated and same-assistant reviewed.

| Route across 16 simulated inventories | Both national criteria | Fully generated score / 70 | Authored public plus model national score / 70 |
|---|---:|---:|---:|
| Optimal silent delivery | 5/16 | 29.75 | 64.75 |
| Always announce with optimal delivery | 6/16 | 30.19 | 65.19 |
| Learned selective announcement | 7/16 | 30.63 | 65.63 |

This establishes receipt-to-record uptake on an exposed docket with source-specific prompts. The result concerns two national accounts and a shared authored public core. Independent scoring and transfer with new events, sources and unfamiliar partners remain open. [Hybrid records, component provenance and exact scores](../evidence/duplicate-card-routes/modular/hybrid.json)

```sh
python -B duplicate_card_modular.py replay ../evidence/duplicate-card-routes/modular
python -B duplicate_card_modular.py compose ../evidence/duplicate-card-routes/modular | cmp - ../evidence/duplicate-card-routes/modular/composed.json
python -B duplicate_card_modular_review.py ../evidence/duplicate-card-routes/modular --score | cmp - ../evidence/duplicate-card-routes/modular/scores.json
python -B duplicate_card_hybrid.py ../evidence/duplicate-card-routes/modular | cmp - ../evidence/duplicate-card-routes/modular/hybrid.json
```


### Transfer the frozen router and modular writer to the DPRK Panel renewal docket

Use the 28 March 2024 proceedings on S/2024/255. The United States proposed renewing the Panel of Experts that assisted the 1718 Committee. Russia vetoed the draft and China abstained. The Panel mandate ended, while the Committee and existing sanctions continued. The benchmark join verifies the UNBench draft and matches all 15 votes to the UNSC-Bench vetoed row indexed 8. The two national cards test Japan’s national statement by the Council President and China’s explanation of its abstention. The case and criteria were frozen before the three writer generations. [Official meeting record](https://digitallibrary.un.org/record/4042816?ln=en) · [Veto report](https://digitallibrary.un.org/record/4042986?ln=en) · [Committee report](https://documents.un.org/doc/undoc/gen/n25/342/61/pdf/n2534261.pdf) · [Benchmark join](../evidence/duplicate-card-routes/dprk-sources.json)

Apply the exact archived Venezuela routing table to the two new slots, without fitting. Under the uniform inventory distribution the router sees the same inputs as before. As a separate distribution test, give desk one more Japan-only inventories and desk two more China-only inventories. Retain the same action rules and costs, and recompute the exact silent and always-announce controls under each prior. The learned policy reaches the optional-signaling net ceiling under both. Both cards arrive with probability 43.75% versus 31.25% for optimal silence under the uniform prior, and 69% versus 65% under the asymmetric prior. [Frozen policy and all matched routes](../evidence/duplicate-card-routes/dprk-routes.json)

| Prior | Route | Both cards delivered | Both complete national accounts | Hybrid points / 70 |
|---|---|---:|---:|---:|
| Uniform | Optimal silence | 31.25% | 0% | 60.375 |
| Uniform | Always announce with optimal delivery | 37.50% | 0% | 59.9375 |
| Uniform | Learned | 43.75% | 0% | 60.375 |
| Asymmetric | Optimal silence | 65% | 0% | 61.74 |
| Asymmetric | Always announce with optimal delivery | 67% | 0% | 61.60 |
| Asymmetric | Learned | 69% | 0% | 61.74 |

Use the modular writer's 144-token public and 56-token national ceilings with case-specific evidence fields. The model identifies Yamazaki in his national capacity and attributes his assessment of the veto accurately. It preserves China’s abstention, the unaddressed Russian views and both substantive positions, but omits that China said time remained for consultations. Under the strict component review the hybrid therefore preserves the Japan component verbatim where received and withholds the incomplete China component. The released hybrid has a new authored public reference and four records of 87–107 words. The Japan card arrives at the same rate under learned routing and optimal silence, so the additional China deliveries produce no increase in verified record points. Exact retrospective optimization for this hybrid score reaches 61.25 uniformly and 62.02 under skew using silent delivery, by prioritizing the only eligible national component.

The generated public paragraph omits the tally and the sponsor. Its description of the proposed end date and current Panel duties is ambiguous. The frozen REPORTING excerpt also permits a reading that both reports were confidential. The draft explicitly labels the midterm report confidential and separately asks for a final report. The rubric and authored reference require both proposed reports without assigning confidentiality to the final report. The model never separates the two. All three archived generations completed early. This is transfer of an unchanged routing table to new inventories and a new set of evidence cards. The texts never enter the routing policy. Writing transfer uses source-specific prompts, prepared reference prose and same-assistant review. [Verbatim components](../evidence/duplicate-card-routes/dprk/final-records.json) · [Annotations](../evidence/duplicate-card-routes/dprk/annotations.json) · [Four records, scores and exact ceilings](../evidence/duplicate-card-routes/dprk/scores.json)

```sh
python -B duplicate_card_transfer_routes.py | cmp - ../evidence/duplicate-card-routes/dprk-routes.json
python -B duplicate_card_transfer.py replay ../evidence/duplicate-card-routes/dprk
python -B duplicate_card_transfer_review.py ../evidence/duplicate-card-routes/dprk --score | cmp - ../evidence/duplicate-card-routes/dprk/scores.json
```


#### Test checklist instructions and evidence order on the incomplete China account

Run the same frozen writer with a 56-token cap and a six-field checklist. Require the abstention, the unaddressed Russian views, the consultation-time qualification, independent Panel work, a sanctions time limit and periodic reviews. The checklist names each field and leaves the value to the evidence. The primary prompt receives the original card. A pre-specified order contrast moves the abstention explanation to the beginning without changing the sentences. The withheld-source control removes only the consultation-time clause and keeps all other content and the checklist. [Frozen runs and exact prompts](../evidence/duplicate-card-routes/dprk-qualification-lock.json)

| China component | Required fields preserved | Factual guard |
|---|---:|---|
| Original writer, original card | 5/6 | Clear |
| Checklist, original card | 4/6 | Failed |
| Checklist, reordered card | 6/6 | Clear |
| Checklist, consultation clause withheld | 5/5 available | Clear |

The primary checklist output says consultation time remained insufficient and omits the objection about the Russian views. The reordered card yields a complete account. Withholding the clause leaves it unstated while retaining the other five fields. All new components finish before the token cap in 23–25 words. The factual reversal would pass a check for mere mention of consultations. The guard requires the directional claim and the exact supporting span. [Unedited responses](../evidence/duplicate-card-routes/dprk-qualification/final-records.json) · [Field-level annotations](../evidence/duplicate-card-routes/dprk-qualification/annotations.json)

The primary composition keeps the prior authored public reference and originally verified Japan account, and withholds the failed China account. Learned and optimal silent delivery still tie at 60.375/70 under uniform inventories and 61.74 under skew. In the order diagnostic, the unchanged learned policy and silent control use the same successfully reviewed China output whenever its card arrives. Learned routing then scores 65.625 versus 64.75 under uniform availability and 67.76 versus 67.48 under skew. The four diagnostic assemblies reuse the existing public reference and verified Japan language, preserve the accepted China wording verbatim, and stay within 160 words.

The order contrast isolates a same-source, same-instruction change at fixed decoding. It demonstrates a record-level effect through a successful source presentation on this case and exposes a grounding failure under the original presentation. It does not establish robust transfer of the writer or improve the primary comparison. No routing policy or model weights changed. [Exact pairing, rejected output and both record replays](../evidence/duplicate-card-routes/dprk-qualification/scores.json)

```sh
python -B duplicate_card_qualification.py replay ../evidence/duplicate-card-routes/dprk-qualification
python -B duplicate_card_qualification_review.py ../evidence/duplicate-card-routes/dprk-qualification --score | cmp - ../evidence/duplicate-card-routes/dprk-qualification/scores.json
```


### Fit communication for the verified record rather than card count

Keep the two-agent action space and the archived writer outputs. Treat the four possible receipts as distinct outcomes. Fit a repertoire of decentralized announcement and delivery policies on nine synthetic team-reward profiles. These profiles include one useful card, two complementary cards, and negative reward when partial evidence produces a rejected record. At evaluation time a selector sees a public table of estimated writer scores. It selects a learned policy using the original training distribution. Each desk then acts using its own inventory and the two announced bits. The selector receives neither desk's actual inventory. Evaluate on uniform and asymmetric distributions that are separate from optimization. [Learned tables, proxy and test returns](../evidence/duplicate-card-routes/outcome-policy.json)

For the original Venezuela writer, an empty receipt produces an eligible 35-point record and both cards produce 49 points. Each single-card receipt produces a rejected record and earns zero under the strict release objective. The first learned selection sends a single card in 25% of uniform scenarios and scores 31.2625 after costs. The optimal silent policy scores 35. Under skew the same learned policy scores 38.787 but still creates rejected records in 15% of scenarios. Average reward alone masks that failure. Add a selector that rejects any candidate policy capable of producing a disallowed single-card receipt when a valid fallback is available. The stronger synthetic penalty still leaves both the cold and warm local searches at silence. [Guarded cold search](../evidence/duplicate-card-routes/guarded-policy.json) · [Warm-start replay](../evidence/duplicate-card-routes/guarded-warm-policy.json)

Optimize the coordinated moves under the synthetic guarded reward by evaluating the two announcement mappings and their conditional delivery actions together. Compile the result into two tables and verify that neither desk's table accesses the other's private inventory. The final policy sends both cards only after two positive bits. Desk one announces only when it has both cards. Desk two announces whenever it holds the second card. The learned tables were fit on synthetic reward magnitudes and the original training prior. Only the public policy choice uses archival calibration. [Joint-phase fit and exact matched controls](../evidence/duplicate-card-routes/guarded-phase-policy.json)

| Original Venezuela writer, strict release objective | Uniform net points | Asymmetric net points | Rejected records |
|---|---:|---:|---|
| Exact silence | 35.0000 | 35.0000 | 0% under both |
| First outcome-based selection | 31.2625 | 38.7870 | 25% uniform, 15% asymmetric |
| Guarded joint-phase policy | 36.6625 | 37.1260 | 0% under both |
| Exact optional signaling with rejected receipts disallowed | 36.6625 | 37.1260 | 0% under both |

Writer calibration still determines which routing result is useful. The same selector prefers prioritizing Japan with the original DPRK writer. It scores 61.0625 versus 60.05 for the proof-trained router under uniform availability. With the reordered DPRK writer, the selector uses the frozen proof router and reaches 65.30. Reusing the original calibration on the reordered writer instead scores 61.0625. This is a deliberately stale calibration control. The calibration uses all four archived receipt scores and the release annotations from a single reviewer. The exact safety check only covers that frozen mapping and the 16 simulated inventories. No new language generations or language-model updates were made.

```sh
python -B duplicate_card_outcome_policy.py | cmp - ../evidence/duplicate-card-routes/outcome-policy.json
python -B duplicate_card_guarded_policy.py | cmp - ../evidence/duplicate-card-routes/guarded-policy.json
python -B duplicate_card_guarded_policy.py --warm | cmp - ../evidence/duplicate-card-routes/guarded-warm-policy.json
python -B duplicate_card_guarded_policy.py --phase | cmp - ../evidence/duplicate-card-routes/guarded-phase-policy.json
```


### Stress-test the learned protocol under message loss and unfamiliar partners

Replay the original guarded Venezuela policy and the archived proof router. Erase each announcement at its receiver and each card at the chair independently. Charge for every attempted transmission. Compare a writer that uses any received cards with a buffer that releases both distinct cards together and otherwise supplies the approved public-only packet. Both use the same archived records and scoring rule. [Exact transport audit](../evidence/duplicate-card-routes/transport-audit.json)

| Uniform inventories, original guarded protocol | Direct net score | Direct rejected records | Buffered net score | Buffered rejected records |
|---|---:|---:|---:|---:|
| Matching team, reliable links | 36.6625 | 0% | 36.6625 | 0% |
| Matching team, 10% signal and card erasure | 34.7191 | 3.8475% | 36.0657 | 0% |
| Older proof router replaces desk one, reliable links | 8.5375 | 75% | 34.7875 | 0% |
| Older proof router replaces desk two, reliable links | 8.5500 | 75% | 34.8000 | 0% |

The buffer prevents calibrated single-card releases by construction. It preserves both-card evidence when both cards arrive, and a desk can still pay to send a card that gets discarded. The control for silence with the buffer therefore optimizes which cards to attempt for every local inventory. It can exceed the score of silence with direct delivery.

Fit local announcement and delivery policies on a synthetic seven-point reward for a complete buffered pair, at a 15% per-link erasure rate. Enumerate the joint combinations while retaining each desk's local observations at execution. Train one pair for matched partners and a second with an equal mixture of matched and mixed teams. The first mixed run uses the older proof router and returns the same performance as the matched fit. The wider mixed run adds the guarded protocol and two silent slot-priority scripts. Evaluate it against two archived policies absent from this population. The figures average both seat swaps against each held-out policy. [Matched and single-partner fit](../evidence/duplicate-card-routes/buffered-fit.json) · [Wider training population and held-out cross-play](../evidence/duplicate-card-routes/buffered-diverse-fit.json)

| Uniform, buffered, 10% signal and card erasure | Net score |
|---|---:|
| Exact silent control | 38.24375 |
| Archived proof router or new matched fit with its own teammate | 39.422375 |
| Exact optional-signaling control | 39.422375 |
| Matched fit with held-out teammates | 38.58947 |
| Wider population fit with held-out teammates | 38.58666 |

The 10% and 25% tests are outside the training erasure rate. Under uniform availability, the matched fit reaches the exact optional ceiling at both rates, matching the older proof router. Under asymmetric availability at 25% loss it scores 39.68337 against 39.75875 for exact silence and an optional ceiling of 39.88088. Training against the wider population helps one seat swap with a known guarded partner and yields no average gain on the held-out teammates. The buffer protects the approved record boundary even in those cases. The learned cooperation advantage can shrink or reverse with partner or inventory changes. All outcomes are exact replays against one calibrated writer and synthetic faults. No language-model updates or new writer calls were made.

```sh
python -B duplicate_card_transport.py | cmp - ../evidence/duplicate-card-routes/transport-audit.json
python -B duplicate_card_buffered_fit.py | cmp - ../evidence/duplicate-card-routes/buffered-fit.json
python -B duplicate_card_buffered_fit.py --diverse | cmp - ../evidence/duplicate-card-routes/buffered-diverse-fit.json
```


### Execute the learned routing protocol through language-model decisions

Translate the fitted buffered policy into desk-specific prose. Give a frozen Qwen3.5-4B desk only the source excerpts it holds and the announcement it received. Include every local inventory and physically possible signal view for both desks in Venezuela and DPRK. Score the next-token A/B/C menu on all 64 prompts. An unsupported action is one that announces a missing card or tries to deliver one. Measure agreement before and after masking impossible actions. The deterministic controls use the same policy and buffered writer interface. The DPRK replay uses the archived reordered-card hybrid response. [Locked prompts](../evidence/duplicate-card-routes/language-lock.json) · [Raw next-token evidence](../evidence/duplicate-card-routes/language/actions.jsonl)

The highest-scoring menu action matches 14 of 16 announcements and 22 of 48 dispatches. Twelve choices are physically unsupported across all 64 views. A legality mask raises agreement to 15 of 16 announcements and 25 of 48 dispatches. Mean probability on the menu letters is about 99% for both dockets. This measures format compliance separately from the correctness of the selected action. The probe includes local views reachable after a model error or message loss alongside views reached by the typed policy.

| Uniform inventories, 10% loss per signal and card | Venezuela net | DPRK net |
|---|---:|---:|
| Exact buffered silent control | 38.24375 | 59.24375 |
| Typed learned policy | 39.422375 | 60.422375 |
| Qwen decisions with impossible actions masked | 36.869625 | 57.882125 |
| Typed announcements, Qwen dispatch | 36.882125 | 57.882125 |
| Qwen announcements, typed dispatch | 37.486625 | 60.422375 |

The typed-dispatch substitution preserves the routing gain on DPRK. In Venezuela, the first desk incorrectly announces with both cards. That signal changes the other desk's action and leaves the hybrid below silence, even with typed delivery. In a post-result diagnostic with typed delivery, accept a physically legal model announcement only when its first-choice odds against the other menu action are at least three to one. Otherwise use the fitted signal. This accepts three of eight optional announcement observations and restores the typed result on both dockets. Such a fallback is an interface check when the correct table is already available. It does not verify general model confidence calibration.

Using Qwen for both stages scores below optimal buffered silence under all tested inventory and loss conditions. This is a frozen-model handoff test using one-token decisions, archived writer scores, and exact replay of their effects. It does not measure unaided language negotiation or an online system's latency. No language weights were updated. [Action mismatches, stage ablations and score replay](../evidence/duplicate-card-routes/language/score.json) · [Confidence diagnostic](../evidence/duplicate-card-routes/language/confidence.json)

```sh
python -B duplicate_card_language_review.py ../evidence/duplicate-card-routes/language | cmp - ../evidence/duplicate-card-routes/language/score.json
python -B duplicate_card_language_confidence.py ../evidence/duplicate-card-routes/language | cmp - ../evidence/duplicate-card-routes/language/confidence.json
```


### Optimize local action scores with the joint record reward

Freeze the Qwen backbone and the 64 archived next-token probes. Fit local signal and delivery logit offsets against the expected joint writer reward. The exact objective enumerates the two private inventories, signal choices and signal loss. Two distinct cards earn seven synthetic points when both reach the buffer. Charge every attempted transmission. Each step differentiates the expected return of both desks together. No target action labels or archived prose-quality scores enter training. Fit on Venezuela logits and the synthetic training prior at 15% per-link loss. Test on both inventory distributions and 0%, 10% and 25% loss. DPRK logits are excluded from fitting. The prior writer assessments enter only in the record-score replay.

Use 240 updates per arm. The full local-offset fit raises synthetic expected return from 0.9005 to 2.3579. Learning the same table from zero logits reaches 2.3484, and fitting the offsets with signals disabled reaches 1.7823. At update 40, the Qwen-initialized fit is at 2.3086 and the zero-initialized fit is at 2.0171 on this single trace. These are cost-adjusted expected training rewards. The central optimizer sees the training distribution. At execution each table lookup uses the local inventory and received signal.

| Uniform inventory, 10% loss, greedy local decisions | Venezuela net | DPRK net |
|---|---:|---:|
| Frozen Qwen with legal masking | 36.869625 | 57.882125 |
| Exact buffered silent control | 38.24375 | 59.24375 |
| Reward-trained local offsets on frozen Qwen | 39.422375 | 60.422375 |
| Reward-trained table from zero logits | 39.411125 | 60.411125 |
| Same trained Qwen offsets with the Qwen logits removed | 39.422375 | 60.422375 |

The full-offset fit recovers the earlier typed controller's greedy score across all 12 conditions. Simple learning from zero falls short by about 0.01 points at 10% loss. Removing the frozen logits preserves the greedy return. The state-indexed offsets can store the dispatch policy, so this result measures whether the team objective can learn coordination on a fixed interface. It does not isolate a contribution from the language model. Under asymmetric inventories at 25% loss the fit scores below the exact silent solution in both dockets. The exact probabilities were independently replayed on all 12 conditions and the gradient checks are in the artifact. [Full fitted offsets, controls and all test conditions](../evidence/duplicate-card-routes/language/reward-fit.json)

```sh
python -B duplicate_card_language_rl.py > /tmp/route-reward-replay.json
cmp /tmp/route-reward-replay.json ../evidence/duplicate-card-routes/language/reward-fit.json
```


#### Restrict the correction to 16 shared biases

Fit one announcement bias per action and desk. For delivery, share each desk's three action biases across its inventories and its own announcement, with a separate vector for each received peer bit. This gives 16 stored values. The masks still enforce which cards the desk can send. Use the same training objective and 240 updates, contrasting frozen Venezuela logits with a zero-logit fit. This adaptive follow-up reduces capacity enough that it cannot set arbitrary values for all local views.

| DPRK logits held out, uniform inventory and 10% loss | Greedy net | Stochastic net conditional on legal actions |
|---|---:|---:|
| Frozen Qwen | 57.882125 | 57.930095 |
| Exact buffered silent control | 59.243750 | |
| Sixteen fitted biases on Qwen | 59.808250 | 59.783710 |
| Sixteen fitted biases from zero | 59.888325 | 59.846375 |
| Qwen-fitted biases with the Qwen logits removed | 59.808250 | 59.730908 |
| Full local offsets on Qwen | 60.422375 | 60.415090 |

Greedy scores still coincide when the Qwen logits are removed, across both dockets and all six conditions per docket. The probabilities under stochastic decoding differ. The Qwen-initialized small fit scores higher than the zero fit under asymmetric inventories at 10% loss, but still scores below the exact silent control on both dockets at 25% asymmetric loss. The public receiver bit, card-availability masks and trained biases are enough to recover the measured greedy gain under uniform availability. Neither parameterization demonstrates that routing depends on semantic understanding of the card text. The rollout uses an identical two-slot schema on both dockets. The DPRK outputs are independent of the optimizer inputs and were already exposed during development. Both sets of 12 stochastic returns were checked with independent arithmetic over the logged policies. [Shared-bias fit and per-condition tests](../evidence/duplicate-card-routes/language/reward-fit-small.json)

```sh
python -B duplicate_card_language_small_rl.py | cmp - ../evidence/duplicate-card-routes/language/reward-fit-small.json
```


### Test whether a single policy transfers across reader and inventory shifts

Model a reader that can accept an incomplete passage or miss a complete passage without swapping the two roles. Fit local announcement and delivery tables to synthetic team reward by enumerating legal policy pairs. Each desk sees its own predicted inventory and the received bit. The optimizer uses the probability of the real inventory given those observations. Unsupported deliveries still cost a transmission and fail the evidence gate. The silent comparator is independently optimized for each test regime with access to the same reader.

Both average-reward and worst-case-gain fitting under reader noise reproduce the previously fitted routing behavior. Adding three distinct shifted inventory and transport configurations to training leaves the same test scores. Over these six training configurations the best fixed table's worst gain relative to the separately optimized silent policies is −0.03969 net points. This exact comparison is confined to deterministic tables and the stated training configurations. Across the 20 evaluation configurations the frozen policy beats the matched silent control in 15. Its largest loss is 0.45847 points with skewed inventories, 25% per-link loss and a reader that often accepts incomplete passages. The test also includes a correlated-noise regime in which both desks share a latent reader condition. [Noise-aware fit](../evidence/duplicate-card-routes/noisy-reader-fit.json) · [Mixed-prior fit](../evidence/duplicate-card-routes/noisy-reader-mixed-priors.json)

#### Calibrate when to use communication

Compare the frozen communicating policy with the silent control on paired simulated pilots. Each pair shares the true inventories, reader errors, signal loss and card loss. Deploy the communicating policy only when a one-sided bound on mean gain is above zero. The bound uses a predeclared 29-point range for the paired difference and covers 20 conditions at two pilot sizes with a 5% family risk budget. Independently enumerate the true gain to audit decisions after selection.

| Paired pilot draws per condition | Conditions selected out of 20 | Selected conditions with negative true gain | Mean gain across conditions |
|---|---:|---:|---:|
| 4,096 | 2 | 0 | 0.10182 |
| 262,144 | 12 | 0 | 0.28910 |

The smaller pilot leaves 13 positive-gain conditions on silence. The larger pilot leaves three. The silent candidate is optimized for the known simulated regime, and the pilot draws use the exact simulator. These are virtual episodes with no new language-model calls. The large pilot is an evaluation of sample requirements, not a realistic budget for new Council-record judgments. The claim applies to a stable regime and the stated payoff range. Neither the fit nor the selector uses the pending Qwen semantic measurements. [Paired calibration, exact differences and choices](../evidence/duplicate-card-routes/noisy-reader-selector.json)

```sh
python -B duplicate_card_noisy_reader_fit.py | cmp - ../evidence/duplicate-card-routes/noisy-reader-fit.json
python -B duplicate_card_noisy_reader_fit.py --mixed-priors | cmp - ../evidence/duplicate-card-routes/noisy-reader-mixed-priors.json
python -B duplicate_card_reader_selector.py | cmp - ../evidence/duplicate-card-routes/noisy-reader-selector.json
```


### Ground local card roles in source passages

Run frozen Qwen3.5-4B on 16 anonymous passages from the Venezuela and DPRK dockets. Each prompt lists the two required facts and a neither option. Freeze an original, reordered, incomplete and fact-reversed version for each evidence role. Reversal passages are synthetic controls. Rotate every semantic answer through all three menu positions, for 48 scored probes. Use the frozen classification results to derive each desk’s local inventory before applying the previously fitted routing policy. The replay counts unsupported attempts before the evidence gate and scores only attested receipts. [Frozen passages and role key](../evidence/duplicate-card-routes/semantic-lock.json) · [Raw model scores](../evidence/duplicate-card-routes/semantic/actions.jsonl)

| Reader | Venezuela, correct out of 8 | DPRK, correct out of 8 |
|---|---:|---:|
| Mean probability across the three orders | 7 | 6 |
| Require agreement across all orders | 8 | 6 |

Five passages have at least one changed decision across rotations. For Venezuela, the agreement rule rejects a chair-only excerpt that omits Equatorial Guinea’s national votes. Averaging probabilities incorrectly accepts that excerpt. For DPRK, Qwen accepts the incomplete China passage in all three orders despite the missing consultation-time qualification. It rejects the complete Japan passage in all three orders after the national-capacity sentence is moved to the end. Requiring agreement cannot repair either stable error.

| Uniform inventories, 10% signal and card loss | Learned routing with pooled reader | Silent policy optimized for same reader | Unsupported delivery attempts, learned |
|---|---:|---:|---:|
| Venezuela, full or incomplete | 38.68575 | 37.535 | 55% |
| DPRK, full or incomplete | 59.39725 | 58.535 | 52.5% |
| DPRK, reordered or reversed | 55.795 | 56.0 | 0% |

Under skewed inventories at the same loss rate, the DPRK full-or-incomplete condition falls to 62.40322 against 62.89760 for the matched silent control. Under uniform inventories with reordered or reversed DPRK passages, neither learned routing nor the optimal silent policy supplies both cards through this reader. The verifier protects record scoring from unsupported passages, but a score increase can coexist with frequent failed attempts. [Classification errors and paired routing results](../evidence/duplicate-card-routes/semantic/score.json)

#### Verify known passages before consulting the policy

Replace the replay’s ground-truth receipt check with a SHA-256 registry keyed by docket and passage bytes. An entry supplies the canonical evidence role independently of the model’s proposed label. Check the role again at delivery. The strict registry accepts four original excerpts. A second registry also accepts the four reviewed order variants. On 16 passages it accepts the eight complete versions and rejects the eight incomplete or reversed versions. The tests also reject swapped role claims, foreign-docket receipts and unreviewed suffixes. Both desks can know the registry without learning what the other holds.

At 10% losses and uniform inventories, the reviewed intake recovers the typed result on both passage sets. On reordered DPRK it scores 60.422375 with learned routing and 59.24375 with silent routing, with zero unsupported delivery attempts. Exact-only intake discards the reordered passages and both policies score the empty-record 56. The registry is a bounded provenance mechanism for known source bundles. It cannot certify an unseen paraphrase. All end-to-end points still come from previously scored writer outputs for canonical receipts. [Executable attestation, checks and replay](../evidence/duplicate-card-routes/semantic/attestation.json)

```sh
python -B duplicate_card_semantic_review.py ../evidence/duplicate-card-routes/semantic | cmp - ../evidence/duplicate-card-routes/semantic/score.json
python -B duplicate_card_attestation.py | cmp - ../evidence/duplicate-card-routes/semantic/attestation.json
```

## Reproduction

From this directory run the following commands. The first checks 40 prompt-derived keys and reports the stored source digests. The remaining commands generate the development prompts, separate acceptable answers and baseline checks without model inference.

```sh
python3 -B check.py | cmp - replay.json
python3 -B contrasts.py tasks
python3 -B contrasts.py key
python3 -B contrasts.py checks
```

## Isolate the two DPRK source-reading failures

The two clause questions probe national versus chair capacity and the remaining-time qualification to China’s abstention. The passage is identical to the archived full-requirement input. Each question is asked about every anonymous excerpt in both label orders, for 32 one-token probes across eight passages. The first-order reader accepts a unique yes. The agreement reader requires yes in both orders for one clause and no in both for the other. A non-target detail such as the Panel’s closure stays fixed in this fixture and receives no separate test.

The scoring script checks the prompt text, model path, run-input hashes and action checksum. Its replay keeps the fitted routing table and archived chair outputs fixed, and computes optimal silence for each reader under the same packet budget and evidence. NumPy is sufficient for this step. Run from this directory.

```bash
python duplicate_card_atomic_review.py ../evidence/duplicate-card-routes/atomic-dprk
```

The completed clause run scores 6/8, the same as agreement across orders on the full-requirement prompts. Its two errors are the complete China passages. It accepts reordered Japan and rejects the incomplete China account, addressing the two failures that motivated the check. The conservative filter passes no China cards and sends no unsupported cards in replay. At uniform inventories and 10% loss, the fitted policy gets 55.80 on either stress fixture and reader-matched silence gets 56.00. Both routes reach the public-only score before charges. The full-requirement probe used 24 model calls and 4,737 input tokens on these passages. The two-clause probe used 32 and 5,244, respectively. [Clause results](../evidence/duplicate-card-routes/atomic-dprk/score.json)

### Distinguish a stated reason from a separate statement

The follow-up offers three meanings for the consultation phrase. The excerpt can give remaining time as a reason, give the absence of remaining time as a reason, or leave consultation time out of the reasons. Two synthetic controls add the otherwise qualifying words to the incomplete passage. One attributes them to Japan. The other attributes them to China on a different agenda item. Keep these controls out of the historical packet archive. Require agreement across all three answer orders before the composite reader accepts the China role. The Japan role uses the two existing votes on national capacity. A passage with competing roles is held. Replay scores are for the original eight variants. The added controls test the China qualifier alone.

All 30 probes completed. Of the 10 passages, eight get a unanimous and correct qualification. All three orders classify each new scope control correctly. For original-order China, the complete passage returns remaining time, omitted reason, then remaining time. The incomplete passage returns no remaining time, omitted reason, then omitted reason. Both are withheld under strict agreement. The composite gets 7/8 routing roles correct, with one missed complete passage and zero unsupported acceptances. It consumes 40 probes and 6,647 input tokens on the original eight passages, including the reused Japan checks.

| Uniform inventories, 10% loss | Fitted route | Optimal silence with same reader | Unsupported attempt probability |
| --- | ---: | ---: | ---: |
| Strict composite, complete or missing | 55.80000 | 56.00000 | 0% |
| Strict composite, reordered or reversed | 60.42238 | 59.24375 | 0% |

With skewed inventories and 25% loss, even the ideal reader leaves the fitted route 0.07538 points below reader-matched silence. As a posthoc sensitivity check, two-of-three voting produces the authored qualifier on all 10 inputs and the right role on all eight original passages. It matches ideal routing in all 12 prior, loss and source-style combinations. Both scope controls test one fixture and leave the other details fixed. These are adaptive development checks with frozen Qwen3.5-4B, no optimizer updates, and no new chair generation. [Exact replay results](../evidence/duplicate-card-routes/qualifier-dprk/score.json)

```bash
python duplicate_card_qualifier_review.py ../evidence/duplicate-card-routes/qualifier-dprk
```

## Compare the final record on the 2024 Western Sahara renewal

The protocol uses retrospective evidence from the October 31 meeting and the adopted instrument. It requires a faithful record of the three votes, Algeria's reservation, Switzerland's split amendment votes and the boundary of the renewed mandate. The archive audit checks the exact UNBench documents and UNSC-Bench adopted row 237. UNBench contributes the three drafts. This family has no main-draft row in its Task 2 author vote test. The archived UNSC-Bench row codes Algeria A, while its own note and the meeting record say Algeria did not participate. Treat that as a label discrepancy when running native vote evaluation. [Dossier and rubric](source-record-minurso.json) · [Source audit](source-record-minurso-sources.json) · [Meeting record](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9771&t=pdf) · [Adopted resolution](https://documents.un.org/api/symbol/access?l=en&s=S%2FRES%2F2756%282024%29&t=pdf)

The pooled analyst runs two draft passes, two review passes and one synthesis with pooled evidence throughout. Independent and interacting agents get one role each, share identical openings and vary only peer delivery during revision. All three arms share the same source menu and task for synthesis, five calls and a 620-token output ceiling. The interactive arm consumes extra context for the peer openings. Treat the final record score and material guard as separate endpoints. The final deck contains only opaque IDs, source blocks, candidate text and the frozen task and rubric. A separate mechanism packet provides delivered spans, recipient openings, peer-visible revisions and matched independent revisions. The five authored anchors check the scoring contract. They are neither judge-model results nor independent review. [Runnable comparison](source_record_minurso.py) · [Packet and transcript replay](source_record_minurso_review.py) · [Judge instructions](../../judge/instructions.md)

The first model comparison completed 13 calls and every call hit its token ceiling. With unblinded same-assistant annotation, the pooled analyst got 14/70 with a failed guard, independent drafts got 28/70 with an uncertain guard, and interactive drafts got 14/70 with a clear guard. The pooled analyst misattributed Algeria's complaint about the penholder to the Council. The independent record alone stated the mandate limits, and the interactive record alone preserved the Swiss split and reason. Each record overstated Algeria's second amendment, which proposed considering expansion. The Swiss role fixed an instrument substitution in both its independent and peer-visible revisions. Neither sampled peer opportunity supplies traceable peer-specific credit. Inputs per arm were 3,562, 2,847 and 3,073 tokens respectively, and all used the entire 620-output-token budget. [Exact records and diagnoses](../evidence/source-record-minurso/score.json) · [Evidence spans](../evidence/source-record-minurso/review.json) · [Judge packets](../evidence/source-record-minurso/judge-packets.json)

The numbered blocks are audited paraphrases of the primary materials. The judge cites exact spans from the supplied blocks. Source entailment and span containment are distinct checks. This case was new to the present evaluation. Public-document exposure during pretraining is unknown.

Replay from this directory with the local Qwen tokenizer and the checked evidence files.

```bash
python source_record_minurso.py check
python source_record_minurso_review.py deck ../evidence/source-record-minurso
python source_record_minurso_review.py score ../evidence/source-record-minurso --review ../evidence/source-record-minurso/review.json
python source_record_minurso_compact_deck.py ../evidence/source-record-minurso-compact
python source_record_minurso_review.py score ../evidence/source-record-minurso-compact --review ../evidence/source-record-minurso-compact/review.json
```

The chair-only completion control replaces the final system instruction with a five-sentence drafting contract, a 115-word target and a request to omit titles and prefatory prose. It retains the 155-word scoring rule, the 250-token generation ceiling, the same user prompt, the exact archived revisions and their delivery history, and the same frozen model. Interpret it as a joint change to style, ordering and concision instructions. [Completion control](source_record_minurso_compact.py)

The compact chair ran to completion in all three arms, at 87, 96 and 97 words for pooled, independent and interactive respectively. Every arm scored 0/70 under the frozen all-or-nothing criteria. All three omit the main draft symbol, the named penholder in Algeria's complaint, Switzerland's first amendment vote and explicit facilitation of OHCHR visits. They preserve partial information across all five criteria. Independent and interactive records clear the material guard. The pooled record changes Algeria's correct non-participation in the first run to an invented abstention. The two team records retain the second Swiss vote and continuity rationale, which the interactive baseline previously covered alongside the first Swiss vote. The compact run fixes termination while losing details that were present before. [Exact records](../evidence/source-record-minurso-compact/final-records.json) · [Unblinded evidence-span review](../evidence/source-record-minurso-compact/review.json) · [Replay scores](../evidence/source-record-minurso-compact/score.json)

For a prospective rubric revision, give independently identifiable claims their own weighted rows within the existing 70 points. Retain a complete-record gate. The recommendation follows from the observed floor effect and the final scores above use the original frozen rubric. A completed partial record needs to distinguish a missing identifier, a wrong vote and the replacement of a hypothetical action with an adopted one. Keep a visible exact quote for each scored part and preserve the guard and independent review requirements.

## Bind the role evidence to the statement and refit the routing policy

A small phrase matcher proposes verbatim role clauses, office labels and distractors from nine DPRK passages. Qwen chooses a span or no explicit capacity in every possible menu rotation. The scorer verifies offsets and requires unanimous selection. In an archived memo the model selects “speaking as Japan's representative” twice and no explicit capacity once. It consistently reads the capacity clause in both complete source orders and withholds both decoys that qualify a different speaker or agenda item. A role phrase matcher alone accepts both decoys. The learned router with the model selector attempts no unsupported delivery in these two scenarios, compared with 55% of episodes for the matcher at uniform inventories and 10% loss. The replay rejects an unsupported receipt using the authored key and still charges the attempt. [Probe and exact spans](../../judge/dprk_capacity_spans.py) · [Routing replay](../evidence/dprk-capacity-spans/route-score.json)

Fit one local policy across the two observed standard reader regimes at uniform availability and 10% link loss. Exhaustively enumerate the legal announcements and conditional deliveries. Maximize the worse gain over same-reader silence, then maximize average gain among equally robust fits. The fitting criterion sees whether a receipt was warranted. During evaluation the policy sees only its local interpreted inventory and the received bit. No model weights or downstream writer outputs change.

| Strict China reader | Original learned policy | Refit | Optimal same-reader silence |
| --- | ---: | ---: | ---: |
| Original-order complete or missing, uniform, 10% loss | 55.800 | 56.000 | 56.000 |
| Reordered or reversed, uniform, 10% loss | 60.422 | 59.709 | 59.244 |
| Reordered or reversed, skewed, 25% loss | 60.683 | 59.943 | 60.759 |

In two source conditions the scope decoys produce the same observed masks as the reordered training condition. Their unchanged routing result adds evidence about reading those phrases. The shifted prior and loss are distinct policy conditions, and the refit loses 0.816 points against silence there. The trade-off is remaining silent when the reader cannot see China, while paying for that restraint when transport is unreliable. This is an exact development replay on existing final-record scores. [Router fit and all shifted checks](../evidence/dprk-capacity-spans/router-fit.json)

```bash
python dprk_capacity_route_review.py ../evidence/dprk-capacity-spans
python dprk_capacity_router_fit.py ../evidence/dprk-capacity-spans
```

## Fit evidence routing against fresh Western Sahara records

Freeze the Western Sahara source packets before generation. The public brief has 42 available points. Algeria and Switzerland each hold one 14-point card, with overlapping availability across the simulated desks. Generate a single final record for each of the four possible receipt masks under an identical 270-token and 155-word ceiling. A chair sees only the delivered packet. The exact-span review allows national claims only when the corresponding card arrived. Route rewards are evaluated on raw points, points on completed guard-clear records and the authored proof ceiling. [Writer and packet checks](minurso_receipt_writer.py) · [Exact-span review](../evidence/minurso-receipt-writer/annotations.json)

| Received evidence | Raw points | Guarded reward | Receipt ceiling |
| --- | ---: | ---: | ---: |
| Public only | 27 | 0 | 42 |
| Algeria | 33 | 33 | 56 |
| Switzerland | 41 | 41 | 56 |
| Both | 55 | 55 | 70 |

All records finished and had the requested headings. The public-only record incorrectly states that the adopted text excludes OHCHR access language. The other records preserve the mandate limits and clear the critical guard. All four omit the main draft symbol, the precise text proposed by each amendment and the request to facilitate OHCHR visits. The final record with both cards preserves both national positions. [Fresh outputs and guarded scores](../evidence/minurso-receipt-writer/score.json)

The previously fitted buffered policy yields 39.188 net points against optimal same-writer silence at 37.629 for uniform inventories and 10% independent signal and card losses. With raw scores it yields 42.176 against 40.481. The positive comparison survives removing the zero penalty for the public-only error. At skewed inventories and 25% loss, the guarded comparison reverses by 0.144 points. A new seeded team-reward search fitted on a third, lossless inventory distribution reaches its exact training ceiling at 46.558, versus 43.043 for exact same-writer silence. It ties the transferred policy on aggregate for all six evaluations. The tables differ in which seat announces and the individual returns are not all identical. The desk observations are typed and the writer is frozen. [Transferred controls](../evidence/minurso-receipt-writer/score.json) · [Fit and six held-condition checks](../evidence/minurso-receipt-writer/learned.json)

### Change the writer while holding the routing experiment fixed

A second writer prompt supplies explicit slots for the main draft identifier, each amendment's proposal and outcome, the national arguments and mandate limits. It uses the same source packets, decoding and cap. All four records again finish, and all recover the draft symbol. Each drops the explicit failure of both amendments. The public-only record also cites three placeholders outside its evidence packet. The Algeria-only record says its national account is absent even though both blocks arrived. The Switzerland-only record describes Algeria as absent, which leaves voting non-participation ambiguous. The both-card record omits the precise reason given by Algeria and scores 33 instead of 55. These findings are unblinded exact-span annotations. [Follow-up prompt](minurso_receipt_fields.py) · [Raw outputs and score](../evidence/minurso-receipt-fields/score.json)

| Uniform inventories and 10% loss | Original writer | Required-slot writer |
| --- | ---: | ---: |
| Both cards, raw points | 55 | 33 |
| Frozen router, guarded net | 39.188 | 10.867 |
| Optimal silence, guarded net | 37.629 | 8.053 |
| Frozen router, raw net | 42.176 | 31.097 |
| Optimal silence, raw net | 40.481 | 31.885 |

The guarded gain increases because only the both-card record meets the follow-up release rule. The raw comparison reverses sign and the protected score falls sharply in both arms. This makes raw quality, release eligibility and the absolute score essential checks on a learned routing reward. The follow-up results reuse the pre-existing transferred policy. Input costs vary with packet length. The replay charges the fixed signal and card costs and retains exact writer token counts. It evaluates simulated typed receipts and archived results from eight fresh writer calls, with no independent annotation or language-model weight updates.

```bash
python minurso_receipt_writer.py replay ../evidence/minurso-receipt-writer
python minurso_receipt_scores.py ../evidence/minurso-receipt-writer ../evidence/minurso-receipt-writer/annotations.json
python minurso_receipt_fit.py ../evidence/minurso-receipt-writer/score.json
python minurso_receipt_fields.py replay ../evidence/minurso-receipt-fields
python minurso_receipt_fields.py score ../evidence/minurso-receipt-fields --annotations ../evidence/minurso-receipt-fields/annotations.json
```

## Test natural-language peer revision without private-source access at the chair

Use the same Western Sahara dossier, but give each national card only to its delegate. Both arms share the same two opening drafts. Each opening can ask a question, then an independent or peer-visible revision goes to the chair. The chair sees only the public docket and the two natural-language revisions. Arm output ceilings are equal at 782 tokens. A replay checks every visible history and the exact input and output token traces. Score historical details, actual support in a delivered revision, guard status, citation eligibility and process separately. [Episode builder](minurso_deliberation.py) · [Review and attribution rules](minurso_deliberation_review.py)

The first eight-call test produces 35/70 for independent revisions and 24/70 for peer-visible revisions. All credited national claims have an exact visible witness. Both chairs repeat the Algerian delegate's wrong abstention after correctly recording non-participation in their own adoption section. The independent chair cites CH-A and CH-B, which were unavailable to it. The peer chair stops at its token cap. The two draft questions ask about an unsupported historical comparison or address South Africa, a country with no role in this exchange. Neither establishes a supported change attributable to a peer. The exchange uses 2,848 input and 558 output tokens, versus 2,683 and 539 for independent revision. These are unblinded same-assistant judgments on one example. [Archived dialogue and final points](../evidence/minurso-deliberation/score.json) · [Exact transcript review](../evidence/minurso-deliberation/review.json)

The follow-up changes only the delegate instructions and their explicit counterpart metadata. It narrows questions to this meeting and gives the public roll call precedence on formal votes. The two source bundles, visibility graph, caps and chair prompt stay fixed. Both questions now address the correct counterpart. Switzerland independently repairs its wrong amendment identifiers in both conditions. Algeria keeps calling non-participation an abstention. Both chairs reproduce the contradictory vote, so neither final record clears the guard.

| Named-counterpart follow-up | Independent revisions | Peer-visible revisions |
| --- | ---: | ---: |
| Verified and historically correct points /70 | 37 | 33 |
| Upper bound allowing ambiguous interpretations | 37 | 43 |
| Input / output tokens | 2,793 / 544 | 2,979 / 593 |
| Chair finished | Yes | No |
| Material guard | Failed | Failed |

The upper range for peer revision credits ambiguous implications about Algeria's monitoring position and the reason for Switzerland's second amendment vote. The Algerian peer revision responds to Switzerland but shifts into an unverified current proposal. Switzerland's reply gives the rationale for a different vote from the one asked about. No supported peer-specific contribution reaches the scored record. Across both protocols the study contains 16 model calls and no weight updates. [Named protocol](minurso_deliberation_named.py) · [Exact supported and ambiguous spans](../evidence/minurso-deliberation-named/review.json) · [Results](../evidence/minurso-deliberation-named/score.json)

```bash
python minurso_deliberation.py replay ../evidence/minurso-deliberation
python minurso_deliberation_review.py ../evidence/minurso-deliberation ../evidence/minurso-deliberation/review.json
python minurso_deliberation_named.py replay ../evidence/minurso-deliberation-named
python minurso_deliberation_named.py score ../evidence/minurso-deliberation-named --annotations ../evidence/minurso-deliberation-named/review.json
```

## Reconcile public facts and recover missing national evidence

A narrow matcher removes the sentence contradicting Algeria's official vote from each of the four archived national drafts. Five controls leave a correct vote, amendment scope, other delegation, question and other meeting unchanged. The matched chair reruns regenerate the Algerian error in three of four cases. The fourth corrects Algeria but still gives the wrong first Swiss amendment vote. Every free-text record fails its guard. [Exact deletions and matched scores](../evidence/minurso-vote-reconciliation/score.json)

A deterministic assembly control uses the public section from the authored source reference and extracts only specific national claims with an exact draft witness. This gives 54/70 and 48/70 on the original independent and peer inputs, and 56/70 on both named inputs. The public section accounts for 42 points by construction. Switzerland's named drafts provide its 14 points, while Algeria's remaining draft evidence falls short. The fixed-phrase grammar is case-specific and does not certify arbitrary diplomatic language. [Compiled records and six software controls](../evidence/minurso-vote-reconciliation/protected-records.json)

Two source-owner calls try to recover the missing statements by copying exact quotes. Both insert new wording and detach the penholder's complaint from the act of non-participation. The evidence check admits neither field and both records remain at 56/70. Save the runner bytes from launch for checksum verification. The active scorer records the actual recovery span and links it to the recovery turn. [Free-text extraction and replay](../evidence/minurso-requery/score.json)

A second recovery interface lets the model select between exact source spans and a no-answer option. The two questions use six one-token probes, with each meaning in all three answer positions. The model unanimously selects the correct monitoring stance and the explanation that explicitly links the penholder's conduct to non-participation. A deterministic tool returns those exact spans. Both final records pass the fixture's 70-point contract in 100 words. Their public text is authored, their national span menus are case-specific, and the same validated reply serves both arms. This run measures source-owner recovery, with no verified peer benefit or trained language weights. [Selection and full records](../evidence/minurso-requery-select/score.json)

```bash
python minurso_vote_reconciliation.py replay ../evidence/minurso-vote-reconciliation
python minurso_vote_reconciliation_review.py ../evidence/minurso-vote-reconciliation ../evidence/minurso-vote-reconciliation/annotations.json
python minurso_protected_record.py ../evidence/minurso-vote-reconciliation/score.json
python minurso_requery.py score ../evidence/minurso-requery --verify-tokens
python minurso_requery_select.py report ../evidence/minurso-requery-select
```

## Learn explicit requests across three historical dossiers

Both desks can privately hold any of the three evidence fields. The first desk chooses one request and one submission without seeing the second desk's inventory. The second chooses its submission after the request or erasure. Use one exact expected team objective and optimize both local policy tables with Adam. The trained objective sees Western Sahara and DPRK inventories and public rubric weights. The policy receives field IDs and its local observation. Mali's source fields, reward profile and three simulated priors are held out from the fit. A record in this experiment is a 28-point evidence addendum, with at most two deliveries and one source dependency bonus. It is not the full historical chair memo. [Field definitions and source locks](source_request_cases.py) · [Optimizer and comparator](source_request_policy.py)

| Mali typed test, 10% loss | Learned | Optimized independent | Scripted request | Learned with request erased |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 14.149 | 13.669 | 13.720 | 13.249 |
| Asymmetric | 15.262 | 15.833 | 15.359 | 13.460 |
| Correlated duplicates | 12.540 | 12.214 | 10.790 | 12.135 |

One seed and 280 actual joint expected-return updates increase the training objective from 7.632 to 13.741. Under uniform Mali inventories, enumeration of all 746,496 requester maps with their exact best replies gives a 14.529 net ceiling at 10% link loss. The score replays all 64 possible inventory states with independent message loss. The learned values and exact-silence comparisons are expectation measurements under simulated priors, not observed real-world prevalence. [Fit with exact bound](../evidence/source-request-policy.json) · [Execution record](../evidence/source-request-policy.launch.json)

Feeding the routing policy the observed frozen Qwen reader changes the result. The reader identifies one of three positive originals and two of three positive reordered passages consistently. It admits no incomplete or reversed passage across all orders. It never admits the Russia field in either complete version, so at 10% loss the learned policy pays a 0.05-per-world request fee without improving verified coverage. The comparison reoptimizes silence for that same decoder. It charges unsupported attempts and uses authored ground truth to reject wrong-role receipts. [Reader and same-decoder comparisons](../evidence/mali-source-request-reader/score.json)

A separate qualifier probe presents exact candidate spans for Russia's stated extension horizon. Qwen selects the final-extension phrase in all three answer orders on both complete versions, leaves the omitted case unsupported and cannot come to agreement on the reversal. The qualifier accepts a positive field only with the Panel dissolution phrase and the docket-specific role framing. This repair is designed after seeing the direct-reader failure. It uses known text patterns, and the positive or counterfactual horizon phrase is placed in the menu mechanically.

The reordered fixture now exposes all three correct role types. It reproduces the 0.480-point learned gain at the uniform prior and 10% loss, with no unsupported attempts. The original-order fixture still loses 0.248 points to optimal independent submissions because the co-penholder field remains withheld. The asymmetric loss also persists. The artifact includes a concrete retained-evidence witness. If the first desk holds only the co-penholder account and the second holds it plus the Russia account, the learned query changes that reply from a duplicate to the Russia account. With links intact the addendum rises from 12 to 25 points when comparing the same policy with and without the query. This is a field-level communication effect with source-provenance text, prior fit weights unchanged, and no new open-ended final record. [Scoped probe and reward replay](../evidence/mali-request-term/score.json)

```bash
python source_request_policy.py --exact
python mali_source_request_replay.py ../evidence/mali-source-request-reader ../evidence/source-request-policy.json
python mali_request_term.py report ../evidence/mali-request-term --old ../evidence/mali-source-request-reader --policy ../evidence/source-request-policy.json
```

## Test the learned Mali requests against fresh full records

Use the previous Mali reader and learned policy with a new frozen Qwen3.5-4B chair. Generate the seven reachable source packets for the two-delivery channel and the full-information solo packet. Hold actual writer outputs fixed across policies. Grade each under the unchanged 70-point Mali rubric and replay all inventory and loss combinations. Track France's objection as a separate source retention metric. The bounded request reward covers that objection explicitly. The existing full-record rubric does not assign it a separate weight. [Writer](mali_request_writer.py) · [Full-record replay](mali_request_writer_review.py)

The initial input mistakenly requests the meeting date without delivering it. Two of eight records guess a date, one prints a placeholder and the other five omit it. Preserve the error and its raw and release scores. The corrected condition adds the verified 30 August 2023 docket, without any other prompt, decoding or packet change. All eight corrected records state the date and finish under the cap. Their raw scores in receipt order are 42, 42, 42, 35, 49, 35, 42 and 49. Only the full-information receipt passes the material and citation release gate. The other records use numeric citations outside the packet, leave vote ownership or a statement's speaker unresolved, attribute France's objection to China, or treat Japan's negative vote as a veto. The full-information record clears the guard and scores 49/70. It still lacks the precise failure mechanism and an explicit overlap and disagreement synthesis. [Initial scores](../evidence/mali-request-writer/score.json) · [Dated prompt and records](../evidence/mali-request-writer-dated/score.json) · [Exact assessments](../evidence/mali-request-writer-dated/annotations.json)

| Uniform Mali inventories, 10% loss | Frozen request policy | Optimized independence | Exact optional-query upper bound |
| --- | ---: | ---: | ---: |
| Prior evidence addendum | 14.149 | 13.669 | 14.529 |
| Dated chair, raw full-record net | 39.735 | 46.683 | 46.683 |
| Dated chair, release net | −0.375 | 0.000 | 0.000 |

The dated exact bounds enumerate all 746,496 requester maps with their best replies on typed receipts. The repaired prose reader generates those same receipt views in the reordered fixture. With these actual writer outputs, the best raw endpoint policy uses no requests. The best release endpoint cannot produce a releasable record under two deliveries. Provisionally accepting the ambiguous judgments, while excluding clear errors and unavailable citations, still leaves learned requests below independence by 12.119 net points under the uniform reordered condition. [Exact bounds](../evidence/mali-request-writer-dated/score.json) · [Guard sensitivity and intact-link counterfactuals](../evidence/mali-request-writer-dated/sensitivity.json)

In the intact-link witness, requesting Russia's proof raises the evidence addendum from 12 to 25 but lowers full-text quality from 42 to 35. Across nine typed inventory pairs in which the request changes the final receipt, two raw scores improve, five decline and two tie. This is an adaptive, unblinded assessment of one frozen writer on one docket held out from policy training. The replay admits attested source IDs and uses canonical source paragraphs, so it measures routing and writing together under those conditions. It does not test unconstrained peer negotiation or an independent judge.

```bash
python mali_request_writer.py replay ../evidence/mali-request-writer
python mali_request_writer_dated.py replay ../evidence/mali-request-writer-dated
python mali_request_writer_dated.py score ../evidence/mali-request-writer-dated --annotations ../evidence/mali-request-writer-dated/annotations.json --policy ../evidence/source-request-policy.json --joint-reader ../evidence/mali-source-request-reader/score.json --scoped-reader ../evidence/mali-request-term/score.json --exact
python mali_request_writer_sensitivity.py ../evidence/mali-request-writer-dated/score.json ../evidence/source-request-policy.json ../evidence/mali-source-request-reader/score.json ../evidence/mali-request-term/score.json
```

## Fix the official section and write national components separately

The frozen Qwen3.5-4B writes one sentence in each of three isolated calls. The assembler uses the same author-verified public section for every receipt, worth 56 points of the unchanged 70-point rubric. Receipt zero needs no generated sentence. The two-delivery channel can now reach a complete record by delivering the French–UAE and Russian rationale fields. France's objection about the separate proposal is tracked separately. These receipts reuse the same three outputs, with no further writer call. [Writer](mali_protected_writer.py) · [Exact output and review](../evidence/mali-protected-writer/)

| Uniform inventories, typed or scoped reordered input, 10% loss | Learned | Optimized independent | Request erased | Exact optional ceiling |
| --- | ---: | ---: | ---: | ---: |
| Strict model-written citations, net points | 59.429 | 60.683 | 59.641 | 60.683 |
| Trusted citation envelope, net points | 63.809 | 63.732 | 63.224 | 64.039 |
| Trusted citations, full-record rate | 29.62% | 25.31% | — | — |

Same-assistant unblinded review found all three sentences substantially grounded. Strict mode drops the Russia sentence for citing `[1]`. Envelope mode assigns the citation from the verified ID of the sole block in each call, leaving the sentence body byte-identical. In the intact-link witness, the request changes the delivered receipt mask from 1 to 3 and raises the assembled record from 63 to 70 points. On reordered inputs, the learned policy trails optimized independence by 0.382 under asymmetric inventories and 0.050 under correlated duplicates. Exact optional-query headroom above independence is 0.306, 0.143 and 0.131 points under the three typed priors, respectively. Scoped original-order input continues to lose the co-penholder field, and the learned policy trails independence under each prior. Scores and release gates are conditional on the verified source envelopes and the three hand-reviewed sentences. The archived generation used CPU and made zero optimizer updates. [Input and token record](../evidence/mali-protected-writer/transcript.jsonl) · [Strict citations](../evidence/mali-protected-writer/score-strict-citations.json) · [Trusted citations](../evidence/mali-protected-writer/score-trusted-citations.json)

```bash
python mali_protected_writer.py check
python mali_protected_writer.py replay ../evidence/mali-protected-writer
OPENBLAS_NUM_THREADS=1 python mali_protected_writer_review.py ../evidence/mali-protected-writer --exact
OPENBLAS_NUM_THREADS=1 python mali_protected_writer_review.py ../evidence/mali-protected-writer --exact --trusted-citations
```

The exact policy fitted under uniform typed inventories also attains the ceiling under both other priors. A subsequent CPU run reuses the original decentralized table optimizer and seed for 280 updates. Its training reward is the national-component score of the actual composed record. It trains on the uniform typed prior and tests on all three priors. It beats optimized independent delivery in all three and stays within 0.024 points of each exact optional-query ceiling. Erasing the fitted question with the same fee costs 0.319, 0.148 and 0.144 net points in prior order. Qwen's weights and sentence bank remain frozen. This is calibration within one source family. [Reward vector, policies, and gradient trace](../evidence/mali-protected-writer/policy-fit.json)

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python mali_protected_policy_fit.py ../evidence/mali-protected-writer/score-trusted-citations.json
```

## Transfer the Mali final-record router to Myanmar

The 21 December 2022 docket contributes 15 UNBench author-test vote rows. The archived pinned UNSC-Bench scan has no matching Myanmar row. The public assembly contributes 42 points. Two national statements and a separate procedural role statement can each earn seven points. The controlled bridge earns seven more when both national statements support regional context and the fixed roll call preserves the vote difference. The raw national clauses are Qwen3.5-4B outputs, each scoped to one primary-source summary. [Docket and dataset linkage](../../crossbench/myanmar/references.json) · [Frozen causal split](myanmar_protected_writer.py)

The frozen Mali fit loses against exact independent delivery across all six field bindings and all three typed inventory priors. Its best uniform score is 50.026 net, versus 50.214 for independence, 50.945 for exact optional queries and 51.361 for the centralized-inventory controller. All-source assembly earns 63/70 because the model omits the UK sponsorship. The two-delivery channel can reach at most 56/70 with the actual component bank. Same-assistant annotations accepted the India capacity change because the sentence explicitly resumes presidential duties following the national explanation. [Generated components, evidence verdicts and exact replay](../evidence/myanmar-protected-transfer/score.json) · [Anonymous evaluator packets](../evidence/myanmar-protected-transfer/judge-packets.jsonl)

The rubric-aware fit uses the intended points for each receipt and never consumes actual writer ratings during optimization. One 280-update CPU fit and a public-rubric exact planner both trail the hindsight independence control on the original bank. The optimizer can assign a question helpful positive value, yet misallocate a scarce slot when the writer omits a required part. [Public-rubric policy and gradient trace](../evidence/myanmar-public-rubric-fit/fit.json)

```bash
python myanmar_protected_writer.py replay
OPENBLAS_NUM_THREADS=1 python myanmar_protected_transfer.py --exact
python myanmar_protected_transfer.py --judge-packets
```

The sponsorship probe regenerates only the source-local UK sentence. It names the UK as submitter and keeps the consultative and substantive points. Both model calls and their exact token sequences are preserved. The matched receipts that do not see the UK card are identical before and after. The all-source assembly now scores 70/70 under the same unblinded assessor. The two-slot ceiling is 63 because obtaining the linked UK–India comparison leaves no slot for the procedural statement.

| Revised sentence bank, net points | Rubric-trained | Request erased | Optimized independence | Exact public-rubric planner |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 53.955 | 52.998 | 53.118 | 54.047 |
| Asymmetric | 55.204 | 54.832 | 55.033 | 55.255 |
| Correlated duplicates | 52.805 | 52.024 | 52.485 | 52.853 |

The two task-aware routing policies were already archived when the revised UK sentence was generated. The trained policy beats the simple priority script across all tested bindings and priors on the revised record bank. The exact planner matches the retrospective optional-query ceiling. The original Mali policy still trails independence across all 18 comparisons. This design measures evidence routing under a typed delivery protocol, with a known public rubric and a writer prompt adapted on Myanmar. It leaves independent judge calibration, end-to-end solo and team generation, and cross-family performance of the revised pipeline open. [Matched generation and score](../evidence/myanmar-sponsorship-probe/score.json) · [Official meeting record](https://documents.un.org/doc/undoc/pro/n22/765/91/pdf/n2276591.pdf)

```bash
python myanmar_sponsorship_probe.py replay
OPENBLAS_NUM_THREADS=1 python myanmar_sponsorship_review.py
```

## Blind end-to-end outer-space comparison with a pooled solo analyst

The 2024 outer-space docket already has benchmark-linked source summaries and an authored authority calibration pair. It was excluded from the Mali and Myanmar router fits and exposed in earlier project work. Fit two decentralized policies for 280 updates on the public rubric, without output ratings. Both desks together hold China, Japan and May evidence. Two worked worlds were selected before generation using the intended rubric and frozen policies. In the first, the learned query asks for China and turns a duplicate Japan note into both national accounts. In the second, independent already delivers both. The rubric-only expected returns over the uniform typed distribution are 20.734 for the fitted policies, 18.501 for exact independence, and 20.833 for the optional-query ceiling. These planning scores exclude the common public text and do not use generated answers. [Fit and worked inventories](../evidence/space-final-routing-policy.json)

The teams get two 56-token notes and a 160-token chair call. The pooled solo gets the full source union and one 272-token call. All use a 125-word record request. The opportunity team uses 644 input tokens and 214 generated tokens, the independent team uses 616 and 214, and solo uses 449 and 215. Teams get the same generation ceiling and different delivered evidence. Solo has broader direct evidence and fewer calls. Partial note text and the fitted typed question are kept in the transcript. [Matched prompts and frozen transcripts](../evidence/space-final-routing-transfer/)

Unblinded exact-span review gives both team arms 14/70 on the opportunity and control. All team chairs hit the cap and misdate the April draft vote. In the opportunity, the learned query adds the supported China argument but the resulting record loses the Japan vote criterion. The pooled solo earns 28/70 with a clear guard and finishes, but uses 131 words. Identical control receipts reproduce byte-identical chair outputs. Treat raw scores, authority guards, completion, word cap and peer-claim retention as distinct measurements. [Source-grounded assessor record](../evidence/space-final-routing-transfer/manual-review.json)

```bash
python space_transfer_episode.py fit --policy ../evidence/space-final-routing-policy.json
python space_transfer_judge.py inspect
python space_transfer_judge.py assess
python space_transfer_judge.py replay-tokens
```

The final judge sees the full source summaries and an opaque content ID. Identical candidate texts share one judgment. There are five requests after deduplication, including the two previously authored anchors. The full judge yields zero usable outputs. Four hit the cap, and the only completed output uses strings where numeric indices were required. Its provisional grades also miss criteria present in the answer. The blinded run uses the same base checkpoint as the writer, and the separate manual scores are unblinded. [Raw and validated judgment audit](../evidence/space-final-routing-blind-judge/assessment.json)

The atomic follow-up supplies explicit dates, vote stages and Council authority in a four-entry ledger verified against the already archived outer-space sources. Its sole output is a guard status with the offending sentence and ledger entry when applicable. It is a scope and interface intervention, so keep its results separate from the ten-unit scores. [Atomic implementation](space_atomic_guard.py) · [Official records and benchmark join](../../crossbench/space/references.json)

All five compact guard cases produce valid syntax. The model cites the exact false authorization on the negative anchor and clears the faithful reference and the pooled solo manuscript. It flags the interactive date error and misses the same verbatim sentence in the independent opportunity record. In both records, sentence 5 dates S/2024/302 to 20 May. The judgment is inconsistent despite matched evidence and contradiction wording. Inspect this context sensitivity before treating a model guard as a source of reward. [Compact judgments](../evidence/space-final-routing-atomic-guard/assessment.json) · [Records](../evidence/space-final-routing-transfer/final-records.json)

```bash
python space_atomic_guard.py assess
python space_atomic_guard.py replay-tokens
```

A mechanical screen binds a sentence-leading day and month to a single draft ID, then checks that pair against the verified ledger. It catches the two distinct incorrect dated sentences and finds no conflict in the two explicit dates it checks in the solo record. It has no coverage on the authority anchors, and every report lists which statements were examined. [Date screen](space_vote_dates.py) · [Coverage and conflict audit](../evidence/space-final-routing-atomic-guard/date-check.json)

## Replay the protected outer-space writer across all evidence receipts

The archived Japan and China notes stay intact. A single new May note and ten 128-token bodies populate all nonempty team receipt masks and three raw-source solo controls. Body caps are identical. Team notes and the typed request add computation beyond the final writer. The fixed April paragraph earns 21 of 70 points by construction. Vote dates and stages remain in that paragraph. The May result stays optional. All ten bodies finish within 75 words. [Frozen generator and prompt audit](space_protected_bank.py) · [Actual traces and unblinded review](../evidence/space-protected-receipt-bank/)

| Selected inventory, final rubric lower score | Interactive | Independent | Request erased | Receipt-matched solo for interactive | Full-pool solo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Query prevents duplication | 56 | 28 | 28 | 49 | 56 |
| Same receipts | 56 | 56 | 56 | 49 | 56 |

The 49-point solo record has two uncertain criteria and an upper score of 63. The interactive record could reach 63 if the narrower treaty-focus credit were accepted. In the selected opportunity, the extra China note supports the broader amendment, China's vote explanation, the common underlying content, and the explicitly stated disagreement. Measure this conditional effect separately from the policy's average across inventories.

| Release-qualified net at 10% loss | Learned after compilation | Optimized independence | Exact optional query |
| --- | ---: | ---: | ---: |
| Uniform | 39.643 | 37.729 | 39.760 |
| Asymmetric | 40.849 | 41.042 | 41.579 |
| Correlated duplicates | 37.329 | 36.330 | 37.426 |

The prose-only writer loses to optimized independence on release-qualified net under all three priors. The May-only row invents a U.S. explanation. The Japan-plus-May row says both drafts lacked affirmative votes after correctly recording Russia's veto in the fixed text. The compiler uses a verified ledger entry when May is delivered, exact archived national sentences, and one reviewed comparison from the two-source writer. No extra inference contributes to the compiled result. The initial 76-word full-information assembly failed the 75-word check; the final ledger wording removes the redundant word “draft” and preserves the standalone stage, tally and failure reason. The all-source compiled record earns 63 lower and 70 upper. These are adaptive, typed-receipt, same-docket results. [Prose policy replay](../evidence/space-protected-receipt-bank/score.json) · [Compiled evidence and exact controls](../evidence/space-protected-receipt-bank/compiled.json) · [Separate UNIFIL reserve provenance](../../crossbench/unifil-reserve.json)

```bash
python space_protected_bank.py replay
OPENBLAS_NUM_THREADS=1 python space_protected_review.py score --exact
OPENBLAS_NUM_THREADS=1 python space_protected_compiler.py --exact
```

The exact optimizer on an equal mixture of the three priors still falls 0.177 points below asymmetric optimal independence. It reaches the separate optional ceiling under uniform and correlated duplicate priors. This uses the same observed receipt scores in calibration and replay. [Retrospective mixture control](../evidence/space-protected-receipt-bank/mixed-prior-planning.json)

The blinded semantic judge tests two rubric units on four generated records and three authored anchors, each in two answer-code assignments. All 28 responses finish and pass the structural checks. Both explicit false-consensus checks are stable and correct. The omission anchor is consistently misclassified as a contradiction, and the two correctly stated comparisons flip judgments between answer assignments. Only three of eight actual record-criterion checks are stable. For the full-input solo, a May vote sentence is incorrectly selected as evidence about the parties' April disagreement. This is evidence against using this judge as a reward. [Judge prompt](space_comparison_judge.py) · [Scores and exact selected spans](../evidence/space-protected-comparison-judge/assessment.json)

## Transfer the fixed Outer Space router to UNIFIL

The UNIFIL reserve joins 15 UNBench author-test votes to adopted row 241 of the pinned UNSC-Bench release. These retrospective records receive 35 public points from the verified Council paragraph. Brazil and China form the predeclared comparison pair, and Russia carries the third field. The frozen routing tables receive typed IDs. The three individual notes and ten final bodies use fresh Qwen3.5-4B generation. Solo and team writers share one final-body limit. The team receives generated notes and the solo receives original source summaries for its selected blocks. [Case sources and rubric](../../crossbench/unifil-record.json) · [Locked generator](unifil_final_transfer.py)

The frozen request raises the selected generated record's material score from 35 to 49. It supplies China's rationale and common support for the mission. Both team records fail release because Brazil's bounded statement was strengthened. The receipt-matched solo preserves support for the mission and China’s view, earns 49, and clears the guard. Full-pool solo omits Russia and wrongly attributes a divergence over enhanced military communication. The prose route's release-qualified net trails exact optimized independence under all three priors, even though the selected China contribution was real. [Generation, notes and hand scores](../evidence/unifil-final-transfer/score.json)

The alternate source-verified renderer preserves Brazil's partial qualifier and conditions the comparative sentence on both source IDs. The all-source record scores 70, and the selected question lifts the result from 42 to 63. The renderer uses case-authored national language and a fixed comparison. This result measures routing under protected content transport. [Proof ranges and policy replay](../evidence/unifil-final-transfer/verified-transport.json)

```bash
python unifil_final_transfer.py check
python unifil_final_transfer.py replay-tokens
OPENBLAS_NUM_THREADS=1 python unifil_final_review.py score --exact
OPENBLAS_NUM_THREADS=1 python unifil_verified_transport.py --exact
OPENBLAS_NUM_THREADS=1 python unifil_robust_prior.py
python unifil_pairwise_judge.py assess
```

| Verified-transport release net, 10% loss | Frozen transfer | Rubric-only MARL fit | Exact independence | Optional ceiling |
| --- | ---: | ---: | ---: | ---: |
| Uniform | 48.945 | 49.034 | 47.713 | 49.120 |
| Asymmetric | 50.028 | 51.093 | 50.711 | 51.141 |
| Correlated duplicates | 47.434 | 47.524 | 46.942 | 47.566 |

The only new fit uses 280 table-policy updates on the uniform public rubric. It reads actual prose scores only for retrospective evaluation. The two nonuniform priors are excluded from optimization. The public-rubric exact planner reaches each separate per-prior ceiling. Its worst-case gain of 0.430 certifies the maximin advantage under the declared prior set. An initial LP implementation could not import SciPy in the pinned CI environment. The final certificate compares a single plan with per-prior exact upper bounds and needs no LP library. [Fit and request erasure](../evidence/unifil-rubric-fit/fit.json) · [Analytic certificate](../evidence/unifil-final-transfer/robust-prior.json)

The same-checkpoint pairwise judge gets two of four authored anchor pairs correct in both presentation orders. It confuses one presentation of the both-omitted anchor and selects the first displayed record in both permission presentations. It selects the two-source record on both applied criteria, including the open-issue item where both candidates lack the required qualification. This is useful as a held-out error example for semantic judge calibration. [Blind judgments](../evidence/unifil-pairwise-judge/assessment.json)

## Preserve UNIFIL qualifiers with model-selected source pointers

The Qwen note writer dropped “some” from the Brazil receipt in the previous run. The new sender chooses a span ID and never rewrites the span. A local check resolves the chosen identifier to its exact named source, then applies the predeclared completeness predicate. A separate model selection links two verified national receipts. The final clauses, the official paragraph and the rubric remain the pre-existing authored renderer.

| Probe | Correct model decisions | Gate effect |
| --- | ---: | --- |
| Intact source, both code orders | 8/8 | Admits all full excerpts |
| Incomplete or misattributed source | 4/10 | Withholds two unsupported and four incomplete selections |
| Intact Brazil–China comparison | 2/2 | Renders the verified narrow comparison |
| Comparison missing China's receipt | 1/2 | Withholds the one new unsupported comparison |

The observed proof bank is identical to the prior verified control on intact summaries. Exact replay uses those proofs and the frozen policy fit. Removing Brazil's qualifier makes the late-gated learner trail independent delivery by 1.959, 3.115 and 1.482 net points across the three priors. Faithful rejection protects the final record while reducing what the policy can achieve. The benchmark should measure qualified extraction, safe withholding, and routing separately. [Source prompts and exact receipt outcomes](../evidence/unifil-span-transport/assessment.json)

The early gate projects each private inventory onto admitted proof IDs before routing. It neither grants a shared missingness flag nor shows the other actor's inventory. When the Brazil qualifier is unavailable, early minus late admission gains are 2.218, 2.744 and 1.506 points. The same early-gated policy remains 0.372 behind optimized independence on asymmetric inventories. [Exact matched projection](../evidence/unifil-span-transport/inventory-gate.json)

Replacing assembled choices with sentence IDs recovers six of eight intact fields. In the reversed layout the model takes the contextual sentence in place of required evidence in the Brazil and Russia fields. It correctly abstains on four of ten incomplete cases, including both May omissions, and makes one wrong-owner selection on the Brazil misattribution control. Every incomplete payload is withheld. The original relation prediction is replayed only for byte-identical available notes. [Prompt and provenance algorithm](unifil_sentence_extraction.py) · [Generation archive](../evidence/unifil-sentence-extraction/)

A single 280-update fit mixes intact and Brazil-missing uniform inventories. Under early admission it changes none of the three missing-qualifier returns and lowers each intact return. This optimizer result gives no reason to replace the prior fit. [Calibration and comparator replay](../evidence/unifil-admission-fit/fit.json)

```bash
python unifil_span_transport.py check
python unifil_span_transport.py replay
OPENBLAS_NUM_THREADS=1 python unifil_span_review.py --exact
OPENBLAS_NUM_THREADS=1 python unifil_inventory_gate.py
OPENBLAS_NUM_THREADS=1 python unifil_sentence_extraction.py assess --exact
```

In the unseen China-only regime, both policies lose only the redundant request fee, across all three priors. The query ceiling matches optimized independence. The optional planner is given the benchmark's inventory distribution and the actors still see their own local IDs. [One-field ceiling and costs](../evidence/unifil-sentence-extraction/china-only-early-gate.json) · [Exact token replay](../evidence/unifil-sentence-extraction/token-replay.json)

## Extract fact slots and condition the routing policy on the public rubric

Two narrow sentence-ID calls recover all 8 intact proofs on the original placement contrasts, compared with 6 for one compound query. They correctly handle 7/8 second-sentence omissions, 2/2 wrong-owner fixtures, and 4/8 first-sentence omissions. The verifier rejects every incomplete bundle. Both proposed spans must satisfy the authored proof roles. Reuse the earlier comparison call only if its receipt text is byte-identical. This is a bounded test of slot extraction with authored questions and final wording. [Source-level checks](../evidence/unifil-slot-extraction/assessment.json) · [Exact token replay](../evidence/unifil-slot-extraction/token-replay.json)

The reward-conditioned router uses a single shared network to produce decentralized action tables from a public rubric. Its synthetic training profiles preserve the same mechanics as the historical receipt experiments. The historical payout tables are read only when scoring. There is no gradient adaptation on the four historical source families. [Reproducible fit](rubric_conditioned_routing.py)

This one 320-update synthetic fit beats exact independence on all four historical uniform priors and in six of twelve case-prior cells overall. Erasing the question lowers scores in each cell, including the cells where exact independence is stronger. All historical payouts come from existing protected receipt banks. The model changes the route only. [Results and freeze](../evidence/rubric-conditioned-routing/report.json)

```bash
python unifil_slot_extraction.py replay
OPENBLAS_NUM_THREADS=1 python unifil_slot_review.py --exact
python rubric_conditioned_audit.py
```

The checkpoint replay reproduces all four greedy tables and all twelve scored returns. The constant-input ablation preserves canonical ordering and matches all four greedy tables. A common exact canonical rule falls 0.043 points behind the mean of separate optima on uniform inventories. Under asymmetric inventories, label permutations of tied fields can change returns. These controls narrow the result to reusable routing and identify the need for sharper tests of adaptation to reward magnitudes. [Frozen-weight audit](../evidence/rubric-conditioned-routing/audit.json) · [Common-policy replay](../evidence/rubric-conditioned-routing/fixed-policy-ceiling.json)

## Reward changes that require different routing actions

Two complement-bonus pairs keep singleton values, total payoff, fees and canonical ordering fixed. A scale contrast keeps the entire reward profile in proportion. Exact enumeration gives the best achievable policy for each endpoint and the best single policy for each pair. The frozen prior fit matches its constant-input arm. Under uniform inventories, using a fixed table costs at least 1.041 mean points on the balanced pair and 0.596 on the steeper pair. The low-reward endpoint cannot cover a single delivery. [Exact panel and frozen policies](../evidence/routing-reward-contrasts/panel.json)

One new fit trains on matched synthetic variations and divides each task's net by its maximum payoff with a 0.25-point floor. The same historical record banks and all exact contrast profiles are withheld from fitting. The fit switches to no communication on the low-stakes endpoint and reaches its exact zero optimum. It still behaves like the constant-input arm on the high-stakes dependency contrasts. Its historical score improves from six to eight comparator wins across twelve cells. [Gradient run and both banks](../evidence/routing-paired-reward-fit/report.json)

The learned portfolio ranks 13 candidates on the public reward and assumed prior. It applies the same chosen table before private inventories are observed. It clears the exact shared-policy average on all three synthetic contrast pairs and closes much of the balanced last-pair gap. On historical banks, it wins 7/12 cells under the nominal uniform assumption and 11/12 with the evaluation prior supplied. With the exact-independent policy as a candidate, the supplied-prior arm ties the last cell. No observed record score is used to select a candidate. [Portfolio and exact controls](../evidence/routing-paired-reward-fit/portfolio.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_reward_contrasts.py
OPENBLAS_NUM_THREADS=1 python routing_paired_reward_fit.py
OPENBLAS_NUM_THREADS=1 python routing_learned_portfolio.py
```

## Choose routing policies without knowing the evaluation prior

The robust selector uses the three established priors as an uncertainty set. It maximizes net gain against each prior's optimized independent policy on the public rubric, using finite simplex enumeration and a dual certificate. Historical realized scores are loaded only for evaluation. A single shared draw before either desk observes its inventory implements the mixture. On these historical anchors every selected mixture is a point mass. Across four new synthetic stress distributions, the selector preserves fewer strict wins than the nominal arm and has a larger worst deficit. [All priors, tables and observed bank scores](../evidence/routing-prior-robustness/report.json)

Column generation adds a best possible two-desk query policy against the current dual prior and checks an unrestricted upper bound. All four anchor optima are certified. These are exact bounds for the candidate inventory distributions on the public rubric. Their policies also lose against optimized independence when desk inventories are exchanged. [Capacity and stress replay](../evidence/routing-prior-robustness/ceiling.json)

A public fair coin makes proposer/responder orientation exchangeable and makes every desk-swap score identical to its original asymmetric score. This lowers the worst swapped-desk deficit from 2.139 to 0.093 points. Symmetry constrains what teams can gain from asymmetric opportunities. On Mali's swapped distribution, the exact symmetric ceiling is 0.029 below the exact prior-aware independent policy. [Symmetry replay](../evidence/routing-prior-robustness/symmetry.json)

A separate 32-observation pilot uses aggregate counts from prior synthetic episodes. It ranks the learned portfolio with both desk assignments and includes an independently optimized candidate using those same counts. Across 128 pilots per distribution, its mean beats the prior-aware independent oracle in 21 of 28 historical case-prior cells, including all four desk swaps. Its future score excludes the cost of collecting the pilot. The replay checks 144 vectorized action values against the original evaluator. [Simulated pilots](../evidence/routing-prior-robustness/pilot.json) · [Verification](../evidence/routing-prior-robustness/verification.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_prior_robustness.py
OPENBLAS_NUM_THREADS=1 python routing_prior_ceiling.py
OPENBLAS_NUM_THREADS=1 python routing_role_symmetry.py
OPENBLAS_NUM_THREADS=1 python routing_prior_pilot.py
```

## Stress pilot freshness, acquisition cost and receipt-only observability

The drift replay pairs original and current synthetic inventory distributions. It prices both inventory disclosures per observation, then reports break-even horizons with the declared fee. Old-only and old-heavy pilots lose under every desk reassignment. A recent cross-validation rule sometimes recovers value from archived data and still underperforms fresh-only routing after the desk swap. [Stale and fresh simulations](../evidence/routing-prior-robustness/pilot-drift.json) · [Recency selector](../evidence/routing-prior-robustness/pilot-recency.json)

A second diagnostic constructs priors that the incumbent's exact receipt channel cannot distinguish even with the role flip observed. An explicit probe can expose a useful difference under three of the four known hypothesis pairs. Eight initial tasks serve as probes, receive their own net reward, and inform selection for the next 64. This evaluates strategic experimentation with a fixed policy library and a specified pair of alternatives. [Passive identifiability bound](../evidence/routing-prior-robustness/receipt-identifiability.json) · [Active probe and matched horizon](../evidence/routing-prior-robustness/active-receipt-probe.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_pilot_drift.py
OPENBLAS_NUM_THREADS=1 python routing_pilot_recency.py
OPENBLAS_NUM_THREADS=1 python routing_receipt_identifiability.py
OPENBLAS_NUM_THREADS=1 python routing_active_receipt_probe.py
```

The first receipt-channel invocation reached scoring and failed on a result-field variable name. The corrected invocation completed all four cases. Validation compared 128 conditional distributions against the original routing evaluator and checked the four equivalence witnesses and exact value caps. [Replayed quantities](../evidence/routing-prior-robustness/pilot-followup-verification.json)

### Probe planning with three anchors

The exact follow-up chooses a probe and post-pilot selector with only the three declared inventory hypotheses and the intended rubric. Test likelihoods and observed-bank scores are calculated after selection. The all-fixed comparator uses the same pool and 72 episodes. Only Mali adopts the probe, and the expected gain is less than 0.004 points across the entire horizon. The desk swaps have much larger avoidable losses if a selector has the correct prior. [Complete scores](../evidence/routing-prior-robustness/population-probe.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_population_probe.py
```

The enriched logger keeps the desk attribution of delivered field IDs on the symmetric incumbent. Its output reduces exactly to the original union mask when desk attribution is discarded. Rank rises from 11 to 25. The original aliases become distinguishable, and new indistinguishable priors leave 0.057 to 0.694 net points per episode on the table relative to a supervisor who knows the prior and can choose the requester. Both the newly constructed priors and the exact realized scores are retained. [Ordered receipt evidence](../evidence/routing-prior-robustness/ordered-receipts.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_ordered_receipts.py
```

### Cross Sudan draft visibility with dossier order

Reuse the archived independent and peer-conditioned drafts, and add a chair with an empty draft list. Reverse the source block order without changing any block. All six frozen Qwen3.5-4B chair requests use the same 256-token ceiling. The two original team outputs match exactly. Same-assistant scoring retains the original two annotations and uses the same ten criteria for the four new records. [Raw generation and replay](../evidence/source-record-sudan-chair-control/replay.json) · [Scores, guards, completion and access provenance](../evidence/source-record-sudan-chair-control/scores.json)

The peer-conditioned chair beats independent drafts by seven raw points in the original order and trails by seven after reversal. The original peer-conditioned and draft-free records both hit the cap. The reversed draft-free record reports unsupported joint support and fails the guard. The draft-free condition isolates access to the dossier at the same chair cap and uses fewer total calls. The dossier-only access results expose a confound if the process score is inferred from the final text alone. The new dataset join identifies the UNBench draft and UNSC-Bench official roll call, with the conflicting 2014 UNBench vote-table ID recorded explicitly. [Accession](../../crossbench/sudan-accession.json)

```bash
python source_record_sudan_chair_control.py replay ../evidence/source-record-sudan-chair-control
python source_record_sudan_chair_score.py ../evidence/source-record-sudan-chair-control --annotations ../evidence/source-record-sudan-chair-control/annotations.json
```

### Calibrate peer evidence attribution against receipts

The development panel uses the Sudan chair, the Outer Space record and the Western Sahara exchange. It moves supporting evidence between the initial dossier, delivered note and unsent note while holding the supported final claim constant. It also checks a peer message that repeats a false claim. The four-way judge changes verdict on all 15 items when the options rotate. The single-excerpt version keeps evidence visibility in code. Its affirmative question gets 14/15 and the inverted wording gets 0/15. A unanimous two-wording verdict resolves none of the 15. [Four-way rotations](../evidence/peer-evidence-judge/scores.json) · [Single-excerpt verdicts](../evidence/peer-evidence-factored/scores.json) · [Exact archived proof spans](../evidence/archived-peer-provenance.json)

```bash
python archived_peer_provenance.py
python peer_evidence_judge.py score ../evidence/peer-evidence-judge
python peer_evidence_factored.py score ../evidence/peer-evidence-factored
```

Two affirmative phrasings agree correctly on 10 of 15 development conditions and all five UNIFIL extension conditions. The development disagreement is concentrated in the compound Outer Space claim, whose official excerpt gives the rationale more directly than its support for the amendment. The Sudan paraphrase is missed under both wordings. The UNIFIL panel includes an exact false peer repetition that turns partial acknowledgment into full acknowledgment. Both questions correctly reject the promotion. [Affirmative controls and scores](../evidence/peer-evidence-affirmative/scores.json)

```bash
python peer_evidence_affirmative.py score ../evidence/peer-evidence-affirmative
```

The atomic follow-up resolves all ten scoped controls under both affirmative questions. Splitting the Outer Space claim exposes the initially visible vote and the separately delivered rationale. The combined version remains unresolved even with both official excerpts. The narrowed Sudan claim recovers the existing paraphrase and passes a generic near-miss and a reverse-polarity delivery. These are preselected atoms from exposed development dockets. [Responses and score](../evidence/peer-evidence-atomic/scores.json)

```bash
python peer_evidence_atomic.py score ../evidence/peer-evidence-atomic
```

### Compare sampled team rewards with per-agent counterfactual credit

Both CPU fits start from the same network and use the same 160 batches of 384 exogenous draws. When a counterfactual requester action changes the question, replay the responder's policy with that observed question and the same responder uniform draw. The exact receipt environment supplies all alternative rewards. The judge calibration above is separate from the training reward.

Counterfactual credit scores higher than shared-reward training on the fixed four-docket record bank under all seven tested inventory priors. It beats optimized independence in 14 of 28 cells, including all four uniform cells. Erasing the request lowers the four uniform scores after keeping the query fee. The shared reward has a higher final exact training objective. The deterministic refit, saved tensors, and ordered gradient check replay. [Original report](../evidence/routing-sampled-credit/report.json) · [Stress replay and exact checks](../evidence/routing-sampled-credit/verification.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_sampled_credit_replay.py ../evidence/routing-sampled-credit
```

### Train across hidden inventory groups and compare capacity

The paired fit uses identical batches under seven synthetic training priors. It compares equal group weights with weights that emphasize the lowest exact scores relative to each group's independent reference. Both improve the worst stress loss from −2.316 to −1.893 and win six of sixteen stress cells. The weighted and unweighted runs choose identical tables on three dockets. [Fit evidence](../evidence/routing-regret-training/report.json) · [Exact refit and earlier request-erasure diagnosis](../evidence/routing-regret-training/verification.json)

On the archived banks, exact pricing bounds any public lottery of tables and requester orientations. UNIFIL, Mali and Myanmar have negative upper bounds against the independence oracle that knows the distribution. The exhibited Outer Space mixture has a positive worst-case gain of 0.182. Constraining independent delivery to the same hidden-prior setting gives a strict comparative advantage for feasible interactive mixtures on all four banks. [Bounds and policy tables](../evidence/routing-regret-training/blind-limit.json) · [Equal-information comparison](../evidence/routing-regret-training/fair-control.json)

```bash
OPENBLAS_NUM_THREADS=1 python routing_regret_replay.py ../evidence/routing-regret-training
OPENBLAS_NUM_THREADS=1 python routing_blind_limit.py --verify ../evidence/routing-regret-training/blind-limit.json
OPENBLAS_NUM_THREADS=1 python routing_blind_fair_control.py ../evidence/routing-regret-training/blind-limit.json
```

### Freeze a policy on the advertised rubric

The Outer Space plan selected from all seven declared priors wins all seven archived comparisons against informed independence. The smallest gain is 0.140 points. Planning on three anchors alone loses on the desk swap. Exact search contributes 96.0% of the winning mixture. The frozen menu loses 0.529 points in its worst case, and the added tables plus silent controls reach a positive 0.168 worst-case gain. The added columns were generated with a learned warm start. [Primary replay](../evidence/routing-announced-selection/scores.json) · [Anchor-only control](../evidence/routing-announced-selection/anchor-scores.json) · [Menu ablation](../evidence/routing-announced-selection/ablation.json)

The August 2020 written-ballot transfer freezes a new historical docket and both routing plans before scoring. With the approved public record and seven fresh frozen Qwen supplements, the team beats same-information independent delivery on all seven raw-score comparisons. One remains under strict release. Admitting uncertain records restores six wins, while the two definite errors still fail. The fixed public section contributes 35 points and the model writes only the optional supplement. [Source and rubric](../../crossbench/ftf2020/task.json) · [Raw and strict scores](../evidence/ftf2020-record-transfer/scores.json) · [Review sensitivity](../evidence/ftf2020-record-transfer/sensitivity.json)

```bash
d=../evidence/ftf2020-record-transfer
OPENBLAS_NUM_THREADS=1 python routing_ftf_record.py score --directory "$d" --plan "$d/plan.json" --annotations "$d/annotations.json"
OPENBLAS_NUM_THREADS=1 python routing_ftf_independence.py score --observed "$d/scores.json" --control "$d/independent-plan.json"
OPENBLAS_NUM_THREADS=1 python routing_ftf_sensitivity.py "$d"
```

### Scope writer instructions to the annexes delivered

The seven-call source-by-source prompt retains the U.S.–Russia comparison and improves release margins, but it introduces a false U.S. motive on three receipts lacking that country's explanation. A six-call follow-up removes the missing-role instructions and only requests a comparison with both annexes present. It reuses the identical full-receipt prompt and answer. The false claims disappear. All seven supplements are eligible, the frozen learned route beats the matched-information independent control on all seven priors, and erasing its questions lowers each score. A matched script menu that uses the public rubric and the original silence controls also trails on all seven. [All-role prompt](../evidence/ftf2020-bounded-writer/comparison.json) · [Delivered-role prompt](../evidence/ftf2020-visible-writer/comparison.json) · [Script control](../evidence/ftf2020-visible-writer/script-control.json)

```bash
old=../evidence/ftf2020-bounded-writer
new=../evidence/ftf2020-visible-writer
python routing_ftf_bounded_writer.py score "$old" --annotations "$old/annotations.json"
python routing_ftf_visible_writer.py score "$new" --annotations "$new/annotations.json"
python routing_ftf_script_control.py "$new/scores.json"
```

### Transfer the delivered-role writer to the 2021 climate-security vote

The two writer conditions share the 70-point fixture, the learned, scripted and independent plans, and all user evidence. They differ in whether system instructions mention absent delegations. The climate case uses the same announced receipt payoff as the written-vote task, so no team or control is refitted. Both conditions release six records. The delivered-role writer removes four off-receipt explanations, raises the team's absolute release score on all seven priors and gives six wins over the script mixture. Its India-only record attaches a subject-matter restriction to the geographic scope of the Sahel alternative. The later broad scope reminder leaves that error and introduces another uncertain guard. A reviewed one-receipt edit restores the advantage over the script in all seven cells. [Fixture and accession](../../crossbench/climate2021/task.json) · [Paired outputs](../evidence/climate2021-writer-transfer/scores.json) · [Scope prompt](../evidence/climate2021-scope-writer/scores.json) · [Reviewed edit](../evidence/climate2021-scope-writer/source-edit.json)

```bash
d=../evidence/climate2021-writer-transfer
python routing_climate_transfer.py score --directory "$d" --plan "$d/plan.json" --annotations "$d/annotations.json"
d=../evidence/climate2021-scope-writer
python routing_climate_scope.py score "$d" --annotations "$d/annotations.json"
python routing_climate_source_edit.py
```

### Separate scope extraction from source support

Direct source support approves the real India-only restriction. The candidate-only scope extractor abstains on that sentence, enabling the fail-closed replay to remove it and retain the rest. It also misses two synthetic restrictions. A frozen rule requiring both checks to clear blocks all six unsupported controls across the new Sahel and UNIFIL panels and admits five of six supported controls. Other guards remain under the previous review when routing is replayed. [Calibration](../evidence/climate2021-scope-gate/scores.json) · [New controls](../evidence/scope-gate-transfer/scores.json) · [Routing replay](../evidence/climate2021-scope-gate/replay.json) · [Judge-cost sensitivity](../evidence/climate2021-scope-gate/cost.json)

```bash
d=../evidence/climate2021-scope-gate
python routing_climate_scope_gate.py score "$d"
python routing_climate_gate_replay.py "$d/scores.json"
python routing_scope_gate_transfer.py score ../evidence/scope-gate-transfer
python routing_climate_gate_cost.py "$d/replay.json"
```

### Put generated national messages on the route

The role writers generate three frozen notes. The chair receives the same field labels but sees the notes in place of approved summaries. The learned route initially wins six of seven release-score comparisons with the script. Strictly dropping the two overlength notes reduces that to two. Forwarding whole-sentence prefixes keeps all three notes within the 55-word limit and restores five wins. The frozen scope gate then removes the recurring India-only overstatement and keeps the two correct control sentences. With those three checks the learned route leads both fixed controls in all seven priors before judge costs. The evaluation caches one note per role and uses the earlier review for the other claims. [Raw language records](../evidence/climate2021-language-channel/scores.json) · [Budget-compliant records](../evidence/climate2021-note-budget-writer/scores.json) · [Scope decisions and scores](../evidence/climate2021-language-gate/scores.json) · [Word and judge volume](../evidence/climate2021-language-gate/cost.json)

```bash
d=../evidence/climate2021-language-channel
python routing_climate_language_channel.py score "$d" --annotations "$d/annotations.json"
python routing_climate_language_budget.py "$d/scores.json"
d=../evidence/climate2021-note-budget-writer
python routing_climate_note_budget_writer.py score "$d" --annotations "$d/annotations.json"
d=../evidence/climate2021-language-gate
python routing_climate_language_gate.py score "$d"
python routing_climate_language_gate_cost.py "$d/scores.json"
```
