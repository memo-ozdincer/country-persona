# Gulf feasibility and opening-order comparison

The Gulf workshop crosses two opening orders, two private-mandate
variants and two model assignments. All meetings use the registered
standard floor procedure, a ten-speech cap and a 30-call cap. The
mixed roster uses GPT-6-Astra for Norway and GPT-6.1-Sol for Ghana
and China. The reference uses GPT-6.1-Sol throughout.

The feasible variant lets Norway accept `briefing` and `regional`,
both of which Ghana and China can also accept. The impasse variant
removes those two options from Norway's private mandate. The public
options and the other two mandates stay fixed.

| Opening delegate | Variant | All Sol | Astra in Norway's seat |
| --- | --- | --- | --- |
| Ghana | Feasible | Agreement on `briefing` in 5 speeches, 13 calls | Agreement on `briefing` in 5 speeches, 13 calls |
| Norway | Feasible | Agreement on `briefing` in 6 speeches, 17 calls | Agreement on `briefing` in 7 speeches, 19 calls |
| Ghana | Impasse | Unresolved in 10 speeches, 24 calls | Certified in 10 speeches, 25 calls |
| Norway | Impasse | Certified in 9 speeches, 22 calls | Unresolved in 10 speeches, 25 calls |

In the fresh run, China ruled out the opening `coastal` package
on speech three. Norway proposed `briefing` next, and the three
delegates signed that version. In the all-Sol reference, China
proposed `briefing` on speech three. The mixed run used one extra
speech and two extra calls.

All four feasible runs reached agreement. Each assignment certified
one of its two impasses, with different openers. Each cell contains
one trajectory. None of the eight runs recorded an incompatible
signature.

```sh
set -o pipefail
out=reports/council-workshop-gulf-feasible-focus-20261124
python3 -B "$out/compare.py" plan | cmp "$out/plan.json" -
python3 -B "$out/compare.py" score | cmp "$out/score.json" -
python3 -B research/council_workshop/replay.py "$out/mixed"
```

[Mixed feasible decision log](mixed/calls.jsonl) · [Meeting result](mixed/result.json) ·
[All eight scores](score.json) · [Norway-opening impasse](../council-workshop-norway-focus-resume-20261124/README.md)
