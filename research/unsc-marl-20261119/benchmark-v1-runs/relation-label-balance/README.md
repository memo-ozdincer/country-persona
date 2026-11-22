# Balance relation labels and learn when to recheck

Three balanced letter mappings block the shared false contradiction on
the Mali final-extension claim by withholding judgment. One of the
two new mappings reads the claim correctly. Majority vote and pooled
logits still return the false contradiction. A learned paid recheck
policy leaves every held decision the same as the first read and
spends additional queries.

## Letter-mapping test

The previous pair moved support and unresolved between A and C and
kept contradiction on B. Add two cyclic mappings to 27 exact archived
prompts. The identity view and both cycles place every relation on
every letter once. The claim, witness, system instruction and model
checkpoint are fixed. Use all 19 routed archive claims and the eight
previously evaluated Myanmar claims. The 19 older paired observations
were collected on CPU. The two new mappings and the older Myanmar
pair use Aurora GPU. This leaves a hardware crossover in the archival
comparisons. [Protocol](protocol.md) · [Locked inputs](plan.json)

| Decoder | Archive correct /19 | Archive wrong decisive | Myanmar correct /8 | Myanmar wrong decisive |
| --- | ---: | ---: | ---: | ---: |
| Old pair, agreement | 15 | 1 | 6 | 0 |
| Old pair, pooled | 15 | 4 | 8 | 0 |
| New pair, agreement | 14 | 3 | 7 | 0 |
| New pair, pooled | 14 | 4 | 8 | 0 |
| Balanced three, unanimity | 15 | 0 | 6 | 0 |
| Balanced three, majority | 14 | 4 | 7 | 0 |
| Balanced three, pooled | 15 | 4 | 8 | 0 |

The Mali comparison targets Russia's stated final extension of the
sanctions regime. The normalized witness says only “the regime”,
with a shortened context. The official meeting makes the referent
explicit. Both older reads chose physical B, mapped to contradiction.
The two new reads chose physical C, mapped respectively to support
and contradiction. Moving the letters elicited a correct alternative
while a decisive pooled repair remained unavailable under the tested
decoders. The first newer mapping by itself makes four wrong archival
decisions. The second newer mapping gets all eight Myanmar claims
right and makes six wrong archival judgments. Selection of that
mapping from the Myanmar results would use the held labels.
[Official meeting S/PV.9408](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.9408&t=pdf) ·
[All mapped decisions and paired changes](results.json)

## Selectively request one paid second read

After inspecting the decoder test, fit one proposer and one reviewer
with exact shared reward. The proposer can withhold, publish its
own label, or request either cyclic read. The reviewer sees its own
read and the first categorical relation, and can keep it, replace it
with its own decisive label, or withhold. Reward correct decisive
relations by +1 and penalize false ones by 2. Withholding earns zero.
An additional read costs 0.10. The fitted weights use 160 CPU updates
and no further model calls. Train on three archive families at a
time for leave-out results and on all four for Myanmar.
[Routing protocol](routing-protocol.md) · [Weights, exact outcomes and fixed controls](route-results.json)

| Policy | Archive net | Archive extra reads | Myanmar net | Myanmar extra reads |
| --- | ---: | ---: | ---: | ---: |
| Learned recheck | 0.3908 | 0.3833 | 0.6125 | 0.1250 |
| First read only | 0.4292 | 0 | 0.6250 | 0 |
| Training-selected fixed confidence rule | 0.2063 | 0.1458 | 0.7250 | 0.2500 |
| Always check with first cycle, require agreement | 0.4542 | 1 | 0.5250 | 1 |
| Always check with second cycle, use its label | −0.1000 | 1 | 0.7750 | 1 |
| Balanced three-read unanimity | 0.3542 | 2 | 0.4250 | 2 |

The fitted objective rises from 0.0568 to 0.3723 on the four training
families. The greedy learned policies reproduce every first-read
relation in the four leave-out folds and on Myanmar. The paid
Myanmar review concerns the unsupported claim that India opposed
ASEAN's role. It leaves that claim unresolved, which the first read
already did. The learned rechecks therefore spend budget without
improving held judgments. The Myanmar per-case score ceiling with
one additional read is 0.85 under this payoff. The classifier keys,
cases and model outputs have project exposure. This replay measures
source decisions and modeled contact costs.

The 54 new frozen Qwen3.5-4B forwards use 15,512 input and 108
constrained output tokens on NVIDIA RTX PRO 6000 Blackwell Server
Edition. The recorder verifies the exact prompt and response IDs.
[Token and artifact check](verified.json) ·
[Worker receipt](evidence/launch.json)

## Reproduce

Use the Aurora Qwen environment from
[the original fit](../reporting-2739/learned-admission/README.md#reproduce).

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
"$py" balance.py plan | cmp plan.json -
"$py" balance.py verify | cmp verified.json -
"$py" score.py | cmp results.json -
"$py" learn_route.py | cmp route-results.json -
```
