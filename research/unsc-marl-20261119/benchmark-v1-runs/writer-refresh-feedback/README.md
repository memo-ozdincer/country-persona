# Refresh learned routing after a writer change

On Resolution 2744, an online receipt-value policy with an exact-record
review cache recovered useful peer routing in a mixed-writer simulation.
The final mixed-phase policy scored **38.241** net points, above the
**38.076** exact arrival-only ceiling and the **37.242** optimized
source-only route. The stale compact policy with approvals tied to pairs
scored **31.548**. It released an unsupported comparison on **12.68%**
of expected mixed-writer episodes.

The learner sees the receipt that actually arrives. Its estimate uses
the score of that receipt at the end of the episode, including a
shadow review if the writer produced an unseen candidate. The chair
uses the source-only record for that episode. A later exact match can
use the reviewed comparison if it improves the record. A material
change in the record or source prefix needs a new review. Both desks
know the channel rates and send cost. Only the peer condition gets
the first note's semantic code. A change signal resets the routing
estimates. Neither desk knows the new mixture.

## Held utility at the end of each phase

| Writer phase | Peer learner with bounded exploration | Exact reviewed peer ceiling | Best reviewed arrival-only ceiling | Frozen compact approvals |
| --- | ---: | ---: | ---: | ---: |
| Compact | **40.565** | 40.565 | 39.457 | 40.421 |
| Topic-guided | **37.242** | 37.242 | 37.242 | 22.676 |
| Half compact, half topic-guided | **38.241** | 38.493 | 38.076 | 31.548 |

The compact phase reached its peer ceiling by the 16-episode checkpoint,
after two shadow reviews. The topic-guided phase fell back for both
comparisons and returned to the source-only optimum. The mixed phase
reused all four exact reviews, which the peer learner had collected
during the first two phases. It learned the mixed receipt values from
fresh episodes with zero additional reviews in that phase.
This tests recurrence of previously indexed text within a changing
distribution. In the continuous exploration arm, arrival-only also
approached its ceiling, reaching 38.056 after one new review in the
mixed phase.

## Exploration has a cost

| Per-episode net change from source-only on matched simulation draws | Compact | Topic-guided | Mixed |
| --- | ---: | ---: | ---: |
| Peer learner, continuous exploration | +1.063 | −0.672 | −0.094 |
| Peer learner, exploration through episode 32 | **+1.813** | **−0.109** | **+0.375** |

The matched comparator uses the same views, channel draws, prices and
uniform training prior. The table charges a hypothetical point for
each distinct shadow review. Capping deliberate exploration turned the
mixed peer phase positive in this sequence, while the bounded
arrival-only arm missed a useful record its continuous version found.
The exact-review mechanism filters every unsupported archived candidate
in these trajectories, subject to the recorded review being correct.
It lowers final-record risk but still incurs review and exploration
costs. The scores exclude inference and review latency.

This is one exposed historical docket, one random sequence, two fixed
writer banks and a simulated mixture. The source-only fallback and
candidate pair list were available before learning. Reviews use
archived same-assistant scores, and there were zero new model calls.
The evidence supports exact reuse and routing recovery with recurring
records. It leaves automatic certification of novel drafts, reviewer
agreement and transfer to new UN event families open. A fresh evaluation
should lock an independently reviewed source-bound case and keep
scoring separate from review-cache lookup.

## Reproduce

[Protocol](protocol.md) · [Input pins](plan.json) · [Chronological traces](results.json) · [Audit](audit.json)

Use the existing Aurora Qwen Python environment. The replay uses NumPy
and archived evidence. The audit checks every observed receipt, the
record and source fingerprints, and the order of release, review and
routing updates. It verifies 1,536 simulated episodes and 15 shadow
reviews across two information conditions and two exploration schedules.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B refresh.py --plan | cmp plan.json -
python -B refresh.py | cmp results.json -
python -B audit.py | cmp audit.json -
```
