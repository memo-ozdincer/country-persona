# Reuse sender calibration when the reply policy changes

**Learning which reply arrived removes the transfer loss when the
partner profile is known.** The sender payoff depends on which claim
the second desk receives and what it sends in reply. Both estimators
use the same 128 randomized episodes per UN docket. The pooled fit
records whether a reply arrived. The other records which reply
arrived and combines those learned scores with the current partner's
probabilities. [Protocol](protocol.md) · [Exact episodes and held grid](results.json)

| Sender policy across 1,152 settings | Mean factual release /70 | Mean cost | Utility | Regret |
| --- | ---: | ---: | ---: | ---: |
| Older fixed-reader calibration | 35.461 | 3.742 | 31.719 | 0.506 |
| Same log, reply identity pooled | 34.374 | 2.513 | 31.861 | 0.363 |
| Reply identity, partner estimated from probes | 34.751 | 2.555 | 32.196 | 0.029 |
| Reply identity, declared partner | 34.623 | 2.398 | **32.225** | 0 |
| Exact sender ceiling for each partner | 34.623 | 2.398 | 32.225 | 0 |

The six deployed profiles include the calibrated claim reader, two
fixed replies, a reversed claim reader, and two mixtures. Identifying
the received reply gives the fit enough data to reconstruct the
archived outcomes. All nine first-arrived cells have at least two
observations in each docket. The declared-profile version matches
the exact sender ceiling in every setting. It adjusts forwarding
to the expected response. The fixed-reader calibration has its
largest mean regret, 1.185, with the reversed reader.

The probe version uses eight independent reply observations for
each receive state. It reaches the ceiling on 1,112 of 1,152 settings.
All 40 misses arise under the profile that mixes 25% of the ordinary
reader and 75% of the reversed one. In this fixed probe draw the
probability of a process reply after positive evidence is estimated
as 0.625 when it is 0.25. The utility score deducts only the existing
forwarding price. The separate 24 probes are excluded from that score,
so their utility cost would reduce the reported value.

The partner policies are stationary and simulated from known
probabilities over two archived actions. No new text is generated.
This test assumes independent delivery and deterministic record
values. One fixed draw supports each probe estimate. The declared
profile setup receives information that may require estimation in
a live interaction. These results measure payoff reuse under partner
change on two exposed dockets. They leave novel dockets, learning
with noisy scores, and live coordination unverified.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B partner_fit.py --plan | cmp plan.json -
python -B partner_fit.py | cmp results.json -
```

[Fixed-partner calibration and source rewards](../shared-policy-transfer/README.md)
