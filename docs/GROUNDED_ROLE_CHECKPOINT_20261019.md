# Grounded country roles: reading succeeds locally, prose remains unstable — 19 October 2026

Eleven actual Qwen3.5-4B generation records were inspected in full: ten public statements and one shared factual map. No optimization occurred. Supplying earlier national positions exposes a concrete attribution problem, and separating extraction from writing recovers the scored facts. It does **not** yet produce reliable complete statements or demonstrate a trained persona gain.

## Source and comparison

The new dossier uses the official [S/PV.9135 record](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9135&t=pdf), dated 22 September 2022: complete earlier India/UK statements, plus already audited UN/US excerpts from S/PV.9138 before either requested national statement on 27 September. The two requests receive the same dossier and differ only in requested delegation. The September 27 India/UK target speeches are not supplied. Public institutional statements are not population views or neutral verification of the speakers' claims.

All used earlier statements and current excerpts were hand-read. New PDF pages 14/15/19/20 were visually checked; the pinned extractor inventories all 30 body pages and preserves normalization/column coverage. Exact source offsets, PDF/text hashes and actual native prefix IDs are retained. The original documentary source and the October 17/18 packs remain unchanged.

Before any answers, nine material units per country and six whole-answer guards were frozen: agenda/legal basis, country-specific priorities/actions, proposal versus endorsement/vote, attribution, unsupported additions, time/authority, public output and a 240-word maximum. This is a **new source-conditioned application task**, not a regrade of the old authentic-speech reconstruction task. A plausible alternative diplomatic statement can fail this deliberately specified coverage task; it is not a comprehensive measure of diplomatic quality.

## Inspected stages

| Stage | Public answers | Material met / unmet / uncertain, of 18 | Provisional strict passes |
|---|---:|---:|---:|
| Base, full earlier speeches | 2 | 12 / 4 / 2 | 0/2 |
| Saved four-speech adapter, identical full dossier | 2 | 12 / 6 / 0 | 0/2 |
| Base, compact explicitly owned quote cards | 2 | 15 / 3 / 0 | 0/2 |
| Base writer, cards plus unedited model-extracted map | 2 | 18 / 0 / 0 | 1/2 |
| Base writer, same map plus smaller requested word target | 2 | 16 / 2 / 0 | 0/2 |

All ratings are by the same assistant who curated the sources. These are dependent adaptive development cases, not 90 independent observations or a statistically supported method ranking. Independent review remains pending. The one UK strict pass is provisional, including judgments about present-tense referendum paraphrase and an awkward self-reference to the UK. Preserve those qualifications; no stable gain is established by that single answer.

The full-dossier base UK answer calls India's global-South economic policy its own earlier position. India loses the specific food/fuel/fertilizer objects. The adapter does not repair this comparison: its Indian answer invents a confirmation of crimes by Ukrainian forces and new requests concerning the ICC, and its UK answer invents additional aid/report details. Those are model outputs, not historical facts endorsed here. The adapter was tested only on the full dossier; untested adapter cells must not be filled by inference.

Compact cards remove the clear UK appropriation of India's economic position. However, India merges humanitarian aid to Ukraine and economic support to neighbours into aid to neighbours; the UK omits its own withdrawal call. A hand-read preflight caught a UK quote beginning with “They” without its Charter antecedent. A separately frozen v2 restores the preceding sentences before any card model answers. The unrun v1 remains intact.

One base reader then produces a 576-token JSON map. It correctly separates the two Indian aid recipients and retains the UK withdrawal call, responsibility, nonrecognition, support, and both countries' unavailable draft endorsement/vote evidence. All 22 fields were read against the sources. The map is not exhaustive: it omits India's ICC nonmembership qualification and compresses the referendum start date. Those limitations are recorded, not silently repaired.

After that inspection, both writers receive the complete original cards plus the **exact unedited actual reader output**, with the original system/task/rubric. They preserve all 18 material units. The UK answer has 233 words and provisionally passes all guards. India has 251 words and adds an uncertain explanation for documentary absence, so it fails. The reader prompt supplies a field checklist and the pipeline adds generation/context/compute; this does not isolate a pure staging effect or demonstrate autonomous multi-agent improvement.

A final, separately frozen test adds only a request to aim for 170–190 words, retaining the same hard 240-word scoring maximum. India/UK shrink to 222/230 words. India's answer now claims the dossier confirms submission although the source only announces forthcoming submission, and adopts an unestablished Indian nonrecognition call. The UK again leaves withdrawal as a description of the US draft rather than its own call. The word-target test therefore regresses content; it is not the selected improvement.

## What this changes

The local reader can recover the needed country-owned facts. Even with those facts explicitly available in a map, prose generation can lose recipients, turn a proposal into a completed action, or drop an agent's own position. This makes **complete evidence-preserving realization** a better identified training target than another repetition of four raw speeches. It does not prove that source reading is solved generally, that more data cannot help, or that the adapter's architectural method is intrinsically unsuitable.

The next useful training candidate is a **fresh native-chat writer**, with a few complete, source-audited contrasting country targets on other episodes and a different episode frozen before fitting. Retain a strong base-plus-map comparison and explicit actor/recipient/proposal-stage controls. Inspect fitting recall and full output guards before expanding. The current Ukraine cases remain exposed development monitors. Do not continue the failed raw-speech branch or launch atomic tokens. No new training pack, fit, seed sweep or next operation is queued.

Two evaluation risks remain explicit. First, broad constructed reactions such as “we welcome” or a general legal inference do not always have a unique entailment grade; the reviews retain uncertainty and need adjudication. Second, strict source-preservation success would still not establish improved private national values, decision prediction, useful disagreement or collective reasoning. A later capability test must measure those separately.

## Execution and reproducibility

Model/revision/runtime are unchanged: Qwen/Qwen3.5-4B at `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, Torch 2.8.0+cu128, Transformers 5.17.0, PEFT 0.21.1, BF16/SDPA on **NVIDIA RTX PRO 6000 Blackwell Server Edition**. Each worker rehashes base weights and rechecks zero memory/utilization/no resident process before loading. The saved adapter's file hashes and trained tensor digest are checked before use. Within paired arms, full inputs and explicit greedy decoder are matched. The reader allows 3,072 generated tokens; all public writers allow 2,048, and none caps.

Four positively identified GPU workers exited normally. No unfamiliar process was altered. Identity receipts record host, UUID, PID, start time/ticks, command and run directory. Short resident sessions accepted only explicit operations after output inspection, avoiding one extra base reload in the weight comparison and another in the reader/writer stage. There is no throughput comparison or distributed/NCCL claim.

The [portable replay](../reports/grounded-role-replay-20261019-v1.json) checks all eleven actual native inputs/output tokens, frozen code/data hashes, source spans, unedited reader-to-writer transmission, review coverage/arithmetic and zero updates. This is engineering evidence, not independent semantic validation. [Resource exits](../reports/grounded-role-resource-exits-20261019-v1.json) and the [measured receipt](../reports/grounded-role-checkpoint-20261019-v1.json) provide the run inventory. All new evidence is bounded and committed directly in private Git; no new adapter or full archive is needed. The immutable v47 manifest and October 18 adapter release remain unchanged.

Cumulative Qwen3.5 updates remain **4,062**; scenario branch 128, earlier paired-Brazil branch 256, separate Qwen2.5 reference 582. Preserve Germany/China work, all original grades/failures and the unrun October 7 explicit seed-only control. The broader research goal remains active and unachieved.
