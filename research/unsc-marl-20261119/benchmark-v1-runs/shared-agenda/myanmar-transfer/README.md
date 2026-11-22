# Transfer the documentary follower to the Myanmar scheduling workshop

The existing Myanmar workshop was excluded from the Iraq/Syria follower
fits. In this workshop the UN office can attend early only or both
slots. The liaison office can attend late only or both slots. An office
with both slots warrants a common time from its own card and the other
office's public alternatives. Four world/order pairs meet that
condition. Each comparison fixes the warranted time and the historical
mandate, then adds the later calendar in the two-report arm.

The protected layout leaves 30 words for the calendar paragraph under
the existing 100-word limit. The scoped writer uses frozen Qwen3.5-4B.
The literal control copies authenticated calendars and states the
published availability guarantee when one card is missing. Two
one-report inputs are shared across pairs, so six physical model calls
yield eight logical paragraphs.
[Protocol](protocol.md) · [Workshop inputs, exact proofs and requests](plan.json)

| Writer and scoring contract | One calendar, released /280 | Both calendars, released /280 |
| --- | ---: | ---: |
| Literal, original rubric | 280 | 280 |
| Literal, actual second calendar required for P2 | 252 | 280 |
| Scoped Qwen, either contract | 0 | 140 |

The original P2 awards seven points for identifying the missing holder
and saying that its card was unavailable. Both literal single-card
records identify the unknown calendar and explain why its published
alternatives permit the selected slot. The stricter sensitivity changes
only P2. The six units supported by the fixed text retain the checked disposition,
the timing proposal and the exact official reporting mandate.

The scoped writer invents a late-only liaison calendar on both logical
UN-first single-card receipts, including the world where the guess
happens to coincide with the hidden card. Both liaison-first single-card
receipts exceed the word cap and leave the referent of “its exact
calendar” unclear. With both calendars, one paragraph exceeds the
cap and one leaves the scope of the claimed public guarantee uncertain.
Two clear, in-limit full records score 70. These are assistant-authored
semantic judgments and mechanically checked quotes. The office
availability is fictional. The event remains an exposed development
family.
[Records](deck.json) · [Exact judgments](marks.json) · [Scores](scores.json)

## Replay the frozen follower after proof

The earlier frozen estimates value a delivered second card at
0.15 for the scoped writer and 0.20 for the literal writer on the
normalized 0–1 scale. The replay uses four equally weighted proof
receipts, four delivery rates and three public priorities. It charges
the fee for attempted reports. Results below are mean additional net
utility over keeping the one-report record, at a fee of 0.06.

| Writer and scoring contract | Frozen fit | Fixed 7-point forecast | Fixed 14-point forecast | Exact archived-grade optimum |
| --- | ---: | ---: | ---: | ---: |
| Literal, original | −0.06000 | −0.03500 | −0.06000 | 0.00000 |
| Literal, second card required | +0.01000 | +0.01475 | +0.01000 | +0.01475 |
| Scoped, original or second card required | +0.28000 | +0.21375 | +0.29000 | +0.32000 |

The same learned value overpays under the literal original rubric and
overestimates the literal incremental reward under the stricter rule.
With the scoped writer it underestimates the value of a second card in
the two cases where it restores release. The simple 14-point forecast
earns more than the transfer fit on that writer at the nominal fee.

A dependent replay scales the frozen estimate by the publicly
available rubric points. On literal records it matches the exact
policy at all four tested prices under both rubrics, tying the
rule that uses the same rubric values directly. On scoped records
it misses recoveries from guard and formatting failures. The rubric
sets the value of a correct extra proposition. It does not predict a
writer's release under changed evidence.
[Dispatch protocol](replay-protocol.md) · [All frozen-policy decisions](replay.json) ·
[Rubric scaling protocol](calibrated-protocol.md) · [Scaled replay](calibrated.json)

## Verify

The six model calls completed on NVIDIA RTX PRO 6000 Blackwell Server
Edition with zero optimizer updates. The locked request replay checks
the true roster, exact token traces, and output boundaries. The same
assistant graded all records and simulated the dispatch. [Preparation](preparation.md) ·
[Worker identity](evidence/launch.json) · [Raw replies](evidence/calls.jsonl)

Use the project Qwen environment in this directory:

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
python transfer.py plan | cmp plan.json -
python transfer.py deck | cmp deck.json -
python evaluate.py score | cmp scores.json -
python evaluate.py replay | cmp replay.json -
python calibrated.py | cmp calibrated.json -
```
