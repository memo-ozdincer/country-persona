# Aurora adaptive Qwen3.5 training results — 30 September 2026

**Small training runs now produce behavioral results, and those results change the next experiment.** On one NVIDIA RTX PRO 6000 Blackwell Server Edition, Qwen3.5-4B completed two new four-example, 20-step LoRA fits and 14 new comparison answers. All answers were inspected against their bounded sources before selecting another checkpoint. Some exposed-context claims improved, but the UK draft-resolution reversal survived both training recipes. Lower training loss did not imply reliable synthesis. The next method should supervise complete synthesis and country-specific evidence support rather than repeat the four short correction targets.

The [earlier two-step smoke](AURORA_QWEN35_TRAINING_SMOKE_20260930.md) established optimization and serialization. These experiments go beyond plumbing, but remain exploratory development: one unblinded assistant authored targets and inspected answers, independent semantic review is pending, and no aggregate fidelity score or validated persona gain is claimed. Germany/China releases and the historical Qwen3-8B locks, packs and results remain preserved.

## Inspected sequence and decisions

| Checkpoint | Concrete question and measured scope | Observation and next decision |
|---|---|---|
| Two-step adapter transfer | Does the earlier smoke adapter help on full synthesis? Three frozen prose memos, base then freshly loaded adapter: six answers, identical input digests, no output caps | Both reverse UK support of the US/Albania draft into rejection and invent all-four agreement. The adapter also loses required climate content and invents a later UK vote. Do not extend the easy four-case smoke blindly; train on diagnosed scope errors. |
| Source-only correction fit | Fresh base, four new short targets using complete climate/Ukraine sources, 20 steps; three original synthesis memos with frozen prior notes | Climate UK G-5 endorsement disappears, France military insufficiency and UK draft support return, and India's absolute-denial characterization is corrected. UK Ukraine draft reversal remains; false French draft rejection and conditional EU funding appear. Test whether the prior notes explain the failure. |
| Prior-note removal | Ukraine only, base and the source-only 20-step adapter: two answers; remove only the terminal notes, retain full sources/questions/decoding | Base quotes UK support but later still says its stance is against the draft. The adapter now states support correctly. Both retain unsupported collective claims. Notes affect the trained answer but do not explain all errors; test including those notes in training. |
| Correction fit with conflicting notes | Fresh base, same four target completions, seed, optimizer settings and 20 steps; add the exact frozen prior notes to training; three original synthesis memos | Target loss falls, but UK support is still interpreted as rejection and a later vote/majority passage is invented. Climate coverage improves in places; false consensus remains in every context. Stop repeating this correction recipe and change the supervised task. |

The four checkpoints were selected sequentially after full-answer inspection, not queued as a speculative sweep. Both 20-step adapters start from the same base, not from the two-step smoke or each other. The note-removal diagnostic changes input length. Adding notes to training increases input tokens and actual compute: equal optimizer steps do not constitute an equal-compute causal comparison. Comparisons with the original smoke also change targets and training duration.

## Optimization and decoding evidence

Model: `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`. Official model files were rehashed during each run before loading. Runtime: Torch 2.8.0+cu128, Transformers 5.17.0, TRL 1.14.1, PEFT 0.21.1, Datasets 5.0.1 and Accelerate 1.15.0. One BF16 GPU, rank-8 LoRA, learning rate 5e-5, seed 42, batch size one with accumulation four, completion-only loss, no packing or source truncation. Thinking is disabled; an explicit greedy `GenerationConfig` supplies a 2,048-token output cap within an 8,192-token context. The frozen memo instructions also request at most 700 words; this instruction is not a semantic completeness or word-count guarantee.

| Measured quantity | Source-only fit | Fit including conflicting notes |
|---|---:|---:|
| Examples / optimizer steps | 4 / 20 | 4 / 20 |
| Sequence tokens processed | 253,860 | 330,100 |
| Supervised tokens processed | 9,440 | 9,440 |
| Same-target evaluation loss, before → after | 2.303679 → 1.100455 | 2.157879 → 1.032410 |
| Training seconds | 191.448 | 315.849 |
| Peak allocated training memory, GiB | 11.335 | 12.067 |
| Finite gradient checks / changed adapter tensors | 20 / 496 | 20 / 496 |
| Save/reload final-token logit difference, 32-token probe | 0 | 0 |

Both actual trainer masks were audited; every adapter tensor changed and stayed finite. Saved tensors were checked, the in-memory adapter was perturbed, and reload restored probe logits exactly. These are optimization/serialization results. The losses use the same exposed training targets and cannot establish generalization. The original transfer freshly loaded and verified the two-step adapter; the note-removal run freshly loaded and verified the source-only 20-step adapter.

The original three base memos are reused for the two 20-step comparisons. Token digests match, as do model revision, GPU type, runtime, inference helper, source packet and decoding. There are 14 new answers: six transfer, three source-only fit, two note-removal, three conflict-note fit. None reaches the 2,048-token cap. No comparison treats historical H100/Qwen3-8B outputs as an Aurora/Qwen3.5 base.

## Behavioral finding and remaining errors

