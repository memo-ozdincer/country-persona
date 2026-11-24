# Council negotiation benchmark scorecard

Delegates see their own source packet or fictional mandate, the public
discussion and the current draft. A speaker can propose a replacement,
sign that draft version, or, in finite cases, record a verified exclusion.
The runner supports a different model in each seat. Floor requests count
against the call budget. The [workshop guide](README.md) gives the setup,
case commands and replay protocol.

## Source-grounded clause

| Model | Meeting outcome | Retrospective clause coverage |
| --- | --- | ---: |
| GPT-6.2-Astra | Unanimous acceptance in 11 speeches | 35–40/70 |
| GPT-6.2-Sol | Unresolved after 20 speeches | 40/70 |

The procedural outcome and source coverage are graded separately.
The coverage range comes from an uncertain item in the archived Astra
annotation. These are retrospective assistant grades on one workshop.
[Blinded rubric export, verdicts and exact replay](../../reports/council-workshop-clause-review-20261123/README.md)

A GPT-6.1-Sol regrade reproduced all 12 criterion labels without seeing
the generating model or meeting outcome. An authored false adoption
claim kept its policy score of 40/70 and received zero released points
after the factual guard failed. [Blinded regrade and control](../../reports/council-workshop-blind-judge-20261123/README.md)

## Verified decisions on fictional mandates

A valid unanimous agreement or a certified impasse earns one point.
A cap, walkout, or invalid agreement earns zero. A provider interruption
before a model reply has no outcome score. The held standard-prompt
matrix has 32 cells. **Fourteen meetings are complete**, one cell is
provider-interrupted, and 17 cells have no archived attempt. Earlier interruptions are preserved
in the dated reports.
The eight drafted case and order combinations all have a successful
scripted reachability check. [Held cases](held-cases.json) · [Scripted audit](held-control-audit.json)

| Case | All Sol | Astra replaces one seat |
| --- | --- | --- |
| Five-seat climate, feasible, nine-speech cap | Unresolved | Unresolved |
| Five-seat climate, impasse | Certified in 7 | Certified in 7 |
| Gulf of Guinea, feasible, Ghana opening | Agreement in 5 | Agreement in 5 |
| Gulf of Guinea, feasible, Norway opening | Agreement in 6 | Agreement in 7 |
| Gulf of Guinea, impasse, Ghana opening | Unresolved in 10 | Certified in 10 |
| Gulf of Guinea, impasse, Norway opening | Certified in 9 | Unresolved in 10 |
| Iraq, feasible, France opening | Agreement in 12 | Agreement in 11 |
| Iraq, feasible, UAE opening | Agreement in 12 | Unrun |
| Iraq, impasse, France opening | Unresolved in 16 | Certified in 14 |
| Iraq, impasse, UAE opening | Unresolved in 15 | Provider interrupted after 4 speeches |

Climate is a separate exposed comparison. Both climate continuations
agreed with a tenth speech. The model assignments in the table use
GPT-6.1-Sol and GPT-6-Astra. All eight registered all-Sol cells now have
one meeting, with four agreements and one certified impasse. The UAE
impasse records all exclusions. A separate continuation certifies it
with one additional call and is excluded from registered coverage.
[Climate control](../../reports/council-workshop-sol-control-20261123/README.md) ·
[Gulf comparison](../../reports/council-workshop-held-pilot-20261123/README.md) ·
[Norway opening and interruption traces](../../reports/council-workshop-norway-opening-20261123/README.md) ·
[Iraq comparison and interruption traces](../../reports/council-workshop-iraq-pilot-20261123/README.md) ·
[Completed all-Sol slice](../../reports/council-workshop-all-sol-matrix-20261123/README.md)

The completed Gulf impasse pairs show opposite outcomes across
openers. The Astra seat swap recovered a certificate with Ghana
opening and lost it with Norway opening. With Norway opening, the
first 17 decisions matched on structured fields. On speech seven,
Sol as Norway ruled out `regional`, while Astra as Norway proposed
`review`. Astra ruled out `regional` on speech ten, leaving no speech
for a declaration. Each pair uses one trajectory per assignment.
[Exact resume and comparison](../../reports/council-workshop-norway-focus-resume-20261124/README.md)

All four feasible Gulf trajectories agreed on `briefing`. With
Norway opening, the mixed roster took seven speeches and 19 calls,
compared with six and 17 for all-Sol. The two rosters each certified
one of their two Gulf impasses.
[Gulf results across both openers and worlds](../../reports/council-workshop-gulf-feasible-focus-20261124/README.md)

In France-opening Iraq, the mixed team certified in 14 speeches and
48 calls. All-Sol finished with three of four exclusions in 16
speeches and 55 calls. The trajectories first differed when Ghana
took speech five, before Astra as the UAE had its first speech.
[Iraq comparison and exact resume](../../reports/council-workshop-iraq-focus-resume-20261124/README.md)

On the feasible twin, both France-opening teams agreed on
`hybrid`. The mixed team collected all six signatures in 11
speeches and 46 calls, compared with 12 and 48 for all-Sol.
The mixed team thus reached the correct outcome in both worlds
of this matched comparison.
[Feasible run and paired scores](../../reports/council-workshop-iraq-feasible-focus-20261124/README.md)

The UAE-opening mixed impasse run matched all-Sol on its first
15 structured decisions. The latest resume recovered the UK poll
and Brazil's opening signature, then a provider rate limit
interrupted the UAE floor poll at call 16.
[UAE-opening attempts and matched pairs](../../reports/council-workshop-iraq-uae-opening-focus-20261124/README.md)

