# Isolate the factual guard from quote formatting

The label-only guard reproduces the bundled judge's aggregate
**17/21** guard-label agreement on the authored anchors. It still
clears the false claim that the vetoed Syria draft authorized aid.
On 12 previously reviewed historical briefs, it matches **6/12**
guard labels and clears **5 of 7** briefs previously marked failed
or uncertain.

| Clearance rule | Anchor false clears | Anchor false blocks | Historical false clears | Historical false blocks |
| --- | ---: | ---: | ---: | ---: |
| Mean of the two label mappings | 1 | 3 | 5 | 0 |
| Both label mappings must clear | 0 | 13 | 3 | 0 |
| Clearance margin calibrated on anchors | 0 | 11 | 3 | 0 |

The first-token guard reads the same final answer and source
packet twice, with clear and failed assigned opposite letters.
The two assignments disagree on 15 of 21 anchors and four of 12
historical briefs. Averaging them gives the same verdict as the
bundled judge on 17 anchors, with some errors changing identity.
The false-authorization anchor is one of those that switches
under label reversal. The higher average logit still goes to
clear.

The threshold selects the smallest nonnegative margin that
clears none of the known blocked anchors. It still clears three
historical briefs with previously reviewed errors. Requiring both
mappings to clear gives the same historical release decisions.
A strict replay changes only the guard and leaves the previous
rubric marks, token caps and word counts fixed. The reviewed
mean peer-minus-independent effect is **−12 points** across
Myanmar and the Residual Mechanism. It becomes **−4 points** under
the averaged guard because both erroneous Myanmar peer records
are allowed through and one unsupported tribunal roster is also
accepted. The two conservative controls give **−12.75 points**
while still clearing individual problematic briefs. Agreement of
an aggregate alone can conceal wrong release decisions.
[Clearance rules and controlled guard swap](operating.json)

The experiment made 66 first-token evaluations with 63,172
input tokens on NVIDIA RTX PRO 6000 Blackwell Server Edition.
Qwen3.5-4B was frozen. There is no citation output or process
rating, and the measured labels can be inspected independently
of formatting. The same checkpoint previously generated the
historical records. Targets are authored anchors and a single
prior assistant reading on exposed dockets. This is a diagnostic
of semantic guard reliability rather than a replacement scorer
or a measure of independent human agreement.

[Protocol](protocol.md) · [Locked inputs](plan.json) ·
[Label logits and comparisons](results.json) · [Token receipt](verified.json)

```bash
set -o pipefail
python -B guard.py plan | cmp plan.json -
python -B guard.py verify | cmp verified.json -
python -B guard.py score | cmp results.json -
python -B operating.py | cmp operating.json -
```
