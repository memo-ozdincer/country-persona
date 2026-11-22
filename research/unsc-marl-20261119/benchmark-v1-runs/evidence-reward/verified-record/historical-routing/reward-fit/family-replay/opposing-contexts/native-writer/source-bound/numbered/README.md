# Select numbered source spans and keep each qualification intact

Each of three frozen Qwen3.5-4B calls returned valid passage IDs from a
single national source. All three selected the main passages. China and
Russia excluded one secondary detail each. The public paragraph uses
authored selections from the official record with exact source offsets.
The passage menus and cross-role comparison rule are also authored.

| Assembly and selection | Learned route | Best fixed target | Learned net margin |
| --- | ---: | ---: | ---: |
| Greedy assembly, native IDs | 175 | 189 | −14.05 |
| Whole-claim assembly, native IDs | 196 | 189 | +6.95 |
| Whole-claim assembly, menu order | 182 | 189 | −7.05 |
| Whole-claim assembly, first menu item | 105 | 105 | −0.70 |

Released points are summed across the same three receipt states. Each
state is worth 70 points. The original greedy assembler scored 49 on
the full record because appending Brazil's final clause also triggered
a comparison line and overflowed the cap. The whole-claim assembler
treated the qualified claim as a unit and used a shorter scoped
comparison. It fit the full native-selected record in 150 words for 70
released points. Preferring all menu items in their given order scored
56 on the full mask. The model's choice to leave out secondary
passages mattered under this budget.

Across modeled inventory and delivery outcomes, the dense team's net
margin over the best fixed continuation was −0.014 with uniform
inventories, +0.010 with the asymmetric prior, and −0.169 with
correlated duplicates. The result supports a selected communication
mechanism with a faithful writer. It gives weaker evidence for an
improvement across operating conditions.

National text comes from selected source passages. The public template
and comparison line are deterministic. Rubric grades use a hand-checked
mapping from emitted passages to required criteria and quote-checked
final records. This test covers one exposed case and simulated transport.
The message costs exclude writer inference. The three calls used frozen
Qwen3.5-4B on an NVIDIA RTX PRO 6000 Blackwell Server Edition, with no
optimizer updates. [Protocol](protocol.md) · [Native selections](evidence/calls.jsonl) ·
[Score and trace verification](verification.json) · [Greedy results](results.json) ·
[Whole-claim results](packed-results.json) · [Cited records and marks](packed-grades.json)

## Score one two-card calibration example

The ordinary empty-plus-singleton forecast misses the extra points
for jointly representing Brazil and China. The Brazil–China grade
recovers the full numbered score bank under the one-pair residual
model. Its dense policy margins over fully informed fixed controls
become +0.145, +0.012 and +0.168 under the same three priors. The
archived UNIFIL bank is identical at the score level. On archived
Myanmar, grading the UK–India pair likewise recovers the bank and
gives dense margins of +0.038, +0.015 and +0.026. The other pair grades
do not change those forecasts. No extra pair helps the additive UNAMA
or emergency-session banks, where the dense route remains behind
fixed targeting. An exact adaptive control still beats the learned
heads in these forecasts.

Each pair is reported as a separate ablation. The results identify
where the extra calibration is informative. They leave open how to
choose a pair prospectively or how often several interactions matter.
[Calibration protocol](calibration-protocol.md) · [All calibration results](calibration.json)

Use the parent environment.

```bash
set -o pipefail
python3 numbered.py plan | cmp - plan.json
python3 numbered.py verify | cmp - verification.json
python3 numbered_eval.py grades | cmp - grades.json
python3 numbered_eval.py replay | cmp - results.json
python3 compact_packer.py grades | cmp - packed-grades.json
python3 compact_packer.py replay | cmp - packed-results.json
python3 calibrate_pair.py | cmp - calibration.json
```

[Myanmar transfer](myanmar/README.md) tests a predeclared calibration pair,
a second native writer, and a routing policy that accounts for grading uncertainty.

[Somalia source transfer](somalia2753/README.md) checks a new docket and
two independently scoped pair effects. It compares the same learned
and fixed routing policies under five and seven reviewed grades.
