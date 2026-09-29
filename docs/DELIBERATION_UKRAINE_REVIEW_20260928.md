# Ukraine deliberation: provisional source review — 28 September 2026

**The first complete event review shows mixed changes, not a demonstrated peer-discussion benefit.** Across the jointly ratable national content units, peer revision corrected none and lost one required point. It separately corrected one attribution error. Self-revision and the single analyst's revision made no confirmed corrections on their jointly ratable units. The overall peer-benefit score remains unresolved because a content criterion is ambiguous.

This is a **single assistant review**, aware of the conditions and involved in the proposed rubric. It covers all 21 Ukraine outputs from the existing 42-call base-model run, using the complete France/UK/India/Brazil statements from [S/PV.9138, 27 September 2022](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9138&t=pdf). No new inference or training ran. These are development annotations, not independent human validation or a benchmark ranking.

## What the revision counts actually say

The national questions have 25 required content units and 16 additional checks across the four countries. A correction means a unit changes from unmet to met; a regression means met to unmet. An unratable unit is excluded from paired counts and retained in the reported denominator/coverage.

| Revision arm | Content units compared | Content corrections | Content regressions | Other checks compared | Check corrections / regressions |
|---|---:|---:|---:|---:|---:|
| Independent self-revision | 24 / 25 | 0 | 0 | 15 / 16 | 0 / 0 |
| Peer discussion | 24 / 25 | 0 | 1 | 14 / 16 | 1 / 0 |
| Single analyst | 23 / 25 | 0 | 0 | 15 / 16 | 0 / 0 |

These are separate dimensions. Do not subtract one content regression from one attribution correction and call that “no change”: they concern different requirements and have different coverage. Country answers, repeated turns and units from one event are dependent observations. No significance claim is justified.

There are **261 rating instances: 165 met, 82 unmet and 14 unratable**. Repeated outputs and rubric units make these unsuitable as an independent sample size. Fourteen responses have complete ratings; seven retain at least one ambiguous judgment. Every response also has at least one known failed unit under this proposed rubric. This is not a validated population-level pass-rate estimate.

## Concrete findings

**The UK chronology error survives revision; it is not newly caused by peers.** Both initial UK answers and both revised UK answers are exactly identical. They describe S/PV.9135 as a later vote confirming support. The actual source calls it the Foreign Secretary's remarks “last week.” The correct draft-support position is present, but the invented vote makes the answer unfaithful to the dated evidence. This is a failure to correct an existing error, not evidence of peer-induced contamination.

**Brazil's peer revision trades a supported point for a cleaner attribution.** The initial and self-revised answers explicitly mention self-determination but attribute a rationale about legitimizing Russian occupation to Brazil that is not in its statement. Peer revision removes that rationale, satisfying the attribution check, while also removing the explicit self-determination point required by the content rubric. The complete answer must be reviewed for both changes.

**India's aid wording becomes clearer without resolving its other gaps.** The peer revision separates humanitarian assistance to Ukraine from economic support to Global South countries. The earlier coordinated phrase was ambiguous, so this is not counted as a confirmed unmet-to-met correction. The answers still omit the food/fuel/fertilizer cost channels. The national-agent answers also claim the draft was submitted three days later, a submission date not established by India's speech. Correctly leaving a later vote unknown does not make every temporal claim in the answer valid.

**France illustrates why required content and unsupported claims need separate checks.** All four national-agent answers preserve the national capacity, non-recognition, continuing support, duration and unspecified financial amount. They also call the support “unconditional,” which the source does not establish. A response can cover all six requested content points while adding a material unsupported commitment.

**The central analyst appends a correction without resolving the contradiction.** Its first answer incorrectly says the UK rejected the US/Albania draft. The revision keeps that sentence and its invented later outcome, then appends that the UK supported the draft while calling the original analysis accurate. The draft-support criterion remains unmet. Searching for the word “supported” would misclassify this as a repair.

## Final synthesis is assessed separately

All three delivered final memos fail the source-supported-country-positions and source/time checks in this assistant review. The self and peer memos both stop at the opening of Brazil's section, before delivering that answer or proposed next steps. They are graded as delivered; an imagined continuation gets no credit.

The single-analyst memo finishes and receives credit for explicitly labeled proposals and a conditional implication about Brazilian recognition. It still reverses the UK draft position and invents a later outcome. Its two met synthesis units out of five do not establish that it is the better method overall. The two other summaries' truncation is part of the observed protocol failure; the separately prepared [format comparison](EVIDENCE_FORMAT_CHECKPOINT_20260928.md) gives all formats more room.

## Six decisions need adjudication

The 14 ambiguous rating instances reduce to six recurring decisions:

1. Whether “Global South nations” adequately preserves India's more specific “some of our neighbours in the global South.”
2. How to read a phrase coordinating multiple assistance types and multiple recipients.
3. Whether Brazil's procedural requirements are materially misattributed when described as outlined in the Charter rather than recommended by international practice.
4. Whether juxtaposing France's non-recognition and continuing support preserves the required support purpose without stating the connection.
5. Whether a military-control/current-participation explanation adequately captures Brazil's separate freedom-under-conflict concern.
6. When combining a fact from another country's supplied source becomes an unsupported attribution of the first country's rationale.

[Adjudication cards with answer/source excerpts](../data/review/deliberation-999389-ukraine-assistant-v1/adjudication-cards.md) make these concrete. They expose the assistant's uncertainties and are **not** a blinded second-review instrument. Independent reviewers should first use the [original unlabelled source-and-answer deck](../data/review/deliberation-999389-reviewer-kit-v1/review-deck.md), then compare decisions. The other ratings also require independent review; resolving these six questions alone does not validate the whole rubric.

No criterion was rewritten to force a numeric result. The full country-macro peer gain remains null because India's content transition is incompletely ratable. Climate remains unreviewed in this annotation set. The exposed evaluation answers and proposed corrections remain diagnostic material, not training-admitted examples for a later same-event comparison.

## Artifacts and checks

- [Machine-readable findings and paired denominators](../reports/deliberation-ukraine-assistant-review-20260928.json)
- [All 21 delivered answers with per-unit rationales and source navigation](../data/review/deliberation-999389-ukraine-assistant-v1/assistant-review.md)
- [Explicit annotations](../data/review/deliberation-999389-ukraine-assistant-v1/reviews.jsonl) and [annotation provenance checks](../data/review/deliberation-999389-ukraine-assistant-v1/annotation-audit.json)
- [Current scores](../data/review/deliberation-999389-ukraine-assistant-v1/scored-v2/scores.json) and [scoring receipt](../data/review/deliberation-999389-ukraine-assistant-v1/scored-v2/receipt.json)

The annotations bind to the exact outputs, cases, criteria and guidance. All **61 output excerpts and 78 source excerpts** were verified as literal spans. Identical outputs with the same rubric receive identical ratings. Span checks establish provenance, not the correctness of a semantic judgment.

This use of the scorer exposed two reporting gaps, now fixed: supplying a partial or assistant-only review no longer clears the semantic-review-pending flag; a known failed unit produces a failed strict result even if another unit is ambiguous. Completion coverage remains separate. **34 focused interaction/policy tests pass**, including those two cases. `scored-v2` supersedes `scored` for the known-failure rule; the annotation labels are unchanged.

The next decisions remain bounded: independently review/adjudicate the source rubric, run the prepared nine-case format comparison after SSH returns, freeze the evaluation configuration, and then execute the prepared technical training smoke test. This review adds concrete evidence for those decisions; it does not waive the evaluation-first gate.
