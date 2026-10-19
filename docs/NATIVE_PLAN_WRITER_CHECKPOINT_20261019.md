# Native plan writer: source transfer improves, application remains incomplete

One fresh **32-update Qwen3.5-4B fit** gives a small source-realization gain: the two WPS statements excluded from fitting improve from **14/18 to 18/18 material units**, and from **0/2 to 2/2 provisional strict passes**, with identical source/plan inputs. France was outside the four new fitting targets. The harder application task still fails. Shorter, more faithful source summaries do not by themselves supply a missing operational recommendation or its practical cost.

This checkpoint has **14 actual generated statements** and 32 optimizer updates. Every complete output was read against its sources. Same-assistant curation, target authorship and grading remain limitations; no independent review, sealed OOD, national-value, decision-prediction or collective-benefit claim is established.

## What was trained

Four complete, source-audited UK/India targets cover two episodes: climate/security (S/PV.8923, 9 December 2021) and humanitarian sanctions (S/PV.9214, 9 December 2022). Each input contains both complete national statements, an attributed checked fact map, the dated institutional scene and a requested national delegation. Within each episode, only the requested country changes. The sanctions procedure quote supplies the actual adopted text and vote: India's abstention and the UK's favourable vote are facts, not predictions. National capacity is distinct from the Indian Council presidency.

Targets are 128–153 words and preserve actor, recipient, polarity, proposal/adoption/vote status and real ongoing commitments. The future-authority sentence must not erase known sponsorship, support, willingness or care commitments. These are assistant-authored paraphrases of public institutional evidence, not authentic speeches, population values or private national utilities. Positions are supplied, so the training question is realization and role binding.

Use the pinned native chat prefix, response-only causal CE, fresh rank-8/alpha-16 all-linear LoRA, learning rate5e-5, batch/accumulation1, no weight decay and clipping1. Eight presentations of each target yield32 updates,80,992 sequence tokens and5,856 supervised tokens. The failed128-update raw-transcript adapter was not continued. Input framing, targets and exposure all differ from that experiment; this is not an isolated native-format causal comparison.

The WPS episode (S/PV.8514, 23 April 2019) is wholly excluded from this fit. Its complete France/UK post-vote statements, all new map claims, every training target and complete prompts were hand-read. Used WPS PDF pages32/33/34 were visually inspected. Six complete speech spans and all point anchors replay. Inherited WPS bounds contain trailing whitespace, and `text_digest` hashes a canonical JSON string rather than raw UTF-8; both distinctions are explicitly preserved. No original PDF, extraction or manifest was rewritten.

## Inspected results

| Task | Base | Native32 adapter | Full strict passes |
|---|---|---|---|
| Four fitting statements | Not separately generated |35/35 material units; all24 guards |4/4 fitting only |
| Excluded WPS source statements |14/18 material |18/18 material; all12 guards |0/2 → **2/2**, provisional |
| Corrected WPS application |23/24 original units,1 uncertain |21/24 original units,3 unmet |0/2 →0/2 |
| Complete map coverage in that application |16/18 met,1 unmet,1 uncertain |17/18 met,1 unmet |Required in addition to original12 units |

Fitting outputs preserve all35 required meanings. Only the UK sanctions answer is string-identical to its target; the other three use small faithful paraphrases. No extra dose was needed to establish that fitting component. The fitted loss sequence decreases from1.43881 to0.07241; quality judgments come from complete answers, not loss alone.

On source-only transfer, France recovers the requested Secretary-General2021 report, the full continuing Council/other-UN/elsewhere care scope and the explicit future-vote boundary. The UK retains its own worldwide care/justice/civil-society content and the future boundary without adding France's specific framework/venue claims. Outputs are186/122 words, versus base232/201. France's bodily autonomy and involuntary-pregnancy termination right remain correctly scoped; UK's care is compatible with and essential to a survivor-centred approach. All positions were given in the input. This is a local benefit beyond the same base-plus-plan control, not evidence that the model inferred a government's hidden preferences.

### The application boundary and repaired control

The initial harder prompt paired “no analysis” with a request for explicitly labeled analytical recommendations. Both base outputs omitted the requested application. That scope conflict prevents interpreting those omissions as a reasoning deficit. Preserve the original20/24 units, all outputs and the unchanged rubric.

A separately locked control changes only that permission: requested hypothetical recommendations may appear in the public statement, with no separate reasoning trace. It retains the full sources/map, hypothetical P (care withheld until final conviction and comprehensive services omitted), the supplied repair/referral plan, the original12 national units and six guards. Before any corrected answer, an addendum also requires every supplied own-country map point. The original12-unit count is still reported separately; duplicate requirements are not independent observations. Assistant feasibility references at169/150 words demonstrate that the unchanged240-word maximum is feasible; they are neither model inputs nor training targets.

