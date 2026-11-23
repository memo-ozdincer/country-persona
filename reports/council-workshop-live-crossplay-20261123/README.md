# A live five-seat Astra and Sol workshop

GPT-6-Astra played Kenya and GPT-6.1-Sol played the UK, India, France
and Brazil. The mixed team certified a real impasse within the
fictional rules. The feasible twin reached a valid agreement one
speech after the original cap.

| Case | Result | Speeches | Decision calls | Reward |
| --- | --- | ---: | ---: | ---: |
| Infeasible, nine-speech cap | Certified impasse | 7 | 18 | 1 |
| Feasible, nine-speech cap | Context proposed and accepted by four of five seats | 9 | 25 | 0 |
| Feasible, same prefix with a tenth speech | Valid unanimous agreement | 10 | 30 | 1 |

The original pair fixes the model assignment, opener, seating order,
opening package and budgets. The only case change is whether the
simulated Kenya mandate includes the context package. The first five
speeches take the same actions, with some differences in phrasing.
Both teams exclude assessment and convention, and Brazil proposes
context. At speech six, Kenya accepts context in the feasible case
and rules it out in the infeasible case. The UK then declares the
certified impasse. There are no out-of-mandate acceptances in either
completed run.

The feasible state at the original cap had four signatures on the
same version and Brazil next in the queue. The continuation reuses all
25 saved decisions and makes five fresh calls, four floor polls and
Brazil's final signature. The original pair scores **1/2** under the
matched nine-speech caps. Both endpoints are observed when the longer
continuation is included. The continuation identifies what would
happen from that exact prefix. It is not a second independent sample.

The initially requested GPT-6.2-Sol failed before its first response
with a model access error from the installed Codex CLI. The successful
runs used the locally listed model IDs, Codex CLI 0.159.0, ChatGPT
subscription login and low reasoning effort. Each selected model saw
only its assigned mandate and public discussion. The floor was chosen
by the models throughout. Python checked package exclusions and
terminal outcomes. This is one live mixed roster and one opener.
Homogeneous comparisons, model/seat swaps and trials on held mandates
remain open.

[Feasible trace](feasible/calls.jsonl) ·
[Impasse trace](impasse/calls.jsonl) ·
[Continuation trace](feasible-extended/calls.jsonl) ·
[Provider failure](unsupported-sol/calls.jsonl) ·
[Replay review](review.json)

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-live-crossplay-20261123
python3 -B "$out/review.py" | cmp "$out/review.json" -
```
