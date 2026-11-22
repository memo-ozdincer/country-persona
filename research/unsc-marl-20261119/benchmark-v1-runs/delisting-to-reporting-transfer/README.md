# Transfer the 2744 policy to Resolution 2739

Reusing the frozen sender and reply weights by position loses to
arrival-only at both price grids. Rebinding the actions to document
roles and choosing the higher-value standalone reply after silence
restores the receiver. Blocking an opening that only repeats public
information gives a **0.312-point advantage over arrival-only at lower
prices**. At the original prices, the same pair loses by **1.814
points** because its sender attempts too many deliveries.

| Receiver and sender on 2739 | Original prices | Lower prices |
| --- | ---: | ---: |
| Frozen policy by position | 33.372 | 35.527 |
| Semantic action binding | 32.665 | 37.332 |
| Semantic binding with silence fallback | 35.425 | 38.836 |
| Above plus local novelty filter | 35.958 | **40.036** |
| Best arrival-only | 37.772 | 39.724 |
| Target-optimal sender with the transferred receiver | 37.772 | 40.084 |
| Content-aware oracle | 37.772 | 40.084 |

The original grid uses send prices of 8, 11 and 15. The lower grid
uses 1, 3 and 5. Each crosses two private-view priors and four
delivery rates in both directions for 96 conditions. The receiver
chooses the sponsors' reason when Algeria's full note establishes a
shared reporting purpose. It chooses the operative reporting
extension after a partial note or silence. The semantic binding and
silence rule are specified explicitly. The resulting actions are
also reproduced by a hand-written rule that chooses the matching
reply on a positive signal and the standalone reply otherwise.

At lower prices the novelty-filtered pair beats arrival-only in 80
of 96 settings and is 0.048 points short of the oracle on average.
At the original prices it spends 5.400 points, compared with 0.717
for the target-optimal sender. Optimizing only the sender against the
target outcomes closes the remaining gap to the content-aware oracle
at both grids. That arm uses target outcome information.

The policy weights come from the 2744 training fit. No fitting on
2739 is used for the frozen comparison. The action bindings and
novelty test use the known evidence schema and rubric weights. The
base experiment replays the archived verifier outputs, uses a typed
final record and scores a single previously exposed docket. It
shows where the transfer succeeds under supplied semantics and
where forwarding costs prevent it.

[Locked mappings](plan.json) · [All 192 settings](results.json) ·
[Donor policy](../delisting-2744/README.md) ·
[Target source and reward bank](../value-routing-docket-transfer/README.md)

## Stress test the receiver's input wording

A fresh frozen Qwen3.5-4B worker reproduced all six original logits
exactly and scored six paraphrase or attribution requests. The full
Algeria note remained positive. A faithful objection-only paraphrase
raised the averaged margin from **−0.125 to +0.500**, despite still
omitting any endorsement of continued reporting. This routed the
note to the sponsors' rationale and enabled a false shared-purpose
sentence. The rubric properly releases zero for that receipt
combination. Lower-grid utility fell from **40.036 to 35.404**, while
the re-optimized arrival-only control scored **39.700**. Correcting
the older vote-only input from the truncated speaker prefix
“Mr.” to “Algeria abstained on the draft” preserved its negative
classification and left the policy scores unchanged.

Requiring both label mappings to support the proposition repairs
the tested wording failure without extra calls. The two margins on
the paraphrased objection were −0.75 and +1.75, while both margins
were positive for the full note. As a post hoc replay, this restores
40.036 to the pair and 39.724 to arrival-only at lower prices.
Applying the same rule to the older source bank on the 2744 donor
rejects the valid A3+ relation. On that bank it changes donor utility
from 40.565 to 39.039, below the 39.457 arrival-only score. The stricter
rule trades false positives for false negatives across the two
cases. These are two exposed dockets and one model checkpoint.

The 12 label evaluations used an eight-thread AMD EPYC 9575F 64-Core
Processor worker. Only early-source margins were recollected. Late
verification and the typed renderer are inherited from the target
archive. No backbone or policy updates occurred.

[Wording protocol](wording/protocol.md) · [Exact prompts](wording/plan.json) ·
[Verified logits](wording/verified.json) · [Policy replay](wording/results.json) ·
[Agreement and donor sensitivity](wording/agreement.json)

Run the following from this directory using the Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B transfer.py --plan | cmp plan.json -
python -B transfer.py | cmp results.json -
(
  cd wording
  python -B wording.py plan | cmp plan.json -
  python -B wording.py verify | cmp verified.json -
  python -B wording.py score | cmp results.json -
  python -B agreement.py | cmp agreement.json -
)
```
