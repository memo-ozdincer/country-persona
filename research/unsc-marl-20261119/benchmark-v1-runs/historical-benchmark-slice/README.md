# Run the historical benchmark with a frozen model

Peer access reduced released coverage on Myanmar in both orders.
On the Residual Mechanism it improved release in one order. Mean
peer-minus-independent was **−12 points** across the two historical
cases. This is a baseline for attaching future learned policies
to the published evaluation.

| Case | Opening desk | Independent /70 | Peer-informed /70 | Pooled solo /70 |
| --- | --- | ---: | ---: | ---: |
| Myanmar | UK | 42 | 0 | 35 |
| Myanmar | India | 42 | 0 | 0 |
| Residual Mechanism | Peru | 0 | 0 | 0 |
| Residual Mechanism | Russia and Serbia | 0 | 36 | 0 |

**Myanmar.** Both independent records preserve the adoption,
the vote tally, India's explanation and its distinct role in the
presidency. Neither gives the reporting instruction. The two peer
records assign reporting to the Council and to ASEAN respectively.
The adopted instruction names the Secretary-General or his Special
Envoy as reporter and asks for coordination with the ASEAN Special
Envoy. In the India-first peer arm, the UK note already contains
the erroneous attribution to ASEAN. The opposite order's chair
introduces its own incorrect attribution. One pooled solo brief
covers 63 points, including the reporting instruction, and exceeds
the 130-word cap by 15 words.

**Residual Mechanism.** In the Russia-and-Serbia-first peer record,
the chair preserves Serbia's non-voting participation and its
medical-release objection. It also gives the Chapter VII appointment
and both dates, plus the Council's recorded conclusion of its progress
review. The other order invents a roster of affirmative voters and
exceeds the word cap. Several independent and solo records assign
roles or votes that the evidence cannot support. One solo brief
identifies Serbia as a voter and Russia as a non-voting participant,
reversing the evidence.

The peer-minus-independent result on raw criterion coverage is
−10.5 on Myanmar and −4.5 on the Residual Mechanism, before word
limits and source guards. The +18 released-point result on the
Residual Mechanism reflects one peer record clearing the release
conditions. Raw coverage remains visible for every record.

The original collector handles two cases, three arms and both orders
without changing the package. It shares the same opening note between
independent and peer conditions. There are 36 logical calls and 32
physical calls. Frozen Qwen3.5-4B uses greedy BF16 generation on an
NVIDIA RTX PRO 6000 Blackwell Server Edition. Six of 20 physical
note calls and three of 12 finals hit the original generation caps.
All requests and token IDs replay. The run used 17,152 input and 4,294
output tokens.

One assistant graded opaque final packets with the original rubric,
then joined the verdicts to the arms. The quote verifier checks the
stored citations. This is a two-docket exposed slice with fixed
routing. It has no learned-policy comparisons, independently
reviewed judgments, process scores, or full-suite result.

[Protocol](protocol.md) · [Opaque final packets](packets.json) ·
[Reading and source bindings](verdicts.json) · [Results](results.json) ·
[Raw transcripts](evidence/episodes.jsonl) · [Token receipt](verified.json)

Run these checks using the existing Aurora Qwen environment.

```bash
set -o pipefail
python -B slice_run.py plan | cmp plan.json -
python -B slice_run.py packets | cmp packets.json -
python -B bind_review.py | cmp verdicts.json -
python -B slice_run.py score | cmp results.json -
python -B slice_run.py verify | cmp verified.json -
```
