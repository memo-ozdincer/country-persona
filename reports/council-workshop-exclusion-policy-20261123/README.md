# Prioritizing checked exclusions from the opening speech

The [selected-turn probe](../council-workshop-exclusion-prompt-20261123/README.md)
found that explicitly prioritizing a valid exclusion changed France's
action. The new Iraq meeting starts from the opening draft with six
GPT-6.1-Sol delegates. Each speech prompt appends the same instruction.
Floor and ballot prompts use the original wording. The instruction
allows any still-unexcluded package outside the speaker's mandate to
be ruled out and asks the speaker to do so before proposing or signing.
The facilitator uses the same rules for validating signatures and
certifying impasse in both conditions.

| Case | Standard instruction | Exclusions first |
| --- | --- | --- |
| Impasse | Unresolved after 16 speeches and 55 calls, three of four exclusions recorded | Certified in 7 speeches and 21 calls |
| Feasible | Agreement on `hybrid` in 12 speeches and 48 calls | Agreement on `hybrid` in 12 speeches and 41 calls |

In the impasse run, France ruled out `closed` in the opening speech.
The other sole holders supplied their exclusions by speech six. Three
of the four exclusions named a package other than the current draft.
France certified the result on speech seven. In the feasible twin, both
runs signed the only package all six mandates allow. The priority run
recorded all three available exclusions. The standard run recorded one.
Both used 12 speeches, and the difference in call count came from floor
polls. Across the four meetings, all signatures were within the
signer's mandate.

Each case pairs identical mandates, seat order, model and caps of 16
speeches and 55 calls. The standard impasse run came from the earlier
archive. The other three meetings were fresh from the opening. Each
condition has a single trajectory. The tested case and opener were
already used to develop the instruction.

[Standard impasse trace](../council-workshop-iraq-pilot-20261123/all-sol/calls.jsonl) ·
[Priority impasse trace](iraq-impasse-priority/calls.jsonl) ·
[Standard feasible trace](iraq-feasible-standard/calls.jsonl) ·
[Priority feasible trace](iraq-feasible-priority/calls.jsonl) ·
[Paired scores and timing](readout.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-exclusion-policy-20261123
python3 -B "$out/readout.py" | cmp "$out/readout.json" -
```

From the repository root, use a fresh output directory to rerun the
priority condition:

```sh
kit=research/council_workshop
case_file=$(mktemp)
python3 -B "$kit/held_suite.py" case iraq impasse > "$case_file"
python3 -B "$kit/run.py" --case "$case_file" --countries FRA GBR BRA JPN GHA ARE \
  --model gpt-6.1-sol --turn-cap 16 --call-cap 55 --call-timeout 90 \
  --prioritize-exclusions --out runs/iraq-priority
```
