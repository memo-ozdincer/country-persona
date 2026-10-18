# Authentic delegation SFT: fitting succeeds, transfer fails — 18 October 2026

One fresh Qwen3.5-4B fit reproduces **all four complete authentic training speeches exactly**, but the two unchanged Ukraine development cases do not improve. They generate unsupported policy/event claims; the raw UK answer even continues into a fabricated US speech. Under both raw and corrected native-chat inputs, reference-speech likelihood is substantially worse after fitting. **Do not scale this four-speech branch or start the atomic-token arm.** This checkpoint establishes working optimization and overfitting, not a country-persona, diplomatic-reasoning or multi-agent gain.

Fourteen saved outputs were hand-read in full, in separately inspected groups: two raw base, two native base, two corrected-native base, four fitting replies, two raw adapter development replies, then two corrected-native adapter replies. Only one fit, 128 actual updates, occurred. Cumulative Qwen3.5 updates are 4,062; this fresh branch has 128. The earlier paired-Brazil branch remains 256 and the separate Qwen2.5 reference remains 582. Earlier experiments, original scores, Germany/China work and the unrun explicit seed-only control are preserved.

## Measured results

The original October 17 material units and guards remain unchanged. Scores below are by the same assistant who curated the sources; independent semantic review remains pending. Uncertain is not a pass.

| Arm | Answers | Material units: met / unmet / uncertain | Strict passes |
|---|---:|---:|---:|
| Base, raw sequence | 2 | 0 / 8 / 0 | 0/2 |
| Base, original native wrapper | 2 | 2 / 6 / 0 | 0/2 |
| Base, corrected native boundaries | 2 | 2 / 5 / 1 | 0/2 |
| Adapter, fitting speeches | 4 | 20 / 0 / 0 | **4/4** |
| Adapter, raw Ukraine development | 2 | 0 / 8 / 0 | 0/2 |
| Adapter, corrected-native Ukraine | 2 | 1 / 7 / 0 | 0/2 |

The fitting results are byte-identical to the normalized authentic targets, including qualifiers, numbers and EOS. Generated lengths are 260/574/1,744/570 tokens, none capped. Full source fidelity on these fitting speeches is a real component result; it is memorization on four examples, not evidence of transfer. The long Indian climate speech preserves both its climate commitments and opposition to a separate Council climate track, rather than flattening it into a generic climate statement.

The raw base India answer copies Ireland, enters a visible thought loop and hits 2,048 tokens. Its UK counterpart copies Ghana, repeats itself and ends mid-sentence. Native chat makes the base produce readable single speeches, but it omits the referendum agenda and changes national positions or adds unsupported claims.

The raw adapter India answer invents an “Initiative for Responsible Nation-States,” observer-status plans and export restrictions. Its UK answer invents meetings and attacks, then emits a USA header with the UK representative's name and a further US speech. These are actual model outputs, not historical claims endorsed by this report. The corrected-native adapter still invents Indian military/justice actions and UK diplomacy tracks. Source/role errors therefore persist beyond the bare serializer. Native formatting does fix some surface behavior; that does not fix the factual or institutional failures.

Matched mean reference-token negative log likelihood, including EOS, worsens in both formats. Lower is better; these are likelihood diagnostics, not persona or decision-quality scores:

| Case | Raw base → adapter | Corrected-native base → adapter |
|---|---:|---:|
| India, Ukraine | 2.218 → 4.600 | 2.149 → 4.862 |
| UK, Ukraine | 2.616 → 4.756 | 2.408 → 4.833 |

Actual prefix IDs match within each comparison; source, decoder, pinned base revision, runtime and hardware type are fixed. The raw Indian correct-role likelihood advantage also changes from +0.034 to −0.227 nats/token; the UK advantage increases, despite its fabricated extra role. Role-likelihood margins alone do not certify country behavior.

## What the small stages revealed

The original native wrapper placed two literal `<|im_end|>` record delimiters inside its user content. That produces three native end tokens rather than one. The corrected control changes only those documentary delimiters to printable recorded-turn boundaries, preserves the documentary text and target bytes, verifies the native target boundary, and generates two separately preserved answers. This repairs protocol validity without creating a source-reconstruction success. The original outputs, initial replan review and later fit decision remain available; no failed baseline was overwritten.