Automatic moderator certification on the same archived decisions
recovers the UAE-opening Iraq impasse and closes the Norway-opening
Gulf impasse earlier. It saves four calls across the eight traces. This
is a replay of a different termination rule, separate from the standard
coverage table. [Moderator replay](../../reports/council-workshop-moderator-certificate-20261123/README.md)

Across all 14 completed registered meetings in the later snapshot,
moderator closing raises the replayed success count from 10 to 12.
It ties the Norway-opening Gulf pair by certifying the mixed run
on its final speech and recovers the call-capped UAE-opening all-Sol
run. The other two unresolved traces still lack checked exclusions.
[Full stopping-rule audit and paired deltas](../../reports/council-workshop-closing-rule-comparison-20261124/README.md)

The budget audit locates the first proven loss on each unresolved
all-Sol trace. The floor queue blocked a required holder after speech
six in the Ghana-opening Gulf run and speech 13 in the France-opening
Iraq run. The UAE-opening Iraq trace lost its remaining call budget
after speech 15 with a complete certificate. [Per-speech audit and scripted recovery](../../reports/council-workshop-budget-headroom-20261123/README.md)

An exact queue search confirms those cutoffs. It finds a scripted
way to finish the UAE-opening Iraq case within 55 calls by having
France join the queue earlier, which saves a redundant poll.
[Exact impasse search and witnesses](../../reports/council-workshop-exact-impasse-reachability-20261123/README.md)

Three live continuations of that Iraq prefix kept France's pass at the
decisive poll, including a reminder with the exact calls remaining.
All gathered the full evidence and stopped at 55 calls before a
declaration. [Live floor reminder comparison](../../reports/council-workshop-live-floor-recovery-20261124/README.md)

An opt-in direct handoff bypassed the two late floor polls after all
exclusions were public on the same Iraq prefix. In one fresh
continuation, Sol as Brazil declared the impasse on call 54 within
the original cap of 55. Brazil received the same prompt and schema
as in the recorded call 56 continuation.
[Direct handoff experiment](../../reports/council-workshop-certificate-floor-20261124/README.md)

Across the ten registered meetings completed at the time of the
floor-rule audit, seven were identical
under direct handoff and a Norway-opening Gulf meeting replayed a
certificate one call sooner. The two remaining meetings needed a
fresh reply. In addition to Iraq, the mixed Ghana-opening Gulf
meeting certified at call 23, two calls earlier, even though bypassing
the poll removed China's request from Ghana's public queue.
[Full floor-rule audit](../../reports/council-workshop-floor-rule-audit-20261124/README.md)

On a live continuation at the Gulf cutoff, the priority prompt let
the delegates record all four exclusions by the last speech. The
automatic moderator replay turned that evidence into a certificate.
The standard continuation stayed one exclusion short under either
closing rule. [Matched live continuations](../../reports/council-workshop-gulf-cutoff-20261123/README.md)

## Prompt and budget controls

| Case | Standard | Exclusions first | Exclusions after a checked rejection |
| --- | --- | --- | --- |
| Iraq, impasse | Unresolved in 16 | Certified in 7 | Unrun |
| Iraq, feasible | Agreement in 12 | Agreement in 12 | Unrun |
| Gulf, impasse | Unresolved in 10 | Certified in 7 | Certified in 7 |
| Gulf, feasible | Agreement in 5 | Agreement in 6 | Unrun |
| Five-speech case with feasible opening | Agreement in 3 | Unresolved in 5 | Agreement in 3 |
| Five-speech case with rejected opening | Agreement in 4 | Unrun | Unresolved in 5 |

Checking alternatives helped certify impasse in these runs. Under a
tight deadline, the same checks can spend turns needed to propose or
sign a feasible draft. The comparative rows use one example per condition.
[Iraq prompt test](../../reports/council-workshop-exclusion-policy-20261123/README.md) ·
[Gulf transfer](../../reports/council-workshop-exclusion-transfer-20261123/README.md) ·
[Feasible opening](../../reports/council-workshop-opening-agreement-20261123/README.md) ·
[Conditional prompt](../../reports/council-workshop-conditional-exclusions-20261123/README.md) ·
[Rejected opening](../../reports/council-workshop-rejected-opening-20261123/README.md)

## Shared observation and private information

With five speeches, China sees the same prompt in two different worlds
and has to choose a different action to preserve each endpoint. The
exact success ceiling is **50% under an equal prior**. With six speeches,
one scripted policy reaches both endpoints by using Norway's next public
action. In the live six-speech trial with fixed floor routing, Sol agreed
in the feasible world and missed the impasse. Substituting one checked
rejection allowed the remaining live delegates to certify on speech six.
[Exact bound and witnesses](../../reports/council-workshop-rejection-fork-20261123/README.md) ·
[Live continuation and substitution](../../reports/council-workshop-live-rejection-fork-20261123/README.md)

## Rebuild the results

From the repository root, run:

```sh
set -o pipefail
kit=research/council_workshop
python3 -B "$kit/scorecard.py" | cmp "$kit/scorecard.json" -
```

The [JSON scorecard](scorecard.json) includes call counts, registered budgets,
registered coverage, scripted controls and the source-coverage ranges.
Its rebuild replays archived runs and validates their saved readouts
without model or network calls. For the separate source-grounded chair
record benchmark, see [UN Deliberation v1.7](../unsc-marl-20261119/benchmark-v1.7/README.md).
