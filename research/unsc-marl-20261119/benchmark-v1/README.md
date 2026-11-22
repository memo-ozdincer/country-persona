# UN Deliberation Benchmark v1.0

A fixed comparison of three ways to write a decision record from UN material.
The benchmark measures whether a visible peer note improves the final record
and traces what survived from the discussion. The workshop track also tests
whether teams find a compatible proposal or correctly report an impasse.

## Frozen cases

| Track | Event family | Episodes | What a record must get right |
| --- | --- | ---: | --- |
| Retrospective | Mali sanctions, S/PV.9408 | 1 | Distinguish a veto from insufficient affirmative votes across two drafts. Preserve sponsors and competing monitoring proposals. |
| Retrospective | Myanmar, S/PV.9231 | 1 | Separate India's Council presidency from its national abstention. Preserve the vote, reporting deadline and ASEAN role. |
| Retrospective | Residual Mechanism, S/PV.8295 | 1 | Attribute the 14–0–1 vote, the operative appointment, a voting member's concerns and a non-voter's request in their proper capacities. |
| Workshop | Iraq UNAMI mandate and review, S/PV.9331 | 2 | Separate the historical deadlines from a proposed package. Identify compatibility or impasse under the two fictional mandates. |
| Workshop | Syria cross-border aid, S/PV.9371 | 2 | Distinguish the two unsuccessful historical drafts and identify compatibility or impasse without creating new authority. |

The [case packets](cases.json) bind dated source blocks, source ownership,
official links, role names, word caps, adjudication criteria and simulated
answer keys. Iraq and the Residual Mechanism join UNBench author-test rows
to UNSC-Bench with matching vote labels. Mali and Syria use the UNBench
all-drafts archive for draft linkage, with official and UNSC-Bench outcome
evidence as applicable. Myanmar uses UNBench and the official record. The
date, source links and exact join scopes are recorded per family. The source
blocks use curated paraphrases. Private instructions in the workshops are
fictional. The release is an exposed, fixed evaluation suite. Its small
family count and public keys limit generalization claims.

## Paired comparison

Every episode uses two note calls and one final call. Each is run in both
speaker orders with a frozen checkpoint, decoding configuration, 100-token
note ceilings, and a 280-token final ceiling. Notes target 55 words. The final
word cap is case-specific. Count all input and output tokens for the
counterfactual per-episode cost even if identical opening calls are reused
in the experiment. Keep invalid or capped generations in the record.

| Arm | Notes | Final writer |
| --- | --- | --- |
| Independent drafts | Two role-local notes, each written from its own source blocks | Public blocks and both notes |
| Peer-informed | The same opening note as independent drafts. The second desk also sees that opening | Public blocks and both notes |
| Pooled solo | One analyst with all source blocks makes two passes in the declared order. The second pass sees the first note | All source blocks and both notes |

The source allocation is fixed. The peer arm gains one visible note without
adding a call. It can still use more input tokens. The pooled analyst is the
full-information solo control. Treat a positive peer effect as robust to
speaker order only if the family-level effect is positive in both orders.
Preserve per-case scores so that a family mean cannot hide losses on
impasse. Family counts are the units for claims about generalization.
Report each track separately. Native vote prediction requires a separate
release using outcome-blind inputs. The v1 retrospective packets include
the historical vote.

## Rubric and judge

**Final record, 70 points.** Use the frozen case weights for disposition,
operative terms, actor-specific positions and reasons, unresolved issues and
authority. The [final judge prompt](../judge/instructions.md) receives
the answer and numbered evidence, without the transcript or treatment.
Every met criterion requires a quoted response span and source support.
Grade each item met, unmet or uncertain. The scorer reports lower and upper
coverage, a strict pass, and released lower-bound coverage. A fabricated
vote, material unsupported claim, invented common position, confused
authority, uncertain guard, truncation or excess words withholds release.
Release failure scores zero **released** points. Raw coverage remains visible.
Workshop exact decision accuracy is computed separately from the first
nonempty line, including a completeness and word-cap check. Partial credit
for prose is separate from mechanical acceptance.

