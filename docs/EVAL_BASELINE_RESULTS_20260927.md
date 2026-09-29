# First measured evidence baseline

**Follow-up:** [Failure analysis with 34 diagnostic generations](EVAL_FAILURE_ANALYSIS_20260927.md) shows strong sensitivity to country names and answer formats. The original metrics below remain unchanged; the next calibration gate is evaluation robustness and source sufficiency before new training.

27 September 2026. **The pinned Qwen3-8B model completed the eight-output probe and the full 30-output comparison on one retained H100 allocation.** We now have actual answers, probabilities, stopping traces and a reviewer packet. No new fine-tuning has run.

The most useful finding is that supplied speeches improve several substantive policy answers, while **both recorded abstentions remain wrong**. Even the evidence-conditioned France answer adds assistance categories absent from its supplied passage. That gives us concrete behavior to evaluate before training.

## Comparison and scope

The frozen package contains seven action pairs and eight policy pairs across France, the UK, India and Brazil, covering two events: the December 2021 climate-security draft and the September 2022 Ukraine draft. A receives the country/role prompt and task inputs; B receives the same task plus the selected dated national statement. For action items, the draft is already in both arms. This is a base-model evidence comparison, not a fine-tuning experiment.

These are exposed development reconstructions. Archived document-version availability is unresolved, and two meetings do not provide seven independent experiments. UK speeches explicitly announce draft support; their rows are separately identifiable in the results. No significance claim, reliability curve or prospective forecasting claim follows from this sample.

## Recorded actions

Each arm has seven outputs, including four Y references, one N and two A. Invalid outputs remain errors; all 14 generated actions followed the one-letter format.

| Method | Correct | Fixed-label macro F1 | NLL ↓ | Brier ↓ |
|---|---:|---:|---:|---:|
| Always Y | 4/7 | 0.242 | — | — |
| Global training prior | 4/7 | 0.242 | 2.114 | 0.832 |
| Country training prior | 4/7 | 0.242 | **1.707** | 0.808 |
| A: country/role, no supplied speech | 4/7 | 0.267 | 2.467 | 0.735 |
| B: same task plus speech | **5/7** | **0.500** | 2.069 | **0.536** |

Priors use only the original UNBench training votes, dated 1994–2016, with add-one smoothing. That release covers adopted resolutions, whereas these two items concern rejected drafts; the priors are useful simple comparators under that distribution shift. The country prior still beats B on NLL here. Better hard-label accuracy does not establish better confidence calibration.

Model probabilities are conditional on the first completion token being canonical Y/N/A, not sequence probabilities or verbal confidence. The runner separately retains legal-label mass and the unconstrained answer. Do not fit a temperature or select a training method from seven outcomes.

| Case | Recorded | A output | B output | Useful observation |
|---|---|---|---|---|
| France, climate | Y | Y | Y | Correct in both arms |
| UK, climate | Y | Y | Y | Speech explicitly supports the draft |
| India, climate | N | Y | N | B assigns **equal 47.50%** probability to Y and N; greedy tie-breaking selects N |
| France, Ukraine | Y | Y | Y | Correct in both arms |
| UK, Ukraine | Y | Y | Y | Speech explicitly supports the draft |
| India, Ukraine | A | Y | N | Probability of the recorded abstention falls from **0.418% to 0.270%** |
| Brazil, Ukraine | A | N | N | Probability of the recorded abstention falls from **0.521% to 0.0399%** |

Thus the single additional correct answer is fragile, and evidence does not solve action inference for the two abstentions. Removing the two UK rows leaves A at 2/5 and B at 3/5. All source/action relationships should remain inspectable rather than being compressed into the aggregate.

## Policy answers: source checks before aggregate ratings

These are assistant observations against the selected source passages, not independent ratings or a calibrated policy pass rate. The rubric remains frozen for reviewers; ambiguous granularity should be recorded rather than silently changed to improve a score.

