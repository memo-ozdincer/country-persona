# Source excerpts preserve exact wording and expose coverage losses

Four model calls shared across the eight receipt masks wrote the public
paragraph and selected national passages. Every assembled record
cleared the factual guard. Each released 28 points. Summed over the
three matched states, the frozen learned route and the strongest fixed
continuation each earned 84 points. Learned routing cost 0.70 more.
It also lost on net under all three modeled inventory priors.

| Component | What the model submitted | Scored consequence |
| --- | --- | --- |
| Public record | Correct tally, mandate and operative conditions, with no draft symbol or sponsor | 28 of 35 public points |
| Brazil | Two verbatim excerpts totaling 27 words | Rejected under the 25-word excerpt cap |
| China | Empty excerpt list and a separate mission-support quote | Rejected under the excerpt schema |
| Russia | Two verbatim excerpts on late changes and mission support | Admitted with no points for the compound reason because the lost compromise is absent |

A post hoc 27-word allowance admits Brazil's actual quoted text.
That gives both routes 105 released points across the three states.
The strongest fixed continuation still costs 0.45 less. The Brazil
comparison tag still points to operational freedom and is unused in
this sensitivity. The word cap on the final record stays at 150.

The comparison covers one exposed docket, fixed learned policies,
simulated receipt masks and same-assistant documentary judgments. All
eight outputs from the two source-bound variants passed native token
replay. Four outputs belong to this exact-excerpt variant. It used a
frozen Qwen3.5-4B checkpoint on an NVIDIA RTX PRO 6000 Blackwell Server
Edition, with zero weight updates. The excerpt gate verified substring
membership, order and budget. Semantic adequacy remains separately
judged. [Protocol](protocol.md) · [Raw calls](evidence/calls.jsonl) ·
[Admitted text](fragments.json) · [Marks](marks.json) · [Results](results.json) ·
[Population](population.json) · [27-word sensitivity](sensitivity.json) ·
[Software and token verification](verification.json)

Use the parent Python environment and import paths.

```bash
set -o pipefail
python3 extract_writer.py plan | cmp - plan.json
python3 extract_writer.py verify | cmp - verification.json
python3 extract_writer.py fragments | cmp - fragments.json
python3 extract_writer.py packets | cmp - packets.json
python3 extract_writer.py score | cmp - results.json
python3 extract_writer.py population | cmp - population.json
python3 sensitivity.py | cmp - sensitivity.json
```
