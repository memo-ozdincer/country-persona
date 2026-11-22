# UN Deliberation Benchmark v1.1

This fixed suite asks whether access to a peer’s note improves a source-faithful
Security Council decision record. The primary outcome is the **released final
record score out of 70**. The transcript shows which arguments were made, who
contributed each supported idea, and what survived into the final record.
Workshop cases also have exact decision keys.

## Cases and evidence

| Track | Event family | Episodes | Documentary challenge |
| --- | --- | ---: | --- |
| Historical reconstruction | Mali sanctions, S/PV.9408 | 1 | Distinguish a veto from insufficient affirmative votes. Attribute each draft and its approach to expert monitoring. |
| Historical reconstruction | Myanmar, S/PV.9231 | 1 | Distinguish India's procedural role as Council president from its national abstention. Preserve the reporting deadline and ASEAN's role. |
| Historical reconstruction | Residual Mechanism, S/PV.8295 | 1 | Preserve the appointment, vote, abstaining member's reasoning and nonvoting participant's separate objection. |
| Fictional workshop | Iraq UNAMI, S/PV.9331 | 2 | Separate the adopted deadlines from invented workshop conditions. Find a compatible package or explain the impasse. |
| Fictional workshop | Syria cross-border aid, S/PV.9371 | 2 | Distinguish both unsuccessful drafts and correctly resolve the fictional workshop without inventing Council authorization. |

