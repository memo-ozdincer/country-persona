# Resuming the Norway-opening focus swap

The registered Gulf impasse varies the opening delegate and whether
Norway uses GPT-6.1-Sol or GPT-6-Astra. Ghana and China use
GPT-6.1-Sol throughout. The case, prompts, standard floor procedure,
ten-speech cap and 30-call cap are shared within each comparison.
The Norway-opening mixed run had previously stalled at call six,
Norway's floor poll.

The resume reused five exact replies and recovered seven new ones.
All twelve decisions match the all-Sol trace on speaker, action,
draft version and any package proposed or excluded. That includes
Norway's checked `briefing` exclusion on speech four. The provider
returned HTTP 429 on Norway's next floor poll at call 13.
The latest archive contains all twelve successful decisions. The
mixed cell has no terminal reward and cannot supply a matched
outcome comparison for this opening order.

| Opener | All Sol | Astra in Norway's seat |
| --- | --- | --- |
| Ghana | Unresolved in 10 speeches, 24 calls | Certified in 10 speeches, 25 calls |
| Norway | Certified in 9 speeches, 22 calls | Provider interruption after 4 speeches and 13 attempted calls |

The registered count stays at ten completed meetings and two interrupted
cells. Both earlier interruptions for this cell remain archived.

```sh
set -o pipefail
out=reports/council-workshop-norway-focus-resume-20261124
python3 -B "$out/paired.py" plan | cmp "$out/plan.json" -
python3 -B "$out/paired.py" score | cmp "$out/score.json" -
```

[Frozen request](plan.json) · [Resumed decisions and terminal error](mixed/calls.jsonl) ·
[Matched trace scores](score.json) · [Earlier attempts](../council-workshop-norway-opening-20261123/README.md)
