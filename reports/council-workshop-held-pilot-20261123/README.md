# Held Council workshop pilot

The [registered suite](../../research/council_workshop/held-cases.json)
adds a three-seat Gulf of Guinea maritime briefing and a six-seat Iraq
consultation-summary workshop. Their two private-mandate variants and
two opening orders produce eight case and order combinations. The
seat-local scripted control reaches the right endpoint on all eight.
Case text, rosters, model assignments and budgets were committed in
`3f83cdb` before either live run.

The live pilot uses the Gulf of Guinea impasse with Ghana opening.
Only Norway can rule out either `briefing` or `regional`. The other two
participants each hold one of the remaining exclusions. A certificate
requires all four. The two arms keep Ghana and China on GPT-6.1-Sol and
use GPT-6.1-Sol or GPT-6-Astra for Norway. Both allow ten speeches and
thirty calls, use the model-driven floor, and omit advisory ballots.

| Roster | Result | Speeches | Calls | Checked exclusions |
| --- | --- | ---: | ---: | ---: |
| All Sol | Unresolved at speech cap | 10 | 24 | 3/4 |
| Astra in Norway, Sol in Ghana and China | Certified impasse | 10 | 25 | 4/4 |
| Checked-exchange script | Certified impasse | 7 | 15 | 4/4 |

With Sol, Norway proposed two packages before excluding `regional` on
speech nine. It never excluded `briefing`. With Astra, Norway proposed
once and recorded both exclusions on speeches six and nine. Ghana's
last speech cited all four checked rejections and declared impasse.
The other seats' earlier decisions also differed between runs. The
comparison measures the whole meeting after a one-seat model swap.
It gives no estimate of how the models would act from identical later
transcripts. Both live runs had zero incompatible signatures.

This covers **2 of 32 live cells**, one case and one opener. The other
opening order, feasible twin, six-seat family and reciprocal swap remain
unrun. The fictional mandates were held out of the workshop fits. Earlier
drafting experiments used the public historical source records.

[All-Sol trace](all-sol/calls.jsonl) ·
[Mixed trace](sol-with-astra-norway/calls.jsonl) · [Paired score](score.json)

## Replay

From the repository root:

```sh
set -o pipefail
kit=research/council_workshop
out=reports/council-workshop-held-pilot-20261123
python3 -B "$kit/held_suite.py" audit | cmp "$kit/held-control-audit.json" -
python3 -B "$kit/held_suite.py" score "$out/all-sol" "$out/sol-with-astra-norway" | cmp "$out/score.json" -
```

The [workshop guide](../../research/council_workshop/README.md#evaluate-on-additional-case-families)
has the live commands. The case topics use archived source joins. The
briefing options and private mandates are newly authored simulations.
The pilot tests procedural decisions. The
[historical deliberation benchmark](../../research/unsc-marl-20261119/benchmark-v1.7/README.md)
grades source-faithful final records.