The UK source says to reject illegitimate actions and support the US/Albania draft. In the final conflict-note adapter answer, the correct support clause is quoted and immediately called rejection. An accurate quote does not repair its opposite interpretation. The same answer invents a later recorded vote and majority passage absent from the packet. It also claims all four delegations call for an immediate ceasefire and negotiations and judge the referendums illegitimate; those collective positions are not established by all four bounded statements. India does not discuss the referendums in its supplied statement. France does not supply the proposed referendum standards attributed to it alongside Brazil.

There are local repairs. The final climate answer retains France's military-insufficiency point and UK draft support, explicitly rejects the false characterization of India, and adds Brazil's scaling-up/timely-finance priority. The source-only adapter's false all-four UNFCCC-primary-forum endorsement is absent. But developed-country climate-finance priority is still wrongly attributed to France; France's climate/crisis understanding and resilience and UK meaningful participation of women/girls remain omitted. Removing a false G-5 endorsement by omitting the issue is not evidence that the model can now correctly attribute G-5 positions.

South Sudan is outside both new adapters' training but was already exposed in the first transfer and subsequent inspections. It is an exploratory monitor, not a sealed test. The final answer preserves UK election-date uncertainty and EU rather than French attribution of EUR 72 million. The source-only adapter's invented funding contingency is absent. However, it wrongly pools assembly formation, the 8.9-million needs figure, truth-commission welcome and Leer accountability across all four delegations. These claims have different country support. A collective paragraph with incorrect attribution cannot replace the omitted France/UK accountability details.

Complete answers and individual observations are retained, including regressions. These are qualitative assistant judgments, not calibrated independent ratings or 14 independent event samples. No full four-country production training or trained-analyst deliberation comparison has run. The historical nine-format-call Qwen3-8B diagnostic remains unrun; these Qwen3.5 experiments use its separately versioned prose subset and one explicit variant.

## Resulting next checkpoint

The working hypothesis is a mismatch between short correction supervision and deployment as a complete policy memo. That is an inference from these failures, not a proven mechanism. Replan the next small training comparison around complete, source-checked synthesis targets: country-specific positions first, documented common ground only where each relevant country supports it, explicit absence/uncertainty, preserved differences and proposals distinguished from government commitments. Include source-over-note conflicts deliberately. Do not fabricate observed negotiations or later votes.

Before that run, make the targets inspectable and check the known draft-position contradiction, unsupported consensus and required country content across the whole target. Use one fresh base initialization and a small matched comparator, retain an outside-training monitor, and inspect repairs and new errors before increasing data or steps. Independent criterion/source review and separate event families remain necessary for substantive quality claims. A distributed smoke is needed only if the next experiment needs multiple GPUs; these 4B fits use about 12 GiB allocated memory on one device. No further run is queued.

## Artifacts, ownership and continuity

- Receipts: [transfer](../reports/aurora-qwen35-transfer-20260930.json), [source-only fit](../reports/aurora-qwen35-scope-fit-20260930.json), [note removal](../reports/aurora-qwen35-note-ablation-20260930.json), [conflict-note fit](../reports/aurora-qwen35-conflict-fit-20260930.json).
- [Checkpoint provenance verification](../reports/aurora-qwen35-adaptive-verification-20260930.json) checks captured source/config hashes, transcript/inspection/adapter bytes, reused base input IDs and runtime/hardware/helper identity, unchanged target completions across the two fits, pack release hashes, output caps, process exit and current Python syntax. These are reproducibility checks, not semantic certification.
- Configurations: `configs/posttraining/qwen35-{transfer,scope-fit,note-ablation,conflict-fit}-20260930.json`. Prepared target packs: `data/prepared/qwen35-scope-fit-20260930-v1/` and `qwen35-conflict-fit-20260930-v1/`; the latter records its parent and exact prior-note digests. These are assistant-authored research fixtures, not admitted production training data.
- Runs: `runs/aurora-qwen35-{transfer,scope-fit,note-ablation,conflict-fit}-20260930-v1/`. Each retains launch identity, source-code copies/hashes, configuration, model verification, transcript and inspection. Fits also retain small adapters, actual masks, gradient traces and reload checks. Original model weights and credentials remain outside the repository.
- Runners: `scripts/run_aurora_qwen35_transfer.py` and `scripts/run_aurora_qwen35_scope_fit.py`, both supporting explicit `--config`, fresh `--output`, `--gpu-uuid` and exactly matching `CUDA_VISIBLE_DEVICES`. Source the private Aurora profile and use the configured scratch runtime and offline model flags. Never fake scheduler state.
- GPU UUID: `GPU-e5de478a-c420-a9e6-0e18-093f28ed5069`, on host `aurora`. Every launch recorded PID, process start time/ticks, command and run directory before CUDA. The final process exited and the selected GPU returned to zero memory use. Unfamiliar processes on GPUs 0 and 6 were left untouched. Recheck occupancy before another launch. NCCL/distributed training remains unverified.

Code synchronization and the [private results archive](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20260930-v2) preserve this checkpoint. The new snapshot includes both target packs, adapters and ignored transcripts; a Git clone alone is insufficient. Earlier smoke/portability snapshots and Germany/China releases remain preserved. Verify a restored copy with `python3 scripts/verify_research_handoff.py --root .`.
