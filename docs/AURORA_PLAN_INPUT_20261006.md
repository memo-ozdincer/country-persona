# Supplied-point realization: retained facts, copying failures

A fresh 256-update Qwen3.5-4B fit on eight point-supplied inputs improves content retention on the newly frozen ICC/Darfur planned cases: base **9 met + 1 unratable / 28**, the earlier raw-input eight-example adapter **21/28**, and the new plan-input adapter **27/28**. This identifies a useful component—preserving supplied source and decision points—but does not justify scaling this exact recipe. The adapter copies the shorthand plan nearly literally, fails to condense the long actual Sudan plan, and repeats raw French source text until the generation cap. The frozen rubric gives one ICC planned strict pass; its whitespace word-count check does not establish readable prose.

The checkpoint contains **42 new stored public outputs: 41 uncapped and one capped**, all hand-read in full. One capped output is not a complete task answer. It adds **256 actual saved optimizer updates**, bringing recorded Aurora Qwen3.5 updates to **2,270**. The separate Qwen2.5 reproduction remains **582**. All three owned GPU identities exited; unfamiliar processes were untouched.

## Question and matched comparison

The user proposed separating content/decisions from their realization in prose. This comparison changes the training input from a raw national speech/current-note task to that same task plus checked source/decision bullet points and a preservation contract. It keeps the eight preferred answer texts, their exact native completion tokens, fresh zero-effect LoRA tensor initialization, 32 presentations per example, 256 updates, optimizer, objective, model/runtime lock, GPU type and generation protocol matched to the earlier raw8 experiment.

The fitting points were constructed sentence by sentence from the previously audited preferred answers. They are synthetic supervision by the same assistant, not a separately executed teacher LLM or independently reviewed plans. They reconstruct each target exactly. Fitting success is consequently a copying/formatting positive control. Input information, length and contract change together; this comparison does not isolate an abstract persona effect or a pure format-only intervention. Supplied analytical decisions are not native decision predictions.

The eight examples cover France/WPS, UK/Mali, India/sanctions and Brazil/Haiti, with defective/repaired or absent/supplied-authority contrasts. The two exposed controls retain the actual question-guided Brazil/Sudan plan and the checked UK/Somalia plan. Four ICC raw/planned cases were frozen before this checkpoint's baseline or fitting. All arms receive the same fourteen actual inputs.

## Source and hand inspection