The [observability audit](../research/scenario-checkpoint-20261018-v1/criterion-observability.json) identifies another limitation: India's actual aid/global-South details and the US/Albania draft sponsorship are absent from the supplied history windows. Their exact recovery needs more earlier evidence or historical knowledge. Missing them is not by itself proof of poor country beliefs or diplomatic reasoning. Conversely, the referendum topic is explicitly present in the UK input and is repeatedly ignored. Unsupported organizations, military actions and speaker changes are failures even after allowing for missing historical details.

Ukraine is excluded from this fit but has historical project exposure and possible pretraining exposure. The December 2022 sanctions fitting source is later than the September 2022 Ukraine episode. This is neither a sealed OOD test nor a forward-time forecast. The strict rubric measures source reconstruction and attribution, not every diplomatically defensible alternative speech or a government's private beliefs. Source fidelity is also distinct from the neutral truth of a delegate's claims.

## Execution and preservation

The [October 17 data/method lock](SCENARIO_ROLE_SFT_READINESS_20261017.md) stays unchanged: four genuine targets, readable markers, rank-8/alpha-16 all-linear LoRA, response-only causal CE, batch/accumulation 1, 5e-5 AdamW, no weight decay, clipping 1, 32 presentations per target. Actual exposure is 444,032 sequence and 100,736 supervised tokens. All 128 actual input/mask/schedule/finite-gradient records replay; all 496 adapter tensors change while frozen base parameter versions remain unchanged.

The saved adapter is 64,996,408 bytes. Saved tensors match training state; perturb/reload on the same base gives zero probe-logit difference. A separate fresh 4B base/adapter process also reproduces the trained adapter tensor digest exactly before the final native comparison. These are separate serialization checks; the latter is not a separately measured cold-base logit-equivalence test.

Hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Every GPU worker starts after zero-memory/zero-utilisation/no-resident-process checks and records host, UUID, PID, start ticks/time, command and run path. An unfamiliar process joined the training GPU after allocation and later left naturally; it was never altered. No throughput comparison is claimed under that shared occupancy. The trained model was retained only for manually requested fitting/development evaluations, saving two multi-GB MFS reloads; no evaluation was queued. All five positively identified GPU workers exited normally. No account-wide cleanup, scheduler action, additional fit or token arm occurred.

The [measured receipt](../reports/scenario-role-checkpoint-20261018-v1.json), [complete outputs and reviews](../research/scenario-checkpoint-20261018-v1/README.md), and [portable replay](../research/scenario-checkpoint-20261018-v1/final-replay.json) distinguish actual model results from decoder/provenance/arithmetic checks. All 35 regression checks pass again (32 pytest and three pinned-runtime unittest checks), separately from the production-model evidence. Executed orchestration source is captured and hashed; parent code/data/weights/runtime remain pinned. The current private GitHub branches contain bounded evidence. The [private checkpoint release](https://github.com/memo-ozdincer/country-persona/releases/tag/scenario-role-checkpoint-20261018-v1) backs up 51 new run files, including the adapter, in a 60,248,805-byte archive plus manifest and verification receipt; all three remote sizes/SHA256 digests match. See the [delivery receipt](../reports/scenario-checkpoint-delivery-20261018-v1.json) for restore instructions. Base weights, credentials and caches remain excluded. The immutable v47 snapshot is unchanged; no replacement full archive is needed.

## Next decision

Keep this failed-transfer adapter and all original evidence; do not select it as a general upgrade. The next useful experiment should first make the task identifiable: a native-chat continuation with a concise, fully source-bound **pre-target** meeting state and separately attributed earlier country evidence. Hold that information fixed across requested-role controls. Compare base and the saved adapter on a small frozen pair before any more optimization. This can test context use and self/other attribution without expecting the model to reconstruct unavailable historical facts.

If another fit becomes warranted, use the model's native chat frame and source-faithful role/topic contrasts, with strong base-plus-evidence controls and an observable held episode. Memorizing four utterances is not a sufficient objective for the larger persona/agent goal. No next pack, training run, special-token arm or seed sweep is prepared as a queue.
