# Aurora Qwen3.5-4B training smoke — 30 September 2026

**The small single-GPU training test passed. No large inference campaign is needed before technical training tests.** The user clarified that Aurora's immediate purpose is small training tests and requested the Qwen3.5 family at 8B or smaller. This checkpoint uses the official [Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B) text model, separately versioned from the historical Qwen3-8B experiments. It does not establish persona quality or clear the substantive-training evaluation gate.

## Question and scope

Can a small official Qwen3.5 checkpoint complete answer-only BF16 LoRA updates on one Aurora Blackwell GPU, show finite loss/gradients and changed adapter tensors, and save/reload exactly? Four existing authored correction tasks, one per FRA/GBR/IND/BRA country, provide four baseline and four adapter controls. These are the training prompts, not held-out evaluation. Two optimizer steps, gradient accumulation four, rank eight, learning rate 5e-5, seed 42, thinking disabled, 2,048-token context and 128-token generation cap.

No multi-seed sweep or subsequent experiment was launched. The prepared nine-call synthesis-format comparison remains unrun and is not a prerequisite for this technical smoke.

## Measured result

| Check | Observation |
|---|---|
| Model | `Qwen/Qwen3.5-4B`, revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; 11 downloaded files verified against Hub hashes and rehashed before launch |
| Text weights | 4,205,751,296 parameters; no missing, mismatched or unexpected loading keys |
| GPU | One RTX PRO 6000 Blackwell Server Edition, CUDA capability 12.0; UUID `GPU-e5de478a-c420-a9e6-0e18-093f28ed5069` |
| Runtime | Torch 2.8.0+cu128, Transformers 5.17.0, TRL 1.14.1, PEFT 0.21.1, Datasets 5.0.1, Accelerate 1.15.0; full dependency inventory retained |
| Actual masks | Four examples, 1,746 sequence / 199 supervised tokens per pass; prompt and padding tokens excluded |
| Optimization | Two steps, eight microbatches, 3,492 sequence / 398 supervised tokens processed; two finite gradient audits; all 496 adapter tensors changed and remained finite |
| Timing/memory | 4.302 seconds around `trainer.train()`; 9.251 GiB peak allocated GPU memory during training, not total process or reserved-memory usage |
| Training-target loss | Token-weighted evaluation-mode loss 0.290596 → 0.190879 on the same four targets; this is fitting, not generalization |
| Serialization | Saved tensors exactly equal; adapter zeroed then reloaded; identical final-token logits on a 32-token probe, maximum difference 0 |
| Delivery | Four answers before and four after, identical input-token digests; all eight inspected |
| Software | 19 shared CPU optimization/mask/reload fault-injection tests passed in this runtime |

The successful launch is `runs/aurora-qwen35-4b-smoke-20260930-v3/`. Its `launch.json` records host, PID 1757430, process start ticks/time, command, selected GPU UUID and run directory before CUDA initialization. The process exited normally and its GPU returned to zero memory use. Existing processes on GPUs 0 and 6 were left untouched. This verifies single-GPU CUDA training; **NCCL and distributed training remain untested**.

## Answer inspection and limits

One assistant inspected all eight complete transcripts against their supplied excerpts and synthetic drafts. Both base and adapter perform the core requested corrections: France's European pillar is **within** the Atlantic Alliance; NATO is **foremost** for the UK; India's target concerns **emissions intensity of GDP**, not total emissions; Brazil supports rather than opposes needs-based flexibility for other developing members.

The base's India and Brazil responses reach the 128-token cap after already supplying their corrected sentences/citations and then adding explanation. The adapter's four answers stop before the cap and are closer to the terse targets. France's wording changes; the UK answer is byte-identical. This is a visible training-control observation, not independent grading, fresh-case improvement or demonstrated country-persona gain. The prompts and targets were already exposed to training and were assistant-authored research fixtures. Independent semantic review remains pending.

## Compatibility failures preserved

The newer Transformers stack returns `BatchEncoding` from chat tokenization by default and changed trainer arguments. The new runner requests token IDs explicitly; the shared mask auditor accepts either the historical list or the current mapping, with regression checks for both. The old model lock and packs are preserved.

Two launch failures were inspected before retrying in fresh directories:

1. `...-v1/`: the model loaded, but loading-report sets could not be serialized. No generation or optimizer step ran. The original log, launcher/shared-check source bytes and manually recovered failure receipt are retained.
2. `...-v2/`: the removed `use_model_defaults` generation argument was rejected before any answer or training. The runner now supplies an explicit greedy `GenerationConfig`; the original failure receipt/log/source bytes are retained.

The successful v3 uses the same immutable prepared pack and model, with fresh outputs. Each launch captures its own code bytes; failed receipts are not replaced by successful results.

## Next decision

**We are ready for another bounded small training test on Aurora.** Model downloading, single-GPU execution, masks, optimization and serialization no longer block it. A distributed smoke is only needed if the next experiment actually requires multiple GPUs; a 4B LoRA run fits comfortably on one device at these sequence lengths.

Before a behavioral learning claim, select reviewed training supervision and a small source-checked evaluation on distinct cases. Keep the base/adapter comparison matched on this model revision, GPU type, runtime, prompts, evidence and decoding. Avoid repeatedly measuring the same four easy corrections: the base already answers them. The existing ten-case/twenty-step fit probe can diagnose longer fitting or repetition if that becomes a concrete question, but it cannot demonstrate generalization. Independent rubric review and broader independent event families remain substantive-research requirements.

## Evidence and reproduction

- [Configuration](../configs/posttraining/qwen35-smoke-20260930.json), [model download verification](../reports/qwen35-model-verification-20260930.json), [checkpoint receipt](../reports/aurora-qwen35-training-smoke-20260930.json)
- [Successful measured run](../runs/aurora-qwen35-4b-smoke-20260930-v3/run.json), [answer inspection](../runs/aurora-qwen35-4b-smoke-20260930-v3/inspection.json), [complete paired transcripts](../runs/aurora-qwen35-4b-smoke-20260930-v3/paired-controls.md)
- Prepared controls: `data/prepared/qwen35-smoke-20260930-v1/`; original `training-readiness-20260928-v1/` is unchanged.
- Explicit Aurora runner: `scripts/run_aurora_qwen35_smoke.py`; fresh output required, no Slurm impersonation, selected GPU must report idle immediately before launch.

Source the private Aurora environment profile, use the configured scratch runtime, expose exactly the chosen idle GPU UUID through `CUDA_VISIBLE_DEVICES`, and pass the same UUID to `--gpu-uuid`. Launch with `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`, `TOKENIZERS_PARALLELISM=false`, `OMP_NUM_THREADS=4` and `--output` pointing to a fresh run directory. The pinned verified weights must already exist at the configured scratch location; otherwise use the separate downloader with private `HF_TOKEN_PATH`. Never put a token in command arguments or repository files. Model weights, credentials, environments and caches remain outside the snapshot; the small adapter and receipts are included.

The private GitHub handoff for this checkpoint is [aurora-handoff-20260930-v1](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20260930-v1), with code and bounded ignored evidence. The prior September 29 archive and Germany/China releases remain preserved.
