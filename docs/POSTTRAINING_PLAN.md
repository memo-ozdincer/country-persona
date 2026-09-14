# Four-H100 proof-of-concept plan

The next-step recommendation is now the [regression research and diagnostic sequence](REGRESSION_RESEARCH.md), which incorporates the full 500-row TRL audit and primary literature. Its proposed runs have not been submitted.

Updated 13 September 2026. **The first Qwen3 pilot completed in 0.155 four-H100 node-hours (9 minutes 17 seconds).** Technical execution passed, but repetition and unsupported policy content prevent promotion. Read [the measured pilot review](../reports/trillium-910107-review.md) before selecting another experiment. The original 1–3-hour planning range below was conservative and is retained as historical planning context, not a measured runtime. No subsequent GPU run has been launched.

The user-selected model is pinned **Qwen/Qwen3-8B + BF16 LoRA, with `enable_thinking=False` throughout preparation, training and evaluation**. The publisher reports 8.2B parameters, a dense multilingual architecture and a supported hard non-thinking switch. [Model card](https://huggingface.co/Qwen/Qwen3-8B). The Trillium directory is named `Qwen3-8B-Instruct`, but its bytes match the official `Qwen/Qwen3-8B` revision. The previous Qwen2.5 job was cancelled before allocation and consumed zero node-hours. Every substantive decision and its evidence boundary is recorded in [DECISION_REGISTER.md](DECISION_REGISTER.md).

The [multilingual data expansion](DATA_EXPANSION_20260913.md) now supplies additional official evidence and a balanced 100-record content-review packet. It is not admitted to the existing training export. Review source attribution and build matched grounded evaluations before increasing training volume.

## What is prepared

The new release is `data/prepared/posttraining-qwen3-v1/`. It selects only authentic Foreign Ministry/Foreign Office responses, keeps each complete earlier dialogue and final answer, applies the pinned tokenizer, and excludes sequences above 8,192 tokens. The original, longer-context and earlier Qwen2.5 releases are retained. Each new row explicitly includes `chat_template_kwargs: {"enable_thinking": false}`. The native empty thinking block belongs to the masked prompt; only the literal final answer and its terminator are supervised. Nothing was translated or replaced by generated answers.

| Pool | Examples / training events | Input + answer tokens per epoch | Supervised answer tokens per epoch |
|---|---:|---:|---:|
| First pilot: 250 China + 250 Germany | 500 / 325 | 1,573,426 | 73,892 |
| Expanded balanced: 416 + 416 | 832 / 491 | 2,566,872 | 122,657 |
| Separate China adapter, same subset | 416 / 416 | 610,647 | 73,663 |
| Separate Germany adapter, same subset | 416 / 75 | 1,956,225 | 48,994 |
| Optional all-QA skew ablation | 8,095 / 881 | 14,674,558 | 1,412,944 |

One epoch of the first pilot is **16 optimizer steps**, with effective batch size 32. This is deliberately a learning-signal probe. Failure to improve after 16 steps does not establish that SFT cannot work. The optional three-epoch pilot gives 48 steps from the same base. Equal examples do not mean equal supervised tokens or independent events; the report exposes all three. Long German conference histories account for much of the compute.

There are 822 over-budget exclusions across train/dev/test. The eligible training pool contains 7,679 Chinese and 416 German examples. The first pilot avoids allowing the much larger Chinese pool to determine almost the entire experiment. Selection visits distinct conference groups before drawing additional answers from the same group, with deterministic seed 42.

Exports are explicitly marked `research_prepared`, with machine integrity checks and original source-use/review metadata. They are usable through the explicit research-release training option. This does **not** assert expert adjudication or grant copyright permissions. Existing manually admitted exports still work; old unprepared candidate files still fail training validation.

## Original compute planning envelope — see measured pilot review first

A **node-hour** below means one hour of **four H100 80GB GPUs**. Multiply by four to obtain GPU-hours. Two such nodes running for an hour cost two node-hours; parallelism reduces elapsed time, not total work. Estimates assume one full BF16 model replica per GPU, SDPA, activation checkpointing, microbatch one, and no packing. Prefer a node with fast GPU interconnects.

| Run | Estimated four-H100 node-hours, training + inline dev loss + load/save |
|---|---:|
| Three-step technical smoke | 0.17–0.41 |
| 500-example, one-epoch pilot | 0.28–0.96 |
| Optional 500-example, three-epoch run | 0.54–2.26 |
| 832-example, one-epoch balanced run | 0.35–1.30 |
| Two separate country adapters, combined | 0.50–1.60 |
| Optional 8,095-example skew ablation | 1.19–5.51 |

Allow **0.15–0.35 node-hours per checkpoint** for the 56-case first inspection pack and **0.25–0.75** for the complete development pack. The first round includes base and tuned generations, smoke training, and the one-epoch pilot: budget **1–3 node-hours total** with weights/dependencies staged. A cold environment or slow downloads add time. Human review and scheduler queue time are excluded; do not leave a paid allocation idle while reviewing.

The range uses an **unmeasured engineering envelope of 800–4,000 non-padding sequence tokens/second across the whole node**. This is not an H100 benchmark quoted from a paper. The formula is:

`node hours = (train sequence tokens × epochs + 0.5 × dev sequence tokens × evaluations) / measured effective node tokens per second / 3600 + load/save allowance`

The 0.5 forward-evaluation factor and 9–18-minute load/save allowance are planning assumptions. Completion masking reduces supervised targets, but the full context still consumes model compute. FLOP peak or trainable parameter count alone cannot predict this job's throughput. Actual DDP sampling, mixed sequence lengths, checkpointing and kernels affect runtime.

`run.json` now records processed sequence/target tokens, elapsed training plus inline evaluation time, maximum allocated memory and global throughput. Run `python scripts/estimate_compute.py --run runs/pilot-s42/run.json --output reports/calibrated_compute.json` after the first pilot. A calibration taken from the same data distribution is more useful than one taken only from unusually short or long examples. The estimator's calibrated throughput already includes inline eval; its additional eval allowance is conservative.

BF16 base weights alone are approximately 16.4 GB decimal per GPU. Optimizer states are for adapters, but activations, vocabulary logits, gradients, allocator reserve and kernels also consume memory. The first pilot measured 32.38 GiB peak allocated memory per GPU; larger batches and contexts still need separate measurement. Stop on OOM, inspect the longest batch, and shorten the context *selection* or use a verified memory optimization before reducing precision or scaling nodes. DDP does not pool four GPUs' memory into a 320GB model device.

## Milestones and inspection gates

Numeric thresholds below are **our provisional experiment gates**, not results or universally valid cutoffs from papers. Revise them before looking at a fresh final test set, not after seeing favorable results.

| Milestone | Concrete artifact | What we inspect | Decision |
|---|---|---|---|
| M0 — Freeze inputs (CPU, prepared here) | Tokenizer/model lock, release hashes, token counts, dev prompts and rubrics | Mask only the last answer; no target truncation; disjoint event groups; full history; country/language/length skew; sample 20 source/answer pairs per country | Fix any material attribution or segmentation error. Data corrections get a new release/version. |
| M1 — Baseline and technical smoke | Base answers for the 56 fixed cases; three-step adapter; measured throughput/memory | Finite loss and gradient norm; no prompt supervision; correct EOS; adapter reload; one actual maximum-length forward/backward check; 8 arithmetic/format controls | Stop on technical failure. Record cost before scaling. Smoke adapter is discarded. |
| M2 — First persona learning signal | One-epoch 500-example adapter and the exact same 56 responses | Review before/after outputs, separate prompt-only and evidence-assisted gains, invented commitments, source-supported positions, language and output-length changes | No unsupported new commitment in the small reviewed set; no more than one extra control failure. Improvement is descriptive here. If errors increase, fix data/objective; if merely unchanged, inspect underfitting. |
| M3 — Change one variable | Either three epochs on 500 examples **or** one epoch on 832; full dev evaluation | Country-specific dev loss, source-supported claim precision, 0–2 position fidelity, commitment/attribution error rates, paraphrase stability; checkpoint-by-checkpoint overfitting | Provisional useful gain: at least +0.10 fidelity on the normalized 0–1 scale in each country, with no >0.02 absolute increase in commitment errors. Use paired group intervals and report insufficient evidence; do not promote a style-only win. |
| M4 — Shared versus separate adapters (only if M3 is promising) | Shared 832-example run versus two adapters on exactly its CHN/DEU subsets | Same questions/evidence/decoding and data exposure; token/event budgets reported; country-specific fidelity and shared-position controls | Prefer the cheaper/simpler shared model unless separate adapters yield a repeatable benefit. Total exposed tokens match; per-country optimizer-update structure differs and is part of the treatment. |
| M5 — Robustness and frozen final test | Best strategy repeated with seeds 42, 43, 44; final test used once | Repeatability, topic/family holdouts, common-language policy distinctions, unchanged shared positions, unsupported claims and generic capability regressions | Promote only after improvements persist. The current German final test has only 9 event groups (45 QA): insufficient for a broad persona-fidelity claim. Expand independent evaluation events before such a claim. |

M3 costs the selected training row above plus a new development generation run. Do **one** M3 branch first; this is not a request to run the full grid. M4 adds roughly 0.5–1.6 node-hours for training plus its evaluations. A full initial sequence through one M3 branch should normally be planned as approximately **2–6 node-hours**, revised using the first measured run. Seed repeats are conditional and cost additional runs; they are not bundled invisibly into the first budget.

The maximum-length check in M1 is available through `scripts/gpu_length_probe.py`; it is separate from the randomly sampled technical smoke. Technical checks passing is not evidence that a country persona is learned.

## What “different personas” means operationally

The primary question is whether **country-conditioned, documented policy content** changes appropriately while irrelevant wording changes do not. Neither country-name classification nor distance between embeddings proves this.

The development pack has three layers:

1. **Authentic QA:** originally 100 questions per country, event-selected. The paired generation context budget retains 170 QA cases (340 prompts: plain and dated retrieval). This is a response-reconstruction evaluation. Chinese examples are English and German examples German; report them separately. Retrieval is frozen per case, strictly earlier than its date, and excludes its event group. Missing or irrelevant retrieval is recorded, not treated as authoritative evidence.
2. **Matched English:** two source-grounded issue pairs × two countries × two paraphrases × plain/shared-evidence conditions = 16 prompts. Both countries receive identical English question wording and, in the evidence condition, the identical packet containing both countries' sources. These are small development diagnostics, not 16 independent policy issues or an uncontaminated forecast. The shared-evidence task measures attribution/position selection from supplied sources.
3. **Eight neutral controls:** exact arithmetic/format checks with no persona prompt. These detect gross regression only; later promotion needs a broader independent general-capability evaluation.

The first inspection subset is **56 prompts**: 8 authentic questions per country in two conditions (32), all matched-English probes (16), and eight controls. The full development pack contains **364 prompts** after the paired context filter. Case hashes prevent a changed prompt/evidence packet from entering a before/after comparison unnoticed.

Concrete policy checks already prepared:

| Issue | What counts as source-supported behavior | What would be a failure |
|---|---|---|
| Ukraine, June 2026 sources | Both delegations can support peace talks. The Chinese source emphasizes legitimate security concerns and a regional security settlement; the German source explicitly attributes aggression to Russia and reaffirms Ukraine's sovereignty and recognized borders. | Inventing a pledge, assigning the other delegation's documented emphasis as an official commitment, or manufacturing disagreement simply because country tags differ. |
| Gaza humanitarian access | Both sources support humanitarian access and civilian protection. Chinese source includes support for UNRWA; the German source emphasizes children's protection. | Artificial polarization on aid access, invented financial pledges, or unsupported exclusive claims. |

The exact source IDs, dates and agent-drafted rubrics are in `configs/posttraining/probes.json`; full text remains in the local evaluation pack. They still warrant subject-matter review, particularly the German Gaza page's date/year inconsistency. Do not promote that example into a temporal-policy claim without resolving it.

At M3, add at least **20 independently reviewed issue/event groups**, including agreement controls and genuinely different documented positions, before interpreting common-language gains statistically. Twenty is an operational minimum for this pilot, not a power-analysis guarantee. Keep the existing two issues for debugging only. Add a verified policy-update test and irrelevant-pressure invariance test only when the correct responses are anchored in dated evidence; no invented private motives or negotiation rewards.

For formal assessment, two reviewers independently score a blinded, randomized sample, adjudicate disagreements, and record one final row per case/run. Position fidelity: 0 = contradictory/misattributed; 1 = partially supported or materially incomplete; 2 = supported and responsive. Separately count supported/checkable claims, unsupported commitments and attribution errors. Silence cannot earn full fidelity merely by making no checkable claims. `score_reviews.py` aggregates paired changes with equal event weights and event-group bootstrap intervals; it refuses empty reviews. It does not fabricate scores or use an unvalidated automatic political judge.

This follows behavioral invariance/directional testing from [CheckList](https://aclanthology.org/2020.acl-main.442/), adapts claim-level support from [FActScore](https://aclanthology.org/2023.emnlp-main.741/), and treats evaluation-unit and significance choices explicitly as recommended by [Dror et al.](https://aclanthology.org/P18-1128/). If an LLM judge is added later, audit its biases against blinded humans; [MT-Bench's judge study](https://arxiv.org/abs/2306.05685) is evidence against treating judge preferences as ground truth.

## When to change training strategy

- Prompt + evidence already matches SFT: invest in retrieval/source quality and reduce training spend.
- Fluent country-styled prose but wrong commitments: improve issue-specific grounded data; do not reward stronger stylistic differences.
- No learning signal and finite stable optimization: compare the three-epoch pilot before changing architecture. Inspect supervised-token scarcity and learning rate.
- Germany deteriorates while China improves: inspect per-country target-token shares and language effects; try reviewed English German mission instructions or a controlled language-matched subset before drawing a country conclusion.
- Unchanged answers across countries despite reliable contrasting evidence: add grounded same-question/different-country training examples from **train-only** sources; keep agreement controls.
- Position drift or invented commitments persists after SFT: collect evidence-adjudicated error pairs and consider DPO. A correct answer from the other country is not automatically a negative. [DPO](https://arxiv.org/abs/2305.18290).
- Missing domain knowledge after retrieval and SFT: consider a small continued-pretraining ablation. Online RL and multi-agent negotiation stay outside this first project; neither compute availability nor a desire for novelty establishes a suitable reward.
