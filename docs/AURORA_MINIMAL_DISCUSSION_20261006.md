# Minimal source-fidelity transfer through discussion, 6 October 2026

The four-example SFT improvement survives national revisions, but the final memo remains the bottleneck. This continuation produced **28 new complete answers and zero optimizer updates**. Every answer was read in full before selecting the next stage. It follows the [26-answer transfer checkpoint](AURORA_MINIMAL_TRANSFER_20261006.md); together these checkpoints add 54 answers, not 54 independent trials. All are same-assistant development annotations on the historically exposed climate event.

The selected model is the preserved fresh 64-step, four-target Qwen3.5-4B LoRA, trained on the 2022 India/Brazil sanctions source. The 2021 climate source and France/UK were outside that fit. Cumulative Aurora Qwen3.5 updates remain 286, including the historical lost preference fit; the separate published Qwen2.5 reproduction remains 582. No new fitting, queue or sweep was prepared.

## What was frozen and read

Use the original S/PV.8923 national questions, four complete speeches, source spans and atomic rubrics from the previous checkpoint. Read the actual eight initials, all country questions and source criteria, then freeze exactly those responses for revision. The original synchronous contrast gives each country either its own initial or all four initials. No agent receives a newly revised peer answer. All countries retain identical full-source access. Actor histories differ across weight arms because each arm generated its own initials; this is an end-to-end comparison, not an identical-input weight contrast.

The original caps remain 384 tokens per national answer and 512 per final memo, with 8192 context and thinking disabled. Runtime, inference code and GPU type match: **NVIDIA RTX PRO 6000 Blackwell Server Edition**. No source or prompt truncation and no capped answer occurred. Frozen histories contain actual response identities and tokens, not rewritten summaries.

## Original revision and fixed-base aggregation

| Weight arm | Initial content | Own revision | Peer revision | Own/peer source guards |
|---|---:|---:|---:|---:|
| Base |19/24|19/24|18/24|14/16,14/16|
| Four-target fit |22/24|22/24|22/24|16/16,16/16|

There are no content corrections in either revision condition. Base peer revision adds one regression: an initially unknown UK quota approval becomes an assertion that the UK did not approve quotas and explicitly distinguished its voluntary climate commitments from Council powers. Both trained conditions preserve their better initials but still omit UK meaningful women/girls participation and Indian developing-country participation.

The same unadapted base then produces four memos, one per actor-weight/revision condition. All four fail at least one original synthesis check; each meets only 2/5. Three invent a 15 December 2021 writing date. Other failures include a Brazilian $1 trillion request borrowed from India, a Brazilian $100 billion proposal borrowed from UK/global references, UK G-5 support absent from its speech, and an explicit UK quota rejection never stated. Improved upstream answers do not make the final writer faithful.

The original national units are also annotated as a **diagnostic** inside each memo:11/24,13/24,13/24,14/24 in base-own, base-peer, fitted-own and fitted-peer order. These are not the original final-memo score or 24 independent observations. Missing detail can coexist with valid high-level synthesis; unsupported extra claims remain separately visible.

## Smallest aggregator change

After reading all four base memos, apply the same saved four-target fit to their **identical actual input tokens**, with unchanged sources, notes, instructions and limits. This is a separate aggregator-weight ablation: it deliberately changes the original fixed-base rule and preserves that original result.

All four adapted memos remove invented writing dates and misattributed numeric finance amounts. Diagnostic national coverage becomes15/24,13/24,17/24,14/24. However, every memo now explicitly pools all four countries into G-5 Sahel Joint Force support. The UK and Brazil speeches establish neither that support nor opposition. All four still meet only 2/5 original synthesis checks. Local repairs are real; a full source-faithful synthesis gain is not established.

## Direct attribution and checked-ledger control

After reading the eight memos, test two smaller cases on identical base/fitted inputs: a direct four-country G-5 support question, and the original fitted-peer memo prompt with a short manually checked attribution ledger. The ledger specifies FRA/IND support, GBR/BRA unknowns, UK draft-versus-quota boundaries, who mentioned the finance amounts, and the absence of a writing date. It is supplied assistant assistance, not a learned planner or independent review.

The direct question has five frozen units. Base meets4/5: it wrongly treats explicit Indian support as absent. The fit meets5/5 but adds an unsupported denial of explicit Indian financial/logistical support. Both fail source guards. An initial base3/5 annotation conflated lack of endorsement with opposition; rereading the narrower frozen criterion corrects that unit to met while retaining its unsupported-inference guard failure. Both annotations are preserved. Counting required points alone would hide these errors.

Base plus ledger still invents a writing date, UK G-5 support, an annual Indian$1 trillion transfer and an adaptation-only$100 billion target. Fit plus ledger correctly limits G-5 support to FRA/IND and drops the date/amount errors. It still omits requested national details. Its broader claim that “they” value regional cooperation could refer to all four or to the explicitly scoped collective contributions; two synthesis checks remain unratable pending adjudication. This memo has 2 met,1 unmet and2 unratable checks, not a strict pass. No invented consensus is accepted merely because a proposal is marked hypothetical.

The first preparation merged words in the new question/ledger. Its positively identified owned process was stopped before generating any answer or update; v1 inputs, launch identity and stop receipt remain. Normally spaced v2 was frozen and read before comparison. No unfamiliar process was changed.

## Decision and receipts

Retain the four-target fit and the eight-target sanctions branch. The next promising **training** candidate is a short complete source-to-attribution/synthesis target that teaches country-specific supported claims, unknowns and required details. Freeze a separate comparison and strong checked-plan control before fitting. Inspect the entire selected target, sources and outputs; establish that the target is learned before enlarging data. More peer rounds, another generic style target or a speculative optimization sweep do not address the inspected failures. The larger eight-target branch's lower training dose remains a deferred alternative, not a selected queue.

No native vote prediction, autonomous diplomacy, independently validated persona gain or positive peer-discussion gain is claimed. The sources contain decisions and public positions; they do not reveal private utilities, population values or an actual negotiation.

- Original continuation: `reports/minimal-deliberation-continuation-20261006.json`, replayed by `scripts/verify_minimal_deliberation_continuation.py`.
- Direct/ledger control: `reports/minimal-attribution-ledger-20261006.json`, replayed by `scripts/verify_minimal_attribution_ledger.py`.
- Frozen data: `data/prepared/minimal-deliberation-revisions-20261006-v1/`, `minimal-deliberation-synthesis-20261006-v1/`, `minimal-deliberation-adapted-aggregator-20261006-v1/`, and both `minimal-attribution-ledger-20261006-*` packs.
- Complete transcripts and individual source/criterion annotations are under the corresponding `runs/aurora-minimal-*` directories; exact old annotations and stopped preparation are preserved.
- Twenty-one existing deliberation/review software guards pass. Token/source/pairing/weights/code replay verifies stored arithmetic and reproducibility, not independent semantics.
- Ownership and exited-process checks: `reports/minimal-discussion-resource-status-20261006.json`. No resources remain queued for a further fit.
