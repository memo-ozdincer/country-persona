# Evidence selection with a fallible final writer

A receipt bank contains the reviewed final records for every subset of
three source notes. Across ten archived banks from seven UN event
families, additional delivered notes sometimes lowered released coverage.
For example, the forward-order Resolution 2422 bank scores 52 with the
second note alone and zero with either pair that contains it. The full
three-note bundle scores 55. Reversing source order changes those bundle
scores. This makes downstream selection depend on bundle combinations
and the writer.

The first test leaves one event family out at a time. The selector sees
only the empty and singleton reviews in the held bank. The routing
comparison fixes two opening policies and plans the last request and
reply against the selector's predicted reward. Families are weighted
equally, after averaging writer variants and orders within each family.

| Bundle selector | Released points over uniform receipt masks | Net utility, uniform inventory | Net utility, correlated inventory |
| --- | ---: | ---: | ---: |
| Forward all | 41.46 | 45.88 | 44.74 |
| Reviewed options only | 43.04 | 43.94 | 43.26 |
| Singleton-additive | 43.29 | 45.88 | 44.74 |
| Learned ridge | 42.54 | 43.51 | 42.80 |
| All labels available | 46.56 | 50.42 | 48.37 |

The fitted selector trails forwarding all under both modeled inventory
laws even though its average across uniform receipt masks is higher.
An evaluation that averages across receipt masks can overstate the
value of a selector that is deployed with a routing policy. Full
knowledge of the archive shows room for selection to help. The
[protocol](protocol.md) and [bank-level results](results.json) retain
the policies and scores for each condition.

The archive combines reviewed frozen-writer outputs with fixed and
verified renderer controls. Scores come from prior assistant reviews.
The result measures selection and routing under archived outputs and
modeled delivery. The case families have prior project exposure.

## Spend one review on a pair or triple

The follow-up keeps the opening policies and delivery assumptions fixed.
It picks one candidate with the ridge forecast or an optimistic 70-point
forecast, reveals the archived score of that candidate, then replans
among reviewed subsets. The four fixed-mask controls receive the same
single review. Hindsight selects the best review after seeing all
candidate scores. The table gives net utility before charging for the
extra review.

| One-review strategy | Net, uniform inventory | Net, correlated inventory |
| --- | ---: | ---: |
| Forward all without another review | 45.88 | 44.74 |
| Choose by ridge forecast | 47.11 | 45.74 |
| Choose by optimistic forecast | 48.33 | 46.70 |
| Always review the first two sources together | 48.87 | 47.12 |
| Best review in hindsight | 49.20 | 47.36 |

The first-pair control beats the learned choice under both inventory laws.
Its gains over forwarding all drop from 2.99 and 2.38 to 0.40 and 0.24
when Resolution 2422 is left out. With Resolution 2422 and Haiti 2699
both removed, its gains become −0.31 and −0.27. The ridge choice loses
to forwarding all without Resolution 2422. Treat the first pair as a
control whose apparent strength depends on source order and case mix.

The study adds one archived score to each replay, with no new model calls
or annotations. The one-review gain includes modeled message cost and
excludes the cost of obtaining the review. The initial run failed when
the inherited replay function expected an oracle table even for a
single-arm call. The completed replay uses the verified forward-all
baseline from the original receipt.
[Follow-up protocol](one-review-protocol.md) · [All choices and outcomes](one-review.json)

From this directory with the project Aurora Qwen environment active:

```bash
set -o pipefail
export PYTHONPATH="$(git rev-parse --show-toplevel)/src"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
python study.py | cmp - results.json
python one_review.py | cmp - one-review.json
```
