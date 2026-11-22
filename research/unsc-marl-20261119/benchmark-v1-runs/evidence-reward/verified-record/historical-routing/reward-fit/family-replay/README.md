# Replay historical routing across four archived dockets

The fixed chair and responder from the synthetic fit are replayed on
UNIFIL, Myanmar, UNAMA and the Ukraine emergency session. None of
these score banks is used to fit the original or revised heads.
The intervention supplies four calibration observations, the empty
record and each singleton. Add their observed gains to estimate the
remaining four receipt scores. Keep the opening policies fixed across
comparison arms. The full archived score bank evaluates the deployed
action. Each uses its own frozen rubric at the 70-point scale.

| Docket | Largest singleton-estimate error | Dense pruned wins over exact no-request | Sparse pruned wins over exact no-request |
| --- | ---: | ---: | ---: |
| UNIFIL | 14 | 3 / 3 | 2 / 3 |
| Myanmar | 7 | 3 / 3 | 3 / 3 |
| UNAMA | 0 | 0 / 3 | 2 / 3 |
| Emergency session | 0 | 0 / 3 | 0 / 3 |

The largest errors arise when extra credit depends on evidence from
two desks. UNAMA and the emergency bank are additive. One card in
UNAMA and two cards in the emergency bank never add points. The
original fit assigns positive singleton value to every training card.

Keeping half the dense banks and training on new synthetic cases
with unusable cards improves all six historical rows in the latter
two dockets relative to the dense fit. It lowers net in five of the
six UNIFIL and Myanmar rows. On the held synthetic sparse banks,
the sparse fit beats the original by net in 68 of 72 rows and ties
the other four. It still loses to exact no-request in 42 of 72.
The dense and sparse teams each have settings where they are useful.
[Initial replay](results.json) · [Sparse fit and held rows](sparse-results.json)

## Choose a policy with a documentary quality floor

The selector uses only the four calibration scores to choose among
the learned teams and an optimized no-request continuation. Restricting
it to those three options loses to actual-score exact no-request on
uniform UNIFIL. Allowing fixed addressed requests alongside them yields
higher net than exact no-request in all 12 rows. The net gains on the
three emergency rows come from lower costs and slightly fewer released
points.

A second selector requires a candidate to preserve at least the forecast
documentary score of no-request before comparing net. It selects the
same nine improving policies in UNIFIL, Myanmar and UNAMA and selects
no-request on the three emergency rows. None of the twelve actual
documentary scores falls. It uses learned routing in three improving
rows and fixed requests in six. The unrestricted mixed selector
outperforms the best fixed request with an optimized responder under
the actual scores in two rows. The quality floor also preserves those
two learned wins. The floor uses forecast quality, so unseen
complementarities can still invalidate it.

These are evaluations of archived, same-assistant-reviewed records and
modeled receipt distributions with stipulated channel and inventory
laws. UNAMA and emergency scores come from the previously reported
post hoc length control. None of the results is a new native generation,
blind historical holdout, or independently reviewed benchmark result.
[Protocols](protocol.md) · [Mixed selector results](qualified-results.json) ·
[Quality floor results](quality-results.json)

Replay with the original project Python, NumPy and CPU Torch.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
python3 replay.py | cmp - results.json
python3 sparse.py | cmp - sparse-results.json
python3 qualify.py | cmp - qualified-results.json
python3 quality.py | cmp - quality-results.json
```

[Selected live UNIFIL witness](live-unifil/README.md) follows one
qualified request into native evidence delivery. It exposes separate
card-identity and length failures, then verifies the mechanism with
the exact quote, a 123-word final record and an identical fixed
Russia request.

[Matched public-state audit](opposing-contexts/README.md) strengthens
the fixed-target comparator. The [native writer replay](opposing-contexts/native-writer/README.md) tests whether the selected adaptive gain survives final generation.
