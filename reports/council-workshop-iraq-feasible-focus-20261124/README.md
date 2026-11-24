# France-opening Iraq feasibility twins

The six delegates negotiate over the same four packages in both
worlds. The UAE's private mandate is the only case difference.
It permits `hybrid` in the feasible world, where every delegation
can accept that package. In the impasse world the UAE excludes
`hybrid`, leaving no feasible package.

Both assignments use the same standard model-driven floor, France
opening, a 16-speech cap and a 55-call cap. The mixed assignment
uses GPT-6-Astra in the UAE seat and GPT-6.1-Sol in the other five.
The reference uses GPT-6.1-Sol throughout.

| World | All Sol | Astra in the UAE seat |
| --- | --- | --- |
| Feasible | Valid agreement in 12 speeches, 48 calls | Valid agreement in 11 speeches, 46 calls |
| Impasse | Unresolved in 16 speeches, 55 calls | Certified impasse in 14 speeches, 48 calls |

In the fresh mixed feasible run, Ghana proposed `hybrid` on
speech five and the next six speakers signed it. In the all-Sol
reference, Ghana ruled out the opening package and the UAE
proposed `hybrid` on speech six. The scorekeeper verified all
six signatures in both runs. No incompatible signature occurred
in these four trajectories. There is one run per world and
assignment.

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-iraq-feasible-focus-20261124
python3 -B "$out/compare.py" plan | cmp "$out/plan.json" -
python3 -B "$out/compare.py" score | cmp "$out/score.json" -
python3 -B research/council_workshop/replay.py "$out/mixed"
```

[Mixed feasible decision log](mixed/calls.jsonl) · [Meeting result](mixed/result.json) ·
[Paired scores](score.json) · [Mixed impasse run](../council-workshop-iraq-focus-resume-20261124/README.md)
