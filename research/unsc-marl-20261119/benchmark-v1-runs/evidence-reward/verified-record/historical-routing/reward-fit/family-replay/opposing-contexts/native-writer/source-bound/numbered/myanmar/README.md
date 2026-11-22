# Transfer source-indexed writing and pair calibration to Myanmar

The case tests whether a retrospective record can preserve the UK
sponsorship, India's national abstention and India's separate role as
Council president. The rubric selected the UK–India pair before model
generation because the overlap criterion needed both private sources.
The presidency criterion needed the chair card. The result was sealed in
the [plan](plan.json) before the first native call.

| Native processing | Full record | Learned route, three states | Best fixed, three states |
| --- | ---: | ---: | ---: |
| Strict ID parser, original packing | 56 | 154 | 161 |
| Recognize ranked objects, original packing | 63 | 189 | 189 |
| Recognize ranked objects and retain each complete reason | 70 | 196 | 189 |
| Menu order and retain each complete reason | 70 | 196 | 189 |

Scores are released documentary points. The full record is worth 70.
The three matched states each have the same two private inventories and
opening sends, with different receipt masks. The strongest fixed
responder can use the absence of an ineligible request as a signal.
The complete-reasons intervention restores the 6.95 summed learned net
margin. The menu-order control matches all eight documentary scores. It
takes 150 words for the full record, while the normalized native path
takes 147. The native passage ranking receives no measured advantage in
documentary points on this case.

The UK output was an array of ranked objects. The strict ID-string
parser rejected it. A post hoc format control validates exact fields,
sequential ranks and role-local membership, then reuses the three IDs.
The first packing control preserved the comparison but displaced the
UK's rationale. Prioritizing complete local reasons then restored the
sponsorship rationale, scoped overlap and distinction between India's
presidential and national capacities. Both changes are preserved as
separate ablations with no extra generation.
[Raw calls](evidence/calls.jsonl) · [Format control](format-control.md) ·
[Packing ablations](coverage-packing.md) · [Strict and normalized results](results.json) ·
[Full record and quote marks](intact-grades.json) · [Routing results](intact-results.json)

## Test calibration and review uncertainty

On the intact-record bank, the predeclared UK–India grade changed the
mixed selector from one population win to three. Margins over fully
informed fixed targeting were +0.038, +0.015 and +0.026 for uniform,
asymmetric and correlated duplicate inventories. The strict writer led
the selector to choose a fixed policy in all three. Overstating the pair
grade by one criterion made the nominal selector lose in all three
intact-record Myanmar conditions. [Reviewer sensitivity](intact-sensitivity.json)

Across the intact Myanmar and numbered UNIFIL banks, three priors and
three review offsets yield 18 modeled comparisons. Selecting from a
one-criterion uncertainty interval reduced losses against fully informed
fixed targeting from six to two and improved mean net margin from
−0.0334 to +0.0223. The worst margin improved from −0.4452 to −0.3405.
Documentary score fell below optimized silence in three nominal
comparisons and zero interval-based comparisons. The interval selector
created two new losses on underestimated Myanmar grades where the
nominal policy tied. [Interval protocol](robust-calibration.md) ·
[Policy choices and results](robust-results.json)

The three native calls used frozen Qwen3.5-4B on an NVIDIA RTX PRO 6000
Blackwell Server Edition. The menus, dependency map, public template
and exact criterion checks are authored. Myanmar and UNIFIL are exposed
cases. Delivery is modeled, and message fees exclude writer inference.
The results leave transfer to independently reviewed, unseen cases
unmeasured. [Protocol](protocol.md) · [Token verification](verification.json)

With the same Python environment and import paths as the parent run:

```bash
set -o pipefail
python3 transfer.py plan | cmp - plan.json
python3 transfer.py verify | cmp - verification.json
python3 preflight.py | cmp - preflight.json
python3 evaluate_transfer.py grade | cmp - grades.json
python3 evaluate_transfer.py replay | cmp - results.json
python3 cover_pack.py grades | cmp - protected-grades.json
python3 cover_pack.py replay | cmp - protected-results.json
python3 cover_pack.py grades --intact | cmp - intact-grades.json
python3 cover_pack.py replay --intact | cmp - intact-results.json
python3 review_sensitivity.py | cmp - sensitivity.json
python3 review_sensitivity.py --intact | cmp - intact-sensitivity.json
python3 robust_selector.py | cmp - robust-results.json
```

[Broader shift evaluation](shift/README.md) tests 20 score banks, a new joint head fit, and the effect of reviewing additional pair masks.