Explicit permission restores substantial application guidance in the base answers. France/UK reach271/266 words and both fail length. France loses some required map detail; its practical cost explanation is uncertain. The UK's final absence wording also needs adjudication.

The saved native32 adapter reduces length to186/170 words and improves map coverage, but **France omits the application entirely**, also dropping the German initiative from its required map point. The UK labels the immediate-care/no-conviction-gate and separate protected investigation/prosecution routes as exercise recommendations, but **omits the practical staffing/funding/coordination cost**. Correct recommendation phrases do not supply that missing explanation. Neither answer passes the full corrected task. The source-summary objective therefore improves one component while leaving an important instruction/application limitation.

## Engineering, errors and ownership

All32 actual input/mask/schedule/finite-gradient records replay. All496 LoRA tensors change and remain finite; frozen base parameter versions remain unchanged. Saved tensors match training state, and perturb/reload on the same base gives zero probe-logit difference. A separate fresh4B process loads the saved adapter with the exact trained tensor digest before the corrected comparison. This cold tensor check is not a separately measured cold-base probe-logit equivalence test.

Model/revision/runtime: Qwen/Qwen3.5-4B at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Torch2.8.0+cu128, Transformers5.17.0, PEFT0.21.1, BF16/SDPA. Hardware is **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Writers use explicit greedy nonthinking decoding,2,048 output tokens and8,192 combined context; no output caps occur.

Three positively identified GPU workers have exited. The first exited after an inspection-gate error; two exited normally. No unfamiliar process or job was altered. Host, UUID, PID, start ticks/time, command and run path are recorded. Initialization briefly waited on filesystem I/O; it was observed live and completed without a restart or intervention. No throughput/NCCL or disk-health claim follows.

One source-audit command initially confused raw versus canonical-string digests and trailing boundaries, preventing the base review from being saved. Sending the next operation prematurely correctly triggered a missing-review refusal. The two valid base answers remain; a separately locked resume token-replays them, with zero duplicate generations, after the original process is confirmed terminal. Launches subsequently use `pipefail` so `tee` cannot mask a Python failure. A separate tokenizer-only control initially reused an India/UK country guard for France/UK and was rejected before model allocation; the new locked entrypoint preserves the original code/manifest and requires the correct exact country set. No updates arose from these preparation failures.

See [actual replay](../reports/native-plan-writer-replay-20261019-v1.json), [measured receipt](../reports/native-plan-writer-checkpoint-20261019-v1.json), [source/data/code and original runtime evidence](../research/native-plan-writer-20261019-v1/README.md), [corrected control](../research/native-plan-writer-application-20261019-v1/README.md) and [resource exits](../reports/native-plan-writer-resource-exits-20261019-v1.json). Replays are engineering checks; semantic ratings remain same-assistant judgments. The source-only and application denominators must not be pooled into a claim of independent sample size.

## Decision and delivery

Retain native32 as a useful source-realization component and preserve its application failures. Do not increase dose to compensate for application behavior absent from all four targets. The next data candidate is **one complete, explicitly labeled application example on a fitting-family source**, keeping the four source targets. It should show the operational recommendation, its cost and its analytical authority alongside all dated national facts. Freeze a fresh source family/country control before another fit; keep WPS as an exposed development monitor and recheck source-only retention. No next target pack, fit, queue or sweep is prepared.

The bounded raw runtime metadata/output trees are copied byte-for-byte into Git, preserving the initial failure and exact reused baseline. The64,996,408-byte adapter is kept separately, with config and restore hashes in the [adapter manifest](../reports/native-plan-writer-adapter-manifest-20261019-v1.json). The [private native32 release](https://github.com/memo-ozdincer/country-persona/releases/tag/native-plan-writer-20261019-v1) now retains the exact adapter, config and manifest; all three remote byte sizes/SHA256 digests match the [verified delivery receipt](../reports/native-plan-writer-delivery-20261019-v1.json). The tag pins source commit `5307382994976d5c04815c24e96d498a466eef27`; later Git commits add delivery proofs. No full archive replaces immutable v47. Base weights, credentials and caches remain excluded.

Cumulative Qwen3.5 updates are **4,094**; this fresh native branch has32. Earlier raw-speech128, paired-Brazil256, separate Qwen2.5 reference582, Germany/China and all original releases/grades remain preserved. The old explicit seed-only control remains unrun. The broader research goal remains active; the source-only gain is not a replacement for dependable policy application, useful disagreement or collective analysis.
