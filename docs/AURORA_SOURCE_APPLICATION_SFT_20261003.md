# Raw-source national-application SFT — 3 October 2026

One fresh Qwen3.5-4B fit repairs selected application errors but loses required details, including on exact training prompts. This recipe does not improve aggregate development coverage. Preserve it as an inspectable result; do not repeat it with more steps. The next informative candidate is a matched coverage-balanced objective, keeping targets and budget fixed, with independently checked criteria where possible and a newly frozen event family.

[Measured receipt](../reports/qwen35-source-application-fit-20261003.json) and [portable replay](../reports/qwen35-source-application-fit-verification-20261003.json) contain the counts, optimization evidence, pairing, ownership and limits. Every one of twelve new complete answers was read before selecting the next direction. Two historical base training controls were reused, not generated again. No subsequent fit is prepared, launched or queued.

## What changed and what was frozen

The previous saved writer learned comparative memos from supplied checked plans. This fresh adapter instead receives raw source statements and a national application question. Its twenty complete synthetic targets were authored by this session assistant using private source-checked plans; those plans never enter the student input. The teacher authoring-context specification is reconstructed provenance, not a separate teacher API transcript. There were zero teacher API calls and no independent teacher/reviewer.

Twenty rows come from two correlated training families: sanctions/humanitarian exemptions (S/PV.9214, Brazil/India) and climate/security (S/PV.8923, France/UK/India/Brazil). Variants cover a harmful proposal, a repair that warrants qualified agreement and unsupported pooled peer claims. Targets distinguish official positions, analyst implementation recommendations, real documented commitments and unknown future Council votes. They include the details later omitted in exact training controls. No reward for disagreement, assertiveness or stylistic novelty was introduced.

