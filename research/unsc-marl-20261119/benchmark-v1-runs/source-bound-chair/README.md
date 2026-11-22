# Build the workshop record from sourced facts and certified disclosures

The chair takes the published historical blocks and menu, the public
roles and the declarations it received. It computes agreement or
impasse with the existing disclosure ledger. It then copies the
historical blocks and places fictional roles, proposal and authority
in a separate part of the brief. A short alias in the Syria menu
expands to the two access channels named in that menu.
[Protocol](protocol.md) · [Chair](chair.py)

| Archived input | Exact decisions | Released records | Released points |
| --- | ---: | ---: | ---: |
| Iraq, sequential declarations | 4/4 | 4/4 | 280/280 |
| Syria, independently collected declarations combined in replay | 4/4 | 4/4 | 280/280 |

All four distinct texts pass the frozen v1.1 rubric in a same-assistant
reading. Both orders use the same canonical wording for a given case.
Iraq's strongest archived free-form comparison earned 210/280 from
the same declarations and certificates. Syria's previous independent,
peer and pooled baselines used a different disclosure and writer
protocol. These are two exposed families. The result measures what can
be assembled from complete declarations and curated official blocks.
It adds zero model generations or updates.
[Raw rendered records and proof IDs](replay.json) · [Quote-backed marks](marks.json) · [Scores](scores.json)

Removing either declaration gives 16/16 appropriate deferrals.
Removing both gives 8/8. Contradictory declarations by the same role
give 16/16. All 192 package-letter permutations preserve the decision
after relabeling. The genuine replies pass the role-local typed check.
Replacing one with an internally coherent false claim yields 16/16
wrong terminals without that check and 16/16 deferrals with it.
The public renderer receives neither the private cards nor the
answer key. The typed gate uses each role's own authoritative card
and assumes the transport binds each declaration to its actual role.

## Measure how much a learned signed reply can support

The earlier learned actors send signed compatibility for a single
package. Replayed on the 44 original Iraq and Syria prompts, each
admitted sign narrows the compatible mandate set for its own role.
Enumerate the menu-compatible values under the declared assumption
that a role has exactly one requirement from the registered menu
fields. Count a role's mandate as identifiable only when one possible
requirement remains. The same local sign audit used in the original
study rejects false signs. Counts apply to forced-recipient prompts
with the reply assumed delivered. They include already certified
openings and give no credit for private information in the actor prompt.

| Reply policy | Admitted signs | Explicit decision proofs | Proofs with both mandates identifiable |
| --- | ---: | ---: | ---: |
| Frozen native Qwen | 19 | 10 | 9 |
| Native direct-credit adapter | 12 | 10 | 8 |
| Native expected-reward adapter | 5 | 5 | 5 |
| Learned feature head | 20 | 16 | 14 |
| Exact decision-oriented reply | 16 | 20 | 16 |
| Always send a truthful reply | 44 | 20 | 16 |

Even the exact decision-oriented reply leaves a mandate ambiguous
on four proofs. All four are agreement presentations, two per family.
One native expected-reward replay identifies both mandates under the
menu model while the explicit-sign ledger is still missing a required
affirmation. The initial check incorrectly assumed these signals
must always coincide. The complete replay records both separately.
The signed analysis counts what could be inferred under the menu
assumption. It neither treats inference as an actual delegate quote
nor turns it into a scored final brief. This exposes a difference
between optimizing correct package decisions and obtaining enough
attributed evidence to write the record.
[Original native fits](../language-signed-reply/native-adapter/README.md) · [All signed replay presentations](signed-coverage.json)

## Verify

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1
python3 replay.py replay | cmp - replay.json
python3 replay.py deck | cmp - deck.json
python3 replay.py score | cmp - scores.json
python3 signed_coverage.py | cmp - signed-coverage.json
```
