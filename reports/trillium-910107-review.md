# Qwen3 pilot: technically complete, do not promote yet

Job 910107 completed on Trillium at 01:51:28 Toronto time on 13 September 2026. The entire allocation lasted **557 seconds: 0.155 hours of one four-H100 node**, including the length probe, technical smoke, baseline generation, 500-example one-epoch LoRA run, adapted generation and reports. This is 0.619 individual H100 GPU-hours. The original 1–3 node-hour estimate was substantially too conservative for this cached environment.

The pilot adapter remains at `/scratch/memoozd/persona/runs/trillium-910107-pilot`. No further GPU job has been launched. This report contains preliminary assistant inspection of diagnostic outputs, not human-expert validation or a national-persona benchmark result.

| Check | Base | LoRA |
|---|---:|---:|
| Completed matched prompts | 56 | 56 |
| Arithmetic/format controls correct | 7/8 | 7/8 |
| Outputs containing generated thinking markers | 0 | 0 |
| Outputs reaching the 256-token cap | 18 | 14 |
| Outputs flagged for repeated sentences | 0 | 13 |

All eight control answers were unchanged, including the incorrect answer 29 to 12 + 13 + 14. All 48 persona outputs changed. Changed text and fewer capped responses do not establish better fidelity. The repetition flag counts an exact normalized sentence of at least six words occurring at least three times; this is a transparent debugging heuristic, not a validated quality score. Case IDs and prediction hashes are in [the machine-readable summary](trillium-910107-summary.json).

The training and inline development evaluation took 156.35 seconds. Measured effective throughput was 10,063 non-padding sequence tokens/second across the node; peak allocated training memory was 32.38 GiB per GPU. All 1,573,426 nominal training tokens and 73,892 supervised targets were counted. The 8,182-token length probe also passed. Development loss was 2.024, but no base-model development loss was measured, so this number is not a before/after gain. Falling training loss does not resolve the generation regressions.

Concrete findings from the paired outputs and supplied references:

- **Repetition regression:** On the Chinese UN Charter question (`mfa:t20260626_11953253:qa:9:prompt_only`), the adapter repeats “The UN Charter is the cornerstone of the international order” until the output limit. The base gives a varied, though truncated, response. LoRA also loops on the German Gaza prompt and several authentic German questions.
- **Unsupported specificity:** For Germany's Ukraine paraphrase without evidence (`probe:ukraine:DEU:paraphrase:prompt_only`), the adapter introduces a three-phase peace proposal. That proposal is absent from the supplied German reference. Treat this as unsupported by this evaluation's evidence, not proof that no such proposal could exist anywhere.
- **Country attribution remains unreliable:** In Germany's Ukraine question with shared evidence, the adapter borrows the Chinese source's common/comprehensive/cooperative/sustainable security formulation and presents it as German guidance. It still condemns Russian aggression, so the answer contains a mixture rather than a complete country swap. Some blending was already present in base outputs; another paraphrase improves explicit German attribution. There is no consistent gain across paraphrases.
- **Source copying can miss the question:** For China's Gaza question with evidence, the adapter reproduces meeting acknowledgments and ceasefire background while omitting the requested access details and UNRWA emphasis. The base covers those points. This is a response-selection failure even though much of the copied content is source-supported.

**Milestone decision:** M1 technical execution passed. M2 does not justify promotion to longer training or a larger data run. Two English issue groups and a tiny arithmetic set cannot establish general persona fidelity; the current output cap also limits interpretation, especially for German answers.

**Next recommended experiment, not launched:** First compare these same base and adapter checkpoints using the publisher's non-thinking sampling settings (temperature 0.7, top-p 0.8, top-k 20, min-p 0), with recorded per-case seeds and otherwise identical prompts. [Qwen3 model card](https://huggingface.co/Qwen/Qwen3-8B#best-practices). This isolates decoding sensitivity without retraining; improvement under sampling would not by itself fix unsupported policy claims. Inspect truncation separately before changing the output cap. Budget a conservative 0.1–0.3 four-H100 node-hours for a bounded inference-only comparison in the same staged environment; this is a planning allowance, not another measured run.

In parallel, review a small train-only set for country attribution, appropriate uncertainty, and question/answer alignment. The first training data are ministry press answers, whereas the English probes ask for UN-delegation responses; that role and language transfer remains unproven. Improve reviewed supervision and source selection before selecting another training setting. Lower learning rate or different data mixtures are hypotheses for controlled follow-ups, not established fixes.

Full generated comparisons: [before/after answer sheet](trillium-910107-before-after.md). The original outputs, measured run metadata and source references remain available for independent review.
