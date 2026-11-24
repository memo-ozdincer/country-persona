# Live floor decisions at the Iraq call limit

The [exact queue search](../council-workshop-exact-impasse-reachability-20261123/README.md)
found a scripted way to certify the UAE-opening Iraq impasse within
55 calls. France can join the queue at call 52 and thereby skip a
second poll before Brazil's turn. This comparison tests that opportunity
with fresh GPT-6.1-Sol replies.

Both runs reuse the first 51 exact archived calls. The standard arm
asks France the original floor question. The other arm appends a
reminder that a request joins the back of the queue and that queued
delegates are skipped in later polls. It permits requesting the floor
for that reason. The reminder names neither the expected certificate
nor a desired answer. All subsequent decisions use the original
prompts. The [frozen plan](plan.json) retains the 16-speech and 55-call
caps and the delegate declaration rule.

| Prompt at call 52 | France at call 52 | France at call 54 | Result |
| --- | --- | --- | --- |
| Standard | Pass | Pass | Unresolved, 15 speeches, 55 calls |
| Queue reminder | Pass | Request floor | Unresolved, 15 speeches, 55 calls |
| Queue reminder and remaining budget | Pass | Pass | Unresolved, 15 speeches, 55 calls |

After the two initial runs, a follow-up added the exact budget to the
reminder. It stated that call 52 was in progress and three calls would
remain after the reply. It used the same prefix and standard prompts
after that decision. The [follow-up plan](budget-cue/plan.json) freezes
the extra sentence. The UK supplied the fourth exclusion on speech 15
in all runs. France's second poll and the UK's poll used the last two
calls, leaving Brazil next without a declaration. In the reminder arm,
France joined the queue only after the second poll had already been
made.

Each condition has one live continuation. Both reminders failed to
elicit the budget-saving floor request on this input. The scripted
queue witness remains a separate feasibility result.

[Standard and reminder scores](score.json) · [Budget follow-up trace](budget-cue/priority.jsonl) ·
[Budget follow-up result](budget-cue/priority-result.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-live-floor-recovery-20261124
python3 -B "$out/paired-floor.py" plan | cmp "$out/plan.json" -
python3 -B "$out/paired-floor.py" score | cmp "$out/score.json" -
python3 -B "$out/paired-floor.py" budget-plan | cmp "$out/budget-cue/plan.json" -
python3 -B "$out/paired-floor.py" budget-replay | cmp "$out/budget-cue/priority-result.json" -
```
