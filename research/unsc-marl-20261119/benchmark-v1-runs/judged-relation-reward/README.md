# Measure what a native relation judge teaches the sender

**The averaged judge gets 10 of 12 archived records right and degrades
the fitted sender by 0.339 utility points.** It is asked to grade only
the specified relationship in the final brief against numbered
evidence. Eight actual records lack the required relationship, while
four express it. Four additional mutations test direct disagreement with
the source. [Exact prompts and model scores](verified.json) · [Metrics and replay](results.json)

| Judge rule | Correct archived records /12 | Rejected mutations /4 | Mean relation-points error | Sender utility | Mean utility regret |
| --- | ---: | ---: | ---: | ---: | ---: |
| A means met | 8 | 4 | −4.5 | 31.453 | 0.772 |
| B means met | 4 | 0 | +9.167 | 30.847 | 1.378 |
| Average mapped logits | 10 | 3 | +1.5 | 31.885 | 0.339 |
| Require both mappings to approve | 8 | 4 | −4.5 | 31.453 | 0.772 |
| Exact archival relationship marks | 12 | 4 | 0 | 32.225 | 0 |

Averaging preserves credit for three of four genuine comparisons. It misses the
Germany–Belgium funding comparison at a zero margin, and awards
22 points to the Russia record that contains the UNAMA safeguard
but omits the required distinction between consultation and consent.
It also accepts the mutated funding record that assigns management
authority to Belgium. The mutation is held out of all reward fits.
Requiring agreement suppresses all four valid relationships because
the first mapping consistently chooses B. Either single mapping has
a large label effect.

The sender replay substitutes only these relationship points into the
same 128 randomized training episodes on each docket. Standalone
material, reply observations, transport, and prices stay fixed.
The fitted action values are evaluated against the archived utility of
the selected actions in 1,152 held settings. The averaged judge fit
matches the exact sender in 898 settings. Its mean regret is 0.025
on 2553 and 0.654 on 2721. Most of the pooled loss comes from pricing
an unsupported alternative reply as though it carried the
22-point Russia relationship. [Original sender fit and oracle](../partner-conditioned-calibration/README.md)

This is a frozen one-criterion judge test. The original guarded renderer
and the assistant-authored rubric scores supply the comparison key.
The replay replaces no source guard or other criterion, and no mutated
record is treated as releasable. The viewed events and cases are exposed.
There were 32 first-token calls, 16,514 input tokens and 64 saved label and
end tokens on Aurora's NVIDIA RTX PRO 6000 Blackwell Server Edition.
Exact prompt and token replay succeeds. No new writer, full judge,
independent annotation, or backbone optimization is measured.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$python" -B collect_judgments.py plan | cmp plan.json -
"$python" -B collect_judgments.py verify | cmp verified.json -
"$python" -B score_judgments.py | cmp results.json -
```

[Protocol](protocol.md) · [Worker receipt](evidence/launch.json)
