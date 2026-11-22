# Test the frozen requester on a procedural Council vote

Resolution 2623 called an emergency special session of the General
Assembly on Ukraine. Russia voted against it and the Council
adopted it. Nebenzia then explained Russia's position in his
national capacity. The evaluation packet distinguishes that
account from the Council President's announcement and the
earlier veto of draft S/2022/155. Brazil's qualified support and
India's diplomacy and evacuation concerns make up the other
two statement cards. All 15 votes match UNBench author-test
event 2427 and adopted UNSC-Bench row 248.
[Official resolution](https://digitallibrary.un.org/record/3958807?ln=en) ·
[Roll call](https://digitallibrary.un.org/record/3958818?ln=en) ·
[Verbatim meeting record](https://digitallibrary.un.org/record/3959142/files/S_PV.8980-EN.pdf) ·
[Release audit](provenance.json)

Freeze the fitted policy from the prior study and write all seven
nonempty receipts using the same documentary supplement prompt.
A fixed public section preserves the Council's tally and operative
action. The two free-form solo controls receive either just the
public cards or all five documents. Apply the same 70-point rubric
to the records and the same postprocessing used for UNAMA's leading
symbols and subjectless verbs. No source is added through the
postprocessing step. The 145-word limit applies to the full record.
The review JSON reuses the scoring engine's public field names.
`mandate` denotes the decision to call the session. `reporting`
denotes the earlier Council deadlock described in the resolution.

The one-pair rule and scoring code are fingerprinted in the
generation launch record. The rule sees only the empty and
singleton scores when choosing a pair to inspect. After one
optional pair score it selects a source order and keeps that same
order under the shifted inventory prior. Evaluation uses the entire
receipt bank to measure the selected policy. It also reports what
exact planners do with the same partial scores and what they can
achieve when given the entire bank. The policy receives typed
source identifiers during these simulations.
[Packet](packet.json) · [Locked protocol and rubric](protocol.md)

## Results

Each singleton scores 46 guarded points, so all six slot orders
tie initially. The locked rule selects Brazil–Russia for the
one additional calibration review. That record contains 163
words and fails the 145-word limit, as does the Russia–India
record at 153 words. The Brazil–India pair uses 133 words but
preserves fewer material units than either singleton, leaving
it at 42 points. The pair score selects the two orders beginning
with India. Both priors use that same choice.

| Original guarded net | Uniform | Correlated duplicates |
| --- | ---: | ---: |
| Frozen guarded fit, singleton calibration | 33.045 | 33.114 |
| Frozen guarded fit, one pair revealed | 35.535 | 35.365 |
| One-pair selection with paid query erased | 38.061 | 37.754 |
| Matched fitted independent policy | 36.333 | 36.221 |
| Exact independent planner, same one pair | 38.855 | 38.521 |
| Exact adaptive planner, same one pair | 36.590 | 37.673 |
| Exact adaptive ceiling, full reward table | 44.485 | 44.205 |

The one-pair rule improves source order selection. Its learned
query fails the paired erasure ablation and trails the equally
informed independent planner. The fully informed adaptive
ceiling leaves room for coordination on the exact same writer,
and the partial score estimates fail to expose all risky pairs.

The full-access solo record scores 58/70 before guards and
fails support and citation. It invents support for the resolution
in India's account. The raw public-only control scores 34/70
before guards. The reviewer marks its claim that the Council
decision superseded the earlier deadlock as uncertain. All nine
calls ended. No record reaches 70 points.

## Post hoc control for the public section's word budget

Replace the 87-word fixed public section with a 58-word
version that retains every scored public fact. Reuse each
supplement and its existing annotations. Both over-length pairs
now earn 50 guarded points. The full-access assembled record
also earns 50. The word-cap repair leaves omissions in the
underlying supplements. The Brazil–India pair still earns 42
and all three singleton scores stay at 46.

Reapplying the locked selection rule to this post hoc alternative
gives 44.426 under uniform inventories. Keeping the original
singleton-only tie average gives 44.900, and the exact adaptive
planner with the same one-pair score reaches 45.631. The revealed
pair is better than its singletons and worse than the additive
proxy's 58-point estimate. The rule treats it as a comparatively
weak pair and retains the same source orders. A one-pair
measurement and an additive model leave unobserved dependence
between the other cards.

The policy was frozen before all nine generations. The initial
selection rule is locked and the compact control followed record
inspection. All scoring is same-assistant exact-span review.
The evaluation replays typed receipts with the learned policies
and includes transportation costs only. No additional model
generation or update was needed for the compact control.
[Initial scores and policy replay](results.json) ·
[Exact review spans](marks.json) ·
[Public section control](compact.json)

```bash
PYTHONPATH=../../../../src python facilitator_emergency_session_provenance.py
python facilitator_emergency_session.py verify facilitator-emergency-session-evidence
OPENBLAS_NUM_THREADS=1 python facilitator_emergency_session_score.py facilitator-emergency-session-evidence --marks facilitator-emergency-session-evidence/marks.json
OPENBLAS_NUM_THREADS=1 python facilitator_emergency_session_compact.py facilitator-emergency-session-evidence
```
