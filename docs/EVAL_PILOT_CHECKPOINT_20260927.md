# Two-event evaluation checkpoint

**Subsequent result:** [The eight-output GPU probe and full 30-output comparison have completed](EVAL_BASELINE_RESULTS_20260927.md). The zero-compute and authentication-pending statements below describe this earlier source/rubric checkpoint. Independent reviews and new training remain outstanding.

27 September 2026. Implements the first small slice of the [research checkpoint plan](RESEARCH_CHECKPOINT_PLAN.md). **We now have two source-checked reconstruction cards, seven action questions, eight policy questions, and a 19-example rubric calibration deck.** Each action/policy question has a no-evidence A arm and a dated-evidence B arm: 30 prompts in total. The countries are France, UK, India and Brazil.

These are development artifacts. No new pretrained-model generations, adapter training, independent human ratings or online publication occurred in this checkpoint. Germany/China work remains separate. Human/expert review and the first inference comparison are still pending. The subsequent [inference instrumentation checkpoint](EVAL_INFERENCE_CHECKPOINT_20260927.md) adds a traced runner and CPU random-weight integration check, bringing the combined targeted test count to 55.

## What we learned and changed

| Check | Observation | Consequence |
|---|---|---|
| Exact voting stage | The primary records confirm the seven selected extension-country votes on the whole drafts, matching the earlier candidate pack. | These action labels can support the reconstruction pilot. Brazil has a climate policy statement but no vote label for the 2021 event. |
| Announced positions | The UK explicitly supported the drafts in both earlier speeches. The climate draft also lists the UK as a cosponsor. | Preserve those clues and report announced-position cases separately. Do not present every correct answer as difficult forecasting. |
| Policy versus action | Brazil criticized the Ukrainian referendums in its earlier statement but subsequently abstained on the draft. | A substantive objection does not uniquely establish a later procedural choice. Evaluate both, with separate references. |
| PDF reading order | Default text extraction can mix the two columns of a meeting record. | Extract each column separately. Retain exact speech boundaries, character offsets, page/column locations and source hashes; visually check relevant pages. |
| Institutional attribution | The French Council President explicitly switched to speaking in France's national capacity. | A national statement must not be scored as a unanimous Council position. |
| Source timing | Meeting dates precede the votes, but the archived PDFs' first online availability is unverified; the draft PDFs bear production stamps after the votes. | Label the pilot historical reconstruction. It is not a clean prospective forecast, nor a certificate that the exact archived version was available before the decision. |
| Input budget | All 30 full prompts fit a 7,168-token input allowance: 44,384 input tokens overall, maximum 5,033. | No truncation is needed for this slice. This does not resolve the longer drafts elsewhere in the seven-event pack. |

The [source acquisition receipt](../data/manifests/eval-sources-20260927.json) pins six official PDFs. The first Digital Library endpoints returned HTML challenge pages; the collector rejected them and obtained the PDFs through the separate public UN document API. No challenge-solving workaround was used. The original failed receipt remains with the raw acquisition.

## The two event cards

| Event | Primary outcome reference | Extension-country actions | Earlier policy evidence |
|---|---|---|---|
| **S/2021/990**, 13 December 2021, meeting 8926; climate/security draft | S/PV.8926, PDF page 5: 12 Yes, two No, one abstention; not adopted because of a permanent-member negative vote | France Y; UK Y; India N. Brazil policy only. | S/PV.8923, 9 December: France pp. 12–13, India pp. 19–21, UK p. 24, Brazil p. 30 |
| **S/2022/720**, 30 September 2022, meeting 9143; Ukraine draft | Special-report bundle dated 6 October, PDF page 2: ten Yes, one No, four abstentions; not adopted because of a permanent-member negative vote | France Y; UK Y; India A; Brazil A | S/PV.9138, 27 September: India p. 8, UK pp. 9–10, Brazil p. 10, France pp. 17–18 |

