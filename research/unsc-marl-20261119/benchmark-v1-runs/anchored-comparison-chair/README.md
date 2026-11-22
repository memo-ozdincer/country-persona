# Generate only the relationship in a source-preserving Council record

Preserving the public lead and delivered source text restores standalone
coverage. The direct comparison earns the 22-point Russia relation but
adds unsupported adoption claims on both Ghana branches. Requiring
verbatim witnesses prevents those additions in this run by rejecting all
four candidate blocks. The constrained writer still yields no advantage
for the trained team over a strong arrival-only control.

| Final writer | Mean utility, learned team | Mean utility, best arrival-only | Learned-team released /70 | Learned-team relationship points |
| --- | ---: | ---: | ---: | ---: |
| Prior native whole brief | −6.64 | 8.50 | 1.96 | 0.00 |
| Verbatim standalone only | 34.20 | 38.13 | 42.81 | 0.00 |
| Verbatim with direct comparison | 28.26 | 40.72 | 36.86 | 4.36 |
| Verbatim with witnessed comparison | 34.20 | 38.13 | 42.81 | 0.00 |
| Authored relation with verbatim standalone | 43.29 | 40.72 | 51.90 | 9.09 |

Each row reuses the existing frozen sender and reply decisions across
48 channel and price settings per writer. The arrival-only comparator
optimizes when to send and may select different replies for arrival and
silence. With either tested native comparison prompt, an oracle that
also reads content still ties that arrival-only comparator. For the
direct writer it can earn the Russia bonus by selectively sending the
Russia view. A second valid relation is needed for reading the note
to improve the strongest policy in this particular replay.

The direct Russia sentence preserves its support condition and the
adopted consultation clause's lack of a consent requirement. The matched
Ghana sentence says the African members' proposal “was adopted,” whereas
the adopted text requests an envoy and preserves UNAMA's mandate. The
other Ghana sentence claims the consultation procedure implemented
the proposal for a complementary envoy. Both claims block release.
The direct Russia/UNAMA crossed pair abstains.

The witness prompt returns three lines on all four pairs. Each early
quote converts a curly apostrophe to ASCII, so the exact validator
retains the standalone record. Two late quotes also change punctuation
beyond the apostrophe. A post hoc apostrophe-only normalization passes
the witness check on both matched pairs. It would also admit their
incorrect links. One recasts Russia's condition for its own support as
a demand for consent to the appointment. The other asserts the African
members' suggestion was “legally adopted.” The model can locate the
relevant text yet still misstate its legal force.

The failure points toward preserving speaker, stance and adopted force
as distinct inputs to any generated relation. The present evidence is
one exposed docket with four complete receipt pairs and one reader.
The scenario replays communication choices over native outputs from a
frozen chair. It uses registered source messages and simulated channels.

The first launch exited at the worker's device occupancy check before
creating a run. A verified empty device permitted the retry. All eight
calls then completed on NVIDIA RTX PRO 6000 Blackwell Server Edition.
No model weights changed. The scored notes are outside the closed
benchmark release.

[Exact prompts](plan.json) · [Captured text and tokens](verified.json) ·
[Evidence-grounded judgments](marks.json) · [Policy replay](results.json) ·
[Worker identity](evidence/launch.json)

```bash
set -o pipefail
python -B collect_anchored.py plan | cmp plan.json -
python -B collect_anchored.py verify | cmp verified.json -
python -B score.py | cmp results.json -
```

Use the existing Aurora Qwen3.5 environment. The verification command
checks stored generation against the local tokenizer without a GPU.
