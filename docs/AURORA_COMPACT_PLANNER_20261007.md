# Keep the faithful writer; train and test the upstream extractor separately

The saved point8 writer now passes three checked-plan cases: the earlier Brazil/Libya case, France/Libya, and a new France/Ukraine speech. **It preserves all 14 required meanings and four source checks in 262, 265 and 260 words respectively.** These are given-content realization results, with compact points authored and graded by the same assistant. The two Libya cases are exposed development; the Ukraine control was frozen before its first calls. This does not establish autonomous country-persona or multi-agent quality.

The upstream small-model planner remains the limitation. Its first raw-source-plus-hypothetical answer invents a French aid suspension and a condition requiring military targets to be neutralized before aid. A source-only probe removes those inventions but loses important qualifications. We therefore test **one audited source-only target**, first at 32 updates and, after inspecting that result, one fresh matched 64-update fit. More exposure fits the example; it does not produce a reliable outside-source extractor.

## Measured results

| Task and input | Base | Saved point8 writer |
|---|---|---|
| France/Libya, same 279-word checked points | 4/14; 296 words; extra section and false operational office | **14/14; 265 words; full pass** |
| New France/Ukraine, same 273-word checked points | 6/14; 306 words; extra section/source-analysis mixing | **14/14; 260 words; full pass** |

The writer almost literally flattens complete, normally spaced bullets into the requested paragraphs. It preserves genuine continuing support and a genuine **conditional** response while denying an unsupported hypothetical endorsement or future-vote guarantee. The source is not needed again by this bounded writer; its quality depends on the supplied points.

| Actual extraction/planning | Full compound coverage | Words | Result |
|---|---:|---:|---|
| Raw Ukraine source plus Z, questions only | 1/14 | 292, limit 280 | Invented aid/support conditions; no usable plan |
| Same Ukraine source, factual questions only, no Z | 1/8 | 146, limit 210 | Partial true facts, lost qualifications |
| Source-only fitting case after fresh 32 updates | 7 met + 1 uncertain/8 | 210 | War-actor sentence ambiguous; not exact target |
| Separate Libya source after 32 updates | 7 met + 1 uncertain/8 | 308 | More detail; over budget; ambassador-posting ambiguity |
| Source-only fitting case after fresh 64 updates | **8/8 plus four source checks** | **198** | Exact preferred target; fitted source-only pass |
| Separate Libya source after 64 updates | 2 met + 1 uncertain/8 | 309 | No pass; omitted qualifiers and unsupported additions |

The matching Libya base is 1/8 at 163 words. Compound units require all their concrete parts: a low score does not mean every statement is false. For example, the 64-update Libya answer includes many more valid details but drops the report ordinal, four-inquiry scope, national arrests, regional seminar qualification and explicit investigate/prosecute obligation. It also generalizes “nearing completion” beyond the single specified inquiry and does not clearly preserve the ambassador's posting. The 32- and 64-update outside results do not improve monotonically. Neither should be used unchanged downstream.

The source-only task is explicitly separate from the full 14-unit pipeline. Its eight documentary units exclude the six application/authority units only for this diagnostic; the full-task criteria and goal remain intact. Removing Z, changing the task and changing the word limit occur together, so the source-only comparison does not isolate one attention mechanism.

## Primary source and hand inspection

The new record is [S/PV.9693, 25 July 2024](https://digitallibrary.un.org/record/4059679), the Ukraine arms-delivery debate. The [official English PDF](https://documents.un.org/doc/undoc/pro/n24/220/27/pdf/n2422027.pdf) has 18 pages, 528,877 bytes, SHA256 `c15af9f660d429fc474bbf04b4c72f1d8434e7e34d0b2cb02a9abc724bfef833`. All 17 body-page word inventories survive two-column extraction. The cover and page 13 were viewed; the complete selected national French speech was read.

The national de Rivière span is offsets **56228–59631**, ending before Sierra Leone/George. The earlier procedural de Rivière intervention is excluded. Russia/Nebenzia–Polyanskiy chair; France speaks nationally. The selected span supplies no vote label. Recorded geopolitical assertions and France's interpretation of the ICJ request remain **attributed to France**, not independently adjudicated world facts. Only printed intraword-hyphen whitespace is joined; raw bytes/text remain preserved.

All source criteria, hypothetical Z, factual questions, both compact checked controls, the preferred 198-word block, and all twelve complete actual outputs were read by the root assistant. The preferred source-only target is the documentary block of the checked plan; neither that block nor answers to the questions are supplied to the student. Libya's full source and criteria were reread; its new source-only questions and 210-word limit were frozen before either fit. This is an already exposed source outside these two fits, not sealed OOD. Corpus/pretraining exposure is unknown. Independent semantic review remains pending.

## Training and integrity

Both fits start from fresh zero-effect LoRA on the pinned Qwen3.5-4B base, with identical target, input, paired actual negative, reference initialization, runtime and inference protocol. Only the selected update count changes: 32 versus 64 presentations. The negative is an inspected actual base output and has **zero gradient**. Native chosen-token NLL is the only optimized objective; no active DPO, added KL, introspection, resumed optimizer or sweep. The writer weights stay fixed.

Actual native checks cover masks/logit gradients, fresh initialization, finite parameter updates, reference immutability, pair presentations, token counters and exact saved-state reload. The 32-step training takes 45.08 seconds/14.01 GiB; the receipt records the corresponding 64-step measurement. Hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Every before/after source input is token-identical; generation remains pinned, greedy, nonthinking, 2,048 tokens, with no truncation.

This checkpoint adds **12 fully read, uncapped generation records and 96 actual optimizer updates**. Cumulative recorded Qwen3.5 updates are **2,622**, separate from the 582 Qwen2.5 reproduction updates. All nine successful project process identities exited, with host/GPU UUID/PID/start/command/run directory recorded; unfamiliar processes were untouched.

An initial raw-planner S5 grade counted the omitted partner component from context. It is corrected under the unchanged criterion, with original annotation/inspection preserved and no pass changed. A portable verifier initially assumed the latest inspection hash was the launch-time review; it stopped on this correction. The final verifier resolves the exact preserved historical review hash. Failure/code/log receipts are retained; no extra calls or updates occurred.

Evidence: `reports/compact-planner-checkpoint-20261007-v1.json`; replay: `scripts/verify_compact_planner_checkpoint.py`. Inputs are under `data/prepared/compact-france-*`, `actual-compact-planner-*`, `source-only-compact-probe-*` and `source-extraction-*`. Complete actual outputs and grades are in their corresponding `runs/aurora-*` directories. Raw primary evidence is under `data/raw/compact-planner-ukraine-grounding-20261007-v1`.

## Next useful change

Keep the successful point8 writer fixed. Improve the upstream data before adding loss complexity or repeating this one-example optimization: retain the fitted target, add source-complete examples and contrasts that preserve legal/temporal qualifiers, and freeze another source monitor before fitting. Train extraction separately from hypothetical application, then test the full 14-unit pipeline with actual model-generated points. Inspect each result before expanding. No next pack, fit, queue or sweep is prepared. Preserve Germany/China and every existing branch, source, failed run, criterion and grade.
