# Research diagnosis of the Qwen3 country-persona pilot

13 September 2026. Scope: job 910107, Qwen/Qwen3-8B revision `b968826d9c46dd6066d109eabc6255188de91218`, TRL 0.24.0, Transformers 4.57.6, BF16 LoRA, thinking disabled. This is a literature review combined with an audit of the actual experiment. No additional GPU job was launched for this research.

**Recommendation: keep Qwen3-8B and LoRA, diagnose generation first, and make the next data experiment teach country-specific use of evidence. Do not extend the current run to three epochs yet.** The evidence supports several testable mechanisms, not one proven root cause. Repetition and unsupported diplomatic claims require separate measurements and may require different fixes.

## 1. What we now know from this project

The original allocation cost 0.155 four-H100 node-hours. The adapter increased the sentence-repetition flag from 0 to 13 of 56 outputs; six flagged answers were Chinese and seven German. Seven used dated evidence and six were prompt-only. None of the shared-evidence English probes triggered this particular repetition rule. Both models passed the same seven of eight arithmetic controls. These are correlated diagnostic outputs, not 56 independent policy questions.

I audited **every one of the 500 training rows through the installed TRL tokenizer and collator**, using a tiny random Qwen3 on CPU without training. The check compared actual input IDs, every label boundary, the native empty thinking prefix, literal answer reconstruction, EOS supervision and maximum length. All passed. No target contained special-token text or the repeated-sentence pattern; all 500 normalized target answers were distinct. This rules out the tested mechanical failures and literal duplicate targets, not semantic duplication or deficient supervision. [Audit results](../reports/pilot-regression-data-audit.json); [reproduction script](../scripts/audit_pilot_regressions.py).

| Actual pilot property | China | Germany |
|---|---:|---:|
| Examples | 250 | 250 |
| Independent conference groups | 250 | 75 |
| Supervised tokens | 43,385 | 30,507 |
| Full sequence tokens | 355,886 | 1,217,540 |

China contributes 58.7% of supervised tokens. Germany consumes 77.4% of sequence-token volume because of long conference histories. Equal example counts did not equalize supervision or event diversity. The target median is 106 tokens; 85 of 500 targets exceed the evaluation cap of 256 tokens. All 16 German **baseline authentic-QA** outputs reached that cap. Truncation limits completeness comparisons; it does not explain repeated sentences that already occur within the cap.

The audit also exposes two instrumentation gaps:

- The evaluator replaces Qwen's default EOS list `[151645, 151643]` with the tokenizer's single EOS `151645`. The checkpoint's [generation configuration](https://huggingface.co/Qwen/Qwen3-8B/blob/b968826d9c46dd6066d109eabc6255188de91218/generation_config.json) is authoritative for that difference. It is a stopping-configuration discrepancy, **not an established cause** of these loops. Stored text omits special tokens, so a short replay retaining generated token IDs is needed.
- There is no base-model development loss, and the saved metadata does not contain the full effective generation configuration. Adapter dev loss 2.024 therefore cannot establish improvement. Future comparisons should record resolved settings, actual stop tokens/reasons and reference-normalized loss by country.

## 2. Ranked explanations and what would distinguish them

| Explanation | Evidence here | Assessment | Decisive next check |
|---|---|---|---|
| Fine-tuning made greedy decoding more susceptible to loops | Same decoder, 0 → 13 flags; targets do not contain those loops | Leading repetition hypothesis; not proven | Base and adapter under identical publisher-recommended sampling, then additional seeds |
| The data teach fluent institutional answers without enough evidence for the requested fact | Invented peace proposal, lost uncertainty, source copying that misses the question | Strong task-design concern; its contribution needs an ablation | Evidence-conditioned SFT versus matched examples without evidence |
| Ministry-to-UN and German-to-English transfer is unreliable | Training is spokesperson QA; English probes request national UN delegation behavior | Confirmed distribution change; effect size unknown | Matched role/language tasks and reviewed train-only UN examples |
| The update was too aggressive for this narrow data | New loops and changed answer behavior after 16 updates | Plausible, not established overfitting or catastrophic forgetting | Lower-LR comparison on the identical release; checkpoint generations and base dev loss |
| Stop handling inflates length or hides termination | EOS-list mismatch; decoded outputs omit special tokens | Concrete audit gap, causal role unknown | Capture raw generated IDs and compare stopping rules separately |
| Broken masking, accidental thinking supervision, or copied target loops | All 500 rows passed the exact audit | Less likely under the checked conditions | Retain checks; inspect saved/reloaded model equivalence if decoding still looks anomalous |

### Repetition: training loss and generation quality can diverge

