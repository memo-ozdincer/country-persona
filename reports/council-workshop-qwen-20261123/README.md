# Frozen Qwen on the five-seat mandate cases

Qwen3.5-4B proposed the context package as the UK in both cases,
then every delegate passed at the first floor poll. Both episodes
were unresolved and earned zero. The proposed package was feasible
in one workshop, while the other workshop had no feasible package.

| Case | First proposal | Finish | Turns | Decision calls | Input tokens | Reward |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| Feasible | Context | All passed | 1 | 6 | 2,502 | 0 |
| Impasse | Context | All passed | 1 | 6 | 2,499 | 0 |

No role accepted a draft or placed a verified exclusion on the
record. In the impasse case the Kenya role's simulated mandate
excluded the proposed package, yet it chose to pass. Across both
cases, every floor decision preferred pass by 0.375–0.625 raw logit
points. The floor labels were fixed. This leaves the effect of
answer order open. The results identify a point where the meeting
stops before testing acceptance strategy or impasse certification.

The evaluator used the same private views, five-seat engine and
terminal reward as the [scripted controls](../council-workshop-mandates-20261123/README.md).
The model selected one legal structured menu action from first-token
logits. An exclusion or impasse choice only appeared when its local
or public prerequisites held. Acceptance and proposals for packages
outside a role's mandate remained selectable. This separates the
model's decisions from free-form JSON format errors. The runner used
a 20-speech and 50-call cap with advisory ballots disabled.

The evidence covers one seating order on two exposed synthetic cases.
The same frozen checkpoint served all seats. The runs used
NVIDIA RTX PRO 6000 Blackwell Server Edition on Aurora and the
recorded worker exited normally. There were no model-weight updates.
The tokenizer and saved logits replay verifies all 12 model choices,
the resulting meetings and the exact rewards.

[Launch receipt](launch.json) · [Locked plan](plan.json) ·
[Feasible trace](feasible/calls.jsonl) · [Impasse trace](impasse/calls.jsonl) ·
[Score and token verification](verification.json) · [Action audit](audit.json)

From the repository root, in the project Qwen Python 3.12 environment:

```sh
set -o pipefail
out=reports/council-workshop-qwen-20261123
model=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["model"])' "$out/plan.json")
python3 -B research/council_workshop/local_baseline.py verify --model "$model" --out "$out" | cmp "$out/verification.json" -
python3 -B "$out/audit.py" | cmp "$out/audit.json" -
```
