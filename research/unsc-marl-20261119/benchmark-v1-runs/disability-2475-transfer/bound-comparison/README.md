# Bind the Resolution 2475 comparison to source claims

The previous free-form comparison degraded records even with the
needed evidence. Here the chair sees one authored proposition at a
time and judges it against the received notes. A deterministic
renderer can add the scoped France–Russia contrast only when the
trusted France and Russia note texts both match their registered
owner and claim ID. The renderer has no route for the two misleading
alternatives. The rule-only control uses the same source registry and
template. This experiment uses authored proposition text and exact
source matches on an exposed case.
[Protocol](protocol.md) · [Locked model inputs](plan.json) ·
[Analysis lock](analysis-plan.json)

## Judging the relation

The two answer-label orders agree on support for the restored
France–Russia pair and full record. They disagree on the remaining
eight cases. The consensus rule admits two of four supported
propositions and zero of six unsupported ones, with eight abstentions.
Both common-ground positives about the UK and Russia are among the
abstentions. They remain credited in the record from the directly
attributed UK note.

| Classifier readout | Exact / 10 | Supported claims admitted / 4 | Unsupported claims admitted / 6 | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| A means support | 8 | 2 | 0 | 0 |
| B means support | 4 | 4 | 6 | 0 |
| Require agreement | 2 | 2 | 0 | 8 |
| Mean mapped logit | 5 | 4 | 5 | 0 |

The mean-logit rule would admit five unsupported relations, including
an attribution of Russia's Article 11 interpretation to the UK.
The constrained label scorer completed 20 inference calls, using
5,148 prompt tokens and 40 rendered label and end tokens. The native
forward passes took 4.73 measured seconds on NVIDIA RTX PRO 6000
Blackwell Server Edition, excluding checkpoint load. The process
exited normally. It performed no optimizer updates.
[Raw logits and token traces](evidence/calls.jsonl) ·
[Verified outputs](verified.json)

## Render and route

| Receipt evidence and renderer | France + Russia | All three |
| --- | ---: | ---: |
| Restored notes, verbatim | 42 | 63 |
| Restored notes, prior plain comparison | 42 | 0 |
| Restored notes, prior scope-check comparison | 0 | 0 |
| Restored notes, rule-only template | 49 | 70 |
| Restored notes, classifier plus template | 49 | 70 |
| Original native notes, any verified renderer | 0 | 0 |

Both authorized renderers add seven points in each restored receipt
set. The full record is 130 words. The exact-match gate rejects the
omitted-France and omitted-Russia controls even when the model
decision is forced positive. It also rejects the correct text under
the wrong owner and the registered text embedded inside a denial.
The unchanged native notes never satisfy both source requirements.
The rule-only baseline and model-gated arm emit identical final text
and scores. The gain on restored notes comes from the template and
source binding. The classifier has no measured incremental benefit.
[Rendered records and exact marks](scored.json)

The two authorized restored banks also yield identical routing
results. Compared with the restored verbatim bank, the nominal
planner's mean released score rises from 46.40 to 48.13, and its mean
net margin over fixed rises from +0.1141 to +0.1880. On the restored
template bank, the frozen learned forecast improves nominal net by
+0.0135 and the additive forecast by +0.0113. They tie on the native
bank. The simulator and independent dispatcher agree on all 288
policy outcomes, and the scoring and routing artifacts reproduce
exactly. These results measure a known-case renderer with authored
note text and simulated delivery. They provide no transfer estimate
for automatic claim extraction or unseen negotiations.
[Routing replay](routing.json)

The first score export stopped in the missing-source self-check
because its role list contained an absent third role. The repair
aligns the fixture's names with its available texts. The prompts,
model results and deployed rendering rule are unchanged.
[Preparation receipt](analysis-repair.json)

## Reproduce

Use the Aurora Python and SciPy setup in the
[Resolution 2475 instructions](../README.md#reproduce).

```bash
set -o pipefail
"$py" choose_relation.py plan | cmp plan.json -
"$py" choose_relation.py verify | cmp verified.json -
"$py" render_bound.py score | cmp scored.json -
replay render_bound.py route | cmp routing.json -
```