The separate evaluation family is women, peace and security: [the primary S/PV.8514 PDF](https://documents.un.org/doc/undoc/pro/n19/117/56/pdf/n1911756.pdf), 23 April 2019, resolution 2467. Complete French and UK **post-vote** national speeches were extracted; earlier speeches are outside the supplied packet. Both countries welcome adoption while deploring omitted health-care language and actually commit to continued support for care. This tests retention of real commitments alongside refusal to invent future votes. France additionally explicitly addresses termination of involuntary pregnancies and the continued earlier 1889/2106 framework; the UK highlights civil society and further justice/accountability. Do not pool every French statement into the UK's explicit position.

The acquired UNBench-all record contains this event. Its parsed list omits the UK Lord-title post-vote speech; the primary PDF governs. All 102 body pages have exact whole-body versus split-column word coverage checks; the relevant speech boundaries were visually inspected. This is benchmark-linked hypothetical application, not native vote prediction. The public record can have appeared in pretraining. One event outside these training families is not certified broad OOD.

The active [training release](../data/prepared/source-application-sft-20261003-v2/release.json) and [evaluation manifest](../data/prepared/source-application-eval-20261003-v2/manifest.json) were frozen before the base answers or fit. Earlier v1 preparation remains preserved; v2 changes source anchors/provenance and two overlapping rubric descriptions, with identical training-row bytes. After seeing base answers, no target, held prompt or criterion was changed.

The held design has France and UK × two single-turn hypotheticals: a restriction that omits comprehensive sexual/reproductive health care and withholds all care until criminal conviction; and a revision that restores care without waiting for conviction while retaining justice/civil society. A peer falsely equates welcoming an imperfect resolution with accepting all omissions. These are fixed application cases, not autonomous peer-pressure/update rollouts. There are also two base-plus-checked-plan restriction controls and two exact historical sanctions training controls.

## Measured behavior

One unblinded assistant authored sources/plans/targets/criteria and annotated the answers. Counts are dependent development annotations, not independent quality scores. Strict pass requires every required unit met; unratable units never count as met.

| Comparison | Base met / unmet / unratable | Fresh adapter met / unmet / unratable | Strict passes base / adapter |
|---|---:|---:|---:|
| Separate WPS event, four raw answers, 48 units | 40 / 7 / 1 | 37 / 10 / 1 | 0/4 / 0/4 |
| Exact sanctions training prompts, two answers, 24 units | 18 / 6 / 0, historical | 16 / 8 / 0 | 0/2 / 0/2 |
| Extra-assisted base restriction plans, two answers, 24 units | 22 / 1 / 1 | Not run | 1/2 / — |

Held raw scores by country/scenario: France restriction 8→9 met, France revision 10→8, UK restriction 11→9, UK revision 11→11, out of twelve each. Two pairwise units have unresolved wording/attribution. Across 46 jointly ratable held units, five corrections coexist with eight regressions. The training controls have three corrections and five regressions across 24 units. These are not independent observations or significance tests. Extra-assisted plans change both information and input length; do not treat them as an equal-compute arm.

Concrete repairs:

- France no longer invents an official future-support contingency. Its revised-proposal answer recognizes restored access rather than explicitly carrying the old objection forward unchanged.
- UK answers stop claiming unsupported specific earlier UK provision/championing from the French material.
- India recommends a Monitoring Team role and reporting without screening every end beneficiary before releasing any funds. The invented 10 December writing date disappears.

Concrete losses:

- French answers lose the earlier reproductive-health framework; the revision also drops historical welcome and explicit pregnancy-termination detail. The restriction's broader pregnancy wording remains unratable.
- UK restriction loses civil society and further justice/accountability. All four adapter held answers lose concrete care/accountability implementation and its trade-off.
- Brazil still omits historical sponsorship/vote and now also drops food/inflation harm and sanctions' legitimate peace/security purpose.
- India omits trade, agency predictability, specific fundraising/recruitment/evasion and political mainstreaming. It rounds “not fully addressed” into “not included,” although the actual training target explicitly says “rather than wholly absent.”

The UK revision does not answer the requested future-support question. Its frozen H8 criterion is a negative no-invention test, so it remains met when no promise is invented; the task omission is preserved separately. Do not rewrite the rubric after seeing the output to convert that silence into a score failure. Before the next freeze, distinguish explicit uncertainty-answer coverage from absence of invented commitments. Other unresolved paraphrase/attribution cases require adjudication and independent review.

Held outputs compress from 2,132 to 1,346 generated tokens; mean words fall from 383 to 286.5. Exact adapter training-control answers average only 140.5 words despite a roughly 300-word request. No answer reaches the 2,048-token cap: these losses are not output truncation. Compression and generic caution are observed alongside factual/operational omissions; this does not prove which training component caused them.

## What the optimizer did

Fresh Qwen/Qwen3.5-4B at revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; rank-8 all-linear LoRA, response-only uniform-token cross-entropy, batch 1 × accumulation 2, learning rate 5e-5 with the existing default linear schedule, seed 42, 20 steps/two dataset epochs. No old writer adapter was resumed. Runtime/model/helper/generation protocol match the Aurora controls; all eleven pinned model files were rehashed before both launches. Greedy decoding, thinking disabled, BF16 SDPA, context 8,192 with no source truncation, max generation 2,048.

One **NVIDIA RTX PRO 6000 Blackwell Server Edition**: training 49.44 seconds, peak allocated training memory 10.39 GiB, 79,556 actually processed sequence tokens and 9,420 supervised target tokens. Twenty finite gradient checks and all 496 adapter tensors changed. Exact saved-tensor reload after perturbing state and a 32-token same-base logit probe pass with maximum difference zero. Training-target loss falls 2.7876→2.0154; this proves optimization, not improved policy behavior. Recorded Aurora Qwen3.5 steps now total **82** across the two-step smoke and four separate fresh twenty-step fits; historical Germany/China optimization is outside that counter.

The loss function remains ordinary SFT. The supervision contract, target content and volume jointly differ from the old two-target writer, so this does not isolate an objective-function advantage.

## Direction selected from this result

The targets already contain the lost exact-control facts and the narrower Indian qualifier. Source-to-application supervision repairs some reasoning errors but uniform token loss still favors short, repeated formulations over retaining every country-specific clause and operational step. That is a candidate explanation, not a proven causal diagnosis; insufficient optimization, target diversity and synthetic-author biases remain alternatives.

Prioritize one matched **clause/coverage-balanced SFT loss** test: mark checked national-fact and implementation clauses, give them controlled extra weight while normalizing per example, and retain the same twenty target texts, initialization and twenty-step budget. Compare against this saved uniform-loss adapter on identical inputs. Freeze another event family before new calls, include both genuine agreement and revision cases, and explicitly score the answer to future-support questions. Audit source/criterion ambiguities independently where possible. This objective comparison is proposed, not implemented or queued; inspect that one result before selecting any further fit. Contrastive preference pairs penalizing a minimally changed omission, gate or invented condition remain a later alternative if coverage weighting fails. More steps, broad inference and sweeps do not isolate the current question.

Keep the strong base-plus-plan control and previous comparative writer. No trained multi-agent result exists. There is no independent persona improvement, preference-method ranking or native benchmark prediction claim from this checkpoint.

## Inspect and replay

- [Twenty actual student inputs/targets](../data/prepared/source-application-sft-20261003-v2/train.jsonl), [private synthetic authoring records](../data/prepared/source-application-sft-20261003-v2/teacher-records.jsonl), [34 exact training source anchors](../data/prepared/source-application-sft-20261003-v2/source-anchor-audit.json).
- [Held cases](../data/prepared/source-application-eval-20261003-v2/cases.jsonl), [frozen criteria](../data/prepared/source-application-eval-20261003-v2/criteria.json), [14 primary anchors](../data/prepared/source-application-eval-20261003-v2/source-criterion-audit.json).
- [All six new base answers](../runs/aurora-qwen35-source-application-base-20261003-v1/transcript.jsonl) and [inspection](../runs/aurora-qwen35-source-application-base-20261003-v1/inspection.json).
- [All six new adapter answers](../runs/aurora-qwen35-source-application-fit-20261003-v1/transcript.jsonl), [inspection](../runs/aurora-qwen35-source-application-fit-20261003-v1/inspection.json), [optimization/ownership receipt](../runs/aurora-qwen35-source-application-fit-20261003-v1/run.json), [saved adapter](../runs/aurora-qwen35-source-application-fit-20261003-v1/adapter/adapter_config.json).
- [Preparation/source-download/exposure audit and retained logs](../runs/source-application-preparation-20261003-v1/download.json). A prospective veto-mechanism definition was adopted before this fit; the historical Gaza unratable judgment and original scores remain unchanged. No veto criterion enters these targets/cases.

Eight focused software checks pass. Initial CPU tests exposed generator/list misuse, fixed before GPU calls; a portable replay initially used an older acquisition-schema field, also fixed, with its failure log retained. Portable checks verify frozen bytes, primary extraction/anchors, family separation, private-plan absence, matching input tokens, measured masks/steps/updates/reload and stored-rating arithmetic. They do not rejudge semantics.

Both recorded project PIDs exited normally with exit code zero. Host, exact GPU UUID, PID/start ticks/time, command and run directory are retained. Unfamiliar jobs/processes were not altered. Credentials and base weights stay outside Git and snapshots; saved adapters and frozen evidence are retained. Independent review and NCCL remain pending.

```bash
python3 -B scripts/verify_source_application_fit_checkpoint.py --root .
python3 -B scripts/verify_research_handoff.py --root .
```
