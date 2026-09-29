# Complete baseline source review — 28 September 2026

All **42 base-model responses** now have provisional source annotations: 21 climate responses and 21 Ukraine responses. The review measures country fidelity, revision gains and losses, and the final multi-country memo separately. It does not establish a general advantage for peer discussion. No new GPU training has run.

One unblinded assistant supplied both batches and helped develop the proposed rubric. The combined file normalizes the batch identifiers to one reviewer. Independent construct review and independent ratings remain pending. The two exposed events and their repeated country responses are dependent observations, not a representative benchmark sample.

## Changes during revision

A confirmed correction changes **unmet to met**; a regression changes **met to unmet**. Units ambiguous on either side are excluded from these counts, with coverage shown. Content and other factual checks remain separate dimensions.

| Event | Revision arm | Content compared | Corrections / regressions | Other checks compared | Corrections / regressions |
|---|---|---:|---:|---:|---:|
| Climate | Independent self-revision | 23 / 24 | 0 / 0 | 15 / 16 | 0 / 0 |
| Climate | Peer discussion | 23 / 24 | 0 / 0 | 15 / 16 | 0 / 0 |
| Climate | Single analyst | 21 / 24 | 1 / 0 | 13 / 16 | 0 / 0 |
| Ukraine | Independent self-revision | 24 / 25 | 0 / 0 | 15 / 16 | 0 / 0 |
| Ukraine | Peer discussion | 24 / 25 | 0 / 1 | 14 / 16 | 1 / 0 |
| Ukraine | Single analyst | 23 / 25 | 0 / 0 | 15 / 16 | 0 / 0 |

The climate single analyst adds France's resilience objective. Its added causal explanation resolves an initially uncertain judgment, and its added Brazilian climate harms expose an ambiguity in the frozen criterion; neither is counted as another confirmed correction. Ukraine peer revision removes an unsupported Brazilian attribution while dropping a required self-determination point. Those different changes must not cancel into a single “no change” judgment.

The country-macro peer benefit remains **null for both events** because India's content comparison is incompletely ratable. This table does not justify a method ranking or significance test.

## What the climate event adds

**Revision often preserves omissions.** National answers retain the same core ratings through self and peer revision. France omits the resilience objective; the UK omits an explicit positive Council role; India omits developing-country participation in the inclusive process; Brazil omits scaling up and timely delivery of climate finance. Some wording changes and supported COP26 details do not repair these required points.

**Aggregation changes uncertainty into a claimed decision.** All three final memos say the UK did not approve binding national carbon quotas. The preceding analyses instead say approval is not established by the statement. The source supports that limited conclusion, not a historical non-approval claim. Country analyses and final memos need separate scores.

**Apparent consensus can be invented.** The climate self-revision memo attributes support for the G-5 Sahel Joint Force to all four countries. France and India discuss support, but the UK and Brazilian passages do not establish it. Shared acknowledgement of climate harms also does not automatically mean agreement on treating climate through a security institution. The central memo's level of abstraction remains an adjudication question.

**A clean end-of-sequence is not task completion.** The climate peer memo ends normally but gives only country summaries, omitting explicit shared analysis and proposed next steps. The self-revision memo reaches its cap mid-proposal. Increasing the token allowance addresses one delivery failure; it does not guarantee completeness or source fidelity.

The [Ukraine review](DELIBERATION_UKRAINE_REVIEW_20260928.md) separately documents an invented later UK vote, an unsupported unconditional French commitment, and a central revision that appends the correct UK draft position without removing its contradictory earlier claim.

## Coverage and unresolved judgments

| Event | Responses annotated | Met units | Unmet units | Unratable units | Responses with no ambiguous ratings |
|---|---:|---:|---:|---:|---:|
| Climate | 21 | 201 | 35 | 19 | 14 |
| Ukraine | 21 | 165 | 82 | 14 | 14 |
| Annotation inventory | 42 | 366 | 117 | 33 | 28 |

