# Colombia verification mandate renewal

The Council unanimously adopted the United Kingdom's S/2023/808 on 30 October 2023 as resolution 2704. It renewed the UN Verification Mission through 31 October 2024. The preamble recalls existing verification authority for the Government–ELN ceasefire and expresses willingness to consider verification of the Government–EMC ceasefire subject to confirmation, suitable protocols and the implementation update. Ghana spoke on behalf of the three African Council members. The presiding representative then spoke for Brazil in his national capacity. [Official meeting](https://digitallibrary.un.org/record/4025984) · [Adopted resolution](https://digitallibrary.un.org/record/4025676)

[Accession](accession.json) confirms all 15 recorded votes against the official meeting and UNBench author-test event 2504. The event has zero matches in the UNBench author train split. Both pinned UNSC-Bench configurations were searched by draft, meeting, resolution or date and have no matching row. This is complementary coverage for the broader benchmark, whose Iraq and other dockets already use both collections. It is the first matched project run on this docket. Prior exposure in model pretraining is unknown.

## Matched drafting

Two historical source analysts work from the common Council records and their assigned Brazil or A3 summary. They make an opening note and a revision. The independent and interactive arms share the same opening notes. In the interactive arm the other analyst's opening is visible at revision. The pooled solo analyst sees every source and its two opening notes at revision. All final writers see the same full dossier and two provisional revisions. The five-call output ceiling is 716 tokens for every arm. Actual input lengths differ. The analysts provide retrospective working notes in generated prose.

| System | Final record out of 70 | Key points out of 10 | Arguments out of 10 | Peer interactions out of 10 | Distinct ideas by working slot |
| --- | ---: | ---: | ---: | ---: | --- |
| Pooled solo | 14 | 4 | 4 | N/A | 2, 5 |
| Independent drafts | 21 | 6 | 6 | N/A | 4, 5 |
| Interactive | 21 | 6 | 6 | 0 | 4, 5 |

Each arm has four working turns and one synthesis. All ten unique working generations hit the 112-token cap. The solo final also hits its cap, and its synthesis attributes a shared requirement for mature verification protocols to both statements. Both team finals complete, but reverse the A3 speaker relationship. They write that the African members spoke on behalf of Ghana. All three have a material guard failure. All three preserve the disposition and term. The two team records retain Brazil's hope for later authorization, and all three lack enough detail to earn the complete EMC condition criterion. The brief mention of the implementation update in the solo answer does not clearly identify it as an input to Council consideration.

No tracked idea in the interactive revisions appears in the peer's opening while also being absent from the writer's own opening and paired independent revision. Brazil's sovereign-will statement in the interactive Brazilian revision is supported by its own dossier. The A3 reversal is first observed in the final texts. Neither correct working-note provenance nor peer exposure prevents an attribution error at synthesis.

The 70-point results come from a same-assistant exact-span review. The additional process rubric counts only identified material ideas and argument links. Its aggregate adds no cross-condition advantage for having a communication channel. [Full records](evidence/final-records.json) · [Review and process measurements](evidence/results.json) · [Transcript rubric](transcript-rubric.md)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" run.py check
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" run.py replay evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" score.py
```

## Authority and speaker-relationship judge

The source-blind candidate-reading pattern used for Iraq was applied here with new case-specific menus. Freeze the menus before inspecting the final records. Supply only verbatim candidate excerpts and permute semantic answer labels across two calls. Test the complete anchor and four single-edit foils, then grade three authority and attribution fields in each actual record. The complete reference fits in 151 words.

The judge gets four of seven authored checks and zero of nine actual checks. The actual panel contains seven omissions and two contradictions under the exact-span review. The judge grants six unsupported credits and defers three. It accepts both actual reversals of Ghana's speaker role and the authored foil that changes willingness to consider into authorization. It catches the authored promotion of the Brazilian statement to the Council presidency. These failures distinguish complete historical action, missing prerequisites and reversed attribution. The case-specific judge remains a diagnostic. Training would reward the identical Ghana reversal in both team finals.

All 13 writer prompt and output-token sequences and 32 judge prompt and label encodings replay exactly. Base-model scores are frozen inference. The source join and judgment label arithmetic reproduce independently of generation. [Authored controls](anchor-controls.json) · [Judge decisions and deferrals](judge-evidence/results.json)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" authority_judge.py report judge-evidence
```

## Compact notes with the same final prompt

Replace only the working-note instructions. Ask for 25–40 words without headings, put the assigned statement and its speaker and represented party first, and retain one material qualification. This intervention combines brevity with attribution priority. The original 112-token note cap, 268-token final cap, source access, stage graph, final synthesis instructions and frozen checkpoint all stay fixed. Input text at synthesis changes only through the generated working notes.

| System | Original final out of 70 | Compact-note final out of 70 | Original and compact output tokens | Compact final complete |
| --- | ---: | ---: | ---: | --- |
| Pooled solo | 14 | 28 | 716, 446 | No |
| Independent drafts | 21 | 28 | 712, 460 | No |
| Interactive | 21 | 28 | 701, 463 | Yes |

All ten notes end before the cap after the intervention, up from zero. All three finals correctly report that Ghana spoke for the African members. The two team chairs receive exactly the same A3 note. The independent Brazilian revision says Brazil’s representative spoke for Colombia, and its final repeats that error. The interactive revision and final preserve Brazil as the speaker’s national role. The paired final prompts differ only in their Brazil note. There is no tracked idea newly taken from the peer’s opening. A role difference in revision can change the final without any new source fact arriving from a peer.

