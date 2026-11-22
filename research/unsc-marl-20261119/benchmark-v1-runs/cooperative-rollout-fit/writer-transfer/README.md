# Does learned routing help once the chair keeps the notes?

On the strongest Resolution 2686 writer, the frozen fitted chair and
responder lose to the robust adaptive planner and the fully informed
fixed policy in **all 18** modeled conditions. They lose to their own
zero-residual control in 16, winning two. The responder-only swap
reproduces the jointly fitted team's outcomes across these 18 conditions.
Its mean released record is 0.0146 points lower than neutral and its
communication cost is 0.0275 higher. Preserving the notes raises the
absolute value of receiving them. It still leaves a cost for unnecessary
transmissions. [Results and deployed policy tables](results.json)

## Validate the learning intervention

We refit the paired-return heads for three rounds on 36 synthetic banks.
Training uses 324 contexts and 373,248 inventory and delivery draws.
Twelve disjoint synthetic banks provide 108 validation conditions.
The preregistered selection tests zero, half and full amplitude for
each head, with a documentary quality floor and a below-silence check.
It selects a **half-strength chair and zero responder residual**.
The selection improves validation net by 0.00069 points over neutral
and preserves the 25 below-silence count. The first attempt stopped
on a historical archive schema mismatch before emitting held results.
[Protocol](protocol.md) · [Locked inputs](plan.json) · [Preparation error](preparation.md)

The five historical banks and both generated Resolution 2686 banks
are disjoint from the synthetic fitting and validation banks up to
a constant shift. The two Resolution 2686 banks share one docket.
All comparisons use matched opening tables, action legality, delivery
law and message fee. The fixed and robust references use the same
announced information as the learned team. The fully informed fixed
reference receives the true reward bank and inventory law.

| Learned or exact component | Five historical banks, net vs neutral / robust | Scoped-rewrite bank, net vs neutral / robust | Verbatim bank, net vs neutral / robust |
| --- | ---: | ---: | ---: |
| Original fitted chair and responder | −0.0593 / −0.0874 | +0.0397 / −0.0169 | −0.0421 / −0.1144 |
| Full-strength refit | −0.0587 / −0.0868 | +0.0397 / −0.0169 | −0.0354 / −0.1077 |
| Validation-selected refit | −0.0002 / −0.0283 | +0.0010 / −0.0556 | −0.0096 / −0.0819 |
| Frozen learned score forecast, neutral action construction | +0.0052 / −0.0229 | +0.0834 / +0.0268 | +0.0040 / −0.0683 |
| Exact adaptive search on the announced forecast | +0.0112 / −0.0169 | +0.0758 / +0.0192 | +0.0678 / −0.0045 |

The selected refit ties neutral in 63 of 90 historical conditions,
wins 11 and loses 16. It ties neutral in 13 verbatim conditions
and loses five. The frozen score forecast on the scoped bank wins
six and loses 12 against robust search, with a positive mean and
zero results below informed silence. It beats the matched fixed
policy in 17 of 18 scoped conditions. It loses to robust search in
all 18 verbatim conditions. On the scoped bank the mean change is
+0.0947 under a seven-point undergrade, +0.0013 with the exact pair
grade and −0.0156 under a seven-point overgrade. The correction costs
more communication on average under all three offsets. The gain
concentrates in conditions where it rescues documentary coverage
under an undergrade.

The exact forecast search nearly matches the robust planner on the
verbatim bank. The robust planner wins five, ties eight and loses five
in that comparison. The learned score model, direct learned residuals
and exact planner are distinct interventions. No LLM was trained or
run for this replay. The evaluation uses 126 modeled conditions on six
exposed UN event families, with 1,008 independent branch replays of
the eight recomputed policy arms. This evaluates transfer to archived
reward profiles. End-to-end performance on unseen negotiations and
independent grading remain unmeasured.

## Reproduce

Use the Aurora Python and SciPy environment documented in the
[parent reproduction instructions](../README.md#replay). Run in this
directory.

```bash
set -o pipefail
replay() {
  "$py" -c 'import numpy,sys,runpy; sys.path.append(sys.argv.pop(1)); runpy.run_path(sys.argv.pop(1),run_name="__main__")' "$scipy_packages" "$@"
}
replay writer_transfer.py plan | cmp plan.json -
replay writer_transfer.py run | cmp results.json -
```
