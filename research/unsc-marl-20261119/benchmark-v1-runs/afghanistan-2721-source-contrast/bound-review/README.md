# Separate native support judgments from source-bound rendering

Exact rendering preserves both approved comparisons from Resolution 2721. An additional frozen Qwen gate rejects at least one of them, losing the benefit of reading the earlier note. The native probe asks whether the entire candidate is supported by the displayed cards. Each of 14 candidates is presented under both label assignments. [Protocol](protocol.md) · [Candidate texts and source keys](probes.json)

| Judgment rule | Exact /14 | Supported admitted /4 | Unsupported admitted /10 | Abstentions |
| --- | ---: | ---: | ---: | ---: |
| A means supported | 10 | 0 | 0 | 0 |
| B means supported | 12 | 3 | 1 | 0 |
| Average mapped logits | 11 | 1 | 0 | 0 |
| Require mapped agreement | 9 | 0 | 0 | 4 |

The averaged judge admits the registered consultation-versus-consent comparison. It rejects the registered UNAMA comparison and both valid rephrasings. The single-order false admission is the Russia comparison on a crossed receipt, where the actual consultation clause is missing. Both label orders reject the six scope and attribution errors made with both source slots filled. The semantic labels are author-reviewed. The proposed rephrasing that says the African members expected the envoy to support UNAMA compresses their discussion of potential complementarity, and deployment uses neither rephrasing. [Native logits and paired scores](scores.json)

| Renderer at 75% delivery, balanced first note | Content-informed | Best arrival-only | Content gain |
| --- | ---: | ---: | ---: |
| Exact provenance and registered comparison | 56.8750 | 50.6875 | +6.1875 |
| Exact provenance and mean-logit gate | 50.6875 | 50.6875 | 0 |
| Exact provenance and agreement gate | 44.5000 | 44.5000 | 0 |

The renderer requires both original source IDs and exact article text to insert either of the two registered comparisons. Eight tamper checks per eligible two-record bank reject altered text, a changed claim, or foreign IDs. If the model gate declines a comparison, all supported verbatim parts still release. The native gates add 1.125 expected forward calls to the content-informed route in this example. The exact rule requires no additional calls. This control measures the value of the added semantic gate within an established registry. It does not judge unseen claims. [Records and all twelve delivery settings](scores.json)

## Transfer a conservative cutoff

A threshold of +0.6875 rejects all unsupported fitting probes on the archived Resolution 2475 bank. It rejects all 14 Resolution 2721 candidates as well. In reverse, the 2721 threshold of −0.125 accepts all four supported 2475 probes and five of six unsupported probes. This is an archival sensitivity comparison between two related but differently worded probe sets. Neither uses the other case's labels to choose the threshold. [Exact two-way transfer](threshold.json)

The 28 frozen Qwen3.5-4B calls completed on NVIDIA RTX PRO 6000 Blackwell Server Edition. The recorded worker exited normally. This measures existing source paraphrases and known relation templates on exposed dockets. Delivery is simulated and no language-model weights were updated. [Worker details](evidence/launch.json) · [Token verification](verified.json)

## Reproduce

From this directory in the project environment:

```sh
set -o pipefail
root=$(git rev-parse --show-toplevel)
export PYTHONPATH="$root/src:$root/research/unsc-marl-20261119/crossbench/gaza2023"
export PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 HF_HUB_OFFLINE=1
py=/mfs1/u/memo/country-persona-research/envs/aurora-qwen35-smoke-v1/bin/python
"$py" review.py plan | cmp plan.json -
"$py" review.py verify | cmp verified.json -
"$py" score_review.py | cmp scores.json -
python3 -B threshold_transfer.py | cmp threshold.json -
```
