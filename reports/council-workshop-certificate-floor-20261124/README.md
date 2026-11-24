# Direct floor handoff after the final checked exclusion

After 53 calls in the UAE-opening Iraq workshop, all four checked
exclusions were public and Brazil was first in the speaking queue.
The default procedure polled France and the UK. Both passed and the
55-call cap ended the meeting. With the opt-in direct handoff, Brazil
received the floor on call 54 and a fresh GPT-6.1-Sol reply declared
the certified impasse.

| Procedure | Call cap | Calls used | Speeches | Outcome |
| --- | ---: | ---: | ---: | --- |
| Registered procedure | 55 | 55 | 15 | Unresolved, four checked exclusions |
| Registered procedure with one extra call | 56 | 56 | 16 | Brazil declares impasse |
| Direct handoff using the archived Brazil reply | 55 | 54 | 16 | Brazil declares impasse |
| Direct handoff with a fresh Brazil reply | 55 | 54 | 16 | Brazil declares impasse |

The replay checks the full request for each of the first 53 calls.
Both direct-handoff runs use the exact same Brazil prompt and schema
as the archived call 56. The moderator bypasses the poll only when
all options have checked public exclusions and the queue already has
a speaker. It gives that speaker the floor and the usual action
validation applies. The experiment uses one selected continuation and
one fresh model decision. Registered scores retain the original floor
procedure.

Run these offline from the repository root:

```sh
python3 -B reports/council-workshop-certificate-floor-20261124/study.py plan
python3 -B reports/council-workshop-certificate-floor-20261124/study.py replay
```

[Frozen plan](plan.json) · [Fresh request and reply](live.jsonl) ·
[Result](live-result.json) · [Original meeting](../council-workshop-all-sol-matrix-20261123/iraq-uae-impasse/result.json)
