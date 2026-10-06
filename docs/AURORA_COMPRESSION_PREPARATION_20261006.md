# Checked long-plan supervision, before student fitting

Eight curated compression examples are now compiled: **420–483-word ordinary English plans paired with the unchanged 200–236-word short answers**. Every native chosen-completion token matches the earlier raw8/point8 data exactly. Only the supplied plan representation changes relative to point8; source, current note, system and realization contract remain unchanged. This is inspected preparation, not a new student-quality result. No student fit is authorized or queued at this checkpoint.

The checkpoint adds **16 actual Qwen3.5-4B teacher outputs and zero optimizer updates**. All sixteen are uncapped and were read in full against the fixed targets and source audits. None is approved unchanged. Cumulative recorded Qwen3.5 updates remain **2,270**, with **582** separate Qwen2.5 reproduction updates.

## What the actual teacher did

The first eight requests included the checked short answer plus the old full case/source as verification context. Most outputs were below the requested 350–450 words. They also omitted meanings or changed actor/scope: Germany's initiative disappeared, the resolution's requested SG report became a request by France, and the UK's counterfactual preference against withdrawal became “withdrawal is not chosen now.” Current repairs and historical defects sometimes blurred. All eight were inspected before selecting another request.

One target-only probe placed the length and retention instructions clearly at the end and in the system prompt. It produced a 417-word WPS plan, retaining Germany and the SG-report distinction. It still added unbounded diplomatic commitments and causal/authority language; these were corrected, with the original preserved. That probe justified seven remaining requests, rather than an automatic repeated eight-case campaign.

The seven remaining outputs ranged from 424 to 722 words and remained unreliable. Both Mali plans reinterpreted **resolution 2690 as 2,690 personnel**, one substituted UK departure for Mission departure, and several added new official support conditions, falsely described a defective note as repaired, or copied rewriting instructions into the plan. Length alone does not establish usable data.

All raw outputs remain immutable. The final eight plans are **extensively corrected or rewritten by the same assistant**, informed by those drafts, the fixed short targets and the checked primary sources. They are not unchanged Qwen teacher outputs, a separate teacher API transcript, or independent review. The exact changes and origin links are preserved in the curation files and compiled draft. The preferred short targets remain unchanged.

The corrected data explicitly preserves the current repaired/defective states, actual hypothetical Indian endorsement when supplied, unknown future vote guarantees, real continuing care/cooperation/willingness, mission versus national-UK departure, all stated sanctions-exploitation modes, and source versus analytical authority. It removes invented causes, conditions and commitments. Shared complete documented-position sections and every case-specific application/authority section were reread after serialization. Shared historical raw sources retain their earlier whole-source audits with exact-byte continuity.

## Separate prospective source family

A new outside-fitting family is [S/PV.9469, 8 November 2023](https://digitallibrary.un.org/record/4027986), the ICC/Libya briefing. The [official English PDF](https://documents.un.org/doc/undoc/pro/n23/340/45/pdf/n2334045.pdf) is 496,217 bytes, SHA256 `e441e063b306755f2ae0e597a7b491dd25bcbbe65d52663a094d07602ee7e2af`. It has seventeen pages; all sixteen body-page word multisets survive column extraction.

The complete national Brazil and France speeches were read. Brazil/França Danese spans offsets 49745–52736, ending before Ecuador; France/Dime Labille spans 60050–65083, ending before Mozambique. English primary pages 11–14 were viewed. China/Zhang Jun presides, while Khan is the Prosecutor. The selected speakers are national representatives, not those other institutional roles; this briefing supplies no present meeting vote label.

The English France speech's “ambassador appointed from the Netherlands” was ambiguous. The official French original says “nouvel Ambassadeur nommé aux Pays-Bas.” French page 14 was viewed and posting **in** the Netherlands clarified; nationality or an unstated personal identity is not inferred. Both language records and the adjudication remain preserved.

Prospective source/application criteria and a mixed hypothetical Q are frozen in `data/curation/compression-libya-prospective-20261006-v1.json`, with zero Libya model calls. Q includes retained cooperation provisions as well as erroneous completion/judgment claims, selective accountability, cooperation exceptions and support conditions. Important contrasts include Brazil's national primacy/ICC unable-or-unwilling/Chapter VII cooperation distinction, no judgments yet, and France's **real continuing political, operational, human and financial support**, potential future roadmap and future Tripoli-office status. Those ongoing commitments must not be denied merely because a new amount or future vote is unknown.

This family remains in the ICC/UN genre. Corpus/pretraining exposure is unknown; it is not strong domain or sealed OOD evidence. Checked held writer plans/control inputs and prospective presentation checks still need completion before the student comparison.

## Ownership and preparation checks

The first teacher attempt selected GPU 2 after an unfamiliar process had occupied it. The native occupancy guard stopped before model loading or ownership. The eight teacher calls then ran on positively free GPU 1. An unfamiliar job later occupied GPU 1, and the probe's guard stopped there too; the probe and seven remaining calls ran on free GPU 3. All three successful project GPU identities are recorded and exited. No unfamiliar process was cancelled or altered.

Hardware in every successful call is **NVIDIA RTX PRO 6000 Blackwell Server Edition**. The model/revision/runtime/native generator remain pinned: Qwen3.5-4B revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`, BF16 SDPA, thinking disabled, greedy 2,048-token generation and the 8,192-token limit. Teacher generation totals **9,197 tokens and 139.25 seconds**, excluding loading/verification overhead.

A student-draft builder initially stopped because the already-read seven-output review had not yet been saved. The missing review was persisted before a fresh version 2 draft was built. No student pack, model call or update resulted from that failed CPU attempt. The initial Digital Library PDF request also returned a non-PDF body; it was not used, and the official symbol-access API succeeded. The failed body was not saved, so exact reproduction of its bytes is not claimed. Logs and failure receipts are retained.

Portable replay verifies all sixteen actual teacher outputs, native input/output/code/model protocol, review chains and positive exit identities; curated pair/source/target hashes, no short-target prose in student inputs, identical native chosen tokens, and English/French primary evidence. These checks establish integrity and preparation arithmetic, not independent semantic review or student behavior.

## Artifacts and next action

- Actual teacher packs/runs: `compression-teacher-20261006-v1`, `compression-teacher-probe-20261006-v1`, `compression-teacher-remaining-20261006-v1`; successful run versions are recorded in the evidence receipt.
- Curated plans: `data/curation/compression-long-plans-20261006-v1.json`.
- Compiled student draft: `data/prepared/compression-student-draft-20261006-v2`.
- New primary evidence: `data/raw/compression-libya-grounding-20261006-v1`.
- Prospective held rubric/note: `data/curation/compression-libya-prospective-20261006-v1.json`.
- Evidence/verifier: `reports/compression-preparation-20261006-v1.json`, `scripts/verify_compression_preparation.py`.

Next, finish and hand-audit the Libya raw/long-plan control inputs and presentation checks. Obtain matching, inspected actual base controls and bind the unused zero-gradient negatives. Then bind one fresh **eight-target, 256-update** comparison with the exact unchanged native chosen tokens, and compare the saved point8 adapter and the new fit on identical outside inputs. Inspect the checkpoint before scaling. No student fit, queue or sweep is prepared now.

Same-assistant planning, data correction and grading remain a limitation; independent review is pending. No new student-quality, persona stability, native prediction, autonomous multi-agent or distributed/NCCL gain is established. Preserve the Germany/China work and every earlier input, criterion, grade, adapter and failure receipt.
