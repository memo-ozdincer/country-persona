# Transfer the source-preserving chair to Resolution 2739

**The fixed record kept both full-evidence briefs at 56/70. The new model
sentences earned zero of the 14 points for bounded agreement.** The Council
extended a reporting request. Japan and the United States explained how
timely information would inform Council deliberations. Algeria valued
receiving the reports and abstained for distinct reasons. The two native
comparisons focused on the difference in votes and left the shared
reporting rationale implicit. [Meeting record, pp. 2–4](https://documents.un.org/api/symbol/access?l=en&s=s%2Fpv.9672&t=pdf) · [Adopted resolution](https://digitallibrary.un.org/record/4053356)

| Received statements | Fixed /70 | Native /70 | Authored ceiling /70 |
| --- | ---: | ---: | ---: |
| No statement | 42 | 42 | 42 |
| Co-sponsors only | 49 | 49 | 49 |
| Algeria only | 49 | 49 | 49 |
| Both, co-sponsors first | 56 | 56 | 70 |
| Both, Algeria first | 56 | 56 | 70 |
| Adopted action and Algeria, both orders | 49 | 49 | 49 |

The three partial or empty prompts produced exactly `NONE`. One crossed order
produced a source-supported restatement of the adopted action and Algeria's
abstention. The other abstained. No native sentence invented agreement.
The complete-pair check skips the crossed writer call without changing the
released record's score. The fixed base uses the prior authored public record,
the co-sponsors' sentence from the authored calibration, and the previously
reviewed Algeria sentence. [Exact appended text and finished records](scores.json)
· [Assistant grading](marks.json) · [Original rubric](../docket.json)

## Send policy transfer

Map the successful India-first order from Resolution 2664 to Algeria-first,
keeping the critic's learned 12-point bonus. Rebase the standalone gains to
the target's seven points per received delegation. Evaluate the policy with
the actual new terminal scores at the same 12 delivery and order settings.
The imported policy sent both sources in six settings and matched the
target optimum in the six where it withheld. Sending increased mean source
coverage and raised average released points to 47.833. Under the constructed
cost, its mean utility was **40**, two points below the target optimum of
42 from withholding throughout. This cost charges each send its expected
standalone gain plus two to isolate the value of synthesis. The replay uses
known delivery and order probabilities. [Routing results](routing.json) · [2664 training and cost definition](../../humanitarian-2664-admission/sender-credit-fit/README.md)

The writer uses the same frozen Qwen3.5-4B procedure and changes the two issue
phrases to match the new comparison. The prior Resolution 2739 full-writer
crossover measured a different writing and information route. This run measures
seven low-cost inference calls on a previously exposed UNBench docket
with assistant grades. Transfer of the release scaffold kept the fixed
claims safe in these outputs. Transfer of the synthesis bonus failed.
All saved tokens replay, and the worker exited normally after seven calls,
using 1,673 input and 106 output tokens on an NVIDIA RTX PRO 6000 Blackwell
Server Edition. There were zero optimizer updates.

```sh
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B study.py plan | cmp plan.json -
python -B study.py verify | cmp verified.json -
python -B annotate.py | cmp marks.json -
python -B score.py | cmp scores.json -
python -B routing.py | cmp routing.json -
```

[Locked protocol](protocol.md) · [UNBench and UNSC-Bench source join](../provenance.json)