These **516 rating instances are not independent samples**. Every response has a known failed unit under the proposed rubric, which can mean an omission as well as an unsupported assertion. This is not a validated population-level failure rate. All six final memos fail the source-supported-position and source/time checks in this assistant review.

Climate uncertainties form nine distinct unit/rationale groups, some reflecting the same underlying interpretation question. They concern India's compound harms criterion and institutional wording, the French causal explanation and military-response inference, the UK's reporting institution, India's qualified denial characterization, alternative source-supported Brazilian harms, and the abstraction level of common ground. No criterion was rewritten to make a result numerically complete.

- [Climate: all 21 complete answers, judgments and full statements](../data/review/deliberation-999389-climate-assistant-v1/assistant-review.md)
- [Climate adjudication cards](../data/review/deliberation-999389-climate-assistant-v1/adjudication-cards.md)
- [Ukraine: all 21 answers and judgments](../data/review/deliberation-999389-ukraine-assistant-v1/assistant-review.md) and [six adjudication decisions](../data/review/deliberation-999389-ukraine-assistant-v1/adjudication-cards.md)
- [Original unlabelled source/answer deck for independent review](../data/review/deliberation-999389-reviewer-kit-v1/review-deck.md)
- [Combined scores](../data/review/deliberation-999389-combined-assistant-v1/scored/scores.json), [receipt](../data/review/deliberation-999389-combined-assistant-v1/scored/receipt.json), [reviewer provenance](../data/review/deliberation-999389-combined-assistant-v1/provenance.json) and [machine-readable findings](../reports/deliberation-combined-assistant-review-20260928.json)

The climate audit verifies 55 output excerpts and 97 source excerpts; the earlier Ukraine audit verifies 61 and 78 respectively. Case, output, source, rubric and guidance hashes bind annotations to the completed inference run. Identical output/rubric pairs receive consistent labels. The complete 42-response scorer run succeeds and retains the semantic-review-pending flags. These checks validate provenance and arithmetic, not the meaning of judgments.

## Next bounded decisions

1. **Independent review:** use the original unlabelled deck before the assistant findings; adjudicate interpretation and attribution. These exposed answers remain development material. Resolving only uncertain units does not validate the other ratings.
2. **Format comparison:** run the prepared [nine-case comparison](EVIDENCE_FORMAT_CHECKPOINT_20260928.md) on one GPU. Compare ordinary prose, evidence-linked prose and evidence-linked JSON on the same tasks with a common larger output allowance, including a new South Sudan event. Inspect semantic support and task completion alongside schema validity; a real quote does not guarantee a supported claim.
3. **Freeze the evaluation:** keep whole event families separated; record sources, prompts, budgets, rubric revisions and reviewer provenance. A format selected on these exposed cases needs separate testing.
4. **Technical training smoke:** after the evaluation gate, use four H100s on `def-zhijing` with `sleep infinity`. Run two LoRA steps on four inspectable examples. Require finite losses/gradients, actual adapter changes, rank agreement, correct masks and successful save/reload before the 20-step fit probe.
5. **Paired comparison:** repeat the frozen base/adapter evaluation with identical evidence and budgets and a fixed unadapted final aggregator. Report gains, new errors, retained positions, false consensus, completeness and cost separately. The ten-example fit probe diagnoses optimization; it cannot establish generalization.

The latest local training payload is `runs/research-readiness-staging-20260928-v3/`; remote v2 lacks the hardened verification code. See [training readiness and launch commands](TRAINING_READINESS_20260928.md). CPU checks pass; four-GPU CUDA/NCCL training remains unverified. At 21:02 Toronto on 28 September, the Trillium multiplex socket was still absent; earlier bounded fresh connections also timed out. The previous allocation's wall deadline has passed, and current scheduler/GPU health cannot be established from its old receipt. No new allocation or training run is claimed. Restore SSH access to execute the prepared comparison; independent evaluation review remains a separate gate before training.