The [case packets](cases.json) contain dated source blocks, ownership, official
source locations, case-specific criteria and workshop answer keys. Iraq and the
Residual Mechanism join matching native vote labels. Mali and Syria use
UNBench's all-drafts archive with official and UNSC-Bench outcome evidence as
available. Myanmar uses UNBench and the official record. The historical tasks
supply the actual outcomes and test reconstruction. Workshop mandates and
package menus are fictional. [UNBench](https://arxiv.org/abs/2502.14122v2) ·
[UNSC-Bench](https://aclanthology.org/2026.mme-main.10/) ·
[Cross-benchmark join audit](../crossbench/README.md)

The 5 families, 7 episodes and 42 scored conditions constitute the complete
fixed suite. All five families are exposed. Keep all versions of an event
together when assigning splits, including nearby resolutions on the same
decision, translations, speaker orders and altered constraints. Use the
[development kit](../benchmark-kit/README.md) for task and policy development.
Log any family used for fitting, prompt tuning, checkpoint selection or reward
design. Use a separately locked, family-disjoint evaluation set to substantiate
transfer claims. The [running research notes](../../../BENCHMARK.md) record
the evidence and diagnostics behind this release.

## Protocol

Each episode uses two note calls and one synthesis call. Run each arm in
both speaker orders. Use the same actor checkpoint and decoding settings in
all roles for the frozen reference. Use 100 output tokens per note and 280
for synthesis. Notes target 55 words, and final word caps are in the case
packets. Record the actual token counts and completion state for every turn.

| Arm | Notes | Source access at synthesis |
| --- | --- | --- |
| Independent drafts | Each desk receives the public packet plus its own evidence | Public packet and both notes |
| Peer-informed | Same opening note as independent drafts. The second desk also sees that opening | Public packet and both notes |
| Pooled solo | One analyst makes two passes with all source blocks. Its second pass sees its own first note | All source blocks and both notes |

The peer comparison holds the opening, final writer, call count and output
ceilings fixed. Compare peer-informed with independent drafts to estimate the
effect of making the opening note visible to the second desk under this
protocol. The pooled solo arm is a full-information baseline and may consume
more input tokens. Peer visibility can also increase input usage versus
independent drafts. The report keeps exact token differences alongside score
differences. A family-level win holds across order when both family deltas
are strictly positive. Report agreement and impasse separately and retain
every episode, including errors. Family means receive equal weight within
each track. With five exposed families, report descriptive results.

For a MARL comparison, pair trained and frozen runs with the same case
projection, turn schedule, reviewer and budgets. Record which roles changed.
A chair-only swap tests synthesis. A delegate-only swap with the same chair
tests what the notes provide. A fixed-delivery control tests how much of a
gain can be explained by supplying the relevant evidence. The
[action-rule contrasts](../benchmark-kit/validity-audit/README.md) test
shortcut policies independently of the documentary score. The record score
can be used for evaluation with any training method.

## Scoring

**Final record, 70 points.** Apply the case-specific weights to the
disposition, operative terms, attributed positions and reasons, remaining
disagreements, and authority. The [final judge](final-judge.md) sees the
answer, rubric and numbered evidence. It grades each criterion met, unmet
or uncertain and supplies exact supporting spans. The guard checks the
whole answer for material fabrications, misleading attributions, invented
agreement or authority, and unreliable scope. An omission lowers coverage.
An uncleared guard, empty final, token truncation, generation error,
excess words or wrong workshop decision yields zero released points.
Report lower and upper raw coverage, guard disposition, release and strict
pass alongside the primary score. The strict pass requires release and all
70 points. The exact workshop decision score checks the first nonempty line
and completion, independently of source coverage.

**Discussion, 30 points.** The [process judge](process-judge.md) scores
key points, arguments and interactions out of ten each, with two 0/2/5 items per
dimension. It judges reason-giving and treatment of disagreement in the
working notes, then tracks supported uptake through to the final. It
records all distinct ideas and the supported subset per speaker, independent introductions,
cross-role recurrence, surviving ideas and unsupported final claims.
Repeated propositions count once in the episode ledger. Recurrence is an
observable trace. Use the paired record delta to evaluate the effect of peer
visibility. The report gives interaction as unavailable for independent
drafts and pooled solo. Retain turn counts, cap hits and token use as
diagnostics. [Discourse Quality Index](https://content.csbs.utah.edu/~burbank/steenbergen2003.pdf) ·
[Decision-Oriented Dialogue](https://aclanthology.org/2024.tacl-1.50/) ·
[MultiAgentBench](https://aclanthology.org/2025.acl-long.421/)

## Run and review

Python 3.10+ and a model adapter are sufficient. The adapter reads a JSON
object per line on stdin and emits one JSON object per line on stdout.
Requests carry `messages` and `max_output_tokens`. Responses carry `text`,
`input_tokens`, `output_tokens` and `termination` (`complete`, `cap` or
`error`). Log to stderr. Treat each request independently. Give the actor
only the emitted messages. Give the judge only its rendered prompt. Keep
keys and adapter credentials outside these contexts. Pin actor and judge
model revisions and decoding settings in their configs. A config is a JSON
object with `model` (the model and decoding identifier) and `command`
(an argument list to launch the adapter).

Run from this directory with fresh output directories.

```bash
python3 verify.py
python3 run_suite.py collect actor.json actor-run
python3 run_suite.py judge judge.json judge-run --input actor-run/episodes.jsonl
python3 review.py packets actor-run/episodes.jsonl > review-packets.json
python3 review.py extract judge-run/validated.jsonl > judge-marks.json
python3 review.py compare actor-run/episodes.jsonl judge-marks.json reviewer-marks.json
python3 review.py apply actor-run/episodes.jsonl resolved-marks.json > resolved-report.json
```

The collector logs 126 logical turns and calls the adapter 112 times by
sharing matched openings. The judge logs 84 logical verdicts and can reuse
identical packets. It saves raw outputs before validation. A malformed
verdict stops scoring and leaves raw evidence for review. The report
requires all arms, cases and orders. `evaluate.py next tribunals peer 0`
renders a single actor request.

Export the [authored judge anchors](anchors.json) with `python3 calibrate.py`.
Send the emitted packets with the final judge prompt. Save each full
verdict under its opaque packet ID and run
`python3 calibrate.py --verdicts anchor-marks.json`. Audit disagreements,
especially false clears on authority, attribution or votes. The anchors
cover ten examples and are exposed checks of judge behavior. A completed
judge pass alone produces a provisional report.

Give an independent reader the blinded packet file and the two judge
prompts. Have them return a JSON object with `final` and `process` maps from
packet ID to full verdict. Lock both readings before comparing them. The
comparison lists criterion, guard, release, process-rating and idea-count
disagreements. Review different idea assignments even when their counts
agree. Save both original readings and a resolved verdict file with reasons
for each adjudication. Validate spans and eligibility with the scorer.
Semantic support and the reliability of a judge require independent review.
[LLM judge bias study](https://arxiv.org/abs/2306.05685)

## Verification and release history

The [release manifest](release.json) pins the cases, instructions, scorer,
report and verification. [Verification](verification.json) exercises the
full matrix with software fixtures. The [Syria replay](replay.json) uses
12 archived frozen Qwen3.5-4B finals and prior assistant annotations.
All 12 missed the exact decision. Independent, peer and solo raw coverage
sums were 0, 70 and 56. Released totals under v1.1 are zero for all three.
The pooled solo total was 56 under the [v1.0 release](../benchmark-v1/README.md),
which allowed prose points through when the decision was wrong.
The replay reuses the original outputs and marks. Independent judge
reliability and unseen-family generalization remain unmeasured.
[Archived Syria experiment](../benchmark-v1-runs/syria-baseline/README.md)
