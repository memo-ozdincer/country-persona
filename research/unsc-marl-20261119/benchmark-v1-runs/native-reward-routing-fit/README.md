# Learn routing from the compact writer's actual release scores

On the ungated compact writer, a new fit reaches **40.411 utility**
and the strongest arrival-only control reaches **39.384**. The
typed-reward policy and the unfitted rubric rule both score 38.539.
Learning from observed final-record scores changes which excerpts
are worth sending, based on the writer's actual guard failures.

| Evaluation writer | Content-aware fit | Matched arrival-only fit | Best arrival-only | Content-aware oracle |
| --- | ---: | ---: | ---: | ---: |
| Ungated compact | **40.411** | 39.237 | 39.384 | 40.420 |
| Gated compact | **40.411** | 39.237 | 39.457 | 40.565 |
| Topic-guided with source gate | 22.852 | 27.368 | **37.168** | 37.242 |

The fitted content-aware pair beats best arrival-only in **75 of
96** ungated settings and matches the oracle in **91 of 96**. It
releases a supported comparison on 25.08% of episodes, versus
16.96% for the best arrival-only control. The typed-trained pair
releases a supported comparison on 25.43% and fails the guard on
3.90%. The new pair yields zero guard failures. It keeps Malta's
80 send settings, reduces A3+ from 80 to 76, and withholds
Switzerland in all 96 settings. The preceding policy sent the
Swiss note in 16 settings. Mean sending cost falls from 5.933 to
5.292 and mean released points rise from 44.472 to 45.703.

A component swap reproduces the full gain with the new sender and
old reply desk. The two reply desks make the same choices after
receiving a note. Their choices after silence differ, with equal
standalone credit for the two documents. This attributes the
improvement over the typed-trained pair to the sender learning
the cost of failed native records. The source-aware reply still
enables the comparison advantage over arrival-only.

Both actors start from zero. The sender estimates paired
send-versus-withhold value under the same writer and channel
draws. The reply actor receives a sampled terminal policy
gradient. The two fits have the same seed, 512 batches of 256
episodes, and 262,144 nominal terminal evaluations per arm.
These are simulator lookups on the same 12 scored receipt
states. They are separate from model calls. The held channel
probabilities, prices and view distributions come from the
previous 2744 protocol.

The topic-guided writer was excluded from optimization. Under
that writer, the delivered combinations that previously
earned comparison credit now frequently fail the guard.
The same content-aware policy drops below arrival-only and
its guard-failure rate rises to 25.08%. This tests transfer
across writers on one exposed docket. The source text and
same-assistant marks come from earlier runs. No generation,
model-weight updates or benchmark release edits were made.

[Locked protocol](protocol.md) · [Training inputs](plan.json) ·
[Policy weights, held settings and writer swap](results.json) ·
[Source records and marks](../delisting-witness-render/README.md)

Run from this directory using the existing Aurora Qwen environment.

```bash
set -o pipefail
export OPENBLAS_NUM_THREADS=1
python -B learn.py --plan | cmp plan.json -
python -B learn.py | cmp results.json -
```
