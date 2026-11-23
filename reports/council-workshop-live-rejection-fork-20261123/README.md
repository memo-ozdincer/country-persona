# Live decisions in the six-speech feasibility fork

The [matched fork](../council-workshop-rejection-fork-20261123/README.md)
has two worlds that differ only in whether Norway can sign `briefing`.
Its scripted bound reaches both outcomes in six speeches and at most
24 calls. This trial keeps that budget and tests each world with
GPT-6.1-Sol on the standard speech prompts.

The opening rejection and floor routing are scripted. Ghana first
rules out `review`, China takes speech two, and Norway takes speech
three. Later routing uses Norway's public third action. China's
second-speech reply is generated once in the feasible world and reused
for the infeasible world only after checking the full prompt and schema
for equality. Subsequent speeches are fresh model calls in each world.
The logs label fixed, reused and model decisions separately.

| World | Norway's third speech | Outcome | Speeches | Logical calls |
| --- | --- | --- | ---: | ---: |
| Feasible | Signed `briefing` | Valid agreement | 5 | 17 |
| Infeasible | Proposed `coastal` | Unresolved, missing the `regional` exclusion | 6 | 21 |

China proposed `briefing` at the shared second speech. In the feasible
world the three delegates signed it. In the infeasible world Norway
proposed `coastal`, China excluded it, Norway excluded `briefing`, and
Ghana proposed `regional`. After Norway's alternative on speech three,
the group needed three checked exclusions and a declaration with only
three speeches left. Every recorded signature was within the speaker's
mandate. Each row used four fresh speech calls. The remaining logical
calls were scripted or reused.

The [substitution trace](impasse-checked-rejection.jsonl) reuses the same
opening and China reply, matches Norway's original prompt, and replaces
its third speech with a checked rejection of `briefing`. It keeps the
same speaker routing and generates three fresh standard-prompt speeches.
China rules out `coastal`, Norway rules out `regional`, and Ghana certifies
the impasse on speech six. The run again uses 21 logical calls. This
controlled continuation shows the next three delegates can complete the
certificate once the missing checked rejection is on the record. The
substitution is scripted and its downstream responses are one sample.

[Feasible trace](feasible.jsonl) · [Infeasible trace](impasse.jsonl) ·
[Substitution result](impasse-checked-rejection-result.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-live-rejection-fork-20261123
for world in feasible impasse impasse-checked-rejection; do
  python3 -B "$out/rollout.py" replay "$world" | cmp "$out/$world-result.json" -
done
```
