# Native reasoning and decoder diagnosis, 6 October 2026

Native thinking has not repaired the exposed source-fidelity failure. At a matched 2,048-token allowance, both base and saved adapter spend the entire generation on reasoning without delivering a public answer. The author-recommended sampling profile also exhausts that allowance. One inspected increase to 4,096 lets the base finish, with two omissions and a scope ambiguity; the adapter still produces no public answer. These are conditional development observations, not a persona-quality gain or an estimate of expected sampled performance.

This checkpoint adds **eight model generations and zero optimizer updates**. All eight stored outputs and all six complete reasoning traces were read. Three public answers were produced; five generations stop inside reasoning. Cumulative Aurora Qwen3.5 updates remain **414**, the selected adapter branch has **160**, reference Qwen2.5 remains **582**, and Germany/China is preserved separately.

## Controlled task and successive decisions

Reuse the exact raw WPS source task from the last checkpoint: complete France/UK post-vote statements in S/PV.8514, 23 April 2019, the hypothetical care-until-conviction proposal, and the original 24 national criteria plus four source guards and five synthesis checks. Both full national speeches, question and criteria were reread before launch. No teacher plan or new training target appears. This family is outside the selected adapter's fitting data but historically exposed in the project; it is not sealed OOD or native vote forecasting.

The first four calls compare base/adapter with native thinking off/on, greedy decoding, and the same total 2,048-token allowance. Messages and sources are identical; the native assistant suffix differs by two tokens. Base/adapter inputs are byte/token matched within each mode. Each one-answer run is inspected before another launch. The larger nonthinking allowance adds only the base's terminal EOS; the adapter's complete output IDs match its earlier 512-cap-protocol answer exactly. Those controls retain the original source annotations after a full reread, rather than being relabeled as fresh semantic review.

Both thinking calls cap inside repeated planning, memo revisions and word counting. We then read the [model card at the exact weight revision](https://huggingface.co/Qwen/Qwen3.5-4B/blob/851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a/README.md). For general thinking tasks it recommends temperature 1.0, top-p .95, top-k 20, min-p 0, presence penalty 1.5 and repetition penalty 1.0. It also recommends much larger output allowances for general usage. Its guidance is archived with an acquisition hash; these small calls do not reproduce its benchmark setup or 32K recommendation.

After the inspected greedy failures, one matched sampled base/adapter pair uses that profile at the same 2,048-token cap and fixed seed 42. Both still fail to reach public output. Only then is one larger, 4,096-token sampled pair frozen, retaining source, criteria, model, seed and profile. This changes only allowance from the sampled 2K protocol. It is not another fully matched thinking/off factorial or an allowance/seed sweep. Both 4K calls retain the 8,192 combined-length guard; model context and RoPE are unchanged.

## Public results and actual compute

| Protocol / weight | Reasoning tokens | Public tokens incl. EOS | Public source units | Public words | Generation seconds |
|---|---:|---:|---|---:|---:|
| Greedy 2K, base off |0|513|22/24, source failures|358|8.1|
| Greedy 2K, adapter off |0|396|17 met +3 unratable/24, source failures|312|9.8|
| Greedy 2K, base on |2048|0|No public answer|0|30.7|
| Greedy 2K, adapter on |2048|0|No public answer|0|48.5|
| Author profile 2K, base on |2048|0|No public answer|0|32.2|
| Author profile 2K, adapter on |2048|0|No public answer|0|49.7|
| Author profile 4K, base on |2237|389|21 met +1 unratable/24|270|41.2|
| Author profile 4K, adapter on |4096|0|No public answer|0|100.1|

The base's 4K answer uses 2,627 total generated tokens, including one reasoning boundary. It preserves care polarity, ongoing support and the conviction-gate objection, but omits France's explicit involuntary-pregnancy/termination right and the UK's remaining justice/accountability-work assessment. A collective clause about both delegations' body-autonomy/advocacy policies could aggregate separately attributed themes or pool France's explicit statement into UK; preserve it as unratable. References to existing health mandates versus the reaffirmed framework also need independent adjudication. No strict source pass occurs.

The adapter repeatedly refines, counts words and declares itself ready, but never emits the native public boundary before 4K. That is a delivery failure under this particular budget/seed, not evidence that every internal fact is wrong or that all larger budgets would fail. Internal drafts cannot count as public policy or persona outputs. Both sampled 4K runs reproduce their complete earlier 2K output IDs as exact prefixes, confirming the observed allowance correction without changing the sampled trajectory before the cutoff.

Across eight calls: **15,824 generated tokens and about 320.3 seconds of measured generation**. Hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**, with the original model/revision/runtime, BF16 text model and saved LoRA bytes verified. Generation time excludes loading and artifact work. Equal caps are not equal consumed compute; one fixed-seed draw does not establish an average decoder or weight ranking.

## Parsing, sampling and evidence

Native `<think>`/`</think>` IDs are verified from the installed tokenizer. The parser retains every generated ID, separates reasoning/public segments, and refuses to promote unfinished or malformed reasoning into an answer. Empty output is not treated as word-limit compliance; the earlier derived arithmetic flag is preserved and corrected without changing any output or semantic grade.

Transformers sampling uses an explicit generated-text-only presence processor, consistent with [vLLM's documented presence semantics](https://docs.vllm.ai/en/latest/api/vllm/sampling_params/). It subtracts the penalty once for each distinct generated token, excludes prompt tokens, and is applied before temperature/top-k/top-p in the pinned Transformers implementation. It is not a frequency penalty or a silently ignored configuration field. Effective sampling settings, processor invocation counts and seed reset immediately before generation are stored. This is a guarded Transformers port, not bitwise vLLM reproduction. Seven focused parser/presence software tests pass; they do not establish model quality.

Source spans/PDF hashes, archived runtime code, model/adapter hashes, mode-specific input tokens, raw outputs, reasoning boundary arithmetic and stored public grades replay. Same unblinded assistant authors/grader; independent source/rubric review remains pending. All eight model identities exited naturally, zero terminations and unfamiliar-process changes.

Evidence: `reports/native-reasoning-checkpoint-20261006.json`, `native-reasoning-20261006-v1.json`, `native-sampling-20261006-v1.json`, `native-sampling-20261006-v2.json`, and `native-reasoning-resource-status-20261006.json` under `reports/`. Frozen packs are `data/prepared/native-reasoning-20261006-v1`, `native-sampling-20261006-v1`, and `native-sampling-20261006-v2`; actual launches/transcripts/code/reviews are under `runs/aurora-native-*`. Primary guidance and the empty-output flag correction are retained separately under `runs/`.

## Next decision

Keep the working nonthinking locks and all model branches. More internal reasoning is not a demonstrated fix, and another full-memo fit is not selected. The next useful candidate is a compact **per-country source card** that separates priorities, source-specific details, real ongoing commitments, unknown future votes and hypothetical application before any joint synthesis. Compare nonthinking base/adapter with the same source guards and inspect source attribution and content selection first. This addresses the observed extraction/composition boundary; it does not assume a planner solves the prior checked-plan realization errors. No next pack, fit, queue or sweep is prepared. No private-value, validated country-persona, native decision-prediction or autonomous multi-agent gain is claimed.
