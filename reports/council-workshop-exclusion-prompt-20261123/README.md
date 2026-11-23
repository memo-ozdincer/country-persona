# Prompting a timely exclusion in the Council workshop

The [six-seat Iraq run](../council-workshop-iraq-pilot-20261123/README.md)
ended one exclusion short. France could rule out `closed` on speech 13,
while `aggregate` was on the floor. That was France’s last speaking turn
within the cap. The probe replays the exact observation with GPT-6.1-Sol
and adds instructions only after the original prompt. The cases,
extracted prompts, schema and targets were saved in [plan.json](plan.json)
before the fresh calls. Each row uses one fresh response.

| Snapshot | Added instruction | Action |
| --- | --- | --- |
| Iraq, France speech 13 | None | Signed `aggregate` |
| Iraq, France speech 13 | May exclude a package other than the current draft | Signed `aggregate` |
| Iraq, France speech 13 | Same permission, plus record an available exclusion before proposing or signing | Ruled out `closed` |
| Feasible Gulf of Guinea, Norway speech 3 | Same priority instruction | Signed `briefing` |

France’s signature was compatible with its own mandate. It left the
last available opportunity to exclude `closed` unused. Norway had no
available exclusions and signed a compatible draft under the same
priority instruction. The engine validates all four actions. The
comparison uses selected snapshots and one call per prompt. It measures
the observed choices at those inputs.

Using France’s prompted action, the live continuation certified the
impasse in **15 speeches and 52 calls** under the original 16-speech,
55-call limits. It reused 45 archived decisions, inserted the one
prompted decision, then collected six fresh replies with the original
instructions. The UK ruled out `aggregate` on speech 14 and Brazil
certified all four exclusions on speech 15. The original run ended
unresolved at speech 16. This is one live continuation of the selected
prefix. There was a fresh original-prompt comparison at France’s turn,
and only the prompted branch received fresh downstream replies.
[Continuation calls](continuation.jsonl) · [Result](continuation-result.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-exclusion-prompt-20261123
python3 -B "$out/probe.py" plan | cmp "$out/plan.json" -
python3 -B "$out/probe.py" score | cmp "$out/score.json" -
python3 -B "$out/continue-meeting.py" replay | cmp "$out/continuation-result.json" -
```
