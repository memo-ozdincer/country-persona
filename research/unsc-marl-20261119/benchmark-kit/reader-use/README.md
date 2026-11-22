# What can the next reader do with the final record?

A chair writes for someone who must use the record. Evaluate that handover by giving a fresh reader only the final memo and a concrete information need. Count a successful handover when the answer is both historically supported and recoverable from the memo. If the reader guesses an omitted fact correctly, the writer receives no transmission credit. If the reader faithfully repeats a false claim, the reader and writer receive different judgments.

## Re-read the six actual UNIFIL and Haiti memos

Eight author-selected questions cover the four facts targeted by the prior question intervention and four additional facts about sponsorship, drafting, voting and finance. For each question, the frozen Qwen3.5-4B reader sees the same three options in three cyclic orders. It sees no author identity, originating question, peer transcript, reference answer or source dossier. Score the leading legal token. Order disagreement makes that reader/item decision unstable. The first pass uses only the generated supplements. A second pass uses the delivered records with their fixed vote prefixes. The same question also receives a faithful single-sentence note, a textually reversed control, and no note. Reversed statements are synthetic controls for reading behavior. Each family contributes four questions and three actual memos. This gives 144 prompted observations in the first pass plus 72 in the assembled-record pass, from eight distinct questions.

For each real memo, the source-supported answer is eligible for credit only when the memo explicitly supplies the requested relation, actor or qualification. A span review records that support separately. The Haiti question about the request needs an explicit attribution to the three members. The phrase “French text” does not explicitly identify who submitted the draft. A reader answering from memory can score well on a conventional factual quiz. Requiring stability across options, textual support, and sensitivity to a changed note makes that shortcut visible. These are interpretations by the same assistant that selected the questions. Model reads are fresh and use the same model family as the writers. [Actual memos](../../crossbench/colombia2023/peer-question-repair-evidence/results.json) · [Question and control text](items.json) · [Support spans](memo-support.json)

### Results on the delivered record

| Stable, text-supported answers | Original question | Deleted question | Answerable question |
|---|---:|---:|---:|
| Four targeted facts | 0/4 | 1/4 | 3/4 |
| Four other facts | 4/4 | 4/4 | 4/4 |

All eight absent-note controls yielded unspecified in every answer order. All eight reversed notes yielded the stated alternative. Seven of eight faithful notes yielded the expected answer in every order. The exception was Brazil's freedom-of-operation statement, which was also order-sensitive in the actual records. Classify this as a reader limitation. The archived span still supports the fact. No stable read of an actual memo recovered an absent historical answer.

The generated supplements alone give 3/4, 3/4 and 2/4 on the untargeted questions. That apparent loss disappears when the common vote line is included, as the original protocol intended. The targeted results stay 0/4, 1/4 and 3/4 in both passes. These totals are eight content questions on two exposed dockets. The 216 model calls count repeated presentations and controls. They cannot estimate a population-wide effect of asking a question. [Supplement results](evidence/score.json) · [Delivered-record results](assembled-evidence/score.json)

## Transfer to a task with a usable deliverable

The separate **handover repair** generator samples from an explicit finite design. Every task contains a provisional schedule with two entries. The successor must confirm supported entries, correct wrong ones with the right date, and flag a specific verification when the supplied material cannot settle a field. Motivation for the fields comes from two UN decisions: the mandate and independent-review deadlines for UNAMI, and the sanctions and Group of Experts deadlines for the DRC. Dates, roles and source text stay historical in every world. Only the provisional memo and the recipient's access to evidence change. [UNAMI docket and sources](../../crossbench/unami2023/case.json) · [DRC docket and sources](../../crossbench/drc2023/case.json)

Each docket crosses four combinations of correct or mistaken draft entries with four combinations of evidence availability. Score all 32 handovers and 64 field decisions. Exact success on a correction requires the replacement date, and a verification must leave the date open. The task permits both concurrent errors and a fully correct draft. Report wrongful confirmation separately from unnecessary referral. The public generator and keys are development data. The row index is bookkeeping and must stay out of agent prompts. Source cards are project summaries with paragraph references.

| Baseline | Correct fields /64 | Complete handovers /32 | Unsupported confirmations |
|---|---:|---:|---:|
| Preserve both draft entries | 16 | 2 | 32 |
| Refer every field for verification | 32 | 8 | 0 |
| Confirm any proposed date found anywhere in the supplied record and refer all others | 38 | 13 | 10 |
| Read the relevant date from its field-specific source and apply the edit | 64 | 32 | 0 |

The last row is a template-specific software control. Holding both fields and source access fixed while reversing one draft date tests whether a system changes only the affected line. Holding a draft fixed while withholding a source tests whether it withdraws only the unsupported certification. A practical extension is a disputed attribution, a minority reservation, or a condition on an amendment. For those fields the replacement must carry the correct actor, scope and speaker capacity. Sample successor questions or edits before writers see the case, withhold them from the question author, and score the complete record against the same contract. Keep negotiation families together for inference.

For a team comparison give source desks separate holdings and let the writer request corrections. Score the resulting handover with the same successor task as pooled solo and independent-draft systems. Record whether the team repaired a particular line that both matched controls left wrong. Open-ended diplomacy still needs a check that the framing, unresolved objections and reasons survive a handover. A deadline repair result alone supports a claim about documentary use.

## Reproduce

Run from this directory. The actual reader run uses the checkpoint and CPU environment recorded in its launch receipt. The two task and key commands emit separate JSON for evaluation.

```sh
python3 -B score.py | cmp - evidence/score.json
python3 -B score.py --assembled | cmp - assembled-evidence/score.json
python3 -B handover.py inputs
python3 -B handover.py keys
python3 -B handover_controls.py
python3 -B grade_handovers.py handover-key.json
python3 -B common_ground.py checks
python3 -B grade_facilitator.py facilitator-key.json
```

### Check the latest generated-question result against a real recipient's job

