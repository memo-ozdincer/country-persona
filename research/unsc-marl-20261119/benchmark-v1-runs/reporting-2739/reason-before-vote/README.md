# Ask the writer to compare reasons before votes

**The prompt change recovered one missing national detail. Both records still
scored 56/70.** With co-sponsors first, the new sentence says Algeria valued
the reports while describing why the sponsors supported reporting. It leaves
unsaid that the shared reason was to keep the Council informed. With Algeria
first, the model again frames the relationship around the abstention and
the sponsors' support. The earlier authored 70-point record explicitly
connects the rationale while preserving the reasons for Algeria's abstention.
[Exact comparisons and records](scores.json) · [Grades](marks.json) · [Rubric and sources](../docket.json)

| View | Previous /70 | Added instruction /70 |
| --- | ---: | ---: |
| Both statements, co-sponsors first | 56 | 56 |
| Both statements, Algeria first | 56 | 56 |
| Public action and Algeria, action first | 49 | 49 |
| Public action and Algeria, action second | 49 | 49 |
| Single source, either card | 49 | 49 |
| Empty | 42 | 42 |

All seven records cleared the source guard and length limit. The writer
returned exactly `NONE` in all three incomplete conditions. In contrast to
one abstention with the previous prompt, both crossed cases now produce a
source-supported restatement. Neither can establish the sponsors' own
reason. One added instruction is the only model request change. All seven
frozen Qwen3.5-4B calls on Aurora's NVIDIA RTX PRO 6000 Blackwell Server
Edition replay to the saved input and output tokens, including 2,107 input
and 150 output tokens.

## Fit on the new terminal outcomes

All three critics trained on the same 64 simulated exchanges used in the
2664 fit, with only the terminal labels replaced by the scored 2739
outcomes. The critics agree that a second source adds its own seven points
with no joint bonus. Under the constructed send cost, they choose silence
in all 12 held settings and attain the exact 42-point utility optimum.
The frozen 2664 policy still sends both in six settings, receiving 47.833
factual points on average at a cost of 7.833, for utility 40. Always sending
raises factual coverage to 53.2 and lowers utility to 38 under the same cost.
[Fitted critics and exact settings](fit.json)

A permissive scoring replay assigns 14 extra points to the borderline
co-sponsors-first comparison. The imported 2664 critic expects the reward
in the opposite order. In this replay it matches the 2739 optimum on just
four settings and averages 41.252 utility, versus 43.688 for the target
oracle. The grade interpretation does not rescue the claim of an
order-invariant transfer. [Grading sensitivity](sensitivity.json)

This is an adaptive prompt change on one exposed target docket and with
assistant grades. The reward fit reuses a finite response archive and a cost
that charges each send its expected standalone benefit plus two. Its exact
optimum is specific to that payoff model. The model weights were frozen.
The record of the original generation runner is preserved. The scoring
replay loads the target scorer by path after a module name collision in the
original scoring command. The verification output was complete before the
successful scoring run.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B experiment.py plan | cmp plan.json -
"$python" -B experiment.py verify | cmp verified.json -
"$python" -B annotate.py | cmp marks.json -
"$python" -B scored_replay.py score | cmp scores.json -
"$python" -B scored_replay.py routing | cmp routing.json -
"$python" -B fit.py --plan | cmp fit-plan.json -
"$python" -B fit.py | cmp fit.json -
"$python" -B sensitivity.py | cmp sensitivity.json -
```

[Locked write protocol](protocol.md) · [Locked fit protocol](fit-protocol.md) · [Prior writer and transfer results](../source-preserving-transfer/README.md)
