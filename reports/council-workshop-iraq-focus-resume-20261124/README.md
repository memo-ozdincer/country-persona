# Completing the six-seat Iraq focus swap

France opened both runs on the registered fictional Iraq impasse.
The mixed team used GPT-6-Astra for the UAE and GPT-6.1-Sol for the
other five seats. The reference used GPT-6.1-Sol throughout.
Both used the standard floor procedure, a 16-speech cap and a
55-call cap. The resume reused 25 exact model replies and received
23 fresh replies. It preserved the original case, prompts and budgets.

| Assignment | Outcome | Speeches | Calls | Checked exclusions |
| --- | --- | ---: | ---: | ---: |
| All Sol | Unresolved | 16 | 55 | 3 of 4 |
| Astra at UAE | Certified impasse | 14 | 48 | 4 of 4 |

The first structured difference was on call 20, when Ghana gave
speech five. Ghana, played by Sol in both arms, proposed `hybrid`
in the reference and ruled out `public` in the mixed run. The UAE
ruled out `hybrid` on its first speech in both. France confronted
`closed` on speech 13 in the mixed run and ruled it out. The UK then
declared the impasse. In the reference, Brazil put `closed` on the
floor on speech 15, after France's last speech.

There is one trajectory per assignment. The first divergence
precedes the UAE's first speech, so the timing and outcome do
not isolate the effect of the UAE's model. The registered matrix
now has 12 completed cells.

From the repository root:

```sh
set -o pipefail
out=reports/council-workshop-iraq-focus-resume-20261124
python3 -B "$out/verify-resume.py" plan | cmp "$out/plan.json" -
python3 -B "$out/verify-resume.py" score | cmp "$out/score.json" -
python3 -B research/council_workshop/replay.py "$out/mixed"
```

[Original attempts and all-Sol run](../council-workshop-iraq-pilot-20261123/README.md) ·
[Mixed decision log](mixed/calls.jsonl) · [Meeting result](mixed/result.json) ·
[Paired trace score](score.json)
