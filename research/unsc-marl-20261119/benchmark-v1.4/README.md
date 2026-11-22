# UN Deliberation Benchmark v1.4

This fixed benchmark measures whether access to a peer's note improves a
source-faithful UN Security Council decision record. It has five event
families, 11 episodes and 66 scored conditions. The headline comparison
is the peer-informed minus independent-drafts difference in released
final-record points, reported separately for historical reconstruction and
fictional workshops. Each track gives its event families equal weight and
averages both speaker orders. The pooled solo comparison, speaker-order
deltas, discussion scores and exact workshop decisions accompany that result.

**Start here.** Verify the frozen release with Python 3.10 or later. The
offline check needs only this directory and the standard library.

```bash
set -o pipefail
PYTHONDONTWRITEBYTECODE=1 python3 verify.py | cmp verification.json -
```

For a live run, follow [run and review](#run-and-review). For standalone
replays, use the [validity diagnostics](#validity-diagnostics-and-measured-status).

## Cases

| Track | Event family | Episodes | Main documentary distinction |
| --- | --- | ---: | --- |
| Historical reconstruction | Mali sanctions, S/PV.9408 | 1 | A veto versus insufficient affirmative votes |
| Historical reconstruction | Myanmar, S/PV.9231 | 1 | India's Council presidency versus its national abstention |
| Historical reconstruction | Residual Mechanism, S/PV.8295 | 1 | An abstaining member's rationale versus a nonvoting participant's objection |
| Fictional workshop | Iraq UNAMI, S/PV.9331 | 4 | Adopted deadlines versus options and mandates invented for the workshop |
| Fictional workshop | Syria cross-border aid, S/PV.9371 | 4 | The reasons two drafts failed versus authority to act in the workshop |

The [case packets](cases.json) include the evidence, ownership, instrument
links, cross-benchmark provenance, word caps and full rubric. UNBench supplies
draft and record coverage. Matching UNSC-Bench rows supply vote evidence
where available. The Myanmar row uses UNBench and official records because
the pinned UNSC-Bench audit found no match. Both tracks give the actor the
historical outcomes through its assigned evidence. The workshop decision is
fictional and mechanically keyed. All five families are public and exposed.
Treat these cases, their anchors and related work in the project as
development data. A transfer claim requires a separately locked,
family-disjoint set covering related drafts, translations and variants.
[UNBench](https://arxiv.org/abs/2502.14122v2) ·
[UNSC-Bench](https://aclanthology.org/2026.mme-main.10/)

## Comparison

| Arm | First note | Second note | Final writer sees |
| --- | --- | --- | --- |
| Independent drafts | Public packet and first desk evidence | Public packet and second desk evidence | Public packet and both notes |
| Peer-informed | Same first note as independent drafts | Public packet, second desk evidence and first note | Public packet and both notes |
| Pooled solo | All evidence | All evidence and the analyst's own first note | All evidence and both notes |

Run both desk orders. The reference protocol uses one fixed model and
decoding configuration across all three arms, 100 output tokens per
working note and 280 for synthesis. Notes target 55 words. The final word
cap is case-specific. The causal comparison within each order changes
second-desk visibility while using the exact same opening note and chair
configuration. The input-token cost of seeing a peer note is part of this
intervention. The full-information solo has the same call count and output
ceilings and can consume more input tokens. Record measured input and
output usage and both orders. A family win across orders requires a strictly
positive mean difference in each order.

For trained/frozen comparisons, run the same matrix for each and retain
checkpoint, role and reviewer identities in the run record. A chair-only
swap measures synthesis from delivered information. A delegate-only swap
holds the final writer fixed. Use fixed delivery as a control when making a
claim about a learned communication policy. The 66 conditions form the
fixed documentary suite. Different graphs, turn limits and partner
populations define separate experiments. For an adaptive-routing claim,
include a fixed-policy control with the same legal actions and visibility.
If a fixed request is suppressed because its card is already present, the
suppression itself can reveal the chair's state through whether a request
arrives. Give the control's responder that same observation and allow it to
optimize its reply.

## Scoring contract

**Final record out of 70.** The [final judge](final-judge.md) scores the
disposition, operative terms, attributed positions and reasons, unresolved
issues and limits of authority. Case-specific weights are frozen. The judge
sees the answer and sources without model or arm labels. A met item needs an
exact answer span and exact source span. Uncertain items contribute only to
the raw upper bound. Material falsehoods, misattributions, invented
agreement or invented authority fail the guard. Omissions lower coverage.
The release score is the raw lower bound if the guard clears and the final
is complete, nonempty, within its word cap and mechanically correct where
required. Otherwise it is zero. The report gives raw bounds, release
blockers and strict pass. Strict pass requires a released 70.

A workshop answer starts on its first nonempty line with one exact
`Decision: A`, `Decision: B`, `Decision: C`, `Decision: D` or
`Decision: IMPASSE` header as applicable. A second decision header fails
the format check. `Decision: UNRESOLVED` records a deferral and does not
satisfy the complete-world task. Judge the remaining prose against the
rubric even when the header fails. Mechanical accuracy, agreement recall, impasse recall and their mean
(balanced accuracy) remain visible beside documentary coverage. The
complete-world rule accepts any menu option meeting both mandates. It
accepts impasse if the intersection is empty.

**Discussion up to 30.** The [process judge](process-judge.md) assigns
0, 2 or 5 to each of two items under key points, arguments and interactions.
It credits notes with substantive evidence and reasons, then follows a
specific correction or qualification into the final. The transcript gives
the judge speaker, source access and directed note visibility. Interaction
is unavailable for independent drafts and pooled solo. Keep the three
dimension scores separate from the headline outcome. The idea ledger counts
distinct propositions, source-supported ideas per speaker, independent
introductions, cross-role recurrence, supported ideas retained in the final
and unsupported final claims. Each occurrence is marked asserted, rejected
or mentioned. Retention and unsupported final claims require an assertion.
Recurrence describes what was said and can be paired with the
independent-drafts control to check whether the idea appeared without
exposure. Speaker
turns, cap hits, completion and usage come from the run logs.
[Discourse Quality Index](https://content.csbs.utah.edu/~burbank/steenbergen2003.pdf) ·
[Decision-Oriented Dialogue](https://aclanthology.org/2024.tacl-1.50/) ·
[MultiAgentBench](https://aclanthology.org/2025.acl-long.421/)

## Worked workshop record

The alternate Syria impasse world accepts either C or D because both
fictional mandates require six months and leave the oversight choice open.
Here is an example selecting C.

> Decision: C
>
> Neither historical draft passed. Brazil and the UK supported S/2023/506,
> which failed 13–1–1 on Russia’s veto. On S/2023/507, Brazil abstained
> and the UK voted no. That draft failed 2–3–10 for insufficient affirmative
> votes. Both fictional delegates require six months. Package C recommends
> six months of cross-border and cross-line access with an extra review
> checkpoint. That checkpoint is a package choice. The workshop neither
> renews the historical authorization nor records a new official vote.

The final judge can cite `S1` for the two outcomes and attributed votes,
`S2` for the lack of renewal, the two mandate blocks for the six-month
overlap, and `menu` and `scope` for the proposed action and its limits.
A record choosing D would specify ordinary reporting instead.

## Run and review

Run from this directory with fresh output locations. Before generation,
record the actor and judge revisions, decoding settings and the planned
primary comparison. For a training comparison, identify the training data
and which component changes, then save all three arms from both checkpoints.
Model runs use a persistent adapter that reads
one request per line and writes one response per line. Each request has
`messages` and `max_output_tokens`. Each response has `text`,
`input_tokens`, `output_tokens` and `termination` (`complete`, `cap` or
`error`). Use stderr for logs. Treat requests as independent. The actor sees
only the emitted messages and the judge sees only its rendered packet.
Use an adapter config like
`{"model":"pinned revision and decoding settings","command":["python3","/path/to/adapter.py"]}`.
Keep credentials outside the config and the prompts.

```bash
python3 calibrate.py > final-anchor-packets.json
python3 calibrate.py --mode process > process-anchor-packets.json
python3 run_suite.py collect actor.json actor-run
python3 run_suite.py judge judge.json judge-run --input actor-run/episodes.jsonl
python3 review.py packets actor-run/episodes.jsonl > review-packets.json
python3 review.py extract judge-run/validated.jsonl > judge-marks.json
python3 review.py compare actor-run/episodes.jsonl judge-marks.json reviewer-marks.json > agreement.json
python3 review.py apply actor-run/episodes.jsonl resolved-marks.json > resolved-report.json
```

Collection logs 198 logical turns and uses 176 calls by sharing openings.
Judging logs 132 logical verdicts and can reuse identical packets. It reads
all final packets first, ordered by opaque packet ID, then all transcript
packets in the same manner. Raw adapter responses are saved before semantic scoring. The judge runner
records malformed or incomplete verdicts and continues through the matrix.
It emits a comparison only when every condition is validated. The review
comparison reports exact score agreement and whether the readers disagree on
the direction of the peer effect for either baseline, overall by track and
by family and order. See [review procedure](REVIEW.md) for calibration and
the independent reading and adjudication formats.

## Validity diagnostics and measured status

- Run `python3 information.py` for the exact decision ceilings in both
  workshop families. Each crosses two mandates from each desk into four
  equally weighted worlds. With only public evidence the ceiling is 50%.
  It is 75% with desk 1's card, 50% with desk 2's, and 100% with both.
  Compatible worlds can allow several options. The oracle gets credit for
  any accepted action and therefore includes strong shortcuts such as
  answering with the same package across worlds. The ceilings describe
  information on the assigned cards. They are separate from empirical
  accuracy and apply before information is relayed through the notes.
- Run `python3 action_contrasts.py tasks` for seven supplementary action-rule
  contrasts in 22 package permutations. Use `key` for evaluator-only labels
  and `checks` for mechanical baselines. The rule first excludes any grade
  of zero, then maximizes the worse-off grade, then maximizes the total.
  Carry every tied option forward. Intersect the winners across compatible
  worlds, using `impasse` for a world with no feasible options and
  `unresolved` when no action is common to every world. Report per-contrast
  selected-action and exact-set accuracy separately from the documentary
  suite. Save a JSON array with `id`, selected `choice` and complete
  `choices` for each task, and score it with
  `python3 action_contrasts.py score --responses answers.json`.
  The full rule reproduces 22/22 exact sets, versus 20/22 for a
  sum-only rule and 8/22 for first feasible.
- Run `python3 replay.py` to reproduce the bundled 12 archived Syria finals
  and prior assistant annotations. All 12 missed the exact workshop
  decision. Independent, peer and solo raw coverage sums are 0, 70 and 56.
  Released totals are zero for all three.

The [manifest](release.json) pins the package and the
[receipt](verification.json) records software verification. v1.4 keeps the
v1.3 cases, actor prompts, scoring rules and archives. It adds an authored
full-credit target for every episode, opaque judge scheduling and
reader-sensitivity reporting. The targets provide calibration material.
The archived Syria replay is the included model-quality evidence and uses
prior same-assistant marks. Independent judge reliability and transfer to
unseen event families remain unmeasured.