**Discussion, 30 points.** The [process judge](process-judge.md) scores
key points, arguments, and interactions out of ten each using two criteria
per category. It also returns an atomic idea ledger. The scorer validates
quoted spans and actual visibility, reports supported ideas by speaker,
distinguishes independent introductions from cross-role recurrence, and
counts retained supported ideas and unsupported ideas in the final.
Interaction is structurally unavailable in independent and pooled arms.
Compare final records on the common 70-point scale. Report process
components beside that score rather than treating interaction availability
as a quality penalty. A solo revision does not count as peer engagement.

**Judge calibration.** Before publishing a model comparison, use masked
authored anchors, hold strong clauses fixed while editing one objection or
authority claim, and double-code a sample across all cases, orders and arms.
Report per-item agreement and guard disagreement separately, retain
uncertain judgments, and adjudicate material discrepancies with a second
reviewer. The validator checks exact quotes, fields and visibility.
Semantic support still requires judgment. Use the [existing calibration
anchors](../judge/calibration.json) and [local judge audit](../judge/model-calibration/replay.json)
as starting points. Judge reliability on this exact suite still needs an
independent double-coded sample.

## Run

Python 3.10+ and a model adapter are sufficient. The adapter is a persistent
process. It reads one JSON object per line from stdin and writes one JSON
object per line to stdout. Send logs to stderr. Each request supplies
`messages` and `max_output_tokens`. The response has exactly
`text`, `input_tokens`, `output_tokens`, and `termination` where termination
is `complete`, `cap`, or `error`. Use the recorded provider token counts.
For the judge, put the verdict JSON object in the response's `text` field.
Keep adapter credentials in the environment. Record the exact actor and
judge model revisions and decoding settings in their configs.

An example config is `{"model":"checkpoint and decoding configuration","command":["python","/path/to/adapter.py"]}`.
Run from this directory with distinct new output directories.

```bash
python check.py
python run_suite.py collect actor.json /path/to/actor-run
python run_suite.py judge judge.json /path/to/judge-run --input /path/to/actor-run/episodes.jsonl
```

The collector makes 112 physical calls for 126 logical turns by sharing the
first note between the independent and peer arms. It logs the actual request
and response for every turn. The judge stage saves raw verdicts before
validation, with 84 requested verdicts in a complete run. An invalid judge
verdict interrupts automated scoring and leaves raw response and valid
preceding rows intact. After adjudication, `python report.py records.json`
accepts a JSON array of reader-checked episodes with `id`, `calls`, `final`,
and `process` as in `validated.jsonl`. Incomplete comparisons are rejected.

Use `python evaluate.py next tribunals peer 0` to inspect or run a single
episode. Provide each previous reply with the returned `request_sha256`
and adapter response fields in a JSON list via `--calls`. Invoke
`evaluate.py final … --calls calls.json` and
`evaluate.py process … --calls calls.json` to obtain judge requests.
Add `--verdict verdict.json` to score. The environment, including the case
file and verdicts, stays outside the agent context. Only the emitted
`messages` reach an actor or judge.

## Evidence behind the release

- The [verification receipt](verification.json) exercises the complete
  42-episode reporting matrix with authored fixtures. It checks the private
  projection, decision keys, paired openings, quote rejection, cap handling
  and process visibility. It establishes software behavior.
- The [speaker-order crossover](../benchmark-kit/reader-use/chair-brief-crossover/README.md)
  is an exposed frozen-model reference from the Gulf of Guinea and Libya.
  Peer-informed notes help the final brief in both Gulf orders and tie in
  both Libya orders. Those dockets motivated the order control.
- The [Resolution 2422 routing and writer transfer](../benchmark-kit/reader-use/tribunals2422-transfer/README.md)
  tests the effect of changing source availability under fixed routing maps.
  It is a separate diagnostic on a v1 family. The literal assembly gains do
  not survive the frozen writer under either source order. It justifies
  reporting evidence delivery, final retention and authority separately.
- For research context and the evolution of the protocol, see [BENCHMARK.md](../../../BENCHMARK.md).
  Its running experiments have their own versioned criteria and remain
  diagnostic evidence. The files named in [release.json](release.json) define
  the v1.0 contract. Keep changes to cases, judge or scoring in a new release.
