# Held Council workshop pilot

The [registered suite](../../research/council_workshop/held-cases.json)
adds a three-seat Gulf of Guinea maritime briefing and a six-seat Iraq
consultation-summary workshop. Their two private-mandate variants and
two opening orders produce eight case and order combinations. The
seat-local scripted control reaches the right endpoint on all eight.
Case text, rosters, model assignments and budgets were committed in
`3f83cdb` before the live runs.

The live pilot uses both Gulf of Guinea variants with Ghana opening.
In the impasse case, Norway's mandate excludes both `briefing` and
`regional`. In the feasible case it allows both.
Only Norway can rule out either `briefing` or `regional`. The other two
participants each hold one of the remaining exclusions. A certificate
requires all four. The two arms keep Ghana and China on GPT-6.1-Sol and
use GPT-6.1-Sol or GPT-6-Astra for Norway. Both allow ten speeches and
thirty calls, use the model-driven floor, and omit advisory ballots.

| Roster | Feasible | Impasse |
| --- | --- | --- |
| All Sol | Valid agreement in 5 speeches, 13 calls | Unresolved after 10 speeches, 24 calls, 3 of 4 exclusions |
| Astra in Norway, Sol in Ghana and China | Valid agreement in 5 speeches, 13 calls | Certified impasse in 10 speeches, 25 calls, 4 of 4 exclusions |
| Checked-exchange script | Valid agreement in 6 speeches, 13 calls | Certified impasse in 7 speeches, 15 calls, 4 of 4 exclusions |

In the feasible case, both live runs followed the same sequence of
speakers, actions and draft versions. Ghana accepted the opening
package. China proposed `briefing` on speech two, clearing that signature.
Norway, Ghana and China then signed the new version. Either `briefing`
or `regional` would have earned full credit. Both runs chose `briefing`.

In the impasse case with Sol, Norway proposed two packages before excluding `regional` on
speech nine. It never excluded `briefing`. With Astra, Norway proposed
once and recorded both exclusions on speeches six and nine. Ghana's
last speech cited all four checked rejections and declared impasse.
The other seats' earlier decisions also differed between runs. The
comparison measures the whole meeting after a one-seat model swap.
It gives no estimate of how the models would act from identical later
transcripts. All four live runs had zero incompatible signatures.

This covers **4 of 32 live cells**, two variants of one case with one
opener. The other opening order, six-seat family and reciprocal swap
remain unrun. The fictional mandates were held out of the workshop fits. Earlier
drafting experiments used the public historical source records.

[Feasible all-Sol](feasible-all-sol/calls.jsonl) · [Feasible mixed](feasible-sol-with-astra-norway/calls.jsonl) ·
[Impasse all-Sol](all-sol/calls.jsonl) · [Impasse mixed](sol-with-astra-norway/calls.jsonl) · [Joint score](twin-score.json)

## Replay

From the repository root:

```sh
set -o pipefail
kit=research/council_workshop
out=reports/council-workshop-held-pilot-20261123
python3 -B "$kit/held_suite.py" audit | cmp "$kit/held-control-audit.json" -
python3 -B "$kit/held_suite.py" score "$out/all-sol" "$out/sol-with-astra-norway" | cmp "$out/score.json" -
python3 -B "$kit/held_suite.py" score "$out/all-sol" "$out/sol-with-astra-norway" \
  "$out/feasible-all-sol" "$out/feasible-sol-with-astra-norway" | cmp "$out/twin-score.json" -
```

The [workshop guide](../../research/council_workshop/README.md#evaluate-on-additional-case-families)
has the live commands. The case topics use archived source joins. The
briefing options and private mandates are newly authored simulations.
The pilot tests procedural decisions. The
[historical deliberation benchmark](../../research/unsc-marl-20261119/benchmark-v1.7/README.md)
grades source-faithful final records.
