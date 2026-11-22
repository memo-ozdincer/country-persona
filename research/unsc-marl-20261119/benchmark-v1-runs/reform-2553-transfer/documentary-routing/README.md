# Route and score replies from the official Resolution 2553 statements

**The claim check matched the best compiled record on all six documentary
views with its default zero cutoff.** The earlier direct prompt matched three
at zero and all six after applying its prior reward calibration. Both
calibrated policies tied. The models saw the official document text and
selected a German reply. A deterministic source-bound renderer assembled the
record and the frozen validator scored it under the same 70-point rubric.
[Exact decisions, records and marks](results.json)

| Reply policy | Best choices /6 | Mean released /70 |
| --- | ---: | ---: |
| Always Fund | 4 | 33.833 |
| Always process | 2 | 33.167 |
| Direct, averaged logit at zero | 3 | 33.500 |
| Direct, existing reward calibration | 6 | 35.167 |
| Claim check, averaged logit at zero | 6 | 35.167 |
| Claim check, existing reward calibration | 6 | 35.167 |
| Best authored-compiler reply | 6 | 35.167 |

The UK full explanation and negotiation excerpt lead to the process reply
and the six-point shared-concern sentence. The UK inclusion discussion and
vote letter provide no support for that relationship. The Belgium explanation
supports its narrower funding priorities, so the Fund reply permits the
separate four-point comparison with Germany's governance position. The
uncalibrated direct router instead chose process on the inclusion excerpt,
Belgium explanation, and empty view. The claim check kept those views
distinct. [Official source](https://documents.un.org/doc/undoc/gen/n20/342/63/pdf/n2034263.pdf)
· [Rubric and relation registry](../docket.json)

The six views come from the same historical docket and overlap in source
text. This is an official-document input test, with source spans mapped
to registered cards by the assistant and a fixed renderer. No claim grade
or mapping entered either model input. The compiler was held fixed across
the prompt comparison. The test did not fit a new policy or score freely
generated final text. The equal means weight the six views uniformly.
The 24 first-token decisions replay exactly on frozen Qwen3.5-4B from
Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition.

The document extractor checks the 28-page official file and the annex
boundaries on pages 23 and 26–28. The locked source views include the PDF
digest and the Germany annex digest. The full source document is supplied
by the UN. No final record reproduced in `results.json` depends on an
unlocated fact from a reader response. [Source extraction](sources.py) · [Protocol](protocol.md)

```sh
set -o pipefail
base_dir=/mfs1/u/memo/country-persona-research
source_pdf=$(mktemp "$base_dir/tmp/un2553-1167-XXXXXX.pdf")
curl --fail --silent --show-error --location \
  'https://documents.un.org/doc/undoc/gen/n20/342/63/pdf/n2034263.pdf' --output "$source_pdf"
"$base_dir/envs/pdf-source-audit-v1/bin/python" -B sources.py "$source_pdf" | cmp source-views.json -
python="$base_dir/envs/aurora-qwen35-smoke-v1/bin/python"
"$python" -B study_doc.py plan | cmp plan.json -
"$python" -B study_doc.py verify | cmp verified.json -
python3 -B score_doc.py | cmp results.json -
```

[Native traces](verified.json) · [Earlier synthetic challenges](../../claim-scoped-routing/README.md)
