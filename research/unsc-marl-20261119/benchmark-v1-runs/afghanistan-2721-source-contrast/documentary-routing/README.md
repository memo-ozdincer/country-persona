# Route Afghanistan replies from the official meeting record

**All three native routing rules reached the compiled-record ceiling of
55/70 across six views. The score concealed errors about who made consent
a condition of support.** The explicit claim check at zero and the direct
router each classify four of six views correctly under the receipt-scoped
support labels. The cutoff fitted on Resolution 2553 drops to three of
six. [Exact choices, records and judgments](results.json)

| Sender rule | Best replies on scored contrasts /3 | Support claim correct /6 | Mean released /70 |
| --- | ---: | ---: | ---: |
| Fixed consultation clause | 1 | 1 | 47.667 |
| Fixed UNAMA safeguard | 2 | 5 | 51.333 |
| Direct, averaged logits | 3 | 4 | 55.000 |
| Explicit claim, averaged logits at zero | 3 | 4 | 55.000 |
| Explicit claim, imported 2553 cutoff | 3 | 3 | 55.000 |

The full Russian speech explicitly made agreement from the de facto
authorities a condition for Russia's own support. Its consultation
excerpt ends before that condition. Ghana, speaking for the African
members, described the envoy as potentially complementing UNAMA.
China argued for consultation and cautioned against overriding Afghan
views. Its delivered statement did not make agreement an explicit
condition for China's support for the appointment. [Official meeting record, pp. 4–5](https://documents.un.org/doc/undoc/pro/n23/432/19/pdf/n2343219.pdf)
· [Adopted text](https://docs.un.org/S/RES/2721(2023))

The complete Russia view and two Ghana views belong to the registry
and change the score by 22 points when the router sends the corresponding
reply. The Russia consultation excerpt, China view and empty view
have no registered early card. Either action on those views produces
a 40-point public-and-standalone brief. Direct and zero-threshold claim
routing treat consultation language in the two substantive controls as
a support condition. The imported cutoff also accepts the empty view.
The exact renderer declines to insert a relationship in all three
controls. Reporting only the release mean would miss these errors.
[Source views and page bounds](source-views.json) · [Archived exact renderer](../replay.py)

The model sees the official text and, for the direct arm, the two
existing reply cards. The explicit claim and its action mapping are
supplied by the experiment. Six overlapping views come from one
previously exposed historical event family. The renderer's known
provenance projections establish the scope of this record test.
The support labels are assistant judgments of the visible text.
There was no new policy or backbone fit. All 24 frozen Qwen3.5-4B
first-token calls on Aurora's NVIDIA RTX PRO 6000 Blackwell Server
Edition replay exactly. The first PDF extraction attempt missed the
translated French speaker heading and exited before plan creation or
any model launch. The corrected extractor and paper trail are included.

```sh
set -o pipefail
base_dir=/mfs1/u/memo/country-persona-research
source_pdf=$(mktemp "$base_dir/tmp/un2721-9521-XXXXXX.pdf")
curl --fail --silent --show-error --location \
  'https://documents.un.org/doc/undoc/pro/n23/432/19/pdf/n2343219.pdf' --output "$source_pdf"
"$base_dir/envs/pdf-source-audit-v1/bin/python" -B sources.py "$source_pdf" | cmp source-views.json -
python="$base_dir/envs/aurora-qwen35-smoke-v1/bin/python"
"$python" -B collect_doc.py plan | cmp plan.json -
"$python" -B collect_doc.py verify | cmp verified.json -
python3 -B score_doc.py | cmp results.json -
```

[Protocol](protocol.md) · [Native outputs](verified.json) · [2553 calibration](../../claim-scoped-routing/README.md)
