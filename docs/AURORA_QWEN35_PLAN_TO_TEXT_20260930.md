# Supplied-content plan-to-text trial, 30 September 2026

The user's proposed division of work is useful in this small development trial: an upstream LLM reads the source material and supplies checked bullet points, including the positions and uncertainty; Qwen3.5-4B turns that content into a policy memo. The checked plans already repair the main draft-support and false-consensus failures in the untrained model. One 20-step complete-task SFT fit adds formatting and selected content repairs, but still omits supplied details. This is evidence about realizing given positions, not learning or predicting national decisions.

All six complete answers were inspected by the same assistant that authored the plans and targets. There is no independent review, aggregate validated fidelity score, sealed test or persona-quality gain claim. Earlier experiments and Germany/China releases remain preserved.

## Question, inspected decision and actual run

First, can the base faithfully realize three checked plans for the already-exposed climate, Ukraine and South Sudan contexts? If it covers them faithfully, avoid redundant training. If useful errors remain, try one small complete-task adapter with matched inputs and an outside-training monitor.

The three base answers completed normally and repaired the core failures. They nevertheless invented writing dates in all three memo headers and omitted some supplied points. This justified one fresh-base fit on **two complete climate/Ukraine memos**, rather than another fit on short corrections. South Sudan was excluded from optimization. It was already exposed and inspected before training, so it is a development monitor, not a held-out test.

| Inspected behavior | Base with checked plans | Adapter with identical plans |
|---|---|---|
| UK support for US-Albania Ukraine draft | Correct support; no retained opposite claim | Correct support retained |
| Country-specific differences and limited common ground | Central false-consensus failures absent | No recurrence of those failures observed |
| Invented memo writing date | Present in 3/3 answers | Absent in 3/3; source dates retained |
| Brazil climate-related development harms | Omitted | Restored in training control |
| Brazil immediate ceasefire | Omitted | Restored in training control |
| France humanitarian-worker protection in South Sudan | Omitted | Restored outside training |
| EU assistance in South Sudan | Correct institution and no invented protection conditionality | Both retained; continuing-support point still omitted |
| Other South Sudan coverage | Some remaining omissions | Newly omits France implementation resources, electoral legal framework and India's 8.9-million humanitarian figure |

The adapter's Ukraine memo also repeats a writing instruction (“do not assert a vote…”), instead of consistently expressing finished prose. Its climate memo keeps the two institutional camps clear in the national paragraphs but removes the base's explicit comparison sentence. These details limit a claim that it has completely learned the requested format or preserves every point.

The raw-source historical contrast changes many things: checked content is now given, instructions and input length change, and erroneous prior notes are removed. It cannot isolate the effect of bullet formatting or demonstrate superiority over a matched raw-source pipeline. The base/adapter comparison within this trial does use identical plans, prompt tokens and generation settings.

## Teacher preparation and supervision

This session's LLM assistant read the twelve complete bounded source statements, authored the plans and checked their scope. No separate teacher endpoint was called; there is no metered upstream-teacher cost. The student receives the checked bullet points and source identifiers, rather than full source texts or their supporting quotations. The audit pack retains source digests, located quotation spans and absence checks against the full bounded statement.

The first prepared plan pack missed explicit India/UNMISS humanitarian deliveries in South Sudan. It was preserved without any model call; the correction produced a fresh V2 pack before inference. Mechanical criterion references cover the existing 24 climate, 25 Ukraine and 13 South Sudan national criteria. This verifies navigation coverage, **not** semantic correctness or a 62-unit model score. Same-assistant semantic inspection remains provisional.

The two targets are complete 434- and 453-word analyst memos, authored from the frozen plans after base inspection. They include national positions, genuine common ground, unresolved differences and proposals distinct from commitments. They are synthetic supervision, not authentic government statements. Their prompts exactly equal the first two evaluation prompts. This gives training controls, not generalization evidence.

The fit uses fresh Qwen3.5-4B weights, rank-8 all-linear LoRA, BF16, learning rate 5e-5, two examples per optimizer step and 20 steps. The base weights remain frozen and loss applies only to the memo completion tokens. No decision labels or unavailable later votes are inferred. No earlier adapter was resumed.

