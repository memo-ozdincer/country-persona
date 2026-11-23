# Five-seat all-Sol control

The comparison changes the opening seat, Kenya, from GPT-6-Astra to
GPT-6.1-Sol. The other four seats use GPT-6.1-Sol throughout. Each case
uses the same fictional mandate cards, menus, opening draft, seat order,
nine-speech limit and 50-call limit as the [mixed roster](../council-workshop-live-crossplay-20261123/README.md).
Models choose who requests the floor. Python checks decisions and the
terminal outcome. No advisory ballots run.

| Condition | Feasible at nine speeches | Impasse at nine-speech cap | Feasible continuation |
| --- | --- | --- | --- |
| Astra in Kenya, Sol elsewhere | Four signatures, 25 calls | Certified in 7 speeches, 18 calls | Valid agreement at speech 10, 30 calls |
| All Sol | Four signatures, 26 calls | Certified in 7 speeches, 17 calls | Valid agreement at speech 10, 31 calls |
| Checked-exchange script | Valid agreement in 9 speeches, 21 calls | Certified in 4 speeches, 11 calls | Already terminal |

Both live rosters earn **1/2** at the original cap. Their public speaker,
action and version sequences match in each case, with differences in floor
polls and phrasing. Neither records an incompatible signature. Both first
record Kenya and the UK accepting the opening package. Brazil proposes the
context package on speech five. That proposal clears the earlier signatures.
Kenya then accepts context when its mandate permits it and rules it out
when its mandate excludes it. In the feasible case, Brazil is next in the
queue with four signatures already recorded. Each continuation reuses that
roster's own nine-speech prefix and adds four floor calls and Brazil's
signature. The continuations are dependent on the original runs.

The script uses the same seat-local information. It rules out incompatible
options before supporting a proposal and certifies impasse once every
option is excluded. It reaches both endpoints under the original limits,
which establishes that the feasible outcome is reachable in nine speeches.
The live endpoint tie covers one opener and two exposed versions of the
same workshop. It supports reporting cap sensitivity and the scripted
comparison alongside the terminal reward. Model rankings and performance
on held case families remain unmeasured. The caps match decision calls and
speeches. Token use is unmeasured.

[Impasse](impasse/calls.jsonl) · [Feasible](feasible/calls.jsonl) ·
[All-Sol continuation](feasible-extended/calls.jsonl) · [Paired results](comparison.json)

## Replay and reproduce

The comparison checks both configurations, replays each decision from its
archived prompt and structured response, and counts incompatible
signatures per decision. The structured result lists speakers, actions,
package versions, terminal status and call counts. Offline replay is
deterministic. Fresh calls can produce different trajectories.

```sh
set -o pipefail
out=reports/council-workshop-sol-control-20261123
python3 -B "$out/compare.py" | cmp "$out/comparison.json" -
```

To regenerate a live control into a fresh directory from the repo root:

```sh
python3 -B research/council_workshop/run.py \
  --case research/council_workshop/climate-packages-impasse.json \
  --countries KEN GBR IND FRA BRA --model gpt-6.1-sol \
  --turn-cap 9 --call-cap 50 --call-timeout 90 --out runs/impasse-all-sol
```

Use `climate-packages-feasible.json` and a different output directory for
the feasible twin. To continue it, keep the same flags and add
`--extend-from runs/feasible-all-sol`, set `--turn-cap 10`, and choose a
fresh `--out` path. The archives contain the actual settings and calls.
