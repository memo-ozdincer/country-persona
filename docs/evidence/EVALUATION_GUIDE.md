# What were our evaluations, and what improved?

[All evidence](README.md) · **[Actual short-answer model outputs](minimal-country-sft-20261021/model-outputs.md)** · **[Actual meeting-context model outputs](meeting-context-20261021/model-outputs.md)**

The country scores in these pages come from **custom, source-grounded development evaluations**, not official UNBench or another public benchmark leaderboard. The same unblinded assistant selected the sources, wrote training targets and criteria, and judged the complete generated answers. These evaluations diagnose specific errors; they do not establish independent persona, diplomatic-reasoning, or multi-agent capability gains.

## 1. Short-answer country SFT: what the task was

The model received both complete India/Brazil national statements from the same 9 December 2022 Council meeting and a hypothetical implementation proposal. It answered as one assigned delegation. We compared the untrained base with two separate fresh 64-step fits: four complete supervision examples versus eight. Sources, decoding and evaluation prompts were matched across those three arms.

The headline set had eight prompts outside the eight fitting prompts: two countries under each of four situations:

| Situation | What the prompt tested |
|---|---|
| Pressure to agree | Would the delegation falsely claim all national concerns were satisfied, or preserve the documented disagreement? |
| Repaired proposal | Would it notice that the requested mechanisms were now supplied and respond constructively, rather than repeat the old objection? |
| Incorrect peer summary | Would it correct pooled sponsorship, endorsement and policy requests, keeping India's and Brazil's positions distinct? This was a supplied erroneous summary, not an interactive multi-agent benchmark. |
| Partially repaired proposal | Would it recognize the added Team role while identifying the remaining reporting gap, without inventing a new national condition? The active/proactive wording has a preserved interpretive qualification. |

Each answer received five checks. Eight answers × five checks = **40**, not 40 independent questions. The last two checks alone give the separate **16** application/commitment checks. Scores below are recomputed from the original saved grades, with no regrading.

## Five criteria: what each model did better on

| Criterion | What counted as met | Base | Four-example SFT | Eight-example SFT |
|---|---|---:|---:|---:|
| Preserve humanitarian priorities | Retain timely relief/basic needs for India, and predictable relief/civilian protection for Brazil. | 6/8 | 5/8 | 8/8 |
| Preserve security qualifications | Retain Indian terrorist-diversion/due-diligence concerns or Brazilian recognition of useful sanctions/legitimate security concerns. | 6/8 | 8/8 | 8/8 |
| Attribute positions to the correct country | Retain India’s proactive Monitoring Team plus robust-reporting requests; retain Brazil’s sponsorship plus favourable vote; avoid borrowing the other delegation’s commitments. | 4/8 | 6/8 | 7/8 |
| Respond to the actual proposal state | Recognize which objections remain and which were repaired; correct false joint claims instead of repeating them. | 2/8 | 7/8 | 7/8 |
| Respect limits on official commitments | Distinguish a negotiating recommendation from a documented government commitment; do not invent a future vote or official vote condition. | 5/8 | 8/8 | 8/8 |
| **All five checks** | Dependent content checks over the same eight answers | **23/40** | **34/40** | **38/40** |
| **Application + commitment only** | Last two rows, not additional observations | **7/16** | **15/16** | **15/16** |

**Four examples:** the main gain was recognizing the proposal state and avoiding invented commitments. Security coverage also improved; humanitarian-priority coverage regressed on this set.

**Eight examples:** recovered humanitarian content and improved national attribution. It did not improve the aggregate application/commitment score beyond the four-example model. A better total therefore does not mean it dominates every case.

## By situation

Each row has two country answers × five checks = ten.

| Situation | Base | Four-example SFT | Eight-example SFT |
|---|---:|---:|---:|
| Pressure to agree | 8/10 | 7/10 | 10/10 |
| Fully repaired proposal | 5/10 | 9/10 | 9/10 |
| Incorrect peer summary | 5/10 | 8/10 | 10/10 |
| Partially repaired proposal | 5/10 | 10/10 | 9/10 |

## Every case

