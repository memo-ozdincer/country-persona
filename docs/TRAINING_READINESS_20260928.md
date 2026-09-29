# Small training run and deliberation readiness — 28 September 2026

The four-H100 training payload is prepared and scheduler-tested. **Update: a separate one-H100 allocation completed the 42-call untrained deliberation baseline and six-call diagnostic.** See [measured findings and next checks](DELIBERATION_BASELINE_20260928.md). No new production training has run. Source/rubric review and synthesis reliability remain gates before training. CUDA inference is verified; multi-GPU/NCCL training remains unverified.

**Next bounded check prepared:** [Nine-case evidence-format comparison](EVIDENCE_FORMAT_CHECKPOINT_20260928.md), including a fresh South Sudan event. Sources, 13 new proposed criteria, full-context preflight and mechanical audit tests pass locally; model inference is pending. The previous allocation's wall deadline has passed and SSH was unavailable at the latest check.

**Training verification hardened:** the actual GPU entry point now uses the same mask, loss, gradient, adapter-update and serialization checks exercised by the tiny CPU probe. A new local v3 handoff includes these changes; the previously uploaded v2 payload does not. Upload the v3 payload before using these checks on Trillium. This is technical readiness, not a new trained persona result.

**Review evidence added:** [Complete provisional assistant review of both events](DELIBERATION_SOURCE_REVIEW_20260928.md) covers all 42 responses, with paired content/check transitions and source-linked adjudication cards. Climate aggregation introduces unsupported claims even where national notes preserve uncertainty; the peer final memo also omits requested analysis despite ending normally. Independent ratings, 33 ambiguous rating instances and the pending format comparison still prevent treating this as a settled training evaluation.

## What the evaluation measures

“Country ideals” means **fidelity to a particular country's dated, attributed public policy**, with uncertainty where the evidence is silent. It does not mean a timeless national personality, or assume official positions represent every citizen. Reddit/public-opinion data are a separate population and must not silently become government ground truth.

| Outcome | Measurement | Current state |
|---|---|---|
| Observed actions | Vote accuracy, minority-class recall, macro-F1, conditional legal-label NLL/Brier; prompt sensitivity alongside correctness | Implemented and run on the exposed two-event pilot; interface robustness remains poor |
| Declared-policy fidelity | Required source-supported content, material qualifications, correct attribution/date, unsupported claims and commitments | Atomic rubric and real-output review kit prepared; independent ratings pending |
| Revision quality | Corrected omissions/errors, newly introduced errors, retention of initially correct content, explicit rating coverage | 42-call baseline completed; rating arithmetic tested; independent semantic scores pending |
| Deliberation benefit | Peer-discussion improvement minus independent self-revision improvement, per country and event; final memo separately rated | Frozen two-event protocol run; mechanical results and assistant source checks available |
| False consensus | Source-supported agreement/differences and invented concessions/commitments in final analysis | Explicit review units; numerical consensus is not treated as success |
| Reliability and cost | Full input/output tokens, latency, output caps, raw generation trace, source/model/adapter hashes | Measured on one H100; training measurements pending |

Before/after fine-tuning repeats the same sources, questions, budgets, prompts and review rules with the pinned base model and the new adapter. The final summarizer stays the unadapted base model in both runs, isolating changes to the participating analysts. Review each checkpoint without model labels, then compare paired country/event outcomes. Independent review and additional event families are needed before any substantive benefit or statistical-generalization claim.

## The bounded interaction experiment

Frozen pack: `data/prepared/deliberation-probe-20260928-v1/`.

France, the UK, India and Brazil analyze two documented debates: climate/security on 9 December 2021 and Ukraine on 27 September 2022. Every arm receives all four corresponding prior statements. These are authored retrospective workshops, not reconstructions of an actual negotiation or prospective forecasts.

1. **Independent revision:** four initial national analyses, four source-checked revisions that see only their own initial answer, one final memo.
2. **Peer revision:** identical initial prompts, then four revisions that see all four frozen initial answers, one final memo. No agent sees another agent's revised answer within the round.
3. **Single analyst:** one four-country analysis, one self-revision, one final memo. Its two analysis calls each receive four times the national-answer output allowance.

There are **42 calls per checkpoint**, with a maximum of **21,504 generated tokens**. Each arm has the same 3,584-token output allowance per scenario. The primary peer/self contrast also has equal call counts. Input tokens and actual generation lengths differ, so this is not a claim of equal actual compute. Record and compare cost separately; the central analyst has fewer calls.

The tokenizer-only run completed all 42 calls without truncation; the longest illustrative prompt had 5,175 tokens within the 8,192-token context budget. Its notes are placeholders, not model outputs or a proof that every possible generation fits. Every real prompt is checked again at runtime.

