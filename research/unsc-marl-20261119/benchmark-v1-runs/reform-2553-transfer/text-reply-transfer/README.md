# Route the German reply from the wording of the UK message

**The calibrated text policy routed all four valid rewrites correctly and
five of eight controls incorrectly.** It averaged 7.50 reply points, tying the
keyword rule and beating fixed replies at 7.00. A genuine concern earns
four more points with the process card than with the Fund card, while
each unnecessary process reply loses two. This makes raw accuracy and
reward tell different stories. [Exact messages](messages.json) · [Choices and reward fit](results.json)

| Reply policy | Correct /12 | Mean points above the fixed record | Mean regret |
| --- | ---: | ---: | ---: |
| One label mapping, either order | 5 | 7.167 | 1.167 |
| Mean mapped logits | 5 | 7.167 | 1.167 |
| Mean logits calibrated on rewards | 7 | 7.500 | 0.833 |
| Keyword rule | 7 | 7.500 | 0.833 |
| Any nonempty message | 4 | 7.000 | 1.333 |
| Always process | 4 | 7.000 | 1.333 |
| Always Fund | 8 | 7.000 | 1.333 |
| True-context ceiling | 12 | 8.333 | 0 |

Calibration uses 64 explorations over the three original calibration
contexts. None of the held texts enters the fit. The predicted advantage
switches near a mean logit margin of 1.583. The model still chooses
process for the reported objection, the explicitly rejected objection,
the next negotiation, reform implementation speed, and approval of
the short timetable. The keyword rule gets implementation speed right
and sends the wrong card for the clarity-only objection. All other held
choices match. The future-negotiation control has margin 3.5, above
the weakest genuine timing objection at 3.375. A stricter threshold on
this margin cannot keep every genuine match while rejecting that control.

The German desk gets the first message and two German cards. It receives
no receipt ID or gold link label. We evaluate first-token action choices
under both letter mappings. The frozen prompt contains a routing heuristic.
The fit only calibrates the frozen model's scalar margin to the archived
environment's terminal reward. The held texts are assistant-authored stress
messages on the same exposed docket, including synthetic counterpositions.
They were never inserted into an official record. Their utility is the
simulated increment from the selected German reply after delivery. It is
assigned according to whether the held message expresses the registered
timing objection. This does not measure a native final-record score on
those rewrites. [Payoff derivation and canonical archives](../concern-transfer/README.md)

All 30 first-token decisions and their source prompts and label tokens
replay exactly. The run used 5,920 input tokens and 60 saved label and end
tokens with frozen Qwen3.5-4B on Aurora's NVIDIA RTX PRO 6000 Blackwell
Server Edition. The learned calibration updates two scalar coefficients,
with zero backbone changes. The fixed benchmark release also replays.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B text_study.py plan | cmp plan.json -
"$python" -B text_study.py verify | cmp verified.json -
"$python" -B readout.py | cmp results.json -
```

[Protocol](protocol.md) · [Logits and decoded choices](verified.json)