The later voting records are reference-only. They never enter either model arm. For the action task, both arms receive the same archived draft; B adds only the country's selected earlier speech. For the policy task, both arms receive the same question, country and date; B adds that speech. The comparison therefore estimates the value of supplying the evidence, while holding task wording and model fixed.

The UK’s Ukraine speech refers to the US/Albania proposal without its eventual document symbol. Its connection to S/2022/720 is retrospective; we have not established that every word of the final archived draft was fixed on 27 September. The English French statement also lists “Kharkiv” on page 17. That source wording is preserved and is not used as an independently verified geography target.

Full [machine-readable event cards](../reports/eval-pilot-20260927/event-cards.json) contain source URLs, PDF hashes, timing limitations and review status. Both events and every derivative are exposed development material; the two issue-family identifiers are provisional, not a completed cross-corpus split audit.

## What the eight policy questions test

| Country/event | Required substance | A plausible answer that should fail |
|---|---|---|
| France / climate | Council assessment/prevention; why military responses alone are insufficient; one supported complementary measure | Accurate general discussion plus the preceding US speaker's PREPARE funding pledge falsely attributed to France |
| India / climate | UNFCCC institutional preference; acknowledgment that climate can exacerbate conflict; objection to climate-only explanations | “India denied that climate change could ever exacerbate conflict” |
| UK / climate | Comprehensive reporting, meaningful participation by women/girls, explicit draft support, limits of the evidence | Inventing approval of binding Council-imposed national carbon quotas |
| Brazil / climate | Respect for mandates/UNFCCC, acknowledged climate harms, developed-country financing priority | Fluent institutional discussion that omits the requested practical financing priority |
| France / Ukraine | National capacity, non-recognition of annexation, continuing support, no specified financial amount | Converting France's statement into unanimous Council agreement |
| UK / Ukraine | Rejection of coercive/illegitimate referendums, support for the US/Albania draft, speech-versus-vote distinction | Treating the 27 September speech as the 30 September recorded vote |
| India / Ukraine | Cessation/diplomacy, law/sovereignty, humanitarian and economic effects, uncertainty about the later vote from this source | Giving the historically correct abstention while falsely claiming this earlier speech establishes it |
| Brazil / Ukraine | Conditional validity of referendums, free expression and other conditions, current concerns, limits of a hypothetical recognition inference | “Adding observers and unrestricted expression guarantees Brazilian recognition” |

The last example is explicitly an authored scenario; it has no invented historical vote. “Not established” always means absent from the bounded selected statement, not proved absent from every historical document. Equivalent supported wording passes. National style and agreement with the reviewer’s politics are not scoring targets.

For example, a good India/climate answer explains that India **acknowledged exacerbated conflicts**, while preferring the inclusive UNFCCC process and resisting a climate-only explanation of conflict. An answer that preserves the institutional point but drops that acknowledgment is incomplete. This is why a vote-only evaluation would miss an important failure.

## Rubric and calibration status

Every policy item has a source-backed required-content checklist. A strict pass requires every item criterion plus three universal checks: no material invented commitment, correct attribution, and correct time/scope. Empty answers fail. Unratable or missing ratings remain visible; they cannot silently disappear from a denominator or become a pass. Reviews are joined to the exact response text and case hashes.

The deck contains **eight authored supported answers and eleven deliberately flawed variants**, mixed under opaque response IDs. The private key contains the author's expected criterion ratings and the reason for each seeded failure. All 19 receive the intended treatment when those ratings are supplied to the scorer. **That checks scoring arithmetic, not a semantic judge or reviewer reliability.** It is not a 42% model score, and there is no independent agreement estimate yet.

Two reviewers should rate the [blinded deck](../data/review/eval-pilot-20260927/calibration-v1/review-deck.md) independently, using its [blank review template](../data/review/eval-pilot-20260927/calibration-v1/review-template.jsonl), before opening the private key. Their ratings should remain separate until disagreements are categorized and resolved. The CLI reports each reviewer separately and does not pretend to adjudicate automatically.

## Checks completed

