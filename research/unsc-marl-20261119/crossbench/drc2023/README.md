# DRC sanctions renewal and evidence coverage

On 27 June 2023 the Council adopted French draft S/2023/469 as resolution 2688 (2023). All 15 official votes match UNBench author-test event 2489 and UNSC-Bench adopted row 254 at revision `55bd5aa5bb317a942b9229de13dca985e642a40b`. UNBench has no training row for the event. This accession was unused in the written-vote routing fit. Russia voted in favour as a Council member. The DRC welcomed the renewal in its statement as the affected state. [Official meeting record, pp. 2–3](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9360&t=pdf) · [Adopted resolution](https://documents.un.org/api/symbol/access?l=en&s=S%2FRES%2F2688%282023%29&t=pdf) · [Accession](accession.json)

## First-pass final record

Freeze four receipts covering sanctions, the Group of Experts, Russia and the DRC. Score ten source criteria at seven points each, including an authored roll call shared by every method. Allow up to 185 words. The comparison receives just the supported common proposition and the separate vote and speaking fields. The renderer sets citation IDs from the predeclared receipt binding and leaves the generated language intact. Run each field once using frozen Qwen3.5-4B on CPU. Verify scope, exact citations and completion for release. Review all delivered criteria separately using exact spans. The annotations are from the same assistant. [Case and source locations](case.json) · [Acceptance rules](acceptance.json) · [Exact-span review](annotations.json) · [Launch record](evidence/launch.json)

All 14 reachable receipt packets clear release. Three preserve every criterion licensed by their receipts. The Experts paragraph gives the mandate and report dates and monthly update cadence. It leaves out possible extension action and the reports' Council recipient, missing both compound criteria. The separate DRC paragraph also compresses the two categories of sanctioned parties into “non-state actors.” The overlap paragraph gives the shared support and identifies who voted and who spoke.

| Receipt packet | Separate fields /70 | Whole packet /70 | Release, separate / whole | Output token cap, both | Input tokens, separate / whole |
| --- | ---: | ---: | --- | ---: | ---: |
| Sanctions, Experts, Russia | 35 | 28 | Pass / pass | 312 | 590 / 410 |
| Sanctions, Experts, DRC | 28 | 21 | Pass / fail | 312 | 593 / 417 |
| Sanctions, Russia, DRC | 49 | 49 | Pass / pass | 416 | 683 / 428 |

The separate writer uses three, three and four calls for these packets. The whole writer uses one each. The whole output that fails release uses decorated source markers in place of the exact IDs. The mean score is 37.33 for separate fields and 32.67 for the whole writer. This comparison matches configured output capacity and evidence, with different input and call costs. [Raw generations](evidence/transcript.jsonl) · [Reviewed comparison and all 14 packets](evidence/results.json)

## Routing and reward

Replay the frozen original and specialist MARL teams and the fixed and adaptive scripts through the same generated field records. Under strong specialisation and an accurate desk hint, the specialist reaches 32.58/70 and 16.338 net points above the local anchor after contact fees. Fixed reaches 32.74 and 16.506. Adaptive reaches 32.99 and 16.755. The scripts use the true simulated holdings prior and select their routes using the source-verified reference bank. The separate pooled upper-information control receives all three requested cards immediately and averages 36.75/70. [Exact routing replay](evidence/policy-replay.json)

Recompute the best adaptive scripts over the same three-contact protocol and compare the objective they optimize. This retrospective diagnostic sees the observed packet scores. The missing Experts criteria give a script little reason to retrieve the Experts receipt if its entire reward comes from the prose minus fees.

| Script objective | Actual net points | All requested cards delivered | Experts delivered when requested and absent locally |
| --- | ---: | ---: | ---: |
| Authored record score minus fees | 16.755 | 65.12% | 79.79% |
| Observed record score minus fees | 17.042 | 37.01% | 19.54% |
| Observed score plus seven per additional requested delivery minus fees | 16.953 | 65.12% | 75.83% |

The last two rows yield almost identical actual record scores, 33.194 and 33.193. Count requested receipts independently of the wording score and check whether the writer preserves the evidence after it arrives. [Objective replay and per-case values](evidence/outcome-objective.json)

Fit one exact joint policy with the seven-point delivery bonus on the original written-vote task. This uses 180 updates of the small tabular policy with the original specialised roster priors. The 13,148 trajectory rows group outcomes by reward, so changing the terminal score changes the number of distinct rows. DRC supplies only the transfer endpoint. The new and old specialist teams are evaluated against the original actual score with no bonus. Changes in net points and source completion are small in all three conditions.

| DRC desk condition | Original specialist net | Coverage-bonus fit net | Original completion | Coverage-bonus fit completion |
| --- | ---: | ---: | ---: | ---: |
| Original prior | 13.194 | 13.198 | 40.78% | 40.82% |
| Strong specialisation, accurate hint | 16.338 | 16.335 | 64.28% | 64.26% |
| Strong specialisation, wrong hint | 14.889 | 14.909 | 53.75% | 53.93% |

The exact script contrast identifies a reward failure. The joint fit tests an auxiliary reward on a different source docket and supplies little evidence of improvement in transfer. The specialist remains below both optimised scripts with a correct hint. The routing observations use simulated availability and documentary evidence. Dialogue quality and an independent assessment remain open. [One fit, policy and all transfer cases](evidence/coverage-fit.json)

## Replay

From this directory, use the existing Qwen smoke environment and the archived transcript. The scoring replay reconstructs the same transcript and packet text before applying the manual span annotations. The policy replay, script optimisation and joint fit require no new model inference.

```bash
p=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp evidence/results.json <("$p" results.py)
cmp evidence/policy-replay.json <("$p" policy_replay.py)
cmp evidence/outcome-objective.json <("$p" outcome_diagnostic.py)
cmp evidence/coverage-fit.json <("$p" coverage_fit.py)
```

From the repository root, use the CI data environment and retained official files to reproduce the dataset accession.

```bash
d=research/unsc-marl-20261119/crossbench/drc2023
ci=/mfs1/u/memo/country-persona-research/envs/ci-data-pipeline-20261019-v1/bin/python
source_dir=/mfs1/u/memo/country-persona-research/runs/drc-source-FEPQLw
cmp "$d/accession.json" <(PYTHONPATH=src "$ci" "$d/accession.py" "$source_dir")
```

## Give credit for individually preserved source facts

The original Experts terms and reporting criteria are conjunctive. The first-pass paragraph earns zero of 14 even though it gives the mandate expiry, prospective review deadline, both report dates and the separate Committee update cadence. The possible extension action and Council recipient stay absent. Divide the two seven-point criteria among their three and four constituent assertions and require exact wording witnesses for every stated assertion. This gives the Experts paragraph 9.92 of 14 for choosing a route. The original scoring, complete-criterion flags and release checks remain the evaluation for the resulting route.

With the same costs, scripts and holdings as the previous diagnostic, using those reviewed witnesses as partial credit recovers 65.12% complete source delivery and 78.03% Experts receipt when needed. The prose-only script reaches 37.01% and 19.54%, respectively. The partial-credit script scores 33.118 on the original prose scale and earns 16.878 net points, compared with 33.194 and 17.042 for prose-only. This identifies information lost by the conjunctive score on this docket. It uses the same inspected prose as an endpoint and a retrospective script. [Exact witnesses, preserved original scores and replay](evidence/experts-reward.json)

Separately ask frozen Qwen3.5-4B to classify each assertion from the candidate alone. For each field, rotate the three alternatives through two letter orders. An order disagreement is a deferral. The panel covers a correct, omitted and incompatible claim for each field and 28 field checks across four unedited model outputs. The model classifies 8/21 authored checks and 19/28 generated checks correctly, with 8 and 4 deferrals respectively. It confuses the sanctions expiry with the Experts review deadline in the generated record that had no Experts receipt. Keep source eligibility as a hard prerequisite, and require an actual actor-action witness before granting credit for an eligible assertion. These named alternatives test specific errors on one docket. They do not estimate detection of all possible wrong values. The generated labels come from same-assistant review. [Prompts and replayable classifications](experts-judge-evidence/results.json) · [Pairwise credit and token replay](experts-judge-evidence/audit.json)

On the authored pairs, stable positive credit prefers the complete version in only two of seven omission pairs and two of seven conflicting-value pairs. The other pairs tie because the judge withholds credit from the complete control as well. A low false-credit count on authored controls therefore overstates this judge's usefulness for ranking records. See the audit for every pair.

## Test a paid reply when a desk has none of the requested sources

A missing receipt in the original protocol could come from a dropped request, a dropped reply or a desk that had none of the currently requested cards. In the revised protocol, a desk that receives the request always sends one reply. If it has no match, it replies with an explicit negative receipt. Both message legs still succeed independently with probability 0.9, the request and reply fees are unchanged, and the chair has three contacts. A delivered negative receipt certifies only that the contacted desk holds none of that request's cards. It carries no roster details beyond that and earns no direct rubric credit.

Fit one joint tabular chair and responder on the original written-vote record objective using 180 exact policy-gradient updates. The new training reward rises from 8.341 to 15.169 net points. Replay the final policy independently to verify the training expectation. Freeze the weights and retain the same source mapping and final writers. The known-prior scripts share the same message protocol and optimize the same authored endpoint, including their reply order. An erasure intervention keeps the fitted weights, fees and physical outcome fixed and hides the negative receipt from the chair. A re-optimized adaptive control also has its receipt hidden and retains the reply fee. These controls distinguish use of the signal from optimal planning with it.

| DRC desk condition | Previous learned net | Learned with receipt | Same learner with receipt hidden | Fixed with receipt | Adaptive with receipt |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original prior | 13.194 | 13.322 | 11.497 | 13.103 | 13.823 |
| Strong specialisation, accurate hint | 16.338 | 16.595 | 16.032 | 16.311 | 17.002 |
| Strong specialisation, wrong hint | 14.889 | 15.456 | 12.016 | 16.311 | 17.002 |

On the accurate-hint row, the learned team delivers all requested cards 66.89% of the time, up from 64.28%. It reaches 65.09% with the canonical desk response and 62.63% when the negative receipt is hidden. The fixed and adaptive scripts with the receipt reach 62.90% and 67.82%. The adaptive script gains 0.220 actual net points over the re-optimized script with equally priced but hidden negative receipts. The larger erasure penalty for the learner shows sensitivity of the fixed policy to a missing signal under intervention. It includes lack of re-optimization. [Training, controls and exact DRC replay](evidence/receipt-feedback.json)

Replay the frozen learned team and baselines on the existing authored UNAMI, UNIFIL and Colombia records. The learned team with negative receipts improves on the previous learner in all nine family and condition pairs. With an accurate hint it earns 16.778, 21.916 and 23.734 net points. This beats the new fixed script on UNAMI and Colombia, and trails it by 0.003 on UNIFIL. The adaptive script still leads in all nine comparisons and the fixed script leads on all three wrong-hint comparisons. DRC uses generated prose and same-assistant annotations. The other three endpoints use authored answers. All use simulated inventories and no learned natural-language interaction. [Cross-family replay with no refitting](evidence/receipt-feedback-transfer.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp evidence/receipt-feedback.json <("$p" receipt_feedback.py)
cmp evidence/receipt-feedback-transfer.json <("$p" receipt_feedback_transfer.py)
```

## Train with a fallible specialist hint

Keep the paid receipt protocol and written-vote reward. Fit once for 180 updates with the indicated desk actually specialised in 75% of training episodes. The held-out comparisons use both pure conditions and their weighted 75% mixture. The calibrated adaptive script sees the 75% prior and updates from receipts. It receives no information about which desk is the true specialist in a particular episode. The oracle scripts have access to its identity. Compare against the preceding fit, which trained with a correct hint and can still receive a wrong one at test time.

| Endpoint | Earlier fit at 75% | New fit at 75% | Calibrated adaptive at 75% |
| --- | ---: | ---: | ---: |
| UNAMI | 16.505 | 16.368 | 16.848 |
| UNIFIL | 21.573 | 21.395 | 22.314 |
| Colombia | 23.333 | 23.136 | 23.466 |
| DRC generated | 16.310 | 16.170 | 16.718 |

The new fit gains 0.21–0.31 net points across the four dockets with a wrong hint and loses 0.25–0.37 when the hint is correct. The losses outweigh the gains at 75% reliability. The DRC generated endpoint still uses the authored score for selecting script routes and the reviewed prose for evaluating them. Other endpoints use the authored scores for both. The suite uses the same simulated availability and four already exposed dockets excluded from the fit. [Single fit, cases and baselines](evidence/receipt-hint-fit.json)

Recover the separate effect of front-end and subsequent decisions with frozen swaps on the generated DRC endpoint. Across the 12 local initial states, the learner's average probability of opening with the named desk drops from 65.48% to 42.81%. Swapping only those opening probabilities to the new fit yields 16.235 net points at 75% reliability. Swapping only follow-up decisions yields 16.234. Swapping only responders leaves the old score within 0.001 points. The decline localizes to both parts of the chair policy. These are retrospective swaps, with the same responder, receipt transport and price for each chair-only comparison. [Component swaps](evidence/receipt-hint-swaps.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp evidence/receipt-hint-fit.json <("$p" receipt_hint_fit.py)
cmp evidence/receipt-hint-swaps.json <("$p" receipt_hint_swaps.py)
```

## Compare generated peer discussion with solo revision

Freeze the earlier DRC Experts paragraph as the opening draft. Give every writer the same official source card and ask for a corrected paragraph. Two targeted review passes precede the final synthesis in the solo, independent-drafts and interactive arms. The mandate review focuses on the dates and possible further action. The reporting review focuses on deadlines, recipients and updates. In the interactive arm the reporting desk receives the actual mandate memo and is asked to address relevant input. The solo analyst sees its own first review in its second pass. The independent reporting desk writes in isolation. One direct chair sees only the opening draft and source card at the same final cap.

| System | Final facts | New supported facts across working notes | Calls | Output cap / actual tokens |
| --- | ---: | ---: | ---: | ---: |
| Two-pass solo review | 7/7 | 1 | 3 | 244 / 203 |
| Independent drafts | 7/7 | 2 | 3 | 244 / 206 |
| Interactive desks | 7/7 | 1 | 3 | 244 / 196 |
| Direct revision | 7/7 | 0 | 1 | 116 / 98 |

All four finish and earn 14/14 on the original two criteria. The shared source card lets the direct chair fix both omissions in one call. The independent drafts alone supply both missing facts before synthesis. The interactive reporter echoes the first desk's proposed extension language and leaves the draft's recipient issue uncorrected. The final interactive chair recovers both facts from the available material, with no final fact exclusive to interaction. The independent final leaves out prior Committee discussion of the midterm report. This is a separate source detail beyond the original seven atoms, and the other three finals preserve it. [Transcripts and exact reviewed spans](deliberation-evidence/results.json)

This is a frozen-model process calibration on one exposed case. The three multi-call arms match call count and configured output capacity. Input and realized output costs differ. Every writer has access to the entire source card. The notes diagnose factual repair and duplication, with no private positions, policy concessions or negotiated outcomes. The annotations are from the same assistant. The ledger counts an echoed correction as observed reuse and requires absence in the solo and independent finals before attributing a unique improvement to the peer exchange.

The direct revision is 68 words against the requested 67-word cap. The three multi-call outputs are 64–65 words. The scores above are for factual coverage. The direct revision misses the length contract.

Cross the reporting desk's peer-note visibility with the explicit instruction to reply. The four reporter calls finish within their shared token cap. The two calls with the mandate note visible echo the mandate correction and leave out the Council recipient. The two without the note give the Council recipient and both deadlines. This holds under both instruction variants in this test. The follow-up calls use a separate generation batch, and this intervention ends at the reporting desk. [Two-by-two focus control](deliberation-control-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp deliberation-evidence/results.json <("$p" deliberation_score.py)
cmp deliberation-control-evidence/results.json <("$p" deliberation_control_score.py)
```

## Test the peer exchange with private source passages

Run the same protocol on DRC and UNAMI. Their pinned official joins match all 15 roll-call labels in both UNBench and UNSC-Bench. The DRC desk cards split mandate terms from the reporting clauses. UNAMI splits mandate and recurring reporting from the strategic review and consultations. The two desks never receive each other's raw passages. The independent and interactive reporting desk prompts are identical except for receipt of the actual first memo. The chair uses the same prompt, public vote and two available memos. It has no direct access to either source card in those arms. Both solo controls also use two working calls and a final call. The local solo has only the public vote, while the pooled solo has both source cards at every stage. All arms have a 236-token episode output budget and 112-token final cap. [DRC accession](accession.json) · [UNAMI accession and source dossier](../unami2023/README.md)

Use eight source assertions per docket. Give each chair credit when it states a historical fact supported either by a source card in view or by an actual memo from a desk entitled to state it. Check memo forwarding against the observed visibility graph. Score conflicts, length and completion separately. The source cards license the facts. The generated notes are the mechanism by which those facts can reach a chair. [Rubric and witnesses](private-deliberation-evidence/results.json)

| Docket | Local solo | Independent drafts | Interactive desks | Pooled solo |
| --- | ---: | ---: | ---: | ---: |
| DRC | 0/8 | 3/8 | 4/8 | 5/8 |
| UNAMI | 0/8 | 2/8 | 4/8 | 5/8 |

On DRC, the independent reporting note says the midterm report goes to the Committee. The interactive note names the Council, and the two final chairs preserve their respective notes. Both team finals turn the intended review deadline into a scheduled date. On UNAMI, the interactive note supplies the review's independence and Kuwait's inclusion in consultations, both preserved in its final. The two team finals both give the four-month cycle but omit the Council recipient required for full reporting credit. The pooled solo instead says quarterly and truncates. None of the eight finals clears the complete contract. Five of 14 working notes hit their cap. The interactive UNAMI reporting note finishes while the independent one truncates, so the one-pair contrast also includes cap effects. Input lengths differ across conditions.

These are two frozen-model cases with simulated document holdings and same-assistant exact-span review. The paired desk comparison identifies changes in the generated peer protocol on these cases. The newly preserved facts are drawn from the reporting desk's own card, so the result can reflect attention or improved reporting rather than transfer of those facts from the incoming memo. [Raw prompts, notes and final records](private-deliberation-evidence/transcript.jsonl)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp private-deliberation-evidence/results.json <("$p" private_deliberation_score.py)
```

## Raise the reporting cap and forward the source verbatim

Keep the mandate note, all reporter prompts and the 112-token final cap from the private-source test. Raise the reporting cap from 62 to 104 tokens for both desk conditions. In a separate arm, give the same chair both source-card groups verbatim in place of the generated notes. This presumes both source groups can be forwarded and uses one inference call. The two team arms have three calls and the same 278-token episode cap. [Archived prompts and generations](private-deliberation-cap-evidence/transcript.jsonl)

| Docket | Independent notes | Interactive notes | Verbatim forwarding |
| --- | ---: | ---: | ---: |
| DRC | 3/8 | 5/8 | 7/8 |
| UNAMI | 2/8 | 4/8 | 6/8 |

All four longer reporter notes finish. Both DRC reruns preserve their exact original 62-token prefixes. The independent note still directs the midterm report to the Committee. The interactive note names the Council and now completes the Committee update cadence, which its final retains. Both team finals still turn the intended review deadline into a scheduled date. The UNAMI reruns share prefixes of 35 and 58 tokens with the original independent and interactive notes. Batch composition changed between the original and extended runs, and the new UNAMI notes also differ before the original limit. The difference in final coverage persists, while the new independent final hits its own token cap.

Verbatim forwarding produces the strongest source-supported final records on these two dockets. It costs 88 DRC and 104 UNAMI model output tokens, compared with 241 and 234 for the interactive episodes. The one-call records finish within the word limit and have no marked contradictions. DRC omits the Committee discussion preceding the midterm report. UNAMI omits the Council as recipient of the recurring reports and strategic review. These gaps still fail the strict completeness contract. The verbatim test is a source-availability control and the forwarded material is the project’s accepted documentary excerpts. It places no length restriction on transmitting those excerpts. Source transmission and inference tokens are separate budget axes. [Review, prefix checks and exact replay](private-deliberation-cap-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp private-deliberation-cap-evidence/results.json <("$p" private_deliberation_cap_score.py)
```

## Compare generated notes and exact extracts under a common payload cap

Limit each desk's chair-facing passage to 48 Qwen tokens, measured on the actual visible text before JSON encoding. Use the same final prompt and 112-token generation cap. Compare the longest fitting source prefix, complete source sentences greedily packed in source order, two generated independent notes and two generated notes with a peer hop. Exact extractors use no reference labels or observed rewards. The generated arms regenerate notes with added instructions to avoid repeating the roll call and to keep actor and scope intact. Content is clipped at the transport boundary as needed. The interactive arm has the same chair-facing cap and one additional 44- or 48-token peer hop. [Protocol and archived messages](private-payload-evidence/transcript.jsonl)

| Docket | Token prefix | Complete sentences | Independent notes | Interactive notes |
| --- | ---: | ---: | ---: | ---: |
| DRC | 6/8 | 7/8 | 4/8 | 1/8 |
| UNAMI | 4/8 | 4/8 | 4/8 | 4/8 |

The DRC independent reporter fits four supported facts in 44 tokens. The interactive reporter repeats the mandate expiry supplied by the first desk and reaches the cap before completing a reporting fact. Its chair invents a requirement for the Group to submit a report for review by 1 July. The source prefix includes an unfinished updates sentence and its chair names the wrong recipient. The complete-sentence control avoids that error and preserves the Committee consultation preceding the midterm report. It delivers 78 payload tokens across two source messages and needs one inference call. The interactive arm transmits 136 payload tokens including the peer hop and uses three calls.

Both UNAMI extractors supply six source facts. Both chairs preserve four, dropping the Council recipient for the recurring reports and the separate strategic review. The generated notes tie the extractors on coverage, and their finals add unsupported claims about Iraqi support for the resolution and a reporting role for the chair, respectively. Every final finishes, and none meets all eight criteria. These are two exposed families with same-assistant review and fixed Qwen inference. The comparison to the previous run also changes the note prompt and regenerated notes. The comparison within this run uses matched limits and retains the observed additional peer traffic. [Per-arm payload and exact-span scoring](private-payload-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp private-payload-evidence/results.json <("$p" private_payload_score.py)
```

## Fit a joint policy to select verified excerpts

Use the four written-vote source slots for a new transport task. A public request names two priorities. Each desk privately holds two of four candidate excerpts and can send one. The second desk sees the first selection with probability 0.8. Each selection independently reaches the chair with probability 0.9. The peer hop costs 0.25 points. This models one truthful verified excerpt per desk rather than unrestricted wording. The reward gives seven points for each distinct card delivered, seven more per requested card and 14 more when both requested cards arrive.

Optimize both tabular policies for 180 exact policy-gradient updates on the uniform private roster distribution. Evaluate all six public requests over all 36 inventories. The stronger script exhaustively enumerates deterministic first-desk policies and chooses the best second-desk reaction for each local holding and observed message. Its known prior and unrestricted optimization over this finite decentralized action space provide a ceiling for the delivery reward. The greedy rule prioritizes requested cards and avoids repeating a received card when it can.

| Roster prior | Learned | Greedy with peer | Best independent | Optimized peer script |
| --- | ---: | ---: | ---: | ---: |
| Uniform fit prior | 25.263 | 25.135 | 23.415 | 25.293 |
| More shared holdings | 24.039 | 23.774 | 21.937 | 24.065 |
| More split holdings | 26.463 | 26.425 | 24.990 | 26.498 |

The trained policy's duplicate probability falls from 25.00% to 6.72% on the uniform prior. Under more shared holdings the frozen learner sends duplicates on 8.27% of episodes and the greedy rule on 10.26%. Erasing the peer message from the fitted pair drops the overlap-prior reward to 21.922 net points, before charging a peer hop. The gain over the greedy rule is small, and the known-prior script stays ahead. The optimization uses an authored excerpt-delivery reward and synthetic inventories. It supplies evidence for paid coordination under a precise bandwidth constraint. [Fit, local policies and exact scripted ceilings](evidence/payload-policy.json)

Replay the frozen extract policies through actual Qwen synthesis for the DRC docket. Use four verified excerpts covering mandate expiry, prospective review and extension action, the Council reports and monthly Committee updates. Every excerpt fits the same 48-token limit. The source-aware transport deduplicates identical cards before final synthesis. Generate one record for every terminal set of zero, one or two excerpts and retain all 11 outputs. The original delivery objective selects every route. Final evaluation counts both supported assertions and the original reward recalculated only for completely preserved fields.

| Overlapping inventories | Expected licensed assertions | Expected preserved assertions /8 | Preserved-field net | Finishes within limit and clears factual guard |
| --- | ---: | ---: | ---: | ---: |
| Learned | 3.480 | 2.976 | 19.767 | 43.30% |
| Same learner with peer absent | 2.937 | 2.618 | 18.846 | 54.47% |
| Greedy with peer | 3.382 | 2.945 | 19.955 | 40.62% |
| Best independent | 2.935 | 2.610 | 18.823 | 54.00% |
| Optimized peer script | 3.430 | 2.972 | 20.089 | 41.26% |

All 11 outputs finish and five clear the factual and scope guard. Two different pairs with the review passage turn prospective action into a mandated review and claimed past consideration. The review passage alone preserves both prospective review assertions. The learned pair's delivery-reward lead over greedy reverses on the same reward calculated from completely preserved fields. The extra peer message improves partial coverage against the same learner with its peer signal absent, while reducing the guard-cleared completion rate. Completed, guard-cleared records can still omit delivered facts. This replay uses one DRC source family excluded from fitting, simulated availability and same-assistant exact-span review. [Fixed writer, guarded fields and exact policy expectations](payload-policy-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp evidence/payload-policy.json <("$p" payload_policy.py)
cmp payload-policy-evidence/results.json <("$p" payload_policy_evaluate.py)
```

## Preserve legal force during synthesis

Keep all 11 previously generated DRC packet views, the frozen checkpoint, the 112-token output cap and the 73-word instruction. Change only the drafting instruction. It keeps each source clause separate and asks the chair to retain its actor, dates, recipient, exceptions, legal verb and tense. An absent packet must produce an explicit lack of additional evidence. Compare against the original writer and a deterministic renderer that copies each admitted excerpt in source order. The renderer checks that every record fits the same word and output-token limits. [Frozen prompt and generations](payload-writer-contract-evidence/transcript.jsonl)

The changed prompt preserves every fact supported by the delivered excerpts and clears all factual guards on 11/11 DRC outputs, up from 5/11. Both previously incorrect prospective-review combinations preserve the intended action. The prompt-specific presentation checks still fail on all six two-excerpt records, which use a single paragraph, and the review-only output repeats the public roll call. The factual guard, completeness relative to delivered evidence and presentation requirements are separate measurements.

On overlapping holdings, the frozen learned route recovers 24.039 net points on fully preserved fields, versus 23.774 for greedy and 24.065 for the optimized peer script. The three values exactly equal their respective delivery scores and their scores under deterministic rendering. Under the original writer they were 19.767, 19.955 and 20.089. Changing only the writer prompt recovers the learned delivery advantage over greedy on this DRC endpoint. Exact rendering attains the same factual result with no writer inference. The policy was frozen before both comparisons, holdings are simulated and the prose uses same-assistant exact-span review. [Original and new writer outcomes, fixed-route replay and exact-renderer controls](payload-writer-contract-evidence/results.json)

Transfer the same prompt unchanged to three UNAMI source views and run both writers in the same batch. The new prompt has the same factual coverage as the original on the full, recurring-and-review and review-only views at 6/8, 4/5 and 4/4. It removes the two marked legal errors. On the recurring-and-review view, the original names the Secretary-General as recipient after correctly saying recurring reports go to the Council. The revised prompt avoids the conflicting claim and still omits the Council as recipient of the strategic review. On the review-only view, the new prompt retains the request and the Council recipient, while the original promotes the request to a mandate. The full view still omits both Council recipients. The new outputs use 98, 71 and 33 tokens, versus 103, 98 and 78. All six finish. These three correlated views test transfer to one other exposed docket. [UNAMI transfer and matched spans](payload-writer-transfer-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp payload-writer-contract-evidence/results.json <("$p" payload_writer_contract_score.py)
cmp payload-writer-transfer-evidence/results.json <("$p" payload_writer_transfer_score.py)
```

## Learn when to pay for peer communication

Allow the first desk to skip the peer hop while still sending its chosen excerpt to the chair. The second desk observes either the excerpt or silence, which can reflect a skipped or lost signal. The two chair delivery legs and the peer delivery probability stay fixed. Run one joint fit over three public hop prices of 0.25, 1.5 and 4 points. The fit sees uniform private inventories. Reuse the 11 reviewed DRC records from the separate-clause writer and replay every policy through identical terminal outputs.

The exact planner considers all 4,096 deterministic first-desk strategies for each price and public request. For each strategy it picks the optimal second-desk action for every local holding and observation. Compare the planner using the true prior for each shift, a frozen planner fitted only on the uniform prior, the earlier mandatory-communication learner and two controls that randomize the decision to signal at the learned rate. The tighter random control keeps both the new sender's choice of excerpt in each private holding and the new recipient's policy. It breaks only the coupling between the first desk's state and its send decision.

| Evaluated inventories | Price | Learned send rate | Learned record net | Same policies with matched random sends | Uniform-prior script | True-prior script |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| More shared holdings | 0.25 | 83.0% | 24.081 | 23.661 | 24.106 | 24.106 |
| More shared holdings | 1.50 | 37.6% | 22.986 | 22.238 | 23.406 | 23.406 |
| More shared holdings | 4.00 | 32.7% | 22.133 | 21.370 | 22.374 | 22.448 |
| More split holdings | 0.25 | 83.0% | 26.511 | 26.197 | 26.539 | 26.539 |
| More split holdings | 1.50 | 37.6% | 25.682 | 25.047 | 25.490 | 25.731 |
| More split holdings | 4.00 | 32.7% | 24.877 | 24.214 | 24.787 | 24.990 |

The fitted team beats its earlier mandatory policy and both rate-matched random controls at every tested price and inventory prior. It beats the uniform-prior script in the two more-split settings at moderate and high prices. The true-prior script still leads everywhere. At the highest price under split holdings, that script sends nothing. The learned heads see each tested price during training. The altered roster priors keep the same local marginals, so the learned team's average send rates do not change between them. The learned team has no separate prior signal about how often desk holdings overlap.

This test measures when to transmit a verified excerpt under a charge. The replay uses the existing DRC output review and the specified simulated source holdings. [Single joint fit](evidence/optional-peer-policy.json) · [Matched-rate and frozen-script controls](evidence/optional-peer-controls.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cmp evidence/optional-peer-policy.json <("$p" optional_peer_policy.py)
cmp evidence/optional-peer-controls.json <("$p" optional_peer_controls.py)
```

## Compare a receipt acknowledgment with a planned send

Reuse the two-excerpt policy interface and test it against the reviewed UNAMI handoff. Each desk privately holds two of four candidate slots and sends one. A public target pair designates the review and recurring report. The other two slots represent competing inventory and contribute no UNAMI text or points. Before the second desk sends, it may observe the first slot through an 80% side channel. Compare a message about the first desk's choice with an acknowledgment emitted only when that choice reaches the chair. Each chair leg succeeds independently with probability 0.9 or 0.7. The first desk cannot resubmit, and the second desk cannot send two clauses.

Use the same strict reward in both protocols. Award 28 points for delivering both target slots and zero otherwise. Count side messages and ordinary record points separately. A planned send and an acknowledgment have the same effect on strict completion under a fixed policy here. In every successful two-slot delivery, the first delivery must already have succeeded. The two side channels differ only in worlds where that first delivery fails, so they can change partial records and traffic. Under the two receipt operations the reviewed UNAMI remainder gives 35 points with neither receipt, 42 with either one, and 49 with both.

Enumerate all 64 first-desk rules and optimize the second desk's local reply for each one. With 90% chair delivery, the strict headroom above the exact silent control is 3.60 percentage points on uniform inventories and 3.32 points under both overlap and split shifts. Train once on uniform abstract inventories under the acknowledgment protocol, with 180 exact updates over 1,836 weighted traces and 216 policy states. The endpoint during fitting is abstract pair delivery. The UNAMI records are replayed afterward.

| Full two-obligation handoff, 90% chair link | Uniform | Overlap shift | Split shift |
| --- | ---: | ---: | ---: |
| Learned with acknowledgment | 32.76% | 28.17% | 37.48% |
| Same learned policy, observation erased | 29.17% | 24.86% | 34.17% |
| Prior raw-score policy with planned send | 32.74% | 28.16% | 37.46% |
| Exact with acknowledgment | 32.85% | 28.25% | 37.59% |
| Exact without peer observation | 29.25% | 24.92% | 34.27% |

The learning change contributes at most 0.02 percentage points over the earlier fit in these conditions. The useful intervention is observing the other desk's choice. On split holdings the exact acknowledgment and silent controls both score 44.05 ordinary record points despite their different full-handoff rates. For the same new learned policy, switching from planned sends to acknowledgments reduces side-message attempts by 10% at the design link or 30% at the weaker link and preserves strict completion. At the weaker link and split holdings full handoff is 22.67% with learned acknowledgments versus 20.67% with their contents erased. These results use simulated holdings and links and a fixed reviewed UNAMI composer. They establish a structured information effect and leave conversational deliberation and record release unmeasured by this fit.

The first replay attempt looked up replies on zero-probability branches of a deterministic script. Skipping those branches resolves the error. The fit is deterministic and the inputs, optimizer and initialization were unchanged on retry. A separate calculation conditioning on both chair deliveries reproduces the strict rates. [Policy, replay and exact headroom](receipt-ack.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" receipt_ack.py --headroom
"$MODEL_PY" receipt_ack.py
```

## Turn receipt prose into a routing action

Use the UNAMI packet witnesses for REVIEW and REPORT and the archived TERM and CONSULT summaries. The public target is REVIEW plus REPORT. Compare nine message conditions. Four say the chair has received the attached passage. Four attach the same passages but say delivery is planned and unconfirmed. One has no message. The receipt-status wrappers are authored controls. The REVIEW body is the actual Qwen actor reply's first sentence.

Score frozen Qwen3.5-4B on two tasks. On the first, identify the confirmed field or report no confirmed receipt. On the second, given both local cards, choose which one to send next. Rotate the labels twice in each condition. A decoder disagreement defers to the no-receipt policy. Direct action replay randomizes equally over the two label orders and breaks a numerical tie uniformly. With the first desk's learned policy fixed, replay the measured choices under the overlap and split rosters and the existing delivery model. Compare with the same learned receiver given the exact typed receipt. Score complete handoff and correct calendar recovery separately from 70-point record coverage. The composer remains the fixed reviewed no-question UNAMI remainder. [Source clauses and assembly](../colombia2023/unami-verbatim.json)

| Complete UNAMI handoff at 90% chair delivery | Overlap holdings | Split holdings |
| --- | ---: | ---: |
| Learned recipient receives typed receipt | 28.17% | 37.48% |
| Learned recipient uses the Qwen decoder | 24.86% | 34.17% |
| Same recipient, receipt erased | 24.86% | 34.17% |
| Qwen chooses from prose directly | 17.84% | 29.04% |
| Same Qwen chooser, receipt erased | 20.75% | 33.19% |

The decoder agrees across both label orders for only one of the four confirmed fields, REVIEW. It correctly withholds confirmation in all five planned or absent controls. REPORT is recognized under one label order and missed under the other. The [replay with corrected decoder entries](receipt-ack-language-evidence/counterfactual.json) restores the typed completion rates by fixing only the REPORT entry. Fixing TERM and CONSULT alone has no material effect. This is an intervention on archived classifier decisions.

The direct action disagrees between label orders or ties on 16 of 54 conditions. When it holds both target clauses and the chair confirms REVIEW, it still selects REVIEW in both orders. Exposing a planned statement in a first-delivery failure slightly lowers the direct model's partial record score and leaves the full-handoff metric unchanged by construction. With the learned recipient, the decoded split record averages 44.04/70 and completes in 34.17% of episodes. The typed form averages 44.03/70 and completes in 37.48%. The aggregate rubric still misses the most consequential loss.

The 126 evaluations score legal next tokens. They use known local choices, one historical docket, authored receipt wrappers and simulated packet delivery. They do not test an unconstrained conversational policy. The first launch stopped before inference because the shared runner was outside the script's import path. The corrected launch used the intended frozen prompts. [All prompts, decisions, and exact replay](receipt-ack-language-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" receipt_ack_language.py score receipt-ack-language-evidence
"$MODEL_PY" receipt_ack_language_repair.py
```

## Read receipt status and clause identity separately

Use the same four UNAMI excerpt bodies and the exact DRC excerpts for the Council midterm report, monthly Committee updates, mandate expiry and prospective review. The DRC docket was previously used for other tasks and is new to the receipt-reading test. Use the earlier UNAMI wording and distinct DRC envelopes. For each docket test four confirmed receipts, the same four passages framed as planned sends, one silent condition and one acknowledgment withdrawn after the fact.

The single-call reader sees the full envelope and the same descriptive field labels as the separate reader. The separate protocol classifies the current receipt status from the whole message and classifies the field from the excerpt alone. It releases a slot only if both labels are stable across two answer orders and the receipt is current. The harness supplies the excerpt boundary. Replay the resulting slot on the frozen learned selector. UNAMI uses the archived assembly and its record scores. The DRC case tests how the slot decisions affect the abstract completion event using the same roster and link assumptions.

| Stable decisions | UNAMI confirmed fields /4 | DRC confirmed fields /4 | Planned, absent or withdrawn receipts rejected /12 |
| --- | ---: | ---: | ---: |
| Read status and field separately | 3 | 3 | 12 |
| Read both together with descriptive labels | 2 | 3 | 12 |

The status read is correct in both label orders on all 20 envelopes. The separate field reader disagrees between orders on the UNAMI consultation clause and the DRC mandate expiry. The joint reader mislabels the DRC expiry as the prospective review and refuses the UNAMI expiry receipt. Both approaches read the target pairs correctly. They recover 28.17% and 37.48% complete handoff in the UNAMI overlap and split replays, equal to the typed receiver on that metric. The earlier label-only reader reached 24.86% and 34.17%. The one-call reader with descriptive labels recovers the same target-pair gain as the two-stage reader, so that gain cannot be attributed to the two-stage split alone. Partial record and calendar scores differ when the readers lose or mislabel a competing slot.

Both readers reject the withdrawn acknowledgments here. The negative controls cover the specified wording. They do not establish robustness to forged receipts or arbitrary envelopes. These are 96 frozen next-label calls across two exposed document families. The field menus and boundaries are provided. Test new phrasing and competing clauses before using the result as a semantic intake guarantee. [Per-order decisions, held-out-to-pilot DRC contrasts and exact replay](receipt-ack-binding-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" receipt_ack_binding.py score receipt-ack-binding-evidence
```

## Score DRC receipt decisions through the actual writer bank

Replay the previous DRC receipt readers over all six public pairs of documentary clauses. Use verified card IDs for what reaches the writer. The model's receipt interpretation changes only the receiving desk's choice. Keep the first desk's learned policy, private inventory distributions and 90% chair link fixed. Score each packet through the earlier original writer, separate-clause writer and verbatim renderer. The bank consists of eleven actual receipt patterns. A successful target handoff preserves every fact in both requested clauses and passes the existing source, length and completion checks for the supplement. This endpoint does not require the rest of the DRC record.

For the requested reports and periodic updates, all three writers preserve both Council report dates, the Council recipient, prior Committee discussion and monthly Committee updates with the two report-due months excepted. The typed, single-read and separate-read routes all complete 37.48% on split holdings, compared with 34.17% after erasing the message. The scripted peers reach 37.59% and the exact independent script reaches 34.27%.

On split holdings, change the request to include mandate expiry. The single reader mislabels the expiry receipt as a prospective review. Its complete-delivery rate falls to 30.87% with either reports or updates as the second target and to 29.21% when the second target is review itself. The separate reader defers on the same receipt and reaches 34.17% on each of those pairs. The typed policy remains at 37.48%. Scoring all six pairs exposes the ancillary error that the original two-target test could not detect.

| Mean first-pass DRC target success, split holdings | Original writer | Separate-clause writer | Verbatim renderer |
| --- | ---: | ---: | ---: |
| Typed learned routing | 12.49% | 37.48% | 37.48% |
| Single receipt read | 11.39% | 33.90% | 33.90% |
| Separate receipt reads | 11.94% | 35.83% | 35.83% |
| Learned routing with the observation erased | 11.39% | 34.17% | 34.17% |

The original writer fails four of six two-clause target packets even if both arrive. For mandate and review it ties reporting requirements to the two dates. On the review packets paired with reports or updates it turns a future intention into a mandated review. Those are recorded failures in the earlier same-assistant review. For the separate-clause writer and verbatim renderer the needed facts survive on all six complete packets. The end-to-end gain therefore depends both on correct routing and on preserving legal force in the finished record.

Use the table as exact replay on frozen DRC outputs, with no new writer generations and simulated rosters and links. The full DRC record and open-ended deliberation remain outside this endpoint. [Per-pair records, old failure spans, and delivery scores](receipt-ack-drc-replay.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_ack_drc_replay.py
```

## Distinguish an enacted expiry from a prospective review

Use the original DRC expiry and review clauses, then reverse their dates without changing the legal verbs. Add clauses containing both acts, neither act, and explicit negations. On Colombia, use the actual extension and willingness to work on a later extension, together with paraphrases and controls. The alternate wordings are evaluation probes. They are not historical replacements.

Compare a four-way classifier with two independent questions about whether the text establishes an operative extension and whether it establishes prospective consideration. Both methods receive the same definitions and two answer-label orders. The composed decision requires a stable answer to both questions. For the receipt replay, retain the earlier status and non-mandate reads and replace only the two mandate-related field classifications from authentic DRC excerpts. Use the exact frozen DRC writer bank and reporting obligations. No new source clauses are admitted by the synthetic contrasts.

| Stable correct over both label orders | DRC /8 | Colombia /6 | Deferrals /14 |
| --- | ---: | ---: | ---: |
| One four-way decision | 3 | 2 | 9 |
| Two independent legal-act decisions | 2 | 1 | 10 |

The four-way reader preserves the authentic enacted expiry and its date-swapped version. It defers on both prospective DRC clauses and all earlier or later variants that combine or negate the two acts. The two-question reader defers on the authentic DRC expiry and review and mistakenly credits only prospective review when both are present. Neither classifies the authentic Colombia willingness-to-work clause consistently. Correctness on both enacted dates in the direct read establishes a limited result about this actor and wording, with no corresponding general result on future authority.

Replay both new approaches using the earlier separate receipt reader for all other fields. On split holdings, the four-way replacement recovers 37.48% for reports plus expiry and updates plus expiry, up from the previous separate reader's 34.17%. But reports plus prospective review and updates plus prospective review both fall from 37.48% to 34.17%. The two-question replacement loses the review gain and fails to recover the expiry gain. The DRC legal-force writer still preserves every complete two-clause packet, so these shifts come from the receipt reader. No full-record recomposition or additional training is involved.

The run used 84 frozen Qwen3.5-4B next-label evaluations. The archived source clause boundaries are supplied. Colombia was previously exposed in the project and first used here to test this classifier. This result measures where errors move when both fields change together. It leaves the historical receipt decoder in place. [Passages, per-order choices and exact writer replay](receipt-force-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_force.py score receipt-force-evidence
```
