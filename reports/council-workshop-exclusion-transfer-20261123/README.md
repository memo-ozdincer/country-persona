# Exclusion-priority prompt in the Gulf of Guinea workshop

The instruction developed in the [six-seat Iraq workshop](../council-workshop-exclusion-policy-20261123/README.md)
was applied from the first speech of the three-seat Gulf of Guinea
workshop. The comparison uses the two archived all-Sol standard-prompt
runs from the [Gulf pilot](../council-workshop-held-pilot-20261123/README.md)
and fresh interventions with the same model and roster. Ghana opens,
China and Norway follow in the seat order, and the limits are ten
speeches and 30 calls. Only the speech prompts gain the new instruction.

In the impasse case, Norway alone can rule out `briefing` and
`regional`. Its feasible twin allows both. Ghana and China each hold
one checked exclusion in either case.

| Case | Standard instruction | Exclusions first |
| --- | --- | --- |
| Impasse | Unresolved after 10 speeches and 24 calls, three of four exclusions recorded | Certified in 7 speeches and 17 calls |
| Feasible | Agreement on `briefing` in 5 speeches and 13 calls | Agreement on `briefing` in 6 speeches and 14 calls |

Norway used its first speech in the prompted impasse run to rule out
`briefing` while `coastal` was current. It ruled out `regional` on speech
six, and Ghana certified the impasse on speech seven. The archived run
had three Norwegian speaking turns and ended without the `briefing`
exclusion. In the feasible twin, Ghana and China used their first turns
to supply checked exclusions. Norway then proposed `briefing`, and all
three signed it. The extra checking took one additional speech and call
in the observed pair. Every signature in the four runs was compatible
with its speaker's mandate.

The exact instruction transfers to a different case and team size from
the Iraq development study. Both families use the same finite-mandate
protocol and GPT-6.1-Sol. This comparison covers one opener and one
trajectory per condition in each twin.

[Standard impasse trace](../council-workshop-held-pilot-20261123/all-sol/calls.jsonl) ·
[Priority impasse trace](guinea-impasse-priority/calls.jsonl) ·
[Standard feasible trace](../council-workshop-held-pilot-20261123/feasible-all-sol/calls.jsonl) ·
[Priority feasible trace](guinea-feasible-priority/calls.jsonl) · [Paired readout](transfer.json)

## Replay and reproduce

```sh
set -o pipefail
out=reports/council-workshop-exclusion-transfer-20261123
python3 -B "$out/transfer.py" | cmp "$out/transfer.json" -
```

For a new live trial, export the case and use a fresh output directory:

```sh
kit=research/council_workshop
case_file=$(mktemp)
python3 -B "$kit/held_suite.py" case guinea impasse > "$case_file"
python3 -B "$kit/run.py" --case "$case_file" --countries GHA CHN NOR \
  --model gpt-6.1-sol --turn-cap 10 --call-cap 30 --call-timeout 90 \
  --prioritize-exclusions --out runs/guinea-priority
```
