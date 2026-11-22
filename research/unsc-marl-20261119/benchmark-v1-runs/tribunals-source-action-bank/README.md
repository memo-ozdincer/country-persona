# Measure the ceiling for tribunal source selection

Only **one of 16** legal pair-and-order combinations releases points
with the frozen chair. The winning 39/70 record places Peru's unity
appeal first and Serbia's medical-release objection second. Every
combination in the opposite speaker order scores zero on release.
The largest raw lower score is 41. Both records earning it fail release.

| Condition | Peru speaks first | Russia and Serbia desk speaks first |
| --- | ---: | ---: |
| Pair combinations | 8 | 8 |
| Best released score | 39 | 0 |
| Mean optimized independent score at 65% availability | 19.064 | 0 |
| Mean optimized peer-informed score at 65% availability | 19.064 | 0 |
| Best released score with only the word cap omitted | 39 | 33 |

The strict failures overlap. Nine records exceed 150 words, five
run into the generation cap, nine fail the factual guard, and four
have an uncertain guard. Typical errors include a fabricated roster
of voting states or a sentence whose wording attributes Peru's
specific judicial examples to the adopted resolution. The winning
record avoids both problems and preserves the appointment, the
Council's progress review, the unity appeal and Serbia's objection.
It omits Peru's draft symbol and Russia's substantive rationale.

The action matrix uses eight pairs of exact source excerpts, with
both speaker orders and the published chair prompt. Three finals
come from the prior run, reused only when the actual request matches.
Thirteen fresh generations ran on NVIDIA RTX PRO 6000 Blackwell
Server Edition with the same frozen Qwen3.5-4B checkpoint and
settings. They used 5,357 input and 3,446 output tokens. One
assistant reading scores each unique opaque packet, carrying over
the verdicts for the three identical records.

For the exact policy comparison, each desk privately receives a
nonempty subset of its sources. Each source is retained independently
with probability 45%, 65% or 85%, conditioning on nonempty slates.
The independent optimizer can coordinate its policies in advance
and each desk chooses from its own slate. The peer policy also gives
the second desk the first selection. The expected released scores
are identical under both information conditions at every tested
retention rate. The analytical optimum assumes the full scored bank
is known. 12 of the 16 pair-and-order combinations have mapped evidence
for at least 41 points, but evidence
coverage alone does not ensure release.

Removing only the word cap adds a valid 33-point pair in the
Russia-and-Serbia-first order, while still yielding zero gain from
peer access. Counting raw lower-bound rubric coverage regardless
of guard or completion creates an optimized peer advantage of
0.11–0.54 points across the six scenarios. These are diagnostics
on the archived text. The released endpoint leaves zero headroom
for improving interaction through source selection on this bank.
This result applies to one exposed case and one particular chair.

[Protocol](protocol.md) · [Scored packets](packets.json) ·
[Verdicts](verdicts.json) · [All 16 results](results.json) ·
[Exact policy ceilings and sensitivities](headroom.json) ·
[Verification receipt](verified.json)

```bash
set -o pipefail
python -B bank.py plan | cmp plan.json -
python -B bank.py packets | cmp packets.json -
python -B read_bank.py | cmp verdicts.json -
python -B bank.py score | cmp results.json -
python -B headroom.py | cmp headroom.json -
python -B bank.py verify | cmp verified.json -
```
