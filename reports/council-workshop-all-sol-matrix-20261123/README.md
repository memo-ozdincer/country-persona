# Completing the same-model workshop matrix

The [registered standard-prompt suite](../../research/council_workshop/held-cases.json)
crosses two case families, two private-mandate variants and two opening
orders. This report adds the three remaining all-Sol cells. Norway opens
the Gulf feasible case, and the UAE opens each Iraq case. All delegates
use GPT-6.1-Sol. Model floor requests, case menus, turn and call limits
follow the original registration. The Gulf permits ten speeches and 30
calls, and Iraq permits 16 speeches and 55 calls.

| Case | Opener | Feasible | Impasse |
| --- | --- | --- | --- |
| Gulf | Ghana | Agreement in 5 speeches, 13 calls | Unresolved in 10 speeches, 24 calls |
| Gulf | Norway | Agreement in 6 speeches, 17 calls | Certified in 9 speeches, 22 calls |
| Iraq | France | Agreement in 12 speeches, 48 calls | Unresolved in 16 speeches, 55 calls |
| Iraq | UAE | Agreement in 12 speeches, 53 calls | Unresolved in 15 speeches, 55 calls |

The completed all-Sol slice has **4 of 4 feasible agreements and 1 of
4 certified impasses**. Each cell is one trajectory, and opener rotations
reuse the same case. With Norway opening, the Gulf feasible run added an
opening signature that was cleared when China proposed `briefing`. The
same three signatures on the replacement then completed agreement. In
Iraq, both openings led to unanimous acceptance of `hybrid` in twelve
speeches, and the UAE-opening run used five more floor calls.

In the UAE-opening impasse, all four exclusions were already public at
speech 15. The floor poll consumed the last of 55 calls with Brazil
next in the queue. Increasing only the call cap to 56 reused all 55
archived decisions and required a single fresh decision. Brazil cited
all four exclusions and certified the impasse on speech 16. The
continuation is outside the registered count. It distinguishes a
call-budget stop from a missing certificate ingredient on that trace.

[Norway-opening feasible trace](guinea-norway-feasible/calls.jsonl) ·
[UAE-opening feasible trace](iraq-uae-feasible/calls.jsonl) ·
[UAE-opening impasse trace](iraq-uae-impasse/calls.jsonl) ·
[One-call continuation](continuation.json)

## Replay

```sh
set -o pipefail
kit=research/council_workshop
out=reports/council-workshop-all-sol-matrix-20261123
python3 -B "$kit/held_suite.py" score --trace "$out/guinea-norway-feasible" \
  "$out/iraq-uae-impasse" "$out/iraq-uae-feasible" | cmp "$out/score.json" -
python3 -B "$out/verify-continuation.py" | cmp "$out/continuation.json" -
python3 -B "$kit/scorecard.py" | cmp "$kit/scorecard.json" -
```
