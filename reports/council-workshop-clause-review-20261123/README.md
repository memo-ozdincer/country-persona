# Review the exact clauses from the Astra and Sol workshop

Astra reached unanimous agreement on the literal text of version 7.
Sol hit the cap on version 14 with India voting yes and the UK and
France voting no. Both final clauses preserved the three India
criteria. Neither explicitly directed UN reporting on the link between
climate and security or an assessment of the implications for peace
and security. Both cleared the factual guard.

| Run | Procedure | Clause coverage /70 | Released lower bound |
| --- | --- | ---: | ---: |
| Astra | Unanimous acceptance, 11 turns | 35–40 | 35 |
| Sol | Cap reached, 20 turns | 40 | 40 |

Astra invited the use of climate findings where relevant to a region
or issue under consideration, without an express agenda or mandate
limitation. The review marks that five-point scope criterion uncertain.
Sol limited the use to matters directly covered by existing Council
reporting mandates and earned those five points. The upper bound for
Astra ties Sol. Differences in simulated acceptance therefore cannot
serve as a measure of clause coverage.

The [rubric](../../research/council_workshop/climate-review.json) uses
dated delegation preferences as evidence. Its weights and grades are
retrospective assistant annotations on familiar runs. The scores
measure explicit source-backed content and give no evidence about
binding private instructions or whether every criterion can be met
simultaneously. The export omits the model, decision history and
outcome so a separate reviewer can independently grade the text.
Independent reviewer agreement remains unmeasured.

[Source case](../../research/council_workshop/climate.json) ·
[Astra verdict](astra-verdict.json) · [Sol verdict](sol-verdict.json) ·
[Astra score](astra-score.json) · [Sol score](sol-score.json)

Run from the repository root:

```sh
set -o pipefail
review=reports/council-workshop-clause-review-20261123
for model in astra sol; do
  python3 -B research/council_workshop/review.py \
    "reports/council-workshop-20-20261123/$model" \
    --verdict "$review/$model-verdict.json" | cmp "$review/$model-score.json" -
done
```
