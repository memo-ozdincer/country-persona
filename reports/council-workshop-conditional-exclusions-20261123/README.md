# Prioritizing exclusions after a checked rejection

The conditional instruction asks each delegate to check the current
draft first. With no public checked exclusions, a delegate signs an
allowed draft or rules out a disallowed draft. After a checked rejection
has entered the public record, the instruction gives priority to any
available exclusion, including one for another package. A delegate
without such an exclusion can sign or propose a package within its
mandate that has survived the checks. The facilitator uses the same
state and rules in all conditions.

The report pairs two fresh all-Sol runs with archived standard and
exclusions-first runs. Each case uses the same mandates, Ghana opener,
seat order, model and limits across its three conditions. The
[feasible opening](../council-workshop-opening-agreement-20261123/README.md)
has a five-speech, 24-call cap. The
[Gulf impasse](../council-workshop-exclusion-transfer-20261123/README.md)
has a ten-speech, 30-call cap.

| Case | Standard | Exclusions first | After checked rejection |
| --- | --- | --- | --- |
| Feasible opening | Agreement in 3 speeches, 8 calls | Unresolved in 5 speeches, 11 calls | Agreement in 3 speeches, 8 calls |
| Gulf impasse | Unresolved in 10 speeches, 24 calls | Certified in 7 speeches, 17 calls | Certified in 7 speeches, 16 calls |

In the feasible opening, all three delegates signed the opening version
before any exclusion was recorded. In the impasse, Ghana first signed
the opening version, which its own mandate allowed. China ruled it
out on speech two. Norway then used speech three to rule out `briefing`
even though it was off the floor, and later ruled out `regional`. Ghana
certified all four exclusions on speech seven. Every signature in the
six runs was compatible with its speaker's mandate.

These are two selected cases that informed the instruction, each with
one trajectory per condition. The results show that a checked rejection
can serve as a public trigger for exclusion search on these inputs.

[Feasible opening trace](feasible-opening/calls.jsonl) · [Gulf impasse trace](gulf-impasse/calls.jsonl) · [Matched readout](readout.json)

## Replay

```sh
set -o pipefail
out=reports/council-workshop-conditional-exclusions-20261123
python3 -B "$out/readout.py" | cmp "$out/readout.json" -
```

Use `run.py --prioritize-exclusions-after-rejection` with a finite-mandate
case and a fresh output directory to generate another run. The setting
is recorded in `settings.json` and is required when resuming that run.
