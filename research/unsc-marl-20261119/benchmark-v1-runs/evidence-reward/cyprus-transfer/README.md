# Transfer the learned team to a Cyprus briefing workshop

The historical packet concerns the United Kingdom's draft S/2023/64,
adopted unanimously as resolution 2674 (2023). The Japanese Council
President reported that the parties maintained their positions. Those
positions and the decision of the Council have distinct authority.
The record rubric also tests the mandate deadline, readiness to review
implementation after six months, and UNFICYP's island-wide mandated
authority. The briefing workshop and private desk constraints are
fictional. [Council meeting record](https://digitallibrary.un.org/record/4001586/files/S_PV.9252-EN.pdf) ·
[Adopted resolution](https://digitallibrary.un.org/record/4001585/files/S_RES_2674_%282023%29-EN.pdf)

UNBench contains the draft and 15 affirmative votes in author-test
event 2477. Neither pinned UNSC-Bench configuration matches the draft
or meeting. The official meeting supplies the independent historical
check for the vote. The [dataset join](dataset-join.json) records the
searched revision and rows. The [case and rubric](case.json) and the
[protocol](protocol.md) were set before native collection.

The saved chair and reply policies are unchanged from the Mali
experiment. The four-option menu uses a role permutation of that
excluded shape. This gives a new docket and different language for
the roles and conditions. The structure of the reasoning task remains
familiar. In the [all-world model](proof-audit.json), the two-question
learned policy earns 0.1305 net and 40.5% expected accuracy. The same
chair with mandatory sending earns 0.1140 at the same accuracy. Fixed
order earns −0.0480 net and 20.25% accuracy. These numbers match the
corresponding Mali model, as expected for a symmetric role
permutation. The audit also verifies the exclusion text against the
allowed option set in all 27 public states.

## Native dialogue and paired final records

The learned chair asked the Access desk and then the Documentation
desk. The frozen Qwen3.5-4B replies `N` and `Y` passed the typed
requirements check. Shared circulation rules out A and B. Slides
rule out B, C and D. Together the replies certify impasse and leave
the scheduling requirement unknown. This selected execution uses
the fully delivered path on NVIDIA RTX PRO 6000 Blackwell Server
Edition.

| First comparison | Words | Workshop output | Released /70 |
| --- | ---: | --- | ---: |
| Raw public evidence | 192 | A | 0 |
| Checked exclusions supplied | 89 | Impasse in prose, invalid first line | 0 |
| Deterministic application control | 121 | Certified impasse | 70 |

The raw writer says A has internal circulation and also says the
Access desk requires shared circulation. Both native writers call
a morning slot an admitted requirement while acknowledging that
Scheduling's requirement is unknown. The proof-assisted writer
names the right disposition in prose. Its first line carries
additional text and fails the exact header check. Both omit the
draft symbol and sponsor and fail the source guard. One rubric item
requires the Council settlement framework or envoy position. The
first comparison provides it in the source packet and references
the positions in the request without explicitly listing that rubric
requirement. This can contribute to missing coverage. All three
records have same-assistant span-backed semantic annotations.

[Native traces](evidence/trace.jsonl) · [Verification](verification.json) ·
[Scoring packets](packets.json) · [Marks](marks.json) · [Scores](results.json)

Replay from this directory using the project Python with NumPy, Jinja,
tokenizers and PyArrow.

```bash
set -o pipefail
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python3 transfer.py plan | cmp - plan.json
python3 proof_audit.py | cmp - proof-audit.json
PYTHONPATH=../../../../../src python3 audit_sources.py | cmp - dataset-join.json
python3 check.py verify | cmp - verification.json
python3 check.py packets | cmp - packets.json
python3 check.py score | cmp - results.json
```

The adaptive [historical-only composition](history-only/README.md)
preserves the exact workshop certificate and places the unedited
model-written historical paragraph after it. It earns 56 raw points.
The guard remains uncertain over how the paragraph attributes the
absence of a party settlement, yielding zero released points.