`review_deliberation_probe.py` creates the source-and-answer review deck, templates bound to exact response/rubric hashes, and per-condition arithmetic. Unreviewed semantic scores remain null. It refuses tokenizer placeholders as model results. The fixture tests demonstrate arithmetic and information boundaries; they do not validate the rubric's meaning.

## Training data: what we learned before increasing scale

The audited official UNBench training slice is extremely imbalanced for the four extension countries:

| Country | Yes | Abstain | No |
|---|---:|---:|---:|
| France | 729 | 5 | 0 |
| United Kingdom | 734 | 0 | 0 |
| India | 113 | 1 | 0 |
| Brazil | 208 | 9 | 1 |

Source: `data/raw/unbench-audit-20260926/full/UNBench-all/task2_train_author.csv`. These counts do not justify treating that slice alone as a useful test of nuanced national decision behavior. The larger authentic-QA pool inspected is China-only, outside this extension's scope. Existing UNGA reconstruction candidates still have speaker/coalition/date review gaps.

For a **technical optimization probe**, the separate policy-workshop set offers ten inspectable, source-backed, assistant-authored correction targets across eight source documents and four connected source components. We selected only its revision SFT view; correlated audit, preference and multi-agent variants do not become extra independent cases. Original quarantine records are preserved, and the export explicitly records research preparation rather than human approval.

Prepared pack: `data/prepared/training-readiness-20260928-v1/`.

| Recipe | Examples | Steps | Effective examples/step on four GPUs | Purpose |
|---|---:|---:|---:|---|
| smoke | 4, one per country | 2 | 4 | Check distributed optimization, saving and subsequent reload |
| fit-probe | 10 | 20 | 4 | Deliberate repetition to diagnose optimization and response behavior |

The full pack has 4,798 sequence tokens and **502 supervised answer tokens**, maximum sequence length 567. Exact source-PDF overlap with the two-event evaluation is zero; semantic event-family separation and model pretraining contamination are not certified. There is no meaningful held-out test within these ten cases. This probe does not replace the planned evidence-conditioned behavioral SFT experiment or establish generalization.

Both recipes use the pinned Qwen3-8B checkpoint, BF16 LoRA (rank 8), response-only loss, learning rate 5e-5 and seed 42. The scheduler dry run rejected the original two-GPU request: Trillium accepts one GPU or multiples of a four-GPU node and disallows explicit memory requests. The corrected allocation requests **four H100s, `def-zhijing`, one hour**, then executes `sleep infinity`. Experiments run as separate steps, leaving the allocation available until its wall limit. Maximum reservation is four GPU-hours; actual experiment cost must be measured.

## Checks completed and limits

- All ten examples passed actual TRL input/label inspection: prompts are masked; only the literal answer and terminator are supervised.
- A tiny randomly initialized Qwen3 network completed two CPU optimizer steps with finite loss (11.9244), changing 14 adapter tensors. Adapter tensors and same-base output logits matched after save/reload. This is software validation, not persona training or a quality score.
- A fresh run using the shared production checks audited all ten masks, then measured **940 sequence tokens and 79 supervised tokens actually consumed in two steps**. All 14 adapter tensors changed; both gradient checks were finite; saved tensors matched exactly and a 32-token same-base reload probe had zero maximum logit difference. A separate new-base PEFT reload check also passed. The 502 supervised tokens describe the whole ten-example inventory once, not the two-step run's consumption.
- The GPU trainer now captures initial adapter weights after DDP preparation, records per-rank step/token counts and gradients, requires matching initial/final adapter hashes across ranks, and checks finite loss plus actual updates before accepting completion. It verifies saved tensors and reloads them after deliberately perturbing in-memory adapter state, then compares a short same-base probe. Completion is written after all ranks reach the final barrier. Failure receipts are retained for errors during training/verification. This does not replace independent base-model/adapter evaluation.
- **42 targeted training/data tests pass**, including injected prompt-mask leakage, lost targets, nonfinite microbatch losses/gradients, unchanged adapters, missing/inconsistent rank reports and corrupted checkpoint tensors. The tiny CPU run exercises the shared TRL hooks, but the full 8B CUDA/NCCL path remains unverified.
- The local two-process attempt exposed a macOS Accelerate/PyTorch incompatibility: Accelerate passes device IDs to a Gloo barrier, and this PyTorch build selects unsupported MPS collectives. The checker now fails clearly for this configuration. No distributed/CUDA/NCCL success is claimed.
- **53 focused tests pass**, covering deliberation controls, source/hash binding, missing-rating handling, corrections/regressions, review arithmetic and inference/training regressions. The literal-mask/optimizer check also ran on the actual prepared data.
- The corrected payload was uploaded to `/scratch/memoozd/persona/research-readiness-20260928-v2`; all 33 hashes verified. Slurm accepted the four-H100 request in `--test-only` mode, and the 42-call tokenizer preflight passed again on Trillium. The earlier scheduler rejection is preserved as a failed checkpoint. Dependency verification on an allocated node, four-GPU training execution and training memory/throughput remain pending. One-H100 deliberation generations and measured inference cost are now complete.