Holtzman et al., **The Curious Case of Neural Text Degeneration** (ICLR 2020), demonstrate that maximization-based decoding can yield repetitive, low-quality continuations even from a useful language model; nucleus sampling changes this behavior. This motivates a decoding control, not a claim that sampling makes factual answers reliable. [Paper](https://arxiv.org/abs/1904.09751).

Xu et al., **Learning to Break the Loop** (NeurIPS 2022), show that sentence repetitions can reinforce their own continuation probability, even when the source corpus rarely repeats that way. That mechanism is consistent with our clean literal targets and looping generations. Their models/tasks differ from Qwen3 diplomatic QA, so the paper cannot diagnose our adapter by itself. [Paper](https://arxiv.org/abs/2206.02369).

Qwen recommends non-thinking sampling at temperature 0.7, top-p 0.8, top-k 20 and min-p 0. Its explicit warning against greedy decoding is in the **thinking-mode** guidance; it does not establish that our non-thinking greedy comparison was invalid. I chose greedy for reproducibility, but that alone was insufficient to assess practical generation quality. Use the recommended sampling configuration as the next controlled comparison. [Publisher guidance](https://huggingface.co/Qwen/Qwen3-8B#best-practices).

### Unsupported claims: authentic targets are necessary but insufficient

Gekhman et al., **Does Fine-Tuning LLMs on New Knowledge Encourage Hallucinations?** (EMNLP 2024), find that learning initially unknown facts through closed-book SFT can harm factual performance as those examples are fitted. Their controlled QA study motivates concern about unsupported factual fluency; it does **not** prove that our 16-step run acquired new knowledge or that SFT can never learn facts. [Paper, including setup and limitations](https://arxiv.org/html/2405.05904v2).

Our inputs often ask about particular meetings, schedules or evolving positions. A real spokesperson had information that a country tag, date and journalist question do not necessarily provide to the model. Training on the answer can teach confident institutional language without teaching when the fact is supported. Similarly, retrieving any earlier same-country text does not guarantee relevant evidence. The retrieved excerpts were frozen and temporally filtered, but relevance was not expert-adjudicated.

**RAFT** trains domain-specific question answering with relevant documents and distractors, teaching the model to select supporting evidence. It is a better conceptual match for documented, changing country positions than expecting a small adapter to store a complete foreign-policy state. Our proposed version adapts its evidence-selection principle; it would not reproduce RAFT's full recipe, including its reasoning targets. [Paper](https://arxiv.org/abs/2403.10131); [authors' explanation](https://gorilla.cs.berkeley.edu/blogs/9_raft.html).

### Hyperparameters and libraries: avoid blaming them without evidence

Qwen's own MS-SWIFT LoRA example uses BF16, all-linear targets and learning rate 1e-4. It also describes masking the empty thinking block for non-reasoning data. Thus our learning rate was a conventional starting value and our masking choice has direct publisher support; neither is guaranteed optimal for 500 spokesperson examples. Its example includes general instruction data, which differs from our narrow corpus. [Qwen training documentation](https://qwen.readthedocs.io/en/v3.0/training/ms_swift.html).

The older gradient-accumulation bug involved averaging batch losses rather than normalizing over supervised tokens. [Hugging Face explanation](https://huggingface.co/blog/gradient_accumulation). I inspected the pinned implementation: the constructed trainer accepts loss kwargs, enables cross-device token averaging, and follows the NLL path with a supervised-token denominator. Our measured target count equals the prepared count. This is evidence against simply assuming that historical bug applies; a numerical distributed-equivalence test has not been performed. [Transformers 4.57.6 source](https://github.com/huggingface/transformers/blob/v4.57.6/src/transformers/trainer.py); [TRL 0.24.0 source](https://github.com/huggingface/trl/blob/v0.24.0/trl/trainer/sft_trainer.py).

**LoRA Learns Less and Forgets Less** finds adaptation/forgetting tradeoffs that depend on method and task. LoRA is not immunity to regression, but this result also does not justify switching to full fine-tuning after one failed diagnostic. [Paper](https://arxiv.org/abs/2405.09673). Our eight arithmetic items cannot establish that broad capabilities were preserved or catastrophically forgotten.

## 3. The smallest informative experiment sequence

These are **proposals, not submitted jobs**. One node-hour means one hour of four H100 80GB GPUs. Estimates use the observed 9-minute pilot, approximately 57/97 seconds of maximum-rank baseline/adapter generation, and allowances for model loading and filesystem variability. They are not exact reservations or published benchmarks. Queue time and human review are excluded.

| Order | Experiment | What stays fixed | Evidence to inspect | Estimated node-hours |
|---|---|---|---|---:|
| D0 | Replay a few failures with raw token IDs and resolved generation settings; compare default EOS list with legacy single EOS if relevant | Checkpoints, prompts, greedy selection | Actual stop token, repeated sequence, prompt bytes; distinguish stopping from repetition | 0.03–0.10, preferably inside D1 allocation |
| D1 | Base vs adapter, Qwen non-thinking sampling, first seed; extend to three seeds only if informative | Same 56 cases, evidence, 256-token cap, EOS policy per comparison | Repetition, unsupported claims, correct attribution, length, variability | 0.08–0.20 for one seed; 0.15–0.35 total for three |
| D2 | Measure base and adapter dev loss on the same country splits; save generation diagnostics for selected failures | Tokenizer, labels, data, checkpoint | Country-specific NLL and behavior; never rank solely by loss | 0.05–0.15 |
| D3 | If needed, fresh LoRA at 2e-5 versus existing 1e-4, 500 examples and one epoch | Data, rank, batch size, seed, decoder | Whether gentler updates reduce loops without losing useful conditioning | 0.10–0.30 including small evaluation |
| D4 | Matched evidence-conditioned SFT ablation on reviewed 100 examples/country | Same source answers and country/event selection across arms | Supported claims, attribution, appropriate uncertainty, agreement controls | 0.20–0.50 for two short runs and diagnostics, after tokenizing the new release |

The 2e-5 value is **our proposed fivefold-lower sensitivity point**, not a paper-established optimum. D4 changes one training input condition by adding verified evidence; both arms use the same final answers and templates otherwise. Its longer inputs mean token cost cannot be assumed equal. Do not run this whole table automatically. Start with D0/D1 on one allocation capped at 30 minutes, stop when it finishes, and inspect.

If sampling removes loops but policy errors persist, that favors work on grounding over longer training. If adapter loops persist across seeds while the base remains clean, test D2/D3 and saved-model consistency. If both models fail equally on shared evidence, improve source selection and task design before attributing the failure to LoRA. A truncation check can later compare a larger cap on the same context-safe subset for both models; do not change cap, EOS and sampling together and call it a single-variable experiment.

## 4. Data changes I recommend preparing next

Prepare a new version; retain the original release for comparison. Start with **100 reviewed items per country**, covering multiple independent events. This size is a cheap design choice, not a literature-backed sufficiency threshold.

Each record should contain country, institution/role, as-of date, a specific question, short dated evidence with source IDs, and a source-supported answer. Keep acquisition provenance, support spans, review status and exclusions in the aligned manifest. Use the existing conversational prompt/completion format and non-thinking template. Completion-only supervision is the native TRL interface; provenance fields should not accidentally become answer text. [TRL format and loss documentation](https://huggingface.co/docs/trl/v0.24.0/en/sft_trainer).

Use separate, explicitly tagged tasks:

1. **Documented position:** answer a precise issue question from that country's dated source. Preserve justified agreement between countries; do not manufacture opposition.
2. **Attribution with distractors:** provide sources from both countries and require the chosen country's supported position. Shuffle evidence order. Use only claims whose attribution can actually be distinguished.
3. **Insufficient evidence:** when the packet cannot establish a requested fact or commitment, state that limitation. Do not turn absence in a packet into a claim that an event did not happen, and do not automatically replace every difficult answer with a refusal.
4. **Question-focused synthesis:** select the relevant position from a speech while omitting meeting greetings and unrelated agenda items. Extractive drafts may help, but consequential paraphrases need source review.

Gold evidence may contain the information needed to answer; that is the point of an open-book task. Do not paste an evaluation reference answer into the prompt and present it as independently retrieved evidence. Authentic, independently selected source documents can contain those same facts; label direct extraction separately from synthesis. Construct training evidence/targets only from train-assigned source families; keep all derivatives of one event together. Do not reuse the two development issues or their statements as training examples.

Retain ministry QA for that role. Add UN-delegation examples for UN claims rather than silently relabeling ministries. For common-English comparisons, prefer existing English UN mission statements; introduce human-reviewed translation as a separate treatment if needed. Expand evaluation beyond the existing two English issue groups before making country-general claims. Report uncertainty, factual support and correct attribution separately from stylistic distinctiveness.

## 5. When other methods become justified

**Repetition-specific objectives:** Unlikelihood training explicitly lowers probabilities of undesirable continuations; DITTO uses constructed repetition examples. These are plausible later interventions if loops survive decoding and ordinary SFT controls. Do not indiscriminately penalize repeated words: institutional names and policy terms legitimately recur. [Unlikelihood paper](https://arxiv.org/abs/1908.04319); [DITTO](https://arxiv.org/abs/2206.02369).

**DFT:** Dynamic Fine-Tuning reweights token updates and is already exposed as `loss_type="dft"` in our TRL release. Its reported gains on reasoning/code and other benchmarks make it a cheap future objective ablation, not a demonstrated remedy for country attribution or our repetitions. Keep it behind the data and decoding diagnostics. [Paper](https://arxiv.org/abs/2508.05629); [TRL documentation](https://huggingface.co/docs/trl/v0.24.0/en/sft_trainer).

**DPO:** Useful once we have reviewed preference pairs distinguishing a supported answer from an unsupported commitment or incorrectly attributed answer. DPO simplifies preference learning but does not supply truthful labels. A valid statement from the other country is a negative only when it is misattributed or otherwise wrong for the current task. [Paper](https://arxiv.org/abs/2305.18290).

Online RL and midtraining remain lower priorities: this experiment has not isolated a reward or knowledge-capacity problem that would justify either. The next success criterion is repeatable, evidence-supported behavior under controlled conditions, not a lower training loss or more obviously different national voices.
