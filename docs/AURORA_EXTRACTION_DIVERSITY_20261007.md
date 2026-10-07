# Two-source fitting succeeds; source-status transfer still fails

Two short, fully audited extraction targets now fit exactly after **64 total updates**, 32 presentations each. A longer 128-update fit also reproduces both. Neither produces a usable summary on the separate French statement. More optimization causes a capped repetition failure; less optimization removes repetition but still turns requested actions into accomplished ones. Keep the previously successful writer fixed and change how the upstream targets preserve source status before adding more full-summary fitting.

## Actual comparisons

All summary inputs contain complete national statements and factual questions, with no checked answers or hypothetical scenario. The first two input/token sequences, the original 198-word Ukraine target, and the 194-word Libya documentary block remain unchanged. The third statement and criteria were frozen before any new base/adapter calls or fitting.

| Weights | Ukraine fitting source | Libya fitting source | Separate Gaza/Middle East source |
|---|---|---|---|
| Base | 1/8; 146 words | 1/8; 163 words | 3/8; 214 words |
| Earlier one-source/64 | Earlier exact 198-word target | Earlier 2 met + 1 uncertain/8; 309 words | 6/8; 236 words |
| Fresh two-source/128 | **8/8, exact 198 words** | **8/8, exact 194 words** | 0/8; **2,030 words, 2,048-token cap** |
| Fresh two-source/64 | **8/8, exact 198 words** | **8/8, exact 194 words** | 2 met + 2 uncertain/8; 195 words |

All four source guards pass on both fitting answers. No separate-source summary passes all eight source compounds, four guards and the 210-word limit. Full compound counts require every specified part; they do not measure the fraction of individual true facts. The lower-exposure answer retains many more correct details than its 2/8 count suggests, but important status/scope changes remain.

The 128-update monitor begins with a partial ceasefire/solidarity/civilian-protection point, then repeats “actual ongoing” until the cap. All stored text was read, including the repetitive suffix. The lower-exposure summary says “Council resolutions implemented” where France says they **must finally be implemented**. It says “Iran ends funding and arms and destabilizing actions” where France urges Iran to cease destabilizing actions. Sovereignty scope and “not actual partnership” also introduce uncertainty. Both fitted targets being exact is insufficient for source-faithful transfer.

The new monitor's S1 includes the named speaker/date and Macron attribution; those are not inferred from merely generating a generic ceasefire sentence. S3 preserves the concrete **recognition** decision concerning five settlements. The earlier one-source answer omits these, though it preserves most other qualifications. Original criteria and grades remain intact. Libya's older S1 has a different, preserved scope and does not demand the same explicit output metadata. This supervision asymmetry is disclosed rather than retroactively changing the fitting target or rubric.

## A smaller diagnostic after inspecting both fits

We then ask only about two real Council clauses, supplying the same complete source to base and the new 64-update adapter. The request asks for an exact modal quotation, a status category, and whether the statement establishes that the action happened. It supplies no answers. This is an exposed four-unit, 100-word diagnostic, **separate from** the eight-compound summary and fourteen-unit application goal.

Base gives both exact quotations and answers “Required / No”: **4/4**, 30 words. The adapter gives both exact quotations and “not established,” but labels the desired unanimous call “Conditional”: **3/4**, 28 words under the frozen category criterion. The class mismatch and possible ability-versus-condition taxonomy ambiguity need independent adjudication; it does not mean the adapter claims the call occurred. All four source guards pass on both outputs.

Thus both models preserve the critical modal wording and avoid claiming either action was accomplished when the question focuses on these clauses. This is compatible with distinctions being lost during summarization, rather than those distinctions being entirely unavailable to the model. It does not isolate a single mechanism: task density, requested quoting and the word budget change together. It is not an improvement caused by training.

## Sources, hand inspection and integrity

The new primary record is [S/PV.9687, 17 July 2024](https://digitallibrary.un.org/record/4059300), [official English PDF](https://documents.un.org/doc/undoc/pro/n24/211/52/pdf/n2421152.pdf): 32 pages, 717,449 bytes, SHA256 `cc9a9c0c5ee83b8da436bd7eea0a54447525ea93f4702c14dd69b68979dcd1bd`. All 31 body-page whole/split word inventories match. The cover and pages 24–25 were viewed. France/de Rivière's entire national speech, offsets 111607–114813, ends before the Russian President introduces Iran/Bagheri. Ecuador's preceding statement and Iran's following statement are excluded. Only printed intraword-hyphen whitespace is joined; raw PDF/text/spans are preserved. Browser metadata opens returned 403; official API/PDF acquisition succeeded and its cover confirms identity/date.

The root assistant reread all three complete selected speeches, questions, criteria, both preferred targets, the private monitor feasibility text and **all twelve complete stored generation records**. Eleven records are uncapped; one is a capped failure, not a complete task answer. The two preferred targets were already source-checked documentary blocks. No independent teacher or semantic reviewer is involved. The private feasibility text's settlement decision was made explicit in the final pack, preserving its original version; neither version is model input or an optimized target. A finalizer configuration-path mismatch stopped on CPU before fitting and its code/failure receipt is preserved.

Both new fits use fresh zero-effect LoRA, the pinned Qwen3.5-4B model/runtime, greedy nonthinking inference and identical data. Chosen-token NLL is the only optimized objective; the actual inspected base negatives and frozen reference have no preference gradient. Native masks/logit gradients, initialization, reference immutability, actual pair presentations, finite parameter updates and exact saved-state reload pass. At 128 updates each target receives 64 presentations; at 64 each receives 32. Doubling targets while retaining 64 presentations doubles total compute versus the earlier one-source fit, so that first comparison is not a fixed-budget causal diversity ablation.

Training takes **193.67 seconds / 14.99 GiB** and **98.77 seconds / 14.99 GiB**, on **NVIDIA RTX PRO 6000 Blackwell Server Edition**. This checkpoint adds **192 actual optimizer updates**, bringing recorded Qwen3.5 updates to **2,814**, separately from 582 Qwen2.5 reproduction updates. All six positively identified project GPU processes exited. Host, GPU UUID, PID/start identity, command and run directory are recorded; unfamiliar processes were untouched.

Evidence: `reports/extraction-diversity-combined-20261007-v1.json`; portable replay: `scripts/verify_extraction_diversity_combined.py`. New inputs are under `data/prepared/extraction-diversity-*` and `modal-status-probe-20261007-v1`; raw evidence is under `data/raw/extraction-diversity-gaza-grounding-20261007-v1`; complete answers/grades/weights are in corresponding `runs/aurora-*` directories. Software replay validates bytes, native execution and stored annotation arithmetic, not independent meaning judgments.

## Next decision

Preserve the writer, earlier extraction weights and both new fits. Do not add full-summary updates or bulk data to this recipe. First define source fields that retain actor, actual claim/request/conditional commitment and critical modal wording; adjudicate the category ambiguity, then test a small reviewed target-format comparison with a separate source and strong base controls. Preserve every existing compound, historical grade and the full fourteen-unit application objective. Actual generated-point application, autonomous persona behavior, native prediction, multi-agent improvement, independent review and strong OOD transfer remain unproved. No next fit, queue or sweep is prepared.
