# Agreement when the opening draft is already feasible

This stress case follows the [Gulf of Guinea prompt comparison](../council-workshop-exclusion-transfer-20261123/README.md).
It uses the same fictional briefing menu and opens on `briefing`.
Ghana alone can rule out `review`, China alone `coastal`, and Norway
alone `regional`. All three can sign `briefing`, the only globally
feasible package. Both prompt conditions have a five-speech deadline
in the public brief and a 24-call cap. The country order is Ghana,
China, Norway. All seats use GPT-6.1-Sol.

Three signatures on the opening version suffice for agreement. If every
seat uses a separate speech to record its unique exclusion before
signing, the meeting needs at least six speeches. The five-speech cap
separates these strategies. A scripted opening-signature policy and a
scripted exclusions-first policy replay under the same rules and caps.

| Condition | Outcome | Speeches | Calls |
| --- | --- | ---: | ---: |
| Standard prompt | Valid agreement | 3 | 8 |
| Exclusions-first prompt | Unresolved, two of three signatures | 5 | 11 |
| Scripted opening signatures | Valid agreement | 3 | 7 |
| Scripted exclusions first | Unresolved, two of three signatures | 5 | 11 |

Under the standard prompt, Ghana, China and Norway each signed the
opening version. Under priority, those seats used their first three
speeches to record the three exclusions. Ghana and China signed the
unchanged version on speeches four and five. The deadline arrived before
Norway could sign. Both live runs stayed within their mandates. This is
one paired run on an intentionally tight case. It establishes a cost
that can arise when the opening draft is feasible and the instruction
requires separate speeches for exclusions and signatures.

[Standard trace](standard/calls.jsonl) · [Priority trace](priority/calls.jsonl) · [Paired readout](readout.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-opening-agreement-20261123
python3 -B "$out/readout.py" | cmp "$out/readout.json" -
```

To generate one condition again, use a fresh output directory:

```sh
kit=research/council_workshop
out=reports/council-workshop-opening-agreement-20261123
python3 -B "$kit/run.py" --case "$out/case.json" --countries GHA CHN NOR \
  --model gpt-6.1-sol --turn-cap 5 --call-cap 24 --call-timeout 90 --out runs/opening-agreement
```

Add `--prioritize-exclusions` for the priority condition.