| Case | Base | Four-example SFT | Eight-example SFT |
|---|---:|---:|---:|
| [pressure-ind](minimal-country-sft-20261021/model-outputs.md#pressure-ind) | 4/5 | 3/5 | 5/5 |
| [pressure-bra](minimal-country-sft-20261021/model-outputs.md#pressure-bra) | 4/5 | 4/5 | 5/5 |
| [repair-ind](minimal-country-sft-20261021/model-outputs.md#repair-ind) | 3/5 | 4/5 | 4/5 |
| [repair-bra](minimal-country-sft-20261021/model-outputs.md#repair-bra) | 2/5 | 5/5 | 5/5 |
| [new-peer-ind](minimal-country-sft-20261021/model-outputs.md#new-peer-ind) | 3/5 | 3/5 | 5/5 |
| [new-peer-bra](minimal-country-sft-20261021/model-outputs.md#new-peer-bra) | 2/5 | 5/5 | 5/5 |
| [new-partial-ind](minimal-country-sft-20261021/model-outputs.md#new-partial-ind) | 3/5 | 5/5 | 4/5 |
| [new-partial-bra](minimal-country-sft-20261021/model-outputs.md#new-partial-bra) | 2/5 | 5/5 | 5/5 |

**Remaining failures:** the eight-example India repaired-proposal answer omits the exact Team/reporting details. On India's partial repair, the four-example answer has 5/5 while the eight-example answer has 4/5; the active/proactive ambiguity qualifies that original grade. The follow-up [literal-mechanism diagnosis](minimal-country-sft-20261021/wording-diagnosis.md) preserves all original outputs and interpretations.

**Limits of a 5/5:** the eight-example pressure-India answer receives all five coverage checks but recommends “joining the resolution” when the task asked about joint-statement wording after adoption. That additional error remains in the original review. Consequently, 38/40 is content coverage, not 95% diplomatic correctness or persona accuracy.

## Other short-answer controls

- The expanded evaluation had **14 prompts**: the eight headline cases, four exact fitting-control prompts, and two supplied-plan controls. Fitting controls check recall; plan controls check whether supplying organized content helps. They are excluded from the 40-check headline total.
- The earlier ten-prompt evaluation compared base, a 16-step four-example fit, and a fresh 64-step four-example fit. Total coverage was 37/50, 36/50 and 43/50. The short fit underfit; fitting more thoroughly helped locally but left transfer errors. [All outputs](minimal-country-sft-20261021/early-fits.md).
- The later literal-mechanism diagnosis compared the same saved models without further training, to qualify the ambiguous partial-state interpretation.

All of these reuse an exposed historical source event. They are not sealed event, time, or role OOD tests. A supplied peer claim is not evidence that a multi-agent system improved.

## 2. Meeting-context / authentic-speech SFT: a different evaluation

This branch trained on four authentic UK/India speeches with scenario, earlier turns and requested role, then evaluated two Ukraine speeches excluded from that fit. The frozen content rubric had **20 material units across the four fitting speeches** and **eight across the two development speeches**, plus whole-answer guards for role/output/source constraints. We also measured the mean negative log likelihood (NLL) of the authentic reference speech, including the end token; lower is better. This is a likelihood diagnostic, not a separate persona score.

| Matched comparison | What improved? | What did not? |
|---|---|---|
| Fresh 128-update four-speech adapter | All four fitting speeches exactly reproduced; 20/20 fitting units and 4/4 fitting strict passes. | Both Ukraine development cases fail in raw and corrected native formats. |
| Native-chat formatting controls | Readable single speeches replaced some raw-format copying/looping in the base. | Source/role fidelity was still inadequate. This was a prompt-format change, not a training gain. |

| Ukraine case, corrected native format | Base reference NLL | Adapter reference NLL |
|---|---:|---:|
| India | 2.149 | 4.862 |
| UK | 2.408 | 4.833 |

The adapter worsened reference likelihood and invented policies/events; there is no demonstrated development improvement on this branch. Some exact historical facts were absent from its supplied windows. Full preceding history fit for sanctions; climate/Ukraine retained only the immediately preceding complete speech plus scenario metadata because of the context budget. Missing facts qualify the reconstruction test, while fabricated policies and extra speakers remain failures. These sources had historical exposure and are not sealed OOD or forward-time tests.

[All generated continuation answers](meeting-context-20261021/model-outputs.md#authentic-meeting-continuation-14-generated-replies) · [Full original rubric](../../research/scenario-role-sft-20261017-v1/rubric.json).

## 3. Context follow-up: better inputs without further training

This was a newly specified source-conditioned task, not a regrade of authentic speech reconstruction. Each of two country answers had **nine required material units** (18 total), plus six whole-answer guards per answer covering attribution, authority/time, unsupported additions, public output, and a 240-word limit. Strict success required the whole contract, not just the content total.

| Input / weight arm | Required material covered | Strict complete answers | Interpretation |
|---|---|---|---|
| Base + complete earlier-country dossier | 12 met / 4 unmet / 2 uncertain of 18 | 0/2 | Attribution and recipient/stage errors. |
| Saved four-speech adapter + same dossier | 12 met / 6 unmet of 18 | 0/2 | No gain over base; unsupported claims. |
| Base + explicitly attributed quote cards | 15/18 | 0/2 | Attribution improves, but facts are still omitted/merged. |
| Base writer + cards + actual unedited model reader map | 18/18 | 1/2, provisional | Better preservation of the scored facts; India exceeds the word limit and has an uncertain authority explanation. |
| Same map + smaller requested word target | 16/18 | 0/2 | Shorter answers reintroduce material errors. |

The 18/18 result is an adaptive same-assistant development result with additional checklist/context/generation/compute. It is not a trained-model gain or isolated evidence that multiple agents reason better. The provisional UK strict pass retains its original interpretation caveats.

[All generated context-follow-up outputs](meeting-context-20261021/model-outputs.md#context-follow-up-11-generated-outputs) · [Original rubric](../../research/grounded-role-20261019-v1/rubric.json) · [Dated analysis](../GROUNDED_ROLE_CHECKPOINT_20261019.md).

## How to read the files

- **Model outputs** pages show the actual saved generated replies immediately, with no input sections.
- **Training** pages show the prompts and supplied supervision targets. A target is not a generated evaluation answer.
- **Full comparisons** show outputs first; exact inputs and original grades are separately expandable.
- All original failures, ambiguous grades and extra fidelity notes are retained. This documentation update runs no model and does not resume the paused research goal.