- **43 targeted tests pass**, including source boundaries, exact evidence spans, A/B pairing, missing qualifications, invented commitments, empty/unreviewed answers and stale output hashes.
- The eight generated package files and six calibration files were rebuilt into fresh directories and matched byte-for-byte.
- The policy-scoring CLI reproduced all 19 authored expectations.
- The locked Qwen3 tokenizer checked every full prompt. Y/N/A are each one token; this is not yet a measurement of model probabilities.
- The assistant inspected the two outcome pages and 12 relevant speech pages. Independent human/expert checks remain pending.

Receipts: [validation](../reports/eval-pilot-20260927/validation.json), [pack manifest](../reports/eval-pilot-20260927/two-event-manifest.json), [tokenizer preflight](../reports/eval-pilot-20260927/preflight.json), [calibration status](../reports/eval-pilot-20260927/calibration-report.json). GPU time and new model-output tokens spent: **zero**. Human reviewer time: **not yet collected**.

## The next bounded experiment

An [eight-output probe](../reports/eval-pilot-20260927/probe-manifest.json) is selected: A/B action pairs for India/climate, France/Ukraine and Brazil/Ukraine, plus the India/climate policy pair. It spans the observed Y/N/A labels while retaining one material-qualification question. Its full input budget is **17,124 tokens**, maximum 5,033 for one prompt. These are tokenized inputs, not a measured runtime or GPU-hour estimate.

The [instrumented inference path](EVAL_INFERENCE_CHECKPOINT_20260927.md) is now built and checked on CPU with a tiny random model. Next run the probe with the pinned Qwen3 model. The runner records raw tokens, full input coverage, effective EOS settings, stop reasons, timing, output caps and repetition. For actions, it retains the actual next-token Y/N/A distribution, its total legal-label mass, and unconstrained generations separately. Replay the legacy single-EOS setting on a bounded subset before attributing a stopping difference to an adapter. The older evaluator is preserved; use `scripts/run_eval_probe.py` for this new package.

Trillium rejected the SSH connection for lack of authentication; no job was submitted. Reconnection was requested. Local compute has 16 GiB of RAM; the pinned BF16 8B model is not a sensible memory-safe fallback with adequate working headroom. A quantized replacement would be a separately declared experiment, not silently substituted into this comparison.

After decoding works, complete the 30-output A/B comparison and review the policy answers with arm identity hidden. Every conclusion must name the affected case and failure mode. Only then expand independent event coverage and prepare the one LoRA SFT comparison against the same-evidence baseline. The [longer-term plan](RESEARCH_CHECKPOINT_PLAN.md) keeps robustness, controlled deliberation, human usefulness and the paper as separate checkpoints with their own decision rules.

## Reproduce the current package

Builders require fresh output directories to preserve earlier cases and reviews. Raw PDF paths are pinned in the acquisition manifest; the earlier action-review-v2 pack is a required label-linkage input.

```bash
.venv/bin/python scripts/collect_eval_sources.py \
  --config data/curation/eval_sources_20260927.json \
  --root data/raw/eval-sources-20260927
.venv/bin/python scripts/build_two_event_eval.py \
  --output data/prepared/eval-pilot-20260927/two-event-rebuild
.venv/bin/python scripts/build_policy_calibration.py \
  --pack data/prepared/eval-pilot-20260927/two-event-rebuild \
  --output data/review/eval-pilot-20260927/calibration-rebuild
.venv/bin/python scripts/preflight_action_eval.py \
  --pack data/prepared/eval-pilot-20260927/two-event-rebuild \
  --prompt-budget 7168 --output reports/eval-pilot-20260927/preflight-rebuild.json
.venv/bin/python -m pytest -q tests/test_action_eval.py \
  tests/test_action_review_pack.py tests/test_unsc_bench.py \
  tests/test_eval_evidence.py tests/test_policy_eval.py
```

For real reviews, run `scripts/score_policy_reviews.py` with the frozen cases, policy references, response file and a completed review file. Blank templates intentionally fail validation. Keep authored fixture ratings out of human/model-performance reports.
