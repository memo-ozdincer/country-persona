# UN deliberation benchmark and MARL handoff

**Benchmark v1.7 is closed.** The portable archive contains 23 files,
including case packets, judge instructions, calibration anchors,
the runner, and the scoring and review tools. Python 3.10 or later
and the standard library suffice for offline verification. Live
evaluation uses the actor and judge adapters described in the guide.
[Download v1.7](un-deliberation-benchmark-v1.7.zip) ·
[Read the release guide](benchmark-v1.7/README.md)

## What the benchmark measures

The suite crosses 11 episodes from five UN event families with three
conditions and both desk orders, for 66 scored conditions. The main outcome
is the difference in released final-record points between peer-informed
drafting and independent drafts. Pooled solo supplies a second control.
Historical reconstruction and fictional workshops are reported
separately, with equal weight per event family. The final rubric assigns
up to 70 points to source-faithful content. The transcript review reports
key points, arguments, interactions, turns, and distinct ideas per speaker
separately. Workshop decisions also have exact answer keys.
[Case packets](benchmark-v1.7/cases.json) ·
[Final-record rubric and judge](benchmark-v1.7/final-judge.md) ·
[Transcript rubric and judge](benchmark-v1.7/process-judge.md)

## What the MARL experiments establish

| Test | Result | Scope |
| --- | --- | --- |
| Live routing on Resolution 2744 | The learned reply gained **2.304 points** over optimized arrival-only under each tested note distribution. | Fresh model calls across 48 weighted delivery branches. Both policies attempted every opening. The learned reply used 345–793 additional expected input tokens per episode. [Evidence](benchmark-v1-runs/delisting-live-routing/README.md) |
| Train both desks against the compact writer’s scores | Utility rose from **38.539 to 40.411**, against **39.384** for optimized arrival-only. With the topic-guided writer, the same policy dropped to **22.852** against **37.168**. | Archived model outputs on one exposed docket. Sender adaptation accounted for the gain over the earlier fit. [Evidence](benchmark-v1-runs/native-reward-routing-fit/README.md) |
| Transfer sender values across three dockets | The factored sender matched the oracle on **576 of 576** canonical settings. The unfitted rubric formula made the identical decisions. | Supplied scoring metadata explains the canonical performance. An objection paraphrase that misled the verifier erased the advantage on 2739. [Evidence](benchmark-v1-runs/sender-value-family-transfer/README.md) |
| Recalibrate after a writer change | Two scored probes preserved the compact writer’s useful comparisons and cleared guard failures on two alternative writers through the source-only fallback. | Exact archived inputs and one modeled writer-use fee. [Evidence](benchmark-v1-runs/writer-change-calibration/README.md) |

The supported claim is that learned routing can improve source-bound
records under controlled delivery and a calibrated writer. Independent
judge reliability, transfer to unseen event families, and improvement
in free-form deliberation remain open. The public benchmark includes
a replay of 12 archived Syria briefs. All missed the exact workshop
decision and earned zero released points. Software verification and
authored judge anchors measure runner correctness and calibration
coverage separately from model quality.
[Benchmark verification](benchmark-v1.7/verification.json) ·
[Syria replay](benchmark-v1.7/replay.json) ·
[Running research notes](../../BENCHMARK.md)

A live calibration of the frozen Qwen3.5-4B judge produced three
usable final verdicts out of 21 and zero process verdicts out of
four. One usable final verdict still cleared a false claim of
official authorization. [Live judge calibration](benchmark-v1-runs/live-judge-calibration/README.md)

## Verify the archive

Extract the archive and run these commands inside its top-level directory.

```bash
set -o pipefail
python3 -B verify.py | cmp verification.json -
python3 -B replay.py | cmp replay.json -
```

Both receipts matched byte for byte from an isolated extraction on
Python 3.12.3. The archive is 61,440 bytes. Its SHA-256 is
`fca0d38277fffd95daefa9acb8eb2eaa18ec07afb301539eaa7a8dbaa1fa3a26`.

## Reward attribution on the tribunal action bank

