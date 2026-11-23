# A feasible replacement after a checked rejection

This case changes only the opening draft of the
[five-speech opening-agreement test](../council-workshop-opening-agreement-20261123/README.md).
`review` replaces `briefing` as the opening. Ghana alone can rule out
`review`, China alone `coastal`, and Norway alone `regional`. All seats
can sign `briefing`, the sole feasible replacement. The public brief
still specifies five speeches. The run cap is 24 calls, and the same
GPT-6.1-Sol seats speak in the same order.

After one checked rejection, a proposal and three signatures can finish
in five speeches. If the team records all three checked exclusions
before it proposes or signs, the minimum rises to seven. The scripted
controls use each seat's own mandate and the public record. The
replacement-first script chooses the first surviving package within the
speaker's mandate, in alphabetical order. The witness demonstrates
reachability for this specific menu.

| Condition | Outcome | Speeches | Calls |
| --- | --- | ---: | ---: |
| Standard prompt | Agreement on `briefing` | 4 | 10 |
| Conditional prompt | Unresolved with one signature on `briefing` | 5 | 11 |
| Scripted replacement after one rejection | Agreement on `briefing` | 5 | 11 |
| Scripted exclusions after rejection | Unresolved with one signature on `briefing` | 5 | 11 |

The standard run used the first speech to propose `briefing`. All three
delegates then signed. The conditional run recorded three exclusions,
proposed the same replacement on speech four, and had room for one
signature. Every recorded signature was within the speaker's mandate.
The scripted comparison starts both branches with the same checked
rejection and reproduces the cost of collecting the other two exclusions
before proposing a replacement. The live comparison has one trajectory
per prompt on this case.

[Standard trace](standard/calls.jsonl) · [Conditional trace](after-rejection/calls.jsonl) ·
[Exact outcomes and scripted witnesses](readout.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-rejected-opening-20261123
python3 -B "$out/readout.py" | cmp "$out/readout.json" -
```
