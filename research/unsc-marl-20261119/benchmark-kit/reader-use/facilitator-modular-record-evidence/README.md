# Preserve delivered documentary evidence in the final record

Compare two exposed Council dockets whose jointly generated
supplements omitted claims or exceeded the shared word limit.
Use the same normalized cards for the UNAMA renewal and the
Ukraine emergency special session. For each docket the frozen
Qwen3.5-4B writer receives one source at a time. The supplied
speaker prefix and the citation are added by the assembler.
The generated predicate is retained exactly. It is subject to
an ending, 27-word limit, one-line format, and source-local
factual review. The public section preserves the Council
decision, tally and second public criterion on each docket.
[Locked protocol](protocol.md) ·
[UNAMA source join](../facilitator-unama-authority-evidence/provenance.json) ·
[Emergency-session source join](../facilitator-emergency-session-evidence/provenance.json)

The same three notes are available across all eight receipt views
and to every transport policy. A rejected note cannot erase an
already admitted contribution. The final records still have a
145-word cap. Any evidence credit requires both delivery and
admission. Under the earlier two-send protocol only full access can
provide all three sources. All transport arms reuse the author
review and the same six actual writer calls. The comparison
replays frozen typed-message policies.

## Results

All six generations returned complete sentences. Five exceeded
the predetermined 27-word allowance. The only short sentence also
failed factual support by overstating India's account of border
movements. The locked predicate gate admitted zero notes. The final
therefore contains the public record alone and scores 34 points
for every receipt. This primary result remains in `results.json`.

In a post hoc control, accept complete sentences with the verified
speaker lead at up to 36 words and retain the 145-word final cap.
Three notes meet the factual and format checks. Norway and China
are admitted on UNAMA. Russia's effectiveness claim has an
uncertain referent and is withheld. Nebenzia's national statement
is admitted on the emergency docket. Brazil's note adds an
obligation to exhaust the Council's tools and India's overstates
its position on movement. Their notes are withheld. The admitted
sentences are unchanged apart from the added source citations.

| Post hoc sentence assembly | Public-only | Full-access | Guarded receipts | Strict complete |
| --- | ---: | ---: | ---: | ---: |
| UNAMA | 34/70 | 58/70 | 8/8 | 0/8 |
| Emergency session | 34/70 | 46/70 | 8/8 | 0/8 |

The earlier jointly generated writer could lose points when
it received another note. With this assembler, the observed
reward equals the sum of admitted singleton contributions plus
the public baseline on all 16 masks. The one-pair check adds
the same score already predicted by the singleton estimates
and leaves the ordering unchanged.

| Uniform inventories, net after transport costs | Learned query | Query erased at equal cost | Fixed request script | Exact independent | Exact adaptive |
| --- | ---: | ---: | ---: | ---: | ---: |
| UNAMA | 47.934 | 47.426 | 47.133 | 47.470 | 48.004 |
| Emergency session | 41.717 | 40.541 | 41.885 | 42.170 | 42.170 |

Under correlated duplicate inventories, the UNAMA query earns
46.251 versus 46.133 for optimized independence and 46.367 for
the exact adaptive policy. On the emergency docket only one
statement can earn credit. The exact independent policy attains
the adaptive ceiling under both priors. The controlled gains on
UNAMA use already exposed documentary sources, typed messages,
and same-assistant review. Complete diplomatic records and
general improvements from live deliberation remain unevidenced.
[Six generations](transcript.jsonl) · [Exact review](marks.json) ·
[Locked scores](results.json) · [Sentence assembly and routing](complete-sentences.json)

```bash
OPENBLAS_NUM_THREADS=1 python facilitator_modular_record_score.py facilitator-modular-record-evidence --marks facilitator-modular-record-evidence/marks.json
OPENBLAS_NUM_THREADS=1 python facilitator_modular_record_sentence.py facilitator-modular-record-evidence
```