| Item | A: observed problem | B: improvement or remaining issue |
|---|---|---|
| France, climate | Gives a generic climate-risk assessment example rather than the specific complementary measures in the rubric | Includes G-5 Sahel support, resilience and the Great Green Wall |
| India, climate | Incorrectly says the statement did not directly address exacerbated conflict; misses the UNFCCC preference | Recovers the explicit acknowledgment of exacerbated conflicts, institutional preference and objection to a climate-only explanation |
| UK, climate | Invents concerns about the draft and omits meaningful participation by women and girls | Correctly reports draft support, participation and the limit on inferring binding quotas |
| Brazil, climate | Substitutes an Amazon-focused account for the selected statement’s institutional argument | Recovers the UNFCCC preference, mandate/duplication concerns, harms and developed-country financing |
| France, Ukraine | Identifies national capacity but omits the duration of continued support | Correctly states non-recognition, but adds **“financial and military assistance”** absent from the supplied passage; also omits “for as long as necessary” |
| UK, Ukraine | Falsely says the UK supported the occupied-region referendums | Correctly rejects the referendums, supports the US/Albania draft and bounds what the speech establishes about a later vote |
| India, Ukraine | Substitutes generic development/capacity-building assistance for the dated statement | Recovers cessation, diplomacy, law and assistance; reviewers should check the missing food/fuel/fertilizer detail and narrowing of “neighbours in the global South” to South Asia |
| Brazil, Ukraine | Falsely says the statement does not discuss the referendums or recognition conditions | Preserves conditional validity, concerns about free choice in conflict, and uncertainty about hypothetical recognition |

For France, the issue is attribution to this specific supplied passage, not a claim that France never provided those forms of assistance. For India and Brazil, accurate policy summaries and accurate recorded action predictions must be assessed separately.

The [16-response review deck](../data/review/eval-pilot-20260927/model-outputs-v1/review-deck.md), [complete source packet](../data/review/eval-pilot-20260927/model-outputs-v1/source-packet.md) and [blank rating template](../data/review/eval-pilot-20260927/model-outputs-v1/review-template.jsonl) are ready. Arm and model labels are hidden; answer wording/citations can still reveal evidence availability. A private key is separate. Two reviewers should first calibrate on the [19 authored fixtures](../data/review/eval-pilot-20260927/calibration-v1/review-deck.md), then rate independently. Human ratings remain zero.

## What the engineering checkpoint taught us

The first real GPU attempt failed before producing scored outputs. Transformers replaced requested global-default generation values, including `do_sample=False`, with the checkpoint’s sampling defaults. The runtime logits/greedy check rejected that mismatch. A controlled regression test reproduced it; explicitly passing `use_model_defaults=False` fixes it without weakening the check. **56 targeted tests now pass.** The failed run and its logs are preserved separately from successful results.

The corrected eight-output probe and expanded run preserve every input token. All 30 outputs stop at EOS, with zero output caps, generated thinking markers or repeated-sentence detections. Some ordinary phrase reuse remains; these mechanical diagnostics are not semantic quality scores. The eight overlapping cases reproduce the exact same output token IDs and action probabilities in the expanded run.

A separate [legacy-EOS replay](../reports/eval-pilot-20260927/legacy-eos-comparison.json) changes only the EOS list from `[151645, 151643]` to `[151645]`. All eight outputs and action probabilities are identical; every response stops at 151645. This does not explain the earlier trained adapter's repetition, which still requires its own replay before interpreting a new adapter.

The expanded run processed **44,384 prompt tokens** and generated **3,365 tokens**. Measured generation time was **76.25 seconds**, trace processing **2.94 seconds**, snapshot rehashing **9.84 seconds**, and model loading **1.92 seconds**. Peak allocated GPU memory was **16.48 GiB**. Those measurements exclude retained idle allocation time; the reservation requests up to three GPU-hours in total.

The [allocation workflow](TRILLIUM_WORKFLOW.md) now uses `def-zhijing` and `sleep infinity`. Job **996664** remains available on **trig0042** until **28 September, 01:30:55 EDT**. Experiment failure and completion leave the reservation intact. Check scheduler state before reuse.

## Next decision

Keep B as the evidence baseline that any later behavioral SFT must beat on the same inputs. Calibrate the rubric and review these actual outputs before treating policy scores as reliable. Expand source-checked event coverage with enough abstentions and institutional qualifications to distinguish a real improvement from the single tie-sensitive case here. Only then prepare one small behavioral LoRA comparison; do not launch a broad training sweep or deliberation system from this result.

The small, concrete failure targets are: preserve the source’s qualifications, avoid inventing commitments or source-specific details, and distinguish a public stance from the eventual recorded action. The current observations identify those targets; they do not yet establish that a particular training recipe fixes them.

Machine-readable [results and input hashes](../reports/eval-pilot-20260927/two-event-base-results.json), [decoding failure and repair](../reports/eval-pilot-20260927/inference-defaults-regression.json), [raw successful run](../runs/two-event-996664-base-v1/run.json), and [predictions with token traces](../runs/two-event-996664-base-v1/predictions.jsonl) preserve the evidence behind this checkpoint.
