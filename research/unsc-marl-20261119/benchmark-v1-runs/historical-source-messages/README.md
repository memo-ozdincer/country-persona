# Let desks send exact source passages

Replacing free-text working notes with source selection restored both
Myanmar peer briefs to released scores of **35 and 42**. Independent
selection earned the same scores. On the Residual Mechanism, all four
briefs using source selections failed release. The chair could still
invent material when every delivered message was grounded.

| Case and first desk | Free-text independent | Free-text peer | Source selection independent | Source selection peer |
| --- | ---: | ---: | ---: | ---: |
| Myanmar, UK | 42 | 0 | 35 | 35 |
| Myanmar, India | 42 | 0 | 42 | 42 |
| Residual Mechanism, Peru | 0 | 0 | 0 | 0 |
| Residual Mechanism, Russia and Serbia | 0 | 36 | 0 | 0 |

On Myanmar, the UK chose its sponsorship and rationale in every
condition. It passed over the block giving the exact reporting
instruction. The chair stopped assigning reporting to ASEAN or the
Council. The reporting criterion remains unmet in all four drafts,
and one no longer preserves UK sponsorship. The output difference
is a transport and selection effect. Both protocols use the same
final chair prompt.

On the Residual Mechanism, every selection from the combined desk
was the Serbian medical-release objection. In one order peer access
changed the later Peru desk's choice from the state-cooperation
passage to the unity passage. Independent and peer selection
otherwise sent identical sources. Two final drafts supplied
unsupported named voting rosters. Two drafts that gave no such
roster exceeded the word cap and ambiguously attached Peru's
judicial examples to the Council's cooperation instruction.

The one-block-per-desk limit makes the legal action space small.
An authored map of evidence dependencies places 49 Myanmar
rubric points within reach with the chosen packets, versus 56
when the UK sends the operative mandate. For the Residual Mechanism
the selected pairs expose 50 or 52 rubric points. These are available
evidence counts. They depend on the supplied source requirements
and leave synthesis quality open. [Mapped source dependencies](coverage.py) · [Enumerated pairs](coverage.json)

Both conditions use one common opening selection per order. The 20
physical calls match the number for the comparable archived
independent and peer arms. Selection uses 8,617 input and 1,665
generated tokens, compared with 9,619 and 2,645 for the prior
free-text arms. The exact passages contain 21–35 tokens apiece.
There are no invalid selections and one final reaches the token cap.
The frozen Qwen3.5-4B worker ran on NVIDIA RTX PRO 6000 Blackwell
Server Edition.

This is a two-docket exposed experiment and one assistant reading
of five unique opaque final packets. It changes the intermediate
action and the content delivered, and retains the original final
prompt and rubric. It provides a constrained baseline for later
learning and shows why validating messages alone leaves the final
record guard necessary. The benchmark release and model weights
were unchanged.

[Protocol](protocol.md) · [Actual selection and synthesis](evidence/episodes.jsonl) ·
[Final verdicts](verdicts.json) · [Scores](results.json) · [Token replay](verified.json)

```bash
set -o pipefail
python -B exact_notes.py plan | cmp plan.json -
python -B exact_notes.py packets | cmp packets.json -
python -B coverage.py | cmp coverage.json -
python -B exact_notes.py score | cmp results.json -
python -B exact_notes.py verify | cmp verified.json -
```
