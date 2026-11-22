# Learn when to ask for one documentary retry

A learned retry policy improves on silence but trails the strongest
fixed rules on average. The learned private hints slightly lower
net return. An exact check using public singleton scores repairs a
preventable failure on Haiti, where a successfully delivered packet
can spoil the writer's final record.

## Fit and transfer

Reduce nine graded, three-packet writer banks to 27 two-packet
tables by treating each packet in turn as already available. Use
actual released writer scores as the terminal documentary reward.
The empty and singleton scores are policy inputs. The score for
holding both remaining packets is hidden during action selection.
The Myanmar and Resolution 2739 transfer banks come from the
source-bound composer with public procedural facts. Both are outside
the fit and have prior development exposure.

The first sends and the optional retry use a simulated persistent
link type. Each missing desk privately receives a noisy indicator and
may send one paid hint. A chair sees the delivered set and hints. It
has one paid retry or can stop. Different archive families have the
same weight. The joint fit uses 200 exact CPU gradient updates and one
shared desk head plus one chair head. Initial expected training net
is 44.4569 and final net is 45.9665 on the full fitting set. A second
branch enumeration verifies the frozen policy outcomes.
[Protocol](protocol.md) · [Bank, channel and input pins](plan.json)

| Cohort | Signal accuracy | Silence | Learned greedy | Fixed with shared prior | Strongest fixed in comparison |
| --- | ---: | ---: | ---: | ---: | ---: |
| Six archive folds | .85 | 43.4883 | 45.5830 | 45.6907 | 45.7132 |
| Six archive folds | .65 | 43.4883 | 45.5818 | 45.6521 | 45.6999 |
| Myanmar and Resolution 2739 | .85 | 53.3330 | 57.9189 | 57.9592 | 57.9592 |
| Myanmar and Resolution 2739 | .65 | 53.3330 | 57.9159 | 57.9075 | 57.9287 |

Net is released points less 0.15 per hint and 0.75 per retry. The
shared-prior fixed rule uses the fitting mixture and assumed .85
signal accuracy even under stress. It selects its hint convention
and interaction offset on the fitting families. The last column is
a retrospective envelope. It uses the known-law fixed menu for
archive folds and the shared-prior menu for transfer. On the matched
transfer the full-bank, free-signal ceiling is 57.9982. On stressed
transfer it is 57.9585. The 232 replay conditions cross both role
orders and link laws with both signal accuracies.
[All scores and costs](results.json) · [Matched-prior control](comparison.json)

Removing the learned hints with the same chair raises net by 0.0266
in the matched archive and 0.00975 on matched transfer. The matched
transfer team's released score and retry frequency are identical
with hints removed. On stressed transfer, the fitted policy beats
the training-selected fixed rule by 0.0085 and trails the fixed
no-hint envelope by 0.01275. These small differences depend on
modeled costs and simulated signal reliability.

## Check retries with a known singleton outcome

When both remaining packets are missing, one successful retry can
add only one packet. The score after that delivery is a public
singleton score. If it is at or below the current score, abstain
from that retry. Suppress both hints when neither retry can help.
The safeguard changes only those jointly empty receipt states.
Apply it after inspecting the results and keep the fitted weights.
The archive's exact branch replay verifies that no condition
loses net or released points when the safeguard is applied.

On matched archive folds this raises net by 0.1385 to 45.7214.
Haiti rises by 0.7492 to 22.4332, above its silence value of 21.9256.
In one Haiti writer bank, the starter alone scores 49 and either
successful retry drops the result to zero. The original learned
chair attempts a retry in the empty receipt state. The public check
prevents that action. The two transfer families have positive
singleton additions and keep their original scores. The post hoc
check supplies no evidence of a learned advantage on a new family.
[Guarded replay](known-dominance.json)

There are no exact opposite-sign outcome collisions across distinct
families among the 58 role-ordered, singleton-gain receipt views.
This finite archive leaves interpolation on novel previews and the
effect of correlated writer errors open. [Observation audit](alias-audit.json)

All terminal results reuse exposed, previously scored records.
Transport, hint accuracy and costs are simulated. The experiment
adds no language-model calls or updated language weights.
[Preparation and numerical verification](preparation.md)

## Reproduce

Use the existing Aurora Qwen environment with Bash pipe failure enabled.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" retry.py plan | cmp plan.json -
"$py" retry.py run | cmp results.json -
"$py" comparison.py | cmp comparison.json -
"$py" known_dominance.py | cmp known-dominance.json -
"$py" alias_audit.py | cmp alias-audit.json -
```
