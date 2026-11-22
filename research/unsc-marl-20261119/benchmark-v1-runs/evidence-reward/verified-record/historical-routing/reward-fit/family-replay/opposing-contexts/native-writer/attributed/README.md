# Attribution-focused writer follow-up

On the same six UNIFIL evidence sets, the more explicit prompt improved
raw coverage for every record. Summed across the learned route's three
states, the raw lower bound rose from 63 to 105. It still released zero.
The best fixed continuation also released zero and used silence, which
gave it a 0.70 advantage after query and reply costs.

| Writer inputs beyond the public record | Words | Raw score | Guard | Released |
| --- | ---: | ---: | --- | ---: |
| Brazil | 154 | 28–42 | Failed | 0 |
| China | 129 | 35–35 | Failed | 0 |
| Brazil and China | 138 | 28–42 | Failed | 0 |
| Brazil and Russia | 144 | 28–35 | Failed | 0 |
| China and Russia | 158 | 42–42 | Clear | 0 |
| Brazil, China and Russia | 148 | 49–56 | Uncertain | 0 |

The Brazil–China record now distinguishes their assessments of Lebanese
concerns, then wrongly says both emphasized sovereignty and consent.
The all-source record is within the word cap. Its statement about China
and Russia could attribute China's stronger request for closer
communication to Russia as well. The separate sensitivity analysis
clears this guard and grants 49 points for the record. The strongest
fixed continuation reaches that same record with less communication cost.

The only actor input change was the system prompt. The six calls ran
with frozen Qwen3.5-4B on an NVIDIA RTX PRO 6000 Blackwell Server Edition.
The marks are from the same assistant and the selected historical case was
exposed. The receipts describe simulated delivery with a native writer.
[Protocol](protocol.md) · [Native responses](evidence/calls.jsonl) ·
[Criterion marks](marks.json) · [Results](results.json) ·
[Sensitivity](sensitivity.json) · [Token verification](verification.json)

Use the same environment as the parent run.

```bash
set -o pipefail
python3 attributed_writer.py plan | cmp - plan.json
python3 attributed_writer.py packets | cmp - packets.json
python3 attributed_writer.py verify | cmp - verification.json
python3 attributed_writer.py score | cmp - results.json
python3 sensitivity.py | cmp - sensitivity.json
```