The compact interactive final preserves the Council’s willingness to work on a further mandate extension based on agreement between the parties. The solo and independent finals preserve the A3 Ethnic Chapter priority. All three still fail the source guard. They merge the two distinct national positions into claims of stronger common ground. The compact solo final also exceeds 185 words and the two noninteractive finals truncate. This is a same-docket prompt intervention with same-assistant exact-span review. [Matched comparison](compact-evidence/comparison.json) · [Unedited records and process replays](compact-evidence/results.json)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" compact.py check
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" compact.py replay compact-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" score.py --evidence compact-evidence --annotations compact-annotations.json
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" compact_compare.py
```

## Chair-only attribution controls

Start from the compact interactive chair. In one run, change only the A3 note's opening phrase so the African members speak for Ghana. The unaltered documentary source still gives the correct direction. The chair repeats the reversal and hits its cap. It stays at 28/70 because it loses the A3 attribution and gains the Ethnic Chapter criterion. The equal point total hides a new material error.

In the other run, remove both notes and keep the full dossier, instructions and chair output cap. The chair completes at 35/70, preserves both the Brazilian hope for later authorization and the A3 Ethnic Chapter commitment, and correctly identifies Ghana as speaking for the African members. It still fails the source guard by overstating the precise conditions shared by Brazil and the A3. This one-call control has a smaller budget than the five-call pooled analyst. [Chair-only records and score](intervention-evidence/results.json)

All 15 new prompt and output-token sequences replay exactly. Neither the prompt intervention nor the chair-only controls use new optimization. The evidence distinguishes note completion, transport of an attribution error and the validity of the final judgment.

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" note_intervention.py replay intervention-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" intervention_score.py
```

## Check source relationships before using working notes

Keep the original documentary cards and output cap. The instruction-only condition explicitly asks the chair to use documentary authority, verify both directions of speaker attribution and check for overstatement of agreement. It sees the reversed A3 note. The matched ledger condition sees exactly the same task and notes plus structured fields for the historical decision and statements. Each field is anchored to an exact passage in its frozen documentary summary. The ledger is authored by the same reviewer. The model has access to the correct original facts in both conditions.

| Chair input | Final out of 70 | A3 speaker direction | Source guard clear | Output complete |
| --- | ---: | --- | --- | --- |
| Source-priority instruction, reversed A3 note | 35 | Reversed | No | No |
| Source ledger, reversed A3 note | 35 | Correct | No | No |
| Source ledger, wrong Brazil and A3 notes | 28 | Correct | No | Yes |
| Source ledger, clean note inputs | 42 | Correct | Yes | No |

With both wrong notes present, the ledger chair identifies Ghana as speaking for the African members and Brazil as speaking nationally. The independent Brazil revision is the actual donor for that treatment, while the A3 reversal is an exact substitution in the interactive revision. Baseline slot IDs in the generation metadata represent the parent plan. The score artifact verifies the literal input text and actual Brazil donor ID separately. The dual-conflict record still combines country-specific conditions into a shared position. The clean ledger variant passes the semantic guard and stops before completing its last sentence, so it also fails release. [Ledger source links](provenance-ledger.json) · [Raw record scoring and attribution trace](provenance-evidence/results.json)

## Transfer with a verified record endpoint

The complete 151-word authored reference can be assembled by source ID. The verified bank covers all 16 subsets of four optional cards. Adding a valid card never reduces its record score, and the scoped Brazil–A3 comparison requires the two statement cards plus the resolution's authority paragraph. The roll call is always available. All 16 records fit within 185 words.

The three-contact transfer freezes the previous written-vote MARL weights, preserves the design distribution over hidden rosters and evaluates all 24 source aliases. The script controls select their best fixed or receipt-dependent contact policy using the new source rubric. With no public alignment, the frozen team averages 17.624 net points over the protected anchor. With alignment to public proof gains it reaches 19.117, compared with 18.606 for the best fixed script and 19.161 for the best adaptive script. The aligned route gives 40.55/70 expected record points and covers the three required cards in 42.52% of the synthetic trials. This is a transfer of the learned receipt policy through authored records. The generated-chair failure modes are measured separately. [Verified record bank](verified-bank.json) · [Exact transfer and script baselines](verified-transfer.json)

## Keep conditions local to the statement that made them

The two follow-up chairs receive the same ledger and the same wrong Brazil and A3 notes. Both get a 145-word target within the original 268-token cap. One only gets the shorter target. The other also gets an ordered plan for the decision, prior and prospective authority, the two national accounts, and their narrowly stated overlap. The overlap instruction leaves exact conditions in their respective accounts.

| Prompt | Final out of 70 | Word count | Both attributions correct | Complete | Source guard clear |
| --- | ---: | ---: | --- | --- | --- |
| Short target only | 35 | 176 | No | No | No |
| Short target with separate accounts | 49 | 134 | Yes | Yes | No |

The second output preserves the scope of common ground and the statement that resolution 2704 did not grant EMC verification. It then says the matter is left to the Secretary-General's update. The resolution sets a confirmation condition with appropriate verification protocols and says to take the update into account. The final record compresses those requirements incorrectly. It also uses six paragraphs where five were requested. The intervention improves a specific writer failure, while the complete authority criterion and strict record still fail. [Completed outputs and exact review](structured-evidence/results.json)

```bash
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" provenance_chair.py replay provenance-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" provenance_score.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" structured_chair.py replay structured-evidence
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" structured_score.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" verified_bank.py
PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" verified_transfer.py
```

## Specialist desks and an unreliable desk label

The original transfer assumes symmetric two-card holdings. Tilt the hidden-roster distribution toward a specialist desk by multiplying each world's original probability by a fixed factor for each missing source held by that desk, then renormalize. A separate condition favors different missing sources at the two desks. All actors retain the same three-contact limit, fees, losses and verified record endpoint. The public hint names the specialist desk. It supplies no private holdings or odds. The original aligned policy matches its previous result when the tilt is one.

