# Classify a typed relationship before rendering the UN record

The apparent MARL recovery depends on the answer labels. In one rotation,
the frozen classifier renders both correct matched records and the
trained desks recover their 2.57-point advantage over best arrival-only.
That same rotation selects two unsupported types on crossed receipts
and misclassifies all four fictional controls. Agreement across two
rotations clears the two crosses but restores only one of the two
relationships, leaving the trained pair behind the control.

| Choice rule | Real pairs correct /4 | Fictional controls correct /4 | Trained team utility | Best arrival-only utility |
| --- | ---: | ---: | ---: | ---: |
| A condition, B mandate, C neither | 3 | 3 | 38.929 | 40.723 |
| A neither, B condition, C mandate | 2 | 0 | 43.291 | 40.723 |
| Require agreement across both | 3 | 3 | 38.929 | 40.723 |
| Authored source-bound relation | 4 | — | 43.291 | 40.723 |

The direct and witnessed native writers in the preceding study produced
28.258 and 34.204 utility for these same trained desks. The agreement
rule here recovers the 22-point Ghana relationship and clears the four
real pairs' guards. Its false negative is the Russia pair. On the
fictional statement that proposes replacing UNAMA, both label mappings
wrongly approve complementarity. The fictional pairs never enter the
policy replay.

The high-utility rotation assigns a relationship to both crossed pairs.
The trained desks avoid those pairs with the matched reply, so their
aggregate utility is identical to the authored reference. Swapping in
the fixed UNAMA reply reveals the damage. Utility falls from 38.929
with the authored reference to 29.412 with the rotated model because
the Russia–UNAMA crossing fails release. This shows how a trained
communication policy can hide a brittle final writer.

A post hoc topic-word rule gets all four canonical pairs and misses all
four fictional controls. A simple phrase rule checks for both
“withhold support” and “no consent requirement,” or for both
“complement to UNAMA” and “preserving the mandate and work of UNAMA.”
It gets all eight. The controls distinguish subject overlap from source
force on this roster. They leave transfer beyond these cues untested.

The two source excerpts appear in separate fields without receipt IDs.
Qwen selects a relation type. The renderer appends a fixed generic
sentence and preserves the public lead and both excerpts. Human
authored template meaning and the prior expected relations determine
rubric credit. No receipt registry chooses the model's output.
The run uses one exposed docket, four phrase-level controls and exact
replay of 48 simulated channel and price settings. This is a comparison
of constrained output and rendering, with no weight updates or
independent semantic review.

All 16 calls completed on one NVIDIA RTX PRO 6000 Blackwell Server
Edition. A first attempt stopped at the device check with no worker
launched. The run started after the device was empty.

[Locked protocol](protocol.md) · [Exact inputs](plan.json) ·
[Verified responses](verified.json) · [Records and utility](results.json) ·
[Lexical controls](cue-baseline.json) · [Worker receipt](evidence/launch.json)

From this directory in the existing Aurora Qwen3.5 environment:

```bash
set -o pipefail
python -B collect_typed.py plan | cmp plan.json -
python -B collect_typed.py verify | cmp verified.json -
python -B score.py | cmp results.json -
python -B cue_baseline.py | cmp cue-baseline.json -
```
