# Isolate national positions before composing the final record

Four frozen Qwen3.5-4B calls wrote one public fragment and three
national fragments. Each national call saw a single role's evidence.
A deterministic renderer selected only the fragments available in the
receipt mask. It could add a comparison when two model-supplied
labels had attached source substrings.

All eight records cleared the factual guard and stayed within the
150-word cap, at 51–108 words. The learned continuation earned 105
released points summed across the three matched states. The strongest
fixed request also earned 105 and cost 0.05 less. The Russia fragment
referred to late changes and missed the earlier lost compromise. The
record with the Russia card had the same 35 points as the one with
Brazil and China alone. Brazil's fragment omitted free operation, and
China's omitted sovereignty and consent. The public fragment omitted
the French draft symbol.

The comparison about Brazil and China was supported by the two source
blocks. Brazil's generated mission-support label cited the draft's
robustness and operational freedom instead of the separate line
supporting the mission. String membership alone did not validate
the semantic label. The national prose independently gave explicit
mission support.

Across the full modeled population, the frozen dense route lost to the
strongest fixed continuation on net under all three inventory priors.
Its margins were −0.270, −0.113 and −0.501 for uniform, asymmetric and
correlated inventories. These comparisons include opening, query and
reply costs and modeled delivery losses.
[Selected states](results.json) · [Population comparison](population.json) ·
[Criterion marks](marks.json) · [Native calls](evidence/calls.jsonl) ·
[Verification](verification.json)

This is an exposed UNIFIL docket with the original policy weights
and same-assistant documentary marking. Four writer calls on an
NVIDIA RTX PRO 6000 Blackwell Server Edition were shared across
receipt masks. The communication-cost estimate charges messages
separately from writer inference.
[Protocol](protocol.md) · [Population protocol](population-protocol.md)

```bash
set -o pipefail
python3 bound_writer.py plan | cmp - plan.json
python3 bound_eval.py fragments | cmp - fragments.json
python3 bound_eval.py packets | cmp - packets.json
python3 bound_eval.py verify | cmp - verification.json
python3 bound_eval.py score | cmp - results.json
python3 population.py | cmp - population.json
```

[Exact-excerpt follow-up](extractive/README.md) preserves all source
wording that passes its gate. The model returns an empty China excerpt
list and an over-budget Brazil submission. Relaxing Brazil's local cap
recovers its criterion without changing the policy ranking.

[Numbered source passages](numbered/README.md) recover a 70/70 full
record when the budget allocator keeps the qualified claim intact. The
matched learned route again beats optimized fixed targeting. Its mean
net advantage in the three modeled priors is uneven.
