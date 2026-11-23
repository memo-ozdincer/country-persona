# One public rejection, two possible outcomes

This matched pair begins with the [rejected opening](../council-workshop-rejected-opening-20261123/README.md).
The infeasible world removes only `briefing` from Norway's private
mandate. The public menu, published five-speech deadline, 24-call cap,
country order and other mandates are identical. Both witnesses begin
with Ghana ruling out `review` and China receiving the next turn.
China's second-speech prompt is byte-identical across worlds within
each prompt condition.

| World | Required second speech | Remaining actions within the cap |
| --- | --- | --- |
| `briefing` feasible | Propose `briefing` | Three signatures |
| No feasible package | Rule out `coastal` | Norway's two checked exclusions and a declaration |

Four speeches remain after Ghana's exclusion. Agreement spends all
four on the proposal and signatures. Impasse spends all four on three
checked exclusions and certification. China is the only seat with
authority to rule out `coastal`, so it must use speech two for that
exclusion in the impasse world. Both outcomes are individually reachable
under the registered caps, as the scripted witnesses show. The needed
actions differ on the identical observation. Any shared policy succeeds
in at most one world, or **50%** under an equal prior, even with the
best legal continuation. Randomizing the second action has the same
upper bound.

At the same frozen decision, one standard-prompt Sol call proposed
`briefing`. One Sol call with exclusion priority after rejection ruled
out `coastal`. The first preserves the feasible endpoint and the second
preserves the impasse endpoint. These are individual decisions at the
shared observation. Their ceilings assume scripted or otherwise ideal
later decisions, and no full live meeting was run for either world.

Giving the group **one extra speech** raises the ceiling to **100%** in
this pair. The same scripted policy proposes `briefing` in both worlds.
Norway's third speech either signs or rules it out, according to its own
mandate. The script uses that public action to route later turns, reaching
agreement at speech five and certified impasse at speech six. Both runs
keep the 24-call cap. This is a controlled turn-routing witness for the
task, with no extra information supplied to individual speakers.

[Frozen cases and second-speech inputs](fork.json) · [Live decision scores](score.json) ·
[Six-speech witness](budget-relaxation.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-rejection-fork-20261123
python3 -B "$out/fork.py" build | cmp "$out/fork.json" -
python3 -B "$out/fork.py" score | cmp "$out/score.json" -
python3 -B "$out/budget-relaxation.py" | cmp "$out/budget-relaxation.json" -
```