The other experiment has since run generated questions on Colombia and UNAMI. With a recipient index both final records scored 21/70. With no question they scored 28 and 35 respectively. The indexed replies supplied no requested proposition deemed answerable in the prior inventory. On UNAMI the indexed final repeats a biannual reporting claim. [Experiment and records](../../crossbench/colombia2023/README.md#generate-questions-from-the-receiving-desks-source-index)

We applied the two UNAMI deadlines from the handover generator to **the actual outputs** of that experiment. Each of the three records supports both one-time calendar entries. A comparison limited to those fields gives all three systems full marks despite their 21–35 range on the original rubric. Inspecting the full job of a calendar clerk reveals the missing third entry. Resolution 2682 requests a report every four months. Both the indexed and no-question records say biannually. The unindexed record rejects biannual submissions and omits the correct interval. **None of the three can populate the complete calendar.** This is a retrospective span audit. The recurring field was added after reading the records. It illustrates why an intended user's actual job should define the required fields before model selection. [Calendar spans and source checks](unami-calendar.json)

The reader exercise draws on QA-based content evaluation and task-based human studies of summary usefulness. Their distinction matters here: recalling a sponsor, repairing a schedule, and reporting a minority reservation are different downstream jobs. A benchmark can average only over an explicitly chosen distribution of those jobs. Publish results by job before any aggregate. [QAEval](https://aclanthology.org/2021.tacl-1.47/) · [Extrinsic human evaluation of summaries](https://aclanthology.org/2024.lrec-main.821/)

### A facilitator's next decision

The [facilitator inputs](facilitator-inputs.json) apply the same idea to substantive disagreement. They ask whether a proposed sentence can be used as **documented common ground**. A narrow overlap can be true even where the delegates supported different drafts. In Mali both sides sought an extension of sanctions. Russia's stated wish to dissolve the Panel defeats a joint claim about retaining it. In Haiti, welcoming Kenya's offer coexisted with different positions on adopting the authorization. The Mozambique source speaks for three Council members. Silence on a funding pledge leaves an open question.

Six proposed sentences crossed with four source-availability conditions give 24 development presentations. The [key](facilitator-key.json) labels two retained statements, four contradicted ones requiring revision and eighteen withheld for insufficient evidence. This deliberate imbalance exposes an always-withhold baseline that gets 18/24 while supplying no common ground. Report recall separately for all three decisions and require a proposed sentence to pass all four evidence conditions before giving it full paired credit. Hiding a source changes the authority to **publish** a joint attribution while keeping the underlying historical positions fixed. The source-relation labels are assistant-authored and remain open to independent review.

For the written replacement score two checks independently of the disposition. First, every factual attribution must identify a speaker in the supplied evidence, carry its scope and cite its passage. Second, where supported, preserve a usable point of overlap or a precise recorded disagreement. For example, with just the African members' Haiti statement, a usable sentence is “Speaking for the three African Council members, Mozambique welcomed Kenya's offer to lead [A3]. China's view is unverified in this packet.” With both statements the chair may report both welcomed the offer. A blanket claim that both endorsed the authorization is a material attribution error. Keep the replacement text and its evidence spans for blind review. The current keys score the disposition and source relations. No model-quality or automated prose-grading result is claimed for these 24 inputs.

[Handover inputs](handover-inputs.json) · [Handover keys](handover-key.json) · [Prediction grader](grade_handovers.py) · [Scripted baseline results](handover-baselines.json)

Applying that facilitator need to the three **actual Haiti records** reveals a common omission. Both source cards document welcoming Kenya's leadership offer, including China's statement despite its abstention. Every chair record mentions the offer on the African side. None conveys that China welcomed it. A facilitator relying on any of the three could recover China's caution and the African members' support, but could not safely introduce this specific point of overlap as shared. This was an additional question selected after inspection and is a descriptive example of an unmet reader need. [Source cards and all three Kenya sentences](haiti-common-ground.json)

### Test a structured receipt on the calendar successor task

Use the 32 existing deadline handovers on UNAMI and DRC. The model chooses for each field whether to confirm its draft date, correct it to the other docket date, or refer the field for verification. Compare two presentations with identical documentary excerpts and answer choices. The first supplies the cards as text. The second also identifies which source can establish the current field and whether that card arrived. The latter metadata comes from the benchmark's host and contains no new date. Use the same label order in each matched pair and rotate the order across rows. Keep a third replay condition that requires referral when the host knows the expected card is absent.

Grade the model's recorded decisions against the existing handover key. Show exact fields, complete handovers, unsupported confirmations and corrections, and unnecessary referrals. In addition, weight the same outputs by the learned router's exact receipt probabilities with its acknowledgment visible or erased. Use the same distribution over the four draft-correction patterns and both case families. To count a fully usable handoff in routing replay, both source cards must arrive and both dates and actions must be correct. A justified referral can still earn field credit when some evidence is withheld. This is a known-option deliberation endpoint with no new prose generation.

| Condition | Exact decisions /64 | Exact handovers /32 | Unsupported confirmations and corrections |
| --- | ---: | ---: | ---: |
| Cards shown as text | 42 | 13 | 19 |
| Cards plus field receipt | 49 | 19 | 12 |
| Field receipt with enforced referral on absence | 64 | 32 | 0 |

Both model presentations get all 16 sourced confirmations and 16 sourced corrections right. When the source is absent, the text presentation refers 10 of 32 cases and the receipt presentation refers 17. Each has three other unresolved outcomes from tied label scores. The deterministic gate changes only a field whose required source the host knows to be absent. Its 64/64 result uses the model's 32 correct dates and the host's 32 forced referrals. The gate relies on the fixture's field-to-source map.

In exact split-holdings routing replay, showing the acknowledgment raises the rate of both dates being usable from 34.17% to 37.48% under all presentations. Both-date usability needs both cards to arrive, which every presentation handles correctly. In the text-only presentation, the same routing gain raises expected unsupported certifications from 0.405 to 0.414 per handoff because the entire pattern of missing fields changes. With the absence gate, both are zero. Overlap results likewise show higher complete-calendar delivery with the acknowledgment, 28.17% versus 24.86%.

These are 128 frozen Qwen3.5-4B next-label reads across 32 development handovers on two previously exposed event families. The two allowed dates and the authenticated field-to-source map are supplied by the harness. Only one rotated order is sampled per matched case. The evaluations leave conflicting authoritative sources, unrestricted dates, and open-ended final records outside the measured scope. [Every decision, grader result and exact routing replay](receipt-handover-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" receipt_handovers.py score receipt-handover-evidence
```

### Generate the handover without a date-choice menu

Reuse all 32 calendar inputs and their existing source and draft permutations. Replace the per-field selection prompt with one generation for both fields. The model may write any ISO date from the evidence. It must give an action, a date and the source for each line. A verification leaves both the date and source open. Compare the same text-only versus field-receipt presentations. The source-ID and absence flag contain no dates. Both share the same 84-token ceiling.

Score the supplied action, ISO date and appropriate documentary source together. Keep format, two-field success and unsupported certification distinct. The absence gate changes a field to verification only when the expected source did not arrive. The status of a received source is still judged from the generated clerk output. Replay the same learned acknowledgment policy and receipt distributions as before. This removes the date-choice menu, and the output retains a fixed two-line schema.

| Open-date condition | Strict fields /64 | Strict handovers /32 | Well-formed generations /32 |
| --- | ---: | ---: | ---: |
| Cards as text | 12 | 5 | 8 |
| Cards plus field receipt | 11 | 5 | 10 |
| Field receipt with forced referral | 43 | 13 | 10 |

Most generated verification lines leave the source column blank or echo the expected ID rather than using a dash. The strict parser treats a malformed two-line generation as unusable. The host's referral gate can still supply a known-missing field, but it does not recover the adjacent field from a malformed record in this strict score. The raw generations and the gate's decisions remain separate. A single surrounding code fence is tolerated.

A post-hoc line audit reads each uniquely identified line independently and normalizes an explicit verification with a blank or dash date. With this normalization, the text and field-receipt presentations produce 51 and 52 exact decisions out of 64 respectively, and 24/32 exact handovers each. The absence gate raises the latter to 54/64. Six additional sourced lines contain the correct date and source and use the wrong action. Deriving confirm or correct from a comparison of the generated ISO date with the corresponding draft brings the receipt pipeline to 60/64 decisions and 29/32 handovers. This adapter does not change any date and was designed after inspecting outputs. Four errors remain. One DRC line attributes the July prospective-review date to Experts mandate expiry. Two fields in a UNAMI handover reverse the source for mandate expiry and strategic-review delivery. The other UNAMI line confirms the wrong date with the proper source ID.

The open generation produces five of eight exact fully sourced handovers. Under split holdings, the learned acknowledgment's gain in both dates usable is 21.36% to 23.42% before action repair, versus 34.17% to 37.48% in the previous date-menu test. In the post-hoc line audit with absence gating and action repair, seven of eight complete-source handovers pass. The split replay reaches 29.90% with receipts erased and 32.79% with receipts visible. The protocol uses 64 frozen model generations on previously exposed dockets, a fixed schema, and a provided source map. [Strict score and records](open-handover-evidence/results.json) · [Line audit and post-hoc adapter](open-handover-evidence/line-audit.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" open_handover.py score open-handover-evidence
"$MODEL_PY" open_handover_line_audit.py open-handover-evidence
```

### Recover one calendar field from its own source

Reuse all 32 UNAMI and DRC draft and receipt cases. Make one call per field. A clock field gets only its assigned source card, or an explicit missing card. The model must return an unrestricted ISO date or UNKNOWN. The host refers the field for verification when its card is missing and derives confirm or correct from the model date and the draft. It does not supply an alternative date. The DRC Experts card still carries both the enacted expiry and the different prospective-review deadline, plus further dates for reports.

Add 12 development controls. Eight cross two draft dates, the existing expiry and an unestablished future authorization date, and the availability of the official Colombia mandate card. Four ask about the two DRC clocks on the authentic Experts clause and on the same passage with the dates exchanged. The exchange changes the synthetic answer key, with no change to the historical record. This comparison isolates ambiguities that a source map can leave inside one card.

Relative to the previous two-line generation, the intervention changes call count, source isolation, action handling and output syntax together. The fixed draft, available historical evidence and route weights stay the same. Score raw open-date recovery and host-gated outcomes independently. Tests on these dockets do not measure whether the model can infer the source map itself.

| Evaluation | Raw open-date reads correct | With the host's absence gate |
| --- | ---: | ---: |
| UNAMI calendar permutations | 32/32 | 32/32 |
| DRC calendar permutations | 32/32 | 32/32 |
| Colombia existing-versus-future controls | 7/8 | 7/8 |
| DRC enacted-versus-prospective date controls | 3/4 | 3/4 |

The model returns UNKNOWN for all 32 historical missing-card fields. The host derives the confirm/correct action from the model's date. The composed output scores 64/64 field decisions and 32/32 handovers under the established grader, compared with 60/64 and 29/32 from the prior post-hoc adapter. Actual mean tokens per historical handover are 326 input and 13 output over two calls, versus 317 input and 28.66 output over one call with the previous field-receipt writer. The aggregate generation ceiling is 60 versus 84 tokens.

The 12 additional controls expose failures that the repeated historical fixtures miss. On Colombia the model supplies the existing October expiry for a possible further authorization that the card does not establish. On the DRC control it returns UNKNOWN for the enacted expiry when the paragraph reference is stripped, even though the source prose and provisional date match the prefixed historical case. It correctly follows both fields in the date-swapped DRC passage. Keep source-card presence, exact coverage of the requested legal act, and sensitivity to packaging distinct.

With the 32 historical handovers perfect under their existing masks, complete usefulness is limited by delivery in the exact replay. Split holdings recover 37.48% with the learned acknowledgment versus 34.17% with it erased. Overlapping holdings recover 28.17% versus 24.86%. These numbers use the same simulated selector and no additional policy fit. The result establishes a working open-date pipeline on the two exposed calendar fixtures under the provided source map. The additional evidence does not establish robust transfer of this approach to arbitrary legal acts. [All 76 reads, controls and replay outcomes](isolated-date-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" isolated_date.py score isolated-date-evidence
```

### Route evidence for publishable common ground

Evaluate all 24 facilitator inputs across the six Haiti and Mali proposals. Compare a direct disposition judge against one that evaluates each side separately with its own document. Both models rank legal labels in two orders. The local judge sees the authored single-side statement and its corresponding historical passage. The host releases the original proposed sentence only if the two local readings establish both sides. A contradiction calls for revision and incomplete support calls for withholding. This test records that decision and preserves the original proposed text for release. Replacement prose remains a separate endpoint.

Apply the previous learned acknowledgment policy to the same two evidence roles and simulated receipt masks. Weight all six proposals equally, and compare visible and erased acknowledgments against the facilitator's case keys. Keep correctly published common ground, correct revisions and false publications separate. A rule that withholds every brief may look accurate across all masks while publishing nothing. [Inputs and frozen keys](facilitator-inputs.json) · [Paired evidence design](facilitator-key.json)

| Disposition across each proposal's four evidence views | Direct judge | Separate side readings and composition | Always withhold |
| --- | ---: | ---: | ---: |
| Retain true common ground | 1/2 | 2/2 | 0/2 |
| Revise a contradicted claim | 1/4 | 4/4 | 0/4 |
| Withhold a claim with insufficient evidence | 15/18 | 18/18 | 18/18 |
| False publications | 3 | 0 | 0 |
| Proposals right under all four views | 1/6 | 6/6 | 2/6 |

With separate readings, the two approved sentences preserve Haiti's shared welcome for Kenya's offer and France and Russia's shared support for an extension of sanctions. Under split holdings the learned receipt raises the chance of correctly publishing common ground across the six equally weighted proposals from 11.39% to 12.49%. Within the two actually publishable proposals, both documents are required and success moves from 34.17% to 37.48%. Conditional disposition accuracy stays at 100% because the method correctly withholds when the receipt is missing. The direct reader publishes unsupported common ground in 12.97% of the visible-receipt replay.

The local classifier gets eight of twelve source readings right, abstains once, and falsely credits three statements. It turns the A3's support for adoption into a vote, treats that support as a specific funding commitment, and treats France's support for sanctions renewal as support for retaining the Panel. These errors cannot produce a false joint disposition in this sample because the other side contradicts the claim or lacks support. A perfect joint score cannot certify the local readings or authorize publishing them as separate attributions.

The run uses 72 frozen Qwen3.5-4B next-label reads on two previously exposed dockets. The side statements and answer keys are authored development data. This tests the disposition and release of an existing proposed sentence, with no generated replacement text. [Every disposition, local reading, and exact receipt replay](routed-common-ground-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" routed_common_ground.py score routed-common-ground-evidence
```

### Draft a replacement that preserves the status of each side

Run the same 24 facilitator inputs with a direct writer and with a writer given the disposition from the separate source-reading protocol. The staged writer receives the disposition only. It still has to find its own documentary support for each sentence. Hold the cards, provisional claims, writing contract and generation ceiling fixed across the two writers. Score the action, documentary attributions, whether the evidence limits are explicit, and the form of the brief separately. To qualify, a retained statement must preserve both documented sides. A revised statement must preserve the specific contradictory position. A withheld statement must preserve any documented side and make its evidentiary limit clear. Compare exact routed receipt patterns with the message visible and erased, using the same learned policy as before.

| Replacement endpoint | Direct writer /24 | Staged writer /24 |
| --- | ---: | ---: |
| Correct disposition, ignoring separator | 15 | 24 |
| Correct output form | 10 | 24 |
| No flagged source or attribution errors | 23 | 19 |
| Required positions preserved and cited | 11 | 10 |
| Full brief usable | 3 | 8 |

Giving the correct disposition eliminates the direct writer's five erroneous retain decisions. The staged writer still drops documented facts, substitutes a different claim and misses required citations. It preserves one of two retain briefs under the full contract. Both writers can publish the sentence about extending sanctions with the correct IDs. In the Haiti retain case, both preserve the shared welcome for Kenya's offer and omit the required bracketed IDs. The staged writer sometimes narrows the factual record too far, for example treating the single China passage as unable to establish China's welcome because China abstained.

Both writers produce zero usable contradiction briefs. The staged writer states the specific contradiction in all four cases and omits the card ID in all four. The Haiti examples use meeting-page references. The Mali examples omit citations. Citation is the only remaining failure on nine staged briefs, including these four. This is an annotation-based diagnosis, with no new repair run. Its review accepts end-of-sentence IDs when the sentence names the supported speakers and distinct positions.

Under split holdings, the staged writer's expected valid publication rate across all six claims rises from 5.70% without the observation to 6.25% with it. This is half of the earlier disposition-plus-copy endpoint, because only one of the two supported retained claims meets the new writing contract. Overall usable briefs rise from 16.48% to 20.91%, and valid contradiction replacements stay at zero.

The run uses 48 frozen Qwen3.5-4B generations on two previously used dockets. The disposition was correct in every staged input on these fixtures. Review is by the same assistant and separates source errors, loss of a required qualification, citation omissions and the requested form. The staged condition changes the prompt and uses the earlier reader calls. The comparison holds writer caps equal but uses different total computation. [All generated replacement text and per-case scores](facilitator-replacement-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" facilitator_replacement_score.py facilitator-replacement-evidence
```

### Attach citations to fixed facilitator prose

Freeze the 24 staged facilitator briefs. For each available card, ask a separate reader whether it establishes at least one factual attribution actually made in the brief. Check both label orders. Append an ID only when both readings agree. Compare with no repair, appending every received ID, and appending the IDs from the earlier review. The last arm is an oracle for citation availability in this fixture. All arms keep every character of the generated brief and append only visible source IDs.

Score the exact citation set, the original semantic review, the writing contract, and final release together. Count new irrelevant citations independently. A card that supports one side cannot establish another side's position. A valid citation also cannot repair a mistake already present in the prose. Replay the same distribution over the six proposals and the learned router's visible and erased receipt masks.

| Citation handling | Usable briefs /24 | Usable retain /2 | Usable revise /4 | Briefs with new excess citations |
| --- | ---: | ---: | ---: | ---: |
| Original citations | 8 | 1 | 0 | 0 |
| Separate frozen source reader | 10 | 2 | 1 | 0 |
| Attach every received ID | 15 | 2 | 2 | 4 |
| Attach review-approved IDs | 17 | 2 | 4 | 0 |

The selective reader repairs the true Haiti common-ground brief and the China-only contradiction brief. It misses the CHINA citation on the paired revision where both cards are visible, even though the draft makes the same substantive correction. It also changes from conflict to citation on the two Russian contradiction drafts when the labels swap. The card supports the writer's correction, while it contradicts the embedded claim being rejected. The test indicates sensitivity to the role of a quoted claim in a revision. Relevance measured at the whole-sentence level can also make an otherwise correct citation order-sensitive.

The selective reader restores the full true-publication rate from the earlier disposition-plus-copy test, 12.49% on split holdings with the acknowledgment visible versus 11.39% erased. Overall usable briefs reach 32.22% with the acknowledgment versus 27.23% erased, up from 20.91% and 16.48% without citation repair. The raw “attach every ID” baseline clears more briefs under this review and adds irrelevant support to four. The review-approved arm is a post-hoc upper bound with the factual prose fixed. It cannot fix unsupported claims or omitted positions.

The test uses 48 frozen Qwen3.5-4B next-label calls on the same authored Haiti and Mali briefs. Strict usability still relies on the earlier same-assistant factual review. It would be incorrect to release arbitrary text solely because the citation reader found a related source. It checks document selection, and the factual review checks the full brief. [Each citation decision, resulting brief and exact routed score](facilitator-citation-evidence/results.json)

```bash
OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 "$MODEL_PY" facilitator_citations.py score facilitator-citation-evidence
```

### Learn when to send a source or pass on common-ground claims

Each of two desks holds two of four slots. Two slots cover the sides of a proposed joint statement. A local read can support, contradict or leave its side unknown. A desk sends one slot or passes. The second may see an acknowledgment only after the first slot arrives at the chair. The designer fixes independent 90% chair delivery, an 80% acknowledgment channel and a cost of 0.10 per attempted send. A correct retain or revision earns one, a wrong actionable decision loses one, and withholding earns zero. Compare with a scripted rule using the same local information, which prioritizes a contradiction, sends a nonduplicate support when appropriate and stops forwarding once a contradiction is confirmed.

Fit the two tabular policies jointly over 180 exact updates on uniform synthetic relation pairs. This creates one retain, five revise and three withhold cases in the nine-pair mixture. The learned strategy earns 0.367 net against 0.356 for the script on that mixture, while retaining only 5.41% of actually publishable cases against the script's 32.40%. Under the actual six Haiti and Mali proposals, the classes are equally frequent. Train one matched policy with the same updates and environment, assigning equal probability to the disposition classes. The global disposition only sets the training probability. Every agent still receives local reads and the acknowledgment alone.

| Split holdings with frozen model source reads | Raw retain | Raw revise | Mean send cost | Net utility | Usable actionable briefs |
| --- | ---: | ---: | ---: | ---: | ---: |
| Uniform fit | 1.39% | 24.74% | 0.036 | 0.225 | 13.76% |
| Balanced fit | 10.53% | 24.75% | 0.093 | 0.260 | 20.14% |
| Balanced fit, acknowledgment erased | 1.58% | 24.74% | 0.089 | 0.174 | 11.19% |
| Greedy local rule | 12.46% | 24.81% | 0.124 | 0.249 | 21.54% |
| Greedy local rule, acknowledgment erased | 11.08% | 24.81% | 0.144 | 0.214 | 17.94% |

Use the prior exact citation and writing checks for the usable-brief endpoint. The balanced policy reduces costs enough to beat the greedy rule in this particular net objective, while the greedy rule still produces more usable briefs. With accurate authored relations in split holdings, the balanced fit scores 0.276 net against the greedy rule's 0.279. In overlap holdings it beats greedy with either relation input on net and still gives up some usable briefs. Thus savings on imperfect local reads and the assumed send price matter to the ordering. The same checkpoint's sharp drop with observation erased establishes dependence on that channel and also shows greater fragility than the greedy erased control.

Both fits train on abstract relation worlds. No Haiti or Mali claim or prose is used in optimization. The six-proposal evaluation is previously exposed, uses same-assistant review, and reuses the frozen briefs under simulated delivery. No new writer generations or human evaluation enter this experiment. [Uniform fit](facilitator-policy.json) · [Training-mixture audit](facilitator-policy-audit.json) · [Balanced fit and all replay outcomes](facilitator-policy-balanced.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_policy.py
"$MODEL_PY" facilitator_policy_audit.py
"$MODEL_PY" facilitator_policy_balanced.py
```

### Transfer the frozen facilitator policy to UNIFIL and Colombia

Use eight additional proposals from supplied archival summaries. These include true common ground, contradicted proposals, and claims where one side states a position and the other is silent. For example, the UNIFIL text documents China's position on sovereignty and consent but supplies no comparable statement from Brazil. The Colombia A3 source documents a pledge on the Ethnic Chapter that the Brazil source does not mention. The label for silence is unknown. Do not infer a position from neighboring evidence. The source excerpts and their identifiers are supplied by the harness.

Apply the unchanged source-local classifier and both previously trained policies. No policy states contain a docket identifier. Compare the balanced fit, its receipt-erased version, the uniform fit and the greedy local rule under overlapping and split holdings. A revision is credited only when the contradiction is present in the cards that actually reached the facilitator. A withheld statement receives no positive action utility, and a wrong actionable decision is penalized. This measures evidence acquisition and publication or revision decisions. It does not generate fresh replacement prose.

| Split holdings, all eight proposals | Valid retain | Valid revise | False actionable decision | Mean send cost | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Balanced fit | 7.90% | 18.56% | 17.18% | 0.108 | −0.015 |
| Balanced fit with acknowledgment erased | 1.19% | 18.56% | 10.46% | 0.100 | −0.007 |
| Greedy local rule | 9.35% | 18.61% | 18.65% | 0.131 | −0.038 |
| Uniform fit | 1.04% | 18.56% | 10.32% | 0.043 | 0.049 |

The model reads 11 of 16 local relations correctly after mapping a disagreement to unknown. With both cards present it falsely retains two of eight proposals. One attributes China's sovereignty emphasis to Brazil. The other attributes Brazil's statement about Colombia's priorities to the African members. It also treats China's view that the text fell short as a contradiction of the weaker proposition that it addressed some concerns. The source leaves that weaker position unknown. These distinctions depend on the supplied summaries and the same-assistant case keys.

A separate exact intervention supplies correct local reads while keeping policy weights and receipt odds fixed. With perfect reads on split holdings the balanced policy gains 0.216 net versus 0.148 with the acknowledgment erased, and records zero false actions. With the measured reads the same acknowledgment increases both valid publication and false actions by about 6.71 percentage points. At the fixed cost of 0.10 per attempted send, the balanced policy and the greedy rule both finish below the zero net value of silence. With the model reads and the policy held fixed, balanced routing breaks even against silence at about 0.086 per attempted send. The earlier uniform fit remains positive on this set because it spends less and rarely attempts publication.

This is a transfer of the policies from the Haiti and Mali evaluation to previously exposed UNIFIL and Colombia events. The run uses 32 frozen next-label calls. Proposal decomposition, relation keys and evidence roles are authored. Delivery and cost remain simulated, and the transfer tests dispositions and evidence use rather than generated replacement prose. [Every claim, reading and weighted outcome](facilitator-policy-transfer-evidence/results.json) · [Perfect-reading and fee sensitivity](facilitator-policy-transfer-evidence/perfect-reader.json)

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_policy_transfer.py score facilitator-policy-transfer-evidence
"$MODEL_PY" facilitator_transfer_audit.py
```

### Require a documentary span for each source reading

Take the sixteen UNIFIL and Colombia local claims from the policy transfer and the twelve Haiti and Mali local claims from the facilitator test. For each, ask frozen Qwen to give its relation and copy a contiguous passage establishing it. The host can check exact provenance using the source bytes it owns. Reject unsupported format and nonmatching spans to unknown. Keep the proposed label, admitted label, and quote for review. Test the resulting relation in the same frozen selector and receipt model, with correct authored readings as a control. This changes the generation prompt as well as enforcing the quote's existence. It supplies the local subclaims and their source assignments.

The reader gets 12/16 local relations correct on UNIFIL and Colombia, compared with 11/16 under the earlier next-label protocol. The fully delivered packet yields 7/8 correct dispositions, up from 5/8. The two earlier false retentions disappear. One false revision remains because the China source says the text fell short of fully addressing Lebanon's concerns. That passage leaves open whether China said the text addressed some concerns. On Haiti and Mali the reader gets 9/12, including two verbatim quotes that fail to establish the positions assigned to the speakers. The exact gate rejects three proposed non-unknown readings across the four dockets. In one case the model copies “without further conditions” from the claim and the host correctly rejects it. In the other two, it replaces the source’s pronoun with the speaker’s name, changing the literal quote while preserving the meaning. The gate checks provenance and the relation keys check meaning.

[Captured generations and exact replay inputs](facilitator-witness-evidence/transcript.jsonl) · [Every admitted and rejected reading](facilitator-witness-evidence/results.json)

| Frozen learned router on split holdings | Valid retain | Valid revise | False action | Mean send cost | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Earlier next-label readings | 7.90% | 18.56% | 17.18% | 0.108 | −0.015 |
| New quote prompt, raw relation labels | 7.90% | 18.20% | 14.79% | 0.089 | 0.025 |
| New prompt with exact quote admission | 7.90% | 15.63% | 14.79% | 0.080 | 0.007 |
| Exact quote admission with authored semantic veto | 7.90% | 18.56% | 0.00% | 0.066 | 0.199 |
| Authored local relations | 7.90% | 21.13% | 0.00% | 0.074 | 0.216 |

The raw-label replay ignores quote provenance while keeping the very same generated responses. Exact admission blocks a real contradiction on one side of the Colombia proposal that calls for immediate unconditional verification. It leaves the split false-action rate unchanged. The semantic veto is diagnostic only. It uses the authored keys to downgrade erroneous admitted relations to unknown and leaves missing relations missing. With the exact gate, the frozen learned policy scores 0.007 net on split holdings compared with −0.030 when acknowledgments are erased and −0.026 for greedy routing. The absolute false-action rate remains 14.79%. A strong next test is to compare a separate entailment check against that veto on weak versus strong wording and correct versus incorrect attribution, with missing support reported alongside false actions.

These are generated local reads and exact simulated receipt replays over exposed event families, with the same assistant's case keys and a fixed send fee. They measure disposition and attribution rather than the fidelity of a newly generated final record.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_witness.py score facilitator-witness-evidence | cmp - facilitator-witness-evidence/results.json
"$MODEL_PY" facilitator_witness_replay.py | cmp - facilitator-witness-evidence/routing-replay.json
```

### Judge whether the cited words establish the proposed relation

Take the 19 non-unknown documentary readings that passed exact admission. Ask frozen Qwen to verify each relation in a separate call using the claim, the candidate relation, the highlighted witness, and the enclosing source for reference resolution. The judge can affirm the proposed relation, find insufficient evidence, or find the opposite relation. The router uses a relation only when the judge affirms it in both presented option orders. Unknown input relations stay unknown. The judge can abstain but cannot recover a valid relation that the first pass or exact quote gate discarded.

The two-order gate retains 12 of 15 correct relations and blocks two of four incorrect relations. Five of 19 decisions change with the option order. It drops all three valid contradictions that reached the judge. It still accepts the invalid inference that China’s statement about incomplete coverage establishes that the text addressed *none* of Lebanon’s concerns and accepts the inference that supporting authorization under Chapter VII establishes how the A3 voted. On the eight full UNIFIL and Colombia packets, disposition accuracy falls from 7/8 to 5/8. Both intended revisions become withhold decisions.

| Frozen learned router, split holdings | Valid retain | Valid revise | False action | Net |
| --- | ---: | ---: | ---: | ---: |
| Exact quote admission | 7.90% | 15.63% | 14.79% | 0.007 |
| Judge, first option order only | 7.90% | 9.28% | 9.28% | 0.013 |
| Judge, reversed order only | 7.90% | 0.00% | 9.28% | −0.069 |
| Judge, agreement across both orders | 7.90% | 0.00% | 9.28% | −0.069 |
| Authored semantic veto | 7.90% | 18.56% | 0.00% | 0.199 |

Keep the exact-quote baseline. A review prompt that asks about support and contradiction relative to a supplied label makes two polarity reversals possible. The material next comparison is to ask separately what proposition the text establishes and whether that proposition can coexist with the claim, then test on matched modal and attribution contrasts. Keep valid revision and false-action rates visible so abstention on every contradiction cannot pass as improved decision quality. The result is based on the same frozen model, development examples, and simulated routing, with no new final records or policy updates.

The archived launch script preserves the original byte hash. A scoring-only tuple unpack was corrected after launch. The scorer verifies the archived digest and reconstructs every prompt and option order before replaying the captured scores.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_entailment.py score facilitator-entailment-evidence \
  --launch-script facilitator-entailment-evidence/launch-script.py | cmp - facilitator-entailment-evidence/results.json
```

[Exact prompts and next-label scores](facilitator-entailment-evidence/actions.jsonl) · [All judge decisions, full packets, and routed replays](facilitator-entailment-evidence/results.json)

### Judge the source-to-claim relation directly

Give frozen Qwen the exact witness, the enclosing passage for resolving references, and the assertion. The premise comes first. The earlier reader's relation and the expected answer are absent from the prompt. The three options describe what the cited words establish, rule out, or leave unresolved. Run both option orders and use unknown on disagreement. Test two ways to pass the reading to the frozen router. The agreement gate keeps an earlier reading if the direct judge independently reaches the same relation. The replacement arm uses the direct judge's relation. Both arms operate only on the 19 admitted witnesses, so neither can recover a relation whose witness was rejected upstream.

Add eight local contrasts that reuse cited words and vary the assertion. For example, language about incomplete coverage rules out full coverage, supports a claim of incomplete coverage, and leaves zero coverage unresolved. Support for adoption is documented and opposition is contradicted, while the vote remains unresolved. These authored contrasts stay outside routing replay.

The direct judge recovers all three valid contradictions, compared with zero for the previous relative-relation judge. It gets 15/19 archived reads correct and 8/8 authored contrasts correct. Seven archived reads and two contrasts depend on presentation order. The two orders swap the supported and unresolved options and keep the contradiction option in the middle. The one stable wrong reading is on Mali. The judge treats language stating that an extension would be final as a contradiction of the assertion that Russia called it the final extension. The agreement gate withholds that reading.

| Frozen learned router, UNIFIL and Colombia split holdings | Valid retain | Valid revise | False action | Net |
| --- | ---: | ---: | ---: | ---: |
| Exact quote admission | 7.90% | 15.63% | 14.79% | 0.007 |
| Earlier judge with two-order agreement | 7.90% | 0.00% | 9.28% | −0.069 |
| Direct judge with agreement gate | 3.95% | 18.56% | 0.00% | 0.171 |
| Authored semantic veto | 7.90% | 18.56% | 0.00% | 0.199 |

Both direct-judge variants score 7/8 with full packets. They correct the false revision on Lebanon but withhold a valid Colombia common-ground statement after an order disagreement on the African members' conditional position. With the same agreement-gated readings and split holdings, the frozen learned router scores 0.171 net, the acknowledgment-erased version scores 0.137, and the greedy script scores 0.149. The greedy script retains more valid common-ground statements at a higher send cost. Net utility subtracts the simulated send cost and excludes inference costs.

Replay the six Haiti and Mali cases against the existing 24 reviewed facilitator briefs across receipt masks. With split holdings, the gate raises usable revision from 9.61% to 12.36% and lowers usable retention from 10.53% to 5.26%. False actions stay at zero. Using the judge's relation without agreement creates 12.37% false actions from the Mali polarity mistake. A brief counts only if its archived wording passed review and the newly routed disposition agrees with the action warranted by the actual receipt. The replay uses the same-assistant case keys and previous prose grades. Event families were previously exposed, the eight contrasts are authored, delivery is simulated, and no new final record or policy update enters this comparison.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_source_relation.py score facilitator-source-relation-evidence | cmp - facilitator-source-relation-evidence/results.json
"$MODEL_PY" facilitator_source_relation_briefs.py | cmp - facilitator-source-relation-evidence/brief-replay.json
```

[All 54 prompts and scores](facilitator-source-relation-evidence/actions.jsonl) · [Judge and policy results](facilitator-source-relation-evidence/results.json) · [Archived-brief replay](facilitator-source-relation-evidence/brief-replay.json)

### Generate a fresh chair brief for the routed receipts

Freeze four development proposals before generation, including a valid common-ground statement from each event, the UNIFIL weaker-coverage contrast, and the Colombia immediate-verification contrast. Generate all four receipt masks per proposal. At each mask use the same writer, source cards and 104-token cap. The pooled writer chooses its own disposition. The quote and agreement arms receive only their mechanically composed disposition, not additional documentary sources. Byte-identical staged prompts share one capture.

Score the final brief out of 70. The heading earns 14 if it records the disposition warranted by the evidence actually received. Each speaker earns 12 for a faithful, relevant position with its decisive condition, or for explicitly leaving that speaker's claim unverified when evidence is insufficient. A global insufficiency statement can cover both speakers on an empty packet. Provenance earns 10 if each documented position has its own verified citation and every cited ID exists in the packet. Factual and authority fidelity earns 12 in the absence of unsupported attributions, polarity reversals, premature authorization, or claims that a speaker did the opposite of what the source permits. Format earns 10 for the requested one-line heading and body, a finished generation and a 48-word maximum. A strict pass requires all 70 points.

For UNIFIL assess continuing work or the claim about what portion of Lebanon's concerns the text addressed, as appropriate. Saying the text did not fully address Lebanon's concerns leaves the weaker claim unsettled. For Colombia, retain Brazil's hope for authorization when sufficiently mature and the African members' reliance on the Secretary-General's conditions. The Council's actual adoption, authorization and future conditions are separate from what each speaker supported. For the immediate unconditional proposal these qualifications are the grounds for correction. Require exact candidate spans for each credited speaker and any critical error. Report raw field coverage and strict eligibility separately. Present outputs for review without the prompting arm or its suggested disposition.

The model generates 35 distinct briefs. The 16 pooled prompts have no decision hint. The staged prompts share the same writer and use the already observed quote or agreement labels. Retain/revise cases account for 11 of the distinct prompts. None passes the strict rubric. Eight of the 24 withhold outputs pass. Three actionable outputs have a correct disposition, complete attributed positions and a valid format, and lose only the provenance criterion. They group source IDs at the end, including one combined bracket group that fails the individual-ID syntax. The A3-only Colombia correction is cited correctly but does not explicitly say that Brazil's position is unavailable.

| Split delivery | Final record out of 70 | False actionable heading | Strict pass | Usable retain or revise |
| --- | ---: | ---: | ---: | ---: |
| Full-access pooled writer | 38.50 | 25.00% | 0.00% | 0.00% |
| Pooled writer on the same packets as agreement routing | 45.76 | 19.78% | 28.75% | 0.00% |
| Quote-only learned routing and writer | 49.26 | 18.56% | 19.23% | 0.00% |
| Agreement-gated learned routing and writer | 62.44 | 0.00% | 46.24% | 0.00% |
| Agreement-gated learned router with acknowledgment erased | 62.44 | 0.00% | 46.24% | 0.00% |
| Agreement-gated greedy routing and writer | 57.21 | 0.00% | 20.44% | 0.00% |

A false actionable heading is a parseable retain or revise when the delivered evidence warrants a different disposition. The gain from agreement persists when the same receipt masks feed the pooled writer, and erasing acknowledgment leaves the agreement results effectively unchanged. In this setup, the chair receives a safer decision hint and often produces a valid abstention. It produces no strictly usable publication or correction. The next writer comparison can bind supported statements to source IDs before document rendering and assess uncovered sides explicitly.

The evidence consists of fresh writing from two exposed event families with proposals chosen to exercise earlier reader differences. Routing and erasure are exact simulated packet delivery. The reviewer is the same assistant and sees source cards and final answers without arm labels. The pooled writer on the same receipts isolates use of the hint. The erasure arm isolates the acknowledgment, and this experiment has no generated independent-draft arm. The send cost excludes reader and chair inference. There are no policy updates.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_fresh_brief_score.py review facilitator-fresh-brief-evidence | cmp - facilitator-fresh-brief-evidence/review-inputs.json
"$MODEL_PY" facilitator_fresh_brief_score.py score facilitator-fresh-brief-evidence | cmp - facilitator-fresh-brief-evidence/results.json
```

[All final outputs](facilitator-fresh-brief-evidence/final-records.json) · [Arm-hidden review packet](facilitator-fresh-brief-evidence/review-inputs.json) · [Exact-span rubric evidence and replay](facilitator-fresh-brief-evidence/results.json)

### Bind each speaker's wording to the card the chair actually receives

Keep the same four proposals and receipt masks. Generate one 21-word field per speaker from that speaker's source and the proposal. The generator sees neither the other speaker's passage nor the answer key. Compose the heading from the same frozen readings as before. For each received card, append its actual source ID immediately after the raw field. For each undelivered card, render a fixed statement that the speaker's position is unverified. The body can use two sentences on one line within the original 48-word budget. This changes the earlier prompt's request for one sentence and retains the previous scorer's one-line format criteria.

Apply the previous 70-point rubric and hand-check each distinct raw field once against the same source key. The renderer attaches provenance and records receipt absence. A field that exaggerates diplomatic commitment, loses a decisive condition, or withholds a documented position still loses rubric points. Use the existing pooled chair outputs and recompute the same learned, acknowledgment-erased and greedy receipt distributions. Keep usable retention, usable revision and warranted abstention distinct.

Eight new generations produce 167 output tokens including end markers. All eight finish. Seven contain the decisive speaker field. Brazil's source says the UNIFIL text addressed **some** of Lebanon's concerns. On that specific proposal, the generated field drops the qualifier and earns no credit for the position. Four of the 19 assembled heading-and-receipt combinations pass the full rubric when the evidence warrants retaining or revising. The earlier unstructured writer produced zero usable actionable briefs.

| Split delivery, with bound fields | Usable retain | Usable revise | False action | Send cost | Net actionable utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| Quote-only learned router | 15.79% | 18.56% | 18.56% | 0.114 | 0.043 |
| Agreement-gated learned router | 7.90% | 18.56% | 0.00% | 0.070 | 0.195 |
| Agreement-gated learned router, acknowledgment erased | 1.19% | 18.56% | 0.00% | 0.067 | 0.130 |
| Agreement-gated greedy router | 9.35% | 18.61% | 0.00% | 0.103 | 0.177 |

Net actionable utility adds usable retentions and revisions, then subtracts false actionable headings and simulated send cost. The acknowledgment raises publishable retention on the UNIFIL continued-work proposal from 4.75% to 31.59%. The other three proposals contribute no usable retention gain. On the four-case mean, usable retentions and revisions together rise from 19.74% to 26.45%. The greedy script yields 27.95% at higher simulated send cost. Inference costs are outside this replay. Agreement's 92.47% overall strict rate includes 66.01 percentage points of warranted withholds.

For the A3-only Colombia correction, the rendered brief states that Brazil's position is unverified and preserves the African members' condition on the Secretary-General with its own citation. This composition is rule-based and reuses actual generated fields under simulated receipts. The exposed dockets, authored answer key and same-assistant review make the result a development test. The paired change tests an acknowledgment, not free-form discussion.

The archived launch script preserves the original checksum. A verifier-only recursion was fixed after generation. The repaired verifier recreates each prompt, token sequence and raw output from the frozen run before scoring.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_bound_field_score.py facilitator-bound-field-evidence | cmp - facilitator-bound-field-evidence/results.json
```

[Unedited generated fields](facilitator-bound-field-evidence/final-records.json) · [Rendered briefs, exact spans and results](facilitator-bound-field-evidence/results.json)

### Transfer the source-bound facilitator to Abyei and the Central African Republic

Use two event families absent from the previous facilitator cases and freeze four proposals before generation. The Abyei proposals test agreement on the mission's importance versus agreement on the vote. For the Central African Republic, distinguish willingness to extend the mission from support for the specific one-year extension adopted. The reference cards paraphrase delegate statements on pages 2–3 of S/PV.9785 and pages 4–6 of S/PV.10041. They are short, actor-scoped records, and do not supply the proposal relations. [Abyei meeting record](https://digitallibrary.un.org/record/4066875/files/S_PV.9785-EN.pdf) · [Central African Republic meeting record](https://digitallibrary.un.org/record/4093326/files/S_PV.10041-EN.pdf)

Run the archived witness prompt and exact-span check, both orders of the direct entailment prompt, and the speaker-bound writer. This run uses generated menu letters rather than masked next-token logits for the auditor. Accept an audit only when the model emits one valid letter and finishes. Hold the routing policy, citation binding, source-card states, and 70-point brief rubric fixed. The pooled analyst and the independent-drafts synthesis both receive the same delivered cards and the same final answer cap. The synthesis additionally sees the two independently generated source notes when both arrive. Compare inference budgets separately because the extra note calls change the total computation. The same assistant reviews synthesis outputs with arm labels hidden and reviews the separate fields against the speaker keys.

For the primary comparison, report usable retentions and revisions, false headings, score out of 70, and cost-adjusted utility. Include acknowledgment erasure, greedy routing, and authored local relations to locate failures. The full-access pooled result has a different information budget and is a ceiling comparison on source availability.

The 60 calls include eight source fields, eight witness reads, 16 generated choice letters, 16 pooled briefs, and 12 independent-draft syntheses. The empty receipt uses the same pooled response in both writing arms. The quote reader gets all eight local relations right. The agreement judge rejects a valid second-speaker support relation in each common-ground proposal, so both full packets lose their route to retention. These are order disagreements. The judge agrees on both contradictions.

| Split delivery | Usable retain | Usable revise | False actionable heading | Final score /70 | Net actionable utility |
| --- | ---: | ---: | ---: | ---: | ---: |
| Pooled writer, agreement receipts | 0.00% | 0.00% | 18.40% | 50.51 | −0.261 |
| Independent-draft synthesis, agreement receipts | 0.00% | 0.00% | 25.93% | 49.54 | −0.336 |
| Quote-only learned router, bound fields | 7.90% | 14.41% | 0.00% | 60.48 | 0.100 |
| Quote-only learned router, acknowledgment erased | 1.19% | 14.40% | 0.00% | 61.22 | 0.039 |
| Quote-only greedy router, bound fields | 9.35% | 13.62% | 0.00% | 58.91 | 0.087 |
| Agreement-gated learned router, bound fields | 0.00% | 14.41% | 0.00% | 63.56 | 0.067 |

Every usable retain or revise comes from the Central African Republic. The acknowledgment helps deliver the two supports for the narrower proposal about extending the mandate, although the greedy policy releases slightly more actionable briefs overall. The learned policy uses fewer paid sends. The agreement gate's higher raw brief score includes more withholds and fewer publishable records. The authored-relation control produces precisely the quote-only learned result, so it cannot fix the remaining errors. For example, the Abyei writer sometimes reports a reservation about bringing the draft to a vote in place of China's actual affirmative vote. The Russia field calls a documented abstention unverified. The China MINUSCA field says China adopted the one-year extension, which confuses one delegate's vote with the Council's act. Keep these as separate rubric failures.

The event families are new to this facilitator protocol and the authors supplied the proposals, source summaries, and reference keys. Model pretraining exposure is unknown. This is same-assistant semantic review over four proposals and simulated receipts. The staged renderer carries extra inference calls, including 4,606 prompt tokens for its agreement audit. This comparison matches delivered evidence and the synthesis output cap, with total inference budgets recorded separately. Neither arm makes a new policy update.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_event_transfer_score.py review facilitator-event-transfer-evidence | cmp - facilitator-event-transfer-evidence/review-inputs.json
"$MODEL_PY" facilitator_event_transfer_score.py score facilitator-event-transfer-evidence | cmp - facilitator-event-transfer-evidence/results.json
```

[Case cards and reference keys](facilitator-transfer-panels.json) · [Raw generations](facilitator-event-transfer-evidence/final-records.json) · [All policy comparisons and exact-span marks](facilitator-event-transfer-evidence/results.json)

### Train routing on reviewed briefs and balance source positions

Fit two joint policies from uniform with the existing exact policy-gradient optimizer. Both use 180 updates, the same rosters and send fees, and the same 10 development proposals. Include the four UNIFIL and Colombia cases and six archived Haiti and Mali cases. The Haiti and Mali cases supply the only receipts on which the decision and prose rewards differ. Each proposal contributes equal mass under the quote and agreement reading channels. Only the terminal reward changes. A correct actionable disposition earns one in the decision fit. In the brief fit it earns one only if the archived brief meets the strict rubric. Both charge one for an unsupported actionable disposition, zero for withholding, and the existing per-send fee. Every actor still sees its local source relations and its messages. No actor sees the reference grade, event ID, or another desk's holdings.

Two of 80 development receipt-channel combinations separate the objectives. Both are presentations of the same Haiti correction when both cards arrive. The decision and brief fits earn 0.13134 and 0.13197 on the development brief objective, compared with 0.11499 for the frozen policy. On the excluded Abyei and Central African Republic dossiers, the brief fit regresses. With quote reading and split holdings, usable revisions fall from 14.41% to 9.27%. Usable retention is approximately 7.9% for all three learned policies. The fitted policy sends the decisive United States card alone on 37.08% of MINUSCA correction episodes, versus 57.65% for the frozen policy. It sends the China card alone more often, and that receipt cannot establish the objection. The shift explains the aggregate loss in usable revisions.

The follow-up fit uses the same brief rewards while giving equal weight to the original and reversed assignment of source addresses. Reversal keeps each real source, its local relation, and the associated receipt grades together. The new fit recovers some performance in the original assignment and makes outcomes invariant to source position within numerical tolerance. The original brief fit earns 0.061 in the original assignment and 0.108 when the test slots reverse. The balanced fit earns 0.077 in both. The frozen policy stays at 0.100.

| Split holdings with quote readings | Usable retention | Usable revision | Net actionable utility |
| --- | ---: | ---: | ---: |
| Frozen learned | 7.90% | 14.41% | 0.100 |
| Greedy local script | 9.35% | 13.62% | 0.087 |
| New decision-reward fit | 7.92% | 9.27% | 0.061 |
| New brief-reward fit | 7.92% | 9.27% | 0.061 |
| New brief-reward fit with balanced slots | 7.90% | 10.31% | 0.077 |
| Slot-balanced fit with acknowledgment erased | 1.18% | 10.30% | 0.015 |

Keep the frozen router as the transfer baseline. A reward comparison needs several independently written cases where a correct disposition yields an unusable brief, in both source positions. A single archival writing failure repeated in two channels provides little evidence about which terminal objective generalizes. The result is a retrospective transfer replay with same-assistant grades and simulated delivery, with no new drafting or LLM weight updates. All three optimization runs fit only tabular routing policies. No evaluation rows enter their training batches.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_record_policy.py | cmp - facilitator-record-policy-results.json
"$MODEL_PY" facilitator_slot_balance.py | cmp - facilitator-slot-balance-results.json
```

[Matched-reward fits and full receipt distributions](facilitator-record-policy-results.json) · [Balanced placement and swap intervention](facilitator-slot-balance-results.json)

### Give the speaker-field writer the decisive witness

Keep the routing weights, source cards, relation labels, and final record rubric fixed across eight proposals. Four are from UNIFIL and Colombia development and four are from the Abyei and Central African Republic transfer. Give the frozen writer the same one-speaker assertion and 21-word budget in both new arms. Only the witness arm receives the previously admitted exact excerpt. The prompt asks both arms to preserve the vote, speaker and institutional act. An unavailable witness uses the assertion-only output, and the receipt model still renders unavailable sources as unverified. The old joint-assertion field serves as a separate baseline.

Score the same required position, qualification and attribution for each speaker. For example, a Russia field that calls its vote unverified and also says it abstained gets credit for mentioning the abstention and fails the factual guard. A China field that says China itself adopted the measure fails the authority guard. The first-stage reviewer receives the source, one-speaker assertion and raw generated sentence with the arm and witness removed. Reuse the earlier citation binding and final record scorer.

Thirty-one calls produce sixteen assertion-only fields and fifteen paired witness fields. In Abyei and the Central African Republic, both new prompts produce seven of eight fields complete and free of critical errors, up from four with the original joint prompt. Both recover China's recorded vote and Russia's abstention on the Abyei resolution. The witness fixes the one-year duration in a MINUSCA correction, while dropping it from the MINUSCA common-ground draft. Under the frozen rubric, the omitted duration costs a field in either case.

| Transfer with split evidence and quote-only learned routing | Usable retention | Usable revision | Usable actionable briefs | False actionable heading | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Original joint-proposal field | 7.90% | 14.41% | 22.31% | 0.00% | 0.100 |
| One-speaker assertion | 15.79% | 32.97% | 48.76% | 0.00% | 0.365 |
| One-speaker assertion plus witness | 7.90% | 37.12% | 45.01% | 0.00% | 0.327 |

With the assertion-only writer, erasing the acknowledgment reduces usable actionable briefs from 48.76% to 35.33%. The greedy script yields 50.92%, with net utility of 0.367 at the fixed send fee. The learned router's net utility is 0.365. The writer change therefore increases the value of the brief channel and leaves the greedy script narrowly ahead overall on this set. The corresponding witness condition is 45.01%, against 38.29% with erasure and 46.56% for greedy. Inference costs are excluded from these utility figures.

On development, the witness recovers Brazil's precise “some” scope on UNIFIL. In the immediate-verification control, the one assertion-only output used in both arms turns Brazil's conditional hope into a call. For agreement routing, the extra strict passes from the witness arise from withholds. Its actionable rate stays at about 26.44%, close to the prior 26.45%. Keep the specific actor, modal force, vote and time constraint explicit in future writer comparisons. The sample is same-assistant review of exposed dockets and generated fields with simulated receipt. No reader, policy, or model weights change.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_witness_writer_score.py review facilitator-witness-writer-evidence | cmp - facilitator-witness-writer-evidence/review-inputs.json
"$MODEL_PY" facilitator_witness_writer_score.py score facilitator-witness-writer-evidence | cmp - facilitator-witness-writer-evidence/results.json
```

[All generated fields](facilitator-witness-writer-evidence/final-records.json) · [Arm-hidden review packet](facilitator-witness-writer-evidence/review-inputs.json) · [Exact-span scoring and final-record replay](facilitator-witness-writer-evidence/results.json)

### Price acknowledgment and retrain the independent control

Train the independent policy from uniform for 180 updates on the same class-balanced synthetic relation pairs as the frozen adaptive fit. Both desks can send one of their two local cards or pass. The second desk in the independent arm never receives acknowledgment. Keep the previously generated quote reads, one-speaker drafts, and chair renderer identical. This separates a policy trained for independent operation from erasing the message expected by a policy trained to use it.

On split Abyei and Central African Republic, the independent control delivers publishable briefs in 45.92% of cases. The frozen policy with acknowledgment erased delivers 35.33%. With acknowledgment, it reaches 48.76% and attempts 1.23 payloads and 0.75 acknowledgments per case. The retrained independent controller attempts 1.67 payloads. At a 0.10 payload fee, the adaptive model's advantage over the trained independent control disappears when each attempted acknowledgment costs about 0.097. If acknowledgment is free, the frozen learned router overtakes greedy at a payload fee of about 0.111. These break-even prices revalue the same fixed decisions. The shared transfer cache contains 16 calls for witnesses and speaker fields with 3,674 input and 408 output tokens. All routing arms reuse it. The replay measures message attempts and synthetic fees, with no measured production inference cost or latency.

Fit two joint policies at equal payload and acknowledgment fees of 0.10. In the optional arm the first desk can send, send with acknowledgment, or pass. The second desk observes the acknowledgment only after first-payload delivery and successful peer transmission. In the mandatory arm any delivered first payload incurs an acknowledgment attempt. Both use the same synthetic world mixture, optimizer, and 180 steps per fit. Evaluate on the archived prose using unchanged receipt masks, grades and links.

| Split transfer at equal fees | Usable retention | Usable revision | Payload attempts | Acknowledgment attempts | Net |
| --- | ---: | ---: | ---: | ---: | ---: |
| Frozen learned with feedback | 15.79% | 32.97% | 1.227 | 0.749 | 0.290 |
| Retrained independent | 17.09% | 28.83% | 1.665 | 0.000 | 0.293 |
| Greedy with feedback | 18.69% | 32.23% | 1.422 | 0.750 | 0.292 |
| Trained optional feedback | 17.08% | 28.93% | 1.662 | 0.006 | 0.293 |
| Retrained mandatory feedback | 2.10% | 37.10% | 0.541 | 0.302 | 0.308 |

The optional fit behaves almost like independent routing at this fee. The fit with mandatory paid feedback earns the highest net utility and publishes far fewer valid joint statements. On split development its net is −0.074 versus −0.065 for independent. Publishable actions, coverage by disposition, and assumed cost remain separate benchmark objectives. Higher cost-adjusted utility alone would hide the loss of valid joint statements. This is one exact control per protocol using simulated delivery and previously scored prose. Policy training excludes all documentary cases.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_feedback_cost.py | cmp - facilitator-feedback-cost-results.json
"$MODEL_PY" facilitator_optional_feedback.py | cmp - facilitator-optional-feedback-results.json
```

[Independent control and fee break-even points](facilitator-feedback-cost-results.json) · [Optional and mandatory paid-feedback fits](facilitator-optional-feedback-results.json)

### Let delegates revise after seeing each other's actual draft

Freeze four proposals from two previously unused facilitator dossiers. Bosnia separates two affirmative EUFOR votes from disagreement over the Office of the High Representative. Afghanistan separates agreement on the one-year UNAMA extension from a claim that both delegations described the initial draft circulation the same way. China described initiating and advancing consultations. Pakistan said China and Pakistan circulated the initial draft together. Treat these as distinct procedural acts. [Bosnia meeting record](https://digitallibrary.un.org/record/4065952/files/S_PV.9774-EN.pdf) · [Afghanistan meeting record](https://digitallibrary.un.org/record/4079147/files/S_PV.9880-EN.pdf)

Each arm uses two opening calls, two revision calls and one final call with the same per-stage token caps. The private arms share byte-identical openings. Independent revision sees its own source and opening. Peer revision also sees the other desk's actual opening. The pooled solo analyst makes the same two speaker-focused passes with both source cards, then revises its own working notes. The chair sees both source cards and the two revised notes in every arm. Its instruction, available sources and format stay fixed. This tests language effects conditional on complete final delivery and does not use a learned routing policy.

Score the chair brief on the shared 70-point rubric. At the note level distinguish a speaker's relevant point from its documentary warrant, including the actor who cast a vote, the duration, the reason for the objection or the separate procedural acts. Compare each revision with the shared opening and its independent revision. Count visible turns and actual tokens separately. A paraphrase alone provides no evidence of productive peer influence. Hide arm metadata and prior messages during same-assistant exact-span review.

The evaluator sees one response at a time with the underlying source cards and prewritten criteria. For each earned criterion it records an exact response span. For omissions it leaves the span blank. For a factual error it records the exact claim and the source distinction it violates. An exact citation must support its attached clause. A working note cannot establish a delegate's position. Apply the heading decision independently of the body, and record heading correctness again after allowing punctuation in place of the separator. These checks distinguish decision disagreement from syntax errors.

| Four cases per arm | Mean final score /70 | Strict passes | Correct printed headings | Revised points | Revised warrants | Input tokens | Output tokens |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Independent | 49.5 | 1/4 | 2/4 | 7/8 | 6/8 | 5,877 | 521 |
| Peer-visible | 49.5 | 1/4 | 2/4 | 7/8 | 6/8 | 6,102 | 528 |
| Pooled solo | 41.0 | 1/4 | 2/4 | 7/8 | 5/8 | 7,371 | 558 |

Peer visibility changes the text of two of eight revisions without improving any required point, warrant or final score. Russia rephrases its existing position on the Office of the High Representative. Pakistan adds continued cooperation with UNAMA from its own source. That addition does not appear in the final. The lower pooled average comes entirely from the initial-circulation case, where the pooled working note attributes Pakistan's account to China and the chair repeats it. The private arms keep the distinction in the body and still print retain. All three arms recognize Russia's proposal to close the Office in the body and print withhold instead of revise. The strict pass is the one-year Afghanistan renewal in every arm. This source-family pilot uses authored summaries, frozen Qwen, and same-assistant review. It measures peer-text visibility with complete delivery and five calls per arm. A claim about the interaction benefit of a learned policy remains open.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_deliberation_score.py review facilitator-deliberation-evidence | cmp - facilitator-deliberation-evidence/review-inputs.json
"$MODEL_PY" facilitator_deliberation_score.py score facilitator-deliberation-evidence | cmp - facilitator-deliberation-evidence/results.json
```

[Official source links and frozen proposals](facilitator-deliberation-panels.json) · [Raw openings, revisions and finals](facilitator-deliberation-evidence/final-records.json) · [Exact-span review and matched comparison](facilitator-deliberation-evidence/results.json)

### Ask for the evidence that decides a disputed heading

Reuse the four Bosnia and Afghanistan proposals and their private openings. One desk generates a question using only its own card, the other desk's identity and the joint claim. The harness fixes the recipient in advance. Run an identical source-local answer prompt with and without the generated question. The chair in both arms sees the same question, openings, source cards, and answerer identity. It additionally sees the answer generated by that arm. A third chair sees the same packet with the answer omitted and uses one fewer call. All chairs receive the same reminder to keep the heading consistent with the body and to distinguish documented contradiction from uncertainty.

Grade the question for whether it targets a distinction the addressee can verify from its own card. For example, the addressee can report that its card does not establish draft circulation. Grade the reply's relation, exact quoted evidence and whether the decisive part of the proof is present. For unresolved claims distinguish an explicit missing-evidence answer from an exact quote documenting a related act. Then score the final record using its source cards and the frozen rubric with arm, question and reply hidden. Compare exact sentence changes and the affected source criterion. A better reply counts as a successful intermediate answer, even if the chair fails to change its decision. [Bosnia source](https://digitallibrary.un.org/record/4065952/files/S_PV.9774-EN.pdf) · [Afghanistan source](https://digitallibrary.un.org/record/4079147/files/S_PV.9880-EN.pdf)

The answering desk gets the key relation right in all four asked replies versus three independent replies. On the Afghanistan circulation proposal, the independent answer treats the consultation excerpt as a contradiction. The asked answer correctly says the source is silent on initial circulation and explains the distinction. It uses a paragraph without the required delimiter, so the exact reply gate rejects it. Most other replies put quotation marks around a literal excerpt. Removing those outer marks would admit the independently mislabeled consultation excerpt too. Keep surface formatting, quote provenance, and semantic sufficiency distinct.

| Four proposals per arm | Semantically usable replies | Strictly usable replies | Correct printed headings | Mean final /70 | Strict final passes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Independent source check | 3/4 | 0/4 | 3/4 | 50.5 | 0/4 |
| Answer after question | 4/4 | 1/4 | 3/4 | 53.5 | 0/4 |
| Omit reply | — | — | 3/4 | 44.5 | 0/4 |

The Afghanistan circulation brief gains 12 points because the chair preserves both China's consultation statement and the uncertainty about circulation. All three chairs print the same correct withhold heading on that proposal. On Bosnia's contested Office, all three print withhold even though the asked chair's own body explicitly calls the evidence a direct contradiction requiring revision. The independent and asked chair prompts there are byte-identical and have identical token IDs. The batched run produced different wording with the same grade, so do not attribute that difference to the question. Deduplicate identical final prompts in future comparisons.

This run evaluates 24 frozen-model generations on the four exposed proposals. The known routing recipient, authored source summaries, and same-assistant review limit the scope. The asked and independent arms each use 12 new calls over the four cases. The no-reply arm uses eight. The shared openings are archived. Future reward comparisons need to separate a usable intervention, changes to the final record, and publication eligibility.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_clarification_score.py review facilitator-clarification-evidence | cmp - facilitator-clarification-evidence/review-inputs.json
"$MODEL_PY" facilitator_clarification_score.py score facilitator-clarification-evidence | cmp - facilitator-clarification-evidence/results.json
```

[Question, reply, and chair outputs](facilitator-clarification-evidence/final-records.json) · [Paired changes and exact-span grades](facilitator-clarification-evidence/results.json)

### Compute the heading from source-local relations

On the four Bosnia and Afghanistan proposals, ask the model to classify each source's relation to its one-speaker assertion. The menu distinguishes documented support, direct incompatibility, and unresolved evidence. Reverse the same option order used in earlier judge probes. The host uses unknown when the two reads disagree. The direct condition uses both independent source checks. The asked condition substitutes the answering desk's check after it sees the archived question. The other source check stays fixed. This replaces the reply's freeform delimiter with a constrained label. The label consumes the supplied source card and does not use a gold relation.

Run two rendering interventions. The first replaces only the heading of the earlier chair text. The second joins the two unchanged source-local sentences from the earlier independent desk revisions and adds the actual card ID to each. It explicitly marks uncertainty when a check defers and names absent speakers when a card is missing. The assembled body keeps the same 48-word budget and can contain two or more short sentences. Grade both with the same 70-point rubric. Authored relations supply a diagnostic ceiling for this exact writer and source collection.

Compute all four receipt masks and exactly replay the frozen learned router, its feedback-erased copy, the retrained independent policy, and greedy routing. The reader's question, where used, is supplied before the replay. Routing costs concern card delivery and exclude that question and model inference.

The constrained source reader gets 5/8 relations correct in both conditions. Reading the question changes one letter-level result and leaves all eight admitted classifications unchanged. The direct Bosnia answer is split between contradiction and unknown across option orders. The asked Bosnia answer is unknown in both. It misses Russia's explicit call to close the Office of the High Representative. The reader also defers on the United Kingdom's documented support for the Office and on Pakistan's explicit statement about initial circulation. The rule therefore misses the Bosnia revision even though both archived field sentences contain the relevant positions.

| Complete packets | Correct headings | Strict passes | Mean final /70 |
| --- | ---: | ---: | ---: |
| Replace the earlier direct heading alone | 3/4 | 0/4 | 50.5 |
| Replace the earlier asked heading alone | 3/4 | 0/4 | 53.5 |
| Bind independent fields and use direct typed reads | 3/4 | 2/4 | 58.0 |
| Bind independent fields and use asked typed reads | 3/4 | 2/4 | 58.0 |
| Same fields with authored labels | 4/4 | 4/4 | 70.0 |

With split simulated receipts, the bound record's frozen router produces publishable retentions in 15.79% and no revisions. Its feedback-erased copy reaches 2.37%, the independent router trained without feedback reaches 17.09%, and greedy reaches 18.69%. Net utility is 0.095 for the frozen learned router, 0.087 for trained independent, and 0.111 for greedy. These outcomes are identical for direct and asked reads. Asking did not improve the typed relation even where it improved the preceding freeform reply. Format enforcement and semantic verification need separate checks. Preserve the authored writer ceiling so a better relation reader can be evaluated without changing the renderer.

The evidence contains 24 frozen-model logit probes, as well as replayed previously reviewed text from exposed dockets. The authored ceiling uses the same retained text and true source relations. It measures a possible endpoint with resolved reading, with no policy-quality inference. No policy is refit here.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_typed_clarification_score.py facilitator-typed-clarification-evidence | cmp - facilitator-typed-clarification-evidence/results.json
```

[All scored source reads and composed briefs](facilitator-typed-clarification-evidence/results.json)

### Verify support and incompatibility in separate reads

Use the same source, one-speaker assertion and optional archived question as the typed clarification test. Query whether the source establishes the assertion and whether it directly rules out the assertion as two separate binary prompts. Reverse the answer order for each prompt. Accept a relation when its two options agree on yes and the other relation does not also receive two yes votes. Use unknown for dual approval or lack of a stable positive answer. Preserve raw scores and conflicting checks.

Compare with the prior three-way reader on Bosnia and Afghanistan. Repeat both formulations on the same eight previously used Abyei and Central African Republic judgments to check portability. Carry the resulting labels through the same source-bound prose, citation and receipt evaluations. For the latter two meetings keep the existing one-speaker assertion writer and replace only the heading. Preserve separate scores for correct local readings, strict final records, false actions and simulated routing costs.

| Local evidence panel | Two binary checks, both orders | Three-way check, both orders | Earlier exact-quote reader |
| --- | ---: | ---: | ---: |
| Bosnia and Afghanistan, direct | 1/8 | 5/8 | — |
| Bosnia and Afghanistan, question on target side | 1/8 | 5/8 | — |
| Abyei and Central African Republic | 0/8 | 4/8 | 8/8 |

The split reader returns unknown for all 20 observations and leaves the source-supported openings unreleased. The correct Bosnia and Afghanistan reading is the one source whose side genuinely remains unresolved. On complete packets the unchanged bound renderer falls from 2/4 strict passes to 0/4. On transfer, neither menu reader routes enough to produce a publishable action, while the earlier quote reader produces 48.76% actionable briefs with the same frozen router and the same speaker fields. All binaries withhold and therefore have zero false actionable headings.

Every first-order binary prompt selects letter B, which carries the negative answer in that order. In the reversed order, using only that presentation would score 6/8 for direct Bosnia and Afghanistan and 8/8 for Abyei and Central African Republic. It would also return a false contradiction for the asked Afghanistan circulation check. Keep the reversed-order result as a diagnostic. It cannot certify a reader whose first presentation chooses the negative label uniformly. The binary probes use 12,924 input tokens on the clarification panel against 5,982 for the three-way probes. Transfer uses 8,272 versus 3,816. These are captured prompt totals, and exclude any cost of the older freeform quote reader.

This is a frozen-reader comparison using authored source cards from exposed families and previous same-assistant prose review. The language model and policies remain fixed. Keep exact-witness generation as a measured comparator. A future verification test should check decision labels directly without letter remapping, then test the same semantics across paraphrases.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_split_relation_score.py facilitator-split-relation-evidence | cmp - facilitator-split-relation-evidence/results.json
```

[All 96 prompts and logit scores](facilitator-split-relation-evidence/actions.jsonl) · [Order diagnostics, records, and delivery replay](facilitator-split-relation-evidence/results.json)

### Put the decisive quote before or after the relation

Pair the original exact-witness prompt with the same instruction and the fields reversed. Read the same one-speaker assertion and card in both prompts. Keep unknown as a standalone reply and require all non-unknown labels to carry a verbatim contiguous span from the actual card. The known question is present only for the previously selected addressee. No answer letters or reference labels appear in the prompt. Regenerate both formats on all four clarification and four transfer proposals, including 12 clarification and eight transfer source displays per format. Log proposed relations, literal span admission, correct relation, malformed outputs, and inference tokens.

Use the existing source-bound writer and policies to score final release. The authored-label arm remains available as a writer ceiling. The earlier quote-reader run remains a separate control to detect batch-related changes in repeated inputs. This comparison treats literal quotation and correctness of the relation as separate constructs. An exact fragment may still be incomplete evidence for the proposed relation.

| Matched direct reader | Bosnia and Afghanistan relations | Strict briefs on complete packets | Abyei and Central African Republic relations | Transfer output tokens |
| --- | ---: | ---: | ---: | ---: |
| Relation then exact quote | 8/8 | 4/4 | 8/8 | 223 |
| Exact quote then relation | 6/8 | 2/4 | 8/8 | 471 |

The original format recovers Russia's call to close the Office of the High Representative, keeps Pakistan's initial-circulation statement, and correctly leaves China's side of circulation unresolved. Its four complete briefs reach the authored ceiling. Replacing only the heading in the earlier freeform body still produces zero strict passes. The asked and direct relation-first arms have identical admitted labels. In quote-first, the question recovers Pakistan's renewal quote and raises strict passes to three of four. One UK reply includes literal template text, and a Pakistan reply tries to join two noncontiguous sentences. Both fail the exact witness gate. Two unknown answers also copy the template instead of using the standalone label.

The quote-first transfer format copies seven of eight entire source cards and uses more than double the output tokens. The relation-first format copies no entire transfer card. Its eight repeated transfer prompts and outputs are byte-identical to the previous capture. Both versions reproduce 48.76% usable actionable briefs in the prior split-delivery replay. On Bosnia and Afghanistan with relation-first reads, the frozen learned router produces usable actions in 34.35% of split receipts versus 20.93% with acknowledgment erased and 35.63% for retrained independent. Greedy achieves 37.30%. After simulated payload fees, frozen learned and greedy both earn about 0.242. Retrospective replay holds both the reader evidence and the writer fixed and does not measure deployment cost.

This comparison records 40 new frozen-model generations on exposed dockets, with published syntax gates, same-assistant case keys and simulated delivery. It supports relation-first witness reading as a concrete comparator for a fresh broader benchmark. The literal witness check still requires separate semantic review before certifying the quote as proof.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_quote_order_score.py facilitator-quote-order-evidence | cmp - facilitator-quote-order-evidence/results.json
```

[Exact generations](facilitator-quote-order-evidence/final-records.json) · [Matched source scores, assembled briefs and receipt replay](facilitator-quote-order-evidence/results.json)

### Measure exact routing headroom and collisions in the source labels

Keep the previously measured relations, complete receipt bank, send fee and link odds. Enumerate each deterministic first-desk table. Given one first table, the second desk chooses its optimal action separately in each local state. The return is affine in each state's distribution when other choices are fixed, so an optimum can be taken at deterministic choices. Include all legal sends and passing, including non-target cards whose acknowledgment might provide a signal. Verify that each winning table reproduces its objective through the original receipt evaluator. The two 12-state panels require 531,441 first tables each. Abyei and the Central African Republic require 19,683. Skip text regeneration.

| Split evidence with free acknowledgment | Best adaptive | Best independent | Frozen learned | Greedy |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL and Colombia | 0.090 | 0.064 | −0.036 | −0.037 |
| Bosnia and Afghanistan | 0.251 | 0.216 | 0.242 | 0.242 |
| Abyei and Central African Republic | 0.382 | 0.323 | 0.365 | 0.367 |

The exact tables are fitted to each evaluated distribution, so their gains are ceilings for the fixed renderer and relation states. Only the UNIFIL and Colombia panel has substantial room above greedy. Train one joint router on synthetic local errors to test whether a general noise model captures that room. Independently replace each true relation with a different one 15% of the time. The fit raises net utility from 0.115 to 0.117 on that synthetic model. It leaves all three previously scored split panels effectively unchanged, including 18.56% false actions on UNIFIL and Colombia.

Inspect one identical observation shared by four cases. Each reports support for slot 1 and contradiction for slot 2. Delivering slot 2 falsely triggers revision on UNIFIL's “some concerns” proposal. It correctly triggers revision on the Bosnia Office proposal, the Abyei vote, and the Central African Republic mandate period. Because the policy receives the same local labels and roster distribution, the chance of delivering slot 2 is identical in those four cases. The noisy-panel optimum suppresses those false revisions by never delivering slot 2 in that observation. Replaying the same table on the other panels also eliminates all three valid revisions. A joint optimum over all 12 proposals instead delivers slot 2 in 74.42% of each colliding case. It accepts the false UNIFIL revisions to preserve the other outcomes.

The collision is a property of the current observation interface. The independent note or acknowledgment identifies the same received label in both situations. To learn a policy that distinguishes them, the input must carry a further source-grounded distinction, such as whether the cited act and scope actually make the proposed assertion impossible. No new model calls or official source labels enter the synthetic optimization. All language reviews and exact ceilings use exposed archives and simulated delivery.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_receipt_ceiling.py | cmp - facilitator-receipt-ceiling-results.json
"$MODEL_PY" facilitator_noisy_reader_fit.py | cmp - facilitator-noisy-reader-results.json
"$MODEL_PY" facilitator_receipt_alias_audit.py | cmp - facilitator-receipt-alias-results.json
```

[Exact decentralized ceilings](facilitator-receipt-ceiling-results.json) · [Synthetic-noise fit and transfer](facilitator-noisy-reader-results.json) · [Conflicting cases with identical observations](facilitator-receipt-alias-results.json)

### Verify that an apparent contradiction rules out the exact claim

Recheck the five contradiction labels that can reach the chair in the three facilitator panels. Give frozen Qwen the assertion, the exact witness previously accepted from the card, and its enclosing source. Ask whether the two can both be true. Require a short compatible reading or an explanation of the opposing act. The runtime preserves a contradiction only after a valid conflict response. It replaces all others with unknown. The existing source-bound writer, citation rules and router weights stay fixed. Supported and unresolved positions bypass this extra call.

Hold the exact witness fixed in nine authored controls and change the asserted vote, act, or degree of coverage. For example, China saying the text fell short of full coverage can rule out a claim of full coverage while allowing some coverage. Russia's abstention is distinct from votes in favor and against. Distinguish the response form and label from whether its explanation actually makes sense. Replay against the original reader, suppressing every contradiction, and rechecking with the authored labels. Count valid revisions and false revisions separately.

The model emits a valid short response for every prompt and chooses open all 14 times. It gets 1/5 routing labels and 7/9 control labels right. Manual review finds one sound explanation among the five routed cases. The UNIFIL label is correct, but the explanation invents China's acknowledgment of some coverage. Colombia's reply correctly identifies why verification contingent on conditions contradicts an unconditional call, yet prints open. The other three genuine objections are obscured by mixing the Bosnia Office with EUFOR, conflating support for principles with a recorded vote, or inventing a United States welcome for the adopted MINUSCA extension.

| Frozen learned router, split holdings | False actions before check | Usable revisions before check | Usable revisions after check | Usable revisions with authored check |
| --- | ---: | ---: | ---: | ---: |
| UNIFIL and Colombia | 18.56% | 18.54% | 0.00% | 18.54% |
| Bosnia and Afghanistan | 0.00% | 18.56% | 0.00% | 18.56% |
| Abyei and Central African Republic | 0.00% | 32.97% | 0.00% | 32.97% |

Both checks remove the UNIFIL false revisions. The model gate behaves exactly like suppressing all contradictions. On UNIFIL and Colombia this improves net utility from −0.036 to 0.007 by preventing false actions. The authored check reaches 0.171 while preserving valid revisions. On the cleaner panels, the model check loses net utility. Measure this trade-off before using compatibility decisions in a cooperative reward or a release rule.

This test adds 14 frozen-model generations, of which five could be invoked at runtime on these archived cases. Those five total 1,247 input and 139 output tokens. Routing utility excludes this additional inference. The proposals, controls, and explanation reviews are from the same assistant and use exposed event families. Neither model nor policy weights change.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_scope_check_score.py facilitator-scope-check-evidence | cmp - facilitator-scope-check-evidence/results.json
```

[Raw compatibility judgments](facilitator-scope-check-evidence/final-records.json) · [Explanation review and end-to-end replay](facilitator-scope-check-evidence/results.json)

### Check covered scope and recorded votes with bounded source rules

Use the same literal witness and attributed source card that entered the failed model check. When the lead sentence matches the grammar, require the same actor and concerns or the same actor and resolution identifier. Compare reported coverage by intersecting possible amounts. “Some” allows partial or full coverage, and “did not fully address” allows zero or partial coverage. Their intersection is partial coverage. Do not use this compatibility result to assert that the speaker actually stated a weaker claim. Compare voting positions as exclusive alternatives on a single recorded roll call. An abstention conflicts with an affirmative or negative vote on the same resolution. Require the unique literal quote to begin the lead sentence and include the target of the claim. Review the complete sentence for qualifiers.

Test 46 controlled inputs, including quantified cases checked by enumeration, vote pairs, and refusals for actor transfer, resolution date changes, mock scenarios, insufficient excerpts, and unrelated topics. All pass. The grammar recognizes two of the five routed candidates. It removes the false UNIFIL contradiction and independently confirms the Abyei abstention. The override retains the original reader's labels for the other three. This yields zero false actions and preserves all four genuine objections on the exposed cases. Requiring a rule result for every objection instead loses the three genuine cases outside the grammar.

| UNIFIL and Colombia, split delivery | False actions | Usable revisions | Net utility |
| --- | ---: | ---: | ---: |
| Frozen learned, original labels | 18.56% | 18.54% | −0.036 |
| Frozen learned, bounded override | 0.00% | 18.54% | 0.171 |
| Frozen learned, verified-only | 0.00% | 0.00% | 0.007 |

Recompute exact routing ceilings after the override. At the 0.10 payload fee with free acknowledgment, the split-evidence adaptive ceiling is 0.176 and the independent ceiling is 0.161. The frozen adaptive router earns 0.171, compared with 0.160 for greedy and 0.146 for trained independent. The ceiling calculation enumerates 4,782,969 first-desk tables. The observed advantage over the independent ceiling is conditional on this corrected input and simulated protocol.

This is a deterministic source-bound correction on exposed cases with synthetic controls. The original parser remains responsible for judgments outside the grammar, including institutional closure and conditional verification. Both those categories and general-source paraphrases remain unverified by the new rule. There are no new model calls or weight updates. Each prior final-record grade is reused under its exact receipt and disposition.

```bash
export OPENBLAS_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
"$MODEL_PY" facilitator_scope_rule_replay.py | cmp - facilitator-scope-rule-results.json
```

[Grammar, guard and receipt outcomes](facilitator-scope-rule-results.json)

### Transfer to ordinary source summaries on the Gulf of Guinea and Libya

The six proposals in [the frozen packet](facilitator-new-meetings.json) ask for a
facilitator's record of an observed vote or a speaker's stated position. The
cards are curator paraphrases that preserve the named speaker, roll call, and
qualifications. For the Gulf of Guinea resolution, Ghana described the scope
of the negotiated compromise and China described the scope of the law of
the sea convention itself. For Libya, Algeria spoke for the A3+ group when
calling for withdrawal. The UK card establishes a yes vote and support for
the road map towards inclusive elections. [Gulf of Guinea meeting, pp. 2–3](https://digitallibrary.un.org/record/3976027/files/S_PV.9050-EN.pdf) · [Official roll call](https://digitallibrary.un.org/record/3975658) · [Libya meeting, pp. 2–3](https://digitallibrary.un.org/record/4092101/files/S_PV.10029-EN.pdf) · [Resolution 2796](https://digitallibrary.un.org/record/4092092)

Gulf of Guinea is UNBench author-test event 2438, with fifteen matching
affirmative votes and draft S/2022/62. Its extracted draft uses the UN print
job identifier `22-08235` in its `ID` field. Libya is an official-record
extension. Neither meeting appears under the audited identifiers in the
pinned UNSC-Bench release. The docket selection excludes prior facilitator
cases and leaves pretraining exposure unknown. [Release joins](facilitator-new-meetings-evidence/provenance.json)

The frozen Qwen3.5-4B run records 12 source-local witness calls, 12
source-local field drafts, six full-access solo briefs and six independent
syntheses. The syntheses see both cards and the two local drafts. The
routing replays use those same local drafts and exact simulated receipts
for the literal reader, the scoped override and the regime that acts only
on rule-verified contradictions. There are zero optimizer updates.
All systems use the same 70-point final-record rubric and separate
disposition accuracy from the strict prose contract. The side points
require the relevant position or an explicit evidence gap. A reported vote
cannot be silently converted into a statement about how the delegate said
it voted. Semantic marks are exact spans from a same-assistant review.
[Raw outputs](facilitator-new-meetings-evidence/transcript.jsonl) · [Review](facilitator-new-meetings-evidence/review.tsv)

The reader admitted an exact quote about Ghana retaining agreed convention
language and clarifying where the piracy resolution applies. It labelled
that quote a contradiction about the convention's legal reach. The Ghana-
only packet therefore gave a false revision. Full access can conceal this
failure since China's separate statement does contradict the proposal.
The scope grammar recognized zero of the six literal contradictions on
these cards. Its fallback preserves all six, and the verified-only version
suppresses all six. The recorded vote cards use ordinary forms such as
“is listed among those voting in favour” and “the roll call records a yes
vote,” which fall outside the grammar and lead-quote requirements.
[Local readings and receipt-mask grades](facilitator-new-meetings-evidence/results.json)

Both full-access systems used a withhold heading on every documentary
contradiction. Independent synthesis sometimes retained material from
both speakers, but the final output still lacked the requested bracketed
citations or valid delimiter. The local field writer also repeatedly
described a vote as a statement by the delegate. Keep those errors separate
from relationship classification and routing. The six proposals cover two
historical events. The compared systems have different model-call budgets,
and the routed arms replay generated text rather than running live peer
deliberation.

To replay each captured prompt, input token sequence, and decoded output,
and to rebuild the scores from this directory, run these with the
Qwen environment Python. The original launch script is archived because
the first replay attempt exposed a recursive lookup of the patched hash
function. Verification now reads the original script hash and regenerates
the same requests.

```bash
python facilitator_new_meetings.py verify facilitator-new-meetings-evidence
python facilitator_new_meetings_score.py facilitator-new-meetings-evidence
python facilitator_new_meetings_provenance.py
```

The provenance command uses PyArrow and the pinned local release files.

| All cards supplied | Correct disposition | Strict brief | Mean points out of 70 |
|---|---:|---:|---:|
| Solo chair | 2/6 | 0/6 | 40.0 |
| Independent drafts and synthesis | 2/6 | 0/6 | 42.0 |
| Local readings and compiled speaker fields | 6/6 | 1/6 | 41.3 |
| Compiled with verified contradictions only | 3/6 | 1/6 | 34.3 |

With split holdings and the literal reader, the frozen adaptive router
scores 0.093 net versus 0.086 for greedy and 0.009 for the separately fitted
independent router. The exact independent ceiling is 0.083 and the exact
adaptive ceiling is 0.096. Greedy has more usable revisions (23.80% versus
22.02%) and more false actions (9.08% versus 7.34%). Net rewards a strict
retain or revise, penalizes any wrong substantive action, and subtracts
simulated payload charges. An appropriate withhold is reported separately.
Under verified-only scope, frozen false actions drop to zero, usable
revisions also drop to zero, and frozen net falls to 0.005. The corresponding
literal-reader comparison under overlapping holdings is 0.085 frozen,
0.074 greedy, 0.007 separately fitted independent, 0.083 exact independent,
and 0.092 exact adaptive. The in-cohort exact ceilings optimize tables
using these cases and the same reward and delivery assumptions.
See the [full scores and all receipt paths](facilitator-new-meetings-evidence/results.json).

The bottleneck is now identifiable before any additional routing fit.
Evaluate evidence against the exact act and its scope on single-card masks
as well as the complete packet. Use a typed roll call as a separately
supplied control for vote questions, and keep open-text position checking
as an independent hurdle. A future deliberation comparison needs a
matched-budget solo arm, a matched independent-drafts arm, and a live
interaction arm with attributable change to a source-faithful final record.

### Bind recorded acts before compiling vote briefs

This paired replay isolates two interventions on the six existing proposals.
First, substitute the official member–resolution–vote tuple only for exact
recorded-vote queries. Then also compile the received vote into a sentence
with its source ID. Preserve the previous reader and draft on the open-text
queries. A separate mixed arm requires the previous scope verification for
open-text contradictions. The tuple never establishes the speaker's reasoning,
policy support, a promised future vote, or the Council's collective authority.
[Historical roll call for 2634](https://digitallibrary.un.org/record/3975658) · [Historical roll call for 2796, page 2](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.10029&t=pdf)

The supplied tuples make no change to the vote dispositions, which were
already correct. Compiling the vote text makes all 12 nonempty vote receipts
strict, up from five. These are four proposals under three receipt masks.
The two open-text proposals still yield zero strict briefs with full
evidence. Under split holdings and the literal open-text reader, frozen
adaptive net rises from 0.093 to 0.315. Greedy reaches 0.283. The exact
independent ceiling is 0.370 and the exact adaptive ceiling is 0.402.
The prose improvement moves the achievable reward. The in-cohort exact
independent comparator now exceeds the old fitted adaptive router.

Requiring verification for open-text contradictions while retaining the
official vote channel eliminates false actions in this replay. It also
loses the genuine open-text objection from China on its own card. Frozen
adaptive net reaches 0.334, compared with 0.337 greedy, 0.309 exact
independent, and 0.342 exact adaptive. A conservative gate can look better
under a fixed policy while shrinking the achievable reward. The new search
reproduces the prior exhaustive results and checks 24 small payoff tensors
against brute force before solving the larger state space. [Bounded solver](facilitator_receipt_search.py)

Frozen Qwen3.5-4B attempted the same four historical reads and twelve
fictional controls twice. The original prompt described the desired output
with literal placeholders. It returned a vote label and the placeholder
on all four historical cards, and all four were rejected. The revised
prompt describes the output fields in prose. It elicits adequate copied
evidence on all four historical cards and six controls with recorded
votes, as checked by the same assistant. All four historical replies use
a comma, so the original parser still admits zero historical votes. A
retrospective parser accepts a comma after a recognized vote label and
continues to require an exact source substring. Under that parser the
revised run gets 4/4 historical and 12/12 fictional statuses right.
The six no-vote controls in the revised run include surplus text after
the unknown label. They resolve to unknown through the safe fallback.
The revised run meets the entire original format on 2/16 replies.
[Original trace and scores](facilitator-vote-channel-evidence/results.json) · [Revised trace and scores](facilitator-vote-channel-format-evidence/results.json)

The comma-admitted extraction replays identically to the supplied roll
calls on the four historical cards. All four votes happen to be affirmative.
The fictional controls include opposing votes, abstentions, an amendment
stage, negotiations without a vote, and evidence about a different
delegation or measure. They test specific error modes on authored language.
The header normalization was designed after inspection, and both historical
events were exposed in the previous diagnostic. This remains a component
test of retrospective evidence, with unequal previous full-chair compute
budgets and zero model updates. Keep an untouched split of actual recorded
no votes and abstentions for a subsequent test.

From this directory, reproduce the artifacts with the Qwen environment
Python.

```bash
python facilitator_vote_replay.py facilitator-vote-channel-evidence
python facilitator_vote_replay.py --revised-format facilitator-vote-channel-format-evidence
```

### Bind votes to competing drafts and amendments in the same meeting

The next packet uses actual affirmative votes, objections, and abstentions
from two meetings, with shortened member names and explicit document
symbols on each vote-group line. The outer-space meeting voted separately
on amendment S/2024/323 and on draft S/2024/302. The Gaza meeting voted on
competing drafts S/2023/792 and S/2023/795. All four documents join UNBench's
draft archive. S/2024/302 and S/2023/792 also match the pinned UNSC-Bench
vetoed rows on all 15 votes each. The meeting records supply the other two
roll calls. [S/PV.9616](https://digitallibrary.un.org/nanna/record/4045546/files/S_PV.9616-EN.pdf?registerDownload=1&version=1&withMetadata=0) · [S/PV.9453](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9453&t=pdf) · [Dataset joins](facilitator-mixed-votes-evidence/provenance.json)

Frozen Qwen3.5-4B reads each of 16 delegation–document pairs twice. It
sees both vote blocks together or the requested block in isolation.
Both arms use the same instructions, decoder cap, and requested output
format. Their input token counts differ. A literal quote admits text that
occurs anywhere in the available source. A bound quote must be an exact
vote-group line with the queried document symbol, the reported label's
heading, and the queried actor in that group. A deterministic roll-call
lookup is the control for the supplied normalized records.

Eight authored two-delegation claims use these readings to populate all
four chair receipt masks. Revision requires a received contradiction.
Retention requires both received votes to support the claim. The compiled
brief credits a correct vote only when the supporting line is bound to
the right actor, document, and vote group. Strict passes here certify
vote attribution and documentary disposition. Explanations, arguments,
and speaker interaction require the fuller final-record rubric. The routing arms
replay fixed local generations and simulated message delivery. The exact
ceilings use the eight cases and the same payoffs and delivery odds.

| Model evidence and admission | Correct vote with admitted evidence | Wrong vote admitted | Strict full-receipt brief |
|---|---:|---:|---:|
| Combined, literal quote | 10/16 | 4/16 | 3/8 |
| Combined, actor and document bound | 10/16 | 0/16 | 3/8 |
| Isolated, actor and document bound | 11/16 | 0/16 | 4/8 |
| Deterministic normalized roll-call lookup | 16/16 | 0/16 | 8/8 |

The literal gate accepted Russia's vote on the amendment as its vote
on the parent draft. It also accepted China's abstention line in response
to a question about Switzerland. The binding check removes all four wrong
vote admissions and all three false dispositions across the receipt masks.
Isolating the requested stage saves 1,900 input tokens across 16 calls and
slightly improves bound coverage (7/8 outer space, 4/8 Gaza). In a remaining
error, the isolated stage returns the correct no label for Japan with an
in-favour list that excludes Japan. Other rejected quotes sometimes insert
a comma between the symbol and the vote heading.

| Split holdings and evidence channel | Frozen router net | Greedy with acknowledgment | Exact independent ceiling | Exact adaptive ceiling |
|---|---:|---:|---:|---:|
| Combined, literal | 0.151 | 0.128 | 0.217 | 0.225 |
| Combined, bound | 0.335 | 0.324 | 0.322 | 0.338 |
| Isolated, bound | 0.469 | 0.466 | 0.444 | 0.471 |
| Deterministic roll-call lookup | 0.566 | 0.569 | 0.531 | 0.572 |

Under split holdings, the bound gate lowers the frozen router's false
action rate from 13.23% to zero and improves replay net by 0.183.
With clean vote facts, greedy slightly exceeds the frozen policy in that
layout. The payoff is one point for a strict retain or revise, minus one
for a false substantive action, minus the payload fees. Acknowledgment is
available to both frozen and greedy and withheld from the independent
ceiling. These are results on two meetings with correlated cases and
normalized tables. No new policy fit or live debate is part of this test.
The deterministic lookup is the strong control when normalized vote
groups are already available. Keep open-text evidence tasks separate when
testing whether learned interaction improves briefs. [Complete results](facilitator-mixed-votes-evidence/results.json)

In the Qwen environment, run `python facilitator_mixed_votes_score.py facilitator-mixed-votes-evidence`
from this directory to verify all prompts and token sequences and
reproduce the scores. Use the PyArrow environment with the repository
`src` on `PYTHONPATH` to run `facilitator_mixed_votes_provenance.py`.

### Live peer turn with matched calls and output caps

Use the open-text Gulf of Guinea and Libya proposals from the prior
packet, with both orders of the source desks. In each panel the peer
and independent conditions share the exact same opening. The other
desk then writes a fresh source check with or without that opening note
and question. Both writers have the answering desk's card. The two
conditions share the same final instructions and full documentary
packet. The three-pass solo analyst gets the full packet from the first
pass and sees its own previous note on the second. All arms use three
model calls per panel and the same per-stage generation caps of
75, 75 and 112 tokens. Raw input lengths and generated token counts
remain visible. The peer intervention exposes both the note and its
question as a unit.

Final records use the six-part 70-point rubric. Report exact output
spans for each side and supported attribution, with material errors
scored separately. For the process readout, collect exact spans for
distinct relevant source units, then check which new reply units survive
in the paired final brief. A peer-only final unit that first appears in
the peer reply is stronger evidence of a contribution than a unit all
arms can recover from the cards. The models have direct source access
in the last pass, so word overlap alone gives weak evidence of uptake.
[Judge instructions and unit definitions](facilitator-live-peers-rubric.md)

| Three-call setup | Mean points out of 70 | Correct disposition | Strict | Final material errors |
|---|---:|---:|---:|---:|
| Peer note and question | 46 | 2/4 | 0/4 | 0/4 |
| Independent desks | 40 | 2/4 | 0/4 | 1/4 |
| Solo analyst with both cards on each pass | 35 | 4/4 | 0/4 | 4/4 |

The peer brief retained Ghana's evidence gap in one direction where the
independent brief omitted it. Both replying desks had expressed the gap.
In the other improved pair, the peer brief described a gap in UK evidence
and the independent brief also asserted that the UK did not make the
withdrawal call. Both effects improve the final rubric by 12 points in
their respective pairs. The answering desk introduced the same set of
tracked units in the peer and independent arms on all four panels.
Neither desk condition recorded the required revise heading on the Gulf
of Guinea proposal, even when the final text stated China's explicit
contradiction. The Libya cases omit Algeria's speaking capacity and the
complete scope of the withdrawal call. Only two of four shared openings
asked a question. Exposure to the opening is the verified intervention.

The peer, independent and solo arms use 3,875, 3,665 and 4,495 total
input tokens respectively across four episodes. The totals of generated
tokens are 526, 546 and 519. Each episode counts three calls even where
the peer and independent test arms share a captured opening. The same
assistant wrote the reference criteria and scored the evidence spans.
The four panels are two source claims with reversed desk assignments.
These are preliminary live interaction measurements on exposed cases
with zero optimizer updates. A strict-only reward would be tied across
every observed final. A subsequent training evaluation needs measurable
grounded outcomes, including scope-preserving institutional attribution,
and enough independent event families to evaluate against the strong
isolated and solo controls. [Exact spans, paired changes, and summaries](facilitator-live-peers-evidence/results.json)

Run `python facilitator_live_peers_score.py facilitator-live-peers-evidence`
in the Qwen environment to replay prompts, output IDs, review spans and
scores. The raw archive records 32 generations and four matched pairs.

### Separate local findings before writing the final brief

The matched-call test now separates a desk's source relation from its
exact witness, with a 22-word witness cap. The opening and reply
prompts test one delegation's side. The peer respondent sees the raw
opening finding. The independent respondent sees the same source and
assertion. Both final writers see the full sources and admitted local
findings. The solo analyst has the full sources at all three stages.
The arms have equal call counts and generation caps. Input lengths can
vary. The repair replay reuses all local calls and regenerates only final
prompts changed by removing matching outer quotation delimiters.

Two panels carry over from the previous live test. Two more distinguish
supporting some extension of MINUSCA from welcoming the adopted
one-year extension. A proposal for six months can establish qualified
support on the first claim. A recorded abstention alone supplies no
reason for the vote. The witness review grades these cases independently
of the formatting check and the final heading. [Source packet and provenance](facilitator-transfer-panels.json) · [Judge instructions](facilitator-peer-findings-rubric.md)

The strict interface admitted no local excerpts. Every local response
used quotes around its passage or included a quote after an unknown
label. The chairs received the same pair of unknown fields across all
three arms on each claim. Each arm scored 46/70 on average, chose two
of four headings correctly, and had zero strict passes. On the
some-extension case, identical peer and independent final input token
sequences produced different wording with the same grade. The raw
archive preserves that variation. Interpretation of any paired effect
requires checking that the treatment reached the final prompt.
[Baseline scores and treatment audit](facilitator-peer-findings-evidence/results.json)

Removing matching outer quotation delimiters recovered ten literal
witnesses from the 20 archived local calls. Eight were adequate for their
reported finding. We regenerated nine changed final prompts and reused
the three unchanged Gulf of Guinea prompts. The repaired peer and
independent final briefs each average 51.5/70. The solo arm averages
43/70. Each gets two of four headings right, and all raw final briefs
still fail the strict rubric. The MINUSCA support-for-some-extension
panel is the sole peer–independent difference in admitted evidence.
Both answers cite the six-month proposal. The peer reply correctly
labels it support, while the independent reply labels it unknown.
Only the repaired peer chair gets two support findings. It still
writes withhold even though its text records both proposed durations.
[Repaired traces and exact spans](facilitator-peer-quote-repair-evidence/results.json)

A separate heading-only replay uses any decisive admitted relations
and keeps the model heading when the relations leave the joint claim
open. It preserves the generated prose. This gives the peer one strict
pass on the qualified MINUSCA case, compared with zero for the
independent and solo arms. Peer disposition accuracy goes from 2/4
to 3/4. Both solo heading changes rely on inadequate evidence, although
they happen to select the correct headings. One uses objection to a
specific adopted package as evidence of support for some extension,
and the other uses an abstention as evidence of a policy objection.
The replay therefore isolates a usable peer contribution and the need
for a semantic check before applying the rule. This is a post hoc
intervention on exposed cases with same-assistant review and zero
model updates. [Heading-only replay and witness flags](facilitator-peer-quote-repair-evidence/header-replay.json)

Run the two scorer commands with the Qwen environment Python.
The heading replay only needs Python's standard library.

```bash
python facilitator_peer_findings_score.py facilitator-peer-findings-evidence
python facilitator_peer_findings_score.py --repaired facilitator-peer-quote-repair-evidence
python facilitator_peer_header.py
```

### Fit routing on archived brief scores and test across meeting families

Train both desks from uniform tables on twelve archived proposals across
UNIFIL, Colombia, Bosnia, Afghanistan, Abyei and MINUSCA. Include both
assignments of the two documentary positions to the source slots.
The two fits share the brief payoff, source holdings, link probabilities
and 180 exact policy-gradient updates. The independent fit receives no
acknowledgment. The adaptive fit receives an acknowledgment after a
successful first transmission when the feedback link succeeds. The
payoff is one for a strict retain or revise, minus one for a wrong
substantive action, minus payload fees. Acknowledgments carry no charge
in this comparison. Qwen weights and archived brief grades are fixed.

The training return moves from −0.053 for both initial policies to
0.171 adaptive and 0.125 independent. Evaluation uses six Gulf of Guinea
and Libya prompts and eight outer-space and Gaza prompts. The latter
have both a model-extracted bound channel and a deterministic roll-call
channel. All test meeting families are excluded from the fit. These
cases had been used in development before this study, and the two
outer-space and Gaza channels share case identities.

| Held-out cohort, split holdings | Trained adaptive | Trained independent | Frozen adaptive | Greedy with acknowledgment | Exact independent | Exact adaptive |
|---|---:|---:|---:|---:|---:|---:|
| Gulf of Guinea and Libya | 0.063 | 0.013 | 0.093 | 0.086 | 0.083 | 0.096 |
| Outer space and Gaza, model reads with binding | 0.332 | 0.315 | 0.335 | 0.324 | 0.322 | 0.338 |
| Outer space and Gaza, deterministic roll calls | 0.553 | 0.504 | 0.566 | 0.569 | 0.531 | 0.572 |

The newly fitted adaptive policy beats the matched independently
fitted policy in all six cohort and holdings comparisons. It loses to
the existing frozen policy in all six. Swapping the two documentary
positions leaves its reported return unchanged to numerical precision.
The trained responder accounts for 0.029 of the 0.030 loss on split
Gulf of Guinea and Libya, averaging both orders of replacing the two
desk tables. The new policy receives both cards more often there
(18.45% versus 13.90%) and yields fewer usable revisions
(18.78% versus 22.02%). [Policy trajectories and transfer scores](facilitator-transfer-fit-evidence/results.json)

The relation labels hide important differences. Three proposals present
the identical pair of contradiction labels. With only the first card,
the two vote proposals earn +1 and the Gulf of Guinea treaty-scope
proposal earns −1. The second card on the treaty-scope proposal earns
+1. The exact split-holdings ceiling on the six proposals rises from
0.096 using the current observations to 0.342 when both desks are
also told whether the requested act is a recorded vote or a statement.
The per-case oracle reaches 0.366. These are exact retrospective
ceilings optimized on the tested cohort. They motivate trying the
public claim-type feature in a future fit. The split used here contains
only two recorded-vote proposals among the twelve fitting cases.
[Policy swaps, observation collisions and ceilings](facilitator-transfer-fit-evidence/attribution.json)

In the Qwen environment, reproduce the two artifacts with these commands.

```bash
python facilitator_transfer_fit.py
python facilitator_transfer_attribution.py facilitator-transfer-fit-evidence/results.json
```

### Train with public claim type and balance the document order at evaluation

Two 180-update exact policy-gradient fits share sixteen archived
proposals, link and acknowledgment access, reward, and both assignments
of the two documentary slots. Six proposals ask about votes and ten
ask about statements. Four additional vote cases come from the
outer-space meeting with the bound evidence reader. The type-aware
policy can use a separate local table for each requested act. A state
with no fitting trajectories for its type falls back to the same
relation-only table used by the control. Type is assigned from the
public target predicates and never from the verdict or evidence label.

Gulf of Guinea and Libya motivated this comparison. Save them as an
exposed diagnostic, with Gaza and Haiti/Mali as further meeting families
held out of fitting. The same receipt grades and transport protocol
apply to the two policies. Mean fitting net goes from −0.038 for both
initial tables to 0.2132 relation-only and 0.2154 claim-type. Exact
fitting ceilings are 0.2155 and 0.2181. The small training gain is close
to the available gain on these archives.

| Held-back cohort, split holdings | Relation-only fit | Claim-type fit | Frozen router |
|---|---:|---:|---:|
| Gulf of Guinea and Libya | 0.06333 | 0.06334 | 0.09296 |
| Gaza, bound model reads | 0.30283 | 0.30262 | 0.30268 |
| Haiti and Mali | 0.12819 | 0.12807 | 0.12815 |

Absolute differences between the two fits stay within 0.00021 net
across both holdings and all cohorts. The training bank contains
zero proposals with the two observed contradiction labels, in either
claim type. That is the observation under which the Gulf of Guinea
scope dispute and the two vote proposals have different useful
receipts. Adding vote volume alone leaves the relevant cell empty.
[Training weights, cases, and paired scores](facilitator-claim-type-fit-evidence/results.json)

The earlier ceiling of 0.342 for claim-type routing evaluated one
document order. In that order, the useful vote evidence occupies a
consistent slot, while the valid objection to the treaty-scope claim
occupies the other slot. Optimizing a single table over both orders
lowers the type-aware split ceiling to 0.121, compared with 0.095 for
the slot-balanced relation-only ceiling. The gain falls from 0.246
to 0.026. On slot-balanced Haiti and Mali, the corresponding ceilings
are 0.165 and 0.132. Expose both document orders at scoring time, and
report the occupancy of the claim-type and observed-relation cells
where the payoff depends on which evidence reaches the chair.
All cases are archived and had been exposed elsewhere in the project.
No language-model calls or updates were added.
[Exact audit and payoff-cell coverage](facilitator-claim-type-fit-evidence/audit.json)

Run these in the Qwen environment to replay fitting and all audits.

```bash
python facilitator_claim_type_fit.py
python facilitator_claim_type_audit.py facilitator-claim-type-fit-evidence/results.json
```

### Add missing receipt contrasts from archived single-card outcomes

The archived training set contains three genuine recorded-vote
contradictions and four statement-side contradiction readings. One
of the four is the false UNIFIL scope contradiction. Compose two
separate contradiction fields from different training proposals
within a claim type. The training-only packet retains each
singleton's established disposition and strict score. The composed
receipt expects revision when at least one received field truly
contradicts. A strict revision requires all received fields to pass.
This yields three vote and six statement pairs, including three
statement pairs with one true and one false contradiction. These
are composed reward examples. The joint fields did not appear
together in an official proceeding or an actual model-generated
brief. Both 180-update fits see the same 16 archived proposals,
the same nine composed pairs, and both source-slot assignments.

| Held-back cohort, split holdings and both document orders | Prior type fit | With pairs, relation only | With pairs and claim type | Frozen |
|---|---:|---:|---:|---:|
| Gulf of Guinea and Libya | 0.06334 | 0.09295 | 0.09296 | 0.09296 |
| Gaza, bound readings | 0.30262 | 0.30271 | 0.30251 | 0.30268 |
| Haiti and Mali | 0.12807 | 0.12816 | 0.12804 | 0.12815 |

Filling the training cell recovers the Gulf of Guinea and Libya
loss in both fitted arms. The public type still offers little
separation. Against the old type fit, the new type fit adds 3.24
percentage points of usable revisions and 1.08 points of false
actions under split holdings. Its expected payload costs drop
0.0080. The false-action penalty would need to rise from 1 to about
3.74 to erase the net improvement at these fixed policy weights.
The test grades and document orders are identical across arms.
[Pairs, fit traces and held-back scores](facilitator-receipt-contrast-fit-evidence/results.json)

A privileged test exposes the correctness of each local label
to its holder and includes it in delivery acknowledgment. The chair
and receipt payoff stay fixed. On Gulf of Guinea and Libya with
split holdings and both orders, the exact adaptive ceiling rises
from 0.095 for relation labels to 0.224 with the manual correctness
bit. Claim type raises 0.224 to 0.231 when that bit is available.
With correctness and type, the exact independent ceiling is
0.208. This locates headroom in the evidence available to each
desk. The audit uses the reviewed reference labels, which are
privileged. Evaluating a deployable cue requires checking whether
it distinguishes an exact but irrelevant quote from a genuine
objection on separate meeting families.
[Payoff decomposition and exact oracle](facilitator-receipt-contrast-fit-evidence/audit.json)

Reproduce in the Qwen environment. Neither command calls Qwen or
updates language-model weights.

```bash
python facilitator_receipt_contrast_fit.py
python facilitator_receipt_contrast_audit.py facilitator-receipt-contrast-fit-evidence/results.json
```

### Verify a contradiction against a fixed witness

The next packet uses normalized cards from the Somalia AUSSOM
decision and the Western Sahara MINURSO decision. Somalia's draft
joins adopted row 236 in the pinned UNSC-Bench release. Western
Sahara is an official-record extension. The six fixed witnesses
each face one compatible and one incompatible assertion. The
contrasts cover abstention versus wider policy support, abstention
versus nonparticipation, a specific financing workaround versus
authorized contributions, and satisfaction of a policy or negotiating
condition. The reproduced evidence is exact relative to the supplied
cards, which paraphrase the official records. [Somalia record](https://digitallibrary.un.org/nanna/record/4071291/files/S_PV.9828-EN.pdf?registerDownload=1&version=1&withMetadata=0) · [Western Sahara record](https://digitallibrary.un.org/nanna/record/4092385/files/S_PV.10030-EN.pdf?registerDownload=1&version=1&withMetadata=0) · [Benchmark joins](facilitator-witness-contrast-evidence/provenance.json)

Frozen Qwen3.5-4B receives exactly the same three fields in both
arms. The direct verifier uses the earlier label-first instruction.
The compare-first verifier checks the speaker, act, target and
qualification before outputting the label. It also changes the
requested order of the output fields. Both arms have the same
100-token cap. The review scores the format, verdict, and concrete
source reasoning separately. Pair credit requires the verdict to
change appropriately when the assertion changes. [Judge instructions](facilitator-witness-contrast-rubric.md)

| Scope check | Correct verdicts | Correct with grounded explanation | Genuine conflicts admitted | Both verdicts correct |
|---|---:|---:|---:|---:|
| Always open | 6/12 | 0/12 | 0/6 | 0/6 |
| Direct, strict | 7/12 | 4/12 | 1/6 | 1/6 |
| Compare first, strict | 7/12 | 6/12 | 2/6 | 1/6 |
| Compare first, trim separator whitespace | 10/12 | 8/12 | 4/6 | 4/6 |
| Trim whitespace and apply same-act vote rule | 12/12 | 10/12 | 6/6 | 6/6 |

The two repairs were added after inspection. Trimming only outer
whitespace around the two response fields recovers three invalid
lines. The vote rule requires a whole, unique literal witness plus
the same named actor and resolution in the claim and witness.
It repairs the two misunderstood vote conflicts. One contrasts
abstention with a vote in favour, and the other contrasts
nonparticipation with a recorded abstention. Neither model arm
admitted an open control as a conflict. Across all checks, two
remaining correct open verdicts lack adequate reasoning. The
model states that France opposed a financing mechanism and that
Pakistan reported negotiating progress. The sources in those
cards leave those claims open.
[Verdicts and exact-span review](facilitator-witness-contrast-evidence/results.json)

For the routing diagnostic, compose pairs of separate claims within
each meeting and include all compatible and conflicting combinations
and both document orders. Each family has 24 such packets. The
literal baseline treats every candidate objection as a conflict.
A strict revision requires the right decision and adequate proof
for each transmitted objection. Both the frozen router and greedy
receive the same admitted evidence.

Under split holdings, literal admission yields 45.73% false actions
and −0.118 net in each family. Compare-first with separator repair
gets 0.397 net with zero false actions in each. Adding the bound vote
rule gets 0.535 frozen, 0.537 greedy and a 0.537 exact adaptive ceiling.
The adapted evidence channel matches the oracle for this
contradiction-only receipt task. Its two ungrounded open explanations
carry no objection and receive no proof credit. This is a post hoc
compositional scope replay using same-assistant review. It measures
transmission of justified objections. Broader final records, live
discussion, and independent review are separate evaluation steps.
[Transport and exact bounds](facilitator-witness-contrast-evidence/routing.json)

Use the Qwen environment to replay the captured generations and
transport. The provenance command also requires PyArrow and the
repository `src` path on `PYTHONPATH`.

```bash
python facilitator_witness_contrast_score.py facilitator-witness-contrast-evidence
python facilitator_witness_contrast_route.py facilitator-witness-contrast-evidence/results.json
python facilitator_witness_contrast_provenance.py
```

### Transfer the witness verifier to a full Council record

Freeze the comparison prompt, separator parser, and typed vote rule
from the Somalia and Western Sahara test. Evaluate on Gaza resolution
2728 and Myanmar resolution 2669. The exact meeting records supply
the cards. Thirty named votes agree with UNBench's author-test event
rows, and the fifteen Gaza votes also agree with the UNSC-Bench
adopted row. The reference dispositions are three revisions and one
withhold. The test covers two recorded-vote claims, a conflict over
continued Council work, and a gap about the preferred instrument.
[March 2024 Gaza record](https://digitallibrary.un.org/nanna/record/4042611/files/S_PV.9586-EN.pdf?registerDownload=1&version=1&withMetadata=0) · [December 2022 Myanmar record](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9231&t=pdf) · [Dataset audit](facilitator-verified-brief-evidence/provenance.json)

The final writer sees both speaker cards, a separate official
Council card, the two claims, and the candidate excerpts. The direct
and hybrid verifier arms add the respective verdict fields to the
same payload. They each use three calls per case and a 150-token
final cap. The pooled reference uses one call. Input token totals
are 3,741 direct, 3,893 hybrid, and 1,714 pooled across the four cases.
Only the Myanmar vote prompt differs between the direct and hybrid
final writers. The other three produce identical final outputs.
[Rubric](facilitator_verified_brief-rubric.md) · [Input and output audit](facilitator-verified-brief-evidence/results.json)

| System | Mean points out of 70 | Correct disposition | Strict briefs |
|---|---:|---:|---:|
| Pooled | 24.5 | 0/4 | 0/4 |
| Direct verifier, generated brief | 29.5 | 0/4 | 0/4 |
| Hybrid verifier, generated brief | 32.0 | 0/4 | 0/4 |
| Hybrid with a bound roll-call composer | 49.0 | 2/4 | 2/4 |

The hybrid verifier gets 7/8 local verdicts correct with 5/8 grounded.
The direct gate gets 6/8 and 4/8. Both miss France's concrete
objection in the Gaza scope case because their explanations compare
French votes and speeches with each other. The queried assertion
concerns whether the Council's work was finished. Both gates also
invent a preference for a presidential statement in Norway's
otherwise correctly labelled open case.

All twelve generated briefs say retain. This includes drafts that
correctly report the contradictory abstention and have a conflict
label in the final payload. The output describes the corrected
facts and then appears to endorse them under its retain heading.
Score the decision on the original pair separately from factual
accuracy of the revised text. The post hoc composer accepts both
vote witnesses only when they bind to the queried actors and the
same resolution as the official Council card. It puts the factual
vote text and Council disposition into the output and computes the
heading from the recorded acts. It repairs both vote cases. The
fallback reproduces the failed hybrid text in the two statement
cases. The inputs are normalized source cards, and the review is
same-assistant. No language model was trained. [Composition proof and raw failures](facilitator-verified-brief-evidence/rollcall-composition.json)

Run the following from this directory in the Qwen environment.
The corpus audit runs in the PyArrow environment with repository
`src` on `PYTHONPATH`.

```bash
python facilitator_verified_brief_score.py facilitator-verified-brief-evidence
python facilitator_rollcall_record.py facilitator-verified-brief-evidence
python facilitator_verified_brief_provenance.py
```

### Decide the original attribution before composing the brief

Separate the decision from the wording of the final record. Each source
desk receives a documentary card and three complete candidate reports:
the original attribution, an authored incompatible attribution, and an
evidence gap. Rotate the candidate order three ways. A unanimous exact
copy across the orders selects a relation. Bounded composition uses an
unknown status when the rotations disagree or fail the output contract.
The alternative attributions are authored from the question's scope.
They are observable inputs to this diagnostic.

Use the Gaza Council-role and Myanmar instrument-preference cases
from the previous test, a new composition on the exposed Somalia
meeting, and the existing qualified MINUSCA-extension case. The
Central African Republic panel supplies a positive retain control.
The two writers receive the same cards and assertions. One also
receives the three-way local findings. Both write only the two
speakers' sentences. The composer inserts the official Council card,
its citation, and the decision on the original claims. The fixed
Council block receives its own twelve points on the same 70-point
scale. This separates the ability to form a disposition, preserve
a specific role fact or evidence gap, and cite the right source.
[Somalia meeting](https://digitallibrary.un.org/nanna/record/4071291/files/S_PV.9828-EN.pdf?registerDownload=1&version=1&withMetadata=0) · [MINUSCA roll call](https://digitallibrary.un.org/record/4093084?ln=en) · [Source packet](facilitator_attribution_choices.json)

The reader makes 18/24 correct choices and produces an exact candidate
every time. It agrees across all three orders on only two of eight
attributions. Falling back to unknown for every disagreement gives
5/8 local relations and 3/4 correct headings. Neither of the two
generated-body arms passes the complete brief. The body-only arm
averages 47/70. Adding the unanimous-or-unknown findings yields
45/70, with one more material error. The writer invents a Norwegian
instrument preference and turns an unresolved US position into
opposition. Preserve the generated outputs as failures even though
the composer supplies correct votes and adoption from the Council
card. [Original experiment and review](facilitator-attribution-choices-evidence/results.json)

A post hoc majority across the same three orders gets 8/8 local
decisions right on this packet. Single-order accuracy is 5/8, 8/8,
and 5/8. Ask a separate local extractor for each of the five
selected substantive findings. All five responses are exact and
adequate sentences from their normalized source cards, including
the US six-month MINUSCA proposal and its conditional openness to a
year. The composer emits those sentences with actor-specific
citations and expresses the other three sides as scoped gaps.
It copies the Council disposition and vote tally and computes
the heading from the original claims. All four records meet the
70-point contract. The composed path uses 24 archived choices and
five new extracts. The majority and extraction changes followed
inspection. The four cases are exposed and use authored alternatives
and same-assistant review.
[Composed briefs and exact witness review](facilitator-attribution-extracts-evidence/results.json)

Each assembled record can also be rebuilt from every receipt mask
without exposing a missing extract to the chair. Keep S0 public
and score against the complete-evidence final record. The replay
uses both slot orders and the same transport odds and fees for all
policies. The withheld Myanmar brief still benefits from the
received Chinese instrument-preference evidence. Under the previous
publication-only reward, supplying that evidence earns no positive
reward. Under a full-brief reward, it contributes a strict pass.

| Split holdings | Frozen | Trained independent | Greedy with acknowledgment | Exact adaptive ceiling |
|---|---:|---:|---:|---:|
| Net with strict retentions and revisions rewarded | 0.367 | 0.348 | 0.363 | 0.370 |
| Net with strict withholds also rewarded | 0.442 | 0.482 | 0.549 | 0.550 |

The fixed frozen router produces a strict withhold in 7.51% of
rollouts, versus 18.61% for greedy. No system makes a false
substantive action in this replay. The ranking changes because
the existing routing objective ignores a well-supported withhold.
The full-record metric credits grounded evidence and uncertainty
even when the correct action is to leave the proposition open.
These are exact replays on four scoped records with preassigned
local evidence and free acknowledgment. Live multi-turn gains and
transfer to fresh families remain unmeasured.
[Receipt records and reward sensitivity](facilitator-attribution-extracts-evidence/routing.json)

Use the Qwen environment to replay all 37 actual generations,
score the extracted records, and rebuild the receipt test.

```bash
python facilitator_attribution_choices_score.py facilitator-attribution-choices-evidence
python facilitator_attribution_extracts_score.py facilitator-attribution-extracts-evidence
python facilitator_attribution_extracts_route.py facilitator-attribution-extracts-evidence/results.json
```

## Train for justified withholds and check revision retention

Fit two joint two-desk policies on the same 14 archived panels with
both slot orders and the same uniform initialization. Each fit uses
180 exact policy-gradient updates, with the same payload fee and free
acknowledgment. Restrict the archived strict grades to the original
complete-evidence disposition and require receipt of every established
side. Use Afghanistan and UNIFIL as the two positive examples where
delivery benefits a correctly unresolved record. Of the six revision
panels, three permit a strict revision on any receipt mask under this
contract. The publication objective credits strict retentions and
revisions. The full-record objective also credits strict withholds.
Both penalize incorrect substantive actions. The older grades check
the archived material fields. The composed test cases use the separate
70-point rubric with an explicit scoped gap and a public Council card.

| Four composed cases, split holdings | Strict retention | Strict revision | Strict withhold | Full-record net |
|---|---:|---:|---:|---:|
| Frozen adaptive | 7.90% | 37.11% | 7.51% | 0.442 |
| Fit with publication credit | 7.89% | 0.07% | 7.51% | 0.115 |
| Fit with full-record credit | 9.34% | 0.07% | 18.57% | 0.220 |
| Frozen on observed contradictions, publication fit otherwise | 7.89% | 37.11% | 7.51% | 0.442 |
| Frozen on observed contradictions, full-record fit otherwise | 9.34% | 37.11% | 18.57% | 0.548 |
| Acknowledgment-aware greedy | 9.35% | 37.21% | 18.61% | 0.549 |

The rates share the denominator of all policy rollouts, with equal
weight per case and slot order. The full-record net adds strict
outcomes, subtracts incorrect substantive actions and subtracts the
expected sending cost. Observed false actions are zero for these arms
on the four cases. The exact split-holdings ceilings are 0.550 for
adaptive routing and 0.527 for independent routing. The primary cases
and two secondary cohorts were excluded from fitting and their
families were exposed in earlier project work.

The post hoc swap uses only the local relation labels and the existing
acknowledgment. It gives 0.463 on overlapping holdings for the primary
cases, where greedy also gives 0.463. On the split Gulf of Guinea and
Libya cohort it gives 0.135, compared with greedy at 0.136. On split
Haiti and Mali it gives 0.280, compared with frozen at 0.294. This replay
measures evidence delivery with the source reader and writer fixed. The
same frozen table preserves revisions in both swap arms. Generalization
of the swap and gains from live deliberation need separate evaluation.
[Fits and per-case values](facilitator-withhold-fit-evidence/fit.json) ·
[Post hoc replay](facilitator-withhold-fit-evidence/guard.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_withhold_fit.py > fit.json
OPENBLAS_NUM_THREADS=1 python facilitator_withhold_guard.py fit.json > guard.json
```
