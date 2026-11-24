# Completing the Norway-opening focus swap

The registered Gulf impasse varies the opening delegate and whether
Norway uses GPT-6.1-Sol or GPT-6-Astra. Ghana and China use
GPT-6.1-Sol throughout. The case, prompts, standard floor procedure,
ten-speech cap and 30-call cap are shared within each comparison.
The Norway-opening mixed run had previously stalled at call six,
Norway's floor poll.

The first resume reused five exact replies and recovered seven new ones.
All twelve decisions match the all-Sol trace on speaker, action,
draft version and any package proposed or excluded. That includes
Norway's checked `briefing` exclusion on speech four. The provider
returned HTTP 429 on Norway's next floor poll at call 13.
That attempt preserved all twelve successful decisions.

| Opener | All Sol | Astra in Norway's seat |
| --- | --- | --- |
| Ghana | Unresolved in 10 speeches, 24 calls | Certified in 10 speeches, 25 calls |
| Norway | Certified in 9 speeches, 22 calls | Unresolved in 10 speeches, 25 calls |

The Gulf impasse result changes direction with the opener. Replacing
Norway's model recovered a certificate with Ghana opening and lost
it with Norway opening. There is one trajectory per assignment and
opener. The registered matrix now has eleven completed meetings
and one interrupted cell. Earlier attempts remain archived.

```sh
set -o pipefail
out=reports/council-workshop-norway-focus-resume-20261124
python3 -B "$out/paired.py" plan | cmp "$out/plan.json" -
python3 -B "$out/paired.py" score | cmp "$out/score.json" -
```

[Frozen request](plan.json) · [Resumed decisions and terminal error](mixed/calls.jsonl) ·
[Matched trace scores](score.json) · [Earlier attempts](../council-workshop-norway-opening-20261123/README.md)

## Follow-up through the ninth speech

The next resume reused all twelve replies and received twelve more.
The two assignments made the same first 17 structured decisions.
At call 18, on speech seven, Sol as Norway ruled out `regional`.
Astra as Norway instead proposed `review`. Ghana and China each
spoke once more in the mixed run. At the meeting's tenth and final speech,
the provider returned HTTP 429. Three checked exclusions were public
and `regional` was still open.

The offline check replays the exact prefix and tries all nine distinct
legal final actions. Even ruling out `regional` on that speech gives
zero reward because the protocol requires a separate declaration.
The audit establishes what the remaining budget permits on this
trace. The interrupted attempt itself has no observed terminal reward.

```sh
python3 -B "$out/paired.py" plan --followup | cmp "$out/followup-plan.json" -
python3 -B "$out/paired.py" score --followup | cmp "$out/followup-score.json" -
python3 -B "$out/paired.py" plan --final | cmp "$out/final-plan.json" -
python3 -B "$out/final-speech.py" | cmp "$out/final-speech-audit.json" -
```

[Follow-up decisions](mixed-followup/calls.jsonl) ·
[Follow-up score](followup-score.json) · [Final-speech audit](final-speech-audit.json)

## Recorded final speech

The final resume reused all 24 replies and sent one fresh model
request. Astra as Norway ruled out `regional` on speech ten. All
four verified exclusions were public at that point. The original
speech cap ended the meeting without a declaration, giving the
registered run zero reward. This records the model action predicted
to be insufficient by the offline final-speech check.

```sh
python3 -B "$out/paired.py" score --final | cmp "$out/final-score.json" -
```

[Completed decision log](mixed-final/calls.jsonl) · [Meeting result](mixed-final/result.json) ·
[Paired outcome table](final-score.json)