Fit once on the written-vote docket with a threefold factor, using 180 joint gradient updates over 12,108 enumerated trajectories and 330 requester and responder states. The target dockets and the tested weak, strong and split roster priors are excluded from fitting. A scalar replay using the independently enumerated terminal receipts matches all fitted metrics. In the strong transfer condition the specialist is on the opposite desk, with a sixfold factor. The policy can use the same public label to order the desks.

| Strong specialization, net gain | UNAMI | UNIFIL | Colombia |
| --- | ---: | ---: | ---: |
| Original aligned team | 16.183 | 21.140 | 22.831 |
| Specialist-trained joint team, correct label | 16.534 | 21.618 | 23.333 |
| Specialist-trained joint team, wrong label | 15.128 | 19.671 | 21.266 |
| Registry-order fixed script, true prior | 16.409 | 21.511 | 23.142 |
| Fixed script with optimized reply order, true prior | 16.651 | 21.994 | 23.142 |
| Adaptive script with optimized reply order, true prior | 16.885 | 22.337 | 23.486 |

The stronger script chooses which of two eligible cards a desk sends first, per public case, and uses the same request IDs and contact limit. It sees the true roster prior. This closes the apparent learned advantage on UNAMI and UNIFIL and leaves a gain of 0.192 on Colombia with the correct hint. The learned requester loses part of its gain when its counterpart is replaced with a canonical responder. Training for one specialist also lowers scores on the original symmetric and the split-specialty conditions relative to the original frozen team. [Frozen shift](roster-shift-results.json) · [Joint update and component swaps](specialist-fit-results.json) · [Optimized script controls](specialist-script-results.json)

