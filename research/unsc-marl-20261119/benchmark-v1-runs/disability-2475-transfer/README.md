# Resolution 2475 source-pair transfer

On 20 June 2019 the Security Council unanimously adopted the
Poland–UK draft on protecting persons with disabilities in armed
conflict. Russia supported the humanitarian purpose and read the
resolution's treaty reference narrowly. France advocated ratifying
and fully implementing the disability convention. The UK agreed
with Russia about avoiding new obligations. The test asks whether
a receipt-scoped chair can preserve the difference in scope and
distinguish it from the narrower shared position.
[Official meeting](https://documents.un.org/api/symbol/access?l=en&s=S%2FPV.8556&t=pdf) ·
[Adopted resolution](https://digitallibrary.un.org/record/3810148/files/S_RES_2475_%282019%29-EN.pdf)

The case was locked before generation. UNBench author-test event
2282 and the official minutes agree on all 15 votes. The join found
no matching adopted row in the 258 pinned UNSC-Bench records. This
family was new to the project experiments and public in both the
archival record and UNBench. Model pretraining exposure is unknown.
[Source join](provenance.json) · [Locked docket](docket.json) · [Protocol](protocol.md)

Only the France–Russia relation requires both country sources.
The UK can establish its agreement with Russia from its own
statement. The source-ownership audit surfaced this distinction
before output and retains the original criterion.
[Source-ownership audit](source-audit.md)

## Live records

The native public lead omits the draft symbol and co-penholders,
the unimpeded-access qualification, and the existing mandates and
resources limits on disability-disaggregated reporting. The French
note omits full implementation and says "UN ratification," leaving
unclear whether it means Member States or the UN itself. The Russia
note keeps Article 11 of the convention and Russia's objections to
new legal categories, while dropping the operative paragraph number.

All three extra comparison sentences add zero raw rubric points.
The UK note already gives the UK–Russia point. The Russia–UK extra
sentence says Russia limited the convention to Article 11. The
meeting record instead describes Russia's reading of an operative
paragraph of the Council resolution. This error takes the pair from
21 released points to zero. Neither the France–Russia pair nor the
full record earns the intended joint criterion. Reading "UN
ratification" leniently restores some full-record release but still
yields no raw pair surplus and no credit for the joint criterion.

| Receipt bank, mask order France, Russia, UK | Released points |
| --- | --- |
| Native verbatim | 0, 0, 7, 0, 14, 0, 21, 0 |
| Native with comparison | 0, 0, 7, 0, 14, 0, 0, 0 |
| Authored source-preserving control | 21, 28, 35, 49, 42, 49, 56, 70 |

The authored control uses the same documentary rubric and fixed
175-word cap. It yields a seven-point France–Russia margin above
the sum of the singleton gains, isolating the distinction the native
notes lost. The live record has no positive raw pair margin. Its
negative release margins come from source and attribution guards.

The seven native Qwen3.5-4B calls all complete, using 1,259 input
tokens, 216 output tokens and 9.03 seconds of measured generation on
NVIDIA RTX PRO 6000 Blackwell Server Edition, excluding checkpoint
load. The worker exited successfully. All candidates fit within 175
words. A single assistant read 11 unique opaque response packets.
There were no model updates or post-generation edits to the native
records. The authored control is a separate calibration artifact.
[Token and prompt verification](verified.json) · [Archived markings](scores.json) ·
[Authored and lenient-reading controls](oracle.json)

## Routing transfer

The exact adaptive planner beats the matched fixed policy in all 18
simulations for each bank. The mean margins are +0.0802 net points for
verbatim and +0.0976 for comparison. The comparison bank's larger
relative margin accompanies a drop in absolute mean released points
from 13.64 to 6.35. The nominal, learned pair and halfway-additive
forecasts choose identical policy tables and produce identical held outcomes within each bank.
The independent dispatcher checks 144 policy outcomes. The result
localizes this case's failure to producing documentary coverage from
the notes. It uses modeled delivery and one newly tested family.
[Routing protocol](routing-protocol.md) · [Exact replay](routing.json)

## Guard and authored-target sensitivity

Replaying the same matrix while accepting the French shorthand
gives the learned and additive pair corrections mean changes of
−0.0061 and +0.0045 on the verbatim bank. On the compared bank the
corrections change mean net by +0.0002 and zero. All three forecasts
there leave 12 results below informed silence. On the authored bank
with seven points of genuine pair surplus, learned and additive
corrections improve nominal net by +0.0135 and +0.0113. The small
difference on authored input is a retrospective diagnostic. No native
record earned that surplus. The sensitivity adds 216 policy replays.
[Alternate score-bank replay](sensitivity.json)

## Reproduce

Use the Aurora environment and `replay` helper in the
[Resolution 2686 instructions](../tolerance-2686-transfer/README.md#reproduce).
Run in this directory with Bash pipe failure enabled.

```bash
set -o pipefail
"$env_root/open-character-20261004-v1/bin/python" -B join_sources.py | cmp provenance.json -
"$py" live_2475.py plan | cmp plan.json -
"$py" live_2475.py verify | cmp verified.json -
"$py" score_2475.py | cmp scores.json -
"$py" oracle_control.py | cmp oracle.json -
replay route_2475.py plan | cmp routing-plan.json -
replay route_2475.py run | cmp routing.json -
replay sensitivity.py | cmp sensitivity.json -
```
