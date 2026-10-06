# Ordinary points expose a compression gap

Three matched, no-fit answers on exposed Brazil/ICC show that the plan-input adapter can preserve all fourteen supplied source/application meanings in readable English, but **does not compress**. A 378-word plan becomes a 367-word answer that exactly flattens its bullets into the three requested paragraphs. The base model omits most named source compounds; the raw-input adapter stays within the word limit but still omits facts. No arm passes the complete realization task.

This changes the next training question. The eight point-input positives paired sentence-by-sentence bullet plans with almost identical prose targets. They taught a copying transformation. Adding more updates to that recipe does not teach the required long-plan-to-short-answer transformation. The next candidate is compression-specific supervision with longer, ordinary English plans paired with the same checked short preferred answers, inspected before any fit.

## Frozen diagnostic

Only the representation of the existing complete Brazilian ICC plan changes. The original national speech, current hypothetical Z, public role metadata, system, realization contract, source/app/universal criterion meanings and model protocol remain byte-identical. Reverse replacement of the new plan with the old shorthand reconstructs the original request exactly. Expansion changes spelling, grammar, abbreviation rendering and token/word length; semantic equivalence is a same-assistant hand assessment, not a programmatic proof or an independently adjudicated claim.

The plan grows from 172 shorthand whitespace words to **378 ordinary words**. The full request is **1,912 native input tokens**. It remains given source positions and analytical decisions, not native government decision prediction. This is an exposed development case: the original ICC family and all three models' shorthand outputs were already inspected. No fresh OOD or confirmation claim is made.

The first draft was rejected before calls: “expenses fall on” might imply an existing allocation rather than Brazil's request, and “ensures accountability” could overstate a Court outcome rather than its purpose. Version 2 retains the original request and Court purpose. Version 1, its code/configs and a superseded-before-calls receipt are preserved without a positive manual-inspection authorization. No model calls, GPU launches or updates came from that correction.

The full serialized ordinary plan was read against the whole original shorthand and complete Brazilian national speech. All fourteen source/application meanings and four universal checks were inspected. Original primary PDF/source-boundary evidence remains unchanged; no new PDF viewing is claimed. Funding is Brazil's position/request, not an actual new UN appropriation; presentation of a prosecution case is not a conviction; complementarity preserves national primacy and ICC unable/unwilling conditions; actual security conditions do not become a universal victory gate; analytical witness protection does not become France's explicit clause attributed to Brazil.

Four supplementary presentation checks were frozen **before** calls: ordinary word separation, only the requested three sections, no repeated whole source in place of task execution, and at most 300 ordinary whitespace words with an uncapped answer. They supplement the unchanged factual rubric. They do not replace any older primitive grade.

## Actual answers

| Same ordinary-plan input | Content units | Words | Presentation | Usable full-task pass |
|---|---:|---:|---|---|
| Base Qwen3.5-4B | 6 met + 1 uncertain / 14 | 347 | Readable; five sections; over limit | No |
| Saved raw8/256 adapter | 10 met + 1 uncertain / 14 | 258 | Readable; three sections; within limit | No |
| Saved plan8/256 adapter | 14/14 | 367 | Readable; three sections; over limit | No |

All three full outputs are uncapped and were hand-read before the next dependent launch. All four universal checks are provisionally met in each answer; omissions, ambiguity and presentation failures remain separate. The annotator is the same unblinded assistant who curated the plans and targets. These are dependent development annotations, not independent ratings or statistical samples.

Base retains the war/security/conditional-steps source compound, but misses the other seven complete source compounds. It does provide useful remote-evidence/funding directions, a time/resource cost and an authority boundary. Its other-case and witness-assistance comparisons are partly implicit, recorded as uncertain. It adds separate Operational steps and Competing cost sections to the three requested sections.

Raw8 retains four complete source compounds. It omits the stalled-road-map qualifier, the named Abd-Al-Rahman trial/family-suffering compound and part of the founding/permanent-treaty/international-support compound. It recovers almost all humanitarian/Juba detail, but “the binding 2020 Juba Agreement” does not explicitly preserve “all signatories”; whether ordinary binding-agreement wording entails the full intended actor scope remains uncertain. Its six application units are met, with an isolated awkward formulation noted. Missing facts prevent a full-task pass despite good presentation.

Plan8 retains all eight source and six application meanings, including the enabling-security, unable/unwilling, trial/presentation, funding, all-case-support and authority distinctions. Its wording is normally spaced but still telegraphic in places. A direct reconstruction proves the answer is exactly the expanded plan with bullet markers removed and headings changed to Documented position, Analytical application and Authority. It shortens only the structural markers: **no substantive compression**. The 300-word requirement fails.

Older shorthand grades remain unchanged: base 6 met + 1 uncertain / 14 at 324 words, raw8 10/14 at 190 words, and plan8 14/14 at 161 words. The earlier narrow plan8 strict pass used a whitespace count on fused shorthand; it did not establish ordinary-prose compression. The new diagnostic resolves that limitation without retrospectively changing its rubric or grades.

## Native and portable verification

The three calls use the unchanged owned one-case runner and native generation helper, the pinned Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, exact runtime pins, BF16 SDPA, thinking disabled, greedy 2,048-token generation and the 8,192-token total limit. All use **NVIDIA RTX PRO 6000 Blackwell Server Edition**, GPU UUID `GPU-e485015c-8b0a-afe0-666e-86eec344e76f`.

The checkpoint adds **three model outputs and zero optimizer updates**. Generation totals 1,305 tokens and 29.83 seconds, excluding loading/verification overhead. Cumulative recorded Qwen3.5 updates remain **2,270**; the separate Qwen2.5 reproduction remains **582**. All three positively recorded project GPU identities exited; unfamiliar processes were untouched.

Portable replay verifies the old/new frozen pack hashes, request reverse replacement, source identity, complete meaning audit, pre-call presentation rubric, native input/output bytes, matching protocols, exact saved-adapter hashes, inspection chain, current/old stored-review arithmetic, word counts and positive exit identities. It does not independently adjudicate the annotations. Original source, criteria, outputs, grades, adapters and the Germany/China work are preserved.

## Artifacts and next decision

- Draft/corrected packs: `data/prepared/ordinary-points-20261006-v1`, `data/prepared/ordinary-points-20261006-v2`.
- Hand source audit: `reports/ordinary-points-source-audit-20261006-v2.json`.
- Pre-call draft correction: `reports/ordinary-points-draft-audit-20261006-v1.json`.
- Actual runs: `runs/aurora-ordinary-points-{base,raw8,plan8}-20261006-v2`.
- Evidence/replay: `reports/ordinary-points-checkpoint-20261006-v2.json`, `scripts/verify_ordinary_points_checkpoint.py`.

The next candidate keeps the **same eight short preferred texts/native chosen tokens, fresh initialization and 256-update budget**, while pairing them with longer ordinary English teacher plans. Prefer actual LLM-expanded plans that preserve exactly the existing source/decision meanings; hand-inspect and correct every plan, retain original teacher transcripts and correction provenance. The input must actually require semantic compression rather than sentence-for-sentence copying. Freeze a separate outside source family and strong base-plus-plan controls before fitting; inspect results before increasing scale. No next pack, fit, queue or sweep is prepared at this checkpoint.

Independent review remains pending. No persona stability, native prediction, autonomous multi-agent, strong OOD or distributed/NCCL gain is established. This is a useful diagnosis of the writer's supervision, not completion of the broader country-persona project.
