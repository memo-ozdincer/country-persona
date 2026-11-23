# Rotating the Gulf impasse to a Norway opening

The [registered Gulf impasse](../../research/council_workshop/held-cases.json)
has no feasible package. Norway alone can rule out `briefing` and
`regional`. The first comparison used Ghana, China, Norway. This one
rotates the same seats to Norway, Ghana, China and keeps the case,
standard prompts, model assignments, ten-speech cap and 30-call cap.
The models request the floor in both orders. The mixed assignment uses
GPT-6-Astra for Norway and GPT-6.1-Sol for Ghana and China. The reference
uses GPT-6.1-Sol in every seat.

| Opener | All Sol | Astra in Norway's seat |
| --- | --- | --- |
| Ghana | Unresolved in 10 speeches, 24 calls | Certified in 10 speeches, 25 calls |
| Norway | Certified in 9 speeches, 22 calls | Provider interrupted after 2 speeches and 6 attempted calls |

In the Norway-opening all-Sol run, Norway first accepted `coastal`
within its own mandate. It excluded `briefing` while that proposal was
current on speech four, then used speech seven to exclude `regional`
while `coastal` was still current. China declared the impasse on speech
nine. The Ghana-opening all-Sol run recorded only the `regional`
exclusion from Norway. Neither run recorded an incompatible signature.

The mixed run reached two speeches before the provider rate-limited
Norway's floor poll. A single resume reused the five available replies
and failed on the same unanswered poll. Both attempts remain archived,
and the scorecard records this as one interrupted cell with no reward.
Sol's different outcomes demonstrate sensitivity to the opening order in
these two trajectories. The mixed comparison has a completed pair only
with Ghana opening.

[All-Sol trace](all-sol/calls.jsonl) · [Mixed attempt](sol-with-astra-norway/calls.jsonl) ·
[Resumed attempt](sol-with-astra-norway-resumed/calls.jsonl) · [Matched readout](score.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-norway-opening-20261123
prior=reports/council-workshop-held-pilot-20261123
python3 -B research/council_workshop/held_suite.py score --trace \
  "$prior/all-sol" "$prior/sol-with-astra-norway" \
  "$out/all-sol" "$out/sol-with-astra-norway-resumed" | cmp "$out/score.json" -
```
