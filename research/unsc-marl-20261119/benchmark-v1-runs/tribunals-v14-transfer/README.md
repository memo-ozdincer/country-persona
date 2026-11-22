# Resolution 2422 transfer for the complete-message decoder and router

The frozen v1.4 case on Resolution 2422 joins UNBench author-test event
2229 and UNSC-Bench adopted row 197. The documentary rubric distinguishes
Peru's call for unity, Russia's explanation of abstention, Serbia's
objection as a nonvoting participant, and the scope of Council action.
This exposed case has prior free-form writing experiments. It is new to
the complete-message decoder and to the archived interval-policy tables
from Myanmar and UNIFIL.
[Frozen cases](../../benchmark-v1.4/cases.json) ·
[Earlier writing evidence](../../benchmark-kit/reader-use/tribunals2422-transfer/README.md)

## Three live role calls

Frozen Qwen3.5-4B received only public material and the two passage
choices for each of Peru, Russia and Serbia. The decoder scored 78 complete
candidate token sequences across the three prompts and emitted both IDs
in each response. The rubric releases 70/70 with all three cards, matching
the authored selection in every receipt mask. Ranking only the canonical
spelling in the saved tables favors Peru's empty list, Russia's medical
clause and Serbia's release objection. That diagnostic yields 52/70 at
full receipt. It uses no additional inference.

| Selection rule | Empty receipt | All three packets | Full-record words |
| --- | ---: | ---: | ---: |
| Authored menu | 33 | 70 | 131 |
| Complete-message model score | 33 | 70 | 131 |
| Canonical spelling only | 33 | 52 | 82 |

The model ran on an NVIDIA RTX PRO 6000 Blackwell Server Edition. The three
selected messages used 1,240 input tokens and 18 emitted tokens. These
counts describe the emitted messages. The 78 separately scored sequences
account for additional inference work. Model weights were frozen. The
owned process exited normally.
[Locked prompts and baseline scores](plan.json) ·
[Launch and runtime identity](evidence/launch.json) ·
[Candidate likelihoods](evidence/likelihood.jsonl) ·
[Exact final records and marks](results.json)

## Route the same role messages

The modeled routing comparison uses each archived source family's opening
tables throughout. The frozen comparison also leaves its chair and responder
tables fixed. The replanned comparison gives both the team and fixed target
seven Tribunals grades and withholds the full-receipt grade. The 36 rows
cross the two source openings with inventory assumptions and grade offsets.
Some rows share the same opening and channel. The results compare expected
released points minus a modeled packet cost, in rubric points.

| Router and matched fixed control | Wins / ties / losses | Mean net gain | Mean gain over fully informed fixed | Below silence in released quality |
| --- | ---: | ---: | ---: | ---: |
| Frozen source policies | 10 / 0 / 2 | +0.085 | −0.063 | 4 / 12 |
| Replanned with seven target grades | 32 / 4 / 0 | +0.128 | +0.063 | 2 / 36 |

Replanning improves the shared-reward policy under the matched budget.
The 12 clean routing contexts replay through the decentralized dispatcher
and reconcile with analytical reward and communication cost. The policy
may cache and resend a selected role packet. Packet delivery and private
inventories are modeled. The case is exposed, marks are authored against
fixed clauses, and the model receives an already authored menu. These
results measure a decoder and a tabular routing policy. They leave
independent grading and free-form generalization unmeasured.
[Source policy tables](source-policies.json) ·
[Routing protocol](routing-protocol.md) ·
[Condition data and branch witnesses](routing-results.json)

## Widen the prior qualification

The two base replay regressions collapse to a single setting after
deduplicating the identical source openings. A seven-point overstatement
of the Peru–Russia grade combined with the uniform proxy puts the team
0.059 released points below fully informed silence. Qualifying policies
over a wider prior envelope keeps the same selection there. None of the
45 candidates passes the documentary floor in every forecast at that
setting. The selected candidate's worst forecast shortfall is 0.082
points. The candidate pool consists of one coordinated and four fixed
or silent policies at each of nine prior and grade combinations.

Across 21 distinct settings, both selectors beat their equally informed
fixed control in 18 and tie in three. The envelope changes mean net gain
over that control from +0.120 to +0.121 while mean gain over fully
informed fixed falls from +0.061 to +0.059. It does not repair the quality
regression. This makes the absence of a qualifying policy in the current
candidate pool the next issue to investigate.
[Prior qualification protocol](prior-protocol.md) · [Per-setting margins and eligibility](prior-results.json)

## Replay

Run in the project inference environment, with `python` pointing to that
environment. The replay verifies checkpoint metadata, token sequences,
candidate rankings, message admission, all eight rubric scores per
selection rule, routing tables and the prior qualification. It reads
the archived model traces.

```bash
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python tribunals_transfer.py plan | cmp plan.json -
python tribunals_transfer.py verify | cmp results.json -
python routing_transfer.py freeze | cmp source-policies.json -
python routing_transfer.py run | cmp routing-results.json -
python prior_qualification.py | cmp prior-results.json -
```

[Direct policy optimization and stochastic reply fallback](constrained/README.md)
revisits the documented quality regression. It verifies the deterministic
infeasibility under the specified forecasts and recovers the held
documentary floor with a private randomized responder.