Replacing only the factual guard with an isolated Qwen label produced
apparent peer gains of +3.22 and +4.85 points at the fitted availability
rate. Both gains were zero against archived review. Three unsupported
voting rosters and two uncertain attributions passed both label mappings
and contributed positive reward. This connects guard errors to learned
message selection under a fixed writer and archived rubric marks. The
next informative MARL comparison needs reviewed peer headroom and a
source-bound scoring check, with an independent exact rule as a control.
[Reward attribution study](benchmark-v1-runs/guard-reward-selection/README.md)

## Single-trajectory credit on Resolution 2744

A receipt-value estimator with decentralized control achieved all 96 exact
compact-writer optima after 256 simulated terminal scores per arm. The
peer route averaged 40.4205 net, above 39.3838 for best arrival-only and
38.5390 for the fixed rubric route. The held topic-guided writer erased
the gain, reducing the frozen peer policy to 22.6755. This uses reviewed
deterministic records and known delivery probabilities. It establishes a
working one-trajectory update in the simulator. The next test is whether
it can safely regain useful cooperation after a writer change, with new
feedback and a source-only fallback.
[Training traces and verification](benchmark-v1-runs/terminal-feedback-routing/README.md)

## Refresh after writer shifts

On 2744, the screened peer learner reached 38.241 in a mixed writer
pool, against an exact arrival-only ceiling of 38.076 and a stale
frozen score of 31.548. The cache keyed exact reviewed records and
source prefixes, and fell back on novel drafts. Bounding exploration
improved realized utility in the mixed phase but left the topic-only
phase below source-only after review costs. Replay verified 1,536
simulated episodes using two fixed writer banks and an announced change.
The missing end-to-end test is a new event family with reviewed positive
peer headroom, fresh writer outputs and an independently reviewed
reference.
[Refresh and exploration replay](benchmark-v1-runs/writer-refresh-feedback/README.md)

## Resolution 2417 prospective chair check

The new docket supports a documentary distinction concerning possible
sanctions and another concerning regular reporting and swift alerts.
Frozen Qwen3.5-4B earned zero complete comparisons in 12 fresh
outputs. An adaptive scope instruction recovered one canonical
comparison in 12 more calls. With only one productive reply, reviewed
peer headroom remained zero and sender fitting did not start.
Substituting the registered US comparison alone restored 1.108
points. This narrows the missing transfer component to faithful
rendering of both relationships, with independent review still open.
[Fresh outputs and rubric replay](benchmark-v1-runs/hunger-2417-transfer/README.md)

## Witness-based assembly on 2417

Evidence selection recovered US reporting in both source orders.
Exact-register completion of missing sanctions witnesses preserved the
second relationship. The one-trajectory peer fit reached 40.565 at
1,024 scores, above the 39.457 arrival-only ceiling. The unfitted
registry reached the same 40.565. Use registry-only assembly when
all required claims are registered. Fresh, independently reviewed
records with an incomplete register are the test for semantic selection,
and transfer remains open for learned routing beyond the fixed rule.
[Released records and verified training replay](benchmark-v1-runs/hunger-2417-transfer/witness-routing/README.md)

## Text-only policy transfer onto 2417

Donor-only learning reaches 39.859 on the original cards and 37.504
on held paraphrases, compared with the 39.457 arrival-only bound.
The fixed semantic rule reaches 40.565 and 39.728. Component swaps
separate poor send valuation on the original cards from reply
selection under paraphrase. The reference still assumes a screened
source-bound writer. [Policy and leakage audit](benchmark-v1-runs/text-only-routing-transfer/README.md)

## Relative choice on text-only routing

Showing both replies and a neither option at once recovered the exact
2417 peer routing score on original and paraphrased cards. Donor-only
probability calibration fell below fixed hard routing. Three of four
fictional controls and five of eleven donor views were still missed.
This identifies a simpler observation baseline and a clear failure
mode for the next held-docket test. Target pairing labels are excluded
from policy fitting.
[Reproducible relative-choice study](benchmark-v1-runs/relative-routing-transfer/README.md)