For the same physical worlds, combine correct- and wrong-hint returns at specified hint reliabilities. The break-even accuracies against the old frozen team are 75.03% on UNAMI, 75.45% on UNIFIL and 75.71% on Colombia under strong specialization. The threshold calculated solely from the written-vote fit is 70.49%. Deploying at that threshold underperforms the frozen team on all three transfer cases. The Colombia specialist needs about 90.73% reliability to beat the stronger fixed script. Even perfect reliability is insufficient on the other two cases. These are expected returns under assumed metadata accuracy and simulated desk assignments. [Hint calibration and sensitivity](specialist-hint-results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" roster_shift.py
"$MODEL_PY" specialist_fit.py
"$MODEL_PY" specialist_hint.py
"$MODEL_PY" specialist_script_control.py
```

## Replay the specialist team through a generated record

Generate a single frozen Qwen body for each of the 14 reachable nonempty source subsets. Supply the underlying source summaries, their structured documentary fields, and the original compact interactive revision for each delivered national statement. A source and its note are withheld together when it is absent. The roll call is an authored prefix. Each route uses the same generated body for the same packet with a 216-token output ceiling. The specialist policy and the stronger script plans use verified authored scores as before. They are frozen before the generated records are scored.

| Strong specialization with correct desk label | Licensed record points | Actual record points | Release probability | Expected released points |
| --- | ---: | ---: | ---: | ---: |
| Original frozen team | 44.32 | 34.63 | 53.80% | 17.25 |
| Specialist-trained team | 44.82 | 34.95 | 54.52% | 17.52 |
| Specialist with canonical replies | 44.21 | 34.59 | 55.18% | 17.56 |
| Best fixed script with optimized reply priority | 44.63 | 34.90 | 54.85% | 17.62 |
| Best adaptive script with optimized reply priority | 44.98 | 34.92 | 55.37% | 17.78 |
| Solo with all three target cards | 50.75 | 38.50 | 50.00% | 17.50 |

The specialist's net actual gain over the protected record is 15.213, against 15.164 for the fixed script and 15.183 for the adaptive script. The comparison is effectively narrow on raw points, and both scripts yield more expected points on releasable records. The wrong desk label lowers the specialist to 33.66 actual points, compared with 34.63 for the original frozen team. Under the same physical roster distribution, the realized break-even accuracy against the stronger fixed script goes from 90.73% on authored records to 96.13% with this writer.

Six of 14 generated records clear the factual guard, citation-ID, length and completion checks together. The three single-source OPERATIVE, BRAZIL and A3 bodies assert that the resolution granted authority for EMC. The ADDITIONAL singleton omits its required source ID. The writer preserves the A3 attribution and Ethnic Chapter criteria in all seven packets that contain that statement, but retains Brazil's full capacity-and-government-priorities criterion in three of seven. The only packet containing both national positions and the authority paragraph overstates their common conditions and truncates. [Generated records and expected route outcomes](receipt-evidence/results.json)

A posthoc modular control joins the four genuinely generated single-source bodies according to each receipt and can append one authored comparison when both national accounts and the authority clause support it. The modular control gives the specialist 39.11 raw record points at an average 2.62 writer calls, and every assembled record fails the release checks because every singleton fails at least one. It tests error propagation by composition with a different generation budget. [Modular control](receipt-evidence/composition.json)

On two failed packets, replace the generic instructions with a shorter task naming only the delivered scope. The A3-only retry stops claiming Council authorization and passes the release checks. It says Ghana represented the African members and preserves their procedural condition, but omits EMC as the object of support. Its raw score falls from 21 to 14. The three-source retry completes and still combines both delegations' conditions into one. Its raw score falls from 35 to 14 and it remains unreleasable. Substituting only these two outcomes while keeping all router choices fixed adds 0.54 percentage points to the specialist's release rate and reduces raw score by 3.41. This is a targeted posthoc diagnosis. [Scope-specific retry and exact reweighting](receipt-scope-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" receipt_chair.py replay receipt-evidence
"$MODEL_PY" receipt_outcomes.py
"$MODEL_PY" receipt_composition.py
"$MODEL_PY" receipt_scope_probe.py replay receipt-scope-evidence
"$MODEL_PY" receipt_scope_score.py
```

## Generate documentary clauses separately

Keep the writer's checkpoint, the delivered source summaries, the original role notes and the learned route probabilities. Generate a separate short field for each delivered source. A fifth field covers limited shared ground and requires the authority source and both statements. The chair adds no new text when concatenating completed fields with the authored vote line. The comparison has its own single-call diagnostic and receives no access when a required source is absent.

The first five generated fields assemble into 13 of 14 releasable packets under the existing checks. The specialist's expected release rate rises from 54.52% to 83.93%, and expected released points rise from 17.52 to 28.90. Its raw score falls from 34.95 to 34.52. The legal field omits ELN verification, and the Brazil field leaves out who expressed Colombia's priorities. The comparison still combines Brazil's maturity condition with the A3's reference to the Secretary-General. [Initial generated fields and replay](field-evidence/results.json)

The first revision recovers the Brazil proof. Restricting the comparison input to the broad conditional position shared by both statements and the legal status prevents it from merging national conditions. This restricted input is an authored projection of the source fields. The same revision recovers prior ELN verification but assigns willingness to consider new authority to the Mission. In a follow-up, the explicit Council subject removes that error while a subordinate clause assigns consideration of the update to the Secretary-General. Preserve both rejected outputs in the audit. [First revision and raw replays](field-revision-evidence/results.json) · [Explicit actor trial](field-authority-evidence/transcript.jsonl)

Give the Council's consideration of the update a separate sentence with an explicit Council subject. The final legal field preserves all three propositions. Resolution 2694 already authorized ELN monitoring and verification. The Council expressed willingness to consider EMC monitoring and verification after the specified confirmation. The Council would take the Secretary-General's update into account. The successful comparison names the resolution and preserves the broad conditional position without supplying identical prerequisites for both delegations.

Assemble the five reviewed fields from the initial and follow-up generations. All 14 reachable packets now preserve every criterion licensed by their received evidence and clear the factual and form checks. Their maximum length is 156 words. This component selection uses same-assistant review after inspecting this docket's failures. The roll call is still authored. Every other sentence is unchanged model text.

| Strong specialization with correct desk label | Whole-packet score | Selected-field score | Selected-field release |
| --- | ---: | ---: | ---: |
| Original frozen team | 34.63 | 44.32 | 100% |
| Specialist team | 34.95 | 44.82 | 100% |
| Strong fixed script | 34.90 | 44.63 | 100% |
| Strong adaptive script | 34.92 | 44.98 | 100% |
| Solo with all three target cards | 38.50 | 50.75 | 100% |

The specialist uses 2.78 writer calls per packet, against one in the original run. Mean input increases from 612.42 to 834.49 tokens and mean output falls from 188.53 to 141.92. Even the longest assembled output uses 200 generated tokens, though the separate-call setup permits a higher combined output ceiling. These figures describe the measured replay. The gain from this selected library requires a fresh docket and independently specified acceptance checks before claiming generalization. [Selected fields, every packet, and frozen policy results](field-update-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" field_writer.py replay field-evidence
"$MODEL_PY" field_revision.py replay field-revision-evidence
"$MODEL_PY" field_authority.py replay field-authority-evidence
"$MODEL_PY" field_update.py replay field-update-evidence
"$MODEL_PY" final_field_outcomes.py
```

## Transfer separate documentary drafting to UNIFIL

Apply the Colombia method to an earlier UNIFIL docket, using the existing 70-point final-record rubric and a shared authored vote line. Freeze the first-pass prompts with no variant selection. Compare a single call per source packet with independent documentary paragraphs assembled in the same order. Add a comparison paragraph only when both Brazilian and Chinese statements were received. Both methods receive the same set of source passages per packet and the same aggregate generation ceiling, with 78 tokens per documentary paragraph and 55 for the comparison. The single call can redistribute this budget across paragraphs. Individual calls see only the sources needed for their requested paragraph, so input visibility and call counts differ. The generation batches group requests by output ceiling. The two paths share the original singletons' prompt and token budget.

Use seven points for each fulfilled criterion and label unsupported statements with exact spans. Require all licensed criteria, no flagged unsupported claims, completed generation and the requested citations and paragraph limits to release a record. The licensed maximum depends on the received packet. Distinguish content score, release, and expected cost. Pass every reachable packet through the same frozen writer bank for each method. Replay the two previously fitted policies, a canonical responder swap and the prior-aware optimized fixed and adaptive scripts. Pooled writing has all three target cards in each request scenario. Message priors and roster allocations are simulated.

The launch runner initially rejected mixed output ceilings before generation. The completed run groups requests by ceiling and keeps the planned prompts and output budgets.

| Frozen route | Whole record points | Separate record points | Whole net gain | Separate net gain | Full-target release with either writer |
| --- | ---: | ---: | ---: | ---: | ---: |
| Specialist joint | 38.01 | 39.40 | 14.785 | 16.171 | 14.69% |
| Specialist with canonical replies | 36.98 | 38.70 | 13.763 | 15.482 | 13.82% |
| Optimized fixed script | 38.27 | 39.80 | 15.036 | 16.567 | 15.73% |
| Optimized adaptive script | 38.66 | 40.00 | 15.416 | 16.757 | 16.28% |
| Pooled three-card view | 43.75 | 43.75 | 21.000 | 21.000 | 25.00% |

All 19 frozen Qwen3.5-4B generations ended before the token cap. The separate operative paragraph preserves the mandate date, independence without prior permission, and the ongoing obligation to coordinate with Lebanon's Government under the status-of-forces agreement. Five whole-packet records omit the Government as counterpart, and one of those omits the date as well. The separate Brazil paragraph drops **some** from Brazil's assessment of Lebanon's concerns. Every whole-packet result containing that statement also misses the full Brazil criterion, either dropping the qualification or describing the French text itself as free instead of saying it allows the mission to operate freely. The one-call drafts state the qualified contrast in all three Brazil–China packets. The separate comparison gives the shared position on the mission but does not state Brazil's side of the contrast or cite the two sources.

Separate drafting increases the number of releasable packets from 4/14 to 7/14, with the same single three-card packet passing in both arms. For the learned team, partial-inclusive release rises from 16.30% to 35.12% and expected released points rise from 7.61 to 14.77. Full-target release remains 14.69%. The team's writer input rises from 324 to 501 tokens per episode on average, output rises from 100 to 120, and calls rise from one to 2.96. These are writer costs, in addition to the unchanged routing costs. The learned team retains a raw net advantage over its canonical responder swap. The prior-aware adaptive script keeps the highest raw net score among routed arms. With packet-relative release applied, the canonical responder produces more expected released points than the learned team by delivering a different mixture. Keep the full-target release rate and expected released points alongside raw points whenever a partial record may be released.

Same-assistant review uses exact output paragraphs against the archived rubric. Ambiguous source attribution or a missing qualification loses credit. No independent review, training updates or new negotiation transcripts enter this test. The UNIFIL event was previously used in the project, and this is the first run of the separate documentary writer on it. [Full records, receipt probabilities and review](unifil-field-transfer-evidence/results.json) · [Review rationale](unifil-field-transfer-evidence/annotations.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" unifil_field_transfer.py replay unifil-field-transfer-evidence
"$MODEL_PY" unifil_field_score.py unifil-field-transfer-evidence
```

## Train routing for full-target delivery

Bound strict release before fitting. The three-contact planner knows the roster prior and may choose the desk and reply priority after each public receipt history. The planners never see the actual private holdings. Enumerate request and reply losses independently to verify each resulting decision tree. The additional reply-order control makes this an upper bound for the tested learned routes. Under the strong-specialist prior it can deliver all three UNIFIL cards in 65.12% of episodes. Either archived writer can release only one of the four complete target sets, even when all cards arrive. That limits full-target release to 16.28%. The older adaptive script already reaches that rate. A planner that knows which complete packets the writer can release reaches the same rate while reducing contacts from 2.55 to 0.62 per episode. It skips the cases it knows the writer cannot complete, so its net score measures both routing and advance knowledge of writer feasibility. [Exact bounds and fixed decision trees](full-target-headroom.json)

Train the requester and responder together once on the existing written-vote task. Use the same initialization, 180 exact policy-gradient updates, 12,108 trajectories, local observations, roster prior, and fees as the prior fit. Change only the terminal award. Complete target delivery now earns 28 points and partial delivery earns zero, with communication costs deducted in both cases. Train delivery rises from 41.65% to 55.62%. The old content score falls from 50.52 to 48.54. UNIFIL and Colombia writer assessments are used only for replay after fitting.

| Correct specialist label | Full-target release with prior fit | Full-target release with new fit | New requester with canonical replies | Exact release ceiling |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL, either fixed writer | 14.69% | 16.20% | 11.66% | 16.28% |
| Colombia, selected documentary fields | 64.28% | 64.78% | 47.12% | 65.12% |

UNIFIL delivery itself rises from 60.21% to 64.78%, with little change in cost. Under the strict release reward, net gain improves from 3.637 to 4.055. The older adaptive script achieves 4.069 and the feasibility-aware upper bound is 4.438. Colombia's new fit improves strict net from 17.508 to 17.660 against the 17.752 upper bound. Its raw final record score falls from 44.82 to 44.41. The responder swap preserves the requester and leaves the three-contact limit in place. Its drop in full release shows a contribution from learned reply selection under the correct label.

The same improvement is weaker with an incorrect desk label. UNIFIL rises from 12.29% to 12.81% release and Colombia falls from 53.75% to 51.22%. With split specialization, UNIFIL rises from 13.86% to 14.87% and Colombia falls from 60.27% to 59.93%. The same physical strong roster appears in the correct- and wrong-label comparisons. Colombia's endpoint uses the earlier clauses selected through same-assistant review. UNIFIL uses the first-pass banks. This is an improvement in joint documentary routing under supplied metadata and simulated holdings. The experiment uses deterministic policy gradients and archived text, with no new model calls or open-ended negotiations. [Fit weights, training history and all replay rows](full-target-fit.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" full_target_headroom.py
"$MODEL_PY" full_target_fit.py
```

## Train complete delivery with unreliable desk labels

Keep the 28-point delivery reward, 180 exact gradient updates, the 12,108 written-vote trajectories and 330 local states. Change the probability mass on the training trajectories by assigning equal weight to a specialist roster aligned with the public label and its desk-swapped counterpart. The roster strength remains three. Each actor uses the same local observations and receives no signal indicating a reversed label. Both prior fits and the new fit are replayed on the same records and physical rosters. On the balanced written-vote training mixture, the new policy delivers all target evidence in 54.68% of episodes against 51.43% for the earlier full-delivery fit and 39.62% for the original raw-score fit.

| Archived writer and label accuracy | Original raw-score fit | Earlier full-delivery fit | Balanced-label full-delivery fit | Balanced-label requester with canonical reply |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL, 50% correct | 13.49% | 14.50% | 15.62% | 12.11% |
| Colombia, 50% correct | 59.01% | 58.00% | 62.50% | 48.82% |
| UNIFIL, always correct | 14.69% | 16.20% | 15.62% | 12.11% |
| Colombia, always correct | 64.28% | 64.78% | 62.50% | 48.82% |

The entries are strict release with all three target cards. The balanced-label policy has equal aggregate release for correct and flipped labels on both frozen banks. It also improves on both previous policies under split specialization, reaching 15.32% on UNIFIL and 61.26% on Colombia. Canonical replies reduce strict release while keeping the learned requester and all link and budget rules fixed.

Compute the exact planning bound for each label accuracy using its mixed prior. The planner sees aggregate label accuracy and the writer's ability to release each complete packet. It cannot observe whether an episode's label was flipped. At 50% label accuracy on Colombia, the new fit scores 17.028 net against the bound of 17.068. On UNIFIL it scores 3.903 against a bound of 4.267. Later comparison by deployment reliability can keep this common reward scale. At roughly 83% label accuracy, the clean full-delivery fit overtakes the balanced fit on strict net in both modeled settings. On Colombia at 50% label accuracy, the raw-score fit and the balanced fit both produce about 43.78 content points, while the balanced fit yields more complete records.

The test uses the prior first-pass UNIFIL and selected Colombia writer banks with same-assistant review. Both event families are excluded from the new fit. Reliability and contact outcomes are simulated, and the replay uses no new writer generations. [Fixed policies, per-reliability scores and exact bounds](noisy-desk-fit.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" noisy_desk_fit.py
```

## Check whether a peer question changes the final record

Use the archived UNIFIL and Haiti dockets. Keep the recorded vote line and provide the chair with the same other documentary cards in each arm. Separate the China and Brazil accounts on UNIFIL and the China and A3 accounts on Haiti. The first desk writes a sourced note and asks the second desk a question about shared ground or a disagreement. The second desk writes a sourced note either seeing that opening or seeing no message. The same opening, including its question, is sent to the chair in both arms, along with the generated second note. The intervention is visibility at the second desk. The independent, interactive and pooled analyst conditions each use three calls and a common 404-token generation ceiling. The pooled analyst can see both national cards during its two working passes. The one-call verbatim relay gives the chair the original national passages instead of notes. It provides a reference for whether the notes transmit the available evidence.

Use the pre-existing 70-point record rubrics. Check vote, actor, legal force, material conditions and the final treatment of shared ground separately. Check source IDs, completeness and length independently of content points. For the working notes, count distinct source-supported ideas by speaker, the second note's additions and the additions that survive into the record. Mark an answer to the opening question as peer-specific only when it appears in the interactive reply and is absent from the matched independent reply. A first-desk fact that was already in its own archive remains a first-desk fact even if someone repeats it. The two dockets were used elsewhere in the project.

| Final-record points out of 70 | Independent drafts | Interactive drafts | Pooled analyst | Verbatim relay |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL | 35 | 35 | 49 | 42 |
| Haiti | 21 | 14 | 21 | 7 |

The opening question is unanswerable from the second desk's source on both dockets. Each asks about the relationship between two elements of China's own position. The Brazil note that sees the opening conflates the concerns of Lebanon with China's own principles of sovereignty and consent. The chair repeats that conflation. The interactive record recovers both delegations' support for the mission, which was already inferable from the independent notes. The pooled analyst preserves Brazil's qualification that the text addressed only some concerns, but adds an unsupported shared position on sovereignty.

On Haiti, visibility of the question coincides with dropping that Mozambique spoke for the three African members. The independent reply and final retain the capacity and Haiti's request. The interactive chair reports a national position and exceeds the 140-word cap. On the alternative paths, the pooled analyst preserves the A3 attribution and inclusive transition and election criteria. The verbatim relay supplies all four source IDs but conflates the three Council members with the African Group and overstates China's endorsement.

All eight final generations end before the token cap. None clears the full rubric and release checks. The matched team arms use two working turns and one writer turn. The interactive arm adds 70 tokens of peer traffic on UNIFIL and 65 on Haiti. It adds zero verified new answers that survive the final, under the tracked idea inventory. Source wording, criterion anchors and all exact output spans are archived. This test intervenes on access to an entire opening, so changes cannot be attributed to the question wording alone. One same-assistant review covers two exposed event families. [Scored records, idea counts and witness spans](peer-question-evidence/results.json)

For process evaluation, ask whether the receiving role can answer from its own source. Distinguish a question with no obtainable answer, an answerable question with no response, and a supported answer that the writer omits. An explicit question, a smooth reply, or factual uptake in the absence of a unique peer contribution does not establish the value of the peer turn.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" peer_question.py replay peer-question-evidence
"$MODEL_PY" peer_question_score.py peer-question-evidence
```

The standalone score command checks all 18 calls. The launcher initially inherited a replay helper fixed at 26 calls. The archived launch source preserves that version, and the replay command now uses the standalone checker.

## Change only the question the second desk sees

Reuse the generated first note from each docket. Hold the source cards, transcript history, speaker roles, output ceilings and chair prompt fixed. Give the second desk the original note in one arm, delete just the question in a second arm, and replace just the question in a third arm. The replacement names the local topic to check, without supplying the answer. On UNIFIL, ask what qualification Brazil applied to Lebanon's concerns and what it said about the mission's freedom to operate. On Haiti, ask whose request was cited and in what capacity Mozambique's representative spoke. Every chair receives the original first note unchanged along with the new second note, so the revised question reaches the chair only through changes in the reply.

Run the three arms in the same generation batch per stage. The caps remain 98 tokens for the reply and 222 for the chair. The frozen opening keeps its original 84-token cap. Compare the replies and supplement against the previous docket rubrics and mark the two requested propositions per case separately. Credit the second note for a supported answer it actually states, and credit carry-through only if the final record preserves the same proposition with the correct scope and actor. Track differences against both the original question and question deletion. A gain over the original question alone could reflect removing a distraction. The source notes and replacement questions are authored or frozen before inference, and independent assessment remains open.

| Docket and endpoint | Original question | Question deleted | Answerable question |
| --- | ---: | ---: | ---: |
| UNIFIL supported targets in reply | 1/2 | 2/2 | 2/2 |
| UNIFIL reply targets retained in final | 1/2 | 0/2 | 2/2 |
| UNIFIL final-record score | 35/70 | 35/70 | 42/70 |
| Haiti supported targets in reply | 0/2 | 2/2 | 2/2 |
| Haiti reply targets retained in final | 0/2 | 1/2 | 2/2 |
| Haiti final-record score | 14/70 | 7/70 | 21/70 |

Deleting the question recovers as many targeted facts in the replies as asking the targeted question. The targeted question produces replies whose facts survive the chair in both dockets. On UNIFIL, the resulting record keeps Brazil's limited qualification and freedom of operation. On Haiti, it keeps Mozambique's capacity and attributes support under Chapter VII at Haiti's request to the three African members. The deleted-question Haiti final preserves the capacity but loses whose request the members cited. The two targeted-question records end before the cap and stay within 140 words. Every arm misses required citations and has at least one flagged issue. No record passes strict release.

Both original-question replies reproduce their archived text. The UNIFIL final reproduces too. The original-question Haiti final changes wording and truncates in the new batch. Its score and failure to preserve the targeted facts are unchanged. Treat the new within-batch comparisons as the primary contrasts. The prior independent scores were 35 and 21. The targeted intervention exceeds that archived score on UNIFIL and ties it on Haiti. The hand-authored changes are based on previously inspected dockets, so apply the result to question design and criterion retention. Independent annotation and generalization to new families remain unmeasured. [All exact replies, record spans and within-batch contrasts](peer-question-repair-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" peer_question_repair.py replay peer-question-repair-evidence
"$MODEL_PY" peer_question_repair_score.py peer-question-repair-evidence
```

## Generate questions from the receiving desk's source index

Advance from the hand-authored UNIFIL and Haiti questions to generated questions on the Colombia and UNAMI dockets. Keep the prior 70-point rubrics, and share one first-desk note across arms. The first desk generates a separate question either with the recipient's source IDs and topic descriptions or with no index. The descriptions contain no documentary answers. The first desk receives its own note and the public vote, while the second desk receives its own documentary cards and only the generated question. A third arm skips the question. The chair receives the same public cards and first note plus the corresponding second note in every arm. It never sees the generated question or recipient index.

Hold model, source holdings, role instructions and generation limits fixed for the indexed and unindexed arms. Each uses a 132-token opening, a 74-token question, a 128-token reply and a 277-token final ceiling. The no-question arm saves the question call. Compare how much of each question the recipient can answer from its cards, which supported propositions it states, and which survive the final. Use the [receiving-desk proposition inventory](peer-index-inventory.json) and archive the factual and form checks independently. The dockets are new to the question experiment and have previously appeared elsewhere in the project.

| Final-record points out of 70 | Unindexed question | Indexed question | No question |
| --- | ---: | ---: | ---: |
| Colombia | 28 | 21 | 28 |
| UNAMI | 28 | 21 | 35 |

The unindexed model asks the receiving desk to verify claims its cards cannot establish in both cases. The indexed Colombia question identifies an A3 topic relevant to verification conditions, but asks whether it confirms Brazil's request. The A3 cards can give the African members' own conditions and cannot establish a Brazilian request. The indexed UNAMI question asks about women's participation, which belongs to the first desk's card. The indexed replies establish no asked and answerable proposition according to the selected inventory.

With no question, the Colombia reply correctly gives Ghana's representative capacity, the conditions for verification, and the Ethnic Chapter pledge. Its final record retains the capacity and pledge while compressing the description of the verification activity. With the index, both the reply and the final recast the collective statement as Ghana's individual position. On UNAMI the first note introduces an incorrect biannual cadence. The indexed reply also mistakes absence from its own review cards for absence from the resolution. The final repeats both errors. These failures distinguish the receiver's evidence limits from whether it can push back on a premise.

None of the six final records passes all accuracy and citation checks. The unindexed Colombia final and no-question UNAMI reply reach their generation caps. All other turns finish. The audited transcript reconstructs all 18 calls and their exact visibility. The [review annotations](peer-index-transfer-evidence/annotations.json) retain the same-assistant judgment and source boundaries. The result tests one metadata prompt with frozen Qwen3.5-4B. It supports auditing whether the question refers to a fact in the receiving role's source before treating a fluent exchange as successful coordination. [Questions, exact spans, counts and records](peer-index-transfer-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" peer_index_transfer.py replay peer-index-transfer-evidence
"$MODEL_PY" peer_index_transfer_score.py peer-index-transfer-evidence
```

## Measure the effect of specific question actions

Use the same Colombia and UNAMI opening notes and evidence access as the source-index test. Enumerate three authorized actions per docket. One passes without a question, one requests the representative or responsible actor, and one requests a bounded scope from a recipient-owned source. The menu names the fields and source ID, with no factual answer in the question. On Colombia, the two questions address the A3 speaker and the Ethnic Chapter pledge. On UNAMI, they address the review's responsible actor, recipient and date, or the review's consultations. All arms reuse the 128-token reply and 277-token final ceiling and use the same chair prompt. The chair sees the original opening and resulting reply, with no direct view of the question.

Compare each action with passing. Count which requested propositions the reply supplies, which the no-question reply would already supply, and what the final retains. Evaluate the shared 70-point final scale, citation and release checks separately. The menus are authored development controls on previously used dockets. Their best measured action is an after-the-fact reference for these fixed outputs. It cannot show that a delegate learned to select a question or predict the consequence on a new case.

| Final-record score | Pass without a question | Ask for the actor | Ask for the scope |
| --- | ---: | ---: | ---: |
| Colombia | 28/70 | 28/70 | 28/70 |
| UNAMI | 35/70 | 42/70 | 28/70 |

The four authorized questions elicit all eight requested propositions. Six already appear in the corresponding no-question replies. Seven requested propositions survive the chair. On Colombia, both requested facts already survive without a question. The scope question preserves Ghana's representative capacity and the Ethnic Chapter pledge at the cost of losing the separate statement welcoming the extension. On UNAMI, the actor question recovers the Secretary-General as the actor and Council as recipient. The final retains the actor and review deadline, drops the recipient, and also gains the review's regional-cooperation purpose. The scope question retains the same consultation facts as passing and drops the recommendations criterion. Every UNAMI final repeats the first desk's incorrect reporting frequency.

All six final records fail release. The observed best question adds seven points over passing on UNAMI and zero on Colombia. Equal final point values can hide changes in which facts survive. Use chance to ask, feasibility from the recipient's local evidence, reply fidelity, incremental retained facts and total record quality as separate measurements. This run compares menu actions with Qwen3.5-4B frozen. The questions and menus were authored after earlier trials on these dockets, and the outputs have same-assistant review. [Question-action table, source spans and exact scores](field-question-action-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" field_question_actions.py replay field-question-action-evidence
"$MODEL_PY" field_question_score.py field-question-action-evidence
```

## Verify the reporting source at the UNAMI handoff

Freeze the previous UNAMI opening, its incorrect biannual reporting claim, and the replies from the no-question and review-actor actions. For each reply, cross the original chair prompt with a prompt asking the chair to state the actor, recipient and time separately for recurring reporting and the one-time review. The added prompt also gives official cards priority over conflicting notes. Cross both prompts with visibility of the original REPORT source. This is the card that states the recurring four-month cycle. The chair receives no new source for the one-time review in any of these eight matched arms. A ninth call gives the same chair all original cards and the edited instruction, with no working notes. It is a pooled information control.

Use the actual calendar handover needs to score the mandate expiry, review deadline and report frequency from the final record. Score the review's actor, independence and Council recipient separately from the recurring report's actor and recipient. The complete 70-point rubric, citations, source issues and form are separate checks. All calls use the same 277-token ceiling and the archived opening and replies are reused verbatim. The pooled control uses different evidence visibility. [Calendar endpoint from the reader-use benchmark](../../benchmark-kit/reader-use/README.md#check-the-latest-generated-question-result-against-a-real-recipients-job)

| Reply and chair condition | Final-record points | Calendar entries correct | Review actor | Review recipient |
| --- | ---: | ---: | --- | --- |
| No question, plain chair | 35/70 | 2/3 | Omitted | Omitted |
| No question, plain chair with REPORT | 35/70 | 2/3 | Omitted | Omitted |
| No question, binding instruction | 35/70 | 2/3 | Omitted | Omitted |
| No question, binding instruction with REPORT | 42/70 | 3/3 | Omitted | Omitted |
| Actor question, plain chair | 42/70 | 2/3 | Preserved | Omitted |
| Actor question, plain chair with REPORT | 42/70 | 3/3 | Omitted | Preserved |
| Actor question, binding instruction | 42/70 | 2/3 | Omitted | Preserved |
| Actor question, binding instruction with REPORT | 49/70 | 3/3 | Omitted | Preserved |
| All-source pooled chair, binding instruction | 35/70 | 3/3 | Omitted | Omitted |

Both plain notes-only controls reproduce exactly. The original chair with a no-question reply incorrectly cites the REPORT card as support for biannual reporting. Adding an explicit source-priority instruction corrects that error and preserves the report's actor and Council recipient with either reply. With the actor reply and no source card, the binding instruction adds the Council as the report recipient without visible documentary support for that relation and retains the false interval. The full source does establish the recipient, but it belongs to a different clause than the review recipient.

Every record preserves the mandate and review deadlines. None preserves both the actor and recipient of the review as a single obligation, even with the cue or with all original cards. No record clears the full release contract. The best matched arm reaches 49/70 and supports all three calendar entries. Its citations remain incomplete. The all-source pooled answer also supports all three entries and conflates the participation requirements for women, civil society and youth. A usable calendar therefore says less than a source-faithful Council record.

This is frozen Qwen3.5-4B on one exposed docket with same-assistant review. The binding prompt changes both the relation-retention instruction and how to resolve contradictions. The test isolates that bundle from card visibility. It does not isolate the two sentences within the prompt. [Every final record, spans and paired effects](unami-handoff-evidence/results.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" unami_handoff.py replay unami-handoff-evidence
"$MODEL_PY" unami_handoff_score.py unami-handoff-evidence
```

## Preserve the reviewed UNAMI handoff clauses verbatim

Use two existing generated UNAMI records as fixed beginnings and remainders. In each one, replace the incomplete review sentence only if the approved peer sentence arrives, and replace the false biannual sentence only if the official REPORT card arrives. Keep the earlier review sentence when the peer receipt is withheld. Remove the false cadence in all conditions. The approved peer text is the actual actor reply's first sentence, which names the Secretary-General, independence, the Council as recipient and the review deadline. The report text comes directly from the official source summary. The composer keeps both sentences byte-for-byte with a source ID appended and preserves the rest of the generated text outside the two edit sites.

| Record remainder and receipt | Neither | Review only | REPORT only | Both |
| --- | ---: | ---: | ---: | ---: |
| No-question remainder | 35/70 | 42/70 | 42/70 | 49/70 |
| Actor-question remainder | 42/70 | 49/70 | 49/70 | 56/70 |

The two slots act independently on content points conditional on each fixed remainder. Both obligations are complete only with both receipts. The reporting receipt alone supplies all three calendar entries. No assembled supplement exceeds the original word ceiling. Inherited criteria and unrelated citation gaps remain visible, and neither completed handoff meets the full 70-point release contract.

The admission test uses the host's simulated receipt plus the approved exact text, field, source and identity. Both authentic inputs pass. Eight withheld, modified or mislabelled inputs fail, including wrong recipients, review dates and cadence. A faithful paraphrase is also withheld because it is outside the reviewed registry. It requires separate review before admission. This is a posthoc two-slot control and contains no new model generations. Masking a receipt on the actor-question remainder does not remove any other effect from the original interaction. Use the table to bound the value of delivering these two fields, with the broader policy effect still unmeasured by this control. [Every assembled record and admission check](unami-verbatim.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" unami_verbatim.py
```
