# Floor participation and mandate compliance

Swapping the labels for request and pass changed none of the ten
frozen Qwen3.5-4B floor decisions. The request-minus-pass margin stayed
negative in both label orders. Averaged margins ranged from −0.500
to −0.375. Under a fixed speaking rotation, the same model reached
unanimity in both worlds, including the world where no valid agreement
was possible.

| Case | Frozen floor poll | Fixed rotation with Qwen | Fixed rotation with scripted speeches |
| --- | --- | --- | --- |
| Feasible | Unresolved, 6 slots | Valid agreement, 31 slots | Valid agreement, 43 slots |
| Infeasible | Unresolved, 6 slots | Invalid agreement, 31 slots | Certified impasse, 31 slots |

Both rotation runs reuse the exact original UK proposal. The
facilitator assigns the next seat in cyclic order. Scripted floor
decisions count toward the 50-slot cap in both rotation conditions,
while fresh model calls occur only for Qwen speeches. Each Qwen run
uses five fresh speech decisions. The label swap is an isolated probe
on the recorded first poll, with no rollout attribution.

The two Qwen transcripts contain the same opening and the same five
accepts. In the infeasible world the Kenya seat had the option to rule
out the context package. It instead ranked accepting first. Ruling
out context was the next highest recorded choice, ahead of proposing
assessment by 0.125 logits. That ranking gives a concrete local
contrast for training or a mandate check. It gives no evidence of
what later turns would do after that decision changed.

The script reaches both correct endpoints starting from the same draft,
rotation and budget. The intervention therefore shows failures on two
different decisions. The model passed when it needed to seek the floor,
then accepted a package outside its private mandate once given the floor.
The comparison uses one roster, one opener, two matched fictional
cases and a frozen Qwen checkpoint. The results do not compare
language generation or performance on unseen mandates.

The worker used NVIDIA RTX PRO 6000 Blackwell Server Edition on
Aurora and exited normally. There were 20 fresh first-token reads
across the floor probes and rotated speeches, using 10,112 input
tokens. The matched script uses no model calls. The replay checks
input tokens, raw logits, action selection, floor decisions and
the terminal score. The workshop suite passed 20 tests on Python
3.12. The project suite passed 278 tests with seven skips on Python
3.11, including the diagnostic test that requires Python 3.12.

[Locked inputs](plan.json) · [Floor probes](floor-probes.jsonl) ·
[Feasible replay](feasible/calls.jsonl) · [Impasse replay](impasse/calls.jsonl) ·
[Verification](verification.json) · [Matched script](control.json)

From the repository root in the Qwen Python 3.12 environment:

```sh
set -o pipefail
out=reports/council-workshop-floor-diagnostic-20261123
model=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["baseline"]["model"])' "$out/plan.json")
python3 -B research/council_workshop/floor_diagnostic.py verify --model "$model" --out "$out" | cmp "$out/verification.json" -
python3 -B "$out/control.py" | cmp "$out/control.json" -
```
