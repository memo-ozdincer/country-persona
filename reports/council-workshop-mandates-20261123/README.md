# Five-seat agreement and impasse controls

Two fictional climate-reporting cases share the roster, opening
clause and menu. In the first, all five seats can accept existing
Council reports citing climate findings as context. In the second,
the Kenya seat's simulated mandate removes that option, creating an
empty intersection. Kenya's and Brazil's private mandates are case
inputs with no inference about their historical positions.

| Script | Feasible case | Infeasible case |
| --- | --- | --- |
| Checked public exchange | 5/5 valid agreements | 5/5 certified impasses |
| Always accept the opening text | 0/5 valid agreements | 0/5 certified impasses |
| Always exit | 0/5 valid agreements | 0/5 certified impasses |

The checked script uses the same private observation as a live delegate
and runs through the production floor and action engine. It excludes
locally unacceptable remaining packages, proposes and accepts the
single surviving package, or declares an impasse after every option has
an exclusion. It consumed 19–21 decision calls in the feasible case
and 11–15 in the impasse case. Blind acceptance produced unanimity on
an infeasible draft in both worlds. The scorer recorded each as an
invalid agreement. A walkout left the case unresolved.

The 30 rows are deterministic scripted runs, covering all five cyclic
openers in two cases for three scripts. There are no live model calls.
The cases diagnose reward and protocol correctness. They leave open how
learned agents perform and how an open-text negotiation should certify a
feasible compromise.

[Case and protocol guide](../../research/council_workshop/README.md) · [All runs](results.json)

From the repository root:

```sh
set -o pipefail
python3 -B research/council_workshop/mandate_smoke.py | cmp reports/council-workshop-mandates-20261123/results.json -
```
