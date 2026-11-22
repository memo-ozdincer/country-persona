# Test native writing downstream of an adaptive UNIFIL route

The matched three-state audit used the same private inventory and opening
sends throughout. Its learned routes produced the Brazil–China record in
two states and the Brazil–China–Russia record in the third. With the prior
archived score bank, the frozen learned route earned 196 released points
summed across states versus 189 for the strongest fixed target. With
records written directly by frozen Qwen3.5-4B, it earns zero versus seven
for optimized silence. Query and reply costs move the differences from
+7 to +6.95 and from −7 to −7.70 respectively.

| Writer inputs beyond the public record | Words | Raw score | Guard | Released |
| --- | ---: | ---: | --- | ---: |
| Brazil | 136 | 7–21 | Clear | 7 |
| China | 135 | 21–28 | Failed | 0 |
| Brazil and China | 119 | 21–35 | Failed | 0 |
| Brazil and Russia | 122 | 14–21 | Failed | 0 |
| China and Russia | 151 | 21–28 | Uncertain | 0 |
| Brazil, China and Russia | 133 | 21–35 | Failed | 0 |

In the two-card learned record the writer inferred that China endorsed
UNIFIL's operational-independence terms. In the three-card record it
inferred that Russia considered the final outcome acceptable or salvageable.
The sources establish support for the mission and reservations about the
text. These are failures even under a generous reading of the vote tally.
The rubric also awards partial raw coverage where the relevant positions
were present. Fixed replies are optimized directly on the observed native
scores, including the option to stay silent.

This selected mechanism check uses the historical public UNIFIL case
with simulated inventories and delivery, six shared writer calls, fixed
routing policies, and same-assistant annotations. It uses greedy decoding
on an NVIDIA RTX PRO 6000 Blackwell Server Edition with zero training
updates. It verifies downstream writing without a fresh transport run.
[Protocol](protocol.md) · [Prompts](plan.json) · [Native responses](evidence/calls.jsonl) ·
[Criterion marks](marks.json) · [Results](results.json) · [Verification](verification.json)

Run in the project Python environment using the parent audit's
`PYTHONPATH` and thread settings.

```bash
set -o pipefail
python3 natural_writer.py plan | cmp - plan.json
python3 read_native.py packets | cmp - packets.json
python3 read_native.py verify | cmp - verification.json
python3 read_native.py score | cmp - results.json
```

[Attribution-focused follow-up](attributed/README.md) changes only the
writer's system prompt and replays the same six masks. Raw coverage
improves, while the learned route continues to release zero. Even a
favorable ruling on the all-source record leaves a fixed policy ahead on
cost.

[Source-bound writer](source-bound/README.md) isolates each national
source before deterministic composition. All eight records clear the
guard. The extra Russia card earns no additional points because the
fragment omits the lost compromise.
