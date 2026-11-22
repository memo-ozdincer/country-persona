# Train local grade disclosure for a warranted workshop decision

Two delegates receive private grades for simulated UN workshop packages. Grades and package names are fictional. Start with public domains and no private grade receipts. Each delegate chooses which one of its own grades to file. The chair can request one missing grade, subject to communication loss and fees. It recommends a common maximin winner, records impasse if every compatible world is an impasse, or withholds a decision. The certificate uses all public worlds consistent with the grade receipts. It does not let an opening action implicitly reveal unobserved grades. [Locked protocol](protocol.md) · [Fit and exact search](../trained_warrant.py)

Each delegate's opening is a learned linear score over its local grades and public evidence features. The same 96 exact shared-return updates fit both delegates on 16 synthetic domains. The chair is an exact best response to each pair of opening policies. The strong initial policy uses public local action values given a uniform partner. The exact control enumerates all 81 deterministic tables per delegate, then optimizes chair requests for each pair. All arms get the same message slots, link losses and legal evidence. Net is the certified decision probability less expected query and reply charges. Common opening fees are omitted from all rows.

## Results

| Named panel | Prior | Initial lookahead | Fitted | Best fixed package | Exact local |
| --- | --- | ---: | ---: | ---: | ---: |
| Mali review | Uniform | 0.9461 | 0.9461 | 0.9461 | 0.9461 |
| Mali review | Correlated | 0.9461 | 0.9461 | 0.9461 | 0.9461 |
| Briefing procedure | Uniform | 0.9306 | 0.9306 | 0.9306 | 0.9306 |
| Briefing procedure | Correlated | 0.9306 | 0.9306 | 0.9306 | 0.9306 |
| Reporting scope | Uniform | 0.8881 | 0.8881 | 0.8456 | 0.8881 |
| Reporting scope | Correlated | 0.9072 | 0.9072 | 0.8456 | 0.9072 |

The policies tie in net in all 36 named panel presentations. For reporting scope, adapting the opening to the local card does help relative to the best constant package, but the untrained lookahead captures that gain. Two Mali worlds distinguish the worse-off rule from total grades. An independent receipt ledger verifies all 36 net results and checks that every resulting certificate is permissible in its underlying complete world. It records examples where the requested grade converts an unresolved record into a warranted decision. [Named trials and traces](results.json) · [Receipt ledger audit](audit.json)

A separate unfiltered draw evaluates 32 new synthetic domains under two priors. Each domain is distinct from the named panels and training after package permutation. Sixteen domains have at least one world where total grades give a different winner set. Relative to the initial lookahead, the fit wins two of 64 conditions, loses one and ties 61. Mean net is 0.922284 versus 0.922069, with the exact local ceiling at 0.922973. The initial policy reaches that ceiling in 59 conditions and the learned policy in 60. This is weak evidence that fitting adds value beyond an informed initial rule in this information structure. The strongest observed result is that evidence-based planning reliably exploits the available communication. [All unfiltered domains and comparisons](generalization.json)

The experiment tests authorized grade disclosures, an explicit welfare ordering and formal withholding. It uses new exact policy-gradient updates using the known workshop model. It evaluates neither live natural-language agents nor independently judged records from these workshops.

## Reproduction

From `benchmark-kit/validity-audit`, use the project Python environment.

```sh
OPENBLAS_NUM_THREADS=1 python trained_warrant.py
OPENBLAS_NUM_THREADS=1 python warrant_generalization.py trained-warrant-evidence/results.json
OPENBLAS_NUM_THREADS=1 python warrant_release_audit.py trained-warrant-evidence/results.json
```