The new primary family is [S/PV.9375, 13 July 2023](https://digitallibrary.un.org/record/4015650), an ICC/Darfur briefing. The official English PDF is [the UN record](https://documents.un.org/doc/undoc/pro/n23/205/77/pdf/n2320577.pdf), 524,814 bytes, SHA256 `d9dff17a789bc9134e4b1b2c4aa30e56aad74f02aa9154e9f5a32b47928f5d61`.

Both complete selected national speeches were read, and their primary PDF pages 10, 11 and 13 were viewed. Brazil/França Danese spans offsets 40569–45654, France/Dime Labille 56310–60655. UK/Kariuki is the chair; Khan is the ICC Prosecutor. Neither is substituted for the selected government speakers, and this meeting supplies no current vote label. Column extraction preserves the body word multiset on all nineteen body pages. Only selected speeches/pages were hand-read/viewed; this is not a claim to have read all twenty PDF pages. A whitespace normalization initially removed printed compound hyphens; it was corrected before any calls, with raw spans retained.

The fitting targets/plans, new source spans, requests, scenarios, plans and criteria were hand-checked before calls. Shared unchanged historical sources retain their prior whole-text audits, with exact-byte continuity. Critical qualifications include conditional crimes-against-humanity allegations, trial/prosecution versus conviction, Brazil's UN-plus-Rome-parties funding stance versus France's absent funding stance, complementarity/States' primary responsibility/ICC unable-or-unwilling, actual security conditions versus a universal victory gate, and universal vocation versus unlimited jurisdiction. No new national appropriation, pledge or future vote is supplied.

That inspection did **not** make every teacher-plan application complete: the French analytical plan omits an explicit comparison with Z's abandonment of other Court investigations. The downstream answer preserves that gap. It remains an unmet A1, and the original source, plan, audit and rubric are preserved. The pre-call audit establishes checked selected meanings and qualifiers, not that every novel plan already passes every application criterion.

The held plans also use artificial shorthand with words run together. This is poor input representation, and the new adapter's copying exposes it. A short whitespace count on those outputs is not a successful test of natural-language compression. Neither defect is fixed retrospectively in the frozen pack.

## Measured stored answers

Scores below count met source/application compounds; uncertain units are separate. They are dependent annotations by the same unblinded assistant who wrote the plans/targets. Compound units are not independent statistical samples.

| Identical input | Base | Raw-input eight-example adapter | New plan-input adapter |
|---|---:|---:|---:|
| Eight fitting point inputs | 56 met + 7 uncertain / 112 | 112/112 | 112/112 |
| Exposed Brazil/Sudan actual QA plan | 8 met + 2 uncertain / 14 | 11 met + 1 uncertain / 14 | 12 met + 2 uncertain / 14 |
| Exposed UK/Somalia checked plan | 7/12 | 12/12 | 12/12 |
| ICC France raw | 3/14 | 6/14 | 9/14, capped |
| ICC France checked plan | 3/14 | 11/14 | 13/14 |
| ICC Brazil raw | 4/14 | 4 met + 2 uncertain / 14 | 3/14 |
| ICC Brazil checked plan | 6 met + 1 uncertain / 14 | 10/14 | 14/14 |

Six raw8 fitting outputs are verbatim targets; the two Indian outputs are faithful paraphrases. The new adapter reproduces all eight targets verbatim. Exact fitting is not transfer evidence.

The new ICC planned answers retain all sixteen source compounds. Brazil also retains all six supplied analytical meanings, including costs and authority boundaries; France retains five, with the upstream other-case comparison absent. The answers substantially copy the plans' fused wording. The nominal strict ICC planned result is base 0/2, raw8 0/2 and plan8 1/2 under the frozen factual/universal/whitespace/cap checks. Readability was not established by that strict result.

Raw-source task execution deteriorates. France repeats the nearly complete source in each requested section and ends mid-name at 2,048 tokens (1,706 whitespace words), without a current-Z assessment, concrete operations/cost or authority conclusion. Brazil repeats selected source clauses across sections (845 words), also without those task components. Their source-coverage arithmetic must not be advertised as a usable raw-task gain.

For the long actual Sudan plan, the new adapter restores the not-issued negation and provided operations, but prints 498 words in many headings instead of the requested three sections. Its “not issued by Brazil” over-resolves the previously documented publication-body ambiguity, retained as uncertain. UK/Somalia retains the twelve required meanings with no French pooling or unrelated counter-Taliban insertion. All older criteria and grades are unchanged.

## Native and portable checks

The run uses the pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 SDPA text loading, thinking disabled and greedy 2,048-token generation with an 8,192-token total limit. Hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**, GPU UUID `GPU-e485015c-8b0a-afe0-666e-86eec344e76f`.

Training takes **469.59 seconds**, with **16.04 GiB** peak allocated GPU memory. Actual processing is 859,872 sequence tokens, 164,832 both-completion tokens and **75,808 chosen supervised tokens**. Rejected/reference forward computation remains for matched native batching; it receives no preference gradient. The objective is chosen-token NLL only, without chosen-plus-DPO, approximate KL or introspective SFT.

Native checks confirm all 248 initial LoRA B matrices are zero, exact base/probe logits, identical fresh adapter tensor digest to raw8, actual chosen-only loss and masks, zero rejected/prompt/padding logit gradients, eight exact pair exposures of 32, 256 finite-gradient updates, frozen reference tensors, saved tensors and perturbation/reload verification. Portable replay checks source/spans/hyphens, target/point reconstruction, actual negative provenance, native inputs/outputs, all three arms' matching protocol, stored reviews/word counts/cap flags and positive process-exit identities. These are software/integrity checks, not independent semantic review.

An inspection script initially assumed every raw8 fitting output was verbatim. That assertion stopped before a review was saved because the Indian answers are paraphrases. Full diffs were inspected, output hashes/word counts were corrected, and the failed script/receipt retained. No additional model calls, GPU launches or updates came from that CPU review failure. No model run failed.

## Artifacts and next decision

- Frozen draft/fitting packs: `data/prepared/plan-input-20261006-v1`, `data/prepared/plan-input-fit-20261006-v1`.
- Raw primary evidence: `data/raw/plan-input-icc-grounding-20261006-v1`.
- Hand source/target audit: `reports/plan-input-target-source-audit-20261006-v1.json`.
- Baseline: `runs/aurora-plan-input-base-20261006-v1`.
- Matching raw8 comparison: `runs/aurora-plan-input-raw8-20261006-v1`.
- Fresh fit/initial and saved adapter: `runs/aurora-plan-input-fit-20261006-v1`.
- Replay/evidence receipt: `reports/plan-input-checkpoint-20261006-v1.json`.
- Portable verifier: `scripts/verify_plan_input_checkpoint.py`.

The next informative candidate is **three no-fit answers on exposed Brazil/ICC**: expand the same complete checked plan into normally spaced English bullets by hand, preserve every meaning/source/scenario/frozen criterion, and compare base/raw8/plan8 on identical inputs. That separates useful realization from copying defective shorthand; it is exposed development, not new confirmation. Inspect those answers before selecting any further fit. No next pack, fit, queue or sweep is prepared at this checkpoint.

Independent review remains pending. The ICC family is outside fitting but shares UN/Council genre; corpus/pretraining exposure is unknown. Country/topic remain correlated. No country persona stability, native prediction, autonomous multi-agent, broad OOD or distributed/NCCL gain is established. Preserve the Germany/China work, all historical adapters, strong base-plus-plan controls and failed receipts.
