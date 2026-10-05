# Open Character Training: a fresh persona reproduction

Started 4 October 2026; training and final verification completed 5 October UTC. The user asked us to reproduce a successful published persona fine-tuning experiment before choosing how to adapt it to the country project.

We reproduced one complete humorous-persona arm of [Open Character Training: Shaping the Persona of AI Assistants through Constitutional AI](https://arxiv.org/abs/2511.01689), using Qwen2.5-7B-Instruct, the authors' exact released raw training records, original OpenRLHF fork and original two-stage training recipe. The fresh fit acquires a persistent recognizable character: humor recognition rises from 10.4% to 58.6% normally and from 4.2% to 35.2% under the strongest neutrality instruction. It falls short of the authors' released sequential weights at 65.8% and 54.2%. This is a qualitative reproduction with disclosed operational differences, rather than exact numerical agreement or a replication of all eleven personas.

[Measured comparison](../reports/open-character-reproduction-20261004.json) · [Complete portable verification](../reports/open-character-reproduction-verification-20261004.json) · [Private run](../runs/open-character-humor-reproduction-20261004-v1/).

## What we actually ran

A fresh original DPO epoch made **212 successful optimizer updates** on 6,806 released preference pairs. We inspected its saved weights and all six fixed pilot outputs before proceeding. We then used the original merge CLI to merge that adapter into the BF16 base and fitted a fresh introspective SFT adapter for **370 successful updates**. The original loaders retain 11,868 of the 12,000 released introspection records. Total new reference-model optimization is **582 updates**; historical Aurora Qwen3.5 optimization remains separately recorded at 142, including its previously lost fit. Germany/China releases and every country comparison are preserved.

Both fits used one explicitly owned **NVIDIA RTX PRO 6000 Blackwell Server Edition**, the original FlashAttention 2 implementation, DeepSpeed FusedAdam and ZeRO stage 2. DPO training took 1,635.47 seconds with 45.46 GiB peak allocated memory; SFT took 2,039.54 seconds with 60.68 GiB. These are observed training measurements, not a cross-hardware performance comparison. All 392 LoRA tensors per saved adapter are finite and nonzero. Both 323,014,560-byte adapters are hashed and included in the private handoff.

We generated and classified **27,000 answers**: six arms, each on the original first 500 Pure-Dove questions with the default prompt and eight persona-removal suffixes. Another 24 pilot answers preceded the full comparison. The original constitution-prompted base is retained as a strong control. The weight-only arms use identical frozen prompts and per-question seeds; constitution prompting has a separately frozen system-message treatment on the same questions and suffixes.

## Results using the authors' released classifier

The metric below is the percentage of 500 answers classified as humor for each condition. It is class-specific recall on a humor-targeted arm. It is not the paper's eleven-persona macro F1.

| Prompt condition | Base | Constitution-prompted base | Authors' DPO | Authors' sequential DPO+SFT | Fresh DPO | Fresh sequential DPO+SFT |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Default | 10.4% | 47.0% | 55.6% | 65.8% | 47.8% | 58.6% |
| 0: ignore roleplay; true identity | 14.4% | 40.0% | 59.6% | 60.2% | 56.6% | 54.6% |
| 1: do not roleplay | 8.6% | 28.6% | 51.4% | 60.2% | 43.0% | 54.0% |
| 2: remove conversational style | 5.2% | 18.2% | 40.8% | 51.4% | 26.2% | 33.6% |
| 3: respond as feels most like you | 24.4% | 57.0% | 62.8% | 59.6% | 61.8% | 60.2% |
| 4: helpful, honest, harmless | 7.2% | 38.6% | 65.4% | 68.6% | 59.4% | 66.8% |
| 5: neutral and natural | 16.0% | 35.4% | 61.0% | 65.8% | 53.8% | 64.8% |
| 6: ignore earlier style instructions | 8.8% | 47.4% | 62.4% | 54.6% | 57.4% | 54.8% |
| 7: try very hard to answer neutrally | 4.2% | 6.2% | 43.0% | 54.2% | 27.8% | 35.2% |

The fresh complete recipe gains **48.2 percentage points over base** normally and **31.0 points under condition 7**. Against constitution prompting it gains 11.6 and 29.0 points. Fresh DPO alone almost ties prompting normally, 47.8% versus 47.0%, but retains considerably more humor under condition 7, 27.8% versus 6.2%. Persistent behavior under removal pressure is the strongest result beyond ordinary prompting.

Adding introspective SFT to fresh DPO improves default recognition by 10.8 points and condition 7 by 7.4 points. It improves six of nine conditions and regresses conditions 0, 3 and 6 by 2.0, 1.6 and 2.6 points. For the default condition, 119 paired questions gain a humor label and 65 lose one; for condition 7, 115 gain and 78 lose. These are classifier-label changes, not source-fidelity corrections. The same questions recur across conditions, so we make no independent-sample significance claim.

The fresh full model trails the authors' released sequential model by 7.2 points normally and 19.0 points under condition 7. We have not identified the cause of that gap. Runtime, unspecified author shuffle/order/seed details and other unreleased training provenance remain possible explanations that would require controlled comparisons.

Output-cap counts across each arm's 4,500 answers are base 208, prompted base 233, authors' DPO 47, authors' full 57, fresh DPO 69 and fresh full 74. The published classifier counts capped outputs; we preserve that rule and report the caps separately.

## What the complete inspected answers show

The assistant read 36 full stored outputs: eighteen original released-weight pilot answers, six fresh DPO pilot answers, six fixed constitution-prompted answers and six fixed fresh-full answers. One fresh DPO pilot reaches the output cap. Selection used question indices 0, 2 and 3 with default and condition 7, fixed before the first outputs; we did not select flattering examples after seeing classifier scores. These are unblinded same-assistant inspections, not independent semantic review. Automated classification covers every full-test answer; semantic inspection does not.

The fresh full group-development and underwriting answers maintain sustained jokes even under explicit neutrality instructions. This is visible behavioral change. The mathematical answers also contain serious errors: the default answer replaces the Fourier transform of a Dirac comb with a sinc function; the pressured answer confuses multiplication with convolution and reverses the aliasing inequality. The pressured group-development answer puts Adjourning before Performing. Earlier base, prompted and released-adapter examples also contain errors, so this small inspection cannot estimate a general capability loss caused by training.

[Fresh full inspection](../runs/open-character-humor-reproduction-20261004-v1/reproduction-full-inspection.json), [fresh DPO inspection](../runs/open-character-humor-reproduction-20261004-v1/reproduction-dpo-inspection.json), [original positive-control inspection](../runs/open-character-humor-reproduction-20261004-v1/pilot-inspection.json), [prompting inspection](../runs/open-character-humor-reproduction-20261004-v1/prompted-base-inspection.json).

## Exact data, original objectives and limits of fidelity

The [lock](../configs/posttraining/open-character-humor-20261004.json) pins the public repositories, revisions, original code and recipes. All four raw training JSONLs are **byte-identical to the publication-time November 2 release**, verified against both dataset revisions. Relevant training, preprocessing, generation and classifier scripts plus the OpenRLHF gitlink are unchanged between our retrieved checkout and that publication checkout. Base and saved author tokenizers produce identical IDs on all 4,500 evaluation prompts and 13,612 preference sequences.

DPO uses batch 32, microbatch one, one epoch, seed 123456, learning rate 5e-5, warmup 0.1, cosine scheduling with the original minimum ratio, Adam betas 0.9/0.98, clipping 1.0, zero weight decay, BF16 and rank-64/alpha-128 all-linear LoRA with zero dropout. Its objective is sigmoid DPO with beta 0.1, **chosen NLL coefficient 0.1** and the fork's **squared log-probability KL approximation coefficient 0.001** over chosen and rejected continuations. This differs from our recent pure-DPO country arm.

SFT uses a fresh rank-64/alpha-128 adapter over the BF16 merged DPO model, batch 32, microbatch two, one epoch and the same original optimization settings. Its 3,072-token context and default multiturn setting supervise **only the final assistant turn**. It is not all-turn SFT.

Original-loader measurements retain all 6,806 DPO pairs, with 2,569,514 chosen and 3,575,287 rejected sequence tokens and no sequences at the 1,024-token cap. SFT retains 11,868 rows after filtering 132 long prompts, with 9,890,307 sequence tokens and 5,082,182 supervised positions; 323 sequences reach the 3,072-token cap. The original epoch does not flush an incomplete accumulation tail: 22 DPO pairs and 28 retained SFT rows do not produce an additional optimizer update. We preserve that behavior rather than silently adding steps.

Raw introspection has 10,000 reflections, 1,000 free interactions and 1,000 leading interactions. We preserve the original Pandas processing, including its literal unformatted {NAME} placeholders. The final shuffled SFT file was not released, so we seed the otherwise unseeded shuffle. We reuse the authors' released introspection examples rather than regenerate conversations from our fresh DPO model; this preserves their training data.

The isolated runtime freezes 212 packages, including Python 3.12.3, Torch 2.8.0+cu128, Transformers 4.57.0, PEFT 0.17.1, DeepSpeed 0.18.0, vLLM 0.11.0 and FlashAttention 2.8.3. The existing Qwen3.5 runtime is unchanged. Private NVIDIA CUDA 12.8 and Ubuntu Python headers enable the original kernels without system installation. Hardware attention forward/backward and one synthetic scalar optimizer probe pass; the latter is excluded from research-model step counts.

The original Python training modules are unmodified. Observation-only wrappers count successful FusedAdam updates and saves. Operational differences are explicit single-process torchrun launching, scratch paths and local TensorBoard replacing W&B. Evaluation preserves temperature 0.7, top-p 0.95, repetition penalty 1.1, 1,024 output tokens and no prompt truncation. It uses paired per-question seeds/source order, eager vLLM execution and BF16 SDPA classifier inference on Blackwell. The paper does not provide a complete runtime lock, original generation seeds or final SFT order; bitwise reproduction is unavailable.

A released-weight composition difference is fully audited. The primary author control follows the original evaluation code: merge DPO into the BF16 base, then load the introspection adapter. The separately published combined adapter instead linearly blends each low-rank factor. All 392 tensors match that helper exactly. It introduces cross products and a quarter-strength SFT self term relative to sequential application. It is mathematically different, so substituting it would change the experiment. We preserve its acquisition and audit without using it as the primary full control.

The released classifier was trained on default generations for **these same first 500 Pure-Dove questions** across all persona methods and eleven personas. Default scores therefore depend on the evaluator's training questions. Removal variants reproduce the paper's robustness comparison, but remain a measure of stylistic resemblance. Zero exact-text overlap between evaluation questions and DPO user prompts does not establish semantic or pretraining independence.

## What this changes about our project

| Dimension | Published reference arm | Recent country application/objective trials |
| --- | --- | --- |
| Target | Persistent humorous assistant character | Dated country–institution–role behavior and source-faithful policy application |
| Model and trainer | Qwen2.5-7B; original OpenRLHF fork | Qwen3.5-4B; separately pinned project/TRL pipeline |
| Training data | 6,806 preferences plus 11,868 retained introspection records | Twenty preferred targets in the latest comparison |
| Optimization | 212 DPO updates plus 370 SFT updates, batch 32 | Twenty-step fits per objective, substantially smaller exposure |
| Adapter | Rank 64 at each stage | Rank 8 |
| Preference objective | DPO plus chosen NLL and approximate KL | Latest completed country arm uses pure DPO |
| Main comparison | Recognizable character and resistance to removal instructions | Coverage, speaker attribution, invented commitments and application boundaries |

**The reproduction supplies a meaningful positive control.** Training can change persistent behavior on our Blackwell hardware. It also shows that the recent twenty-step pure-DPO country comparison was a small distinct hypothesis test, rather than a faithful implementation of the paper's pipeline. These findings support studying adequate example diversity and the full objective; they do not isolate data scale, capacity, model, dose or objective as the cause of our country null results. The older, larger Germany/China adapter also regressed and remains part of that diagnosis.

**The behavioral target differs substantially.** Humor can be recognized from repeated stylistic signals. A national representative must preserve speaker-specific facts, apply material constraints, reject unsupported pressure and revise when valid dated evidence changes. Our checked bullet-plan intervention isolates realization; raw-source application tests another part of that chain. This reproduction does not evaluate either task. A successful persistent voice can coexist with wrong facts, as the inspected examples demonstrate.

**Persistence must be conditional in the country project.** Resisting a tone-removal instruction is the paper's desired persona behavior. Institutional agents should retain supported priorities under content-free pressure and change them under legitimate new evidence. Treating constitutional slogans or synthetic introspection as a government's private beliefs would blur our country–institution–role–date target. The [goal-gap audit](PERSONA_GOAL_GAP_RESEARCH_20261001.md) and [research anchor](RESEARCH_ANCHOR.md) remain relevant: behavioral choices, legitimate updates and interaction benefit require separate evidence.

The introspection contrast adds a full epoch and many more records. It does not isolate self-reflection as the active mechanism without a matched non-introspective data/dose control. Similarly, this OpenRLHF reproduction does not validate the exact Qwen3.5/TRL implementation used in our country trials.

## Decision after inspecting the result

Preserve the successful reference arm and its strong prompting control. The most informative next technical candidate is to port a published persona positive control into our Qwen3.5 pipeline with its own versioned lock, then determine whether it learns the same recognizable behavior. That would help separate pipeline/model transfer issues from country supervision and evaluation issues. It is a recommendation, not a prepared run or experiment queue.

For the country task, first adjudicate the three unresolved source/rubric units and independently review where feasible. Retain base plus checked-plan controls, freeze separate event families, and require both unsupported-pressure resistance and legitimate-update acceptance. The deferred matched DPO+chosen-NLL comparison remains a narrow objective candidate. The reproduction does not justify a sweep, rigid national identities or optimizing for disagreement.

## Reproducible evidence and resource status

The private run contains exact raw/compiled inputs, frozen prompted/unprompted test packs, complete transcripts and classifier logits, measured/verification receipts, both saved adapters, original source/PDF archives, public acquisition hashes and preserved failures. The complete portable replay rehashes eight frozen inputs, 213 reference files and all 22 saved adapter files; checks 582 observed updates, matched prompt treatments and all 27,000 stored classifier decisions/probabilities. This verifies recorded artifacts and arithmetic rather than independently regrading semantics.

All 23 owned launch records have exited. Final PID/start-tick checks show no project process remains; the selected GPUs are free. Both unfamiliar GPU processes remain untouched. No account-wide cleanup or further fit was performed. Multi-GPU/NCCL and independent semantic review remain pending.

Base weights, author adapters, merged full models, headers and the isolated runtime stay on scratch outside the checkout. Pinned repositories/hashes enable reacquisition; credentials stay outside the repository and handoff. Both newly trained LoRA adapters and all ignored evidence are included in the new private handoff, alongside the preserved country artifacts. Code synchronization and artifact archival are separate. The first snapshot attempt stopped on a generated Python parser's quoted private-key header, which contains no key body. A bounded literal-header check resolves that false positive while retaining rejection of key blocks; raw outputs and the failed snapshot remain preserved.

The fresh handoff release is [aurora-handoff-20261004-v10](https://github.com/memo-ozdincer/country-persona/releases/tag/aurora-handoff-20261004-v10). Consult the scratch-root CURRENT_HANDOFF.json for verified archive hashes, snapshot identity and remote digest status.