## Measured execution and verification

Both runs use **NVIDIA RTX PRO 6000 Blackwell Server Edition** GPUs on Aurora, the pinned model revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, the official text-only Qwen3.5 class, thinking disabled and greedy generation with a 2,048-token cap. All prompts plus the output allowance fit the 8,192-token context without truncation. Torch 2.8.0+cu128, Transformers 5.17.0, TRL 1.14.1, PEFT 0.21.1, Datasets 5.0.1 and Accelerate 1.15.0 are locked.

- Training: **44.43 seconds**, **9.66 GiB** peak allocated memory, 74,400 processed sequence tokens and 23,340 supervised tokens. Same-target token-weighted loss **0.68184 → 0.26669**. This measures fitting, not generalization.
- Actual trainer completion masks passed on both examples. All 20 gradient checks were finite, all 496 adapter tensors changed, and saved-state reload after perturbation reproduced the 32-token probe logits exactly.
- Base generation: 3,891 input tokens, 2,626 output tokens, **40.67 seconds**. Adapter generation: identical input tokens, 1,764 output tokens, **43.32 seconds**. Shorter answers did not reduce measured generation time here. Teacher preparation is excluded; this is not an equal-total-compute efficiency claim.
- All three prompt/case/plan digests match between arms; model bytes, runtime, hardware type, shared inference-helper bytes and effective generation configuration match. Different GPU UUIDs were used because another process occupied the base GPU after it exited.
- Six pack software checks passed: exact captured-builder replay, unchanged evaluated content after an all-country guard, exact training-pack replay, and rejection of missing-country, missing-criterion and absent-quote mutations. These are software checks, separate from the assistant's output judgments. Frozen V2 keeps the builder actually used before inference; current code adds the all-country guard without changing evaluated content.

Launch identities record host, GPU UUID, PID, process start time/ticks, command and run directory before CUDA work. Both project processes exited normally. Unfamiliar VLLM/Ollama/llama-server processes were observed and left untouched; no process was cancelled. This is single-GPU CUDA execution, not distributed/NCCL verification.

## Evidence and resulting next decision

- [Base configuration](../configs/posttraining/qwen35-plan-to-text-base-20260930.json), [fit configuration](../configs/posttraining/qwen35-plan-to-text-fit-20260930.json), [teacher plans](../configs/posttraining/qwen35-plan-to-text-content-20260930-v2.json) and [complete teacher targets](../configs/posttraining/qwen35-plan-to-text-targets-20260930.json).
- [Base receipt](../reports/aurora-qwen35-plan-to-text-base-20260930.json), [fit/inspection receipt](../reports/aurora-qwen35-plan-to-text-fit-20260930.json) and [verification receipt](../reports/aurora-qwen35-plan-to-text-verification-20260930.json).
- Prepared packs: `data/prepared/qwen35-plan-to-text-eval-20260930-v1/`, `qwen35-plan-to-text-eval-20260930-v2/`, and `qwen35-plan-to-text-fit-20260930-v1/`.
- Runs: `runs/aurora-qwen35-plan-to-text-base-20260930-v1/` and `runs/aurora-qwen35-plan-to-text-fit-20260930-v1/`. Each retains full transcripts, captured source, launch/configuration evidence, inspection and exit receipts. The fit also retains `complete-comparison-memos.md` and its adapter. Preparation review is in `runs/qwen35-plan-preparation-review-20260930-v1/`.

Keep checked-plan realization as a useful direction. Most of the diagnosed position repair was already present before SFT; the adapter contributes observable formatting and selected coverage changes, with omissions outside training. **Before increasing optimization**, freeze a separate-context plan pack with atomic coverage and source/absence audits, review the upstream planner independently where possible, and compare this adapter with the base on identical plans. Check omissions alongside invented positions. Do not repeat short correction fits, queue a sweep or turn these three exposed examples into a persona-quality claim. Independent review remains pending.

Git code synchronization alone excludes the prepared packs, transcripts and adapter. A fresh verified handoff archive must include them alongside the preserved historical evidence; weights, credentials, environments and caches remain outside it.