Evidence: `reports/training-readiness-20260928.json`, `reports/training-readiness-20260928-trillium-validated.log`, `runs/training-readiness-20260928-cpu-single-v2/check.json`, `runs/deliberation-20260928-preflight-v1/run.json`, training `release.json`, and `runs/research-readiness-staging-20260928-v2/staging-manifest.json`.

New verification evidence: `runs/training-readiness-20260928-cpu-shared-checks-v1/check.json`, `reports/training-verification-20260928.json`, and `runs/research-readiness-staging-20260928-v3/staging-manifest.json`. The new v3 payload is local; no upload, scheduler submission or GPU run is implied.

## Next useful checkpoints

| Checkpoint | Inspectable output | What determines the next step |
|---|---|---|
| Review the existing 16-response policy/source kit | Independent ratings, disagreements and adjudicated ambiguous units | Repair criteria or source gaps before treating scores as reliable |
| Inspect the retained-allocation recipe and cluster environment | Scheduler test, current GPU/environment health, verified model bytes | Resolve infrastructure issues before spending time on a fit probe |
| Completed: 42-call interaction probe and six-call follow-up | Source-linked transcripts, cost, stopping behavior, review deck and diagnosed errors | Stabilize full-answer review and synthesis before scale |
| Run the two-step GPU smoke after the evaluation gate | Per-run losses, token counts, GPU memory, saved adapter and reload/eval outputs | Stop on nonfinite loss, missing updates, changed masks or repetition |
| Run the ten-case fit probe if the smoke is clean | Paired base/adapter outputs on the frozen evaluation | Diagnose learning or regression; do not label memorization a research gain |
| Expand reviewed training and evaluation families | Diverse, source-linked cases and whole-family splits | Freeze a substantive pilot with usable minority/uncertainty coverage |

The research motivation for the controls is consistent with [budget-aware evaluation of reasoning strategies](https://aclanthology.org/2024.emnlp-main.1112/) and [controlled comparisons of debate decision protocols](https://aclanthology.org/2025.findings-acl.606/). Those studies motivate accounting for additional computation and protocol choices; they do not validate this diplomatic task or guarantee that debate helps.

## Handoff commands

Local preparation (use a fresh destination):

```bash
PYTHONPATH=src .venv/bin/python scripts/stage_training_readiness.py --output runs/research-readiness-staging-20260928-v3
PYTHONPATH=src .venv/bin/python scripts/launch_training_readiness.py smoke --output runs/four-gpu-smoke-v1
```

The second command only prints the launch command. The v3 payload has now been built locally, so choose a fresh suffix if rebuilding. Upload v3 to a fresh `/scratch/memoozd/persona/research-readiness-20260928-v3` directory before using the new checks. The older v2 payload was uploaded and scheduler-tested; its scheduler recipe is unchanged, but it lacks the new verification module and trainer changes. Once the evaluation gate is resolved, validate and submit `scripts/trillium_training_allocation.sbatch` from the new staged directory. A test-only job ID/start estimate does not submit a real job. Do not run experiments on the login node. SSH into the allocated node and invoke steps from the staged directory:

```bash
# The allocated node, with the actual job ID and staged working directory:
srun --input=/dev/null --jobid=JOB_ID --ntasks=1 --gpus=4 --cpus-per-task=24 bash scripts/trillium_readiness_step.sh health
srun --input=/dev/null --jobid=JOB_ID --ntasks=1 --gpus=1 --cpus-per-task=12 bash scripts/trillium_readiness_step.sh deliberation runs/deliberation-base-v1
# Only after the evaluation gate:
srun --input=/dev/null --jobid=JOB_ID --ntasks=1 --gpus=4 --cpus-per-task=24 bash scripts/trillium_readiness_step.sh smoke runs/four-gpu-smoke-v1
```

The login environment previously rejected `srun`; run it on the allocated node. Training uses one Slurm task that launches four torchrun workers. When driving a node shell through SSH/heredoc input, use `srun --input=/dev/null` so one step cannot consume the next shell command. Keep the allocation alive between checks as requested.

After retrieving a completed deliberation run:

```bash
PYTHONPATH=src .venv/bin/python scripts/review_deliberation_probe.py --run runs/deliberation-base-v1 --output data/review/deliberation-base-v1
# Score one independently completed rating set at a time:
PYTHONPATH=src .venv/bin/python scripts/review_deliberation_probe.py --run runs/deliberation-base-v1 --reviews REVIEWS.jsonl --output data/review/deliberation-base-rated-v1
```

Use fresh output directories. Retain failed-run receipts and original data; no new result should overwrite the existing baselines.
